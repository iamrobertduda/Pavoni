"""Top-down skeleton (PLAN 6.1): axes, planes and interfaces between assemblies.

Every assembly is built in its own local frame and placed only via these
datums, so assemblies can be developed independently and still fit.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from build123d import Location

from .dims import Dims


@dataclass
class Datums:
    D: Dims
    frames: dict[str, Location] = field(default_factory=dict)

    def __post_init__(self):
        D = self.D
        # table plane z = 0, boiler axis = Z axis
        self.boiler_foot_z = D.boiler_foot_z
        self.boiler_shoulder_z = D.boiler_foot_z + D.boiler_cyl_h
        self.boiler_top_z = self.boiler_shoulder_z + D.boiler_shoulder_h
        # group axis: vertical, in front of the boiler
        self.group_xy = (0.0, -D.group_offset)
        self.group_bottom_z = D.group_bottom_z
        self.piston_z = D.piston_z
        # every assembly frame is identity for now (axes given in world frame)
        for a in ("boiler", "group", "group.piston"):
            self.frames.setdefault(a, Location())

    def frame(self, assembly: str) -> Location:
        """Frame of an assembly; falls back to the nearest ancestor."""
        a = assembly
        while a:
            if a in self.frames:
                return self.frames[a]
            a = a.rpartition(".")[0]
        return Location()
