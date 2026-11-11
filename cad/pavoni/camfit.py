"""Fit pinhole cameras to the owner's reference photos from point correspondences.

Unknowns per photo: camera position (3), yaw, pitch (no roll), vertical field of view.
Prints residuals and a views.yaml entry. Usage: python -m pavoni.camfit [--write]"""
from __future__ import annotations

import json
import math
import sys

import numpy as np
import yaml
from scipy.optimize import least_squares

from .paths import DATA, MANIFEST

PHONE_FOV = 67.0  # vertical field of view of a 26-mm-equivalent phone camera, portrait 4:3


def basis(yaw, pitch):
    f = np.array([math.cos(pitch) * math.cos(yaw), math.cos(pitch) * math.sin(yaw), math.sin(pitch)])
    up = np.array([0.0, 0.0, 1.0])
    r = np.cross(f, up)
    r /= np.linalg.norm(r)
    u = np.cross(r, f)
    return f, r, u


def project(params, P, W, H):
    cx, cy, cz, yaw, pitch, fov = params
    f, r, u = basis(yaw, pitch)
    d = P - np.array([cx, cy, cz])
    z = d @ f
    fy = (H / 2) / math.tan(fov / 2)
    return np.stack([W / 2 + (d @ r) / z * fy, H / 2 - (d @ u) / z * fy], axis=1)


def main(argv=None):
    write = "--write" in (argv or sys.argv[1:])
    man = json.loads(MANIFEST.read_text())
    dims = {k: v["resolved"] for k, v in man["dims"].items()}
    datums = man["datums"]
    env = {"datum": lambda n: datums[n], "dim": lambda n: dims[n], "__builtins__": {}}
    spec = yaml.safe_load((DATA / "photo_points.yaml").read_text())
    views = yaml.safe_load((DATA / "views.yaml").read_text())
    out = {}
    for photo, s in spec.items():
        W, H = s["size"]
        P = np.array([eval(p["p"], env) for p in s["points"]], float)  # noqa: S307 - restricted env
        U = np.array([p["px"] for p in s["points"]], float)
        cen = P.mean(0)
        # start: 600 mm away in the direction implied by the photo name
        vname = next(k for k, v in views["views"].items() if v.get("photo") == photo)
        v0 = views["views"][vname]
        c0 = np.array(v0["position"], float)
        dvec = np.array(v0["target"], float) - c0
        yaw0 = math.atan2(dvec[1], dvec[0])
        pitch0 = math.atan2(dvec[2], math.hypot(dvec[0], dvec[1]))
        x0 = [*c0, yaw0, pitch0, math.radians(v0.get("fov", 50))]

        fov_fixed = math.radians(s.get("fov", PHONE_FOV))

        def res(x6):
            return (project(x6, P, W, H) - U).ravel()

        def res5(x5):
            return res([*x5, fov_fixed])

        sol5 = least_squares(res5, x0[:5], bounds=([-3000, -3000, -500, -10, -1.5], [3000, 3000, 3000, 10, 1.5]))

        class _S:
            pass

        sol = _S()
        sol.x = [*sol5.x, fov_fixed]
        r = res(sol.x).reshape(-1, 2)
        err = np.linalg.norm(r, axis=1)
        cx, cy, cz, yaw, pitch, fov = sol.x
        f, _, _ = basis(yaw, pitch)
        pos = np.array([cx, cy, cz])
        dist = float(np.linalg.norm(cen - pos))
        target = pos + f * dist
        print(f"{photo}: RMS {math.sqrt((err ** 2).mean()):.1f} px, Kamera {pos.round(0).tolist()} mm, fov {math.degrees(fov):.1f}°, Abstand {dist:.0f} mm")
        for p, e in zip(s["points"], err):
            print(f"   {e:6.1f} px  {p['name']}")
        out[vname] = {"position": [round(float(c), 1) for c in pos], "target": [round(float(c), 1) for c in target], "fov": round(math.degrees(fov), 2)}
    if write:
        txt = (DATA / "views.yaml").read_text()
        for vname, v in out.items():
            import re

            pat = re.compile(rf"^  {vname}: \{{.*\}}$", re.M)
            label = views["views"][vname]["label"]
            photo = views["views"][vname]["photo"]
            line = f'  {vname}: {{label: "{label}", position: {v["position"]}, target: {v["target"]}, fov: {v["fov"]}, photo: {photo}}}'
            txt = pat.sub(line, txt)
        (DATA / "views.yaml").write_text(txt)
        print("views.yaml aktualisiert")


if __name__ == "__main__":
    main()
