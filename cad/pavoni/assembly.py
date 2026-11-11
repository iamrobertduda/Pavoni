"""Collect all part modules into one model keyed by instance id."""
from __future__ import annotations

import importlib
import time
from dataclasses import dataclass, field
from types import SimpleNamespace

from build123d import Solid

from .data import load_all
from .datums import Datums
from .dims import Dims
from .parts import MODULES


@dataclass
class Model:
    data: dict
    D: Dims
    T: Datums
    solids: dict[str, Solid] = field(default_factory=dict)  # instance id -> solid (world, mm)
    part_of: dict[str, str] = field(default_factory=dict)  # instance id -> part id
    timings: dict[str, float] = field(default_factory=dict)

    @property
    def parts(self) -> dict[str, dict]:
        return {p["id"]: p for p in self.data["parts"]}


class BuildError(Exception):
    pass


def build_model(modules: list[str] | None = None, data: dict | None = None) -> Model:
    """Build all parts. `data` overrides the files under data/ (e.g. another boiler diameter)."""
    data = data or load_all()
    D = Dims(data["dimensions"])
    T = Datums(D)
    m = Model(data=data, D=D, T=T)
    parts = m.parts
    ctx = SimpleNamespace(D=D, T=T, parts=parts)
    errors = []
    for name in modules or MODULES:
        mod = importlib.import_module(f"pavoni.parts.{name}")
        t0 = time.time()
        out = mod.build(ctx)
        m.timings[name] = round(time.time() - t0, 2)
        for pid, solids in out.items():
            if pid not in parts:
                errors.append(f"{name}: Teil '{pid}' fehlt in parts.yaml")
                continue
            inst = parts[pid]["instances"]
            if len(solids) != len(inst):
                errors.append(f"{pid}: {len(solids)} Solids gebaut, parts.yaml nennt {len(inst)} Instanzen")
                continue
            for iid, s in zip(inst, solids):
                if not isinstance(s, Solid):
                    errors.append(f"{iid}: kein Solid ({type(s).__name__})")
                    continue
                m.solids[iid] = s
                m.part_of[iid] = pid
    for pid, p in parts.items():
        if p["status"] != "planned" and not any(m.part_of.get(i) == pid for i in p["instances"]):
            errors.append(f"{pid}: status '{p['status']}', aber kein Modul baut es")
        if p["status"] == "planned" and any(m.part_of.get(i) == pid for i in p["instances"]):
            errors.append(f"{pid}: wird gebaut, steht aber noch auf status 'planned'")
    if errors:
        raise BuildError("\n".join(errors))
    return m
