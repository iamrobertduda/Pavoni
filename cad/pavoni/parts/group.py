"""Group head (pos. 71-86): body, sleeve, piston, seals, shower screen. (Phase 1 slice; Phase 4.1 replaces it.)"""
from __future__ import annotations

from build123d import Location

from ..lib import lip_seal, revolve_rz


def build(ctx):
    D, T = ctx.D, ctx.T
    gx, gy = T.group_xy
    at = Location((gx, gy, 0))
    rp = D.piston_d / 2
    h = D.piston_h
    z = T.piston_z
    ri = D.piston_seal_id / 2
    sh = D.piston_seal_h + 0.3
    g1 = z + D.piston_lower_groove_z - sh  # lower groove lower flank
    piston = revolve_rz([
        (0, z), (rp, z, 0.6), (rp, g1), (ri, g1), (ri, g1 + sh), (rp, g1 + sh), (rp, z + h, 0.6), (0, z + h),
    ]).moved(at)
    lower = lip_seal(D.piston_seal_od, D.piston_seal_id, D.piston_seal_h, open_up=False, z0=g1 + 0.15).moved(at)
    g2 = z + h - 3.0 - sh
    upper = lip_seal(D.piston_seal_od, D.piston_seal_id, D.piston_seal_h, open_up=True, z0=g2 + 0.15).moved(at)
    piston = piston - revolve_rz([(ri, g2), (rp + 1, g2), (rp + 1, g2 + sh), (ri, g2 + sh)]).moved(at)
    from ..lib import solid_of
    return {"p079_piston": [solid_of(piston)], "p080_piston_seal": [upper, lower]}
