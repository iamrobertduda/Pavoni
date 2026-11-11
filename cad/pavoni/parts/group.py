"""Group head (pos. 71-86): body, sleeve, piston, seals, shower screen."""
from __future__ import annotations

from build123d import Location

from ..lib import lip_seal, revolve_rz


def build(ctx):
    D, T = ctx.D, ctx.T
    gx, gy = T.group_xy
    at = Location((gx, gy, 0))
    rp = D.piston_od / 2
    h = D.piston_h
    z = T.piston_z
    ri = D.piston_seal_id / 2
    sh = D.piston_seal_h + 0.3  # groove width = seal height + axial play
    g1 = z + 2.5  # lower groove bottom flank
    piston = revolve_rz([
        (0, z), (rp, z, 0.6), (rp, g1), (ri, g1), (ri, g1 + sh), (rp, g1 + sh), (rp, z + h, 0.6), (0, z + h),
    ]).moved(at)
    seal = lip_seal(D.piston_seal_od, D.piston_seal_id, D.piston_seal_h, open_up=False, z0=g1 + 0.15).moved(at)
    return {"p079_piston": [piston], "p080_piston_seal": [seal]}
