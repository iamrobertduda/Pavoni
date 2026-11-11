"""Safety valve with anti-vacuum (pos. 17-21), Millennium M12 version.

Fitting with 16 mm hex through the boiler hole, held by washer and nut inside; seat =
bevelled bore at the top of the fitting; PTFE poppet seats downwards, spring above it
inside the chrome cap nut (16 mm); condensate cup between hex and cap (Q4, Q18, Q27).
Built along the local +Z axis (= cone normal, datums.sv_axis) from the cone surface."""
from __future__ import annotations

from build123d import Edge, Face, Helix, Plane, Solid, Wire, sweep

from ..lib import cyl, hex_nut, place, revolve_rz, solid_of, washer

CLEAR = 0.15  # kosmetisch
HEX_H = 6.0  # kosmetisch
UP_THREAD = 9.0  # kosmetisch: M12 über dem Sechskant für die Kappe
CUP_H = 9.0  # kosmetisch
CAP_H = 30.0  # kosmetisch: Kappenhöhe (Feder 26 + Ventil)


def local_parts(D, T):
    rt = D.sv_thread_d / 2 - CLEAR
    af = D.sv_hex_af
    inside = D.boiler_wall + 1.0 + D.inner_washer_t + D.inner_nut_af * 0.55 + 2.0
    z_hex0, z_hex1 = 0.3, 0.3 + HEX_H
    z_top = z_hex1 + UP_THREAD
    fit = revolve_rz([(0, -inside), (rt, -inside), (rt, z_hex0), (af / 2, z_hex0), (af / 2, z_hex1), (rt, z_hex1), (rt, z_top - 0.8), (3.2, z_top)])
    fit = solid_of(fit & revolve_rz([(0, -inside - 1), (af, -inside - 1), (af, z_top + 1), (0, z_top + 1)]))
    hexp = hex_nut(af, HEX_H, 0.01, z_hex0)
    fit = solid_of(fit + hexp)
    fit = solid_of(fit - cyl(2.0, inside + z_top + 2, -inside - 1))  # bore; bevel at the top = seat
    fit = solid_of(fit - revolve_rz([(2.0, z_top - 1.6), (3.2, z_top + 0.01), (2.0, z_top + 0.01)]))
    # condensate cup sits on the hex, held by the cap
    rc = D.sv_cup_d / 2
    cup = revolve_rz([(rt + CLEAR, z_hex1), (rc, z_hex1, 1.0), (rc, z_hex1 + CUP_H, 0.6), (rc - 0.8, z_hex1 + CUP_H), (rc - 0.8, z_hex1 + 0.8), (rt + CLEAR, z_hex1 + 0.8)])
    # cap nut: hex 16 with dome, M12 inside, cavity for spring and poppet, vent holes
    zc0 = z_hex1 + 0.8 + 0.05
    cap = revolve_rz([(rt + CLEAR, zc0), (af * 0.6, zc0), (af * 0.6, zc0 + CAP_H - 6.0, 5.0), (3.0, zc0 + CAP_H, 3.0), (0, zc0 + CAP_H), (0, zc0 + CAP_H - 2.5),
                      (D.sv_spring_d / 2 + 0.6, zc0 + CAP_H - 3.5), (D.sv_spring_d / 2 + 0.6, z_top + 0.5), (rt + CLEAR, z_top + 0.5)])
    cap = solid_of(cap - place(cyl(1.0, af * 2, -af), (0, 0, zc0 + CAP_H * 0.3), (1, 0, 0)))
    # poppet (PTFE mushroom): conical tip in the seat, collar, stem guiding the spring
    pop = revolve_rz([(0, z_top - 1.2), (2.9, z_top + 0.1), (3.4, z_top + 1.6, 0.4), (3.4, z_top + 3.0), (1.6, z_top + 3.0), (1.6, z_top + 8.0), (0, z_top + 8.0)])
    # spring: 8 coils, Ø7 x 26 free (compressed to the cavity height)
    zs0 = z_top + 3.0
    zs1 = zc0 + CAP_H - 3.5
    spring = coil(D.sv_spring_d / 2 - 0.4, 0.8, zs0, zs1, int(D.sv_spring_coils))
    # inner washer + nut on the thread inside the boiler
    from .steam import cone_inner_gap
    gap = cone_inner_gap(D, T, T.sv_base)
    iw = washer(D.inner_washer_od, D.inner_washer_id + CLEAR, D.inner_washer_t, -D.boiler_wall - gap - D.inner_washer_t)
    inut = hex_nut(D.inner_nut_af, D.inner_nut_af * 0.55, D.sv_thread_d + CLEAR, -D.boiler_wall - gap - D.inner_washer_t - 0.05 - D.inner_nut_af * 0.55)
    return fit, cup, cap, pop, spring, iw, inut


def coil(r, wire_r, z0, z1, turns):
    """Helical compression spring with closed ends (wire radius wire_r)."""
    h = z1 - z0 - 2 * wire_r
    pitch = h / turns
    path = Helix(pitch, h, r, center=(0, 0, z0 + wire_r))
    start = path @ 0
    tangent = path % 0
    prof = Face(Wire([Edge.make_circle(wire_r, Plane(origin=start, z_dir=tangent))]))
    try:
        s = solid_of(sweep(prof, path, is_frenet=True))
        if s.is_valid:
            return s
    except Exception:  # noqa: BLE001
        pass
    return solid_of(cyl(r + wire_r, z1 - z0, z0) - cyl(r - wire_r, z1 - z0 + 2, z0 - 1))


def build(ctx):
    D, T = ctx.D, ctx.T
    fit, cup, cap, pop, spring, iw, inut = local_parts(D, T)
    p, a = T.sv_base, T.sv_axis

    def pl(s):
        return place(s, p, a)

    return {
        "p018_sv_fitting": [pl(fit)],
        "p021_sv_collar": [pl(cup)],
        "p018_sv_cap": [pl(cap)],
        "p019_sv_valve": [pl(pop)],
        "p020_sv_spring": [pl(spring)],
        "x005_sv_inner_washer": [pl(iw)],
        "x004_sv_inner_nut": [pl(inut)],
    }
