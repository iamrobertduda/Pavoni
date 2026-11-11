"""Heating element (pos. 9), its O-ring (8) and three bolts (10).

Stainless element: flange Ø84 with three ears bolted to the ring, O-ring in a face
groove sealing against the end of the boiler neck, U-shaped tube with a coil ring
inside the boiler, two terminals, M4 stud (thermostat) and pressurestat fitting below
(Q8, Q15, Q16, Q18)."""
from __future__ import annotations

import math

from build123d import Location

from ..lib import cyl, hex_bolt, o_ring, pipe, revolve_rz, solid_of

EAR_R = 5.5  # kosmetisch
TERM_D = 6.0  # kosmetisch


def element(D, T):
    zt = T.element_flange_top_z
    tf = D.element_flange_t
    zb = zt - tf
    rf = D.element_flange_d / 2
    rb = D.element_bolt_circle / 2
    ro = D.element_oring_id / 2 + D.element_oring_cs / 2  # O-ring centre radius
    # flange with a face groove for the O-ring
    flange = revolve_rz([(0, zb), (rf, zb, 0.6), (rf, zt, 0.4), (ro + D.element_oring_cs * 0.55, zt),
                         (ro + D.element_oring_cs * 0.55, zt - D.element_oring_cs * 0.8), (ro - D.element_oring_cs * 0.55, zt - D.element_oring_cs * 0.8),
                         (ro - D.element_oring_cs * 0.55, zt), (0, zt)])
    for k in range(3):
        a = math.radians(90 + 120 * k)
        ear = cyl(EAR_R, tf, zb).moved(Location((rb * math.cos(a), rb * math.sin(a), 0)))
        flange = solid_of(flange + ear)
        flange = solid_of(flange - cyl(D.element_bolt_d / 2 + 0.3, tf + 2, zb - 1).moved(Location((rb * math.cos(a), rb * math.sin(a), 0))))
    # heater tube: two legs up from the flange, coil ring at the top
    r_t = D.element_tube_d / 2
    rc = D.element_coil_d / 2 - r_t
    ztop = zt + D.element_immersed - r_t
    legx = rc * 0.62
    tube = pipe([(-legx, 0, zt - 0.5), (-legx, 0, ztop - rc * 0.6), (-rc, 0, ztop), (0, rc, ztop), (rc, 0, ztop), (legx, 0, ztop - rc * 0.6), (legx, 0, zt - 0.5)],
                r_t, bend_r=rc * 0.55)
    body = solid_of(flange + tube)
    # below: two terminals, central M4 stud for the thermostat, pressurestat fitting
    below = D.element_h - D.element_immersed - tf
    for x in (-legx, legx):
        body = solid_of(body + cyl(TERM_D / 2, below, zb - below).moved(Location((x, 0, 0))))
    body = solid_of(body + cyl(2.0, below * 0.7, zb - below * 0.7))
    body = solid_of(body + cyl(4.0, below * 0.5, zb - below * 0.5).moved(Location((0, -rc * 0.75, 0))))
    return body


def build(ctx):
    D, T = ctx.D, ctx.T
    zt = T.element_flange_top_z
    ring = o_ring(D.element_oring_id, D.element_oring_cs, zt - D.element_oring_cs * 0.8 + D.element_oring_cs / 2)
    rb = D.element_bolt_circle / 2
    bolts = []
    for k in range(3):
        a = math.radians(90 + 120 * k)
        head_h = D.element_bolt_d * 0.7
        zb = zt - D.element_flange_t - head_h
        b = hex_bolt(D.element_bolt_d, D.element_bolt_len, 8.0, head_h, zb)
        bolts.append(b.moved(Location((rb * math.cos(a), rb * math.sin(a), 0))))
    return {"p009_heating_element": [element(D, T)], "p008_element_oring": [ring], "p010_element_bolt": bolts}
