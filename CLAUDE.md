# CLAUDE.md - Kurzregeln für dieses Repo

Zerlegbares 3D-Modell der La Pavoni Professional (Millennium). Verbindliche Spezifikation: `PLAN.md`.
Fortschritt: Checkboxen in `PLAN.md` Abschnitt 12 und `status` je Teil in `data/parts.yaml`.

## Befehle
- `make setup` - Python-venv (uv, `cad/.venv`) und `npm ci` in `web/`
- `make cad` - build123d → `build/pavoni_raw.glb`, `pavoni.step`, `manifest.json`, `meshes.npz` → optimiertes `web/public/models/pavoni.glb`
- `make validate` - Prüfungen PLAN 11.1 (Bericht `build/validation_report.json`)
- `make web` - YAML → `web/src/generated/data.json`, Typecheck, Vite-Build
- `make test` - pytest, vitest, oxlint, Playwright-E2E
- `make renders` / `make overlay` - PNGs nach `artifacts/renders/` bzw. `artifacts/overlays/`
- `make all` - cad, validate, web, test, renders

## Regeln
- **Teile-ID** = CAD-Label = GLB-Knoten = Eintrag in `parts.yaml`. Nur `[a-z0-9_]`, Instanzen `<id>__<n>`.
- **Kein Maß im CAD-Code.** Alles aus `data/dimensions.yaml`, jedes Maß mit `source` und `confidence`.
  Foto-Maße als `ratio_of: boiler_od`. Geschätzte Maße nie als Tatsache ausgeben, schon gar nicht bei Dichtungen.
- Ein reales Teil = ein Solid. Hohlteile hohl. Dichtungen in Nennmaß, Nut im Gegenstück modellieren.
- Gewinde nur kosmetisch; Gewindebezeichnung als `thread` in `parts.yaml`.
- Rundungen ins Drehprofil legen (`lib.revolve_rz` mit Radius je Ecke), keine nachträglichen OCCT-Fillets.
- Koordinaten: mm, Z oben, Ursprung Kesselachse ∩ Tisch, −Y vorn (Gruppe), +X rechts. GLB: m, Y oben.
- `requires_removed` darf Baugruppen-IDs enthalten (= als Einheit abgenommen, z. B. `group`).
  `carrier`: elastisches Teil wird über diesen Träger gezogen (Ausbaupfad ignoriert den Träger).
- Nach jeder Modellier-Iteration: `make cad validate renders`, PNGs ansehen, mit `reference/photos/` vergleichen.
  Erst dann `status: verified`.
- `build123d`: `bounding_box()`/`volume` löschen die Tessellierung - in `export.py` zuletzt vernetzen.
- Repo ist öffentlich: keine fremden Bilder/Zeichnungen committen, nur verlinken (`reference/SOURCES.md`).
- Kein Pull Request und kein GitHub-Pages-Deployment ohne Freigabe des Besitzers.
