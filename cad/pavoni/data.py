"""Load and schema-validate the YAML data under data/."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from .paths import DATA, SCHEMA


@lru_cache(maxsize=None)
def _registry() -> Registry:
    resources = []
    for p in SCHEMA.glob("*.schema.json"):
        doc = json.loads(p.read_text())
        resources.append((doc["$id"], Resource.from_contents(doc)))
    return Registry().with_resources(resources)


def _schema(name: str) -> dict:
    return json.loads((SCHEMA / f"{name}.schema.json").read_text())


class DataError(Exception):
    pass


def validate(doc, schema_name: str, label: str) -> None:
    v = Draft202012Validator(_schema(schema_name), registry=_registry())
    errors = sorted(v.iter_errors(doc), key=lambda e: list(e.absolute_path))
    if errors:
        msg = "\n".join(f"  {label}:{'/'.join(map(str, e.absolute_path))}: {e.message}" for e in errors[:30])
        raise DataError(f"{label} verletzt {schema_name}.schema.json:\n{msg}")


def load_yaml(path: Path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


@lru_cache(maxsize=None)
def load_all() -> dict:
    """Return all data files, validated against their schemas."""
    out = {}
    for name, schema in [
        ("dimensions", "dimensions"),
        ("parts", "parts"),
        ("assemblies", "assemblies"),
        ("tools", "tools"),
        ("overlaps", "overlaps"),
        ("views", "views"),
        ("proportions", "proportions"),
    ]:
        p = DATA / f"{name}.yaml"
        doc = load_yaml(p)
        if doc is None:
            doc = [] if name not in ("dimensions", "views") else {}
        validate(doc, schema, p.name)
        out[name] = doc
    procs = []
    for p in sorted((DATA / "procedures").glob("*.yaml")):
        doc = load_yaml(p)
        validate(doc, "procedure", f"procedures/{p.name}")
        if doc["id"] != p.stem:
            raise DataError(f"procedures/{p.name}: id '{doc['id']}' muss dem Dateinamen entsprechen")
        procs.append(doc)
    out["procedures"] = procs
    return out
