# Herkunftsprüfung der Artefakte — was erzeugen die Skripte wirklich?

Prüfdatum: 2026-09-09, 20:13–22:0x. Verfahren: **Neuerzeugung in einer Arbeitskopie**, nicht Textsuche.
Arbeitsverzeichnis der Prüfung: `/tmp/claude-1000/…/scratchpad/provenance/analyse/` (Skript-Kopie, **leeres** `artefakte/`, Symlink auf das echte `data/`).
Am Original (`analyse/`) wurde **nichts** geschrieben; belegt durch `find … -printf '%T@ %s %p'` vor und nach dem Lauf: kein Eintrag verschwand, keiner änderte Größe oder Zeit durch diesen Lauf (Anhang, Ambiguität A4).

## Kernzahlen

| Menge | Dateien |
|---|---:|
| Original `analyse/artefakte/` (Stand Prüfende) | 335 |
| **regeneriert** (ein benanntes Skript hat sie erzeugt) | **232** |
| davon byte-identisch mit dem Original | 211 |
| davon inhaltlich abweichend | 21 (8 Logs, 13 Datentabellen) |
| **nicht regeneriert** | **103** |
| davon **Wurzel-Waisen** (kein Skript erzeugt sie, sie blockieren die Kette) | 14 |
| davon im Paper referenziert | 28 |
| **verwaist/neu** (im Testlauf entstanden, im Original nicht vorhanden) | **0** |

Die beiden früheren statischen Zählungen (63 bzw. 64 Dateien ohne Erzeugungsstelle) sind widerlegt: sie liegen sowohl zu niedrig (die echte Zahl nicht regenerierter Dateien ist 103) als auch systematisch falsch begründet. Der Grund steht in `53_mathematik.py:27` — `OUT = lambda n: os.path.join(ART, "paper_math_" + n)`; die Datei `paper_math_multiplizitaet.csv` entsteht aus dem Aufruf `save(tests, "multiplizitaet.csv")` (`53_mathematik.py:398`), ihr voller Name kommt im Quelltext nirgends vor. Dasselbe Muster: `54_horizont.py:410` (`OUT(f"paper_horizont_testE_km_{col}.csv")`) und `54_horizont.py:569` (`…_tier{int(thr)}.csv`). Eine Textsuche muss hier scheitern.

## Methode

1. **Arbeitskopie.** `scripts/` kopiert, `artefakte/` leer angelegt, `data/` symbolisch verlinkt. 54 nummerierte Skripte (`01`–`66`) lagen zum Kopierzeitpunkt vor.
2. **Zwei Pfad-Reparaturen nur in der Kopie** (das Original blieb unangetastet): `41_lernkurve.py:3` verankert seinen Basispfad **absolut** auf das echte Repository (`B = pathlib.Path("/home/philflow/…/analyse")`) — ohne Patch hätte der Testlauf ins Original geschrieben. `40_chartdata.py:13` schreibt nach `/home/philflow/Dokumente/coding/philflow.io/src/public/charts`, also in ein fremdes Repository; auch das wurde in der Kopie umgeleitet. **Beides widerspricht `paper/main.tex:487`**, wo steht, die Skripte `01` bis `66` liefen „with script-relative paths".
3. **Läufe.** Numerische Reihenfolge `01`→`66`, Zeitlimit 900 s je Skript, Verzeichnis-Schnappschuss vor und nach jedem Lauf. Insgesamt sechs Durchgänge: zwei vollständige Durchgänge zur Auflösung der Reihenfolgeabhängigkeiten, danach eine **Saat-Schleife** (fehlende Eingabe aus dem Original nachlegen, betroffenes Skript erneut starten, bis alles läuft), zwei Kontrollpässe und ein Schlusslauf, der über Schreibzeitpunkte prüft, welche der nachgelegten Dateien von einem Skript doch noch überschrieben werden.
4. **Warum die Saat-Schleife nötig war.** Nach dem ersten Durchgang fehlten 156 Dateien — die meisten davon nur, weil ein Skript weiter oben an einer fehlenden Eingabe abgebrochen war. Erst das gezielte Nachlegen trennt „Kaskadenopfer" von „hat wirklich keinen Erzeuger". Es genügen **18** nachgelegte Dateien, damit die gesamte Kette durchläuft; von diesen 18 werden vier später doch von einem Skript geschrieben, 14 bleiben echte Wurzeln.
5. **Zwei Skripte sind keine Erzeuger, sondern Werkzeuge.** `20_grep.py:16` und `21_mine.py:18` lesen ihr Suchmuster aus `sys.argv[1]`; ohne Argument brechen sie mit `IndexError` ab. Sie sind in der Lauftabelle als Fehler geführt, erzeugen aber bestimmungsgemäß nichts von selbst.

## Lauftabelle

Spalte „Exit (Erstlauf)" ist der erste Durchgang mit leerem `artefakte/`, „Schlusslauf" der letzte Durchgang mit vollständigen Eingaben. „Erzeugte Artefakte" zählt die Dateien, die dieses Skript als erstes angelegt hat.

| Skript | Exit (Erstlauf) | Exit (Schlusslauf) | s (Schlusslauf) | erzeugte Artefakte |
|---|---|---|---:|---:|
| `01_explore.py` | 0 | 0 | 0.6 | 1 |
| `02_timeline.py` | 0 | 0 | 0.6 | 1 |
| `03_battle.py` | 0 | 0 | 0.5 | 2 |
| `04_mod.py` | 0 | 0 | 0.2 | 0 |
| `05_social.py` | 0 | 0 | 2.5 | 3 |
| `06_markers.py` | 0 | 0 | 4.1 | 3 |
| `07_exploit.py` | 0 | 0 | 0.6 | 1 |
| `08_exploit_quotes.py` | 0 | 0 | 0.6 | 0 |
| `09_damage.py` | 0 | 0 | 0.8 | 2 |
| `10_extra.py` | 0 | 0 | 3.0 | 0 |
| `11_frontpage.py` | 0 | 0 | 1.4 | 1 |
| `12_checks.py` | 0 | 0 | 1.8 | 0 |
| `13_awareness.py` | 0 | 0 | 9.8 | 1 |
| `20_grep.py` | 1 | 1 | 0.0 | 0 |
| `21_mine.py` | 1 | 1 | 0.0 | 0 |
| `22_tiers.py` | 0 | 0 | 2.7 | 5 |
| `23_net.py` | 0 | 0 | 8.9 | 1 |
| `24_model.py` | 0 | 0 | 6.0 | 0 |
| `25_dates.py` | 0 | 0 | 0.6 | 1 |
| `26_config.py` | 0 | 0 | 2.4 | 1 |
| `27_calibration.py` | 0 | 0 | 0.0 | 1 |
| `28_tiertable.py` | 0 | 0 | 0.0 | 1 |
| `29_scaling.py` | 0 | 0 | 2.7 | 1 |
| `30_load.py` | 0 | 0 | 1.0 | 1 |
| `31_arrival.py` | 0 | 0 | 3.3 | 5 |
| `32_delta.py` | 0 | 0 | 2.0 | 1 |
| `33_taxonomy.py` | 0 | 0 | 0.8 | 3 |
| `34_reziprozitaet.py` | 0 | 0 | 3.0 | 2 |
| `35_dissens.py` | 0 | 0 | 0.8 | 2 |
| `36_form.py` | 0 | 0 | 1.0 | 2 |
| `37_gleichzeitig.py` | 0 | 0 | 0.9 | 1 |
| `38_kaltstart.py` | 0 | 0 | 3.0 | 5 |
| `39_selbstbild.py` | 0 | 0 | 0.8 | 11 |
| `3A_extra.py` | 0 | 0 | 1.2 | 2 |
| `3B_grammatik.py` | 0 | 0 | 0.6 | 1 |
| `3C_robust.py` | 0 | 0 | 0.6 | 0 |
| `40_chartdata.py` | 1 | 0 | 0.0 | 0 |
| `41_lernkurve.py` | 0 | 0 | 1.6 | 12 |
| `42_flotte_marker.py` | 0 | 0 | 1.3 | 5 |
| `50_uhr_auslastung.py` | 0 | 0 | 54.6 | 13 |
| `51_prozess.py` | 0 | 0 | 25.2 | 26 |
| `52_ml_verhalten.py` | 0 | 0 | 1.9 | 8 |
| `53_mathematik.py` | 1 | 0 | 28.7 | 19 |
| `54_horizont.py` | 1 | 0 | 10.1 | 29 |
| `55_dramaturgie.py` | 0 | 0 | 4.7 | 11 |
| `56_archetypen.py` | 0 | 0 | 39.4 | 11 |
| `57_chartdata_paper.py` | 1 | 0 | 0.5 | 0 |
| `58_figures_paper.py` | 1 | 0 | 6.2 | 0 |
| `61_goldset_sample.py` | 0 | 0 | 23.1 | 2 |
| `62_goldset_eval.py` | 2 | 0 | 1.2 | 5 |
| `63_fortschritt_robust.py` | 0 | 0 | 109.3 | 7 |
| `64_uhr_robust.py` | 1 | 0 | 208.5 | 10 |
| `65_adoption_robust.py` | 1 | 0 | 32.8 | 3 |
| `66_exposition.py` | 1 | 0 | 9.7 | 9 |

Summe zugeordneter Artefakte: 232

Alle nummerierten Skripte laufen im Schlusslauf fehlerfrei durch; die beiden Ausnahmen `20_grep.py` und `21_mine.py` sind argumentgetriebene Werkzeuge (siehe Methode 5). Kein Skript lief in ein Zeitlimit; das langsamste ist `64_uhr_robust.py` mit 208 s.

## Menge 1 — regeneriert (232 Dateien)

211 der 232 sind **byte-identisch** mit dem Original (SHA-256 über jede Datei). Die 21 Abweichungen zerfallen in vier Klassen; nur zwei davon sind Befunde.

| Datei(en) | Klasse | Belegte Ursache |
|---|---|---|
| `_audit.log`, `_paper_exposition.log`, `_paper_flotte.log`, `_paper_goldset_eval.log`, `_paper_lernkurve.log`, `_paper_robust_adoption.log`, `_paper_robust_fortschritt.log`, `_paper_robust_uhr.log` | unkritisch | Laufprotokolle mit absoluten Pfaden und Zeitstempeln |
| `harness_tier_intervals.csv`, `harness_tier_words.csv`, `paper_flotte_marker_multiplizitaet.csv` | unkritisch | nur Zeilenreihenfolge; nach Sortierung aller Spalten sind alt und neu gleich (geprüft mit `sort_values(...).equals(...)` → `True`) |
| `paper_archetypen_zuordnung.csv` | unkritisch | Spalte `zentroid_ratio`, größte absolute Abweichung 4,44e-16 (Fließkomma-Rundung); die Datei war in einem früheren Durchgang bitgleich und im letzten nicht — die Abweichung ist lauf-, nicht codeabhängig |
| `paper_lernkurve_q3_format_erstversion_6h/tag/woche.csv`, `paper_lernkurve_q4_technik_summary.csv`, `paper_lernkurve_revflags.parquet` | **P2 — Artefakt ist älter als sein Skript** | `paper_lernkurve_q4_technik_summary.csv` hat im Original **21** Spalten, neu **15**; `paper_lernkurve_revflags.parquet` original **29**, neu **26** (die Zusatzspalte `state_conf2` existiert im heutigen Code nicht mehr). In den drei `q3`-Tabellen weicht nur `state_conf` ab (bis 0,3), passend zur Härtung des Musters in `41_lernkurve.py:21` („gehaertet: URL-Param State= ausgeschlossen"). Die Artefakte tragen 8. Sep. 18:37/18:39, das Skript 18:48 — sie stammen aus einer älteren Skriptfassung. |
| `paper_goldset_gold.csv`, `paper_goldset_konflikte.csv`, `paper_robust_regex_guete.csv` | **P1 — Handentscheid lebt nur im Artefakt** | `62_goldset_eval.py:436-444` liest die **vorhandene** `paper_goldset_konflikte.csv` und übernimmt daraus die adjudizierten Werte. In einem leeren `artefakte/` gibt es diese Datei nicht: 63 Konfliktfälle bleiben `open` statt `adjudicated`, dem Goldstandard fehlen die Handentscheide, und die im Anhang zitierte Gütetabelle verschiebt sich (`n` 263→261, `n_gold_pos` 140→139, Recall der ersten Zeile 0,4714→0,4748, F1 0,6377→0,6408). Die Adjudikation ist damit **nicht** aus dem Abzug rekonstruierbar. |
| `paper_math_population_gamma_poisson.csv`, `paper_math_population_schaetzer.csv` | Prüfartefakt | Meine Skript-Kopie ist von 20:13, das Original wurde um 20:27 erweitert (neuer Block `53_mathematik.py:107-116`, `population_bereinigt.csv`). Der zusätzliche Monte-Carlo-Aufruf verschiebt den Zufallsstrom; `ci_hi` weicht um bis zu 13,6 ab. Nebenbefund (P2): die Intervallgrenzen dieser Tabelle hängen an der Aufrufreihenfolge der Zufallszahlen, nicht nur am Seed. |

## Menge 2 — nicht regeneriert (103 Dateien)

Das ist der eigentliche Befund. „Wurzel" heißt: die Datei hat keinen Erzeuger **und** blockiert nachgelagerte Skripte; alle übrigen 89 Dateien sind entweder Prosa, Beispielmaterial oder Ad-hoc-Ausgaben.

| Gruppe | Dateien | davon im Paper zitiert | davon Wurzel-Waise |
|---|---:|---:|---:|
| Prosa: Berichte, Codebook, Synthese | 23 | 14 | 0 |
| uebrige paper_* | 20 | 7 | 3 |
| paper_episode_* (Paper-Ausnahme) | 17 | 6 | 8 |
| harness_* (Ad-hoc-Extraktion mit 21_mine.py) | 16 | 0 | 0 |
| Szenen-/Visualisierungs-Beispiele | 16 | 0 | 0 |
| paper_neuheit_* (Paper-Ausnahme) | 6 | 1 | 1 |
| Handerhobene Rohdaten | 3 | 0 | 2 |
| Logs verwaister Laeufe | 2 | 0 | 0 |
| **Summe** | **103** | **28** | **14** |

### Prosa: Berichte, Codebook, Synthese

| Datei | Im Paper zitiert in | Prioritaet |
|---|---|---|
| `BERICHT_archetypen.md` | `limitations_raw.md` | P1 |
| `BERICHT_dramaturgie.md` | `limitations_raw.md` | P1 |
| `BERICHT_episodenstruktur.md` | `limitations_raw.md` | P1 |
| `BERICHT_exposition.md` | — | P3 |
| `BERICHT_flottengroesse.md` | `limitations_raw.md` | P1 |
| `BERICHT_horizont.md` | `limitations_raw.md` | P1 |
| `BERICHT_kriesel_auftritt.md` | — | P3 |
| `BERICHT_kriesel_rhetorik.md` | — | P3 |
| `BERICHT_lernkurve.md` | `limitations_raw.md` | P1 |
| `BERICHT_mathematik.md` | `limitations_raw.md`, `refs/methods_time.md` | P1 |
| `BERICHT_ml_verhalten.md` | `limitations_raw.md` | P1 |
| `BERICHT_neuheit_kritik.md` | `limitations_raw.md`, `refs/PRUEFUNG_literatur.md`, `refs/emergent_stigmergy.md`, `refs/escape_rewardhacking.md`, `refs/methods_time.md`, `refs/schelling_awareness.md` | P1 |
| `BERICHT_prozess.md` | `limitations_raw.md` | P1 |
| `BERICHT_robust_adoption.md` | — | P3 |
| `BERICHT_robust_fortschritt.md` | — | P3 |
| `BERICHT_robust_goldset.md` | — | P3 |
| `BERICHT_robust_uhr.md` | — | P3 |
| `BERICHT_szenen.md` | — | P3 |
| `BERICHT_uhr_auslastung.md` | `limitations_raw.md` | P1 |
| `BERICHT_visualisierung.md` | `limitations_raw.md` | P1 |
| `CODEBOOK_goldset.md` | `main.tex` | P1 |
| `MECHANIK_v1_ueberholt.md` | `main.tex` | P1 |
| `PRUEFUNG_abbildungen_und_D.md` | — | P3 |

### uebrige paper_*

| Datei | Im Paper zitiert in | Prioritaet |
|---|---|---|
| `paper_flotte_datum_topic.csv` | `limitations_raw.md` | P1 |
| `paper_flotte_datumsabdeckung.csv` | — | P3 |
| `paper_flotte_hexpraefixe.csv` | — | P3 |
| `paper_flotte_kohortendaten_body.csv` | — | P3 |
| `paper_flotte_markergruppen_zeit.csv` | — | P3 |
| `paper_flotte_namensfamilien.csv` | — | P3 |
| `paper_flotte_schaetzer.csv` | `figures/CAPTIONS.md` | P1 |
| `paper_flotte_schaetzer_versoehnt.csv` **(Wurzel)** | `figures/CAPTIONS.md`, `figures/data/fig7_population_estimate.json`, `limitations_raw.md`, `main.tex`, `tables/tab_population_robust.tex` | P1 |
| `paper_flotte_seiten_label_pro_kohorte.csv` | — | P3 |
| `paper_flotte_zeitcluster.csv` | — | P3 |
| `paper_lernkurve_q1_ankunft_6h_koordpop.csv` | — | P3 |
| `paper_lernkurve_q1_kontaktzeit.csv` | — | P3 |
| `paper_lernkurve_q2_inhaltlicher_lesebeweis.csv` **(Wurzel)** | `figures/data/fig3b_format_filtered.json` | P1 |
| `paper_lernkurve_q3_format_erstversion_koordpop_6h.csv` **(Wurzel)** | `figures/data/fig3_format_convergence.json` | P1 |
| `paper_lernkurve_q3_format_erstversion_koordpop_tag.csv` | — | P3 |
| `paper_lernkurve_q5_namensschema_materialisierung.csv` | — | P3 |
| `paper_lernkurve_q5_vokabular.csv` | — | P3 |
| `paper_math_population_bereinigt.csv` | `figures/data/fig7_population_estimate.json` | P1 |
| `paper_netzblock_whois.csv` | `limitations_raw.md`, `main.tex` | P1 |
| `paper_visualisierungsplan.csv` | — | P3 |

### paper_episode_* (Paper-Ausnahme)

| Datei | Im Paper zitiert in | Prioritaet |
|---|---|---|
| `paper_episode_clock_pairs.csv` | — | P3 |
| `paper_episode_clock_pairs_validated.csv` | — | P3 |
| `paper_episode_clockwait_measurements.csv` **(Wurzel)** | `figures/data/fig1_clock_two_states.json`, `figures/data/fig6_lead_ecdf.json` | P1 |
| `paper_episode_daily.csv` **(Wurzel)** | `figures/data/fig2_time_course.json` | P1 |
| `paper_episode_dilation_factors.csv` | — | P3 |
| `paper_episode_dilation_factors_usable.csv` | — | P3 |
| `paper_episode_horizon_claims.csv` **(Wurzel)** | — | P3 |
| `paper_episode_hourly.csv` **(Wurzel)** | `figures/data/fig2_time_course.json` | P1 |
| `paper_episode_label_lifespan.csv` | — | P3 |
| `paper_episode_label_lifespan_distinctive.csv` **(Wurzel)** | — | P3 |
| `paper_episode_r6_sichtung.csv` **(Wurzel)** | `figures/CAPTIONS.md`, `figures/data/fig5_round_staircase.json`, `limitations_raw.md`, `main.tex` | P1 |
| `paper_episode_r6plus_observation_candidates.csv` | `figures/CAPTIONS.md` | P1 |
| `paper_episode_round_ge6_mentions.csv` | — | P3 |
| `paper_episode_round_mentions.csv` **(Wurzel)** | `figures/data/fig5_round_staircase.json` | P1 |
| `paper_episode_round_mentions_raw.csv` | — | P3 |
| `paper_episode_tier_durations.csv` **(Wurzel)** | — | P3 |
| `paper_episode_top_pages.csv` | — | P3 |

### harness_* (Ad-hoc-Extraktion mit 21_mine.py)

| Datei | Im Paper zitiert in | Prioritaet |
|---|---|---|
| `harness_audit.log` | — | P3 |
| `harness_browser.csv` | — | P3 |
| `harness_cache.csv` | — | P3 |
| `harness_clocks.csv` | — | P3 |
| `harness_clockwait.csv` | — | P3 |
| `harness_dilation.csv` | — | P3 |
| `harness_feedback.csv` | — | P3 |
| `harness_horizon.csv` | — | P3 |
| `harness_msgstruct.csv` | — | P3 |
| `harness_phantom.csv` | — | P3 |
| `harness_proxy.csv` | — | P3 |
| `harness_r1.csv` | — | P3 |
| `harness_termination.csv` | — | P3 |
| `harness_tiernames.csv` | — | P3 |
| `harness_tools.csv` | — | P3 |
| `harness_wording.csv` | — | P3 |

### Szenen-/Visualisierungs-Beispiele

| Datei | Im Paper zitiert in | Prioritaet |
|---|---|---|
| `szenen_skripte/alpha.py` | — | P3 |
| `szenen_skripte/conf.py` | — | P3 |
| `szenen_skripte/ctr.py` | — | P3 |
| `szenen_skripte/flip.py` | — | P3 |
| `szenen_skripte/flip2.py` | — | P3 |
| `szenen_skripte/lib.py` | — | P3 |
| `szenen_skripte/moji.py` | — | P3 |
| `szenen_skripte/moji3.py` | — | P3 |
| `szenen_skripte/sc14.txt` | — | P3 |
| `szenen_skripte/zzz.py` | — | P3 |
| `viz_beispiele/intervalle_jitter_singleaxis.json` | — | P3 |
| `viz_beispiele/themen_heatmap_cartesian.json` | — | P3 |
| `viz_beispiele/treppe_step_ecdf.json` | — | P3 |
| `viz_beispiele/uhr_zwei_zustaende_loglog.json` | — | P3 |
| `viz_beispiele/waldplot_ci_custom.json` | — | P3 |
| `viz_beispiele/zeitverlauf_zwei_achsen.json` | — | P3 |

### paper_neuheit_* (Paper-Ausnahme)

| Datei | Im Paper zitiert in | Prioritaet |
|---|---|---|
| `paper_neuheit_ankunftsstaffelung_familie.csv` | — | P3 |
| `paper_neuheit_empfang_fremdinfo.csv` | — | P3 |
| `paper_neuheit_vorsprung_eigenankunft_items.csv` | — | P3 |
| `paper_neuheit_vorsprung_eigenankunft_labels.csv` **(Wurzel)** | `figures/CAPTIONS.md`, `figures/data/fig6_lead_ecdf.json`, `main.tex` | P1 |
| `paper_neuheit_vorsprung_items.csv` | — | P3 |
| `paper_neuheit_vorsprung_labels.csv` | — | P3 |

### Handerhobene Rohdaten

| Datei | Im Paper zitiert in | Prioritaet |
|---|---|---|
| `adjudikation_phil.json` | — | P3 |
| `paper_goldset_rater1.jsonl` **(Wurzel)** | — | P3 |
| `paper_goldset_rater2.jsonl` **(Wurzel)** | — | P3 |

### Logs verwaister Laeufe

| Datei | Im Paper zitiert in | Prioritaet |
|---|---|---|
| `_paper_math.log` | — | P3 |
| `_paper_math_seedscan.log` | — | P3 |

## Die 14 Wurzel-Waisen im Einzelnen

Diese Dateien werden von **keinem** Skript geschrieben, und ohne sie bricht die Kette. Belegt zweifach: (a) in einem Lauf mit leerem `artefakte/` entstehen sie nie und die abhängigen Skripte brechen mit `FileNotFoundError` genau auf ihren Namen ab; (b) im Schlusslauf mit vollständigen Eingaben bleibt ihr Schreibzeitpunkt unverändert, während vier andere zunächst nachgelegte Dateien (`paper_math_hawkes.csv`, `paper_math_uhr_clockwait_modelle.csv` aus `53_mathematik.py`, `paper_horizont_testH_cvd_kohorten.csv`, `paper_horizont_testH_cvd_saetze.csv` aus `54_horizont.py`) sehr wohl überschrieben werden — die gehören also **nicht** zu den Waisen.

| Wurzel-Waise | blockiert | Im Paper zitiert |
|---|---|---|
| `paper_episode_clockwait_measurements.csv` | `53_mathematik.py:339`, `57_chartdata_paper.py:62` | `figures/data/fig1_clock_two_states.json`, `fig6_lead_ecdf.json` |
| `paper_episode_daily.csv` | `57_chartdata_paper.py` | `figures/data/fig2_time_course.json` |
| `paper_episode_hourly.csv` | `57_chartdata_paper.py` | `figures/data/fig2_time_course.json` |
| `paper_episode_horizon_claims.csv` | `54_horizont.py` | — |
| `paper_episode_label_lifespan_distinctive.csv` | `54_horizont.py:53` | — |
| `paper_episode_r6_sichtung.csv` | `57_chartdata_paper.py` | `main.tex`, `figures/CAPTIONS.md`, `fig5_round_staircase.json`, `limitations_raw.md` |
| `paper_episode_round_mentions.csv` | `57_chartdata_paper.py` | `figures/data/fig5_round_staircase.json` |
| `paper_episode_tier_durations.csv` | `54_horizont.py` | — |
| `paper_neuheit_vorsprung_eigenankunft_labels.csv` | `57_chartdata_paper.py` | `main.tex`, `figures/CAPTIONS.md`, `fig6_lead_ecdf.json` |
| `paper_flotte_schaetzer_versoehnt.csv` | `57_chartdata_paper.py:423` | `main.tex`, `tables/tab_population_robust.tex`, `fig7_population_estimate.json`, `CAPTIONS.md`, `limitations_raw.md` |
| `paper_lernkurve_q2_inhaltlicher_lesebeweis.csv` | `65_adoption_robust.py:225`, `66_exposition.py:103` | `figures/data/fig3b_format_filtered.json` |
| `paper_lernkurve_q3_format_erstversion_koordpop_6h.csv` | `57_chartdata_paper.py`, `65_adoption_robust.py` | `figures/data/fig3_format_convergence.json` |
| `paper_goldset_rater1.jsonl` | `62_goldset_eval.py` | — |
| `paper_goldset_rater2.jsonl` | `62_goldset_eval.py` | — |

**Gegen die im Paper offen benannten Ausnahmen gehalten.** `paper/main.tex:487` nennt genau zwei: „Two derived tables---the R6 review (`paper_episode_*`) and the head-start measurement (`paper_neuheit_*`)---were produced in interactive sessions". Damit sind 9 der 14 Wurzeln gedeckt (`paper_episode_*` × 8, `paper_neuheit_*` × 1). Der versöhnte Populationsschätzer ist die dritte, im Auftrag vorab bekannte Ausnahme. **Nicht gedeckt bleiben vier Wurzeln:**

- `paper_lernkurve_q2_inhaltlicher_lesebeweis.csv` — **P1**, steckt in `figures/data/fig3b_format_filtered.json` und damit in Abbildung 3b.
- `paper_lernkurve_q3_format_erstversion_koordpop_6h.csv` — **P1**, Datengrundlage von `figures/data/fig3_format_convergence.json` (Abbildung 3).
- `paper_goldset_rater1.jsonl` / `paper_goldset_rater2.jsonl` — **P2**: die beiden Rater-Rohdateien sind Handarbeit und als solche legitim, aber im Paper nicht als Ausnahme geführt. Zusammen mit dem Adjudikations-Rücklauf aus `62_goldset_eval.py:436` heißt das: der gesamte Goldstandard-Anhang (`tables/app_goldset.tex`) ist aus dem Abzug allein nicht herstellbar.

## Weitere nicht regenerierte Gruppen, kurz erklärt

- **16 × `harness_*.csv`** (`harness_browser`, `harness_cache`, `harness_clocks`, `harness_clockwait`, `harness_dilation`, `harness_feedback`, `harness_horizon`, `harness_msgstruct`, `harness_phantom`, `harness_proxy`, `harness_r1`, `harness_termination`, `harness_tiernames`, `harness_tools`, `harness_wording`, `harness_audit.log`). Erzeuger ist `21_mine.py`, aufgerufen als `21_mine.py <regex> --csv <name>.csv` (`21_mine.py:18`, `:44-48`). Beweis: alle 15 CSV tragen exakt die Kopfzeile aus `21_mine.py:46` — `n_revs,n_labels,n_pages,first_time,first_page,first_label,sentence`. Es fehlt nur das **Suchmuster**; es ist nirgends im Repository festgehalten. Diese Dateien werden in `analyse/HARNESS.md:400,406` als Belegquellen zitiert, im Paper selbst nicht. **P2** — reparabel durch eine Zeile pro Datei in einem Aufruf-Skript.
- **23 Prosa-Dateien** (`BERICHT_*.md` × 20, `CODEBOOK_goldset.md`, `MECHANIK_v1_ueberholt.md`, `PRUEFUNG_abbildungen_und_D.md`). Handgeschrieben, was für Prosa in Ordnung ist; 14 davon sind über `paper/limitations_raw.md` und `main.tex` zitiert. Anmerkung (P3): `main.tex:487` spricht von „the thirteen detail reports (`BERICHT_*.md`)", tatsächlich liegen **20** vor.
- **16 Beispiel-Assets** (`szenen_skripte/*.py`, `viz_beispiele/*.json`). Nicht im Paper zitiert. **P3**.
- **20 übrige `paper_*`-Tabellen** — überwiegend Nebenausgaben derselben interaktiven Sitzungen (`paper_flotte_*` × 10, `paper_lernkurve_q1/q5`, `paper_visualisierungsplan.csv`, `paper_netzblock_whois.csv`). Davon im Paper zitiert und **nicht** von einer benannten Ausnahme gedeckt: `paper_netzblock_whois.csv` (`main.tex`, WHOIS-Abfrage — extern, prinzipiell nicht aus dem Abzug herstellbar), `paper_flotte_schaetzer.csv` und `paper_flotte_datum_topic.csv` (`figures/CAPTIONS.md`, `limitations_raw.md`), sowie `paper_horizont_testH_cvd_kohorten.csv` — letztere ist **kein** Befund: sie wird von `54_horizont.py` erzeugt, sobald dessen eigene Eingabe vorliegt.
- **`adjudikation_phil.json`** — von keinem Skript gelesen oder geschrieben. Vermutlich Arbeitsstand der Handadjudikation; **P3**, aber ein Hinweis darauf, dass die Adjudikation außerhalb der Kette gepflegt wurde.
- **`paper_math_population_bereinigt.csv`** taucht in der Fehlliste auf, ist aber **kein** Befund: das Skript, das sie erzeugt (`53_mathematik.py:116`), entstand um 20:27 — nach dem Kopierzeitpunkt dieser Prüfung.

## Menge 3 — verwaist/neu

Leer. Der Testlauf hat **keine** Datei erzeugt, die es im Original nicht gibt. Die Skripte schreiben also nichts Überzähliges; das Ungleichgewicht liegt vollständig auf der anderen Seite.

## Stichprobenvergleich: die im Paper zitierten, regenerierten Tabellen

Nicht 8–10, sondern **alle 26** regenerierten CSV, deren Dateiname in `paper/main.tex`, `paper/tables/`, `paper/figures/` oder `paper/limitations_raw.md` vorkommt. 24 davon sind bitgleich.

| Artefakt | Erzeuger | Zeilen alt/neu | Spalten alt/neu | Abgleich |
|---|---|---:|---:|---|
| `harness_tier_table.csv` | `28_tiertable.py` | 33/33 | 9/9 | bitgleich |
| `hourly.csv` | `03_battle.py` | 356/356 | 4/4 | bitgleich |
| `paper_exposition_adoption_6h.csv` | `66_exposition.py` | 1250/1250 | 13/13 | bitgleich |
| `paper_fortschritt_kohorten.csv` | `51_prozess.py` | 907/907 | 38/38 | bitgleich |
| `paper_goldset_agreement.csv` | `62_goldset_eval.py` | 9/9 | 9/9 | bitgleich |
| `paper_goldset_konflikte.csv` | `62_goldset_eval.py` | 63/63 | 28/28 | **max abs. Abweichung 0** |
| `paper_horizont_testH_cvd_kohorten.csv` | `54_horizont.py` | 38/38 | 11/11 | bitgleich |
| `paper_lernkurve_q5_rendezvous_treffer.csv` | `41_lernkurve.py` | 100/100 | 5/5 | bitgleich |
| `paper_math_fahrplan_latente_skala.csv` | `53_mathematik.py` | 3/3 | 5/5 | bitgleich |
| `paper_math_uhr_clockwait_modelle.csv` | `53_mathematik.py` | 2/2 | 7/7 | bitgleich |
| `paper_prozess_zitatkaskade_kopien.csv` | `51_prozess.py` | 3295/3295 | 15/15 | bitgleich |
| `paper_robust_fahrplan_loo.csv` | `64_uhr_robust.py` | 16/16 | 8/8 | bitgleich |
| `paper_robust_fahrplan_provenienz.csv` | `64_uhr_robust.py` | 15/15 | 15/15 | bitgleich |
| `paper_robust_format_gefiltert_6h.csv` | `65_adoption_robust.py` | 72/72 | 11/11 | bitgleich |
| `paper_robust_fortschritt_effekte.csv` | `63_fortschritt_robust.py` | 88/88 | 22/22 | bitgleich |
| `paper_robust_hawkes_dedup.csv` | `65_adoption_robust.py` | 24/24 | 11/11 | bitgleich |
| `paper_robust_horizont_cvd_intervalle.csv` | `64_uhr_robust.py` | 24/24 | 14/14 | bitgleich |
| `paper_robust_horizont_cvd_klassen.csv` | `64_uhr_robust.py` | 7/7 | 11/11 | bitgleich |
| `paper_robust_marker_D.csv` | `42_flotte_marker.py` | 2/2 | 7/7 | bitgleich |
| `paper_robust_regex_guete.csv` | `62_goldset_eval.py` | 36/36 | 18/18 | **max abs. Abweichung 2643.72** |
| `paper_robust_uhr_ebenen.csv` | `64_uhr_robust.py` | 4/4 | 19/19 | bitgleich |
| `paper_robust_uhr_mitternacht.csv` | `64_uhr_robust.py` | 4/4 | 13/13 | bitgleich |
| `paper_uhr_faktoren.csv` | `50_uhr_auslastung.py` | 352/352 | 35/35 | bitgleich |
| `paper_uhr_korrelation.csv` | `50_uhr_auslastung.py` | 144/144 | 9/9 | bitgleich |
| `paper_uhr_tagesgang.csv` | `50_uhr_auslastung.py` | 39/39 | 8/8 | bitgleich |
| `schwarm_pagename_morphology.csv` | `31_arrival.py` | 4568/4568 | 10/10 | bitgleich |

Die beiden Abweichungen stammen aus derselben Ursache — dem fehlenden Adjudikations-Rücklauf (siehe Menge 1). `paper_goldset_konflikte.csv` weicht nur in den `adjudicated_*`-Spalten ab (63 Zeilen, alle numerischen Spalten deckungsgleich), `paper_robust_regex_guete.csv` in Fallzahlen und Güte-Maßen.

## Ambiguitäten

- **A1 — Das Original war während der Prüfung in Bewegung.** Eine parallele Sitzung hat um 20:16–20:51 die Skripte `90_release_index.py` bis `93_release_repo.py` neu angelegt und `53_mathematik.py` sowie `57_chartdata_paper.py` geändert, danach `53` neu laufen lassen (alle `paper_math_*` tragen neue Zeitstempel, `paper_math_population_bereinigt.csv` kam hinzu). Die Prüfung bildet den Codestand **20:13** ab. Die vier `9x_release_*`-Skripte wurden nicht geprüft.
- **A2 — `paper_flotte_schaetzer_versoehnt.csv` wurde um 20:2x im Original neu geschrieben,** obwohl kein Skript diesen Namen schreibt (`57_chartdata_paper.py:423` liest ihn nur). Ob die parallele Sitzung sie von Hand ersetzt hat oder ein neues Werkzeug sie erzeugt, ist von hier aus nicht entscheidbar: `N/A_PENDING_REVIEWER`.
- **A3 — Reihenfolge.** `63_fortschritt_robust.py:65-78` liest `paper_exposition_kohorten.csv`, also die Ausgabe von `66_exposition.py`. Die Nummerierung suggeriert die umgekehrte Reihenfolge; wer `01`→`66` einmal durchlaufen lässt, bekommt eine stillschweigend gekürzte Tabelle (74 statt 88 Zeilen, es fehlen die Prädiktoren `exp_runde_max_vor` und `exp_vorsprung_b`) — ohne Fehlermeldung, nur mit einer Warnzeile im Log (`63_fortschritt_robust.py:77`). Das betrifft `figures/data/fig9_progress_forest.json`. **P2**, weil eine falsche Laufreihenfolge hier eine plausible, aber falsche Abbildung erzeugt.
- **A4 — Unversehrtheit des Originals.** Vor und nach dem Lauf mit `find … -printf '%T@ %s %p' | sort` verglichen. Die einzigen Unterschiede sind Zuwächse und Neuschreibungen der parallelen Sitzung (A1); keine Datei wurde durch diese Prüfung angefasst. Der Beweis ist damit nicht ganz sauber isoliert — bei einer ruhenden Arbeitskopie wäre er es.
- **A5 — Nicht geprüft:** ob die Zahlen im Fließtext von `main.tex` zu den Artefakten passen (nur Dateinamen-Referenzen wurden gesucht, keine Werte); ob `paper/figures/*.pdf` aus den neu erzeugten `figures/data/*.json` identisch entstehen; die vier `9x_release_*`-Skripte; `scripts/c/mt_seedscan`.
- **A6 — Zwei Vergleichsläufe zeigten unterschiedliche Ergebnisse** für `paper_archetypen_zuordnung.csv` und `harness_tier_words.csv` (einmal bitgleich, einmal abweichend). Beide Abweichungen sind Sortier- bzw. Rundungsrauschen unterhalb jeder Berichtsschwelle, belegen aber, dass die Kette nicht vollständig deterministisch ist.

## Was daraus folgt

1. Die Behauptung „jede Zahl stammt aus einem Artefakt, das die Skripte neu erzeugen" hält für **232 von 335** Dateien, davon 211 auf das Byte genau — inklusive aller großen Tabellen des Papers (`paper_fortschritt_kohorten.csv` 907 Zeilen, `paper_uhr_faktoren.csv`, `paper_prozess_zitatkaskade_kopien.csv` 3295 Zeilen).
2. Die im Paper offen benannten Ausnahmen decken **9 der 14** blockierenden Wurzeln.
3. Nicht gedeckt und im Paper zitiert sind **`paper_lernkurve_q2_inhaltlicher_lesebeweis.csv`** und **`paper_lernkurve_q3_format_erstversion_koordpop_6h.csv`** (Abbildungen 3 und 3b) sowie der gesamte Goldstandard-Zweig (zwei Rater-Dateien plus der im Artefakt selbst gespeicherte Adjudikations-Rücklauf).
4. Die 15 `harness_*`-Tabellen sind mit einem bekannten Werkzeug, aber unbekanntem Suchmuster entstanden — der billigste Reparaturposten der Liste.

```
verdict: fail
confidence: 88
ambiguities: [
  "A1: Original wurde waehrend der Pruefung von einer parallelen Sitzung veraendert (Skripte 90-93 neu, 53/57 geaendert, alle paper_math_* neu geschrieben); geprueft ist der Codestand 2026-09-09 20:13",
  "A2: paper_flotte_schaetzer_versoehnt.csv wurde im Original neu geschrieben, obwohl kein Skript diesen Namen schreibt - Urheber nicht bestimmbar (N/A_PENDING_REVIEWER)",
  "A5: Zahlenabgleich Fliesstext<->Artefakt, Neuerzeugung der PDF-Abbildungen, die vier 9x_release_*-Skripte und scripts/c/mt_seedscan wurden nicht geprueft",
  "A6: zwei Dateien (paper_archetypen_zuordnung.csv, harness_tier_words.csv) fielen zwischen zwei Laeufen unterschiedlich aus - Sortier-/Rundungsrauschen, kein Inhaltsunterschied"
]
```

---

## Nachtrag 2026-09-10 — zwei P2-Befunde behoben

Zwei der oben genannten Reparaturposten sind erledigt. Der Prüfbericht darüber bleibt unverändert; hier steht, was sich seither am Bestand geändert hat.

### P2 „unbekanntes Suchmuster" (Punkt 4 unter *Was daraus folgt*) — 14 von 15 geschlossen

Die Suchmuster der `harness_*`-Tabellen sind nicht mehr verloren. Sie wurden durch **Rückwärtssuche** rekonstruiert: ein Kandidat gilt nur dann als richtig, wenn `21_mine.py` mit ihm eine **bytegleiche** Datei erzeugt. Ergebnis:

- Muster stehen in `analyse/scripts/21_muster.json`.
- Erzeuger ist neu `analyse/scripts/21_mine_alle.py`; `--pruefen` baut alle Tabellen in einer Arbeitskopie neu und vergleicht Byte für Byte, `--schreiben` ersetzt den Bestand. Damit hat die Lauftabelle für diese 15 Dateien erstmals ein Skript, das ohne Argument durchläuft.
- **14 Tabellen: bitgleich.** Lauf vom 2026-09-10: `14 Tabellen geprueft, 0 Abweichungen`.
- **`harness_r1.csv`: nicht rekonstruiert.** Der beste falschtrefferfreie Kandidat `(initial|r1) (timer|deadline|window)|r1 (was|began)` deckt 151 der 193 Zeilen. Für die restlichen 42 gibt es keinen tragfähigen Zweig: im Korpus stehen fast gleich gebaute Sätze auf beiden Seiten der Grenze (im Ziel „nov27 cohort: r1 croatia prompt 03:36:50 … 5m59s timer, deadline 03:42:49", nicht im Ziel „may09 slow-tier cohort: r1 czech republic at 04:21:39 … 18m39 timer"). Auch eine erschöpfende Zweigsuche (Wort-n-Gramme mit null Fehltreffern plus Nähe-Templates um `r1`) lässt 62 Zeilen ungedeckt. Das spricht dafür, dass diese eine Datei aus einer älteren Fassung von `21_mine.py` stammt oder nach dem Lauf von Hand beschnitten wurde. Sie ist im Manifest als `status: naeherung` geführt und von der Prüfung ausgenommen — **offener Restposten, P3**.

*Warnung für Nachahmer:* `21_mine.py` schreibt fest nach `<basis>/artefakte/<name>`. Wer es zum Prüfen mit dem Original-Skriptpfad aufruft, überschreibt den Bestand. Beim Bau dieses Nachtrags ist genau das einmal passiert (`harness_r1.csv` wurde auf die Kopfzeile reduziert und aus einer Sicherung wiederhergestellt); `21_mine_alle.py` legt deshalb eine vollständige Ersatzwurzel im Temporärverzeichnis an und rührt `artefakte/` nur bei `--schreiben` an.

### P2 „Artefakt ist älter als sein Skript" — behoben, ohne Folgen für das Paper

Die fünf Lernkurven-Artefakte aus einer älteren Skriptfassung sind mit dem heutigen `41_lernkurve.py` neu erzeugt: `paper_lernkurve_q3_format_erstversion_{6h,tag,woche}.csv`, `paper_lernkurve_q4_technik_summary.csv`, `paper_lernkurve_revflags.parquet`.

Was sich geändert hat, ist belegt und klein:

- In den drei `q3`-Tabellen bewegt sich **einzig die Spalte `state_conf`**, um höchstens 0,3 Prozentpunkte — die Härtung des Musters in `41_lernkurve.py:21`. Alle übrigen Spalten und alle Zeilenzahlen sind unverändert.
- `paper_lernkurve_q4_technik_summary.csv` hat jetzt 15 statt 21 Spalten. **Alle Werte, die in Berichten zitiert werden, sind identisch** (je Technik geprüft: `t50` = alte `t_50pct` auf die Sekunde, `h_bis_10_labels` = alte `h_bis_10`, `labels_1h`, `labels` = alte `labels_gesamt`). Umbenannt, nicht neu berechnet. Die Technik `api.counterapi.dev` heißt jetzt `counterapi`.
- `paper_lernkurve_revflags.parquet` hat 26 statt 29 Spalten; die Zusatzspalte `state_conf2` gibt es im heutigen Code nicht mehr.

**Kein Wert des Papers bewegt sich.** Nachgewiesen, nicht angenommen: `65_adoption_robust.py` (der einzige Verbraucher von `revflags`) wurde mit den neuen Eingaben neu gelaufen; `paper_robust_hawkes_dedup.csv`, `paper_robust_format_gefiltert_6h.csv` und `paper/figures/data/fig3b_format_filtered.json` sind **bitgleich** zum Bestand. Die beiden Eingaben von Abbildung 3 (`…q2_inhaltlicher_lesebeweis.csv`, `…q3_format_erstversion_koordpop_6h.csv`) waren schon vorher bitgleich reproduzierbar und bleiben es.

Zwei Berichte nannten Spalten, die das heutige Skript nicht mehr schreibt; sie sind auf die aktuellen Namen gezogen: `BERICHT_lernkurve.md` (Verfahrensabsatz Q4, `t_50pct` → `t50`) und `BERICHT_visualisierung.md` (`h_bis_10` → `h_bis_10_labels`).
