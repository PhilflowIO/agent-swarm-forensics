# Robustheit: Gold-Set für die Regex-Klassifikatoren

Stand: Vorlage vom 2026-09-09. Der Zahlenblock zwischen den `AUTO`-Markern wird von
`analyse/scripts/62_goldset_eval.py` geschrieben, sobald die beiden Rater-Dateien
(`paper_goldset_rater1.jsonl`, `paper_goldset_rater2.jsonl`) vorliegen. Solange er leer ist,
existieren noch keine echten Zahlen; der Selbsttest des Skripts schreibt hier nichts hinein.

## 1. Frage

Die Prozessbefunde des Papers beruhen auf Regex-Klassifikatoren (Sprechakt, starke
Rundenbeobachtung, Vorab-Empfang fremder Antworten, Uhr-Aussagen, Koordinationsthema,
Umgebungs-Register). Das Gold-Set prüft, wie gut diese Regeln gegen menschliche Lesart
bestehen: Präzision (wie viele Treffer sind echt), Recall (wie viele echte Fälle werden
gefunden) und ob zwei unabhängige Leser die Kategorien überhaupt gleich anwenden.

## 2. Material

* Stichprobe: `paper_goldset_sample.csv`, 400 Sätze, 16 Strata, Seed 20260909
  (`61_goldset_sample.py`). Ein Satz = eine Zeile eines nicht-leeren Deltas, gesplittet wie in
  `51_prozess.py`; Kontext = Nachbarsätze derselben Revision (`CODEBOOK_goldset.md:12-15`).
* Kodieranweisung: `CODEBOOK_goldset.md`, sechs Kategorien (§1-§6), Ausgabeschema §8, Scoring-Map §9.
* Rater: zwei unabhängige Kodierungen der blinden Datei; Konflikte werden von Hand in
  `paper_goldset_konflikte.csv` (Spalten `adjudicated_*`) entschieden.

## 3. Methode

1. **Laden** beider JSONL-Dateien; ungültige Zeilen, unbekannte oder doppelte IDs und Werte
   außerhalb des Schemas (§8, `CODEBOOK_goldset.md:324-336`) werden protokolliert; ungültige Felder
   zählen als fehlend.
2. **Übereinstimmung** je Ziel: roher Anteil, Cohens κ (zwei Rater), Krippendorffs α (nominal,
   Koinzidenzmatrix, fehlende Werte erlaubt). Beide Maße sind im Skript selbst implementiert.
3. **Konflikte**: jeder Satz mit mindestens einem abweichenden Rohfeld → `paper_goldset_konflikte.csv`
   mit beiden Werten, `unclear`/`note` beider Rater und leeren `adjudicated_*`-Spalten. Bereits
   eingetragene Entscheidungen bleiben beim Neulauf erhalten.
4. **Gold**: übereinstimmender Wert, sonst adjudizierter Wert, sonst NA → `paper_goldset_gold.csv`
   (Spalte `gold_source` ∈ agree / adjudicated / open).
5. **Regex-Güte** je Klassifikator: Präzision, Recall, F1 gegen Gold, Wilson-95-%-Intervalle,
   (a) auf der geschichteten Stichprobe, (b) auf die Population zurückgewichtet.
6. **Formatvergleich** (§7): erhalten gefüllte `STATE5-XX`-Token und `R# CONFIRMED`-Sätze dasselbe
   arrival/speech_act-Profil (Fisher-Exakt-Test auf den arrival-Anteil)? Wenn ja, dürfen beide
   Formen als Ankunftsbeobachtung gepoolt werden.

### Gewichte

Gewicht eines Satzes = Populationsgröße seines Stratums / gezogene Anzahl. Die Populationsgrößen
stammen aus einem Wiederholungslauf von `61_goldset_sample.py` am 2026-09-09 (identische Ausgabe
zur Artefaktdatei, byteweise geprüft); verwendet wird die tatsächliche Ziehungsmenge nach Abzug
der schon von früheren Strata gezogenen Sätze (`61_goldset_sample.py:257`, Variable `pool`), nicht
die rohe Maskengröße. Konfidenzintervalle der gewichteten Anteile nutzen die effektive
Stichprobengröße nach Kish, n_eff = (Σw)² / Σw². Liegt `artefakte/_paper_goldset_sample.log` vor
(mitgeschnittene Ausgabe von 61), überschreibt es die Tabelle im Skript.

Die Rückgewichtung bezieht sich auf das **beprobte Universum** (Vereinigung aller Strata-Masken:
19 502 von 309 235 Korpussätzen), also auf Sätze, die entweder einen Regex-Treffer, einen Rundenmarker
oder eine Zeitangabe tragen. Über Sätze ohne all das sagt das Gold-Set nichts; für die
Klassifikatoren, deren Population `regex_has_round` ist (§9), ist das per Definition unerheblich, für
die "alle Sätze"-Klassifikatoren (Uhr, Koordination, Register) ist es ein Recall-Blindfleck.

## 4. Mapping Rater-Felder → Regex-Labels (`CODEBOOK_goldset.md:342-352`)

| Ziel (Skript) | Rater-Feld / Ableitung | Regex-Spalte(n) | Population |
|---|---|---|---|
| `arrival` | `arrival_round != null` | `regex_strong_obs` (stark); `regex_speech_act == observation` (schwach) | `regex_has_round` |
| `speech_act` | `speech_act` (4 Klassen + none), one-vs-rest | `regex_speech_act`; `unclassified` = keine der vier | `regex_has_round` |
| `future_answer` | `future_answer_receipt` | `regex_future_answer` (Paper-Zahl); `regex_future_answer_candidate` (nur Vokabular) | alle |
| `clock` | `clock_statement` | `regex_clock_route`: A = pair, B = bare_internal, C = past_event; bei Mehrfachroute Priorität A > B > C (`CODEBOOK_goldset.md:175`) | alle |
| `coord_topic` | `coordination_topic` | `regex_coord_topic_sentence` (Satz), `regex_coord_topic_delta` (Paper-Regel auf Delta-Ebene) | alle |
| `env` | `register ∈ {environment, both}` | `regex_env_sentence`, `regex_env_delta`, `regex_primary_delta == ENV_META` (Paper-Priorität ENV > TASK) | alle |
| `task` | `register ∈ {task, both}` | `regex_task_sentence` | alle |
| Format | Strata `format_state_filled`, `format_r_confirmed`, `format_state_placeholder` | `regex_format_state_filled`, `regex_format_rconfirmed` | Format-Strata |

Übereinstimmung wird zusätzlich auf `arrival_round` (exakte Rundenzahl) und `register` (4 Klassen)
berechnet, weil die Ableitungen sonst Konflikte verstecken.

## 5. Ergebnisse

<!-- AUTO:BEGIN -->
_Automatisch von 62_goldset_eval.py am 2026-09-09 eingesetzt; Modus: real._

**Stichprobe:** n = 400; vollständig kodiert von Rater 1: 400, Rater 2: 400 (Ladeprobleme R1: bad_json=0, unknown=0, dup=0, fehlend=0; R2: bad_json=0, unknown=0, dup=0, fehlend=0).

**Konflikte:** 63 Sätze mit mindestens einem abweichenden Feld (von 400 beidseitig kodierten); 63 vollständig adjudiziert, 0 offen (Gold = NA); 0 Sätze noch nicht von beiden kodiert.

**Übereinstimmung:**

| Ziel | n | roh | κ | α | Abweichungen |
|---|---|---|---|---|---|
| arrival | 400 | 0.95 | 0.90 | 0.90 | 19 |
| arrival_round | 400 | 0.95 | 0.92 | 0.92 | 19 |
| speech_act | 400 | 0.96 | 0.94 | 0.94 | 15 |
| future_answer | 400 | 0.99 | 0.90 | 0.90 | 5 |
| clock | 400 | 1.00 | 0.99 | 0.99 | 1 |
| coord_topic | 400 | 0.99 | 0.94 | 0.94 | 3 |
| register | 400 | 0.93 | 0.88 | 0.88 | 30 |
| env | 400 | 0.94 | 0.82 | 0.82 | 26 |
| task | 400 | 0.97 | 0.94 | 0.94 | 12 |

**Regex-Güte** (Gewichte: POP_TABLE in 62_goldset_eval.py (captured 61 re-run 2026-09-09)):

| Klassifikator | Klasse | n | P [95 %] | R [95 %] | F1 | R_pop [95 %] | F1_pop |
|---|---|---|---|---|---|---|---|
| arrival_obs_strong | arrival | 263 | 0.99 [0.92, 1.00] | 0.47 [0.39, 0.55] | 0.64 | 0.54 [0.37, 0.71] | 0.66 |
| arrival_obs_weak | arrival | 263 | 0.98 [0.93, 0.99] | 0.73 [0.65, 0.80] | 0.84 | 0.63 [0.46, 0.78] | 0.73 |
| speech_act | request | 263 | 0.74 [0.58, 0.86] | 0.74 [0.58, 0.86] | 0.74 | 0.82 [0.58, 0.94] | 0.82 |
| speech_act | prediction | 263 | 0.68 [0.53, 0.81] | 0.57 [0.42, 0.70] | 0.62 | 0.85 [0.65, 0.94] | 0.77 |
| speech_act | negation | 263 | 0.67 [0.48, 0.81] | 0.95 [0.75, 0.99] | 0.78 | 0.87 [0.28, 0.99] | 0.88 |
| speech_act | observation | 263 | 0.99 [0.95, 1.00] | 0.69 [0.61, 0.76] | 0.81 | 0.47 [0.31, 0.64] | 0.61 |
| future_answer_exact | true | 400 | 0.89 [0.57, 0.98] | 0.30 [0.16, 0.48] | 0.44 | 0.01 [0.00, 0.70] | 0.03 |
| future_answer_candidate | true | 400 | 0.81 [0.57, 0.93] | 0.48 [0.31, 0.66] | 0.60 | 0.02 [0.00, 0.71] | 0.05 |
| clock_route | pair | 400 | 0.81 [0.60, 0.92] | 0.94 [0.74, 0.99] | 0.87 | 0.98 [0.79, 1.00] | 0.61 |
| clock_route | bare_internal | 400 | 0.76 [0.55, 0.89] | 0.76 [0.55, 0.89] | 0.76 | 0.43 [0.19, 0.71] | 0.55 |
| clock_route | past_event | 400 | 0.97 [0.87, 1.00] | 0.75 [0.61, 0.84] | 0.84 | 0.60 [0.33, 0.82] | 0.75 |
| clock_route_any | any_internal | 400 | 0.91 [0.83, 0.96] | 0.82 [0.73, 0.89] | 0.87 | 0.64 [0.40, 0.82] | 0.72 |
| coord_topic_sentence | true | 400 | 0.98 [0.96, 0.99] | 0.66 [0.61, 0.70] | 0.79 | 0.81 [0.73, 0.88] | 0.89 |
| coord_topic_delta | true | 400 | 0.98 [0.96, 0.99] | 0.99 [0.97, 0.99] | 0.98 | 1.00 [0.96, 1.00] | 0.99 |
| env_sentence | environment | 400 | 0.60 [0.50, 0.70] | 0.56 [0.47, 0.65] | 0.58 | 0.79 [0.63, 0.89] | 0.78 |
| env_delta | environment | 400 | 0.32 [0.27, 0.38] | 0.85 [0.77, 0.91] | 0.47 | 0.95 [0.82, 0.99] | 0.57 |
| primary_delta_env | environment | 400 | 0.32 [0.27, 0.38] | 0.85 [0.77, 0.91] | 0.47 | 0.95 [0.82, 0.99] | 0.57 |
| task_sentence | task | 400 | 0.89 [0.67, 0.97] | 0.08 [0.05, 0.13] | 0.15 | 0.04 [0.01, 0.14] | 0.08 |

**Formatvergleich (§7):**

| Stratum | n | arrival | R5 | observation | request | negation |
|---|---|---|---|---|---|---|
| format_state_filled | 17 | 6/17 | 6 | 6/17 | 1 | 1 |
| format_r_confirmed | 25 | 25/25 | 2 | 25/25 | 0 | 0 |
| format_state_placeholder | 10 | 0/10 | 0 | 0/10 | 9 | 0 |

Fisher exact (Anteil arrival, STATE-filled vs R CONFIRMED): p <0.001.

**Stratum-Gewichte:**

| Stratum | gezogen | Population | Gewicht |
|---|---|---|---|
| coord_topic | 20 | 8545 | 427.25 |
| env_positive | 20 | 6525 | 326.25 |
| speech_prediction | 25 | 3089 | 123.56 |
| speech_request | 25 | 2087 | 83.48 |
| strong_obs | 30 | 1225 | 40.83 |
| clock_C_past_event | 20 | 606 | 30.30 |
| negative_random | 102 | 3059 | 29.99 |
| format_r_confirmed | 25 | 472 | 18.88 |
| clock_A_pair | 20 | 347 | 17.35 |
| format_state_placeholder | 10 | 171 | 17.10 |
| speech_observation_weak | 25 | 334 | 13.36 |
| speech_negation | 25 | 205 | 8.20 |
| clock_B_bare_now | 20 | 109 | 5.45 |
| format_state_filled | 17 | 17 | 1.00 |
| future_answer_ack | 9 | 9 | 1.00 |
| future_answer_candidate | 7 | 7 | 1.00 |
<!-- AUTO:END -->

## 6. Bekannte Mehrdeutigkeiten

* **Sprechakt-Priorität.** Codebook: request > observation > negation > prediction
  (`CODEBOOK_goldset.md:118-121`); Regex: request > negation > prediction > observation
  (`51_prozess.py:166-171`). Sätze mit Beobachtung *und* Negation/Vorhersage werden daher
  systematisch verschieden geordnet; das ist beabsichtigt und erscheint als Präzisionsverlust der
  Klassen negation/prediction, nicht als Rater-Uneinigkeit.
* **`arrival` ohne Rundenmarker.** Rater dürfen eine Ankunft auch ohne Regex-Rundenmarker kodieren
  (z. B. "Poland done"). Diese Fälle sind für die Regex nicht erreichbar; sie werden im Log gezählt,
  aber aus der Population `regex_has_round` (§9) herausgelassen.
* **Delta- vs. Satzebene.** Koordinationsthema und Register klassifiziert das Paper auf
  Delta-Ebene (`52_ml_verhalten.py:111-115`, `55_dramaturgie.py:186`); das Gold-Set kodiert Sätze.
  Die Delta-Spalten sind deshalb erwartbar präzisionsschwach (ein Delta mit einem ENV-Satz färbt alle
  Sätze). Beide Ebenen werden ausgewiesen; die Satz-Ebene ist die faire Prüfung der Regex, die
  Delta-Ebene die Prüfung der tatsächlich benutzten Zahl.
* **`future_answer_receipt`** setzt Kohortenzustand voraus (Runde vor der eigenen), den die Rater
  nur aus dem Kontext ableiten können (`CODEBOOK_goldset.md:156-158`). Erwartbar viele
  `unclear`-Flags; Recall der Paper-Regel ist gegen diese unsichere Gold-Basis zu lesen.
* **Uhr-Routen** stammen aus dem zeilenbasierten Artefakt `paper_uhr_taskzeiten.csv` und wurden per
  Teilstring auf Sätze gejoint (`61_goldset_sample.py:213-225`); ein Join-Fehler zählt als Regex-Fehler.
* **Populationen überlappen.** Ein Satz kann mehreren Masken angehören, wurde aber nur einem Stratum
  zugeteilt (Reihenfolge in `61_goldset_sample.py:237-253`). Recall je Klassifikator ist deshalb
  über *alle* Strata gewichtet zu lesen, nicht nur über das namensgebende.
* **Kleine Strata** (`future_answer_ack` n = 9, `future_answer_candidate` n = 7, `format_state_filled`
  n = 17) sind Vollerhebungen (Gewicht 1); ihre Intervalle sind breit.

## 7. Dateien

| Datei | Inhalt |
|---|---|
| `analyse/scripts/62_goldset_eval.py` | Auswertung |
| `analyse/artefakte/paper_goldset_agreement.csv` | κ, α, roher Anteil je Ziel |
| `analyse/artefakte/paper_goldset_konflikte.csv` | Konflikte, Adjudikationsspalten |
| `analyse/artefakte/paper_goldset_gold.csv` | Goldlabels je Satz |
| `analyse/artefakte/paper_robust_regex_guete.csv` | P/R/F1 roh und gewichtet |
| `paper/tables/app_goldset.tex` | Appendix-Fragment (nur bei echten Daten) |
| `analyse/artefakte/_paper_goldset_eval.log` | Lauf-Log |
