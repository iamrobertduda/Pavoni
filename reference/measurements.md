# Mess-Checkliste für den Besitzer

Jede Messung ersetzt eine Schätzung in `data/dimensions.yaml`. Eintragen mit `confidence: measured` und
`source: "Messung Besitzer, <Datum>"`, dann `make cad validate renders`. Kein Maß ist Voraussetzung: das Modell
läuft mit Schätzwerten, zeigt sie aber als solche an.

Werkzeug: Messschieber (0,1 mm), Lineal, Smartphone für Fotos. Maße in mm.

## A. Ohne Zerlegen (Reihenfolge = Nutzen)

| # | Was | Wie messen | Schlüssel in dimensions.yaml | Ersetzt |
|---|---|---|---|---|
| A1 | **Kessel-Außendurchmesser** | Messschieber quer über den Kessel zwischen Naht und Schauglas, an zwei um 90° versetzten Stellen, Mittelwert | `boiler_od` | Herleitung aus Fotos und Katalogteilen 104 mm (erste Schätzung 100). **Skaliert alle Foto-Proportionen auf einmal.** |
| A2 | Basis Länge × Breite × Höhe | Länge: hinten (Rundung) bis Vorderkante; Breite an der breitesten Stelle; Höhe Tisch bis Oberkante neben der Tropfschale | `base_len`, `base_w`, `base_h` | Fotos (2,5 × 1,6 × 0,5 D) |
| A3 | Abstand Kesselachse zu Gruppenachse | Lineal waagerecht: Kesselmitte (halber Durchmesser von der Vorderkante) bis Mitte Gruppenzylinder | `group_offset` | Foto 1,09 D |
| A4 | Außen-Ø Gruppe oben und Glocke unten | Messschieber am oberen Zylinder (über dem Hals) und an der breitesten Stelle der Glocke | `group_upper_od`, `group_bell_od` | Katalog 60 vs. Foto 54; Glocke Foto 0,64 D |
| A5 | Höhen über dem Tisch | Gruppenunterkante, Oberkante Hebelturm, Oberkante Hutmutter, Achse Gruppenhals, Kesselfuß, Schulterkante, Oberkante Deckel | `group_bottom_z`, `group_arm_z`, `boiler_foot_z`, `boiler_cyl_h` (Fuß bis Schulter), `cap_h` | Fotos; Höhen sind dort am unsichersten |
| A6 | Hebel | Länge Drehpunkt (hinterer Bolzen) bis Griffende; Winkel in Ruhelage (Smartphone-Wasserwaage auf der Stange) | `lever_len`, `lever_rest_deg`, `lever_pivot_back` | Katalog 230 / Foto 24° |
| A7 | Schauglas | Länge der Abdeckung; Abstand der beiden Halter-Mitten; Abstand Schauglas-Achse zur Kesselwand | `sg_cover_h`, `sg_upper_z`, `sg_axis_r` | Katalog 162 / Foto |
| A8 | Siebträger | Außen-Ø des Kopfes (ohne Ohren), Gesamtlänge, Höhe Auslauf-Unterkante über Tisch bei eingesetztem Siebträger | `pf_head_od`, `pf_len`, `spout_bottom_z` | Foto / Katalog |
| A9 | Dampfhahn | Rohr-Ø, Abstand Knauf-Außenkante bis Lanzen-Rohrende, Höhe der Rohrachse über der Schulterkante | `steam_tube_d`, `steam_total_w`, `steam_z_above_shoulder` | Fotos |
| A10 | Schalter und Emblem | Rahmen B × H, Lage (Abstand Schaltermitte zur Hinterkante); Emblem-Ø | `switch_w`, `switch_h`, `switch_pos_frac`, `emblem_d` | Fotos |

## B. Fotos, die noch fehlen (PLAN 14.3)

Ohne Metadaten senden (oder ich entferne sie vor dem Commit).

1. Unterseite **mit abgenommener Bodenplatte**: klärt Heizelement-Befestigung (3 Schrauben am Ring?), Lage von Pressostat, Thermostat, Klemmblock, Anzahl der Bodenschrauben und Gummifüße.
2. Gerade von vorn, gerade von rechts, von oben (je mit Abstand, damit die Perspektive gering ist).
3. Nahaufnahmen: Sicherheitsventil (Umfangswinkel auf dem Konus), Hebelgabel mit beiden Bolzen, Dampfhahn (Stutzen in den Konus), Siebträger von unten.

## C. Beim ersten Zerlegen (wertvollste Maße)

Jede ausgebaute Dichtung **innen, außen und Dicke** messen, bevor bestellt wird. Gerade bei den Kolbendichtungen
gibt es zwei Katalogangaben (Innen-Ø 36 oder 33 mm).

| # | Teil | Maße | Schlüssel |
|---|---|---|---|
| C1 | Kolbendichtungen (Pos. 80, 2×) | OD, ID, Höhe; Einbaurichtung fotografieren | `piston_seal_od`, `piston_seal_id`, `piston_seal_h` |
| C2 | Kolben (Pos. 79) | Ø, Höhe, Nutbreite, Nuttiefe (Nutgrund-Ø), Abstand untere Nut zur Unterkante, Material (Messing → v3.1) | `piston_d`, `piston_h`, `piston_lower_groove_z`, `machine.version` |
| C3 | Siebträger-Dichtung (Pos. 82) | OD, ID, Höhe, Profil (gerundete Seite?) | `group_gasket_*` |
| C4 | Duschsieb (Pos. 81) | Ø oben, Ø des abgesetzten Teils, Gesamthöhe | `screen_d`, `screen_body_d`, `screen_h` |
| C5 | Kolbenstange (Pos. 78) | Ø, Länge, Höhe der Querbohrung über dem unteren Ende | `rod_d`, `rod_len` |
| C6 | Stangendichtung, Scheibe, Sicherungsring (73-75) | OD, ID, Dicke | `rod_seal_*`, `rod_washer_*` |
| C7 | Hülse (Pos. 76, nur wenn ausgebaut) | Länge, Außen-Ø oben/unten, Lage von O-Ring-Nut und Gewinde | `sleeve_*` |
| C8 | Dichtung Gruppe/Kessel (Pos. 85) | ID, Schnurstärke | `group_oring_*` |
| C9 | Schauglas-Dichtungen (60), Glas (62) | OD, ID, Höhe; Glaslänge | `glass_*` |
| C10 | Heizelement, O-Ring (8), Ring (7), Dichtungen Kessel/Basis (4, 6) | Flansch-Ø, Lochkreis, O-Ring ID/Schnur, Ring OD/Höhe, Dichtungen OD/ID/Dicke | `element_*`, `base_ring_*`, `base_gasket_*` |
| C11 | Dampfhahn-Packung (50), Scheiben (49) | OD, ID, Dicke; Anzahl Scheiben | `steam_packing_*`, `steam_washer_t` |

## D. Version klären

Typenschild nennt kein Baujahr. Hinweise: Aufkleber oder Datumsstempel im Inneren der Basis bzw. am Heizelement;
beim Zerlegen der Kolben (Messing = v3.1 ab 2007, Kunststoff = v3.0). Eintrag: `machine.version` und
`machine.version_confidence: measured`.
