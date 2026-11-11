from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DATA = REPO / "data"
SCHEMA = DATA / "schema"
BUILD = REPO / "build"
WEB_MODEL = REPO / "web" / "public" / "models" / "pavoni.glb"
RAW_GLB = BUILD / "pavoni_raw.glb"
STEP = BUILD / "pavoni.step"
MANIFEST = BUILD / "manifest.json"
REPORT = BUILD / "validation_report.json"
