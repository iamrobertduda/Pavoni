"""Evaluate photo proportions (PLAN 8.2, data/proportions.yaml) on the built model."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BB:
    x0: float
    y0: float
    z0: float
    x1: float
    y1: float
    z1: float

    @property
    def dx(self):
        return self.x1 - self.x0

    @property
    def dy(self):
        return self.y1 - self.y0

    @property
    def dz(self):
        return self.z1 - self.z0

    @property
    def cx(self):
        return (self.x0 + self.x1) / 2

    @property
    def cy(self):
        return (self.y0 + self.y1) / 2

    @property
    def cz(self):
        return (self.z0 + self.z1) / 2


class Missing(Exception):
    pass


def make_env(manifest: dict, D: float, meshes: dict | None = None) -> dict:
    inst = manifest["instances"]
    datums = manifest.get("datums", {})

    def datum(name):
        v = datums[name]
        return float(v)

    def slice_extent(iid, normal_axis, value, measure_axis):
        """Extent of the mesh section (plane normal_axis = value) along measure_axis."""
        import numpy as np
        import trimesh

        if meshes is None or f"{iid}__v" not in meshes:
            raise Missing(iid)
        ax = "xyz".index(normal_axis)
        n = [0.0, 0.0, 0.0]
        n[ax] = 1.0
        o = [0.0, 0.0, 0.0]
        o[ax] = value
        tm = trimesh.Trimesh(meshes[f"{iid}__v"], meshes[f"{iid}__f"], process=False)
        sec = trimesh.intersections.mesh_plane(tm, n, o)
        if len(sec) == 0:
            raise Missing(f"{iid} @ {normal_axis}={value}")
        pts = np.asarray(sec).reshape(-1, 3)[:, "xyz".index(measure_axis)]
        return float(pts.max() - pts.min())

    def bbox(*ids):
        boxes = []
        for i in ids:
            if i not in inst:
                raise Missing(i)
            (a, b) = inst[i]["bbox"]
            boxes.append((a, b))
        return BB(min(b[0][0] for b in boxes), min(b[0][1] for b in boxes), min(b[0][2] for b in boxes),
                  max(b[1][0] for b in boxes), max(b[1][1] for b in boxes), max(b[1][2] for b in boxes))

    def part_bbox(prefix):
        ids = [i for i in inst if i.startswith(prefix)]
        if not ids:
            raise Missing(prefix)
        return bbox(*ids)

    def all_bbox(exclude=()):
        ids = [i for i in inst if not any(i.startswith(e) for e in exclude)]
        return bbox(*ids)

    import math

    return {"bbox": bbox, "part_bbox": part_bbox, "all_bbox": all_bbox, "datum": datum, "slice_extent": slice_extent,
            "D": D, "abs": abs, "max": max, "min": min, "hypot": math.hypot}


def evaluate(entries: list[dict], manifest: dict, D: float, meshes: dict | None = None) -> list[dict]:
    env = make_env(manifest, D, meshes)
    out = []
    for e in entries:
        tgt = e["target"] * (D / 100.0 if e.get("scale_with_d", True) else 1.0)
        tol = e.get("tolerance", 0.10)
        try:
            val = float(eval(e["measure"], {"__builtins__": {}}, env))  # noqa: S307 - restricted env
        except Missing as m:
            out.append({**e, "status": "skip", "reason": f"Instanz fehlt: {m}"})
            continue
        dev = (val - tgt) / tgt if tgt else 0.0
        out.append({**e, "value": round(val, 2), "target_mm": round(tgt, 2), "dev": round(dev, 4),
                    "status": "ok" if abs(dev) <= tol else "fail"})
    return out
