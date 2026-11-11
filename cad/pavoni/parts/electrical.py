"""Electrics (tier C, PLAN 6.3): simplified bodies at the right place inside the base.

Pressurestat with copper tube from the heating element flange (Q18), safety thermostat
on the M4 stud in the middle of the element (Q21), green switch in the left side wall,
terminal block, cable with grommet at the rear right (photos B2/B3)."""
from __future__ import annotations

import math

from build123d import Location

from ..lib import box, cyl, hex_nut, pipe, place, revolve_rz, rounded_rect, extrude_xy, solid_of, washer

PLATE_CLEAR = 1.0  # kosmetisch: Abstand zur Bodenplatte


def build(ctx):
    D, T = ctx.D, ctx.T
    z_floor = D.foot_h + D.bottom_plate_t + PLATE_CLEAR
    zf = T.element_flange_top_z - D.element_flange_t  # underside of the element flange
    below = D.element_h - D.element_immersed - D.element_flange_t
    # thermostat: bracket on the central M4 stud, body hanging beside the stud (Q21)
    stud_len = below * 0.7
    zb_br = zf - stud_len + 3.0  # bracket underside
    th_h = 11.0
    ty_ = D.thermostat_d / 2 + 1.6 + 5.0  # cover clears washer and nut on the stud
    zt_top = zb_br
    body_t = revolve_rz([(0, zt_top - th_h), (D.thermostat_d / 2, zt_top - th_h, 1.0), (D.thermostat_d / 2, zt_top), (0, zt_top)]).moved(Location((0, ty_, 0)))
    bracket_t = box(10.0, ty_ + 6.0, 1.5, center=(0, (ty_ + 6.0) / 2 - 5.0, zb_br + 0.75))
    thermo = solid_of(body_t + bracket_t)
    thermo = solid_of(thermo - cyl(2.2, 4.0, zb_br - 1.0))
    # tooth washer and M4 nut under the bracket on the stud
    tw = washer(8.0, 4.2, 0.6, zb_br - 0.65)
    nut_m4 = hex_nut(7.0, 3.2, 4.1, zb_br - 0.7 - 3.2)
    rcv = D.thermostat_d / 2
    cover = revolve_rz([(rcv + 0.6, zt_top - th_h - 2.0), (rcv + 1.6, zt_top - th_h - 2.0, 0.5), (rcv + 1.6, zt_top - 0.2), (rcv + 0.6, zt_top - 0.2)])
    cover = solid_of(cover + revolve_rz([(0, zt_top - th_h - 2.0), (rcv + 0.6, zt_top - th_h - 2.0), (rcv + 0.6, zt_top - th_h - 0.8), (0, zt_top - th_h - 0.8)]))
    cover = cover.moved(Location((0, ty_, 0)))
    # pressurestat lying in the free cavity under the drip pan (front left), nipple pointing backwards
    pw, pd = D.pressurestat_w, D.pressurestat_d
    ph = 18.0
    px, py = -D.base_w * 0.2, T.group_xy[1] + 6.0
    pz0 = z_floor
    pstat = extrude_xy(rounded_rect(pd, pw, 4.0, px, py), ph, pz0)
    nip_y = py + pw / 2
    pstat = solid_of(pstat + place(cyl(6.0, 8.0, 0), (px, nip_y - 0.5, pz0 + ph / 2), (0, 1, 0)))
    rc = D.element_coil_d / 2 - D.element_tube_d / 2
    fx, fy = 0.0, -rc * 0.75  # fitting on the element
    fz = zf - below * 0.5
    zt_run = pz0 + ph / 2
    f_bot = zf - below * 0.5  # underside of the fitting on the element
    tube = pipe([(fx, fy, f_bot - 0.05), (fx, fy, zt_run + 2.5), (fx, fy - 18.0, zt_run), (px, nip_y + 22.0, zt_run), (px, nip_y + 7.6, zt_run)],
                D.pstat_tube_d / 2, bend_r=6.0, r_inner=D.pstat_tube_d / 2 - 0.8)
    # switch in the left side wall
    sy = T.base_rear_y - D.switch_pos_frac * D.base_len
    skirt_h = D.base_h - D.base_step_h - (D.foot_h + D.bottom_plate_t)
    zc = D.foot_h + D.bottom_plate_t + skirt_h * 0.45
    draft = math.radians(D.base_side_draft)
    x_wall = -D.base_w / 2 + (D.base_h - D.base_step_h - zc) * math.tan(draft)
    frame = extrude_xy(rounded_rect(D.switch_w, D.switch_h, 2.0), 3.0, 0)
    frame = solid_of(frame - extrude_xy(rounded_rect(D.switch_w - 6, D.switch_h - 6, 1.0), 5.0, -1))
    rocker = extrude_xy(rounded_rect(D.switch_w - 6.4, D.switch_h - 6.4, 1.0), 4.5, -1.5)
    body_sw = extrude_xy(rounded_rect(D.switch_cutout_w - 0.6, D.switch_cutout_h - 0.6, 0.5), 22.0, -22.0)
    sw = solid_of(frame + rocker + body_sw)
    x_wall -= D.switch_h / 2 * math.tan(draft) + 0.1  # flat frame against the drafted wall
    sw = place(sw, (x_wall - 0.05, sy, zc), (-1, 0, 0), x_dir=(0, 1, 0))
    # terminal block with bracket, screw, M3 nut, tooth washer, cable clamp (rear right)
    tx, ty = 0.0, D.base_rear_overhang * 0.78  # behind the boiler, outside the ring and the element ears
    bracket = box(40.0, 18.0, 1.5, center=(tx, ty, z_floor + 0.75))
    tblock = box(26.0, 14.0, 12.0, center=(tx, ty, z_floor + 1.5 + 6.0))
    sx_, sy_ = tx - 16.5, ty - 5.0  # screw and washer beside the block
    bracket = solid_of(bracket - cyl(1.6, 4.0, z_floor - 1.0).moved(Location((sx_, sy_, 0))))
    bracket = solid_of(bracket - cyl(1.7, 4.0, z_floor - 1.0).moved(Location((tx - 16.5, ty + 5.0, 0))))
    screw = cyl(1.5, 3.2, z_floor - 0.9).moved(Location((sx_, sy_, 0)))
    tw2 = washer(6.5, 3.2, 0.5, z_floor + 1.55).moved(Location((sx_, sy_, 0)))
    screw = solid_of(screw + cyl(2.8, 1.2, z_floor + 2.1).moved(Location((sx_, sy_, 0))))
    nut3 = hex_nut(5.5, 2.4, 3.2, z_floor + 1.55).moved(Location((tx - 16.5, ty + 5.0, 0)))
    # cable: grommet in the rear right wall, short stub outside down to the table (schematic)
    a = math.radians(40)
    rr = D.base_w / 2
    gx, gy = rr * math.cos(a), rr * math.sin(a)
    gz = D.foot_h + D.bottom_plate_t + 10.0
    grommet = place(revolve_rz([(D.cable_d / 2 + 0.1, -3.0), (D.cable_d / 2 + 3.0, -3.0, 0.5), (D.cable_d / 2 + 3.0, 3.0, 0.5), (D.cable_d / 2 + 0.1, 3.0)]), (gx, gy, gz), (math.cos(a), math.sin(a), 0))
    out_dir = (math.cos(a), math.sin(a))
    c0 = (tx + 13.0 + D.cable_d / 2 + 1.0, ty + 2.0, z_floor + 1.5 + D.cable_d / 2 + 0.3)  # leaves the block at its right end
    cable = pipe([c0, (gx - out_dir[0] * 10, gy - out_dir[1] * 10, gz), (gx + out_dir[0] * 25, gy + out_dir[1] * 25, gz),
                  (gx + out_dir[0] * 45, gy + out_dir[1] * 45, D.cable_d / 2 + 0.2)], D.cable_d / 2, bend_r=10.0)
    # strain relief clamp around the cable, half way to the grommet
    p1 = (gx - out_dir[0] * 10, gy - out_dir[1] * 10, gz)
    seg = [p1[i] - c0[i] for i in range(3)]
    sl = math.sqrt(sum(c * c for c in seg))
    mid = tuple(c0[i] + seg[i] * 0.5 for i in range(3))
    ring = solid_of(cyl(D.cable_d / 2 + 2.5, 8.0, -4.0) - cyl(D.cable_d / 2 + 0.25, 10.0, -5.0))
    clamp = place(ring, mid, tuple(c / sl for c in seg))
    return {
        "p011_pstat_tube": [tube],
        "p012_pressurestat": [pstat],
        "p013_thermostat": [thermo],
        "p014_thermostat_cover": [cover],
        "p015_tooth_washer": [tw],
        "p016_nut_m4": [nut_m4],
        "p026_switch": [sw],
        "p027_cable_grommet": [grommet],
        "p028_power_cable": [cable],
        "p030_tooth_washer": [tw2],
        "p031_sheet_screw": [screw],
        "p032_terminal_bracket": [bracket],
        "p033_cable_clamp": [clamp],
        "p034_terminal_block": [tblock],
        "p035_nut_m3": [nut3],
    }
