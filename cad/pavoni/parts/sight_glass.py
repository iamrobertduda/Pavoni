"""Sight glass and gauge (pos. 59-70, 100) on the left of the boiler.

Built at azimuth 0 (nipples along +X towards the boiler axis), then turned about the
boiler axis by datums.sg_azimuth so the nipples are radial.

Per fitting, from the glass centre outwards (Q17): gland screw 61 (hex 17, male thread
into the fitting, "threaded portion faces out") - brass washer 100 - silicone seal 60 in
the counterbore - glass end ~1.5 mm proud. Each fitting: nipple through the boiler wall,
PTFE washer 64 outside in a recess, brass washer 65 and nut 66 inside (Q9, Q17).
Upper fitting: through bore so the glass comes out upwards; gauge nut 68 (M12) with the
gauge 69 on top (Professional).
"""
from __future__ import annotations

import math

from build123d import Location

from ..lib import box, cyl, extrude_xy, hex_nut, place, revolve_rz, rounded_rect, solid_of, washer

CLEAR = 0.15  # kosmetisch
BODY_D = 21.0  # kosmetisch: Ø Halterkörper
GLAND_THREAD_D = 16.0  # kosmetisch: Gewinde der Druckschraube (Hohlschraube, SW 17)
GLAND_THREAD_L = 6.0  # kosmetisch
GLAND_HEX_H = 5.0  # kosmetisch
COVER_T = 1.2  # kosmetisch: Wandstärke Abdeckung
GN_HEX = 5.0  # kosmetisch: Sechskant Manometermutter


def inner_offset(D, T, a):
    """Gap so a flat washer of radius a clears the concave inner boiler wall."""
    ri = T.R - D.boiler_wall
    return ri - math.sqrt(ri * ri - a * a) + 0.05


def fitting(D, T, z, upper: bool):
    """Fitting in local coords: glass axis = Z at x = 0, nipple along +X."""
    r = BODY_D / 2
    reach = D.sg_boss_reach
    face = z - reach if upper else z + reach  # end face towards the glass
    dirz = -1 if upper else 1  # direction from the fitting towards the glass
    far = z - dirz * (r + 2.0)
    body = cyl(r, abs(far - face), min(far, face))
    rx = D.sg_axis_r  # distance from the glass axis to the boiler axis
    x_out = rx - T.R  # outer boiler surface on the nipple axis
    recess_x = x_out - D.fitting_washer_t
    nl = x_out + D.boiler_wall + inner_offset(D, T, D.inner_washer_od / 2) + D.inner_washer_t + D.inner_nut_af * 0.55 + 1.5
    nip = place(cyl(D.nipple_thread_d / 2 - CLEAR, nl, 0), (0, 0, z), (1, 0, 0))
    flange = place(cyl(D.fitting_washer_od / 2 + 1.0, recess_x - r * 0.6, 0), (r * 0.6, 0, z), (1, 0, 0))
    s = solid_of(body + flange + nip)
    # recess for the PTFE washer at the flange face
    s = solid_of(s - place(solid_of(cyl(D.fitting_washer_od / 2 + 0.2, 1.0, -0.5) - cyl(D.nipple_thread_d / 2 - CLEAR, 2, -1)), (recess_x - 0.5, 0, z), (1, 0, 0)))
    # passage along the nipple
    s = solid_of(s - place(cyl(2.5, nl + 2, -1), (r * 0.2, 0, z), (1, 0, 0)))
    # towards the glass: female thread for the gland screw, then counterbore for the seal, then glass bore
    zt0, zt1 = sorted((face, face - dirz * GLAND_THREAD_L))
    s = solid_of(s - cyl(GLAND_THREAD_D / 2 + CLEAR, zt1 - zt0 + 0.02, zt0 - 0.01))
    z_cb = face - dirz * GLAND_THREAD_L
    zc0, zc1 = sorted((z_cb, z_cb - dirz * (D.glass_seal_h - 0.4)))
    s = solid_of(s - cyl(D.glass_seal_od / 2 - 0.1, zc1 - zc0 + 0.01, zc0 - 0.005))  # seal squeezed 0.1 radially
    if upper:
        s = solid_of(s - cyl(D.glass_od / 2 + CLEAR + 0.15, 200, face - 1))  # glass leaves upwards
        s = solid_of(s - cyl(D.nipple_thread_d / 2 + CLEAR, 12.0, far - 12.0 + 0.01))  # M12 for the gauge nut
    else:
        s = solid_of(s - cyl(D.glass_od / 2 + CLEAR + 0.15, face - (z - 3.0) + 1, z - 3.0))
    # grooves for the cover noses
    s = solid_of(s - box(3.0, BODY_D + 2, 1.6, center=(-r + 0.6, 0, z + (2.5 if upper else -2.5))))
    return s, face, dirz, far, recess_x, x_out


def build(ctx):
    D, T = ctx.D, ctx.T
    rx = D.sg_axis_r

    def put(shape):
        """local (glass axis at x = 0) -> world: shift to x = -rx, then turn about the boiler axis."""
        return shape.moved(Location((-rx, 0, 0))).moved(Location((0, 0, 0), (0, 0, 1), -math.degrees(T.sg_azimuth)))

    out = {k: [] for k in ["p059_upper_fitting", "p063_lower_fitting", "p060_glass_seal", "p100_glass_washer", "p061_glass_nut",
                           "p064_fitting_washer", "p065_inner_washer", "p066_inner_nut"]}
    faces = {}
    for upper in (True, False):
        z = T.sg_upper_z if upper else T.sg_lower_z
        s, face, dirz, far, recess_x, x_out = fitting(D, T, z, upper)
        faces[upper] = (face, dirz, far)
        out["p059_upper_fitting" if upper else "p063_lower_fitting"].append(put(s))
        # stack inside the fitting, from the face inwards: gland screw thread, washer, seal
        z_cb = face - dirz * GLAND_THREAD_L
        # washer sits at the bottom of the thread, seal beyond it in the counterbore
        if dirz < 0:  # upper fitting: glass below, stack goes upwards from the face
            z_w = z_cb - D.glass_washer_t - 0.05
            z_s = z_cb
        else:
            z_w = z_cb + 0.05
            z_s = z_cb - D.glass_seal_h
        seal = revolve_rz([(D.glass_seal_id / 2, z_s), (D.glass_seal_od / 2, z_s), (D.glass_seal_od / 2, z_s + D.glass_seal_h), (D.glass_seal_id / 2, z_s + D.glass_seal_h)])
        wsh = washer(D.glass_washer_od, D.glass_washer_id, D.glass_washer_t, z_w)
        # gland screw: male thread from the washer to the face, hex outside the face
        if dirz < 0:
            gl = solid_of(cyl(GLAND_THREAD_D / 2 - CLEAR, (z_w - 0.05) - face, face) + hex_nut(D.glass_nut_af, GLAND_HEX_H, 0.01, face - GLAND_HEX_H))
            gl = solid_of(gl - cyl(D.glass_od / 2 + 0.35, 40, face - 20))
        else:
            gl = solid_of(cyl(GLAND_THREAD_D / 2 - CLEAR, face - (z_w + D.glass_washer_t + 0.05), z_w + D.glass_washer_t + 0.05) + hex_nut(D.glass_nut_af, GLAND_HEX_H, 0.01, face))
            gl = solid_of(gl - cyl(D.glass_od / 2 + 0.35, 40, face - 20))
        out["p060_glass_seal"].append(put(seal))
        out["p100_glass_washer"].append(put(wsh))
        out["p061_glass_nut"].append(put(gl))
        # PTFE washer outside (convex wall: touches on the nipple axis), brass washer + nut inside
        out["p064_fitting_washer"].append(put(place(washer(D.fitting_washer_od, D.fitting_washer_id + CLEAR, D.fitting_washer_t, 0), (recess_x, 0, z), (1, 0, 0))))
        xi = x_out + D.boiler_wall + inner_offset(D, T, D.inner_washer_od / 2)
        out["p065_inner_washer"].append(put(place(washer(D.inner_washer_od, D.inner_washer_id + CLEAR, D.inner_washer_t, 0), (xi, 0, z), (1, 0, 0))))
        out["p066_inner_nut"].append(put(place(hex_nut(D.inner_nut_af, D.inner_nut_af * 0.55, D.nipple_thread_d + CLEAR, 0), (xi + D.inner_washer_t + 0.05, 0, z), (1, 0, 0))))
    # glass tube: ends 1.5 mm beyond the seals
    f_up, d_up, far_up = faces[True]
    f_lo, d_lo, _ = faces[False]
    zg1 = f_up + GLAND_THREAD_L + D.glass_seal_h - 0.4 + D.glass_proud
    zg0 = f_lo - GLAND_THREAD_L - (D.glass_seal_h - 0.4) - D.glass_proud
    glass = revolve_rz([(D.glass_id / 2, zg0), (D.glass_od / 2, zg0), (D.glass_od / 2, zg1), (D.glass_id / 2, zg1)])
    # gauge nut on top of the upper fitting, third PTFE washer under its hex
    z_top = far_up
    gauge_nut = cyl(D.nipple_thread_d / 2 - CLEAR, 10.0 + D.fitting_washer_t, z_top - 10.0)
    gauge_nut = solid_of(gauge_nut + hex_nut(14.0, GN_HEX, 0.01, z_top + D.fitting_washer_t))
    gauge_nut = solid_of(gauge_nut - cyl(4.9, 12.0, z_top + D.fitting_washer_t + GN_HEX - 8.0))  # 1/8 BSP for the gauge stem
    gauge_nut = solid_of(gauge_nut - cyl(D.glass_od / 2 + 0.5, 20, z_top - 12.0))
    ptfe3 = washer(D.fitting_washer_od, D.nipple_thread_d + 2 * CLEAR, D.fitting_washer_t, z_top)
    out["p064_fitting_washer"].append(put(ptfe3))
    # gauge: case Ø41 facing front, stem down into the gauge nut
    rg = D.gauge_d / 2
    zc = z_top + D.fitting_washer_t + GN_HEX + 9.0 + rg
    case = revolve_rz([(0, -D.gauge_depth / 2), (rg - 1.0, -D.gauge_depth / 2, 1.0), (rg, D.gauge_depth / 2 - 2.0, 1.0), (rg - 2.0, D.gauge_depth / 2, 0.8),
                       (rg - 2.5, D.gauge_depth / 2 - 1.5), (0, D.gauge_depth / 2 - 1.5)])
    case = place(case, (0, 0, zc), (0, -1, 0))
    z_stem = z_top + D.fitting_washer_t + GN_HEX - 8.0
    stem = cyl(4.75, zc - rg - z_stem + 1.0, z_stem)
    gauge = solid_of(case + stem)
    dial = place(cyl(rg - 3.0, 0.6, 0), (0, -(D.gauge_depth / 2 - 1.5) - 0.02, zc), (0, -1, 0))
    # clear U cover outside the glass, open towards the boiler
    zm = (T.sg_upper_z + T.sg_lower_z) / 2
    h, w, dpt = D.sg_cover_h, D.sg_cover_w, D.sg_cover_d
    x_cov = -BODY_D / 2 - 2.0  # outer face of the U
    outer = extrude_xy(rounded_rect(dpt, w, 3.0, x_cov + dpt / 2, 0), h, zm - h / 2)
    inner = extrude_xy(rounded_rect(dpt, w - 2 * COVER_T, 2.0, x_cov + dpt / 2 + COVER_T, 0), h + 2, zm - h / 2 - 1)
    cover = solid_of(outer - inner)
    out.update({
        "p062_sight_glass": [put(glass)],
        "p068_gauge_nut": [put(gauge_nut)],
        "p069_gauge": [put(gauge)],
        "x001_gauge_dial": [put(dial)],
        "p070_glass_cover": [put(cover)],
    })
    return out
