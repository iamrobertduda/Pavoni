"""Boiler-to-base fixing (pos. 4, 6, 7): fibre gaskets above and below the base sheet,
brass ring screwed onto the threaded boiler neck (Q11, Q15, Q21)."""
from __future__ import annotations

import math

from build123d import Location

from ..lib import cyl, flat_gasket, place, revolve_rz, solid_of

CLEAR = 0.15  # kosmetisch: Spiel am kosmetischen Gewinde
LUG_W = 8.0  # kosmetisch: Nasen für den Ringschlüssel


def build(ctx):
    D, T = ctx.D, ctx.T
    upper = flat_gasket(D.base_gasket_upper_od, D.base_gasket_upper_id + 2 * CLEAR, D.base_gasket_upper_t, T.base_under_boiler_z)
    lower = flat_gasket(D.base_gasket_lower_od, D.base_gasket_lower_id + 2 * CLEAR, D.base_gasket_lower_t, T.ring_top_z)
    ring = revolve_rz([(D.bottom_neck_od / 2 + CLEAR, T.ring_bottom_z), (D.base_ring_od / 2, T.ring_bottom_z, 0.8),
                       (D.base_ring_od / 2, T.ring_top_z, 0.8), (D.bottom_neck_od / 2 + CLEAR, T.ring_top_z)])
    # three tapped holes for the element bolts, three lugs for the ring wrench
    rb = D.element_bolt_circle / 2
    for k in range(3):
        a = math.radians(90 + 120 * k)
        ring = solid_of(ring - cyl(D.element_bolt_d / 2 + CLEAR, 10, T.ring_bottom_z - 1).moved(Location((rb * math.cos(a), rb * math.sin(a), 0))))
        # wrench notch on the outside, between the bolts
        b = a + math.radians(60)
        notch = place(cyl(LUG_W / 2, 10, -5), (D.base_ring_od / 2 * math.cos(b), D.base_ring_od / 2 * math.sin(b), T.ring_bottom_z), (0, 0, 1))
        ring = solid_of(ring - notch)
    return {"p004_base_gasket_upper": [upper], "p006_base_gasket_lower": [lower], "p007_base_ring": [ring]}
