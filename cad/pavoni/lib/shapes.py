"""Shape helpers for cast/sheet parts: outlines, lobed knobs, bent tubes."""
from __future__ import annotations

import math
from typing import Sequence

from build123d import Edge, Face, Plane, Solid, Transition, Vector, Wire, fillet, sweep

from .geom import solid_of

__all__ = ["rounded_rect", "slot_outline", "lobed_outline", "path_wire", "pipe", "try_fillet", "extrude_taper", "lobed_knob", "circle_pts"]


def circle_pts(r: float, n: int = 48, cx: float = 0.0, cy: float = 0.0):
    return [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def rounded_rect(w: float, h: float, r: float, cx: float = 0.0, cy: float = 0.0):
    """Corner points with fillet radius for extrude_xy / profile_wire."""
    r = min(r, 0.49 * min(w, h))
    x0, x1, y0, y1 = cx - w / 2, cx + w / 2, cy - h / 2, cy + h / 2
    return [(x0, y0, r), (x1, y0, r), (x1, y1, r), (x0, y1, r)]


def slot_outline(length: float, width: float, cx=0.0, cy=0.0, n=16):
    """Stadium (obround) along X."""
    r = width / 2
    a = length / 2 - r
    pts = []
    for i in range(n + 1):
        t = -math.pi / 2 + math.pi * i / n
        pts.append((cx + a + r * math.cos(t), cy + r * math.sin(t)))
    for i in range(n + 1):
        t = math.pi / 2 + math.pi * i / n
        pts.append((cx - a + r * math.cos(t), cy + r * math.sin(t)))
    return pts


def lobed_outline(r_out: float, r_in: float, lobes: int, n_per: int = 24):
    """Star/lobed knob outline: smooth alternating lobes (cosine blend)."""
    pts = []
    n = lobes * n_per
    for i in range(n):
        t = 2 * math.pi * i / n
        k = 0.5 * (1 + math.cos(lobes * t))
        k = k ** 0.6
        r = r_in + (r_out - r_in) * k
        pts.append((r * math.cos(t), r * math.sin(t)))
    return pts


def lobed_knob(r_out: float, r_in: float, lobes: int, h: float, z0: float = 0.0, top_round: float = 0.0) -> Solid:
    from build123d import Face as F, Wire as W, Edge as E
    pts = lobed_outline(r_out, r_in, lobes)
    edge = E.make_spline([Vector(x, y, z0) for x, y in pts] + [Vector(pts[0][0], pts[0][1], z0)], periodic=False)
    face = F(W([edge]))
    s = solid_of(Solid.extrude(face, Vector(0, 0, h)))
    if top_round > 0:
        s = try_fillet(s, [e for e in s.edges() if abs(e.center().Z - (z0 + h)) < 1e-3], top_round)
    return s


def try_fillet(solid, edges, r):
    """Fillet with fallback: return the unfilleted solid if OCCT fails (PLAN 6.2)."""
    try:
        out = fillet(edges, r)
        out = solid_of(out)
        if out.is_valid:
            return out
    except Exception:  # noqa: BLE001
        pass
    return solid


def extrude_taper(pts: Sequence[Sequence[float]], h: float, z0: float, taper_deg: float) -> Solid:
    """Extrude an outline in +Z with draft (positive = narrows upwards)."""
    from build123d import extrude
    from .geom import profile_wire

    w = profile_wire(pts, to3d=lambda a, b: (a, b, z0))
    return solid_of(extrude(Face(w), amount=h, dir=(0, 0, 1), taper=taper_deg))


def path_wire(pts: Sequence[Sequence[float]], bend_r: float | Sequence[float] = 0.0) -> Wire:
    """Open 3D polyline with tangent bend arcs at the inner vertices."""
    P = [Vector(*p) for p in pts]
    n = len(P)
    radii = [bend_r] * n if isinstance(bend_r, (int, float)) else list(bend_r)
    edges = []
    cur = P[0]
    for i in range(1, n - 1):
        A, B, C = P[i - 1], P[i], P[i + 1]
        u1 = (A - B).normalized()
        u2 = (C - B).normalized()
        cos_t = max(-1.0, min(1.0, u1.dot(u2)))
        theta = math.acos(cos_t)
        r = radii[i]
        if r <= 0 or theta < 1e-3 or abs(math.pi - theta) < 1e-3:
            edges.append(Edge.make_line(cur, B))
            cur = B
            continue
        d = min(r / math.tan(theta / 2), 0.49 * (A - B).length, 0.49 * (C - B).length)
        r = d * math.tan(theta / 2)
        t1, t2 = B + u1 * d, B + u2 * d
        bis = (u1 + u2).normalized()
        Cc = B + bis * (r / math.sin(theta / 2))
        mid = Cc - bis * r
        if (t1 - cur).length > 1e-6:
            edges.append(Edge.make_line(cur, t1))
        edges.append(Edge.make_three_point_arc(t1, mid, t2))
        cur = t2
    edges.append(Edge.make_line(cur, P[-1]))
    return Wire(edges)


def pipe(pts: Sequence[Sequence[float]], r: float, bend_r: float = 0.0, r_inner: float = 0.0) -> Solid:
    """Round tube swept along a bent polyline; hollow if r_inner > 0."""
    path = path_wire(pts, bend_r)
    start = Vector(*pts[0])
    tangent = (Vector(*pts[1]) - start).normalized()
    plane = Plane(origin=start, z_dir=tangent)
    prof = Face(Wire([Edge.make_circle(r, plane)]))
    s = solid_of(sweep(prof, path, transition=Transition.RIGHT))
    if r_inner > 0:
        inner = Face(Wire([Edge.make_circle(r_inner, plane)]))
        # extend the bore slightly beyond both ends
        s = solid_of(s - sweep(inner, path, transition=Transition.RIGHT))
    return s
