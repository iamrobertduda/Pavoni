import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pavoni.data import load_all  # noqa: E402
from pavoni.paths import MANIFEST  # noqa: E402


@pytest.fixture(scope="session")
def data():
    return load_all()


@pytest.fixture(scope="session")
def manifest():
    if not MANIFEST.exists():
        pytest.skip("build/manifest.json fehlt - erst 'make cad'")
    return json.loads(MANIFEST.read_text())


@pytest.fixture(scope="session")
def ctx(data, manifest):
    from pavoni.validate import Ctx

    meshes = dict(np.load(MANIFEST.parent / "meshes.npz"))
    return Ctx(data, manifest, meshes)
