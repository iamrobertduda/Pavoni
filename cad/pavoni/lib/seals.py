"""Seals in nominal (uncompressed) size. PLAN 6.2."""
from __future__ import annotations

from build123d import Solid

from .geom import revolve_rz

__all__ = ["o_ring", "lip_seal", "flat_gasket"]


def o_ring(id_: float, cs: float, z: float = 0.0) -> Solid:
    """O-ring with inner diameter id_ and cross-section cs, centred at height z."""
    from build123d import Location, Solid as S

    t = S.make_torus(id_ / 2 + cs / 2, cs / 2)
    return t.moved(Location((0, 0, z)))


def lip_seal(od: float, id_: float, h: float, open_up: bool = True, z0: float = 0.0) -> Solid:
    """U-cup lip seal. The groove between the lips opens towards +Z if open_up.

    The open side must face the pressure it seals against; the heel is solid.
    """
    ro, ri = od / 2, id_ / 2
    w = ro - ri
    lip = 0.28 * w
    hh = 0.42 * h  # heel height
    f = min(0.25 * w, 0.6)
    prof = [
        (ri, 0, f * 0.6),
        (ro, 0, f * 0.6),
        (ro, h, 0.25),
        (ro - lip * 0.8, h, 0.25),
        (ro - lip * 1.25, hh, min(0.45 * (w - 2.5 * lip), 0.8)),
        (ri + lip * 1.25, hh, min(0.45 * (w - 2.5 * lip), 0.8)),
        (ri + lip * 0.8, h, 0.25),
        (ri, h, 0.25),
    ]
    if not open_up:
        prof = [(r, h - z, *rest) for (r, z, *rest) in prof][::-1]
    prof = [(r, z + z0, *rest) for (r, z, *rest) in prof]
    return revolve_rz(prof)


def flat_gasket(od: float, id_: float, t: float, z0: float = 0.0) -> Solid:
    return revolve_rz([(id_ / 2, z0), (od / 2, z0), (od / 2, z0 + t), (id_ / 2, z0 + t)])
