# La Pavoni Professional - zerlegbares 3D-Modell. Siehe PLAN.md und CLAUDE.md.
PY      := cad/.venv/bin/python
SHELL   := /bin/bash
.PHONY: setup cad validate web test renders overlay all clean e2e

setup:            ## Python-venv (uv) und npm-Abhängigkeiten
	cd cad && uv venv -q --allow-existing .venv -p 3.13 && uv pip install -q -p .venv/bin/python -r pyproject.toml
	cd web && npm ci --no-audit --no-fund

cad:              ## CAD bauen -> build/pavoni_raw.glb, pavoni.step, manifest.json -> optimiertes GLB
	cd cad && .venv/bin/python -m pavoni.export
	cd web && node scripts/optimize-glb.mjs ../build/pavoni_raw.glb public/models/pavoni.glb

validate:         ## PLAN 11.1: Abgleich, Gültigkeit, Durchdringung, Ausbaupfade, Hüllmaß, Budgets, Anleitungen
	cd cad && .venv/bin/python -m pavoni.validate

web:              ## Daten -> JSON, Typecheck, Vite-Build
	cd web && npm run --silent build

test:             ## pytest, vitest, Lint, E2E
	cd cad && .venv/bin/python -m pytest -q
	cd web && npx vitest run && npx oxlint src scripts && npx playwright test --trace off

renders:          ## feste Ansichten -> artifacts/renders/*.png
	node scripts/render_views.mjs

overlay:          ## Renderings halbtransparent über die Referenzfotos -> artifacts/overlays/
	node scripts/overlay.mjs

all: cad validate web test renders

clean:
	rm -rf build artifacts web/dist web/public/models web/src/generated
