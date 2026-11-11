"""Build the model and export GLB (raw), STEP, manifest.json and collision meshes.

GLB hierarchy: pavoni -> <top-level assembly> -> <instance id>. The raw GLB has
one primitive per B-rep face; web/scripts/optimize-glb.mjs merges them per
instance node (PLAN 3.3). Coordinates: CAD mm Z-up; GLB m Y-up,
gl = (x, z, -y) / 1000.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time

import numpy as np
from build123d import Compound, Shape, Unit, export_gltf, export_step
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.gp import gp_Vec

from .assembly import build_model
from .meshing import extract, mesh_solid
from .paths import BUILD, MANIFEST, RAW_GLB, STEP

LARGE_CHROME = {"chrome", "stainless", "brass", "glass", "plastic_clear"}


def mesh_params(part: dict, solid) -> tuple[float, float]:
    """Tessellation per part (PLAN 6.4): big chrome surfaces fine, small parts coarse."""
    diag = solid.bounding_box().diagonal
    shiny = part["material"] in LARGE_CHROME
    if shiny and diag > 120:
        return 0.03, 0.07
    if shiny and diag > 50:
        return 0.04, 0.14
    if diag > 40:
        return 0.06, 0.25
    return 0.05, 0.3


def world_axis(loc, axis) -> list[float]:
    v = gp_Vec(*axis).Transformed(loc.wrapped.Transformation())
    n = (v.X() ** 2 + v.Y() ** 2 + v.Z() ** 2) ** 0.5 or 1.0
    return [round(v.X() / n, 6), round(v.Y() / n, 6), round(v.Z() / n, 6)]


def git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return "unknown"


def main() -> int:
    t0 = time.time()
    m = build_model()
    t_build = time.time() - t0
    BUILD.mkdir(parents=True, exist_ok=True)
    parts = m.parts
    asm = {a["id"]: a for a in m.data["assemblies"]}

    instances = {}
    meshes = {}
    groups: dict[str, list] = {}
    for iid, s in m.solids.items():
        pid = m.part_of[iid]
        p = parts[pid]
        bb = s.bounding_box()
        ex = (p.get("instance_explode") or {}).get(iid, p["explode"])
        loc = m.T.frame(p["assembly"])
        instances[iid] = {
            "part": pid,
            "assembly": p["assembly"],
            "bbox": [[round(bb.min.X, 3), round(bb.min.Y, 3), round(bb.min.Z, 3)], [round(bb.max.X, 3), round(bb.max.Y, 3), round(bb.max.Z, 3)]],
            "center": [round(c, 3) for c in (bb.center().X, bb.center().Y, bb.center().Z)],
            "volume": round(s.volume, 3),
            "valid": bool(BRepCheck_Analyzer(s.wrapped).IsValid()),
            "closed": all(sh.is_closed for sh in s.shells()) if hasattr(s.shells()[0], "is_closed") else True,
            "n_faces": len(s.faces()),
            "explode": {"axis": world_axis(loc, ex["axis"]), "distance_mm": ex["distance_mm"], "stage": ex["stage"]},
        }
        # NB: bounding_box()/volume clear OCC triangulations, so mesh last.
        lin, ang = mesh_params(p, s)
        mesh_solid(s, lin, ang)
        verts, tris = extract(s)
        meshes[f"{iid}__v"] = verts.astype(np.float64)
        meshes[f"{iid}__f"] = tris.astype(np.int32)
        s.label = iid
        groups.setdefault(p["assembly"].split(".")[0], []).append(s)

    assemblies = {}
    for aid, a in asm.items():
        parent = aid.rpartition(".")[0] or None
        loc = m.T.frame(parent or aid) if parent else m.T.frame(aid)
        assemblies[aid] = {
            "parent": parent,
            "detachable": a["detachable"],
            "explode": {"axis": world_axis(loc, a["explode"]["axis"]), "distance_mm": a["explode"]["distance_mm"], "stage": a["explode"]["stage"]},
        }

    children = []
    for top, solids in groups.items():
        c = Compound(children=solids)
        c.label = top
        children.append(c)
    root = Compound(children=children)
    root.label = "pavoni"

    t1 = time.time()
    # Keep our per-part tessellation: build123d's export_gltf would re-mesh every
    # node with one global deflection, so its mesh() call is disabled here.
    orig_mesh = Shape.mesh
    Shape.mesh = lambda self, *a, **k: None
    try:
        export_gltf(root, str(RAW_GLB), unit=Unit.MM, binary=True)
    finally:
        Shape.mesh = orig_mesh
    t_gltf = time.time() - t1
    t1 = time.time()
    export_step(root, str(STEP))
    t_step = time.time() - t1
    np.savez_compressed(BUILD / "meshes.npz", **meshes)

    manifest = {
        "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "git": git_sha(),
        "machine": m.D.machine,
        "units": "CAD: mm, Z up, -Y front, +X right. GLB: m, Y up; gl = (x, z, -y) / 1000",
        "instances": instances,
        "assemblies": assemblies,
        "dims": m.D.all_entries(),
        "timings": {"build_s": round(t_build, 1), "gltf_s": round(t_gltf, 1), "step_s": round(t_step, 1), "modules": m.timings},
    }
    MANIFEST.write_text(json.dumps(manifest, indent=1, ensure_ascii=False))
    print(f"export: {len(instances)} Instanzen, build {t_build:.1f}s, glb {t_gltf:.1f}s, step {t_step:.1f}s -> {RAW_GLB.name}, {STEP.name}, {MANIFEST.name}")
    bad = [i for i, v in instances.items() if not v["valid"]]
    if bad:
        print("WARNUNG ungültige Solids:", ", ".join(bad))
    return 0


if __name__ == "__main__":
    sys.exit(main())
