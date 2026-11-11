# La Pavoni Professional (Millennium) — zerlegbares 3D-Modell: Umsetzungsplan

Stand: 2026-11-11 · Status: in Umsetzung, siehe Abschnitt 12 (Checkboxen) und 16 (Umsetzungsnotizen).
Leser: der Build-Agent, der diesen Plan umsetzt, und der Besitzer der Maschine.

## 0. Kurzfassung

Gebaut wird eine Web-App, in der die Maschine als 3D-Modell aus **echten Einzelteilen** besteht:
jedes Teil anklickbar, die Maschine schrittweise zerlegbar, mit Schnittansicht, Dichtungs-Übersicht
und geführten Reparatur-Anleitungen (z. B. Kolbendichtungen tauschen).

Technische Kernentscheidung: **Geometrie als parametrischer CAD-Code (build123d, Python) → GLB →
Three.js-Viewer (React Three Fiber)**. Kein Blender-MCP. Begründung in Abschnitt 3; die Pipeline ist
in der Cloud-Umgebung bereits end-to-end verifiziert (Abschnitt 3.3).

Die größte Unsicherheit ist nicht die Software, sondern die **Maßhaltigkeit**: Es gibt keine
öffentlichen CAD-Daten. Deshalb trägt jedes Maß eine Quelle und eine Konfidenz, und der Besitzer
kann Messwerte nachliefern, die das Modell ohne Code-Änderung korrigieren (Abschnitt 5.2, 14).

## 1. Ziel und Nicht-Ziele

**Ziel**

1. Vollständiges 3D-Modell der La Pavoni Professional (Chrom, Millennium-Gruppe), jedes reale
   Bauteil als eigener Körper (ca. 100 Positionen, ca. 120–140 Instanzen).
2. Zerlegen in physikalisch plausibler Reihenfolge: Die App weiß, was vorher ausgebaut sein muss.
3. Reparaturhilfe: Wo sitzt welche Dichtung, wie herum, welches Werkzeug, welche Reihenfolge,
   welches Ersatzteil (Bezeichnung, Maße, Suchbegriffe).
4. Am Tablet/Handy neben der Maschine benutzbar (Touch, statische Seite, offline-tauglich nach
   erstem Laden).

**Nicht-Ziele**

- Kein Fertigungs-CAD mit verbürgten Toleranzen. Maße sind so gut wie ihre Quelle.
- Keine Strömungs-, Thermik- oder Elektrosimulation. Verkabelung nur schematisch.
- Kein fotorealistischer Schmutz/Verschleiß. Sauberer Chrom-Look genügt.
- Kein Blender-Workflow, keine handmodellierten Meshes.

## 2. Die konkrete Maschine

Modell: La Pavoni Professional, Chrom-Basis, Millennium-Gruppe (51-mm-Siebträger).
Laut Versionshistorie (Quelle Q1) gibt es zwei in Frage kommende Generationen:

| Version | Baujahre | Unterschied |
|---|---|---|
| v3.0 | 2001–2007 | neue Gruppe mit Kunststoff-/Teflon-Hülse |
| v3.1 | ab 2007 | wie v3.0, aber Messingkolben, geänderte Basis und Unterboden |

**Typenschild** (Foto D1, Unterseite): „LA PAVONI · Mod. PROFESSIONAL · Capacità l 1,6 · V 230 ~ ·
W 1000 · Made in Italy“. Ein Baujahr steht nicht darauf. Die Version bleibt damit offen → Parameter
`machine.version` in `dimensions.yaml`, Standard `v3.1`. Klären lässt sie sich beim ersten Zerlegen
(Kolben aus Messing = v3.1, aus Kunststoff = v3.0) oder über einen Aufkleber/Datumsstempel im Inneren
der Basis (Abschnitt 14).

### 2.1 Vorhandene Fotos des Besitzers

Zehn Fotos unter `reference/photos/` (Metadaten entfernt, Bilddaten unverändert; Zuordnung auch in
der dortigen `README.md`). Alles Ablesbare steht zusätzlich hier und in Abschnitt 8.2 als Text und Zahl.

| Datei | Blickrichtung | Wert für das Modell |
|---|---|---|
| `A1_front-left_bare.jpg` | schräg von links-vorn, ohne Siebträger und Tropfgitter | Gesamtform, Manometer-Skala |
| `A2_rear-right.jpg` | schräg von rechts-hinten | Dampflanze, Sicherheitsventil |
| `B1_base-front_closeup.jpg` | Nahaufnahme Basis-Stirnseite | Emblem, Tropfgitter, Basis-Profil |
| `B2_rear.jpg` | **gerade von hinten** | Kessel-Proportionen, Dampfhahn-Baugruppe, Schauglas, Kabelaustritt |
| `B3_left.jpg` | **gerade von links** (Bedienersicht), mit Siebträger | Achsabstände, Höhen, Gruppe, Hebel, Schalter |
| `C1_front-left.jpg`, `C2_front-left_wide.jpg`, `C3_front-left.jpg` | schräg von links-vorn, Maschine komplett | Gesamteindruck, Siebträger, Tropfgitter |
| `C4_left_far.jpg` | schräg von links, aus größerer Entfernung | Silhouette mit wenig Perspektive |
| `D1_type-label_underside.jpg` | Unterseite | Typenschild; schwarze Kunststoff-Bodenplatte (Pos. 36) mit zwei großen runden Öffnungen und mehreren kleinen Bohrungen |

B2 und B3 sind die Hauptreferenzen für Proportionen (Abschnitt 8.2).

### 2.2 Anordnung der Baugruppen

Richtungen aus Sicht des Bedieners, der vor der Gruppe steht („vorn“ = Gruppe, Tropfschale, Emblem):

- **Gruppe:** vorn am Kessel, an kurzem waagerechtem Arm mit Flansch. Armachse knapp unter der
  Schulterkante des Kessels.
- **Schauglas mit Manometer:** links am Kessel, etwa 90° zur Gruppe, minimal nach hinten versetzt.
  Das Manometer sitzt auf dem oberen Schauglas-Anschluss, Zifferblatt zeigt nach vorn.
- **Dampfhahn-Baugruppe:** ein waagerechtes Rohr quer hinter dem Kesselhals, über dem Schulterkonus.
  Von links nach rechts: schwarzer Sternknauf, Spindel, Sechskant-Mutter, Ventilkörper, mittig ein
  Stutzen schräg nach unten in den Konus, Bund, Schwenkstück mit geschlossenem Rohrende; daran hängt
  die Dampflanze rechts außen nach unten.
- **Sicherheitsventil:** rechts auf dem Schulterkonus, senkrecht zur Konusfläche nach außen geneigt,
  mit Sechskant am Fuß. Genauen Umfangswinkel an Referenzbildern prüfen.
- **Schalter:** linke Längsseite der Basis, etwa in der Mitte; grüner beleuchteter Wippschalter
  (0/I) in schwarzem Rahmen.
- **Netzkabel:** tritt hinten rechts aus der Basis aus; Schuko-Winkelstecker.
- **Emblem:** rund, schwarz/gold, mittig an der Stirnseite der Basis.

### 2.3 Formdetails

- **Kessel:** polierter Zylinder mit umlaufender Naht/Ringnut bei etwa 64 % der Zylinderhöhe (von
  unten). Unten ein ausgestellter Fußring, der in einem erhöhten runden Kragen der Basis sitzt. Oben
  eine konische Schulter, darauf der Einfüllhals mit schwarzem gelapptem Deckelknauf auf konischem
  schwarzem Sockel.
- **Basis:** verchromt, Grundriss ein stark abgerundetes Rechteck (hinten annähernd halbrund um den
  Kessel), Seitenwände leicht nach außen geneigt, umlaufender Absatz unter der Oberkante, schwarze
  Bodenplatte bzw. Gummikante unten. Hinten unten mittig eine kleine Aussparung.
- **Tropfschale:** schwarzer Kunststoff-Einsatz (Pos. 40) mit schwarzem Kunststoff-Gitter (Pos. 41),
  abgerundet-rechteckig, etwa zehn Querschlitze unterschiedlicher Länge, Griffmulden links und
  rechts. Das Metallgitter Pos. 42 ist bei dieser Maschine nicht verbaut.
- **Gruppe:** zylindrischer Oberteil, darunter glockenförmig erweitert; oben ein angegossener
  Ständer mit Gabel für den Hebel. Auf der Kolbenstange oben Kontermutter und Hutmutter.
- **Hebel:** zwei Bolzen mit Sicherungsringen: Drehpunkt am Ständer (zur Kesselseite versetzt) und
  Bolzen an der Kolbenstange (auf der Gruppenachse). Gabel aus Flachmaterial, verchromte Rundstange,
  schwarzer Griff. Ruhelage: etwa 24° unter der Waagerechten nach vorn.
- **Siebträger:** verchromt, schwarzer Griff, Doppelauslauf.
- **Schauglas:** Glasrohr zwischen verchromten Anschlüssen oben und unten, davor eine transparente
  U-förmige Kunststoff-Abdeckung über die ganze Höhe.

### 2.4 Zustand

Kalk-/Rostspuren am Kesselfuß (Übergang zur Basis), am unteren und oberen Schauglas-Anschluss und in
der Tropfmulde. Das deutet auf Undichtigkeiten in diesem Bereich hin → Schauglas-, Kessel/Basis- und
Gruppendichtungen haben bei den Anleitungen Priorität.

## 3. Technische Entscheidungen

### 3.1 Stack

| Thema | Entscheidung |
|---|---|
| Geometrie | **build123d** (Python, OpenCascade-Kernel), parametrisch, als Code im Repo |
| Formate | **GLB** für den Viewer, **STEP** als CAD-Archiv (und für 3D-Druck von Hilfswerkzeugen) |
| Viewer | **Vite + React + TypeScript**, three.js über **@react-three/fiber** + **drei**, State mit **Zustand** |
| Daten | YAML unter `data/`, per JSON-Schema validiert, von CAD **und** Web gelesen |
| GLB-Optimierung | `@gltf-transform/cli` (join, weld, dedup, meshopt) |
| Tests | pytest (CAD-Validierung), vitest (Logik), Playwright (E2E und Render-Screenshots) |
| Hosting | rein statisch; GitHub Pages optional und erst nach Freigabe des Besitzers |

### 3.2 Warum CAD-Code statt Blender-MCP

- **Passt zur Maschine.** Fast alles ist Drehteil oder Normteil (Kessel, Gruppe, Kolben, Muttern,
  O-Ringe, Rohre). Ein Drehprofil aus wenigen Maßen ergibt das exakte Teil; Mesh-Modellieren wäre
  hier langsamer und ungenauer.
- **Echte Volumenkörper.** Jedes Teil ist ein geschlossener Solid. Nur damit funktionieren
  Schnittansicht mit gefüllten Schnittflächen, Durchdringungsprüfung („sitzt die Dichtung wirklich
  in der Nut?“) und die automatische Prüfung der Ausbaureihenfolge.
- **Korrigierbar.** Messschieber-Wert in `dimensions.yaml` ändern → neu bauen. In Blender wäre das
  Handarbeit pro Teil.
- **Reproduzierbar und reviewbar.** Code im Git, deterministischer Build, Diffs lesbar.
- **Läuft dort, wo gebaut wird.** Blender-MCP braucht ein lokal laufendes Blender mit Add-on und
  Socket-Verbindung. Das gibt es in einer Cloud-Session nicht; build123d läuft headless per `pip`.
- **Kein visuelles Blindflug-Problem.** Der Build-Agent rendert das GLB per Headless-Chromium und
  sieht sich die PNGs an (Abschnitt 11.3).

Photogrammetrie/3D-Scan als Formquelle scheidet aus: Chrom spiegelt, Scans werden unbrauchbar.
Vorhandene Fremd-CAD-Modelle (z. B. GrabCAD) dürfen als Proportions-Referenz angesehen, aber nicht
kopiert werden (Lizenz, und ihnen fehlen die Innenteile).

### 3.3 In der Cloud-Umgebung bereits verifiziert

Diese Punkte sind getestet, nicht angenommen:

- `uv pip install build123d` → Version 0.13.0 auf Python 3.13, Installation ca. 20 s.
- Ein `Compound` mit `label` und `children` ergibt per `export_gltf(..., binary=True)` ein GLB mit
  **benannter Knoten-Hierarchie** (Baugruppe → Teil). `export_step` funktioniert für dieselbe Baugruppe.
- Das GLB ist in **Metern und Y-up** (100 mm im CAD → 0,1 im GLB). Der Viewer darf keine
  Millimeter annehmen.
- build123d exportiert **jede B-Rep-Fläche als eigenes Primitive**. three.js lädt ein Teil dadurch
  als `Group` namens `<label>` mit Kind-Meshes `<label>_1 … <label>_n`. Folgen: (a) Picking muss vom
  getroffenen Mesh zum nächsten Vorfahren mit registrierter Teile-ID hochlaufen, (b) ohne
  `gltf-transform join` entstehen tausende Draw Calls.
- Headless-Chromium (vorinstalliertes Playwright, nicht neu installieren) rendert WebGL 2 mit
  `--use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader`. Ein Chrom-Material
  (`metalness 1`, `roughness ≈ 0.08`) mit Environment-Map sieht darin korrekt aus (three 0.170.0).

## 4. Architektur und Repo-Struktur

Datenfluss:

```
data/*.yaml ──┬─► cad/ (build123d) ─► build/pavoni.glb + pavoni.step + manifest.json
              │                              │
              │                    gltf-transform (join/weld/meshopt)
              │                              ▼
              └─► web/ (Vite) ◄──── web/public/models/pavoni.glb
                     │
                     └─► Viewer: Teile-IDs im GLB  ⇄  parts.yaml  ⇄  procedures/*.yaml
```

Die **Teile-ID** ist der Schlüssel, der alles verbindet: CAD-Label = GLB-Knotenname = Eintrag in
`parts.yaml` = Referenz in den Anleitungen.

```
PLAN.md
CLAUDE.md                 Kurzregeln und Befehle (in Phase 0 anlegen)
Makefile                  setup | cad | validate | web | renders | test | all
data/
  parts.yaml              Stückliste (Single Source of Truth)
  dimensions.yaml         alle Maße mit Quelle und Konfidenz
  tools.yaml              Werkzeuge
  procedures/*.yaml       Reparatur-Anleitungen
  schema/*.schema.json    JSON-Schemas für alle Dateien oben
cad/
  pyproject.toml
  pavoni/
    dims.py               lädt dimensions.yaml → typisierte Parameter
    datums.py             Skelett: Achsen, Ebenen, Schnittstellen der Baugruppen
    lib/                  o_ring, lip_seal, flat_gasket, hex_bolt, nut, washer, circlip, cosmetic_thread
    parts/                boiler, group, lever, sight_glass, steam, safety_valve, base,
                          electrical, portafilter (je ein Modul)
    assembly.py           Gesamt-Compound, Labels = Instanz-IDs
    export.py             GLB, STEP, manifest.json
    validate.py           Abgleich Stückliste, Durchdringung, Ausbaupfade, Hüllmaße
  tests/
web/
  src/scene/              Laden, Materialien, Picking, Explode, Schnitt
  src/state/              Zustand-Store
  src/ui/                 Teilebaum, Info-Panel, Anleitungs-Player
  src/data/               Laden/Validieren der YAML-Daten (zur Build-Zeit zu JSON)
  public/models/          generiert, gitignored
  public/env/             lokales HDRI (CC0, z. B. Poly Haven)
  e2e/
scripts/
  render_views.mjs        Playwright: feste Ansichten → artifacts/renders/*.png
  overlay.mjs             Render halbtransparent über ein Referenzfoto legen
reference/
  SOURCES.md              Links zu Quellen (keine fremden Bilder committen)
  measurements.md         Mess-Checkliste für den Besitzer
  photos/                 eigene Fotos des Besitzers
```

GLB/STEP sind Build-Artefakte (gitignored), kein Binär-Churn im Repo.

## 5. Datenmodell

### 5.1 `parts.yaml`

```yaml
- id: p080_piston_seal            # p<Pos.-Nr. der Hersteller-Explosionszeichnung>_<name>
  pos: 80                         # Positionsnummer (Abschnitt 7)
  name: {de: "Kolbendichtung (Lippendichtung)", en: "Piston lip seal", it: "Guarnizione pistone"}
  assembly: group.piston          # Baugruppen-Pfad → Teilebaum und Explode-Hierarchie
  instances: [p080_piston_seal__1, p080_piston_seal__2]
  kind: seal                      # seal | fastener | structural | electrical | accessory
  material: seal_silicone         # Schlüssel in der Material-Tabelle des Viewers
  wear_part: true
  detail_tier: A                  # A | B | C (Abschnitt 6.3)
  spec: {type: lip_seal, od: piston_seal_od, id: piston_seal_id, h: piston_seal_h}  # → dimensions.yaml
  notes: {de: "Obere Dichtung: Nut nach oben. Untere Dichtung: umgekehrt."}
  order_terms: ["La Pavoni Kolbendichtung Millennium", "361005"]
  explode: {axis: [0, 0, -1], distance_mm: 40, stage: 3}   # relativ zur Eltern-Baugruppe
  requires_removed: [p081_shower_plate, p079_piston]        # muss vorher raus (ergibt einen DAG)
```

Regeln für IDs: nur `[a-z0-9_]`. Teile ohne Position in der Hersteller-Zeichnung bekommen das Präfix
`x` (z. B. `x001_rubber_subbase`). Instanzen mit **doppeltem** Unterstrich (`__1`), weil three.js
selbst `_1`-Suffixe vergibt (Abschnitt 13).

### 5.2 `dimensions.yaml`

```yaml
piston_seal_od: {value: 44.0, unit: mm, confidence: catalog, source: "Q5 Art. 361005"}
piston_seal_id: {value: 36.0, unit: mm, confidence: catalog, source: "Q5 Art. 361005",
                 note: "Andere Quelle nennt 33 mm. Vor Bestellung am Kolben messen."}
boiler_od:      {value: 100.0, unit: mm, confidence: photo, source: "Abschnitt 8.2"}
group_offset:   {ratio_of: boiler_od, ratio: 1.09, confidence: photo, source: "Foto B3"}
```

Aus Fotos abgeleitete Maße werden als **Verhältnis zum Kesseldurchmesser** gespeichert (`ratio_of`).
Misst der Besitzer den Kessel einmal mit dem Messschieber, skaliert alles Foto-Abgeleitete mit.

`confidence` ist geordnet: `measured` > `catalog` > `spec` > `photo` > `guess`.
Kein Maß steht als Zahl im CAD-Code; alles kommt aus dieser Datei. Der Viewer zeigt die Konfidenz
als Badge am Maß. **Geschätzte Maße werden nie als Tatsache dargestellt**, vor allem nicht bei
Dichtungen (sonst bestellt der Besitzer falsch).

### 5.3 `procedures/*.yaml`

```yaml
id: piston_seals
title: {de: "Kolbendichtungen tauschen"}
difficulty: 2          # 1–5
duration_min: 45
tools: [wrench_14, wrench_10, rubber_mallet, pick, silicone_grease]
preconditions: [unplugged, cold, depressurized, boiler_empty]
steps:
  - id: s1
    title: {de: "Hutmutter und Kontermutter lösen"}
    text: {de: "…"}
    remove: [p093_group_upper_nut, p092_lock_nut]   # Teile, die dieser Schritt ausbaut
    motion: {type: unscrew, axis: group_axis}       # optional; sonst gilt explode aus parts.yaml
    highlight: [p078_piston_shaft]
    camera: group_top                               # benannte Ansicht
    warn: {de: "…"}
    reassembly: {de: "Hinweis für den Zusammenbau, z. B. Einbaurichtung, Fett"}
```

Zusammenbau ist dieselbe Schrittfolge rückwärts, ergänzt um die `reassembly`-Hinweise.
Ein Validator prüft: alle IDs existieren, und kein Schritt baut ein Teil aus, dessen
`requires_removed` noch nicht erfüllt ist.

## 6. Modellierungsregeln (CAD)

### 6.1 Koordinaten und Skelett

- Einheit mm, Z nach oben. Ursprung: Kesselachse ∩ Tischebene. −Y = vorn (Gruppe, Tropfschale),
  +X = rechts aus Sicht des Bedieners.
- **Top-down-Skelett** in `datums.py`: Kesselachse, Gruppenachse (Abstand `group_offset`),
  Flanschebene Gruppe/Kessel, Schauglas-Achse, Anschluss Dampfventil, Anschluss Sicherheitsventil,
  Oberkante Basis, Ebene Heizelement-Flansch. Jede Baugruppe wird im eigenen lokalen System gebaut
  und nur über diese Datums platziert. Dadurch lassen sich Baugruppen unabhängig (auch parallel)
  entwickeln und passen trotzdem zusammen.

### 6.2 Grundsätze

- **Ein reales Teil = ein Solid = ein Label.** Nichts verschmelzen. Mehrfachteile sind Instanzen
  derselben Geometrie.
- Hohlteile sind echte Hohlkörper mit Wandstärke (Kessel, Gruppenbohrung, Rohre, Schauglas), sonst
  ist die Schnittansicht wertlos.
- **Dichtungen** in Nennmaß (unverpresst) modellieren, der Sitz/die Nut im Gegenstück wird ebenfalls
  modelliert. Die gewollte Überdeckung steht auf einer Whitelist der Durchdringungsprüfung.
- **Gewinde nur kosmetisch** (keine Helix; sie bläht das Mesh auf). Gewindegröße als Metadatum am Teil.
- Sichtbare Chromkanten bekommen Rundungen/Fasen, sonst wirkt Chrom künstlich. Rundungen möglichst
  schon im Drehprofil als tangentiale Bögen anlegen; nachträgliche OCCT-Fillets scheitern öfter.
- Drehteile per `revolve` aus 2D-Profil. Gussartige Teile (Gruppenkörper mit Arm, Basis,
  Hebelgabel) per Loft/Sweep/Boolean. Dafür ein Zeitlimit setzen und bei Fillet-Fehlern die Form
  vereinfachen statt festzuhängen.

### 6.3 Detailstufen

| Stufe | Was | Anspruch |
|---|---|---|
| A | Alle Dichtungen und alles, woran sie sitzen: Kolben, Hülse, Kolbenstange, Gruppenbohrung, Duschsieb, Schauglas-Garnitur, Dampfventil innen, Sicherheitsventil innen, Heizelement mit Flansch, Kesselöffnungen, zugehörige Schrauben/Muttern | so maßhaltig wie die Quellen erlauben; Sitz und Einbaurichtung müssen stimmen |
| B | Außenformen: Kesselmantel, Basis, Hebel, Griffe, Siebträger, Manometer | Proportionen und Silhouette stimmen mit den Fotos |
| C | Elektrik: Pressostat, Thermostat, Schalter, Klemmblock, Kabel, Stecker | vereinfachte Körper an der richtigen Stelle |

### 6.4 Tessellierung und Budgets

- Große Chromflächen (Kessel, Gruppe, Basis) fein tessellieren (Winkelabweichung klein), denn
  Spiegelungen zeigen jede Facette. Kleinteile gröber.
- Budget nach Optimierung: GLB ≤ 15 MB, ≤ 1,5 Mio. Dreiecke, ≤ 300 Draw Calls.

## 7. Stückliste (Skelett)

Positionsnummern nach der Hersteller-Explosionszeichnung Europiccola/Professional (cod. 383131,
Stand 2007), Bezeichnungen nach Quelle Q2. Die Zeichnung selbst nicht ins Repo legen, nur verlinken.

| Baugruppe | Positionen |
|---|---|
| Kessel | 1 Kesseldeckel · 2 Deckeldichtung · 3 Kessel · 4 Dichtung Kessel/Basis oben · 6 Dichtung Kessel/Basis unten · 7 Ring Kessel/Basis |
| Heizung | 8 Heizelement-Dichtung · 9 Heizelement · 10 Schraube M5×12 |
| Elektrik | 11 Pressostat-Rohr (Kupfer) · 12 Pressostat · 13 Sicherheitsthermostat · 14 Thermostat-Schutz · 15 Zahnscheibe · 16 Mutter M4 Messing · 26 Schalter · 27 Kabeltülle · 28 Kabel mit Stecker · 30 Zahnscheibe · 31 Blechschraube M3 · 32 Halter Anschlussdose · 33 Kabelhalter · 34 Klemmblock · 35 Mutter M3 |
| Sicherheitsventil | 17 komplett · 18 Gehäuse und Sitz · 19 Ventil mit Anti-Vakuum · 20 Feder · 21 Dampfablass-Kragen (22–25 = alte Bauart, hier nicht relevant) |
| Basis | 5 Basis · 29 Emblem · 36 Bodenplatte Kunststoff · 37 Gummifuß · 38 Stopfen Bodenplatte · 39 Basisschraube · 40 Tropfschale · 41 Gittereinsatz Kunststoff (42 Metallgitter: an dieser Maschine nicht verbaut) |
| Dampf | 45 Dampfhahn komplett · 46 Hahnkörper · 47 O-Ring · 48 Spindel · 49 Messingscheibe · 50 Gummischeibe · 51 Mutter · 52 Knauf · 53 Stift · 54 Dampfrohr komplett · 55 Düse (56–58 Cappuccino-Automatik: Zubehör, optional) |
| Schauglas/Manometer | 59 Halter oben · 60 Schauglas-Dichtung · 61 Mutter oben/unten · 62 Schauglas · 63 Halter unten · 64 Scheibe · 65 Messingscheibe · 66 Mutter Schauglas/Kessel · 67 Stopfen oben · 68 Manometer-Mutter · 69 Manometer · 70 Schauglas-Abdeckung (gesteckt) · 100 Scheibe |
| Gruppe | 71 komplett · 72 Gruppenkörper · 73 Kolbenstangen-Dichtung · 74 Scheibe · 75 Sicherungsring · 76 Kolbenhülse innen · 77 Hülsen-Dichtung · 78 Kolbenstange · 79 Kolben (Messing) · 80 Kolbendichtung (2×) · 81 Duschsieb · 82 Siebträger-Dichtung · 83 Kunststoff-Verbinder Steigrohr/Gruppe · 84 Wasserrohr Kessel→Gruppe · 85 Dichtung Gruppe/Kessel · 86 Schraube Gruppe/Kessel (2×) |
| Hebel | 87 Hebel · 88 Griff · 89 Rollenmutter · 90 Hebelbolzen (2×) · 91 Sicherungsring Gr. 5 · 92 Kontermutter · 93 obere Gruppenmutter |
| Siebträger | 94 komplett · 95 Siebträger · 96 Doppelauslauf · 97 Gewindestück · 88 Griff · 98 Zweier-Sieb · 99 Einer-Sieb · 101 Siebträger-Feder |
| Zubehör | 43 Tamper · 44 Messlöffel (optional) |

Offen und in Phase 2 zu klären: Stückzahlen je Position, Zuordnung der Pos. 10 (hält sie das
Heizelement?), sowie welche Positionen bei v3.0/v3.1 abweichen.

## 8. Bekannte Maße und Werkzeuge

Alle Werte sind Start-Einträge für `dimensions.yaml`. Keiner ist am Gerät gemessen.

### 8.1 Katalog- und Händlerangaben

| Größe | Wert | Konfidenz | Quelle |
|---|---|---|---|
| Hüllmaß H × B × T | 320 × 200 × 290 mm (eine Quelle: H 366). Das ist die Hülle **mit** Knäufen, nicht die Basis (siehe 8.2) | spec | Q3 |
| Gewicht | 5,5–6,2 kg | spec | Q3 |
| Kesselinhalt | 1,6 l | spec | Typenschild, Q1, Q3 |
| Betriebsdruck | 0,7–0,8 bar | spec | Q3 |
| Heizleistung, Spannung | 1000 W, 230 V | spec | Typenschild |
| Sieb-Durchmesser | 51 mm (teils als 52 angegeben) | spec | Q3 |
| Duschsieb | Ø 54 mm (Art. 327115) | catalog | Q5 |
| Kolbendichtung (2×) | Ø 44 × 36 × 5,5 mm (Art. 361005); andere Listung: 44 × 33 × 5,5 | catalog, **widersprüchlich** | Q5, Q6 |
| Siebträger-Dichtung | O-Ring 60 × 50 × 5 bzw. 5,5 mm NBR (Art. 465301) | catalog | Q4, Q5 |
| Schauglas-Dichtung (2×) | Ø 15 × 9 × 5 mm Silikon (Art. 362020) | catalog | Q5 |
| O-Ring „03112“ EPDM (Art. 465128) | Normmaß nachschlagen; Einbauort klären (vermutlich Gruppe/Kessel) | catalog | Q5 |
| O-Ring „OR 176“ (Art. 465225) | Normmaß nachschlagen; Einbauort klären | catalog | Q5 |
| Dichtung Kessel/Basis | Ø 93 × 80 × 1,5 mm (Art. 362019) | catalog | Q6 |
| Heizelement-Dichtung | alte Bauart flach 82 × 68 × 2; Edelstahl-Element: O-Ring in eigenem Sitz, Maß offen | catalog / offen | Q6, Q8 |
| Sicherungsring Kolbenstange | „J-20“, Ø 21,5 mm | catalog | Q6 |

O-Ring-Normmaße aus einer Normtabelle übernehmen, nicht raten.

### 8.2 Proportionen aus den Fotos

Abgelesen aus Foto B3 (gerade von links) und B2 (gerade von hinten), angegeben als Vielfaches des
Kessel-Außendurchmessers **D**. Handyfotos aus kurzer Distanz: Genauigkeit etwa ± 10 %, Konfidenz
`photo`. Die Zahlen ersetzen keine Messung, reichen aber für Blockout und Proportionen.

**Maßstab.** Mit D = 100 mm ergibt die Hülle aus den Fotos 191 mm Breite (Dampfknauf bis
Lanzen-Rohrende), 298 mm Tiefe (Dampfknauf bis Basis-Vorderkante) und 314 mm Höhe (Tisch bis
Deckelknauf). Das passt zu den Katalogwerten 200 × 290 × 320; rechnerisch D ≈ 97–105 mm. Zusätzlich
misst das Manometer in beiden Ansichten 0,43 D, was zu einem 40-mm-Manometer mit Zierring passt.
Arbeitswert daher **D = 100 mm**. Daraus folgt auch: Die Katalogmaße beschreiben die Hülle ohne
Hebel und Siebträgergriff, die Basis selbst ist deutlich kleiner.

| Größe | × D | mm bei D = 100 |
|---|---|---|
| Kessel-Außendurchmesser | 1,00 | 100 |
| Kesselzylinder, Fußunterkante bis Schulterkante | 1,8–1,9 | 180–190 |
| Naht/Ringnut, Höhe über Fußunterkante | 64 % der Zylinderhöhe | ca. 118 |
| Schulterkonus, Höhe | 0,26 | 26 |
| Deckelknauf, Durchmesser | 0,60 | 60 |
| Oberkante Deckelknauf über Konus-Oberkante (Hals, Sockel, Knauf) | 0,6 | 60 |
| Kesselfuß-Unterkante über Tisch (Basis-Plateau) | 0,5 | 50 |
| Gesamthöhe Tisch bis Deckelknauf | 3,14 | 314 |
| Basis Länge × Breite | 2,5 × 1,6 | 250 × 160 |
| Basis Höhe (Chrom-Schürze samt Bodenplatte) | 0,5 | 50 |
| Abstand Kesselachse zu Gruppenachse | 1,09 | 109 |
| Gruppenarm, Achshöhe über Tisch | 2,0 | 200 |
| Gruppe Oberteil, Durchmesser | 0,54 | 54 |
| Gruppe Glocke, größter Durchmesser | 0,64 | 64 |
| Unterkante Gruppe (Siebträger-Ebene) über Tisch | 1,6 | 160 |
| Siebträger-Körper, Durchmesser | 0,55 | 55 |
| Auslauf-Unterkante über Tisch | 1,2 | 120 |
| Oberkante Hebelständer über Tisch | 2,8 | 280 |
| Hebel-Drehpunkt hinter der Gruppenachse | 0,20 | 20 |
| Hebelstange, Durchmesser | 0,09–0,10 | ca. 10 |
| Hebelstange sichtbar, Gabel bis Griffanfang | 1,07 | 107 |
| Schauglas-Achse, Abstand zur Kesselachse | 0,65 | 65 |
| Schauglas-Abdeckung, Höhe | 1,5 | 150 |
| Schauglas-Abdeckung, Breite × Tiefe | 0,30 × 0,23 | 30 × 23 |
| Manometer, Durchmesser | 0,43 | 43 |
| Dampfhahn-Rohrachse über Schulterkante | 0,35 | 35 |
| Dampfhahn-Rohrachse hinter der Kesselachse | 0,40–0,45 | 40–45 |
| Dampfhahn-Rohr, Durchmesser | 0,18–0,22 | ca. 20 |
| Dampfhahn-Baugruppe, Gesamtbreite | 1,91 | 191 |
| Dampfknauf, Durchmesser | 0,41–0,47 | 41–47 |
| Schalter-Rahmen, Breite × Höhe | 0,29 × 0,23 | 29 × 23 |
| Schalter-Mitte, Lage entlang der Basis | 47 % von hinten | — |

Höhenmaße über dem Tisch sind wegen des schrägen Blicks von oben am unsichersten.

### 8.3 Werkzeuge

Werkzeuge laut Wartungsanleitungen (Q7–Q10): Schlüssel 14 mm (obere Gruppenmutter und Kontermutter,
Dampfhahn), 10 mm (Schrauben Gruppe/Kessel), 17 mm (Schauglas-Muttern), Sicherungsringzange,
Haken/Pick, Gummihammer oder Holzstück, Durchschlag 3 mm (Stift im Dampfhahn-Knauf), großer
Schlitzschraubendreher (Schauglas-Kappe), Spezialschlüssel für den Basisring (ersatzweise über den
Kessel drehen), lebensmittelechtes Silikonfett.

## 9. Viewer: Funktionsumfang

**MVP**

1. Orbit/Zoom/Pan mit Maus und Touch, Chrom-Look über lokales HDRI.
2. Teil anklicken → Hervorhebung und Info-Panel: Name (de/en/it), Positionsnummer, Stückzahl,
   Material, Maße mit Konfidenz-Badge, Verschleißteil ja/nein, Hinweise, Suchbegriffe fürs Ersatzteil.
3. Teilebaum nach Baugruppen mit Suche, Ein-/Ausblenden, Isolieren, „alles andere transparent“.
4. Explosionsansicht: globaler Regler und je Baugruppe, **hierarchisch** (Baugruppen fahren
   auseinander, dann ihre Teile entlang der jeweiligen Achse), nicht radial vom Mittelpunkt.

**V1**

5. **Dichtungs-Karte:** ein Schalter färbt alle Dichtungen in Signalfarbe und macht den Rest
   transparent. Das ist die zentrale Reparatur-Übersicht.
6. **Schnittansicht:** verschiebbare Schnittebene mit gefüllten Schnittflächen (Stencil-Caps),
   Voreinstellungen „Schnitt durch Gruppe“, „Schnitt durch Schauglas“, „Schnitt durch Dampfventil“.
7. **Zerlege-Modus:** Teil anklicken → die App zeigt, welche Teile vorher raus müssen (aus
   `requires_removed`), und baut sie auf Wunsch in der richtigen Reihenfolge animiert aus.
8. **Anleitungs-Player:** Schritt vor/zurück, Text, Werkzeuge, Warnungen, Kamera fährt zur
   benannten Ansicht, betroffene Teile bewegen sich entlang ihres Ausbaupfads. Umschalter
   Zerlegen/Zusammenbauen.
9. Deep-Links (Teil, Anleitung, Schritt in der URL), Layout für Tablet und Handy.

**Später, falls gewünscht:** Offline-PWA, Einkaufsliste aus gewählten Anleitungen, Notizen/Fotos des
Besitzers je Teil, Sprachumschaltung de/en.

Technische Vorgaben: Materialien werden im Viewer aus dem `material`-Schlüssel der Stückliste
erzeugt (Chrom, Messing, Edelstahl, Kupfer, Gummi schwarz, Silikon, Glas mit Transmission, Bakelit,
Kunststoff), nicht aus den exportierten Farben. Für Tests stellt die App
`window.__pavoni` bereit (`select(id)`, `setExplode(x)`, `setView(name)`, `gotoStep(proc, n)`).
UI-Sprache Deutsch.

## 10. Reparatur-Anleitungen

Reihenfolge nach Nutzen für den Besitzer:

| # | Anleitung | Kernpunkte aus den Quellen |
|---|---|---|
| 1 | Kolbendichtungen tauschen | siehe Ablauf unten (Q7) |
| 2 | Siebträger-Dichtung und Duschsieb | Teil von 1, auch einzeln |
| 3 | Kolbenstangen-Dichtung | Sicherungsring, Messingscheibe, Dichtung; Ring und Scheibe ersetzen, wenn verrostet (Q7) |
| 4 | Schauglas-Dichtungen | Abdeckung abziehen (bricht leicht), Kappe lösen, Muttern 17 mm, Glas nach oben herausziehen, Scheiben und Dichtungen mit Haken entfernen (Q9) |
| 5 | Dichtung Gruppe/Kessel | nach Abnehmen der Gruppe |
| 6 | Dampfhahn-Dichtungen | Hahn mit 14 mm lösen, Stift mit 3-mm-Durchschlag austreiben, Spindel ziehen (Q10) |
| 7 | Kesseldeckel-Dichtung | einfachste Anleitung, guter Einstieg |
| 8 | Sicherheitsventil reinigen/tauschen | Feder, Ventil, Sitz |
| 9 | Heizelement-Dichtung | Bodenplatte ab, Elektrik lösen, Element ausbauen, O-Ring tauschen, nicht überdrehen (Q8) |
| 10 | Dichtungen Kessel/Basis | erst Heizelement raus, dann Kessel gegen den Uhrzeigersinn drehen; Kunststoff-Ring (ab 1996) bricht leicht (Q11) |
| 11 | Komplettzerlegung | Verkettung aller obigen |

Ablauf Anleitung 1 laut Q7 (für die Millennium-Gruppe in Phase 6 gegen weitere Quellen prüfen,
besonders den Umgang mit der Hülse Pos. 76/77):

1. Obere Gruppenmutter und Kontermutter lösen (14 mm).
2. Je einen Sicherungsring der beiden Hebelbolzen abnehmen, Bolzen ziehen, Hebel und Rollenmutter abnehmen.
3. Zwei Schrauben Gruppe/Kessel lösen (10 mm), Gruppe abnehmen. Vorsicht: Das Steigrohr hängt an der Gruppe.
4. Kolbenstange mit Gummihammer oder Holz-Zwischenlage nach unten austreiben: Kolben und Duschsieb kommen heraus.
5. Kolbendichtungen abnehmen, vorher Einbaurichtung merken.
6. Einbau: obere Dichtung mit der Nut nach oben, untere umgekehrt. Mit lebensmittelechtem Fett.
7. Die Hülsen-Dichtung (Pos. 77) nur tauschen, wenn die Hülse herausgeschraubt wurde.

Jede Anleitung beginnt mit denselben Voraussetzungen: Netzstecker gezogen, Maschine kalt, drucklos,
Kessel entleert. Anleitungen 9 und 10 betreffen netzspannungsführende Teile und den Druckkessel und
bekommen einen deutlichen Warnhinweis. Die App ist eine Sehhilfe, kein Ersatz für Fachkenntnis.

## 11. Verifikation

Nach jedem Arbeitsschritt gilt: bauen, prüfen, **Renderings ansehen**. Ein Modell, das nur
kompiliert, ist nicht fertig.

### 11.1 CAD (`make validate`)

1. **Abgleich:** Jede Instanz aus `parts.yaml` existiert als Knoten im optimierten GLB, und umgekehrt.
2. **Gültigkeit:** Jeder Solid ist gültig und geschlossen, Volumen > 0.
3. **Durchdringung:** Paarweise Schnittvolumen (mit Bounding-Box-Vorfilter) unter Toleranz;
   Ausnahmen nur über eine begründete Whitelist (Dichtungs-Verpressung, kosmetische Gewinde).
4. **Ausbaupfade:** Für jedes Teil wird geprüft, ob es sich entlang seiner Explode-Achse
   kollisionsfrei herausbewegen lässt, wenn genau die Teile aus `requires_removed` fehlen. Das
   prüft die Zerlege-Reihenfolge automatisch. Mesh-basierte Kollisionsprüfung genügt (z. B.
   trimesh mit FCL), Laufzeit im Auge behalten.
5. **Hüllmaß:** Bounding-Box aller Teile außer Hebel und Siebträgergriff gegen die Katalogwerte
   200 × 290 × 320 mm (weiche Prüfung, ± 7 %).
6. **Budgets:** Dateigröße, Dreiecke, Draw Calls.

### 11.2 Web

`tsc --noEmit`, Lint, vitest für Daten-, Explode- und Anleitungslogik, Playwright-E2E: Laden,
Teil wählen, Explode, Schnitt, eine Anleitung komplett durchklicken, Deep-Link öffnen.

### 11.3 Visuell (`make renders`)

`scripts/render_views.mjs` erzeugt feste Ansichten nach `artifacts/renders/`: vorn, links, rechts,
hinten, oben, die Blickwinkel der Besitzer-Fotos (Abschnitt 2.1; „gerade von links“ und „gerade von
hinten“ sind die wichtigsten), voll explodiert, Dichtungs-Karte, Schnitt durch die Gruppe. Zusätzlich
zum Blick auf die Bilder dienen die Proportionen aus Abschnitt 8.2 als Soll: Ein Test liest die
entsprechenden Verhältnisse aus dem Modell und vergleicht sie mit der Tabelle. Der Build-Agent sieht sich die Bilder nach jeder Modellier-Iteration an und
vergleicht mit den Referenzen. `scripts/overlay.mjs` legt ein Rendering halbtransparent über ein
Referenzfoto, um Proportionen zu prüfen. Keine pixelgenauen Bildvergleiche als Test (unter
Software-Rendering instabil).

## 12. Phasen

Jede Phase endet mit grünem `make all` und einem Commit. Fortschritt durch Abhaken hier im Plan.

**Phase 0 — Fundament**
- [x] Repo-Struktur, Makefile, `CLAUDE.md`, Python-Umgebung (uv), Vite-Projekt, JSON-Schemas.
- Abnahme: `make setup && make all` läuft auf frischem Klon durch.

**Phase 1 — Durchstich**
- [x] Drei Teile (Kesselmantel, Kolben, eine Kolbendichtung) durch die gesamte Kette: CAD → GLB →
  Optimierung → Viewer → Picking → Info-Panel → Explode-Regler → Mini-Anleitung mit zwei Schritten
  → Render-Skript → Validierung.
- Abnahme: alle Prüfungen aus Abschnitt 11 existieren und laufen, wenn auch mit wenig Inhalt.
  Erst danach beginnt die Modellier-Arbeit.

**Phase 2 — Recherche und Stückliste**
- [ ] `parts.yaml` vollständig (alle Positionen, Stückzahlen, Material, Stufe, Baugruppe,
  erster Entwurf von `explode` und `requires_removed`).
- [ ] `dimensions.yaml` mit allen Schlüsselmaßen samt Quelle und Konfidenz; `datums.py` festgelegt.
- [ ] `reference/SOURCES.md` und `reference/measurements.md` (Abschnitt 14).
- Abnahme: Schemas gültig; jedes Teil hat alle Pflichtfelder; offene Fragen sind als solche notiert.

**Phase 3 — Blockout**
- [ ] Alle Außenformen (Stufe B) an ihren Datums; Anordnung nach Abschnitt 2.2, Proportionen nach
  Abschnitt 8.2, zusätzlich per Overlay gegen `B2_rear.jpg` und `B3_left.jpg` abgeglichen.
- Abnahme: Renderings aus den Foto-Blickwinkeln sind klar als diese Maschine erkennbar; jede Größe
  aus Tabelle 8.2 liegt im Modell innerhalb ± 10 %; Hüllmaß passt. Guter Zeitpunkt für Rückmeldung des Besitzers, aber nicht darauf warten.

**Phase 4 — Detail-Baugruppen (Stufe A)**, in dieser Reihenfolge:
- [ ] 4.1 Gruppe und Kolben · [ ] 4.2 Hebel · [ ] 4.3 Schauglas und Manometer ·
  [ ] 4.4 Dampfhahn und Lanze · [ ] 4.5 Sicherheitsventil und Kesseldeckel ·
  [ ] 4.6 Heizelement, Kessel/Basis-Verschraubung, Elektrik · [ ] 4.7 Basis und Tropfschale ·
  [ ] 4.8 Siebträger
- Abnahme je Baugruppe: alle Positionen als eigene Solids; Durchdringungs- und Ausbaupfad-Prüfung
  sauber; ein Schnitt-Rendering zeigt jede Dichtung in ihrem Sitz.
- Nach festgelegten Datums sind die Baugruppen unabhängig und können parallel bearbeitet werden.

**Phase 5 — Viewer V1**
- [ ] Punkte 5–9 aus Abschnitt 9, Materialien, HDRI, Touch-Layout.
- Abnahme: E2E-Tests grün; Budgets aus 6.4 eingehalten.

**Phase 6 — Anleitungen**
- [ ] Alle elf Anleitungen als Daten, Player fertig, Validator grün.
- Abnahme: jedes Verschleißteil kommt in mindestens einer Anleitung vor; jede Anleitung lässt sich
  vorwärts und rückwärts ohne Kollision abspielen.

**Phase 7 — Feinschliff und Auslieferung**
- [ ] Performance, Bedienbarkeit, README. GitHub-Pages-Deployment nur nach Freigabe des Besitzers.

**Phase 8 — Kalibrierung (laufend)**
- [ ] Messwerte des Besitzers in `dimensions.yaml` eintragen (`confidence: measured`), neu bauen,
  Prüfungen laufen lassen.

**Arbeitsweise:** Fehlende Angaben des Besitzers blockieren nie. Schätzen, Konfidenz setzen,
weiterbauen. Entwicklung und Commits auf dem vorgegebenen Feature-Branch.

## 13. Risiken und Stolperfallen

| Risiko | Gegenmaßnahme |
|---|---|
| Keine verbürgten Maße | Konfidenz je Maß, Badge im Viewer, Mess-Checkliste, Kalibrier-Phase |
| Widersprüchliche Dichtungsmaße (Kolbendichtung 33 vs. 36 mm innen) | im Viewer ausdrücklich „vor Bestellung messen“ anzeigen |
| v3.0 vs. v3.1 unklar | Versions-Parameter; Typenschild erfragen |
| Bauart Heizelement-Befestigung unklar (eingeschraubt oder Flansch mit Schrauben) | Foto der Unterseite erfragen; bis dahin als Parameter |
| Freiformteile (Gruppenkörper, Basis) scheitern an OCCT-Fillets | Zeitlimit, Rundungen ins Profil legen, notfalls vereinfachen |
| three.js bereinigt Knotennamen (entfernt `[ ] . : /`) und hängt bei Duplikaten `_1`, `_2` an | IDs nur `[a-z0-9_]`, eindeutig, Instanzen mit `__n` |
| `gltf-transform` (join/prune/flatten) kann benannte Knoten entfernen | Abgleich 11.1 Nr. 1 läuft gegen das **optimierte** GLB |
| GLB in Metern/Y-up | Viewer leitet Skalierung aus der Bounding Box ab, Kamera-Near-Plane klein |
| drei-`Environment`-Presets laden von einem CDN | HDRI lokal unter `web/public/env/` |
| Chrom zeigt Facetten | feine Tessellierung großer Flächen, Kanten gerundet |
| Repo ist öffentlich | keine fremden Zeichnungen/Fotos committen, nur verlinken. Die Besitzer-Fotos liegen mit dessen Zustimmung und ohne Metadaten im Repo; neue Fotos vor dem Commit ebenfalls von Metadaten befreien |
| Netzspannung und Druckkessel | Warnhinweise in den betroffenen Anleitungen |

## 14. Was der Besitzer beisteuern kann

Nichts davon ist Voraussetzung für den Baustart, alles verbessert die Genauigkeit.

1. **Kessel-Außendurchmesser** mit dem Messschieber. Dieses eine Maß kalibriert alle
   Foto-Proportionen aus Abschnitt 8.2 auf einmal.
2. **Baujahr/Version:** Das Typenschild nennt kein Baujahr. Hinweise geben ein Aufkleber oder
   Datumsstempel im Inneren der Basis bzw. am Heizelement, sonst der Kolben beim ersten Zerlegen
   (Messing = v3.1, Kunststoff = v3.0).
3. **Noch fehlende Fotos:** Unterseite mit abgenommener Bodenplatte (klärt die
   Heizelement-Befestigung und die Elektrik), gerade von vorn, gerade von rechts, von oben,
   Nahaufnahmen von Sicherheitsventil, Hebelgabel, Dampfhahn und Siebträger von unten. Seiten- und
   Rückansicht, Schrägansichten und Typenschild sind vorhanden (Abschnitt 2.1).
4. **Weitere Messschieber-Maße**, in dieser Priorität: Basis Länge × Breite × Höhe · Abstand
   Kesselachse zu Gruppenachse · Außendurchmesser Gruppenkopf · Kesselhöhe · Hebellänge ·
   Schauglas-Länge und -Durchmesser · Siebträger-Durchmesser.
5. **Beim ersten Zerlegen:** jede ausgebaute Dichtung messen (innen, außen, Dicke) und die
   Kolbenmaße (Durchmesser, Nutbreite, Nuttiefe). Das sind die wertvollsten Maße überhaupt.

Die genaue Liste mit Skizze, wo gemessen wird, entsteht in Phase 2 als `reference/measurements.md`.

## 15. Quellen

- Q1 Versionshistorie Professional: https://www.francescoceccarelli.eu/lapavoni_pr_eng.htm
- Q2 Ersatzteilliste mit Positionsnummern: https://www.francescoceccarelli.eu/lapavoni_apezzi_eng.htm
- Q3 Technische Daten (Händlerangaben): https://alternativebrewing.com.au/product/la-pavoni-professional-pl ·
  https://www.cremashop.se/en/products/la-pavoni/professional-plh · https://lapavoni.com/en/products/domestic-machines/professional-lusso
- Q4 Millennium-Teile: https://www.espressoparts.com/collections/la-pavoni-home-espresso-machine-parts-la-pavoni-millennium-parts
- Q5 Dichtungssatz Millennium mit Artikelnummern: https://coffeesection.com/products/la-pavoni-gasket-silicon-repair-kit-for-europiccola-professional-millenium
- Q6 Weitere Dichtungssätze/Einzelteile: https://coffeesection.com/products/la-pavoni-kit-group-replacement-gasket-set-europiccola-professional-millennium ·
  https://coffeesection.com/products/la-pavoni-parts-blue-silicone-gasket-kit-for-europiccola-professional-piston
- Q7 Wartung Gruppe: https://www.francescoceccarelli.eu/La_Pavoni/Faidate/gruppo_eng.htm
- Q8 Heizelement-Dichtung: https://www.francescoceccarelli.eu/La_Pavoni/Faidate/g_resistenza_eng.htm
- Q9 Schauglas: https://www.francescoceccarelli.eu/La_Pavoni/Faidate/g_livello_eng.htm
- Q10 Dampfhahn: https://www.francescoceccarelli.eu/La_Pavoni/Faidate/g_rubinetto_eng.htm
- Q11 Befestigung Kessel/Basis: https://www.francescoceccarelli.eu/La_Pavoni/Faidate/fissaggio_base_eng.htm
- Wartungs-Übersicht: https://www.francescoceccarelli.eu/lapavoni_faidate_eng.htm
- build123d Import/Export: https://build123d.readthedocs.io/en/latest/import_export.html

## 16. Umsetzungsnotizen und Abweichungen

Hier steht, was bei der Umsetzung anders gelöst wurde als oben beschrieben, und warum.

**Phase 0/1 (2026-11-11)**

- **Kein HDRI-File.** Statt eines Poly-Haven-HDRI unter `web/public/env/` erzeugt der Viewer ein
  Studio-Environment aus drei-`Lightformer`n (`web/src/scene/Viewer.tsx`). Grund: Der Besitzer will keine
  fremden Bilder im öffentlichen Repo; CC0 hin oder her, ein HDRI ist ein fremdes Foto. Lokal und ohne CDN ist
  es trotzdem, Chrom spiegelt sauber.
- **GLB-Export ohne globale Neuvernetzung.** `build123d.export_gltf` vernetzt jeden Knoten mit *einer* globalen
  Toleranz neu. `cad/pavoni/export.py` vernetzt jedes Teil vorher selbst (große Chromflächen fein, Kleinteile
  grob, PLAN 6.4) und schaltet die Neuvernetzung beim Export ab. Stolperfalle: `bounding_box()` und `volume`
  löschen in build123d die Tessellierung, deshalb wird zuletzt vernetzt.
- **Optimierung mit der gltf-transform-API statt `gltf-transform join`.** `web/scripts/optimize-glb.mjs`
  führt die Flächen-Primitives **je benanntem Instanz-Knoten** zusammen (`joinPrimitives`), danach weld, dedup,
  prune, meshopt (Positionen 16 bit, Normalen 12 bit). Ein globales `join` kann über Knoten hinweg mischen und
  Namen verlieren (Risiko aus Abschnitt 13). Das Skript bricht ab, wenn ein Instanz-Knoten fehlt. Ergebnis:
  genau ein Draw Call pro Instanz.
- **Datenmodell ergänzt** (Schemas unter `data/schema/`):
  - `data/assemblies.yaml`: Baugruppenbaum mit Pfad-IDs (`group.piston`), eigener Explode-Achse und
    `detachable` (wird als Einheit abgenommen, z. B. die ganze Gruppe vom Kessel).
  - `requires_removed` darf Baugruppen-IDs enthalten: „Gruppe ist abgenommen“. Die Ausbaupfad-Prüfung
    rechnet dann nur noch innerhalb der abgenommenen Baugruppe („Werkbank“).
  - `status` je Teil: `planned | blockout | modeled | verified`. `verified` heißt: im Rendering gegen Fotos
    bzw. Quellen geprüft. Damit ist jederzeit sichtbar, was fertig, geprüft und offen ist.
  - `carrier`: Elastische Teile (Dichtungen, Sicherungsringe) werden über ihren Träger gedehnt; die
    Ausbaupfad-Prüfung ignoriert den Träger.
  - `data/overlaps.yaml` (Whitelist gewollter Überdeckungen), `data/views.yaml` (benannte Ansichten und
    Schnitte), `data/proportions.yaml` (Soll-Proportionen aus 8.2, als Test).
  - `dimensions.yaml` hat die Ebenen `machine` (Version) und `dims`; ein Maß ist `value`+`unit`,
    `ratio_of`+`ratio` oder `expr` (abgeleitet), jeweils mit `confidence` und `source`, optional `alt`
    für widersprüchliche Angaben.
- **Kollisionsprüfung:** python-fcl auf den Tessellierungen, bewegtes Teil um 0,05 mm geschrumpft
  (Berührung ist keine Kollision), Abtastung 0,5 mm. Durchdringungsvolumen über manifold3d; Überdeckungen
  dünner als 0,06 mm gelten als Tessellierungsartefakt. Ein pytest beweist, dass eine Dichtung beim seitlichen
  Herausschieben aus ihrer Nut als Kollision erkannt wird.
- **Hüllmaß und Abdeckung Verschleißteile** sind Warnungen, solange Teile `planned` sind oder
  Hauptbaugruppen fehlen, danach harte Fehler.
- Versionen: Vite 8, React 19, TypeScript 7, three 0.187, R3F 9, drei 10 (Vorgaben des aktuellen
  Vite-Templates). build123d 0.13.0 wie verifiziert.
