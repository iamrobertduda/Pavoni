"""Boiler (pos. 3)."""
from __future__ import annotations

from ..lib import revolve_rz, solid_of


def build(ctx):
    D, T = ctx.D, ctx.T
    r = D.boiler_od / 2
    w = D.boiler_wall
    z0 = T.boiler_foot_z
    z1 = T.boiler_shoulder_z
    z2 = T.boiler_top_z
    rn = 0.32 * r  # neck radius (blockout)
    outer = revolve_rz([(0, z0), (r, z0, 2), (r, z1, 6), (rn, z2, 2), (rn, z2 + 6), (0, z2 + 6)])
    inner = revolve_rz([(0, z0 + w), (r - w, z0 + w, 1), (r - w, z1 - 0.5, 5), (rn - w, z2 - 0.5, 1), (rn - w, z2 + 7), (0, z2 + 7)])
    return {"p003_boiler": [solid_of(outer - inner)]}
