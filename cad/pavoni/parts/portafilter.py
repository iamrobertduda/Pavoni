"""Portafilter (pos. 94-101) in the locked position.

Head inserts into the bayonet zone of the group mouth, the basket rim (Ø60) presses
against the group gasket (Q13, Q21). Handle points forward and slightly down (photos
B3/C3). Basket spring sits in an inner groove (Q12, Q21)."""
from __future__ import annotations

import math

from build123d import Location

from ..lib import box, cyl, o_ring, pipe, place, revolve_rz, safe_union, solid_of

CLEAR = 0.2  # kosmetisch
HANDLE_DOWN_DEG = 18.0  # Foto B3: Griff leicht nach unten geneigt
EAR_DEG = 40.0  # kosmetisch: Winkelbreite der Bajonett-Ohren
EAR_REACH = 1.0  # kosmetisch: Überstand der Ohren in die Bajonett-Nut der Gruppe


def head(D, T):
    gx, gy = T.group_xy
    zt = T.screen_face_z  # basket rim / gasket plane
    r_top = D.group_mouth_bore / 2 + 1.0 - CLEAR  # fits the bayonet bore of the group
    r_body = D.pf_body_od / 2
    depth = D.basket_h + 4.0
    zb = zt - depth
    r_in = (D.basket_id + 1.3) / 2 + CLEAR  # holds the basket body
    r_seat = D.basket_rim_d / 2 + CLEAR
    seat = 1.0
    prof = [(0, zb - 3.0), (r_body * 0.55, zb - 3.0, 1.0), (r_body, zb + 4.0, 4.0), (r_body, zt - T.mouth_depth - 1.0, 2.0),
            (r_top, zt - T.mouth_depth + 1.0, 0.5), (r_top, zt - seat, 0.4), (r_seat, zt - seat), (r_seat, zt - seat - 0.8),
            (r_in, zt - seat - 0.8), (r_in, zb + 2.0, 1.5), (4.0, zb), (0, zb)]
    s = revolve_rz(prof)
    # handle neck first (OCCT fuses it reliably with the plain revolve), then all cuts
    hd = handle_dir()
    nl = neck_len(D)
    r0 = r_in + 0.25  # neck base lies inside the wall: not in the cavity, edges not outside
    zc = zb + depth * 0.45
    boss = place(revolve_rz([(0, 0), (9.5, 0), (7.5, nl - r0, 1.0), (0, nl - r0)]), (hd[0] * r0, hd[1] * r0, zc + hd[2] * r0), hd)
    s = safe_union(s, boss)
    s = solid_of(s - cyl(r_in, zt - seat - 0.8 - (zb + 2.0) - 1.6, zb + 2.0 + 1.6))  # re-open the basket cavity
    s = solid_of(s - place(cyl(6.0 + CLEAR, 14, -0.01), (hd[0] * (nl - 13), hd[1] * (nl - 13), zc + hd[2] * (nl - 13)), hd))
    # spring groove (5 mm below the edge, ~1.5 high, Q21)
    zg = zt - 5.0
    s = solid_of(s - revolve_rz([(r_in - 0.1, zg - 0.75), (r_in + 0.9, zg - 0.75), (r_in + 0.9, zg + 0.75), (r_in - 0.1, zg + 0.75)]))
    # two bayonet ears at the top, perpendicular to the handle
    for a0 in (0.0, 180.0):
        ear = revolve_rz([(r_top - 0.5, zt - seat - D.pf_ear_t), (r_top + EAR_REACH, zt - seat - D.pf_ear_t), (r_top + EAR_REACH, zt - seat - 0.2),
                          (r_top - 0.5, zt - seat - 0.2)], angle=EAR_DEG)
        ear = ear.moved(Location((0, 0, 0), (0, 0, 1), a0 - EAR_DEG / 2))
        s = safe_union(s, ear)
    # outlet to the spout (3/8 BSP)
    s = solid_of(s - cyl(5.0, 6.0, zb - 4.0))
    return s.moved(Location((gx, gy, 0))), zb, zt


def neck_len(D):
    """Chrome neck between head and grip so that the overall length is pf_len (Q21)."""
    return D.pf_len - D.pf_head_od / 2 - D.grip_len - 2.0


def handle_dir():
    a = math.radians(HANDLE_DOWN_DEG)
    return (0.0, -math.cos(a), -math.sin(a))


def build(ctx):
    D, T = ctx.D, ctx.T
    gx, gy = T.group_xy
    body, zb, zt = head(D, T)
    hd = handle_dir()
    z_boss = zb + (D.basket_h + 4.0) * 0.45
    # handle stud M12 x 45 and grip
    nl = neck_len(D)
    s0 = nl - 13.0  # stud seated 13 mm in the neck
    stud = place(cyl(6.0, D.pf_stud_len, 0), (gx + hd[0] * s0, gy + hd[1] * s0, z_boss + hd[2] * s0), hd)
    rg = D.grip_d / 2
    g0 = nl + 0.5 - 4.0
    grip = revolve_rz([(0, 0), (rg * 0.7, 0, 1.5), (rg * 0.85, 25.0), (rg, D.grip_len * 0.8, 10.0), (rg * 0.5, D.grip_len, 6.0), (0, D.grip_len)])
    grip = solid_of(grip - cyl(6.0 + CLEAR, s0 + D.pf_stud_len - (g0 + 4.0) + 0.5, -0.01))
    grip = place(grip, (gx + hd[0] * (4 + g0), gy + hd[1] * (4 + g0), z_boss + hd[2] * (4 + g0)), hd)
    # spout: threaded fitting + two nozzles down to spout_bottom_z
    z_sp = D.spout_bottom_z
    fit = revolve_rz([(0, zb - 12.0), (8.0, zb - 12.0, 1.0), (8.0, zb - 3.0), (4.5, zb - 3.0), (4.5, zb + 0.5), (0, zb + 0.5)])
    sp = solid_of(fit + box(26.0, 8.0, 5.0, center=(0, 0, zb - 13.5)))
    for sx in (-1, 1):
        sp = solid_of(sp + pipe([(sx * 10.0, 0, zb - 13.0), (sx * 10.0, 0, z_sp + 4.0), (sx * 8.0, 0, z_sp)], 2.6, bend_r=0.0))
    sp = sp.moved(Location((gx, gy, 0)))
    # basket: rim on the seat, body down into the head
    rr = D.basket_rim_d / 2
    ro = (D.basket_id + 1.3) / 2
    ri = D.basket_id / 2
    bh = D.basket_h
    basket = revolve_rz([(0, zt - bh), (ro - 2.0, zt - bh, 2.0), (ro, zt - bh + 3.0), (ro, zt - 1.0), (rr, zt - 1.0, 0.3), (rr, zt, 0.3), (ri, zt), (ri, zt - bh + 3.6),
                         (ri - 2.0, zt - bh + 0.65, 1.5), (0, zt - bh + 0.65)])
    basket = basket.moved(Location((gx, gy, 0)))
    spring = o_ring(2 * ((D.basket_id + 1.3) / 2 + CLEAR + 0.05), D.pf_spring_wire, zt - 5.0).moved(Location((gx, gy, 0)))
    return {
        "p095_portafilter": [body],
        "p097_handle_stud": [stud],
        "p088_portafilter_grip": [grip],
        "p096_spout": [sp],
        "p098_basket_double": [basket],
        "p101_portafilter_spring": [spring],
    }
