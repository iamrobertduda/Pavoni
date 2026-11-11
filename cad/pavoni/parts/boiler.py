"""Boiler (pos. 3) and boiler cap (pos. 1, 2).

The shell is one revolved wall profile (outside up, inside down) plus a flat
boss for the group flange and the openings for all fittings.
Cosmetic constants (fillet radii, chamfers, small clearances) are named here;
every functional dimension comes from dimensions.yaml.
"""
from __future__ import annotations

import math

from build123d import Location

from ..lib import box, cyl, lobed_knob, o_ring, place, revolve_rz, solid_of

FILLET_SHOULDER = 6.0  # kosmetisch
FILLET_SMALL = 1.5  # kosmetisch
SEAM_DEPTH = 0.6  # kosmetisch: Ringnut der Naht
CLEAR = 0.1  # Spiel bei kosmetischen Gewinden


def shell(D, T):
    R, w = T.R, D.boiler_wall
    rn = T.neck_r
    rf = D.boiler_foot_od / 2
    rb = D.bottom_neck_od / 2
    rbi = rb - D.bottom_neck_wall
    rni = D.cap_thread_d / 2 - 0.5  # neck bore (thread minor)
    z0, z1, z2, z3 = T.boiler_foot_z, T.boiler_shoulder_z, T.cone_top_z, T.neck_top_z
    zf = z0 + D.boiler_foot_h
    zb = T.bottom_neck_end_z
    # inner cone exactly parallel to the outer one, offset by the wall thickness along its normal
    tilt = T.cone_normal_tilt
    slope = (z2 - z1) / (R - rn)

    def z_in(r):
        return z2 - w * math.cos(tilt) + (rn - w * math.sin(tilt) - r) * slope
    prof = [
        (rbi, zb), (rb, zb),  # neck end face (element O-ring seals here)
        (rb, z0), (rf, z0, FILLET_SMALL), (rf, zf - 1.0, FILLET_SMALL), (R, zf + 2.0),  # flared foot ring
        (R, z1, FILLET_SHOULDER), (rn, z2, 3.0), (rn, z3, 0.6),  # cone and filler neck
        (D.cap_oring_id / 2 + D.cap_oring_cs - D.cap_oring_squeeze, z3),  # counterbore = O-ring seat
        (D.cap_oring_id / 2 + D.cap_oring_cs - D.cap_oring_squeeze, z3 - D.cap_oring_cs - 0.5),
        (rni, z3 - D.cap_oring_cs - 0.5),
        (rni, z_in(rni)), (R - w, z_in(R - w), FILLET_SHOULDER - w),  # inner cone
        (R - w, z0 + w, 1.0), (rbi, z0 + w),  # inner bottom
    ]
    s = revolve_rz(prof)
    # seam groove (PLAN 2.3)
    zs = T.boiler_seam_z
    s = s - revolve_rz([(R - SEAM_DEPTH, zs), (R + 1, zs - 0.9), (R + 1, zs + 0.9)])
    # flat boss for the group flange, with the water passage and two tapped holes
    gy = T.group_flange_y
    bw, bh = D.group_flange_w * 0.95, D.group_flange_h * 0.95
    boss = box(bw, R * 0.25, bh, center=(0, gy + R * 0.125, T.group_arm_z))
    boss = solid_of(boss - cyl(R - w * 0.5, 400, 0))  # keep only the part outside the inner wall
    boss = solid_of(boss & cyl(R + 30, 400, 0))
    s = solid_of(s + boss)
    s = solid_of(s - place(cyl(D.group_hole_d / 2, 30, -15), (0, gy, T.group_arm_z), (0, 1, 0)))
    for sx in (-1, 1):
        s = solid_of(s - place(cyl(D.group_bolt_d / 2 + CLEAR, D.group_bolt_len + 2, 0), (sx * D.group_bolt_spacing / 2, gy - 0.01, T.group_arm_z), (0, 1, 0)))
    # sight glass holes (left side)
    ca, sa = math.cos(T.sg_azimuth), math.sin(T.sg_azimuth)
    for z in (T.sg_upper_z, T.sg_lower_z):
        s = solid_of(s - place(cyl(D.sight_hole_d / 2, 20, -10), (-R * ca, R * sa, z), (ca, -sa, 0)))
    # steam stub hole and safety valve hole
    s = solid_of(s - place(cyl(D.sight_hole_d / 2, 24, -12), T.steam_entry, tuple(-c for c in T.steam_stub_dir)))
    s = solid_of(s - place(cyl(D.sight_hole_d / 2, 24, -12), T.sv_base, T.sv_axis))
    return s


def cap(D, T):
    """Plastic cap: threaded spigot in the neck, conical socket, lobed knob (Q21: 60 x 65)."""
    z3 = T.neck_top_z
    top = D.cap_top_z
    z_sp = z3 - D.cap_thread_len  # spigot bottom inside the neck (catalog 65 total: see dimensions.yaml)
    r_sp = D.cap_thread_d / 2 - 0.5 - CLEAR
    z_knob = top - D.cap_knob_h
    groove_r = D.cap_oring_id / 2
    prof = [
        (0, z_sp), (r_sp - 0.5, z_sp, 0.5), (r_sp, z_sp + 1.0),
        (r_sp, z3 - D.cap_oring_cs - 0.6),
        (groove_r, z3 - D.cap_oring_cs - 0.6),  # O-ring groove at the spigot root
        (groove_r, z3 - D.cap_oring_cs - 0.25),
        (groove_r, z3 + 0.4),
        (D.cap_od * 0.37, z3 + 0.4, 1.0),  # socket underside sits just above the neck
        (D.cap_od * 0.26, z_knob + 1.0, 2.0),
        (0, z_knob + 1.0),
    ]
    body = revolve_rz(prof)
    knob = lobed_knob(D.cap_od / 2, D.cap_od * 0.35, int(D.cap_lobes), D.cap_knob_h, z_knob, top_round=2.5)
    c = solid_of(body + knob)
    ring = o_ring(D.cap_oring_id, D.cap_oring_cs, z3 - D.cap_oring_cs / 2 - 0.2)
    return c, ring


def build(ctx):
    D, T = ctx.D, ctx.T
    c, ring = cap(D, T)
    return {"p003_boiler": [shell(D, T)], "p001_boiler_cap": [c], "p002_cap_oring": [ring]}
