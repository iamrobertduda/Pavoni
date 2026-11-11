"""Steam valve (pos. 45-53), wand (54, 55) and the inner nut/washer of the tee.

Horizontal tube behind the filler neck; from left to right: star knob, gland nut,
valve body with the stub down into the shoulder cone, collar, swivel of the wand
with closed end; the wand hangs down on the right (PLAN 2.2, photo B2).
Inside: shaft with flat end closing metal-to-metal on the seat at the stub, packing
(12x7x5) between two brass washers pressed by the gland nut (Q15, Q17)."""
from __future__ import annotations

import math

from build123d import Location

from ..lib import cyl, hex_nut, lobed_knob, o_ring, pipe, place, revolve_rz, safe_union, solid_of, washer

CLEAR = 0.15  # kosmetisch
STUB_HEX_AF = 16.0  # = inner_nut_af (gleicher Schlüssel, Q22)
SPIGOT_D = 8.6  # kosmetisch: Zapfen für die Lanze (O-Ring-Nutgrund = OR-Innen-Ø)
SWIVEL_OD = 14.0  # kosmetisch
TIP_L = 12.0  # kosmetisch: Düsenkörper
GLAND_SPIGOT = 4.0  # kosmetisch: Zapfen der Stopfbuchsmutter im Körper
GLAND_HEX_AF = 14.0  # Q10: Schlüssel 14
X_SEAT = -4.0  # kosmetisch: Sitzfläche links der Stutzenmitte


def cone_inner_gap(D, T, p):
    """Gap so a flat washer (perpendicular to the cone normal) clears the curved inner cone."""
    r = math.hypot(p[0], p[1]) - D.boiler_wall
    rho = r / math.sin(T.cone_normal_tilt)  # normal curvature radius of the cone, circumferential
    a = D.inner_washer_od / 2
    return rho - math.sqrt(rho * rho - a * a) + 0.2


def xs(D):
    """Stations along X (left = knob, right = closed end of the swivel)."""
    W = D.steam_total_w
    left, right = -W / 2, W / 2
    knob_t = D.steam_knob_d * 0.45
    x_knob1 = left + knob_t
    x_body0 = -D.steam_tube_d * 1.6
    x_body1 = D.steam_tube_d * 1.3
    x_spig1 = x_body1 + 22.0
    return dict(left=left, right=right, knob1=x_knob1, body0=x_body0, body1=x_body1, spig1=x_spig1)


def body(D, T, X):
    """Valve body in local coords: tube axis = X axis, stub towards local -Z rotated later."""
    rt = D.steam_tube_d / 2
    b = place(revolve_rz([(0, X["body0"]), (rt, X["body0"], 1.0), (rt, X["body1"] - 3.0, 1.5),
                          (rt + 1.5, X["body1"] - 2.0, 0.6), (rt + 1.5, X["body1"], 0.6), (SPIGOT_D / 2, X["body1"]), (SPIGOT_D / 2, X["spig1"], 0.5), (0, X["spig1"])]),
              (0, 0, 0), (0, 0, 1))
    b = b.moved(Location((0, 0, 0), (0, 1, 0), 90))  # revolve axis Z -> X
    # stub with hex and M12 thread towards the cone
    L = T.steam_stub_len
    stub = revolve_rz([(0, 0), (rt * 0.75, 0), (rt * 0.7, L - 12.0), (STUB_HEX_AF / 2, L - 9.0), (STUB_HEX_AF / 2, L - 3.0),
                       (D.nipple_thread_d / 2 - CLEAR, L - 3.0), (D.nipple_thread_d / 2 - CLEAR, L + D.boiler_wall + D.inner_washer_t + D.inner_nut_af * 0.55 + 3.0),
                       (0, L + D.boiler_wall + D.inner_washer_t + D.inner_nut_af * 0.55 + 3.0)])
    stub = place(stub, (0, 0, 0), T.steam_stub_dir_local)
    s = safe_union(b, stub)
    # bores: packing counterbore (gland spigot + washer + packing + washer), shaft thread bore
    # ending in the flat seat, small orifice into the junction with stub and outlet
    rs = D.steam_shaft_d / 2
    cb = GLAND_SPIGOT + 2 * D.steam_washer_t + D.steam_packing_h + 0.4
    s = solid_of(s - place(cyl(D.steam_packing_od / 2 + CLEAR, cb, 0), (X["body0"] - 0.01, 0, 0), (1, 0, 0)))
    s = solid_of(s - place(cyl(rs + 1.2, X_SEAT - (X["body0"] + cb) + 0.01, 0), (X["body0"] + cb - 0.01, 0, 0), (1, 0, 0)))
    s = solid_of(s - place(cyl(1.5, 2.0 - X_SEAT, 0), (X_SEAT - 0.01, 0, 0), (1, 0, 0)))  # seat orifice
    s = solid_of(s - place(cyl(2.5, X["spig1"] + 1, 0), (0, 0, 0), (1, 0, 0)))  # outlet to the spigot
    s = solid_of(s - place(cyl(2.5, L + 30, 0), (0, 0, 0), T.steam_stub_dir_local))  # steam path from the boiler
    # O-ring grooves on the spigot
    for k in range(2):
        xg = X["body1"] + 6.0 + k * 7.0
        s = solid_of(s - place(revolve_rz([(D.wand_oring_id / 2, 0), (SPIGOT_D, 0), (SPIGOT_D, 2.0), (D.wand_oring_id / 2, 2.0)]), (xg - 1.0, 0, 0), (1, 0, 0)))
    return s


def build(ctx):
    D, T = ctx.D, ctx.T
    X = xs(D)
    # local frame: origin on the tube axis above the stub, X along the tube
    T.steam_stub_dir_local = T.steam_stub_dir
    org = (0.0, T.steam_y, T.steam_z)
    mv = Location(org)
    b = body(D, T, X).moved(mv)
    rs = D.steam_shaft_d / 2
    # shaft: flat tip at the seat (stub centre), thread in the body, out through the packing to the knob
    x_tip = X_SEAT
    cb = GLAND_SPIGOT + 2 * D.steam_washer_t + D.steam_packing_h + 0.4
    thr_len = x_tip - (X["body0"] + cb) - 0.5  # thread section ends before the packing counterbore
    kt0 = D.steam_knob_d * 0.45 * 0.3  # where the knob bore starts
    shaft_len = x_tip - (X["left"] + kt0 + 0.5)
    shaft = place(revolve_rz([(0, 0), (rs + 1.0, 0), (rs + 1.0, thr_len - 0.5), (rs, thr_len), (rs, shaft_len), (0, shaft_len)]),
                  (x_tip, 0, 0), (-1, 0, 0)).moved(mv)
    shaft = solid_of(shaft - place(cyl(D.knob_pin_d / 2 + CLEAR, 30, -15), (X["left"] + D.steam_knob_d * 0.22, 0, 0), (0, 0, 1)).moved(mv))
    # packing stack in the counterbore, from the knob side inwards: washer, packing, washer
    x0 = X["body0"] + GLAND_SPIGOT + 0.05
    w_out = place(washer(D.steam_packing_od, D.steam_packing_id + 0.2, D.steam_washer_t, 0), (x0, 0, 0), (1, 0, 0)).moved(mv)
    pack = place(revolve_rz([(D.steam_packing_id / 2 + 0.05, 0), (D.steam_packing_od / 2, 0), (D.steam_packing_od / 2, D.steam_packing_h), (D.steam_packing_id / 2 + 0.05, D.steam_packing_h)]),
                 (x0 + D.steam_washer_t + 0.05, 0, 0), (1, 0, 0)).moved(mv)
    w_in = place(washer(D.steam_packing_od, D.steam_packing_id + 0.2, D.steam_washer_t, 0), (x0 + D.steam_washer_t + D.steam_packing_h + 0.1, 0, 0), (1, 0, 0)).moved(mv)
    # gland nut: hex 14 outside, threaded spigot into the counterbore presses the packing
    gn = revolve_rz([(rs + 0.3, 0.0), (D.steam_packing_od / 2 - CLEAR, 0.0), (D.steam_packing_od / 2 - CLEAR, GLAND_SPIGOT), (rs + 0.3, GLAND_SPIGOT)])
    gn = solid_of(gn + solid_of(hex_nut(GLAND_HEX_AF, 7.0, 2 * rs + 0.6, -7.0)))
    gnut = place(gn, (X["body0"], 0, 0), (1, 0, 0)).moved(mv)
    # star knob with hub, pin across the hub
    kt = D.steam_knob_d * 0.45
    knob = lobed_knob(D.steam_knob_d / 2, D.steam_knob_d * 0.3, 6, kt * 0.55, 0.0, top_round=2.0)
    hub = revolve_rz([(0, kt * 0.5), (D.steam_knob_d * 0.2, kt * 0.5), (D.steam_knob_d * 0.17, kt), (0, kt)])
    knob = solid_of(knob + hub)
    knob = solid_of(knob - cyl(rs + CLEAR, kt + 1, kt * 0.3))
    knob = knob.moved(Location((0, 0, 0), (0, 0, 1), 90.0 / 6 * 3 - 90.0 / 6 * 2))  # lobe tips up and down (photo B2)
    knob = place(knob, (X["left"], 0, 0), (1, 0, 0))
    knob = solid_of(knob - place(cyl(D.knob_pin_d / 2 + CLEAR, 70, -35), (X["left"] + D.steam_knob_d * 0.22, 0, 0), (0, 0, 1))).moved(mv)
    pin = place(cyl(D.knob_pin_d / 2, D.knob_pin_len, -D.knob_pin_len / 2), (X["left"] + D.steam_knob_d * 0.22, 0, 0), (0, 0, 1)).moved(mv)
    # wand: swivel sleeve over the spigot, closed end, tube hanging down, tip
    x_sw0 = X["body1"] + 0.6
    sw = revolve_rz([(0, x_sw0), (SWIVEL_OD / 2, x_sw0), (SWIVEL_OD / 2, X["right"] - 1.5, 1.5), (SWIVEL_OD / 2 - 1.5, X["right"], 1.5), (0, X["right"])])
    sw = place(sw, (0, 0, 0), (0, 0, 1)).moved(Location((0, 0, 0), (0, 1, 0), 90))
    sw = solid_of(sw - place(cyl(D.wand_oring_id / 2 + D.wand_oring_cs - 0.25, X["spig1"] - x_sw0 + 0.5, -0.01), (x_sw0, 0, 0), (1, 0, 0)))
    rw = D.wand_d / 2
    xw = X["right"] - SWIVEL_OD * 0.6
    z_end = T.steam_z - D.wand_drop
    tube = pipe([(xw, 0, -SWIVEL_OD / 2 + 1.0), (xw, 0, -SWIVEL_OD / 2 - 18.0), (xw + 9.0, 0, -SWIVEL_OD / 2 - 32.0), (xw + 9.0, 0, z_end - T.steam_z + TIP_L)], rw, bend_r=12.0, r_inner=rw - 1.0)
    wand = safe_union(sw, tube).moved(mv)
    # tip: nozzle body below the wand end, male M6 spigot into the wand bore (Q15)
    tip = revolve_rz([(0, 0.0), (rw * 0.55, 0.0, 1.0), (rw + 0.6, TIP_L * 0.35, 1.0), (rw + 0.6, TIP_L - 0.05), (D.tip_thread_d / 2 - 0.25, TIP_L - 0.05),
                      (D.tip_thread_d / 2 - 0.25, TIP_L + 6.0), (0, TIP_L + 6.0)])
    tip = tip.moved(Location((xw + 9.0, 0, z_end - T.steam_z))).moved(mv)
    # wand O-rings in the spigot grooves
    rings = []
    for k in range(2):
        xg = X["body1"] + 6.0 + k * 7.0
        rings.append(place(o_ring(D.wand_oring_id, D.wand_oring_cs, 0.0), (xg, 0, 0), (1, 0, 0)).moved(mv))
    # inner nut + washer on the stub thread inside the boiler
    d = T.steam_stub_dir
    L = T.steam_stub_len
    gap = cone_inner_gap(D, T, T.steam_entry)
    p_in = tuple(o + c * (L + D.boiler_wall + gap) for o, c in zip(org, d))
    iw = place(washer(D.inner_washer_od, D.inner_washer_id + CLEAR, D.inner_washer_t, 0), p_in, d)
    p_n = tuple(o + c * (L + D.boiler_wall + gap + D.inner_washer_t + 0.05) for o, c in zip(org, d))
    inut = place(hex_nut(D.inner_nut_af, D.inner_nut_af * 0.55, D.nipple_thread_d + CLEAR, 0), p_n, d)
    return {
        "p046_steam_body": [b],
        "p047_wand_oring": rings,
        "p048_steam_shaft": [shaft],
        "p049_steam_washer": [w_out, w_in],
        "p050_steam_packing": [pack],
        "p051_steam_nut": [gnut],
        "p052_steam_knob": [knob],
        "p053_knob_pin": [pin],
        "p054_steam_wand": [wand],
        "p055_wand_tip": [tip],
        "x002_steam_inner_nut": [inut],
        "x003_steam_inner_washer": [iw],
    }
