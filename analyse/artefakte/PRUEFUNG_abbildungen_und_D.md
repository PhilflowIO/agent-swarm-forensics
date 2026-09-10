# Prüfung: Abbildungen gegen ihre Quellen, und der widersprüchliche Datensatz-Zähler D

**Auftrag.** (A) Für jede Abbildung im Paper Quelle, Skriptzeile, Aktualität, Wertegleichheit und Caption-Treue bestimmen. (B) Den Widerspruch 331 vs. 332 belegte Kalendertage auflösen — durch Neuberechnung aus dem Rohabzug, nicht durch Glauben an eine der beiden Quellen.

**Datenbasis.** `analyse/data/labels.jsonl` (3.103 Labels), `analyse/artefakte/paper_*.csv`, `paper/figures/data/*.json`, `paper/figures/*.pdf|png`, `paper/main.tex`, `paper/tables/*.tex`, `MECHANIK.md`.

**Vorgehen.** Zeitstempel per `ls -l --time-style=full-iso`. Wertevergleich per Neulauf einer **Kopie** von `57_chartdata_paper.py` mit umgebogenem `ROOT`/`OUT` in ein Scratch-Verzeichnis (`/tmp/claude-1000/.../scratchpad/figcheck/`), anschließend `diff` gegen die eingecheckten JSON. **Es wurde nichts unter `paper/` oder `analyse/` geschrieben** außer dieser Datei.

---

## Das Wichtigste in fünf Sätzen

1. **Neun von zehn Abbildungen sind aktuell und wertgleich** — der Neulauf von `57_chartdata_paper.py` erzeugt für fig1–fig7 byteidentische JSON.
2. **Abbildung 9 ist veraltet und widerspricht ihrer eigenen Tabelle.** `paper_robust_fortschritt_effekte.csv` wurde am 2026-09-09 um 20:05:45 neu geschrieben, `fig9_progress_forest.json` stammt von 10:40:04. Die Abbildung druckt **jede** BH-q-Zahl anders als `tab_progress.tex` (0,91 statt 0,83; 0,24 statt 0,22; 0,20 statt 0,16 …) und zeigt nur 10 der 12 Prädiktoren.
3. **D = 332 ist richtig, 331 ist falsch** — unabhängig aus `labels.jsonl` nachgerechnet: von 333 kalendergültigen Marker-Töpfen entfällt beim Entfernen der 20 Namen mit realem Schreibdatum genau **ein** Topf vollständig (`Jun16`, einziges Label `ResearchAssistantJune16`).
4. **Die kanonische Zeile ist eine Chimäre aus drei verschiedenen D.** `paper_flotte_schaetzer_versoehnt.csv:4` schreibt D = 331, dazu den Punktschätzer 876 (der zu D = 332 gehört) und das Intervall [784, 1008] (das nachweislich zu D = **333** gehört, `_paper_math.log:8`).
5. **Folge für den Text:** Das gedruckte 95-%-Intervall des kanonischen Populationsschätzers ist zu weit. Unter der Bereinigungsregel gehört zu n̂ = 876 das Monte-Carlo-Intervall **≈ [776, 995]**, nicht [784, 1008].

---

# Teil A — Abbildungen gegen die CSVs

## A.1 Quellen- und Skriptkarte

`57_chartdata_paper.py` erzeugt in seinem `__main__` (Z. 524–525) nur `fig1, fig2, fig3, fig4, fig5, fig6, fig7, fig9`. **fig8, fig10 und fig3b entstehen in anderen Skripten.** `58_figures_paper.py` liest ausschließlich `paper/figures/data/*.json` (Z. 48) und schreibt PDF/PNG (Z. 53–54) — es rührt die Artefakte nicht an, kann also eine veraltete JSON nicht bemerken.

| Abb. | Datenquelle (Artefakt) | Erzeugende Zeile | Zeitstempel-Urteil | Wertevergleich | Caption-Treue |
|---|---|---|---|---|---|
| **1** Uhr, zwei Zustände | `paper_uhr_faktoren.csv` (09-08 18:58), `paper_episode_clockwait_measurements.csv` (09-08 18:41), `paper_math_uhr_clockwait_modelle.csv` (09-08 19:46) | `57:58–139` → `58:85` | **aktuell** (JSON 09-09 10:40, PDF 09-09 20:05) | **identisch** | **ok** |
| **2** Zeitverlauf | `paper_episode_daily.csv`, `paper_episode_hourly.csv` (beide 09-08 18:34) | `57:141–205` → `58:125` | **aktuell** | **identisch** | **ok** |
| **3** Formatkonvergenz | `paper_lernkurve_q3_format_erstversion_koordpop_6h.csv` (09-08 18:39) | `57:207–262` → `58:195` | **aktuell** | **identisch** | **ok** |
| **4** Last-Nullbefund | `paper_uhr_korrelation.csv` (09-08 19:00) | `57:265–319` → `58:251` | **aktuell** | **identisch** | **ok** |
| **5** Rundentreppe | `paper_episode_round_mentions.csv` (09-08 18:35), `paper_episode_r6_sichtung.csv` (09-08 19:56) | `57:321–386` → `58:307` | **aktuell** | **identisch** | **ok** |
| **6** Vorsprungs-ECDF | `paper_neuheit_vorsprung_eigenankunft_labels.csv` (09-08 19:27), `paper_episode_clockwait_measurements.csv` | `57:388–420` → `58:348` | **aktuell** | **identisch** | **ok** |
| **7** Populationsschätzer | `paper_flotte_schaetzer_versoehnt.csv` (09-08 19:56) | `57:422–453` → `58:377` | **aktuell** (Quelle älter als JSON) | **identisch** | **ok für die Abbildung**, aber die *Quelle* ist falsch — siehe Teil B |
| **8** CVD-Intervalle | direkt in `64_uhr_robust.py` berechnet (kein CSV-Zwischenschritt); Schwesterdatei `paper_robust_horizont_cvd_intervalle.csv` 09-09 10:33:54.4345 | `64:470` → `58:417` | **aktuell** (JSON 10:33:54.4350, aus demselben Lauf) | nicht neu gerechnet — `N/A_PENDING_REVIEWER` (Neulauf von `64` schreibt nach `paper/tables/`, außerhalb des Leseauftrags) | **ok** |
| **9** Fortschritts-Forest | `paper_robust_fortschritt_effekte.csv` — **09-09 20:05:45** | `57:477–520` → `58:479` | **VERALTET**: Quelle 20:05:45, JSON 10:40:04 | **ABWEICHUNG** in allen 14 `q_bh`-Werten | **FALSCH** — siehe A.3 |
| **10** Exposition/Übernahme | `paper_exposition_adoption_6h.csv` (09-09 20:04:27) | `66:663` → `58:535` | **aktuell** (JSON 20:04:29, derselbe Lauf) | nicht neu gerechnet — `N/A_PENDING_REVIEWER` (Neulauf von `66` schreibt in `paper/`) | **ok**, mit einer Fußnote (A.4) |

`fig3b_format_filtered.json` (`65_adoption_robust.py:328`) hat **kein** Gegenstück in `paper/figures/` und wird in `main.tex` nirgends referenziert (`grep -n "fig3b" paper/main.tex` → 0 Treffer). Tote Datei, kein Befund.

## A.2 Wertevergleich (Neulauf in Scratch)

Kommando:

```
sed -e 's#^ROOT = .*#ROOT = Path("<repo>")#' \
    -e 's#^OUT = ROOT / "paper" / "figures" / "data"#OUT = Path("<scratch>/out")#' \
    analyse/scripts/57_chartdata_paper.py > <scratch>/57_copy.py
analyse/.venv/bin/python <scratch>/57_copy.py
```

Ausgabe des anschließenden `diff` je Datei:

```
IDENTISCH  fig1_clock_two_states
IDENTISCH  fig2_time_course
IDENTISCH  fig3_format_convergence
IDENTISCH  fig4_load_null_forest
IDENTISCH  fig5_round_staircase
IDENTISCH  fig6_lead_ecdf
IDENTISCH  fig7_population_estimate
ABWEICHUNG fig9_progress_forest
```

## A.3 P1 — Abbildung 9 ist veraltet und widerspricht Tabelle 5

**Befund 1: alle BH-q-Werte sind falsch.** Der `diff` zeigt Abweichungen ausschließlich im Feld `q_bh`; alle `beta`, `ci_lo`, `ci_hi`, `n` sind unverändert. Die Geometrie des Forest-Plots stimmt also, die **gedruckte q-Spalte nicht**. `58_figures_paper.py:511` druckt sie sichtbar in die Abbildung:

```python
txt = f"{b['beta']:+.2f} [{b['ci_lo']:+.2f}, {b['ci_hi']:+.2f}]  q = {b['q_bh']:.2f}"
```

Basis-Teilmenge, alt (in `fig9_progress_forest.pdf`) gegen neu (in `tab_progress.tex`, erzeugt 20:05:45):

| Prädiktor | Abbildung 9 zeigt | Tabelle 5 zeigt |
|---|---|---|
| Cadence (log s) | 0,91 | **0,83** |
| Initial deadline (log s) | 0,24 | **0,22** |
| `clock.wait` used | 0,91 | **0,83** |
| `counterapi` used | 0,13 | **0,16** |
| Request rate | 0,20 | **0,16** |
| Future answer received | 0,91 | **0,83** |

Auch die vier ≥5-Revisionen-Werte verschieben sich (0,44→0,36; 0,73→0,70; 0,94→0,92; 0,45→0,37; 0,18→0,22; 0,11→0,13), sie werden aber nicht gedruckt. **Jede** gedruckte q-Zahl der Abbildung widerspricht der Tabelle, auf die die Caption selbst verweist (`main.tex:356`: „(Table~\ref{tab:progress})"). Das ist der Fehler, der im Druck auffällt.

**Befund 2: zwei Prädiktoren fehlen.** Ursache derselbe Lauf: `63_fortschritt_robust.py:106–107` hat die Expositions-Prädiktoren ergänzt —

```python
("exp_runde_max_vor", "Highest round visible on arrival", False),
("exp_vorsprung_b",   "Answer ahead visible on arrival",  True),
```

— beide stehen in `paper_robust_fortschritt_effekte.csv` und in `tab_progress.tex` (12 Prädiktorzeilen). Die Reihenfolge-Konstante `PROGRESS_ORDER` in `57_chartdata_paper.py:460–471` listet weiterhin nur die alten 10. Der Kommentar dort lautet „same order as `paper/tables/tab_progress.tex`" — das stimmt seit 20:05:45 nicht mehr. Weil die BH-Korrektur über die gewachsene Familie läuft, ist das auch die *Ursache* von Befund 1: Familiengröße 10 → 12 verschiebt alle q.

**Korrektur (in dieser Reihenfolge):**
1. `analyse/scripts/57_chartdata_paper.py:460–471` — `("exp_runde_max_vor", "Highest round visible on arrival")` und `("exp_vorsprung_b", "Answer ahead visible on arrival")` ans Ende von `PROGRESS_ORDER` ergänzen.
2. `analyse/.venv/bin/python scripts/57_chartdata_paper.py` aus `analyse/` heraus.
3. `analyse/.venv/bin/python scripts/58_figures_paper.py`.
4. Caption `main.tex:356` prüfen: der Satz „No interval excluding zero is positive except one specification of the counter-service indicator" bleibt wahr, weil beide neuen Prädiktoren negativ sind (`exp_vorsprung_b`: β = −0,12 [−0,24, −0,00]); der Satz „Predictors with fewer than five treated families are drawn hollow" ebenfalls. Die Zeilenzahl der Abbildung wächst von 10 auf 12 — Höhe der Grafik prüfen.

## A.4 Caption-Treue im Einzelnen (alle übrigen Abbildungen)

Geprüft wurde jede Zahl aus dem jeweiligen `\caption{}` gegen das JSON bzw. Artefakt.

**Abb. 1 (`main.tex:228`)** — „$n=71$ pair-level … from 53 names": `fig1…json` Serie `work` hat 71 Punkte, 53 distinkte `label`. ✔ „$n=11$ agent self-calibrations": Serie `wait`, 11 Punkte. ✔ „median factor 0.435": `factor_median` = 0,435. ✔ „factors 1.0--18.9": Wertebereich der `wait`-Faktoren 1,0 … 18,94. ✔

**Abb. 2 (`main.tex:176`)** — „24 May to 2 July": `points` laufen `2026-05-24` … `2026-07-02`. ✔ „Four days carry 78.9\,\%": `top4_share` = 0,78912. ✔ „18 June, 20:00 UTC, \num{2350} revisions": Stundenpunkt `2026-06-18T20:00:00Z` = 2350. ✔ „one runaway copy loop": Mark-Text „2,350 revisions, of which 1,769 are one copy loop". ✔ „begins at 09:27:10 UTC on 16 June" und „night of 21/22 June": beide als `marks` hinterlegt. ✔

**Abb. 3 (`main.tex:286`)** — „start at exactly 0\,\%": `cohort.first` = 0,0, `runde.first` = 0,0. ✔ „round marker reaches 76\,\% and cohort 47\,\% within 18 hours": erstes Fenster `2026-06-16T06:00Z`, +18 h = `2026-06-17T00:00Z` → `runde` 76,4 / `cohort` 47,2. ✔ „full report format goes from 0 to 75\,\% in 24 hours": +24 h = `2026-06-17T06:00Z` → `meldeformat` 75,0. ✔ „plateaus at 60--79\,\%": `meldeformat.max` = 78,8, letzter Wert 60,9. ✔ „Windows with $n<20$ are masked": `min_n` = 20, 14 von 25 Fenstern behalten. ✔

**Abb. 4 (`main.tex:241`)** — „clean set ($n=71$)": Panel `clean`, `n` = 71, `all_ci_contain_zero` = true. ✔ „($n=281$)": Panel `dirty`, `n` = 281. ✔ „$\rho=0.22$--$0.31$": `rho_range` = [0,2219; 0,3053]. ✔ „five … measures in three window widths" = 15 Zeilen je Panel. ✔ „effectively 2.2 independent tests" stammt aus `MECHANIK.md §7.4`, nicht aus dem JSON — `N/A_PENDING_REVIEWER` für die Abbildungsprüfung, im Bericht `BERICHT_mathematik.md` aber belegt.

**Abb. 5 (`main.tex:272`)** — „For R6 the naive classifier lists 85 candidates": `review.r6_table_observation` = 85. ✔ „manual review of all 101 R6 candidates leaves exactly one genuine arrival": `r6_candidates` = 101, `r6_arrivals` = 1. ✔ „the single R7 candidate is genuine": `r7_candidates` = 1, `r7_arrivals` = 1. ✔ „a control of 40 random R5 observations found 40 genuine arrivals" und „sixteen borderline cases … copied sixteen times by eleven names": stehen nicht im JSON — `N/A_PENDING_REVIEWER` (Quelle ist `paper_episode_r6_sichtung.csv` bzw. der Sichtungsbericht, nicht die Abbildungsdaten).

**Abb. 6 (`main.tex:340`)** — „185 reporter--item pairs (144 distinct names)": `n_rows` = 185, `n_distinct_names` = 144. ✔ „Median 3.4\,h": `median_h` = 3,4436. ✔ „82.7\,\% above one hour": `share_ge_1h` = 0,82703. ✔ „dashed line … (27\,min)": Mark bei x = 0,4578 h = 27,5 min. ✔

**Abb. 7 (`main.tex:213`)** — „876 [784--1008]", „294 self-named cohorts", „\num{3103} names": alle drei so im JSON. ✔ **Aber** die Quelle selbst ist falsch, siehe Teil B; die Caption erbt den Fehler des Intervalls.

**Abb. 8 (`main.tex:511`)** — „server-evidenced rows in black, self-reported audits in grey": im JSON kommen nur `kind ∈ {server, audit, audit_inferred_death}` vor, kein Fall bleibt unbeschrieben. ✔

**Abb. 10 (`main.tex:318`)** — „for the \num{1140} coordinating names": `paper_exposition_adoption_gesamt.csv:2` führt `n` = 1140 für jede Variante. ✔ „Windows with $n<20$ are masked": `min_n` = 20. ✔ **P3-Fußnote:** die Summe der 25 Fenster-`n` im JSON ist **1130**, nicht 1140 — zehn Namen fallen aus dem 6-h-Raster. Die Caption sagt „per six-hour window, for the 1140 coordinating names"; streng gelesen zeigt die Abbildung 1130 davon. Formulierungssache, kein Zahlenfehler; die Gesamtzahl 1140 ist korrekt.

---

# Teil B — Der Datensatz-Zähler D: 331 gegen 332

## B.1 Fundstellen

**Für 331 (fünf Stellen, alle auf dieselbe Quelle zurückgehend):**

| Datei:Zeile | Beleg |
|---|---|
| `analyse/artefakte/paper_flotte_schaetzer_versoehnt.csv:4` | `bereinigt: minus 20 reale Schreibdaten,331,876,784,1008,"KANONISCH — Monte-Carlo-Intervall, 15x Jun22 entfernt"` |
| `paper/figures/data/fig7_population_estimate.json:35` | `"observed": 331,` (von `57_chartdata_paper.py:427` aus der CSV übernommen) |
| `paper/main.tex:198` | `\textbf{Names, minus 20 real write dates} & \textbf{331} & \textbf{876} & \textbf{784--1008} (Monte Carlo) \\` |
| `paper/tables/tab_population_robust.tex:8` | `Minus 20 names carrying their real write date & 331 & 876 [784--1008] & main-text estimate; Monte-Carlo interval \\` |
| `MECHANIK.md:111` | `\| **bereinigt um 20 reale Schreibdaten** \| **331** \| **876** \| **784…1008** \|` |
| `paper/figures/CAPTIONS.md:167` | `- names, minus 20 real writing dates (canonical): 876 [784–1,008], D = 331` |

**Für 332 (drei Stellen, alle aus dem Code):**

| Datei:Zeile | Beleg |
|---|---|
| `analyse/scripts/53_mathematik.py:106` | `print(f"  Ohne diese {n_real} Namen: D = {D_clean}, n̂ = {invert(D_clean):.0f}")` — die Zählregel selbst |
| `analyse/artefakte/_paper_math.log:11` | `  Ohne diese 20 Namen: D = 332, n̂ = 876` (Lauf-Ausgabe) |
| `analyse/artefakte/paper_math_population_schaetzer.csv:4` | `ohne reale-Datums-Kontamination,332,876.0350297541821,777.6768616649688,983.4482297304235` |
| `analyse/artefakte/BERICHT_mathematik.md:53` | „Ohne diese 20 Namen: D = 332, **n̂ = 876** [777 … 985]." |
| `paper/main.tex:206` (Fließtext!) | „gives 782 clusters **on 332 dates** with a dispersion index of 0.85" — **`main.tex` widerspricht sich selbst um eins**, Tabelle gegen Fließtext. |

## B.2 Neuberechnung aus dem Rohabzug

**Zählregel (die im Code stehende, `53_mathematik.py:98–106` in Verbindung mit `42_flotte_marker.py:47–86`):** D ist **nicht** „Kalendertage mit archivierter Version", sondern die Zahl der **belegten (Monat, Tag)-Töpfe von 365** im Fang-Wiederfang-Modell:

1. Aus jedem Labelnamen wird per `RX` (`42:59`) ein fiktiver Datumsmarker extrahiert — Kürzel+2 Ziffern, ausgeschriebener Monat+2 Ziffern, ausgeschriebener Monat+ausgeschriebener Tag.
2. **Kalendergültig** (`42:62–63`, `valid()`: Tag ≤ Monatslänge, Feb ≤ 28, Referenzjahr 2027 = kein Schaltjahr).
3. Ein Label zählt **nur mit genau einem** distinkten gültigen Marker (`42:83`, `if len(ms) == 1`).
4. **Bereinigung:** Labels, deren Marker gleich Monat und Tag ihres **realen** `first_write` ist, werden entfernt (`53:99–105`, `real_date_match`).
5. D = `dated_clean.groupby(["month","day"]).ngroups` (`53:105`).

Es gibt in dieser Regel weder eine UTC-Tagesgrenze noch ein `date_range` — beides sind mögliche Fehlerursachen, die hier **nicht** greifen.

Unabhängiger Nachlauf direkt gegen `analyse/data/labels.jsonl` (Skript in `<scratch>/dcheck.py`, importiert nur die Extraktionsfunktionen aus `42_flotte_marker.py`, ohne dessen Schreibpfade):

```
labels: 3103
D_full (kalendergueltig, genau ein Marker): 333   n datierte Labels: 1035
Namen mit Marker == realem Erstschreibdatum: 20
{('Jun', 16): 1, ('Jun', 18): 2, ('Jun', 20): 1, ('Jun', 21): 1, ('Jun', 22): 15}
D_clean: 332
komplett entfallene Buckets: [('Jun', 16)]
    ('Jun', 16) n_labels: 1 alle real: True ['ResearchAssistantJune16']
```

**D = 332 ist richtig.** Die Bereinigung entfernt 20 Namen aus 5 Töpfen; nur `Jun16` verliert dabei sein einziges Label und fällt aus der Belegung. 333 − 1 = 332.

## B.3 Ursache der Abweichung

Keine Zeitzone, kein halboffenes Intervall, kein `date_range`-Off-by-one. Die Ursache ist ein **Denkfehler beim Handpflegen einer nicht regenerierbaren Tabelle**.

`42_flotte_marker.py:189–191` sagt es selbst:

```
log("  NICHT regeneriert (Ableitung aus diesem Skript nicht belegbar): 'Labels + Seitennamen' (D=353),")
log("  'Kohortennennungen im Text' (D=294), 'nur Body-Kohorten' (D=287), 'Verhaeltnis Labels:Kohorten',")
log("  'bereinigt: minus 20 reale Schreibdaten' (Monte-Carlo-Intervall, vgl. 53_mathematik.py Teil A).")
```

`paper_flotte_schaetzer_versoehnt.csv` ist also von Hand gepflegt; `paper_flotte_schaetzer_regen.csv` enthält nur die zwei maschinell belegbaren Zeilen (335 und 333). Die Bemerkung der fraglichen Zeile — „15x Jun22 entfernt" — verrät die Annahme: es wurde unterstellt, dass mit den 15 `Jun22`-Namen auch der Topf `Jun22` verschwindet, zusätzlich zu `Jun16`, also 333 − 2 = 331. Tatsächlich enthält `Jun22` weitere Labels, die *kein* reales Schreibdatum tragen; der Topf bleibt belegt.

**Der Widerspruch ist damit größer als „um eins".** Die Zeile mischt drei verschiedene D:

| Feld der Zeile | Wert | gehört zu D = |
|---|---|---|
| `beobachtet_D` | 331 | — (kein D erzeugt diese Kombination) |
| `n_hat` | 876 | **332** — `invert(332)` = 876,04; `invert(331)` = 865,15; `invert(333)` = 887,25 |
| `ci_lo, ci_hi` | 784, 1008 | **333** |

Beleg für die letzte Zeile, `analyse/artefakte/_paper_math.log:5–8`:

```
Belegte Daten D=333, datierte Namen n=1035, …
[Nachrechnung] n̂ = 887.3, Akzeptanzbereich-Inversion (Normalapprox.) 95%: [787, 997]
[Monte-Carlo-Inversion, exakt] 95%: [784, 1008]
```

`53_mathematik.py:86` ruft `mc_ci(D_obs)` mit `D_obs` = **333** auf, nie mit `D_clean`. Das Intervall [784, 1008] ist das Monte-Carlo-Intervall des **unbereinigten** Markersatzes und wurde an den bereinigten Punktschätzer angeheftet.

Eigene Monte-Carlo-Inversion (gleiche Methode, 3000 Replikate, drei Startwerte, `<scratch>`):

```
D=331: (765, 983) (767, 981) (768, 982)
D=332: (776, 998) (776, 995) (775, 992)
D=333: (787, 1009) (790, 1009) (786, 1006)
```

[784, 1008] liegt eindeutig im D-333-Band.

## B.4 Auswirkung

**Auf den Punktschätzer: keine.** n̂ = 876 ist bereits der Wert zu D = 332 und bleibt unverändert. Die Prämisse „verschiebt eine Populationsschätzung um etwa drei Episoden" trifft nicht zu: hätte D = 331 gestimmt, wäre n̂ = **865** gewesen, also **11 Episoden** weniger. Der Fehler steckt nicht im gedruckten Schätzer, sondern in der gedruckten Beobachtungszahl daneben — Tabelle und Schätzer sind zueinander inkonsistent.

**Auf das Intervall: ja.** Zu n̂ = 876 unter der Bereinigungsregel gehört Monte Carlo **≈ [776, 995]** (Normalapproximation: [778, 983], `paper_math_population_schaetzer.csv:4`). Gedruckt ist [784, 1008]. Die untere Grenze liegt um ~8, die obere um ~13 Episoden zu hoch.

**Was sich nicht ändert.** Der Fließtext `main.tex:206` (782 Cluster auf 332 Daten, Dispersionsindex 0,85, n̂_GP = 877, Chao1 365,3 ± 9,6, Obergrenze 1185) rechnet durchgehend mit D = 332 — `paper_math_population_cluster.csv:2` und `paper_math_population_gamma_poisson.csv:2` führen beide `332`. Ebenso unberührt: die Zeilen 335/333/353/294 der Tabelle, die Bodenschätzung 294 und die Spanne „roughly 800--1400".

## B.5 Empfohlener Wert und die genau zu ändernden Stellen

**Empfohlen: D = 332, n̂ = 876, 95 % Monte Carlo [776, 995].**

Die Ursache liegt in genau **einer** Datei; alles andere ist abgeleitet. Reihenfolge:

1. **`analyse/artefakte/paper_flotte_schaetzer_versoehnt.csv:4`** — Wurzel. Ersetzen durch:
   ```
   bereinigt: minus 20 reale Schreibdaten,332,876,776,995,"KANONISCH — Monte-Carlo-Intervall zu D=332 (53_mathematik.py); 20 Namen mit realem Erstschreibdatum entfernt, davon 15x Jun22; nur der Topf Jun16 entfaellt"
   ```
   Vorher `53_mathematik.py` so laufen lassen, dass `mc_ci(D_clean)` protokolliert wird, und dessen Zahl übernehmen — die drei Startwerte oben schwanken um ±3.
2. **`analyse/.venv/bin/python scripts/57_chartdata_paper.py`** (aus `analyse/`) → schreibt `paper/figures/data/fig7_population_estimate.json` neu; dann **`scripts/58_figures_paper.py`** → `fig7_population_estimate.pdf|png`.
3. **`paper/main.tex:198`** — `\textbf{331}` → `\textbf{332}`; `\textbf{784--1008}` → `\textbf{776--995}`.
4. **`paper/main.tex:206`** — „(95\,\% interval 784--1008)" → „(95\,\% interval 776--995)". Der Nebensatz „on 332 dates" bleibt und stimmt dann mit der Tabelle überein.
5. **`paper/main.tex:213`** (Caption Abb. 7) — „876 [784--1008]" → „876 [776--995]".
6. **`paper/tables/tab_population_robust.tex:8`** — `331 & 876 [784--1008]` → `332 & 876 [776--995]`. (Die Datei trägt in Z. 1 den Kommentar „generated … from paper_flotte_schaetzer_versoehnt.csv"; falls sie ein Generator schreibt, dort ansetzen statt von Hand.)
7. **`paper/figures/CAPTIONS.md:167`** — „876 [784–1,008], D = 331" → „876 [776–995], D = 332".
8. **`MECHANIK.md:111`** — `**331**` → `**332**`, `**784…1008**` → `**776…995**`.

Zusätzlich empfohlen, damit der Fehler nicht wiederkehrt: `42_flotte_marker.py` um eine Zeile erweitern, die die bereinigte Variante mit erzeugt (die Bereinigungslogik steht bereits vollständig in `53_mathematik.py:98–106`), damit `paper_flotte_schaetzer_versoehnt.csv` keine handgepflegte Zeile mehr braucht.

---

## Zusammenfassung der Befunde

| # | Prio | Befund | Ort |
|---|---|---|---|
| 1 | **P1** | Abb. 9 zeigt veraltete BH-q-Werte, jeder einzelne widerspricht `tab_progress.tex` | `paper/figures/data/fig9_progress_forest.json` (10:40) vs. `paper_robust_fortschritt_effekte.csv` (20:05:45) |
| 2 | **P1** | Abb. 9 fehlen die zwei Expositions-Prädiktoren, die die Tabelle führt | `analyse/scripts/57_chartdata_paper.py:460–471` |
| 3 | **P1** | D = 331 ist falsch; richtig ist 332 (nur `Jun16` entfällt vollständig) | `analyse/artefakte/paper_flotte_schaetzer_versoehnt.csv:4` + 5 abgeleitete Stellen |
| 4 | **P1** | Das kanonische 95-%-Intervall [784, 1008] gehört zu D = 333, nicht zur bereinigten Zeile | `_paper_math.log:8`, `53_mathematik.py:86` |
| 5 | **P2** | `main.tex` widerspricht sich intern: Tabelle 331 gegen Fließtext 332 | `paper/main.tex:198` vs. `:206` |
| 6 | **P3** | Abb. 10: Caption nennt 1140 Namen, die Fenstersumme der Abbildung ist 1130 | `paper/main.tex:318` |
| 7 | **P3** | `fig3b_format_filtered.json` wird erzeugt, aber nirgends gezeichnet oder zitiert | `analyse/scripts/65_adoption_robust.py:328` |

---

```
verdict: fail
confidence: 92
ambiguities:
  - "fig8 und fig10 wurden nicht wertgleich nachgerechnet: ihre Erzeuger (64_uhr_robust.py, 66_exposition.py) schreiben auch nach paper/tables/ bzw. paper/figures/ und liessen sich nicht ohne Mehrfach-Patch in ein Scratch umleiten. Zeitstempel-Urteil (beide aus demselben Lauf wie ihre JSON) steht, Inhaltsgleichheit ist N/A_PENDING_REVIEWER. Klaerung: Kopien der Skripte mit umgebogenen FIGDATA/TABLES-Konstanten laufen lassen und diffen."
  - "Das exakte Monte-Carlo-Intervall zu D=332 schwankt startwertabhaengig zwischen [775,992] und [776,998]. Der empfohlene Wert [776,995] ist der Median dreier Laeufe mit reps=3000. Klaerung: 53_mathematik.py mit dem projekteigenen Startwert 20260908 und mc_ci(D_clean) laufen lassen und die protokollierte Zahl uebernehmen."
  - "Zwei Caption-Aussagen zu Abb. 5 (40 von 40 kontrollierten R5-Beobachtungen; sechzehn Grenzfaelle, elf Namen, eine Seite) stehen nicht in den Abbildungsdaten und wurden nicht gegen paper_episode_r6_sichtung.csv geprueft: N/A_PENDING_REVIEWER."
  - "Ob paper/tables/tab_population_robust.tex von einem Skript erzeugt wird, ist offen — der Kopfkommentar behauptet es, aber kein Skript unter analyse/scripts/ nennt den Dateinamen. Falls handgepflegt, ist es eine zweite haendische Wahrheit neben der versoehnt-CSV."
```
