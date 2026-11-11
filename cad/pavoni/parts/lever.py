"""Lever (pos. 87-93): fork plates outside the tower cheeks, bar and grip, roller,
two pins with E-clips (DIN 6799 RS5), lock nut and cap nut on the piston rod.

Rest position: straight line through the rear pin (roller) and the front pin
(piston rod), lever_rest_deg below horizontal towards the front (photo B3, Q17)."""
from __future__ import annotations

import math

from build123d import Location

from ..lib import box, cap_nut, cyl, hex_nut, place, revolve_rz, solid_of
from ..lib.geom import profile_wire

FORK_GAP_CLEAR = 0.3  # kosmetisch: Luft Gabelblech/Turm
ROUND = 1.0  # kosmetisch
THREAD_LEN_IN_GRIP = 15.0  # kosmetisch


def lever_frame(D, T):
    gx, gy = T.group_xy
    th = T.lever_rest_rad
    u = (0.0, -math.cos(th), -math.sin(th))  # along the lever towards the grip
    n = (0.0, -math.sin(th), math.cos(th))  # in-plane normal (up-ish)
    origin = (gx, T.roller_y, T.roller_z)  # rear pin
    return origin, u, n


def pt(origin, u, n, s, t, x=0.0):
    return (origin[0] + x, origin[1] + u[1] * s + n[1] * t, origin[2] + u[2] * s + n[2] * t)


def plate_solid(D, T, x0, x1, s0, s1, h, origin, u, n):
    """Flat bar in the lever plane from s0 to s1 (rounded ends), thickness along X."""
    r = h / 2
    pts2 = []
    for i in range(13):
        a = math.pi / 2 + math.pi * i / 12
        pts2.append((s0 + r * math.cos(a), r * math.sin(a)))
    for i in range(13):
        a = -math.pi / 2 + math.pi * i / 12
        pts2.append((s1 + r * math.cos(a), r * math.sin(a)))
    from build123d import Face, Solid, Vector

    w = profile_wire(pts2, to3d=lambda s, t: pt(origin, u, n, s, t, x0))
    return solid_of(Solid.extrude(Face(w), Vector(x1 - x0, 0, 0)))


def arm(D, T):
    origin, u, n = lever_frame(D, T)
    s_front = D.lever_pivot_back / math.cos(T.lever_rest_rad)
    half_in = D.tower_gap / 2 + D.tower_cheek_t + FORK_GAP_CLEAR
    half_out = half_in + D.lever_fork_t
    h = D.lever_fork_h
    r_end = h / 2
    s_j = s_front + 2.2 * h  # junction of fork and bar
    plates = [plate_solid(D, T, sx * half_in if sx > 0 else -half_out, half_out if sx > 0 else -half_in, 0.0, s_j, h, origin, u, n) for sx in (1, -1)]
    block = plate_solid(D, T, -half_out, half_out, s_j - 0.6 * h, s_j, h * 0.85, origin, u, n)
    lev = solid_of(plates[0] + plates[1] + block)
    # bar
    s_end = D.lever_len - r_end
    rb = D.lever_rod_d / 2
    L = s_end - s_j
    bar = revolve_rz([(0, 0), (rb, 0), (rb, L - THREAD_LEN_IN_GRIP), (min(D.grip_d * 0.2, rb * 1.15), L - THREAD_LEN_IN_GRIP + 0.5), (min(D.grip_d * 0.2, rb * 1.15), L - 0.5), (rb, L), (0, L)])
    bar = place(bar, pt(origin, u, n, s_j - 2.0, 0), u)
    lev = solid_of(lev + bar)
    # pin holes
    for s in (0.0, s_front):
        lev = solid_of(lev - place(cyl(D.lever_pin_d / 2 + 0.15, 2 * half_out + 4, -half_out - 2), pt(origin, u, n, s, 0, 0), (1, 0, 0)))
    grip_start = s_end - THREAD_LEN_IN_GRIP
    rg = D.grip_d / 2
    grip = revolve_rz([(0, 0), (rg * 0.78, 0, 1.5), (rg * 0.92, D.grip_len * 0.35), (rg, D.grip_len * 0.75, 8.0), (rg * 0.55, D.grip_len, 6.0), (0, D.grip_len)])
    grip = solid_of(grip - cyl(min(D.grip_d * 0.2, rb * 1.15) + 0.15, THREAD_LEN_IN_GRIP, -0.01))
    grip = place(grip, pt(origin, u, n, grip_start, 0), u)
    return lev, grip, s_front, half_out


def eclip(D):
    """DIN 6799 E-clip: flat C ring with the opening facing +Z (pushed off upwards)."""
    ro = D.eclip_od / 2
    ri = D.eclip_groove_d / 2
    t = D.eclip_t
    ring = solid_of(cyl(ro, t, 0) - cyl(ri, t + 2, -1))
    opening = box(ri * 2 * 0.98, ro + 1, t + 2, center=(0, ro / 2 + 0.5, t / 2))
    return solid_of(ring - opening)


def pin(D, half_out):
    L = D.lever_pin_len
    r = D.lever_pin_d / 2
    rg = D.eclip_groove_d / 2
    xg = half_out + 0.25  # groove just outside the plates
    w = D.eclip_t + 0.1
    prof = [(0, -L / 2), (r - 0.3, -L / 2), (r, -L / 2 + 0.3), (r, -xg - w), (rg, -xg - w), (rg, -xg), (r, -xg), (r, xg), (rg, xg), (rg, xg + w), (r, xg + w),
            (r, L / 2 - 0.3), (r - 0.3, L / 2), (0, L / 2)]
    return revolve_rz(prof), xg


def build(ctx):
    D, T = ctx.D, ctx.T
    lev, grip, s_front, half_out = arm(D, T)
    origin, u, n = lever_frame(D, T)
    gx, gy = T.group_xy
    p, xg = pin(D, half_out)
    pins = [place(p, (gx, gy, T.front_pin_z), (1, 0, 0)), place(p, (gx, T.roller_y, T.roller_z), (1, 0, 0))]
    clips = []
    for (y, z) in ((gy, T.front_pin_z), (T.roller_y, T.roller_z)):
        for sx in (-1, 1):
            c = eclip(D)
            # lies in the YZ plane around the pin axis, opening up
            c = c.moved(Location((0, 0, 0), (0, 1, 0), 90))  # normal along X
            x = sx * xg + (0.05 if sx > 0 else -D.eclip_t - 0.05)  # inside the groove (width t + 0.1)
            clips.append(c.moved(Location((gx + x, y, z))))
    roller = revolve_rz([(D.roller_id / 2, -D.roller_w / 2), (D.roller_od / 2, -D.roller_w / 2, 0.4), (D.roller_od / 2, D.roller_w / 2, 0.4), (D.roller_id / 2, D.roller_w / 2)])
    roller = place(roller, (gx, T.roller_y, T.roller_z), (1, 0, 0))
    lock = hex_nut(D.top_nut_af, D.lock_nut_h, D.rod_thread_d + 0.3, T.lock_nut_bottom_z).moved(Location((gx, gy, 0)))
    cap = cap_nut(D.top_nut_af, D.cap_nut_h * 0.65, D.cap_nut_h * 0.35, D.rod_thread_d + 0.3, D.cap_nut_engage, T.cap_nut_bottom_z).moved(Location((gx, gy, 0)))
    return {
        "p087_lever": [lev],
        "p088_lever_grip": [grip],
        "p089_roller": [roller],
        "p090_lever_pin": pins,
        "p091_eclip": clips,
        "p092_lock_nut": [lock],
        "p093_cap_nut": [cap],
    }
