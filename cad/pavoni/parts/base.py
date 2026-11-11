"""Base (pos. 5), emblem (29), bottom plate (36-39), drip tray (40, 41).

Chrome sheet shell: rear nearly semicircular around the boiler, side walls drawn in
towards the bottom, a step below the top edge, a raised collar around the boiler
foot and a recessed drip pan in front (PLAN 2.3, photos A1/B1/B2/B3).
"""
from __future__ import annotations

import math

from build123d import Location

from ..lib import box, cyl, extrude_taper, extrude_xy, place, revolve_rz, rounded_rect, solid_of, tube

CLEAR = 0.3  # kosmetisch: Luft zwischen Einsatz und Mulde
STEP_INSET = 1.8  # kosmetisch: Absatz unter der Oberkante
FRONT_R = 0.31  # Eckradius vorn relativ zur Basisbreite (Foto)


def footprint(D, T, inset=0.0):
    """Outline points (x, y, fillet) of the base at a given inset."""
    w = D.base_w - 2 * inset
    y0 = T.base_front_y + inset
    y1 = T.base_rear_y - inset
    rr = w / 2 * 0.999
    rf = D.base_w * FRONT_R - inset
    return [(-w / 2, y0, rf), (w / 2, y0, rf), (w / 2, y1, rr), (-w / 2, y1, rr)]


def drip_outline(D, T, inset=0.0):
    cy = T.group_xy[1]
    return rounded_rect(D.drip_len - 2 * inset, D.drip_w - 2 * inset, D.drip_w * 0.22 - inset, 0, cy)


def base_shell(D, T):
    t = D.base_wall
    z_plate_top = D.foot_h + D.bottom_plate_t
    h_band = D.base_step_h
    z_step = D.base_h - h_band
    skirt_h = z_step - z_plate_top
    draft = D.base_side_draft
    inset_bottom = skirt_h * math.tan(math.radians(draft))
    # outer: drafted skirt (narrow at the bottom) + set-back top band
    skirt = extrude_taper(footprint(D, T, inset_bottom), skirt_h, z_plate_top, -draft)
    band = extrude_xy(footprint(D, T, STEP_INSET), h_band, z_step)
    outer = solid_of(skirt + band)
    # hollow inside
    # inner skirt ends one wall thickness below the step (ledge), inner band overlaps it
    in_skirt = extrude_taper(footprint(D, T, inset_bottom + t), skirt_h - t + 1.0, z_plate_top - 1, -draft)
    in_band = extrude_xy(footprint(D, T, STEP_INSET + t), h_band + 0.01, z_step - t - 0.01)
    inner = solid_of(in_skirt + in_band)
    # drip pan: pocket from the top, its walls stay
    z_pan = D.base_h - D.drip_depth
    pocket = extrude_xy(drip_outline(D, T), D.drip_depth + 5, z_pan)
    pocket_wall = extrude_xy(drip_outline(D, T, -t), D.drip_depth + t + 5, z_pan - t)
    # boiler seat: floor lowered to base_under_boiler_z inside the collar
    rf = D.boiler_foot_od / 2 + 1.0
    seat = cyl(rf, 10, T.base_under_boiler_z)
    seat_wall = cyl(rf + t, 10, T.base_under_boiler_z - t)
    s = solid_of(outer - pocket - seat)
    s = solid_of(s - solid_of(solid_of(inner - pocket_wall) - seat_wall))
    # raised collar around the boiler foot
    collar = revolve_rz([(rf, T.base_under_boiler_z), (D.base_collar_od / 2, D.base_h - 0.5),
                         (D.base_collar_od / 2 - 1.5, D.base_h + D.base_collar_h, 1.5), (rf, D.base_h + D.base_collar_h, 0.8)])
    s = solid_of(s + collar)
    # hole for the threaded boiler neck
    s = solid_of(s - cyl(D.bottom_neck_od / 2 + 0.5, 30, T.base_under_boiler_z - 10))
    # switch cut-out in the left side wall
    sy = T.base_rear_y - D.switch_pos_frac * D.base_len
    zc = z_plate_top + skirt_h * 0.45
    s = solid_of(s - box(30, D.switch_cutout_w, D.switch_cutout_h, center=(-D.base_w / 2, sy, zc)))
    # cable grommet hole, rear right
    a = math.radians(40)
    rr = D.base_w / 2
    s = solid_of(s - place(cyl(D.cable_d / 2 + 2.0, 20, -10), (rr * math.cos(a), rr * math.sin(a), z_plate_top + 10), (math.cos(a), math.sin(a), 0)))
    # screw bosses for the bottom plate
    for (x, y) in screw_positions(D, T):
        boss = cyl(4.0, D.base_h - z_plate_top, z_plate_top + 0.5).moved(Location((x, y, 0)))
        boss = solid_of(solid_of(boss - pocket) & outer)  # runs up to the top skin or the pan floor
        s = solid_of(s + boss)
        s = solid_of(s - cyl(D.element_bolt_d / 2 - 0.4, 14, z_plate_top - 1).moved(Location((x, y, 0))))
    return s, sy, zc


def screw_positions(D, T):
    yf = T.base_front_y + D.base_w * 0.2
    return [(-D.base_w * 0.36, yf), (D.base_w * 0.36, yf), (-D.base_w * 0.36, T.base_rear_y * 0.25), (D.base_w * 0.36, T.base_rear_y * 0.25)]


def foot_positions(D, T):
    yf = T.base_front_y + D.base_w * 0.12
    return [(-D.base_w * 0.38, yf), (D.base_w * 0.38, yf), (-D.base_w * 0.32, T.base_rear_y * 0.55), (D.base_w * 0.32, T.base_rear_y * 0.55)]


def bottom_parts(D, T):
    z0 = D.foot_h
    t = D.bottom_plate_t
    skirt_h = D.base_h - D.base_step_h - (D.foot_h + D.bottom_plate_t)
    inset_bottom = skirt_h * math.tan(math.radians(D.base_side_draft))
    plate = extrude_xy(footprint(D, T, inset_bottom + 0.6), t, z0)
    # two large holes (photo D1) and the reset-plug hole under the element centre
    hd = D.bottom_plate_hole_d
    for (x, y) in [(0, T.base_front_y * 0.55), (D.base_w * 0.18, T.base_rear_y * 0.35)]:
        plate = solid_of(plate - cyl(hd / 2, t + 2, z0 - 1).moved(Location((x, y, 0))))
    plate = solid_of(plate - cyl(6.0, t + 2, z0 - 1))
    for (x, y) in screw_positions(D, T):
        plate = solid_of(plate - cyl(D.element_bolt_d / 2 + 0.2, t + 2, z0 - 1).moved(Location((x, y, 0))))
        plate = solid_of(plate - revolve_rz([(0, z0 - 0.01), (D.element_bolt_d, z0 - 0.01), (D.element_bolt_d / 2 + 0.2, z0 + 1.6), (0, z0 + 1.6)]).moved(Location((x, y, 0))))
    feet = [cyl(D.foot_d / 2, D.foot_h, 0).moved(Location((x, y, 0))) for (x, y) in foot_positions(D, T)]
    screws = []
    for (x, y) in screw_positions(D, T):
        d = D.element_bolt_d
        s = revolve_rz([(0, z0), (d, z0), (d / 2, z0 + 1.4), (d / 2 - 0.4, z0 + 1.4), (d / 2 - 0.4, z0 + 12), (0, z0 + 12)])
        screws.append(s.moved(Location((x, y, 0))))
    plug = revolve_rz([(0, z0 - 0.8), (7.5, z0 - 0.8, 0.5), (7.5, z0), (5.9, z0), (5.9, z0 + t + 1.2), (0, z0 + t + 1.2)])
    return plate, feet, screws, plug


def drip_parts(D, T):
    z_pan = D.base_h - D.drip_depth
    t = 1.5
    h = D.drip_tray_h
    tray = solid_of(extrude_xy(drip_outline(D, T, CLEAR), h, z_pan) - extrude_xy(drip_outline(D, T, CLEAR + t), h, z_pan + t))
    gz = z_pan + h
    g_t = 2.5
    grid = extrude_xy(drip_outline(D, T, CLEAR + 0.2), g_t, gz)
    # ~10 transverse slots of different lengths (photo B1)
    n = int(D.drip_slots)
    cy = T.group_xy[1]
    span = D.drip_w - 16
    for i in range(n):
        y = cy - span / 2 + span * (i + 0.5) / n
        f = 1 - 0.55 * abs((i + 0.5) / n - 0.5) * 2
        L = (D.drip_len - 26) * (0.62 + 0.38 * f) * (0.9 if i % 3 == 1 else 1.0)
        grid = solid_of(grid - extrude_xy(rounded_rect(L, 3.2, 1.55, 0, y), g_t + 2, gz - 1))
    # grip notches left and right
    for sx in (-1, 1):
        grid = solid_of(grid - cyl(5.0, g_t + 2, gz - 1).moved(Location((sx * D.drip_len / 2, cy, 0))))
    return tray, grid


def emblem(D, T, sy):
    # front face of the drafted skirt at the emblem height
    z_plate_top = D.foot_h + D.bottom_plate_t
    skirt_h = D.base_h - D.base_step_h - z_plate_top
    zc = z_plate_top + skirt_h * 0.55
    draft = math.radians(D.base_side_draft)
    y_face = T.base_front_y + (z_plate_top + skirt_h - zc) * math.tan(draft)
    disc = revolve_rz([(0, 0), (D.emblem_d / 2, 0, 0.6), (D.emblem_d / 2, D.emblem_t, 0.5), (0, D.emblem_t)])
    # tilt with the draft, stand off the face by a hair
    loc = Location((0, y_face - 0.05, zc), (1, 0, 0), 90 + math.degrees(draft))
    return disc.moved(loc)


def build(ctx):
    D, T = ctx.D, ctx.T
    shell, sy, _ = base_shell(D, T)
    plate, feet, screws, plug = bottom_parts(D, T)
    tray, grid = drip_parts(D, T)
    return {
        "p005_base": [shell],
        "p029_emblem": [emblem(D, T, sy)],
        "p036_bottom_plate": [plate],
        "p037_rubber_foot": feet,
        "p039_base_screw": screws,
        "p038_plate_plug": [plug],
        "p040_drip_tray": [tray],
        "p041_drip_grid": [grid],
    }
