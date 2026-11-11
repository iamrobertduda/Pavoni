"""dimensions.yaml -> typed parameters.

Every dimension carries a source and a confidence. Photo-derived values are
stored as a ratio of the boiler outer diameter (ratio_of), so one caliper
measurement of the boiler rescales all of them.
"""
from __future__ import annotations

import math

CONF_ORDER = ["measured", "catalog", "spec", "photo", "guess"]

_SAFE = {k: getattr(math, k) for k in ("sqrt", "sin", "cos", "tan", "atan", "atan2", "radians", "degrees", "pi", "hypot")}
_SAFE.update(min=min, max=max, abs=abs)


def weakest(confs):
    return max(confs, key=CONF_ORDER.index) if confs else "guess"


class Dims:
    def __init__(self, doc: dict):
        self.machine = doc["machine"]
        self._raw: dict = doc["dims"]
        self._val: dict[str, float] = {}
        self._stack: list[str] = []

    @property
    def version(self) -> str:
        return self.machine["version"]

    def keys(self):
        return self._raw.keys()

    def __contains__(self, k):
        return k in self._raw

    def __getattr__(self, k: str) -> float:
        if k.startswith("_"):
            raise AttributeError(k)
        return self.get(k)

    def __getitem__(self, k: str) -> float:
        return self.get(k)

    def get(self, k: str) -> float:
        if k in self._val:
            return self._val[k]
        if k not in self._raw:
            raise KeyError(f"Maß '{k}' fehlt in data/dimensions.yaml")
        if k in self._stack:
            raise ValueError(f"Zirkuläre Maßdefinition: {' -> '.join(self._stack + [k])}")
        self._stack.append(k)
        try:
            e = self._raw[k]
            if "value" in e:
                v = float(e["value"])
            elif "ratio_of" in e:
                v = float(e["ratio"]) * self.get(e["ratio_of"])
            else:
                v = float(eval(e["expr"], {"__builtins__": {}}, _DimsNS(self)))  # noqa: S307 - names restricted
        finally:
            self._stack.pop()
        self._val[k] = v
        return v

    def deps(self, k: str) -> set[str]:
        e = self._raw[k]
        if "ratio_of" in e:
            return {e["ratio_of"]}
        if "expr" in e:
            import ast

            return {n.id for n in ast.walk(ast.parse(e["expr"], mode="eval")) if isinstance(n, ast.Name) and n.id in self._raw}
        return set()

    def entry(self, k: str) -> dict:
        """Resolved entry for display: value in its unit plus provenance."""
        e = dict(self._raw[k])
        e["key"] = k
        e["resolved"] = round(self.get(k), 3)
        e.setdefault("unit", "mm")
        return e

    def all_entries(self) -> dict:
        return {k: self.entry(k) for k in self._raw}


class _DimsNS(dict):
    def __init__(self, dims: Dims):
        super().__init__(_SAFE)
        self._dims = dims

    def __missing__(self, key):
        return self._dims.get(key)
