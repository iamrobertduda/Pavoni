"""Explicit OCC tessellation (absolute deflection) and triangle extraction."""
from __future__ import annotations

import numpy as np
from OCP.BRep import BRep_Tool
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.TopAbs import TopAbs_REVERSED
from OCP.TopLoc import TopLoc_Location


def mesh_solid(solid, lin: float, ang: float, min_size: float = 0.1) -> None:
    """Absolute linear deflection (mm) and angular deflection (rad)."""
    from OCP.BRepTools import BRepTools
    from OCP.IMeshTools import IMeshTools_Parameters

    BRepTools.Clean_s(solid.wrapped)
    p = IMeshTools_Parameters()
    p.Deflection = lin
    p.Angle = ang
    p.Relative = False
    p.InParallel = True
    p.DeflectionInterior = max(lin, 0.5)
    p.AngleInterior = max(ang, 0.5)
    p.ControlSurfaceDeflection = False
    p.MinSize = min_size
    BRepMesh_IncrementalMesh(solid.wrapped, p)


def extract(solid) -> tuple[np.ndarray, np.ndarray]:
    """Vertices (N,3) and triangles (M,3) of the existing triangulation, outward oriented."""
    vs, fs, off = [], [], 0
    for f in solid.faces():
        loc = TopLoc_Location()
        tri = BRep_Tool.Triangulation_s(f.wrapped, loc)
        if tri is None:
            continue
        trsf = loc.Transformation()
        n = tri.NbNodes()
        pts = np.empty((n, 3))
        for i in range(1, n + 1):
            p = tri.Node(i).Transformed(trsf)
            pts[i - 1] = (p.X(), p.Y(), p.Z())
        m = tri.NbTriangles()
        t = np.empty((m, 3), dtype=np.int64)
        rev = f.wrapped.Orientation() == TopAbs_REVERSED
        for i in range(1, m + 1):
            a, b, c = tri.Triangle(i).Get()
            t[i - 1] = (a, c, b) if rev else (a, b, c)
        vs.append(pts)
        fs.append(t - 1 + off)
        off += n
    if not vs:
        return np.zeros((0, 3)), np.zeros((0, 3), dtype=np.int64)
    return np.vstack(vs), np.vstack(fs)
