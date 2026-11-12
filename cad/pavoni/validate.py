"""make validate - PLAN.md 11.1 plus data and procedure checks.

Runs against build/manifest.json, build/meshes.npz and the OPTIMIZED GLB in
web/public/models/pavoni.glb (named nodes can get lost in optimization).

Checks
  1 reconcile    every instance in parts.yaml is a node in the optimized GLB and vice versa
  2 solids       every solid valid, closed, volume > 0
  3 interference pairwise overlap below tolerance, except the reasoned whitelist
  4 paths        each part/assembly leaves along its explode axis without collision
                 when exactly its requires_removed closure is gone (way: Ctx.travel)
  5 envelope     bounding box (without lever and portafilter grip) vs 200 x 290 x 320-366:
                 within 7 % ok, within 15 % warning, beyond that error
  6 budgets      GLB size, triangles, draw calls
  7 data         references, DAG, tools, dims keys
  8 procedures   ids exist, requires satisfied, every step collision-free, nothing overlaps
                 where the removed parts and assemblies come to rest
  9 proportions  photo ratios and catalog sizes against the model
 10 explode      no two parts overlap at the end of any stage of the exploded view
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import defaultdict

import numpy as np

from .data import load_all
from .dims import Dims
from .glbinfo import glb_stats
from .paths import MANIFEST, REPORT, WEB_MODEL
from .proportions import evaluate

# B x T x H from retailer data sheets (Q3). Their heights for the Professional differ
# (320 ... 366 mm, PLAN 8.1), so the height is a range. Up to ENVELOPE_TOL outside is fine, up to
# ENVELOPE_FAIL a warning (photo ratios or the boiler diameter are a little off - a measured
# boiler diameter must not be rejected by a catalog figure), beyond that a modelling error.
ENVELOPE = {"x": (200.0, 200.0), "y": (290.0, 290.0), "z": (320.0, 366.0)}
ENVELOPE_TOL = 0.07
ENVELOPE_FAIL = 0.15
ENVELOPE_EXCLUDE = ("p087_", "p088_lever_grip", "p088_portafilter_grip", "p095_portafilter")
# The model counts as complete (envelope and wear-part coverage become hard errors) once no
# non-optional part is 'planned'.
BUDGET = {"bytes": 15e6, "triangles": 1.5e6, "draw_calls": 300}
SHRINK = 0.05  # mm, moving meshes are shrunk so touching faces are not collisions
STEP = 0.5  # mm path sampling
WHITELIST_FREE_TRAVEL = 1.0  # mm, whitelisted pairs may overlap at the start of a path
INTERFERENCE_THICKNESS = 0.06  # mm, thinner overlap = tessellation artefact / contact
# Boiler diameters for which the photo ratios and the catalog parts fit together (checked by
# cad/tests/test_calibration.py). Below ~98 mm the catalog gasket (dia. 104) no longer fits under
# the boiler foot and the element no longer fits into the base.
BOILER_OD_RANGE = (98.0, 118.0)


class Report:
    def __init__(self):
        self.checks: dict[str, dict] = {}

    def add(self, check: str, level: str, msg: str):
        c = self.checks.setdefault(check, {"errors": [], "warnings": [], "info": []})
        c[{"error": "errors", "warn": "warnings", "info": "info"}[level]].append(msg)

    def ok(self, check: str, msg: str = ""):
        c = self.checks.setdefault(check, {"errors": [], "warnings": [], "info": []})
        if msg:
            c["info"].append(msg)

    @property
    def n_errors(self):
        return sum(len(c["errors"]) for c in self.checks.values())

    def print(self):
        for name, c in self.checks.items():
            state = "FEHLER" if c["errors"] else ("WARN" if c["warnings"] else "ok")
            print(f"[{state:6}] {name}")
            for m in c["errors"]:
                print(f"         x {m}")
            for m in c["warnings"][:25]:
                print(f"         ! {m}")
            if len(c["warnings"]) > 25:
                print(f"         ! ... {len(c['warnings']) - 25} weitere Warnungen")
            for m in c["info"][: (60 if name.startswith("9") else 12)]:
                print(f"           {m}")


# --------------------------------------------------------------------------- model


class Ctx:
    def __init__(self, data, manifest, meshes):
        self.data = data
        self.manifest = manifest
        self.parts = {p["id"]: p for p in data["parts"]}
        self.asm = {a["id"]: a for a in data["assemblies"]}
        self.inst = manifest["instances"]  # built instances only
        self.part_instances = {p["id"]: [i for i in p["instances"] if i in self.inst] for p in data["parts"]}
        self.inst_asm = {i: v["assembly"] for i, v in self.inst.items()}
        self.meshes = meshes
        self._bvh = {}
        self._bvh_shrunk = {}
        self.overlaps = {}
        for o in data["overlaps"]:
            for a in self.expand(o["a"]):
                for b in self.expand(o["b"]):
                    self.overlaps[frozenset((a, b))] = o

    # refs -------------------------------------------------------------------
    def kind(self, ref: str) -> str:
        if ref in self.asm:
            return "asm"
        if ref in self.parts:
            return "part"
        if "__" in ref and ref.split("__")[0] in self.parts and ref in self.parts[ref.split("__")[0]]["instances"]:
            return "inst"
        return "unknown"

    def expand(self, ref: str) -> list[str]:
        k = self.kind(ref)
        if k == "part":
            return list(self.part_instances[ref])
        if k == "inst":
            return [ref] if ref in self.inst else []
        if k == "asm":
            return [i for i, a in self.inst_asm.items() if a == ref or a.startswith(ref + ".")]
        return []

    def requires(self, ref: str) -> list[str]:
        k = self.kind(ref)
        if k == "asm":
            return self.asm[ref].get("requires_removed", [])
        if k == "part":
            p = self.parts[ref]
            extra = [r for v in (p.get("instance_requires") or {}).values() for r in v]
            return list(dict.fromkeys(p["requires_removed"] + extra))
        if k == "inst":
            p = self.parts[ref.split("__")[0]]
            return (p.get("instance_requires") or {}).get(ref, p["requires_removed"])
        return []

    def closure(self, refs) -> set[str]:
        """Removed set: instance ids and detached assembly ids."""
        out: set[str] = set()
        stack = list(refs)
        while stack:
            r = stack.pop()
            k = self.kind(r)
            if k == "part":
                # declared instances (independent of what is modelled yet)
                new = [i for i in self.parts[r]["instances"] if i not in out]
                out.update(new)
                if new:
                    stack.extend(self.requires(r))
            elif k == "inst":
                if r not in out:
                    out.add(r)
                    stack.extend(self.requires(r))
            elif k == "asm":
                if r not in out:
                    out.add(r)
                    stack.extend(self.requires(r))
        return out

    @staticmethod
    def chain(asm_id: str) -> list[str]:
        parts = asm_id.split(".")
        return [".".join(parts[: i + 1]) for i in range(len(parts))]

    def context(self, unit: str, removed: set[str]):
        """(moving instances, present instances) for removing `unit` given `removed`."""
        if self.kind(unit) == "asm":
            own_chain = self.chain(unit)[:-1]
            moving_all = self.expand(unit)
        else:
            own_chain = self.chain(self.inst_asm[unit]) if unit in self.inst_asm else []
            moving_all = [unit]
        detached = {r for r in removed if r in self.asm}
        bench = [a for a in own_chain if a in detached]
        scope = bench[-1] if bench else None

        def gone(i):
            if i in removed:
                return True
            for a in self.chain(self.inst_asm[i]):
                if a in detached and a not in own_chain:
                    return True
            return False

        moving = [i for i in moving_all if not gone(i)]
        mset = set(moving)
        present = []
        for i, a in self.inst_asm.items():
            if i in mset or gone(i):
                continue
            if scope and not (a == scope or a.startswith(scope + ".")):
                continue
            present.append(i)
        moving_parts = {self.inst[i]["part"] for i in moving}
        carried = {i for i in present if self.parts[self.inst[i]["part"]].get("carrier") in moving_parts}
        if self.kind(unit) == "inst":
            car = self.parts[unit.split("__")[0]].get("carrier")
            if car:
                carried |= set(self.part_instances.get(car, []))
        present = [i for i in present if i not in carried]  # carriers and parts riding on the moving part
        return moving, present

    def travel(self, unit: str, removed=()) -> tuple[np.ndarray, float]:
        """Axis and length of the way a part or assembly travels when it is removed.
        removal_mm sets the way while the unit still sits on the machine (e.g. the shower
        screen above the drip tray). Once an assembly above it is detached - it lies on the
        bench - the unit travels the full explode distance, so that it comes to rest where
        the exploded view puts it. Same rule as web/src/logic/explode.ts."""
        if self.kind(unit) == "asm":
            e = self.manifest["assemblies"][unit]["explode"]
            above = self.chain(unit)[:-1]
        else:
            e = self.inst[unit]["explode"]
            above = self.chain(self.inst_asm[unit])
        on_bench = any(a in removed for a in above)
        dist = e["distance_mm"] if on_bench else e.get("removal_mm", e["distance_mm"])
        return np.array(e["axis"], float), float(dist)

    def display_offsets(self, removed: set[str], moving: list[str]) -> dict[str, np.ndarray]:
        """What the viewer shows at the end of a procedure step (removalDisplay in
        web/src/logic/explode.ts): detached assemblies lie at their offset ("bench"), the
        units of this step have moved out, parts removed earlier are hidden (not in the result)."""
        mset = set(moving)
        gone = set(removed) | mset
        out = {}
        for i in self.inst:
            if i in removed and i not in mset:
                continue
            o = np.zeros(3)
            for a in self.chain(self.inst_asm[i]):
                if a in self.asm and a in gone:
                    axis, dist = self.travel(a, gone)
                    o = o + axis * dist
            if i in mset:
                axis, dist = self.travel(i, gone)
                o = o + axis * dist
            out[i] = o
        return out

    def overlaps_at(self, off: dict[str, np.ndarray], skip=()):
        """Pairs of instances that overlap when each is moved by its offset. Pairs with the
        same offset keep their assembled relation (check 3) and are left out. Yields
        (a, b, volume) with volume None where the intersection cannot be computed."""
        import fcl
        import trimesh

        ids = list(off)
        bbs = {i: self.bbox(i) + off[i] for i in ids}
        req = fcl.CollisionRequest()
        for a_i, a in enumerate(ids):
            for b in ids[a_i + 1 :]:
                if frozenset((a, b)) in skip or np.allclose(off[a], off[b], atol=1e-6):
                    continue
                A, B = bbs[a], bbs[b]
                if np.any(A[1] < B[0]) or np.any(A[0] > B[1]):
                    continue
                o1 = fcl.CollisionObject(self.bvh(a, True), fcl.Transform(off[a]))
                o2 = fcl.CollisionObject(self.bvh(b, True), fcl.Transform(off[b]))
                if not fcl.collide(o1, o2, req, fcl.CollisionResult()):
                    continue
                ma = trimesh.Trimesh(self.meshes[f"{a}__v"] + off[a], self.meshes[f"{a}__f"])
                mb = trimesh.Trimesh(self.meshes[f"{b}__v"] + off[b], self.meshes[f"{b}__f"])
                try:
                    inter = trimesh.boolean.intersection([ma, mb], engine="manifold")
                    vol = float(inter.volume) if len(inter.faces) else 0.0
                    area = float(inter.area) if len(inter.faces) else 1.0
                except Exception:  # noqa: BLE001
                    yield a, b, None
                    continue
                if 2 * vol / max(area, 1e-9) > INTERFERENCE_THICKNESS and vol > 0.5:
                    yield a, b, vol

    def explode_stages(self) -> int:
        es = [v["explode"] for v in self.inst.values()] + [v["explode"] for v in self.manifest["assemblies"].values()]
        return max([1] + [int(e["stage"]) for e in es])

    def explode_offsets(self, t: float) -> dict[str, np.ndarray]:
        """Offsets (mm, world) of the exploded view at t in [0, 1]. Same rule as
        web/src/logic/explode.ts: the assemblies along the chain, then the part itself,
        each opening during its stage."""
        n = self.explode_stages()

        def factor(stage):
            x = min(1.0, max(0.0, t * n - (stage - 1)))
            return x * x * (3 - 2 * x)

        out = {}
        for i, v in self.inst.items():
            o = np.zeros(3)
            for a in self.chain(v["assembly"]):
                e = self.manifest["assemblies"].get(a, {}).get("explode")
                if e:
                    o += np.array(e["axis"], float) * e["distance_mm"] * factor(e["stage"])
            e = v["explode"]
            out[i] = o + np.array(e["axis"], float) * e["distance_mm"] * factor(e["stage"])
        return out

    # collision --------------------------------------------------------------
    def bvh(self, iid: str, shrunk: bool):
        import fcl
        import trimesh

        cache = self._bvh_shrunk if shrunk else self._bvh
        if iid not in cache:
            v = self.meshes[f"{iid}__v"]
            f = self.meshes[f"{iid}__f"]
            tm = trimesh.Trimesh(v, f, process=True)
            verts = tm.vertices - tm.vertex_normals * SHRINK if shrunk else tm.vertices
            m = fcl.BVHModel()
            m.beginModel(len(verts), len(tm.faces))
            m.addSubModel(np.asarray(verts, float), np.asarray(tm.faces, np.int32))
            m.endModel()
            cache[iid] = m
        return cache[iid]

    def bbox(self, iid):
        return np.array(self.inst[iid]["bbox"], float)

    def path_collisions(self, moving, present, axis, dist):
        """First collision along the straight path, or None."""
        import fcl

        if not moving or dist <= 0:
            return None
        bb_m = np.array([self.bbox(i) for i in moving])
        lo = bb_m[:, 0].min(0)
        hi = bb_m[:, 1].max(0)
        travel = axis * dist
        slo = np.minimum(lo, lo + travel) - 0.01
        shi = np.maximum(hi, hi + travel) + 0.01
        cands = []
        for j in present:
            b = self.bbox(j)
            if np.all(b[1] >= slo) and np.all(b[0] <= shi):
                cands.append(j)
        if not cands:
            return None
        static = {j: fcl.CollisionObject(self.bvh(j, False), fcl.Transform()) for j in cands}
        req = fcl.CollisionRequest()
        n = max(1, int(np.ceil(dist / STEP)))
        for k in range(n + 1):
            t = dist * k / n
            off = axis * t
            for i in moving:
                bi = self.bbox(i) + off
                obj = fcl.CollisionObject(self.bvh(i, True), fcl.Transform(off))
                for j in cands:
                    bj = self.bbox(j)
                    if np.any(bi[1] < bj[0]) or np.any(bi[0] > bj[1]):
                        continue
                    wl = self.overlaps.get(frozenset((i, j)))
                    if wl and (wl.get("scope") in ("path", "both") or t <= wl.get("free_mm", WHITELIST_FREE_TRAVEL)):
                        continue
                    res = fcl.CollisionResult()
                    if fcl.collide(obj, static[j], req, res):
                        return {"moving": i, "hit": j, "travel_mm": round(t, 2)}
        return None


# --------------------------------------------------------------------------- checks


def check_data(ctx: Ctx, rep: Report, D: Dims):
    name = "7 Daten (Referenzen, DAG, Werkzeuge, Maße)"
    rep.ok(name)
    data = ctx.data
    ids = [p["id"] for p in data["parts"]]
    for dup in {i for i in ids if ids.count(i) > 1}:
        rep.add(name, "error", f"doppelte Teile-ID {dup}")
    all_inst = [i for p in data["parts"] for i in p["instances"]]
    for dup in {i for i in all_inst if all_inst.count(i) > 1}:
        rep.add(name, "error", f"doppelte Instanz-ID {dup}")
    tools = {t["id"] for t in data["tools"]}
    for p in data["parts"]:
        pid = p["id"]
        if "__" in pid:
            rep.add(name, "error", f"{pid}: Teile-ID darf kein '__' enthalten")
        for i in p["instances"]:
            if not i.startswith(pid + "__"):
                rep.add(name, "error", f"{pid}: Instanz {i} passt nicht zur Teile-ID")
        if p["assembly"] not in ctx.asm:
            rep.add(name, "error", f"{pid}: Baugruppe {p['assembly']} fehlt in assemblies.yaml")
        for iid in (p.get("instance_requires") or {}):
            if iid not in p["instances"]:
                rep.add(name, "error", f"{pid}: instance_requires für unbekannte Instanz {iid}")
        for r in p["requires_removed"] + [x for v in (p.get("instance_requires") or {}).values() for x in v] + ([p["carrier"]] if p.get("carrier") else []):
            if ctx.kind(r) == "unknown":
                rep.add(name, "error", f"{pid}: Referenz {r} unbekannt")
        for t in p.get("tools", []):
            if t not in tools:
                rep.add(name, "error", f"{pid}: Werkzeug {t} fehlt in tools.yaml")
        keys = list(p.get("dims", [])) + [v for k, v in (p.get("spec") or {}).items() if k != "type" and isinstance(v, str)]
        for k in keys:
            if k not in D:
                rep.add(name, "error", f"{pid}: Maß '{k}' fehlt in dimensions.yaml")
        if p["kind"] == "seal" and p["status"] != "planned" and not p.get("dims"):
            rep.add(name, "warn", f"{pid}: Dichtung ohne Maßangabe (dims)")
        for iid in (p.get("instance_explode") or {}):
            if iid not in p["instances"]:
                rep.add(name, "error", f"{pid}: instance_explode für unbekannte Instanz {iid}")
    for a in data["assemblies"]:
        par = a["id"].rpartition(".")[0]
        if par and par not in ctx.asm:
            rep.add(name, "error", f"Baugruppe {a['id']}: Eltern {par} fehlt")
        for r in a.get("requires_removed", []):
            if ctx.kind(r) == "unknown":
                rep.add(name, "error", f"Baugruppe {a['id']}: Referenz {r} unbekannt")
    # DAG
    graph = {p["id"]: [r.split("__")[0] if ctx.kind(r) == "inst" else r for r in p["requires_removed"]] for p in data["parts"]}
    graph.update({a["id"]: a.get("requires_removed", []) for a in data["assemblies"]})
    state = {}

    def visit(n, path):
        if state.get(n) == 1:
            rep.add(name, "error", f"Zyklus in requires_removed: {' -> '.join(path + [n])}")
            return
        if state.get(n) == 2:
            return
        state[n] = 1
        for m in graph.get(n, []):
            visit(m, path + [n])
        state[n] = 2

    for n in graph:
        visit(n, [])
    for k in D.keys():
        try:
            D.get(k)
        except Exception as e:  # noqa: BLE001
            rep.add(name, "error", f"Maß {k}: {e}")
    rep.ok(name, f"{len(data['parts'])} Positionen, {len(all_inst)} Instanzen, {len(data['assemblies'])} Baugruppen, {len(list(D.keys()))} Maße")
    lo, hi = BOILER_OD_RANGE
    if not lo <= D.boiler_od <= hi:
        rep.add(name, "warn", f"boiler_od {D.boiler_od:.1f} mm liegt außerhalb des geprüften Bereichs {lo:.0f}-{hi:.0f} mm: "
                              "Foto-Proportionen und Katalogteile passen dann nicht mehr zusammen. Weitere Maße messen und eintragen "
                              "(reference/measurements.md A2-A5: Basis, Achsabstand, Höhen).")
    planned = [p["id"] for p in data["parts"] if p["status"] == "planned" and not p.get("optional")]
    for p in data["parts"]:
        if p.get("optional") and p["status"] != "planned":
            rep.add(name, "error", f"{p['id']}: optional (nicht verbaut), darf nicht gebaut werden")
    by_status = defaultdict(int)
    for p in data["parts"]:
        by_status[p["status"]] += 1
    rep.ok(name, "Status: " + ", ".join(f"{k} {v}" for k, v in sorted(by_status.items())))
    return planned


def check_reconcile(ctx: Ctx, rep: Report, stats: dict):
    name = "1 Abgleich Stückliste <-> optimiertes GLB"
    rep.ok(name)
    import re

    pat = re.compile(r"^[px][0-9]{3}_[a-z0-9_]+__[0-9]+$")
    glb = {n for n in stats["nodes"] if pat.match(n)}
    expected = {i for p in ctx.data["parts"] if p["status"] != "planned" for i in p["instances"]}
    for i in sorted(expected - glb):
        rep.add(name, "error", f"Instanz {i} fehlt im GLB")
    for i in sorted(glb - expected):
        rep.add(name, "error", f"GLB-Knoten {i} steht nicht (oder als planned) in parts.yaml")
    rep.ok(name, f"{len(glb)} Instanz-Knoten im GLB, {len(expected)} erwartet")


def check_solids(ctx: Ctx, rep: Report):
    name = "2 Gültigkeit der Solids"
    rep.ok(name)
    for i, v in ctx.inst.items():
        if not v["valid"]:
            rep.add(name, "error", f"{i}: ungültiger Solid")
        if not v["closed"]:
            rep.add(name, "error", f"{i}: nicht geschlossen")
        if v["volume"] <= 0:
            rep.add(name, "error", f"{i}: Volumen {v['volume']}")
    rep.ok(name, f"{len(ctx.inst)} Solids geprüft")


def check_interference(ctx: Ctx, rep: Report):
    import fcl
    import trimesh

    name = "3 Durchdringung"
    rep.ok(name)
    ids = list(ctx.inst)
    bbs = {i: ctx.bbox(i) for i in ids}
    req = fcl.CollisionRequest()
    seen_whitelist = set()
    n_pairs = 0
    for a_i in range(len(ids)):
        a = ids[a_i]
        for b in ids[a_i + 1 :]:
            A, B = bbs[a], bbs[b]
            if np.any(A[1] < B[0]) or np.any(A[0] > B[1]):
                continue
            n_pairs += 1
            o1 = fcl.CollisionObject(ctx.bvh(a, True), fcl.Transform())
            o2 = fcl.CollisionObject(ctx.bvh(b, True), fcl.Transform())
            if not fcl.collide(o1, o2, req, fcl.CollisionResult()):
                continue
            ma = trimesh.Trimesh(ctx.meshes[f"{a}__v"], ctx.meshes[f"{a}__f"])
            mb = trimesh.Trimesh(ctx.meshes[f"{b}__v"], ctx.meshes[f"{b}__f"])
            try:
                inter = trimesh.boolean.intersection([ma, mb], engine="manifold")
                vol = float(inter.volume) if len(inter.faces) else 0.0
                area = float(inter.area) if len(inter.faces) else 1.0
            except Exception as e:  # noqa: BLE001
                rep.add(name, "warn", f"{a} x {b}: Schnittvolumen nicht berechenbar ({e})")
                continue
            thick = 2 * vol / max(area, 1e-9)
            key = frozenset((a, b))
            wl = ctx.overlaps.get(key)
            if wl and wl.get("scope") == "path":
                wl = None
            if wl:
                seen_whitelist.add(key)
                if vol > wl["max_mm3"]:
                    rep.add(name, "error", f"{a} x {b}: {vol:.1f} mm³ > Whitelist {wl['max_mm3']} mm³ ({wl['reason']})")
                else:
                    rep.ok(name, f"{a} x {b}: {vol:.1f} mm³ erlaubt ({wl['reason']})")
                continue
            if thick > INTERFERENCE_THICKNESS and vol > 0.5:
                rep.add(name, "error", f"{a} x {b}: Überdeckung {vol:.1f} mm³ (mittlere Dicke {thick:.2f} mm)")
    used = {id(ctx.overlaps[k]) for k in seen_whitelist}
    for o in ctx.data["overlaps"]:
        if o.get("scope") == "path" or id(o) in used:
            continue
        if any(all(k in ctx.inst for k in key) for key, w in ctx.overlaps.items() if w is o):
            rep.add(name, "warn", f"Whitelist-Eintrag ohne Überdeckung: {o['a']} x {o['b']} ({o['reason']})")
    rep.ok(name, f"{n_pairs} Paare mit überlappender Bounding-Box geprüft")


def check_paths(ctx: Ctx, rep: Report):
    name = "4 Ausbaupfade (requires_removed)"
    rep.ok(name)
    n = 0
    units = [(a, "asm") for a, v in ctx.asm.items() if v["detachable"]]
    for p in ctx.data["parts"]:
        for i in ctx.part_instances[p["id"]]:
            units.append((i, "inst"))
    for unit, kind in units:
        reqs = ctx.requires(unit)
        removed = ctx.closure(reqs)
        removed.discard(unit)
        axis, dist = ctx.travel(unit, removed)
        if dist <= 0:
            continue
        moving, present = ctx.context(unit, removed)
        hit = ctx.path_collisions(moving, present, axis, dist)
        n += 1
        if hit:
            rep.add(name, "error", f"{unit}: kollidiert bei {hit['travel_mm']} mm mit {hit['hit']} (bewegt: {hit['moving']}); requires_removed unvollständig oder Achse falsch")
    rep.ok(name, f"{n} Ausbaupfade geprüft")


def check_envelope(ctx: Ctx, rep: Report, strict: bool):
    name = "5 Hüllmaß (ohne Hebel und Siebträgergriff)"
    rep.ok(name)
    ids = [i for i in ctx.inst if not i.startswith(ENVELOPE_EXCLUDE)]
    if not ids:
        rep.add(name, "warn", "keine Teile")
        return
    b = np.array([ctx.bbox(i) for i in ids])
    lo, hi = b[:, 0].min(0), b[:, 1].max(0)
    size = dict(zip("xyz", hi - lo))
    for ax, (lo, hi) in ENVELOPE.items():
        v = size[ax]
        dev = (v - lo) / lo if v < lo else (v - hi) / hi if v > hi else 0.0
        ref = f"{lo:.0f}" if lo == hi else f"{lo:.0f}-{hi:.0f}"
        msg = f"{ax}: {v:.0f} mm, Katalog {ref} mm ({dev:+.1%})"
        if abs(dev) > ENVELOPE_FAIL:
            rep.add(name, "error" if strict else "warn", msg + (" - Modell unvollständig" if not strict else ""))
        elif abs(dev) > ENVELOPE_TOL:
            rep.add(name, "warn", msg + " - Foto-Proportionen oder Kesseldurchmesser prüfen")
        else:
            rep.ok(name, msg)


def check_budgets(rep: Report, stats: dict):
    name = "6 Budgets (GLB)"
    rep.ok(name)
    for k, v, lim in [("Dateigröße", stats["bytes"], BUDGET["bytes"]), ("Dreiecke", stats["triangles"], BUDGET["triangles"]),
                      ("Draw Calls", stats["primitives"], BUDGET["draw_calls"])]:
        msg = f"{k}: {v:,.0f} (Budget {lim:,.0f})"
        rep.add(name, "error", msg) if v > lim else rep.ok(name, msg)


def check_procedures(ctx: Ctx, rep: Report, coverage_strict: bool):
    name = "8 Anleitungen"
    rep.ok(name)
    tools = {t["id"] for t in ctx.data["tools"]}
    views = set(ctx.data["views"].get("views", {}))
    sections = set(ctx.data["views"].get("sections", {}))
    covered = set()
    for proc in ctx.data["procedures"]:
        pid = proc["id"]
        for t in proc["tools"]:
            if t not in tools:
                rep.add(name, "error", f"{pid}: Werkzeug {t} unbekannt")
        removed = ctx.closure(proc.get("start_removed", []))
        n_moves = 0
        for st in proc["steps"]:
            before = set(removed)
            step_units = []
            for t in st.get("tools", []):
                if t not in tools:
                    rep.add(name, "error", f"{pid}/{st['id']}: Werkzeug {t} unbekannt")
            if st.get("camera") and st["camera"] not in views:
                rep.add(name, "error", f"{pid}/{st['id']}: Ansicht {st['camera']} unbekannt")
            if st.get("section") and st["section"] not in sections:
                rep.add(name, "error", f"{pid}/{st['id']}: Schnitt {st['section']} unbekannt")
            for r in st.get("highlight", []):
                if ctx.kind(r) == "unknown":
                    rep.add(name, "error", f"{pid}/{st['id']}: highlight {r} unbekannt")
            for r in st.get("remove", []):
                k = ctx.kind(r)
                if k == "unknown":
                    rep.add(name, "error", f"{pid}/{st['id']}: Teil/Baugruppe {r} unbekannt")
                    continue
                covered.add(r.split("__")[0] if k == "inst" else r)
                if k == "asm":
                    covered.update(p for p, q in ctx.parts.items() if q["assembly"] == r or q["assembly"].startswith(r + "."))
                need = ctx.closure(ctx.requires(r))
                missing = sorted(need - removed - {r})
                if missing:
                    rep.add(name, "error", f"{pid}/{st['id']}: {r} ausgebaut, aber noch nicht entfernt: {', '.join(missing[:6])}")
                units = [r] if k == "asm" else ([r] if r in ctx.inst else []) if k == "inst" else ctx.part_instances[r]
                step_units.extend(units)
                for u in units:
                    axis, dist = ctx.travel(u, removed)
                    moving, present = ctx.context(u, removed)
                    hit = ctx.path_collisions(moving, present, axis, dist)
                    n_moves += 1
                    if hit:
                        rep.add(name, "error", f"{pid}/{st['id']}: {u} kollidiert bei {hit['travel_mm']} mm mit {hit['hit']}")
                    removed.add(u)
                if k == "inst":
                    removed.add(r)
                if k == "part":
                    removed.update(ctx.parts[r]["instances"])
            # what lies on the "bench" at the end of the step must not overlap either
            for a, b, vol in ctx.overlaps_at(ctx.display_offsets(before, step_units)):
                how = "Schnittvolumen nicht berechenbar" if vol is None else f"{vol:.1f} mm³"
                rep.add(name, "error", f"{pid}/{st['id']}: {a} x {b} überdecken sich am Ende des Schritts ({how}) - Ausbauweg/Ablage (removal_mm) anpassen")
        rep.ok(name, f"{pid}: {len(proc['steps'])} Schritte, {n_moves} Bewegungen vorwärts kollisionsfrei geprüft (rückwärts = gleiche Pfade), Ablage ohne Überdeckung")
    wear = [p["id"] for p in ctx.data["parts"] if p["wear_part"] and p["status"] != "planned"]
    for w in wear:
        if w not in covered:
            rep.add(name, "error" if coverage_strict else "warn", f"Verschleißteil {w} kommt in keiner Anleitung vor")


def check_proportions(ctx: Ctx, rep: Report, D: Dims):
    name = "9 Proportionen (PLAN 8.2)"
    rep.ok(name)
    res = evaluate(ctx.data["proportions"], ctx.manifest, D.boiler_od, ctx.meshes)
    for r in res:
        if r["status"] == "skip":
            rep.add(name, "warn", f"{r['name']}: übersprungen ({r['reason']})")
        elif r["status"] == "fail":
            rep.add(name, "error", f"{r['name']}: {r['value']} mm, Soll {r['target_mm']} mm ({r['dev']:+.1%})")
        elif r["status"] == "advisory":
            rep.add(name, "warn", f"{r['name']}: Katalogmaß {r['value']} mm gegen Foto-Verhältnis {r['target_mm']} mm ({r['dev']:+.1%}) - eines von beiden stimmt nicht, messen")
        else:
            rep.ok(name, f"{r['name']}: {r['value']} mm, Soll {r['target_mm']} mm ({r['dev']:+.1%})")


def check_explode(ctx: Ctx, rep: Report):
    """The exploded view must not put parts into each other: coincident faces of two parts
    flicker in the viewer (the shower screen used to end up around the piston sleeve, both
    dia. 50). Checked where the slider comes to rest, at the end of every stage."""
    name = "10 Explosionsansicht (keine Überdeckung am Ende jeder Stufe)"
    rep.ok(name)
    n = ctx.explode_stages()
    found: set[frozenset] = set()
    for k in range(1, n + 1):
        for a, b, vol in ctx.overlaps_at(ctx.explode_offsets(k / n), skip=found):
            found.add(frozenset((a, b)))
            how = "Schnittvolumen nicht berechenbar" if vol is None else f"{vol:.1f} mm³"
            rep.add(name, "error", f"{a} x {b}: überdecken sich ab Stufe {k} ({how}) - explode-Wege staffeln")
    rep.ok(name, f"{n} Stufen geprüft")


def geometry_report(data: dict, instances: dict, assemblies: dict, meshes: dict) -> Report:
    """Solids, interference, removal paths, procedures and the exploded view for a model held in memory
    (see export.collect). Used to check variants, e.g. other boiler diameters."""
    rep = Report()
    ctx = Ctx(data, {"instances": instances, "assemblies": assemblies}, meshes)
    check_solids(ctx, rep)
    check_interference(ctx, rep)
    check_paths(ctx, rep)
    check_procedures(ctx, rep, coverage_strict=False)
    check_explode(ctx, rep)
    return rep


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-geometry", action="store_true", help="nur Daten und Anleitungen")
    args = ap.parse_args(argv)
    t0 = time.time()
    data = load_all()
    D = Dims(data["dimensions"])
    rep = Report()
    manifest = json.loads(MANIFEST.read_text())
    meshes = dict(np.load(MANIFEST.parent / "meshes.npz"))
    ctx = Ctx(data, manifest, meshes)
    planned = check_data(ctx, rep, D)
    complete = not planned
    if not complete:
        print(f"Hinweis: Modell unvollständig ({len(planned)} Positionen noch 'planned') - Hüllmaß und Abdeckung nur als Warnung")
    stats = glb_stats(WEB_MODEL)
    check_reconcile(ctx, rep, stats)
    check_solids(ctx, rep)
    if not args.skip_geometry:
        check_interference(ctx, rep)
        check_paths(ctx, rep)
    check_envelope(ctx, rep, strict=complete)
    check_budgets(rep, stats)
    check_procedures(ctx, rep, coverage_strict=complete and len(data["procedures"]) >= 11)
    check_proportions(ctx, rep, D)
    if not args.skip_geometry:
        check_explode(ctx, rep)
    rep.print()
    REPORT.write_text(json.dumps({"time_s": round(time.time() - t0, 1), "checks": rep.checks}, indent=1, ensure_ascii=False))
    print(f"validate: {rep.n_errors} Fehler, {time.time() - t0:.1f} s -> {REPORT.relative_to(REPORT.parents[1])}")
    return 1 if rep.n_errors else 0


if __name__ == "__main__":
    sys.exit(main())
