"""Calibration: the model must survive the owner entering a measured boiler diameter.

All photo-derived dimensions are ratios of boiler_od, while catalog parts keep their size.
The two only fit together if the geometry is anchored sensibly (see datums.py). This test
rebuilds the whole model for other diameters and runs the geometric checks on each.
"""
import copy

import pytest

from pavoni.assembly import build_model
from pavoni.export import collect
from pavoni.validate import BOILER_OD_RANGE, geometry_report

# both ends of the supported range and a value between them and the default
DIAMETERS = [BOILER_OD_RANGE[0], 100.0, 110.0, BOILER_OD_RANGE[1]]


@pytest.mark.parametrize("boiler_od", DIAMETERS)
def test_model_builds_and_validates_for_boiler_diameter(data, boiler_od):
    variant = copy.deepcopy(data)
    variant["dimensions"]["dims"]["boiler_od"]["value"] = boiler_od
    model = build_model(data=variant)
    instances, assemblies, meshes, _ = collect(model)
    built = {i for p in variant["parts"] if p["status"] != "planned" for i in p["instances"]}
    assert set(instances) == built
    rep = geometry_report(variant, instances, assemblies, meshes)
    errors = [f"{check}: {msg}" for check, c in rep.checks.items() for msg in c["errors"]]
    assert not errors, f"boiler_od={boiler_od}:\n" + "\n".join(errors)
