"""Built model: manifest consistency, proportions, collision machinery."""
import numpy as np
import pytest

from pavoni.dims import Dims
from pavoni.proportions import evaluate


def test_manifest_has_every_built_part(data, manifest):
    for p in data["parts"]:
        if p["status"] == "planned":
            continue
        for i in p["instances"]:
            assert i in manifest["instances"], i


def test_solids_valid(manifest):
    for i, v in manifest["instances"].items():
        assert v["valid"] and v["volume"] > 0, i


def test_proportions_within_tolerance(data, manifest, ctx):
    D = Dims(data["dimensions"])
    res = evaluate(data["proportions"], manifest, D.boiler_od, ctx.meshes)
    fails = [f"{r['name']}: {r['value']} vs {r['target_mm']} ({r['dev']:+.1%})" for r in res if r["status"] == "fail"]
    assert not fails, "\n".join(fails)


def test_collision_detects_seal_in_groove(ctx):
    """Path check must report a seal pushed sideways out of its groove."""
    seal = "p080_piston_seal__1"
    piston = "p079_piston__1"
    if seal not in ctx.inst or piston not in ctx.inst:
        pytest.skip("Kolben/Dichtung nicht gebaut")
    hit = ctx.path_collisions([seal], [piston], np.array([1.0, 0, 0]), 10.0)
    assert hit and hit["hit"] == piston
    # moving along the axis out of a closed groove also collides with the flank
    hit = ctx.path_collisions([seal], [piston], np.array([0, 0, -1.0]), 20.0)
    assert hit


def test_touching_parts_do_not_collide(ctx):
    """Seal sitting in its groove (touching) is not a collision at travel 0."""
    seal = "p080_piston_seal__1"
    piston = "p079_piston__1"
    if seal not in ctx.inst:
        pytest.skip()
    assert ctx.path_collisions([seal], [piston], np.array([0, 0, -1.0]), 0.0) is None
