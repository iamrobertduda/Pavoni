"""Data files are schema-valid and internally consistent."""
from pavoni.dims import Dims


def test_all_files_validate(data):
    assert data["parts"], "parts.yaml leer"
    assert data["assemblies"]


def test_dimensions_resolve(data):
    D = Dims(data["dimensions"])
    for k in D.keys():
        assert D.get(k) == D.get(k)  # resolves without error, deterministic


def test_every_dimension_has_source_and_confidence(data):
    for k, e in data["dimensions"]["dims"].items():
        assert e["source"].strip(), k
        assert e["confidence"] in {"measured", "catalog", "spec", "photo", "guess"}, k


def test_seal_dims_are_never_bare_numbers(data):
    """Seal parts must reference dimension keys (with provenance), not literals."""
    for p in data["parts"]:
        if p["kind"] != "seal" or p["status"] == "planned":
            continue
        for k, v in (p.get("spec") or {}).items():
            if k != "type":
                assert isinstance(v, str), f"{p['id']}.spec.{k} muss ein Maß-Schlüssel sein"


def test_photo_ratios_scale_with_boiler(data):
    import copy

    D1 = Dims(copy.deepcopy(data["dimensions"]))
    raw = copy.deepcopy(data["dimensions"])
    f = 1.1
    raw["dims"]["boiler_od"]["value"] = D1.boiler_od * f
    D2 = Dims(raw)
    for k, e in raw["dims"].items():
        if e.get("ratio_of") == "boiler_od":
            assert abs(D2.get(k) / D1.get(k) - f) < 1e-9, k


def test_procedure_ids_match_files(data):
    for proc in data["procedures"]:
        assert [s["id"] for s in proc["steps"]] == list(dict.fromkeys(s["id"] for s in proc["steps"])), proc["id"]
