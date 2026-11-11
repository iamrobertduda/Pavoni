"""Group head (pos. 71-86) incl. piston assembly (78-80).

Body: brass casting (chromed) = bell + cylinder + neck with two-bolt flange + lever
tower (two cheeks with slots, bridge on top as down-stop for the lock nut).
Inside, from the bottom: mouth (portafilter ears) - group gasket around the shower
screen skirt - screen flange - threaded plastic sleeve with O-ring - piston with two
lip seals - ceiling with the rod-seal stack (seal, washer, J-20 circlip) in a Ø20
counterbore (Q7, Q12, Q14, Q17, Q19, Q20).

Positions come from datums.py; cosmetic constants are named below.
"""
from __future__ import annotations

import math

from build123d import Location

from ..lib import (
    box,
    circlip_internal,
    cyl,
    extrude_xy,
    hex_bolt,
    hull_circles,
    lip_seal,
    o_ring,
    pipe,
    place,
    revolve_rz,
    solid_of,
    washer,
)

CLEAR = 0.15  # kosmetisch: Spiel an Passungen und kosmetischen Gewinden
FILLET = 3.0  # kosmetisch
BRIDGE_T = None  # = D.tower_cap_t (Steg über der Rolle)
FLANGE_EAR_R = 7.0  # kosmetisch: Ohren des Flansches um die Schrauben
OR_GROOVE_DEPTH = 0.75  # Nuttiefe relativ zur Schnurstärke (25 % Verpressung)


class G:
    """Group-local helper: x, y relative to the group axis, z absolute."""

    def __init__(self, T):
        self.gx, self.gy = T.group_xy

    def p(self, x, y, z):
        return (self.gx + x, self.gy + y, z)

    def at(self, shape, x=0.0, y=0.0, z=0.0):
        return shape.moved(Location((self.gx + x, self.gy + y, z)))


def body(D, T, g: G):
    zb = D.group_bottom_z
    rbell = D.group_bell_od / 2
    rcyl = D.group_upper_od / 2
    rtb = D.tower_base_d / 2
    z_dome = T.ceiling_top_z + 1.5
    outer = revolve_rz([
        (0, zb), (rbell - 0.5, zb, 0.6), (rbell, zb + 0.35 * D.group_bell_h, 6.0), (rbell, zb + 0.62 * D.group_bell_h, 4.0),
        (rcyl, T.bell_top_z, FILLET), (rcyl, T.cyl_top_z, 5.0), (rcyl - 2.5, T.sleeve_top_z + 1.0, 3.0),
        (rtb, z_dome, 2.0), (0, z_dome),
    ])
    s = g.at(outer)
    # --- tower: two cheeks + bridge, conical in side view (photo B3)
    half = D.tower_gap / 2 + D.tower_cheek_t
    y_front = -D.tower_base_d / 2
    y_back = D.lever_pivot_back + D.roller_od / 2 + 3.0
    z0, z1 = z_dome - 3.0, T.tower_top_z
    tower = box(2 * half, y_back - y_front, z1 - z0, center=(0, (y_front + y_back) / 2, (z0 + z1) / 2))
    # taper the front in side view: from tower_base_d at the bottom to tower_top_d at the top
    ttd = D.tower_top_d / 2
    cut_pts = [(y_front - 1, z0 - 1), (-ttd, z1 + 1), (y_front - 30, z1 + 1), (y_front - 30, z0 - 1)]
    taper = _yz_prism(cut_pts, 2 * half + 2)
    tower = solid_of(tower - taper)
    # back end rounded around the roller
    tower = solid_of(tower - _yz_prism([(D.lever_pivot_back + 2, z0 - 1), (y_back + 1, z0 - 1), (y_back + 1, T.roller_z - D.roller_od / 2 - 4)], 2 * half + 2))
    s = solid_of(s + g.at(tower))
    # gap between the cheeks (open at the back), bridge stays on top
    bridge_t = D.tower_cap_t
    gap = box(D.tower_gap, y_back + 10 - (-D.rod_d / 2 - 1.0), T.tower_top_z - bridge_t - (T.ceiling_top_z + 2.0),
              center=(0, (y_back + 10 + (-D.rod_d / 2 - 1.0)) / 2, (T.tower_top_z - bridge_t + T.ceiling_top_z + 2.0) / 2))
    s = solid_of(s - g.at(gap))
    # vertical slots for the front pin (travel = piston stroke), horizontal slots for the roller pin
    r_pin = D.lever_pin_d / 2 + 0.3
    vslot = box(2 * half + 2, 2 * r_pin, D.piston_stroke + 2 * r_pin + 2, center=(0, 0, T.front_pin_z + D.piston_stroke / 2))
    hslot = box(2 * half + 2, 14.0, 2 * r_pin, center=(0, D.lever_pivot_back, T.roller_z))
    s = solid_of(s - g.at(vslot) - g.at(hslot))
    # --- neck (arm) and two-bolt flange towards the boiler
    y_fl_back = T.group_flange_y - g.gy  # local y of the flange contact face (towards +Y)
    y_fl_front = y_fl_back - D.group_flange_t
    arm_r = D.group_arm_od / 2
    arm = place(cyl(arm_r, y_fl_front + 0.5 - (rcyl - 4), 0), g.p(0, rcyl - 4, T.group_arm_z), (0, 1, 0))
    sx = D.group_bolt_spacing / 2
    outline = hull_circles([(0, 0, D.group_flange_h / 2), (-sx, 0, FLANGE_EAR_R), (sx, 0, FLANGE_EAR_R)])
    fl = extrude_xy(outline, D.group_flange_t, 0)  # in XY, thickness along Z -> rotate to Y
    fl = fl.moved(Location(g.p(0, y_fl_front, T.group_arm_z), (1, 0, 0), -90))
    s = solid_of(s + arm + fl)
    # O-ring face groove on the boiler side of the flange
    ro_in = D.group_oring_id / 2 - 0.2
    ro_out = D.group_oring_id / 2 + D.group_oring_cs + 0.3
    depth = D.group_oring_cs * OR_GROOVE_DEPTH
    groove = solid_of(cyl(ro_out, depth + 1, -1) - cyl(ro_in, depth + 3, -2))
    s = solid_of(s - place(groove, g.p(0, y_fl_back, T.group_arm_z), (0, -1, 0)))
    # bolt holes, water passage with the threaded seat for the plastic connector
    for x in (-sx, sx):
        s = solid_of(s - place(cyl(D.group_bolt_d / 2 + CLEAR + 0.2, 40, -20), g.p(x, y_fl_back, T.group_arm_z), (0, 1, 0)))
    s = solid_of(s - place(cyl(D.connector_d / 2 + CLEAR, 14, -12), g.p(0, y_fl_back, T.group_arm_z), (0, 1, 0)))
    s = solid_of(s - place(cyl(D.dip_tube_d / 2 - 1.0, y_fl_back - (D.sleeve_od / 2 - 1) + 1, 0), g.p(0, D.sleeve_od / 2 - 1, T.group_arm_z), (0, 1, 0)))
    # --- bores from below
    bores = revolve_rz(bore_profile(D, T))
    s = solid_of(s - g.at(bores))
    # rod bore through ceiling and bridge
    s = solid_of(s - g.at(cyl(D.rod_d / 2 + 0.3, 80, T.ceiling_bottom_z - 1)))
    return s


def _yz_prism(pts_yz, width):
    """Prism from a (y, z) outline, extruded symmetrically along X."""
    from build123d import Face, Solid, Vector
    from ..lib.geom import profile_wire

    w = profile_wire(pts_yz, to3d=lambda a, b: (-width / 2, a, b))
    return solid_of(Solid.extrude(Face(w), Vector(width, 0, 0)))


def bore_profile(D, T):
    """Internal cavity (r, z) of the group, from the mouth up to the ceiling."""
    zb = D.group_bottom_z
    r_mouth = D.group_mouth_bore / 2
    r_ear = r_mouth + 1.5  # bayonet zone below the gasket
    z_g0 = T.screen_face_z  # gasket bottom = screen face
    z_g1 = z_g0 + D.group_gasket_h
    r_scr = D.screen_d / 2 + CLEAR
    r_seal = D.sleeve_seal_od / 2 + CLEAR  # sleeve thread / O-ring bore
    r_ann = D.sleeve_od / 2 + 1.5  # annulus around the upper sleeve
    z_thr = T.sleeve_bottom_z + D.sleeve_oring_cs * 3.2  # end of the threaded/O-ring section
    rc = D.circlip_bore / 2
    z_cb = T.ceiling_bottom_z + D.circlip_t + D.rod_washer_t + D.rod_seal_h + 0.3  # counterbore top
    return [
        (0, zb - 1), (r_ear, zb - 1), (r_ear, z_g0 - 1.2 - D.pf_ear_t - 0.5), (r_ear + 0.5, z_g0 - 1.2 - D.pf_ear_t - 0.5),
        (r_ear + 0.5, z_g0 - 0.8), (r_ear, z_g0 - 0.8),  # bayonet groove for the portafilter ears
        (r_ear, z_g0 - 0.01), (r_mouth, z_g0), (r_mouth, z_g1),
        (r_scr, z_g1), (r_scr, T.screen_top_z), (r_seal, T.screen_top_z), (r_seal, z_thr),
        (r_ann, z_thr + 1.0), (r_ann, T.ceiling_bottom_z, 1.0), (rc, T.ceiling_bottom_z), (rc, z_cb), (0, z_cb),
    ]


def circlip_groove(D, T, g):
    z = T.ceiling_bottom_z
    return g.at(revolve_rz([(D.circlip_bore / 2 - 0.1, z), (D.circlip_groove_d / 2, z), (D.circlip_groove_d / 2, z + D.circlip_t + 0.1),
                            (D.circlip_bore / 2 - 0.1, z + D.circlip_t + 0.1)]))


def sleeve(D, T, g):
    zb, zt = T.sleeve_bottom_z, T.sleeve_top_z
    ri = D.group_bore / 2
    ro = D.sleeve_od / 2
    rs = D.sleeve_seal_od / 2
    cs = D.sleeve_oring_cs
    z_thr = zb + cs * 3.2
    gz0 = zb + cs * 0.9  # O-ring groove (lower part of the sleeve, Q20)
    gz1 = gz0 + cs * 1.25
    r_root = D.sleeve_oring_id / 2
    prof = [(ri + 0.8, zb), (rs, zb, 0.4), (rs, gz0), (r_root, gz0), (r_root, gz1), (rs, gz1), (rs, z_thr), (ro, z_thr + 1.0),
            (ro, zt - 0.01), (ri + 0.6, zt), (ri, zt - 0.6), (ri, zb + 1.2), (ri + 0.8, zb)]
    s = revolve_rz(prof)
    # four tabs on top bear against the ceiling (Q20)
    for k in range(4):
        a = math.radians(45 + 90 * k)
        tab = cyl(2.0, 0.5, zt - 0.5).moved(Location(((ri + ro) / 2 * math.cos(a), (ri + ro) / 2 * math.sin(a), 0)))
        s = solid_of(s + tab)
    # two tool grooves at the bottom (removal bar, Q14)
    s = solid_of(s - box(2 * rs + 2, 5.0, 3.0, center=(0, 0, zb + 1.0)))
    # water inlet at the top, opposite the neck (front), Q20
    z_in = T.piston_z + D.piston_stroke + D.inlet_above_piston
    s = solid_of(s - place(cyl(1.75, 10, -5), (0, -(ri + ro) / 2, z_in), (0, 1, 0)))
    ring = o_ring(D.sleeve_oring_id, cs, (gz0 + gz1) / 2)
    return g.at(s), g.at(ring)


def piston_parts(D, T, g):
    z = T.piston_z
    rp = D.piston_d / 2
    h = D.piston_h
    ri = D.piston_seal_id / 2
    sh = D.piston_seal_h + 0.3
    g_lo = z + D.piston_lower_groove_z - sh / 2  # lower groove (seal centre ~7 mm above the underside, Q20)
    g_up = z + h - (D.piston_lower_groove_z - sh / 2) - sh  # upper groove, symmetric
    rt_hole = D.rod_thread_d / 2 + CLEAR  # blind M10 thread from the top (cosmetic)
    prof = [(0, z), (rp - 0.6, z), (rp, z + 0.6),
            (rp, g_lo), (ri, g_lo), (ri, g_lo + sh), (rp, g_lo + sh), (rp, g_up), (ri, g_up), (ri, g_up + sh), (rp, g_up + sh),
            (rp, z + h - 0.6), (rp - 0.6, z + h), (rt_hole, z + h), (rt_hole, z + D.rod_end_in_piston), (0, z + D.rod_end_in_piston)]
    piston = revolve_rz(prof)
    lower = lip_seal(D.piston_seal_od, D.piston_seal_id, D.piston_seal_h, open_up=False, z0=g_lo + 0.15)
    upper = lip_seal(D.piston_seal_od, D.piston_seal_id, D.piston_seal_h, open_up=True, z0=g_up + 0.15)
    # rod: Ø12 with M10 ends, cross hole for the front lever pin
    rr = D.rod_d / 2
    rt = D.rod_thread_d / 2
    zb0 = T.rod_bottom_z
    zt = T.rod_top_z
    thr_lo = z + h + 1.0 - zb0  # lower thread length (into the piston, shoulder on its top face)
    thr_up = (zt - T.lock_nut_bottom_z) + 2.0
    rod = revolve_rz([(0, zb0), (rt - 0.5, zb0), (rt, zb0 + 0.5), (rt, zb0 + thr_lo - 0.01), (rr, zb0 + thr_lo, 0.0),
                      (rr, zt - thr_up), (rt, zt - thr_up + 0.01), (rt, zt - 0.5), (rt - 0.5, zt), (0, zt)])
    rod = solid_of(rod - place(cyl(D.lever_pin_d / 2 + CLEAR, 30, -15), (0, 0, T.front_pin_z), (1, 0, 0)))
    return g.at(rod), g.at(piston), g.at(upper), g.at(lower)


def rod_seal_stack(D, T, g):
    z = T.ceiling_bottom_z
    clip = circlip_internal(D.circlip_bore, D.circlip_t, z + 0.05, width=1.5)
    wsh = washer(D.rod_washer_od, D.rod_washer_id, D.rod_washer_t, z + D.circlip_t + 0.1)
    seal = lip_seal(D.rod_seal_od, D.rod_seal_id, D.rod_seal_h, open_up=False, z0=z + D.circlip_t + 0.1 + D.rod_washer_t + 0.05)
    return g.at(seal), g.at(wsh), g.at(clip)


def screen_and_gasket(D, T, g):
    z0 = T.screen_face_z
    z1 = T.screen_top_z
    rf = D.screen_d / 2
    rb = D.screen_body_d / 2
    t = 1.0
    screen = revolve_rz([(0, z0), (rb, z0, 0.5), (rb, z1 - 1.5), (rf, z1 - 1.5, 0.3), (rf, z1, 0.3), (rb - t, z1), (rb - t, z0 + t), (0, z0 + t)])
    # gasket: flat side down to the basket rim, rounded side up (Q12, Q19)
    go, gi, gh = D.group_gasket_od / 2, D.group_gasket_id / 2, D.group_gasket_h
    gasket = revolve_rz([(gi, z0), (go, z0), (go, z0 + gh * 0.55), (go - 1.2, z0 + gh, 1.5), (gi + 1.2, z0 + gh, 1.5), (gi, z0 + gh * 0.55)])
    return g.at(screen), g.at(gasket)


def flange_parts(D, T, g):
    """O-ring 85, plastic connector 83, dip tube 84, bolts 86."""
    yb = T.group_flange_y
    za = T.group_arm_z
    cs = D.group_oring_cs
    # sits in the face groove of the flange and protrudes (1 - depth) * cs towards the boiler
    ring = place(o_ring(D.group_oring_id, cs, 0.0), (g.gx, yb - cs * OR_GROOVE_DEPTH + cs / 2, za), (0, 1, 0))
    # plastic connector screwed into the back of the neck: head reaches into the boiler hole
    rc = D.connector_d / 2
    conn = revolve_rz([(D.dip_tube_d / 2 + CLEAR, -10.0), (rc, -10.0), (rc, 0.0), (rc - 1.5, 3.5), (D.dip_tube_d / 2 + CLEAR, 3.5)])
    conn = place(conn, (g.gx, yb, za), (0, 1, 0))
    # dip tube: into the boiler, bend down, ~115 mm immersion (Q13)
    r = D.dip_tube_d / 2
    y_in = yb + 3.5 - 6.0
    y_bend = yb + 3.5 + 10.0
    tube = pipe([(g.gx, y_in, za), (g.gx, y_bend, za), (g.gx, y_bend, za - D.dip_tube_drop)], r, bend_r=10.0, r_inner=r - 1.0)
    bolts = []
    for x in (-D.group_bolt_spacing / 2, D.group_bolt_spacing / 2):
        head_h = 4.0
        b = hex_bolt(D.group_bolt_d, D.group_bolt_len, D.group_bolt_af, head_h, 0.0)
        # head on the front face of the flange, shank into the boiler boss
        bolts.append(place(b, (g.gx + x, yb - D.group_flange_t - head_h, za), (0, 1, 0)))
    return ring, conn, tube, bolts


def build(ctx):
    D, T = ctx.D, ctx.T
    g = G(T)
    b = body(D, T, g)
    b = solid_of(b - circlip_groove(D, T, g))
    slv, slv_ring = sleeve(D, T, g)
    rod, piston, seal_up, seal_lo = piston_parts(D, T, g)
    rseal, rwasher, clip = rod_seal_stack(D, T, g)
    screen, gasket = screen_and_gasket(D, T, g)
    oring, conn, tube, bolts = flange_parts(D, T, g)
    return {
        "p072_group_body": [b],
        "p076_sleeve": [slv],
        "p077_sleeve_oring": [slv_ring],
        "p078_piston_rod": [rod],
        "p079_piston": [piston],
        "p080_piston_seal": [seal_up, seal_lo],
        "p073_rod_seal": [rseal],
        "p074_rod_washer": [rwasher],
        "p075_rod_circlip": [clip],
        "p081_shower_screen": [screen],
        "p082_group_gasket": [gasket],
        "p085_group_oring": [oring],
        "p083_tube_connector": [conn],
        "p084_dip_tube": [tube],
        "p086_group_bolt": bolts,
    }
