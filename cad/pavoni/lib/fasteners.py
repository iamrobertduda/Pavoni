"""Fasteners: nuts, bolts, washers, circlips, pins. Threads are cosmetic
(no helix, PLAN 6.2); the thread designation is metadata in parts.yaml."""
from __future__ import annotations

import math

from build123d import Solid

from .geom import box, cyl, hex_prism, revolve_rz, solid_of

__all__ = ["hex_nut", "cap_nut", "hex_bolt", "washer", "circlip_external", "circlip_internal", "pin"]


def _chamfer_body(af: float, h: float, z0: float, both: bool = True) -> Solid:
    rc = af / math.sqrt(3)
    c = 0.18 * (rc - af / 2) + 0.12 * af * 0.15
    r_top = af / 2 * 0.97
    pts = [(0, z0), (r_top if both else rc + 1, z0), (rc + 1, z0 + c + (rc + 1 - r_top) * 0.58 if both else z0),
           (rc + 1, z0 + h - c - (rc + 1 - r_top) * 0.58), (r_top, z0 + h), (0, z0 + h)]
    return revolve_rz(pts)


def hex_nut(af: float, h: float, bore: float, z0: float = 0.0, chamfer_both: bool = True) -> Solid:
    body = solid_of(hex_prism(af, h, z0) & _chamfer_body(af, h, z0, chamfer_both))
    return solid_of(body - cyl(bore / 2, h + 2, z0 - 1))


def cap_nut(af: float, h_hex: float, dome_h: float, bore: float, bore_depth: float, z0: float = 0.0) -> Solid:
    """Acorn (cap) nut: hex at the bottom, dome on top, blind threaded bore from below."""
    hexp = solid_of(hex_prism(af, h_hex, z0) & _chamfer_body(af, h_hex, z0, True))
    rd = af / 2 * 0.92
    dome = revolve_rz([(0, z0 + h_hex - 0.5), (rd, z0 + h_hex - 0.5), (rd, z0 + h_hex + 0.15 * dome_h, dome_h * 0.6),
                       (rd * 0.55, z0 + h_hex + dome_h, dome_h * 0.5), (0, z0 + h_hex + dome_h)])
    body = solid_of(hexp + dome)
    bore_depth = min(bore_depth, h_hex + 0.4 * dome_h)
    return solid_of(body - cyl(bore / 2, bore_depth + 1, z0 - 1))


def hex_bolt(d: float, length: float, af: float, head_h: float, z0: float = 0.0) -> Solid:
    """Bolt along +Z: head from z0 to z0+head_h, shank above it."""
    head = solid_of(hex_prism(af, head_h, z0) & _chamfer_body(af, head_h, z0, True))
    shank = revolve_rz([(0, z0 + head_h - 0.2), (d / 2, z0 + head_h - 0.2), (d / 2, z0 + head_h + length - 0.4 * d / 4, 0.0),
                        (d / 2 - 0.4, z0 + head_h + length), (0, z0 + head_h + length)])
    return solid_of(head + shank)


def washer(od: float, id_: float, t: float, z0: float = 0.0) -> Solid:
    return revolve_rz([(id_ / 2, z0), (od / 2, z0), (od / 2, z0 + t), (id_ / 2, z0 + t)])


def _c_ring(ro: float, ri: float, t: float, z0: float, gap_deg: float, lug: float, outward: bool) -> Solid:
    """Flat C-shaped retaining ring with two pliers lugs next to the gap (+Y side)."""
    from build123d import Location

    ring = revolve_rz([(ri, z0), (ro, z0), (ro, z0 + t), (ri, z0 + t)])
    gap_w = 2 * ro * math.sin(math.radians(gap_deg / 2))
    r = solid_of(ring - box(gap_w, ro + 2, t + 2, center=(0, ro / 2 + 1, z0 + t / 2)))
    if lug > 0:
        for sgn in (-1, 1):
            cx = sgn * (gap_w / 2 + lug * 0.6)
            cy = (ri + ro) / 2 + (lug * 0.3 if not outward else -lug * 0.3)
            lug_body = cyl(lug * 0.65, t, z0).moved(Location((cx, cy, 0)))
            hole = cyl(lug * 0.25, t + 2, z0 - 1).moved(Location((cx, cy, 0)))
            r = solid_of((r + lug_body) - hole)
    return r


def circlip_external(shaft_d: float, t: float, z0: float = 0.0, width: float | None = None) -> Solid:
    """Shaft circlip (DIN 471 style), simplified: C-ring with lugs."""
    width = width or max(1.2, 0.12 * shaft_d)
    ri = shaft_d / 2 * 0.94  # sits in a groove
    return _c_ring(ri + width, ri, t, z0, 28, width, outward=False)


def circlip_internal(bore_d: float, t: float, z0: float = 0.0, width: float | None = None) -> Solid:
    """Bore circlip (DIN 472 style), simplified."""
    width = width or max(1.2, 0.10 * bore_d)
    ro = bore_d / 2 * 1.03
    return _c_ring(ro, ro - width, t, z0, 28, width, outward=True)


def pin(d: float, length: float, z0: float = 0.0, chamfer: float = 0.3) -> Solid:
    c = min(chamfer, d / 4)
    return revolve_rz([(0, z0), (d / 2 - c, z0), (d / 2, z0 + c), (d / 2, z0 + length - c), (d / 2 - c, z0 + length), (0, z0 + length)])
