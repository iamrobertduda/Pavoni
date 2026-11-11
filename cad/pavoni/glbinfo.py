"""Minimal GLB reader: node names, primitive and triangle counts (no deps)."""
from __future__ import annotations

import json
import struct
from pathlib import Path


def read_glb_json(path: Path) -> dict:
    b = Path(path).read_bytes()
    magic, _ver, _len = struct.unpack("<4sII", b[:12])
    if magic != b"glTF":
        raise ValueError(f"{path} ist kein GLB")
    clen, ctype = struct.unpack("<I4s", b[12:20])
    if ctype != b"JSON":
        raise ValueError("erster Chunk ist nicht JSON")
    return json.loads(b[20 : 20 + clen])


def glb_stats(path: Path) -> dict:
    j = read_glb_json(path)
    acc = j.get("accessors", [])
    prims = 0
    tris = 0
    for m in j.get("meshes", []):
        for p in m["primitives"]:
            prims += 1
            if "indices" in p:
                tris += acc[p["indices"]]["count"] // 3
            else:
                tris += acc[p["attributes"]["POSITION"]]["count"] // 3
    return {
        "nodes": [n.get("name", "") for n in j.get("nodes", [])],
        "primitives": prims,
        "triangles": tris,
        "bytes": Path(path).stat().st_size,
        "extensions": j.get("extensionsUsed", []),
    }
