"""Top-down skeleton (PLAN 6.1): axes, planes and interfaces between assemblies.

Every assembly is built in its own local frame and placed only via these datums,
so assemblies can be developed independently and still fit. All numbers come from
data/dimensions.yaml; this file only combines them.

Coordinates: mm, Z up, origin = boiler axis on the table, -Y front, +X right.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from build123d import Location

from .dims import Dims


def unit(v):
    n = math.sqrt(sum(c * c for c in v))
    return tuple(c / n for c in v)


@dataclass
class Datums:
    D: Dims
    frames: dict[str, Location] = field(default_factory=dict)

    def __post_init__(self):
        D = self.D
        R = D.boiler_od / 2
        self.R = R
        # ---------------------------------------------------------------- boiler
        self.boiler_foot_z = D.boiler_foot_z  # underside of the flared foot ring
        self.boiler_shoulder_z = D.boiler_foot_z + D.boiler_cyl_h
        self.boiler_seam_z = D.boiler_foot_z + D.boiler_seam_frac * D.boiler_cyl_h
        self.neck_r = D.boiler_neck_od / 2
        self.cone_top_z = self.boiler_shoulder_z + D.boiler_shoulder_h
        self.neck_top_z = self.cone_top_z + D.boiler_neck_h
        # cone: radius r -> height z on the outer surface
        self.cone_slope = D.boiler_shoulder_h / (R - self.neck_r)  # dz/dr (negative direction)
        self.cone_normal_tilt = math.atan2(D.boiler_shoulder_h, R - self.neck_r)  # outward normal, angle from vertical
        # bottom: threaded neck through the base, element seals on its end face
        self.bottom_neck_end_z = D.boiler_foot_z - D.bottom_neck_h
        # ---------------------------------------------------------------- base / mount / heating
        self.base_under_boiler_z = D.boiler_foot_z - D.base_gasket_upper_t  # base sheet top under the foot
        self.base_top_z = D.base_h
        self.ring_top_z = self.base_under_boiler_z - D.base_wall - D.base_gasket_lower_t
        self.ring_bottom_z = self.ring_top_z - D.base_ring_h
        self.element_flange_top_z = self.bottom_neck_end_z
        self.base_front_y = -(D.base_len - D.base_rear_overhang)
        self.base_rear_y = D.base_rear_overhang
        # ---------------------------------------------------------------- group (vertical axis in front)
        self.group_xy = (0.0, -D.group_offset)
        self.group_bottom_z = D.group_bottom_z
        self.group_arm_z = D.group_arm_z
        self.group_flange_y = -(R + D.group_boss_h)  # flat contact face on the boiler front boss
        # Chain from the photo-measured underside of the group upwards through catalog parts
        # (mouth depth, screen 14, 2.5 mm play, piston, rod 111, nuts). Anchored at ONE end
        # only: the resulting top of the cap nut is compared with the photo (group_nut_top_z)
        # as a proportion, it does not drive the geometry. Anchoring both ends pushed the
        # residual into the mouth depth, which only worked for one boiler diameter.
        self.mouth_depth = D.group_mouth_depth
        self.screen_face_z = D.group_bottom_z + self.mouth_depth
        self.screen_top_z = self.screen_face_z + D.screen_h
        self.piston_z = self.screen_top_z + D.piston_screen_gap  # piston underside at rest (lever down)
        self.rod_bottom_z = self.piston_z + D.rod_end_in_piston
        self.rod_top_z = self.rod_bottom_z + D.rod_len
        self.cap_nut_top_z = self.rod_top_z + (D.cap_nut_h - D.cap_nut_engage)
        self.cap_nut_bottom_z = self.cap_nut_top_z - D.cap_nut_h
        self.lock_nut_bottom_z = self.cap_nut_bottom_z - D.lock_nut_h
        self.tower_top_z = self.lock_nut_bottom_z - D.piston_screen_gap  # lock nut = down-stop (Q19, Q20)
        self.sleeve_bottom_z = self.screen_top_z
        self.sleeve_top_z = self.sleeve_bottom_z + D.sleeve_len
        self.ceiling_bottom_z = self.sleeve_top_z
        self.ceiling_top_z = self.sleeve_top_z + D.ceiling_t
        self.bell_top_z = D.group_bottom_z + D.group_bell_h
        # outer cylinder ends below the sleeve top, whatever the photo ratio says: the casting
        # has to enclose the catalog parts inside it
        self.cyl_top_z = min(D.group_bottom_z + D.group_cyl_top, self.sleeve_top_z - 1.5)
        self.roller_z = self.tower_top_z - D.roller_od / 2 - D.tower_cap_t
        self.roller_y = self.group_xy[1] + D.lever_pivot_back
        self.lever_rest_rad = math.radians(D.lever_rest_deg)
        self.front_pin_z = self.roller_z - D.lever_pivot_back * math.tan(self.lever_rest_rad)
        self.front_pin_y = self.group_xy[1]
        # ---------------------------------------------------------------- sight glass (left side)
        # sight glass sits radially on the left, turned slightly to the rear (PLAN 2.2)
        self.sg_azimuth = math.asin(D.sg_axis_back / D.sg_axis_r)  # rotation about Z from -X towards +Y
        self.sg_x = -D.sg_axis_r * math.cos(self.sg_azimuth)
        self.sg_y = D.sg_axis_r * math.sin(self.sg_azimuth)
        self.sg_upper_z = D.sg_upper_z
        glass_engage = D.sg_boss_reach - D.glass_seal_h - D.glass_proud  # glass end short of the nipple axis
        self.sg_lower_z = self.sg_upper_z - (D.glass_len + 2 * glass_engage)
        # ---------------------------------------------------------------- steam valve (behind the neck)
        self.steam_z = self.boiler_shoulder_z + D.steam_z_above_shoulder
        self.steam_y = D.steam_back
        t = self.cone_normal_tilt  # stub perpendicular to the shoulder cone (PLAN 2.2: schräg in den Konus)
        self.steam_stub_dir = (0.0, -math.sin(t), -math.cos(t))  # from the tube down into the cone
        # where the stub axis meets the cone surface
        s = self._cone_hit((0.0, self.steam_y, self.steam_z), self.steam_stub_dir)
        self.steam_stub_len = s
        self.steam_entry = tuple(p + d * s for p, d in zip((0.0, self.steam_y, self.steam_z), self.steam_stub_dir))
        self.steam_x_left = -D.steam_total_w / 2
        self.steam_x_right = D.steam_total_w / 2
        # ---------------------------------------------------------------- safety valve (right, on the cone)
        phi = math.radians(D.sv_azimuth)  # from +X towards +Y (rear)
        b = self.cone_normal_tilt
        self.sv_axis = unit((math.cos(phi) * math.sin(b), math.sin(phi) * math.sin(b), math.cos(b)))
        r_sv = 0.5 * (R + self.neck_r)
        self.sv_base = (r_sv * math.cos(phi), r_sv * math.sin(phi), self.cone_z(r_sv))
        # ---------------------------------------------------------------- frames
        # explode axes in parts.yaml/assemblies.yaml are given in these frames (rotation only):
        # sight glass: local -X = radially outwards; safety valve: local +Z = valve axis
        from build123d import Plane, Vector

        self.frames["boiler.sight_glass"] = Location((0, 0, 0), (0, 0, 1), -math.degrees(self.sg_azimuth))
        sv_x = Vector(-self.sv_axis[1], self.sv_axis[0], 0).normalized()
        self.frames["boiler.safety_valve"] = Location(Plane(origin=(0, 0, 0), x_dir=sv_x, z_dir=self.sv_axis))
        for a in ("boiler", "mount", "heating", "electrical", "base", "portafilter"):
            self.frames.setdefault(a, Location())

    # helpers ------------------------------------------------------------------
    def cone_z(self, r: float) -> float:
        """Height of the outer cone surface at radius r (neck_r <= r <= R)."""
        return self.boiler_shoulder_z + (self.R - r) * self.cone_slope

    def _cone_hit(self, p, d) -> float:
        """Distance along d from p to the outer cone surface (bisection)."""
        lo, hi = 0.0, 200.0
        for _ in range(60):
            mid = (lo + hi) / 2
            x, y, z = (p[i] + d[i] * mid for i in range(3))
            r = math.hypot(x, y)
            above = z > (self.cone_z(min(max(r, self.neck_r), self.R)) if r <= self.R else self.boiler_shoulder_z)
            lo, hi = (mid, hi) if above else (lo, mid)
        return (lo + hi) / 2

    def frame(self, assembly: str) -> Location:
        """Frame of an assembly; falls back to the nearest ancestor, then identity."""
        a = assembly
        while a:
            if a in self.frames:
                return self.frames[a]
            a = a.rpartition(".")[0]
        return Location()

    def report(self) -> dict:
        keys = [k for k, v in vars(self).items() if isinstance(v, (int, float, tuple)) and k not in ("D",)]
        return {k: (round(v, 2) if isinstance(v, float) else tuple(round(c, 3) for c in v) if isinstance(v, tuple) else v) for k, v in
                ((k, getattr(self, k)) for k in keys)}
