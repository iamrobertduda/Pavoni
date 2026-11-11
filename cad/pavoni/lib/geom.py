"""Geometry helpers on top of build123d.

Revolved profiles are given in (r, z) with optional per-vertex fillet radius:
(r, z) or (r, z, fillet). Fillets are built as tangent arcs directly in the
profile (PLAN 6.2: round edges in the profile instead of OCCT fillets).
"""
from __future__ import annotations

import math
from typing import Iterable, Sequence

from build123d import (
    Axis,
    Edge,
    Face,
    Location,
    Plane,
    Solid,
    Vector,
    Wire,
)

__all__ = [
    "profile_wire",
    "revolve_rz",
    "extrude_xy",
    "place",
    "cyl",
    "tube",
    "box",
    "hex_prism",
    "frame_from_axis",
    "union_all",
    "solid_of",
]


def _v(p) -> Vector:
    return Vector(*p)


def profile_wire(pts: Sequence[Sequence[float]], to3d=lambda a, b: (a, 0.0, b)) -> Wire:
    """Closed wire through 2D points with optional fillet radius per vertex.

    pts: [(a, b) | (a, b, r)], mapped to 3D by to3d (default: XZ plane, a=r, b=z).
    """
    n = len(pts)
    P = [_v(to3d(p[0], p[1])) for p in pts]
    R = [p[2] if len(p) > 2 else 0.0 for p in pts]
    # tangent points per vertex: (t_in, mid, t_out) or None
    corner = []
    for i in range(n):
        r = R[i]
        if r <= 0:
            corner.append(None)
            continue
        A, Pi, B = P[i - 1], P[i], P[(i + 1) % n]
        u1 = (A - Pi).normalized()
        u2 = (B - Pi).normalized()
        cos_t = max(-1.0, min(1.0, u1.dot(u2)))
        theta = math.acos(cos_t)
        if theta < 1e-3 or abs(math.pi - theta) < 1e-3:
            corner.append(None)
            continue
        d = r / math.tan(theta / 2)
        lim = 0.49 * min((A - Pi).length, (B - Pi).length)
        if d > lim:  # clamp radius to available segment length
            d = lim
            r = d * math.tan(theta / 2)
        bis = (u1 + u2).normalized()
        C = Pi + bis * (r / math.sin(theta / 2))
        corner.append((Pi + u1 * d, C - bis * r, Pi + u2 * d))
    edges = []
    for i in range(n):
        j = (i + 1) % n
        start = corner[i][2] if corner[i] else P[i]
        end = corner[j][0] if corner[j] else P[j]
        if (end - start).length > 1e-6:
            edges.append(Edge.make_line(start, end))
        if corner[j]:
            t_in, mid, t_out = corner[j]
            edges.append(Edge.make_three_point_arc(t_in, mid, t_out))
    return Wire(edges)


def revolve_rz(pts: Sequence[Sequence[float]], angle: float = 360.0) -> Solid:
    """Revolve a closed (r, z[, fillet]) profile about the Z axis."""
    face = Face(profile_wire(pts))
    s = Solid.revolve(face, angle, Axis.Z)
    return solid_of(s)


def extrude_xy(pts: Sequence[Sequence[float]], h: float, z0: float = 0.0) -> Solid:
    """Extrude a closed (x, y[, fillet]) outline in +Z by h."""
    w = profile_wire(pts, to3d=lambda a, b: (a, b, z0))
    return solid_of(Solid.extrude(Face(w), Vector(0, 0, h)))


def solid_of(shape) -> Solid:
    """Return a single Solid from a boolean/op result (fails loudly otherwise)."""
    if isinstance(shape, Solid):
        return shape
    solids = shape.solids()
    if len(solids) != 1:
        vols = [round(s.volume, 2) for s in solids]
        if len(solids) > 1:
            # keep the dominant solid, drop slivers from tangent booleans
            solids = sorted(solids, key=lambda s: s.volume, reverse=True)
            if solids[1].volume < 1e-3 * solids[0].volume:
                return solids[0]
        raise ValueError(f"Erwartet genau einen Solid, erhalten {len(solids)} (Volumina {vols})")
    return solids[0]


def cyl(r: float, h: float, z0: float = 0.0) -> Solid:
    return Solid.make_cylinder(r, h, Plane.XY.offset(z0))


def tube(ro: float, ri: float, h: float, z0: float = 0.0) -> Solid:
    return solid_of(cyl(ro, h, z0) - cyl(ri, h + 2, z0 - 1))


def box(dx: float, dy: float, dz: float, center=(0, 0, 0)) -> Solid:
    cx, cy, cz = center
    return Solid.make_box(dx, dy, dz, Plane.XY.offset(0)).moved(Location((cx - dx / 2, cy - dy / 2, cz - dz / 2)))


def hex_prism(af: float, h: float, z0: float = 0.0) -> Solid:
    """Hexagon prism, across-flats af, flats parallel to X."""
    rc = af / math.sqrt(3)  # corner radius
    pts = [(rc * math.cos(math.radians(a)), rc * math.sin(math.radians(a))) for a in range(0, 360, 60)]
    return extrude_xy(pts, h, z0)


def frame_from_axis(origin, z_dir, x_dir=None) -> Location:
    """Location whose local Z is z_dir at origin."""
    z = Vector(*z_dir).normalized()
    if x_dir is None:
        ref = Vector(0, 0, 1) if abs(z.Z) < 0.9 else Vector(1, 0, 0)
        x = ref.cross(z).normalized() if abs(z.Z) < 0.9 else Vector(1, 0, 0)
        # project to be orthogonal
        x = (x - z * x.dot(z)).normalized()
    else:
        x = Vector(*x_dir)
        x = (x - z * x.dot(z)).normalized()
    return Location(Plane(origin=Vector(*origin), x_dir=x, z_dir=z))


def place(shape, origin=(0, 0, 0), z_dir=(0, 0, 1), x_dir=None):
    """Move a shape built along +Z at the origin onto (origin, z_dir)."""
    return shape.moved(frame_from_axis(origin, z_dir, x_dir))


def union_all(shapes: Iterable) -> Solid:
    it = iter(shapes)
    acc = next(it)
    for s in it:
        acc = acc + s
    return solid_of(acc)
