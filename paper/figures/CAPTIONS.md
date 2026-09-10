# Figure captions (draft) and displayed numbers

Built by `analyse/scripts/57_chartdata_paper.py` (data → `paper/figures/data/*.json`) and
`analyse/scripts/58_figures_paper.py` (rendering → `paper/figures/*.pdf|png`). All numbers below are
taken from the JSON files; the paper text should cite them exactly as listed. Times are wall time, UTC.

---

## Figure 1 — Two operating states of the internal clock (`fig1_clock_two_states`)

**Caption (draft).** Internal-clock advance against wall-clock time between two contributions, both on
logarithmic axes. Open circles: 71 machine-derived factor measurements from the clean set (`primaer_AB`),
which scatter around a median factor of 0.435 (IQR 0.335–0.881) and follow slope ≈ 1. Filled diamonds:
11 self-reported `clock.wait` calibrations, in which the internal clock advanced 1.0–18.9 times faster
than wall time, with a sub-linear cost curve (log wall = 0.73 + 0.55·log internal). The two clouds occupy
disjoint wall-time ranges (12–140 s vs. 163–31,824 s); this is the finding, not a gap in the data.
The single working-set point with factor 26.3 is labelled, not removed.

**Numbers displayed.**
- working set: n = 71; factor median 0.435, IQR 0.335–0.881; wall-time range 163–31,824 s; 51 of 71 measurements on 16 Jun (text, not drawn)
- clock.wait set: n = 11; factor 1.0–18.9; wall-time range 12–140 s; largest internal advance 1,648 s
- reference lines: factor 1; factor 0.435 (median); wait regime log wall = 0.73 + 0.55·log internal (a = 0.734, b = 0.546)
- labelled outlier: factor 26.3 (wall 1,449 s, internal 38,115 s; name `TransportHelperDec08OAI`)

---

## Figure 2 — Time course of the incident (`fig2_time_course`)

**Caption (draft).** (A) Revisions per day over the full 40-day range 24 May – 2 Jul 2026 (14,591
revisions); 78.9 % fall on four days (16, 17, 18 and 22 Jun). (B) Hourly detail for 16–22 Jun
(cropped; only 260 of 948 hours in the full range have any activity): bars are revisions per hour, the
dashed line is distinct names per hour. The densest hour, 18 Jun 20:00, holds 2,350 revisions, of which
1,769 belong to one runaway copy loop; the highest simultaneity, 340 distinct names, is at 16 Jun 19:00.
The dash-dotted line marks the start of coordination (16 Jun 09:27); the grey band the night of
21/22 Jun, after which coordination ends.

**Numbers displayed.**
- 40 days, 14,591 revisions; 78.9 % on 16–18 and 22 Jun; daily maximum 6,543 (18 Jun)
- 260 of 948 hours have activity
- peak revisions: 18 Jun 20:00 = 2,350, of which 1,769 are one copy loop (the 1,769 is from MECHANIK.md, not a CSV)
- peak names: 16 Jun 19:00 = 340
- markers: 16 Jun 09:27 (start), night 21/22 Jun drawn as 21 Jun 21:00 – 22 Jun 06:00 (end)
- hourly panel cropped to 16 Jun 00:00 – 23 Jun 00:00

---

## Figure 3 — Format convergence in newcomers' first contributions (`fig3_format_convergence`)

**Caption (draft).** Share of newcomers' first contributions that carry a given format feature, per 6-h
window, for the coordinating population (top strip: newcomers per window; windows with n < 20 are
masked, 14 of 25 windows and 1,039 names remain; marker area ∝ n). Features the swarm invented on the
board (solid lines: "cohort", round marker, full report format) start at 0 % in the window before
coordination began (16 Jun 09:27) and reach 76–77 % within 24 h; features newcomers bring along
(dashed: signature line, "please relay" request formula) start at 31–33 %.

**Numbers displayed.**
- windows: 14 of 25 shown (n ≥ 20); names in shown windows 1,039; masked windows (n): 16 Jun 12:00 (6), 18 Jun 00:00 (8), 06:00 (8), 12:00 (10), 18:00 (14), 19 Jun 00:00 (12), 06:00 (11), 20 Jun 12:00 (11), 18:00 (9), 22 Jun 00:00 (1), 06:00 (1)
- "cohort" (invented): 0.0 % (16 Jun 06:00, n = 39) → 46.5 % (16 Jun 18:00, n = 409) → 47.2 % (17 Jun 00:00, n = 127); max 84.8 % (19 Jun 18:00); last 52.2 % (21 Jun 18:00, n = 46)
- round marker (invented): 0.0 % → 29.8 % (16 Jun 18:00) → 76.4 % (17 Jun 00:00, n = 127) → 77.1 % (17 Jun 06:00, n = 48); max 92.5 % (20 Jun 06:00); last 80.4 %
- full report format (invented): 0.0 % → 41.1 % → 61.4 % (17 Jun 00:00) → 75.0 % (17 Jun 06:00); max 78.8 % (19 Jun 18:00); last 60.9 %
- signature line (brought): 33.3 % at start; max 90.9 % (19 Jun 18:00); last 73.9 %
- "please relay" (brought): 30.8 % at start; max 73.9 % (17 Jun 18:00); last 50.0 %
- marks: 16 Jun 09:27; band "first 24 h" = 16 Jun 09:27 – 17 Jun 09:27; threshold n = 20

---

## Figure 4 — The load null result as a forest plot (`fig4_load_null_forest`)

**Caption (draft).** Spearman ρ with 95 % CI between the internal-clock factor and five wiki-load
measures (revisions, bytes, names, IP blocks, server events) in 5-, 15- and 60-min windows.
(A) Clean set `primaer_AB`, n = 71: all 15 estimates lie between +0.09 and +0.18 with the wrong sign
for the load hypothesis (which requires ρ < 0), and every interval contains 0 (p = 0.13–0.44); the
grey band shows that |ρ| < 0.33 was not detectable at 80 % power. The lower block shows three
robustness variants; only "wall ≥ 600 s, 15 min" narrowly excludes 0 (CI 0.009–0.529, p = 0.045).
(B) The same computation on the contaminated set `mit_Ereignissen_ABC`, n = 281, yields
ρ = 0.22–0.31 with p ≤ 1.8·10⁻⁴ — the spurious signal that appears when the control is dropped.
Because the five load measures correlate at 0.97, the 15 tests per panel amount to ≈ 2.2 independent tests.

**Numbers displayed (panel A, clean set, n = 71).**
| window | measure | ρ | 95 % CI | p |
|---|---|---|---|---|
| 5 min | revisions | +0.131 | −0.121 … +0.359 | 0.28 |
| 5 min | bytes | +0.094 | −0.154 … +0.323 | 0.44 |
| 5 min | names | +0.124 | −0.133 … +0.359 | 0.30 |
| 5 min | IP blocks | +0.145 | −0.111 … +0.380 | 0.23 |
| 5 min | server events | +0.152 | −0.104 … +0.385 | 0.21 |
| 15 min | revisions | +0.162 | −0.091 … +0.389 | 0.18 |
| 15 min | bytes | +0.127 | −0.120 … +0.345 | 0.29 |
| 15 min | names | +0.175 | −0.076 … +0.406 | 0.14 |
| 15 min | IP blocks | +0.169 | −0.082 … +0.399 | 0.16 |
| 15 min | server events | +0.170 | −0.082 … +0.400 | 0.16 |
| 60 min | revisions | +0.151 | −0.108 … +0.383 | 0.21 |
| 60 min | bytes | +0.099 | −0.152 … +0.324 | 0.41 |
| 60 min | names | +0.123 | −0.116 … +0.344 | 0.31 |
| 60 min | IP blocks | +0.170 | −0.089 … +0.398 | 0.16 |
| 60 min | server events | +0.181 | −0.085 … +0.411 | 0.13 |

Robustness block (revisions only): half sample n = 36: +0.119 / +0.141 / +0.185 (p 0.49 / 0.41 / 0.28);
wall ≥ 600 s n = 55: +0.254 (CI −0.014…0.505, p 0.062) / +0.272 (CI 0.009…0.529, p 0.045) / +0.274
(CI −0.003…0.536, p 0.043); bounds 0.01–200 n = 73: +0.130 / +0.155 / +0.155 (p 0.27 / 0.19 / 0.19).

**Numbers displayed (panel B, contaminated set, n = 281).** ρ: 5 min 0.271 / 0.233 / 0.277 / 0.301 / 0.279;
15 min 0.280 / 0.244 / 0.295 / 0.305 / 0.280; 60 min 0.254 / 0.222 / 0.268 / 0.274 / 0.251
(order: revisions, bytes, names, IP blocks, server events); all CIs exclude 0; largest p = 1.8·10⁻⁴
(bytes, 60 min), smallest 1.8·10⁻⁷ (IP blocks, 15 min).

Other: x-axis fixed to −0.4 … +0.6 in both panels; power band ±0.33; "≈ 2.2 effectively independent tests"
and "load measures correlate at 0.97" are from MECHANIK.md §7.4 (not in a CSV).

---

## Figure 5 — Rounds R1–R7 as a speech-act stack (`fig5_round_staircase`)

**Caption (draft).** Sentences mentioning each round, stacked by speech act (observation, request,
prediction, negation, unclassified), with the number of distinct names per round. R1–R5 are broadly
observed (563–1,390 observation sentences each); R6 is mentioned in 1,143 revisions by 405 names, but a
manual review of all 101 candidate "observation" sentences leaves exactly one genuine arrival report
("R6 CONFIRMED: Ecuador …", posted twice by the same name), so the figure shows 1 instead of the table
value 85. R7 has one arrival ("R7 CONFIRMED: Madagascar …"); R8–R10 (combined as R8+) have none.
Counts are sentence/revision counts, not agents — R2 > R1 is not survival.

**Numbers displayed.**
| round | observation (shown) | request | prediction | negation | unclassified | names | revisions |
|---|---|---|---|---|---|---|---|
| R1 | 976 | 114 | 380 | 73 | 1,567 | 723 | 2,050 |
| R2 | 1,390 | 494 | 1,219 | 232 | 1,287 | 808 | 2,247 |
| R3 | 1,082 | 1,020 | 1,541 | 52 | 1,255 | 851 | 2,416 |
| R4 | 888 | 1,111 | 1,560 | 204 | 1,008 | 752 | 2,170 |
| R5 | 563 | 1,802 | 1,600 | 324 | 1,057 | 778 | 2,354 |
| R6 | **1** (table: 85) | 953 | 613 | 215 | 400 | 405 | 1,143 |
| R7 | 1 (table: 1) | 23 | 41 | 2 | 61 | 36 | 127 |
| R8+ | 0 | 0 | 71 | 0 | 183 | 44 | 254 |

Review annotation: 102 candidate sentences reviewed in total (101 for R6, 1 for R7); R6: 2 rows judged
"arrival", both the same sentence by the same name → 1 arrival; R7: 1 arrival. R7 row: 128 classified sentences.

---

## Figure 6 — Lead time on the board (`fig6_lead_ecdf`)

**Caption (draft).** Empirical distribution of the lead (upper bound, hours) that the first report of an
item on the board had over a non-first reporter's own arrival, for 185 reporter–item pairs (144
distinct names) with leads within 24 h. The median lead is 3.4 h and 82.7 % of leads exceed 1 h,
whereas the most internal time any `clock.wait` ever bought was 27 min (1,648 s; dashed line) — an
order of magnitude too little to explain the information trade.

**Numbers displayed.**
- n = 185 reporter–item pairs, 144 distinct names, leads ≤ 24 h (of 236 rows in the source table; rows with lead 0 = first reporters excluded)
- median 3.4 h (3.44 h); 82.7 % of pairs ≥ 1 h
- 27 min = 1,648 s / 60 = 27.5 min, drawn at 0.458 h
- x-axis log, 0.01–24 h

---

## Figure 7 — Population estimate (`fig7_population_estimate`)

**Caption (draft).** Estimated number of episodes behind the 3,103 distinct names, by estimator, with
95 % intervals. The canonical capture–recapture estimate from calendar-valid name markers minus 20 real
writing dates is 876 [784–1,008] (Monte-Carlo interval); alternative label-based variants give 888
[787–996] and 911 [807–1,024], names + page names 1,245 [1,064–1,438], self-named cohorts 597
[541–658] (censored downward), and the assumption-free ratio 1,397 (no interval). The hard floor is
294 self-named cohorts; the naive count of 3,103 names lies far outside every interval.

**Numbers displayed.**
- names, all (month, day) markers: 911 [807–1,024], observed D = 335
- names, calendar-valid markers only: 888 [787–996], D = 333 (value in MECHANIK.md v1)
- names, minus 20 real writing dates (canonical): 876 [774–995], D = 332
- names + page names: 1,245 [1,064–1,438], D = 353
- self-named cohorts: 597 [541–658], D = 294
- ratio names : cohorts: 1,397 (no interval)
- reference lines: 294 (hard floor), 3,103 (distinct names)

---

## Figure 8 — CVD last-activity intervals (`fig8_cvd_intervals`)

**Caption (draft).** Last activity and death interval of the 23 reconstructed CVD cohorts on the
internal-clock axis (seconds after R1; top axis mm:ss), grouped by speed class. Each row runs from the
last observed sign of life (marker) to the first round never reported (R6 due, dash-dotted line:
5,513 s fast, 6,485 s medium). Filled circles: server-evidenced (20 cohorts); open diamonds:
self-reported in a cohort's own audit (3, fast class only); orange crosses: the time of death the
Apr30 and Dec30 audits inferred themselves (5,464 s). In the fast class all last signs of life fall
within a 62 s window (5,401–5,463 s), in the medium class within 120 s (6,332–6,452 s); the grey band
is the interval in which the class must have died — 50 s [5,463, 5,513] and 33 s [6,452, 6,485].

**Numbers displayed.**
- fast class (17 s answers): n = 11 cohorts (8 server, 3 audit); last activity 5,401–5,463 s (window 62 s); R6 due 5,513 s; death interval [5,463, 5,513] = 50 s; audits Apr30 and Dec30 infer death at 5,464 s
- medium class (22 s answers): n = 12 cohorts (12 server, 0 audit); last activity 6,332–6,452 s (window 120 s); R6 due 6,485 s; death interval [6,452, 6,485] = 33 s
- R6 due derived as global+5,549 s − 36 s (global → R1) for the fast class and R1+108m05 for the medium class (`r6_source` in the JSON)
- Jun30 (`unclassified`, last alive 6,142 s, no speed class stated) is in `paper_robust_horizont_cvd_intervalle.csv` but not in the JSON and not drawn
- source: `paper/figures/data/fig8_cvd_intervals.json` (written by `64_uhr_robust.py`, not by 57); the window and death-interval numbers are recomputed from the intervals in the plot and match `paper_robust_horizont_cvd_klassen.csv` (`alle_belegten` rows: fenster_s 62 / 120, todesintervall_s [5463, 5513] / [6452, 6485])

---

## Figure 9 — Progress predictors as a forest plot (`fig9_progress_forest`)

**Caption (draft).** Controlled standardised β with family-clustered 95 % CI for the ten progress
predictors of Table `tab_progress`, for the base set (n = 510 episodes, circles) and the ≥ 5-revision
subset (n = 256, squares). Only `counterapi` use (β = 0.19 [0.04, 0.35], q = 0.13) and request rate
(β = −0.10 [−0.19, −0.00], q = 0.20) have intervals that exclude zero in the base set, and neither
survives BH correction; the ≥ 5-revision subset reproduces both signs. Predictors marked † have fewer
than five treated families (hollow markers); blob egress has one treated family, so the clustered
SE is degenerate and no controlled estimate exists. Redirect services' subset CI is clipped at −1.0
(arrowhead). Right column: base-set β [95 % CI] and BH q, as in the table.

**Numbers displayed.**
- rows (table order): Cadence (log s), Initial deadline (log s), Answer deadline (log s), clock.wait used, counterapi used, Redirect services, Blob egress †, Observation on foreign page, Request rate, Future answer received †
- base (n = 510; cadence n = 99, initial deadline n = 68, answer deadline n = 217): β [CI], q — −0.07 [−0.29, 0.15] 0.91; −0.10 [−0.20, 0.01] 0.24; 0.02 [−0.16, 0.21] 0.92; 0.04 [−0.11, 0.19] 0.91; 0.19 [0.04, 0.35] 0.13; −0.07 [−0.79, 0.65] 0.92; blob egress ---; 0.01 [−0.11, 0.12] 0.92; −0.10 [−0.19, −0.00] 0.20; −0.16 [−0.76, 0.44] 0.91
- ≥ 5 revisions (n = 256; cadence n = 65, initial deadline n = 47, answer deadline n = 138): 0.01 [−0.36, 0.38]; −0.04 [−0.10, 0.01]; 0.05 [−0.12, 0.22]; 0.02 [−0.20, 0.25]; 0.24 [0.01, 0.46]; −0.32 [−1.34, 0.71]; blob egress ---; 0.08 [−0.15, 0.31]; −0.13 [−0.23, −0.03]; −0.12 [−0.29, 0.06]
- † = fewer than 5 treated families in the base set (`n_fam_true`): blob egress 1, future answer 4 (redirect services has exactly 5 and is not flagged)
- x-axis −1.0 to 0.8; clipped CI ends drawn as arrowheads
- CSV rows used: `paper_robust_fortschritt_effekte.csv` with `variante == basis`, `modell == OLS_std_FE_cluster`, `teilmenge ∈ {alle, n_deltas>=5}` (20 rows, one per predictor × subset; the raw Spearman / rank-biserial / HC1 / permutation rows are not drawn)

---

## Deviations from the plan

1. **Fig 1 axis meaning.** The plan's `clock.wait` power law is stated as log(cost) = 0.55·log(duration) + 0.73 with cost = wall seconds and duration = internal seconds (`paper_math_uhr_clockwait_modelle.csv`: a = 0.734, b = 0.546, log_rss best of two models). It is drawn as internal = (wall / e^a)^(1/b), i.e. the same relation with axes as in the scatter. The line is limited to wall 8–400 s so it does not extend under the working cloud.
2. **Fig 2 "end" marker.** The plan gives no explicit end time; "night of 21/22 Jun" is drawn as a grey band 21 Jun 21:00 – 22 Jun 06:00. Hourly data show two further bursts on 22 Jun at 02:00 (411 revisions) and 08:00 (463 revisions) and a last revision at 22 Jun 19:00 (1); the band is a marker, not a cut. Lower panel cropped to 16 Jun – 23 Jun 00:00 (plan: 16–22 Jun) so that 22 Jun is fully visible.
3. **Fig 2 copy-loop count.** "1,769 of 2,350 revisions are one copy loop" is in MECHANIK.md §2 only, not in any `paper_*.csv`; it is drawn as given in the task.
4. **Fig 3 series selection.** The plan lists six lines (cohort, runde, meldeformat solid; sig_endzeile, please_relay, uhrenpaar dashed). Five are drawn; `uhrenpaar` (clock pair) was dropped to stay legible at single-column width; the task's "brought along" pair is signature + request formula. The CSV has two extra columns (`zeitstempel`, `vollformat`) not used. Windows with n < 20 are masked (not interpolated); lines connect the remaining points. The Wilson band for `meldeformat` suggested in the plan was not drawn (would require computing new statistics).
5. **Fig 3 key number.** The task says "0 → 75 % in 24 h". In the CSV, the round marker goes 0.0 % (16 Jun 06:00 window, n = 39) → 76.4 % (17 Jun 00:00, n = 127) → 77.1 % (17 Jun 06:00, n = 48); the full report format reaches 75.0 % at 17 Jun 06:00; "cohort" reaches only 47 % by 17 Jun 00:00 and peaks at 84.8 % on 19 Jun. Cite "76 % within 24 h" for the round marker, not 75 % for all invented features.
6. **Fig 4 panel C.** The plan's third panel (diurnal cycle, `paper_uhr_tagesgang.csv`, Kruskal p = 0.881) was not requested and is not drawn. The robustness block under panel A is drawn as the plan requires. The power threshold |ρ| = 0.33 and the "≈ 2.2 effective tests" come from MECHANIK.md §7.4, not from a CSV.
7. **Fig 5 review source.** The plan cites `paper_episode_r6plus_observation_candidates.csv`; the task names `paper_episode_r6_sichtung.csv`, which exists and was used (102 rows: 101 R6, 1 R7; `urteil == ANKUNFT` for 2 R6 rows that are the same sentence by the same name, and 1 R7 row). Note the mismatch between the table's 85 R6 "observation" sentences and the 101 reviewed R6 candidates — the review file counts more candidates than the classifier column; the figure text says "table value 85; 101 candidates reviewed".
8. **Fig 6 column names.** `paper_neuheit_vorsprung_eigenankunft_labels.csv` has columns `fam, round, item, label, time, first, lead_h`; `lead_h` is used. The task's "185 names" corresponds to 185 *rows* (reporter–item pairs) with 0 < lead_h ≤ 24, which map to 144 distinct names; the median (3.44 h) and share ≥ 1 h (82.7 %) match MECHANIK.md only under this row-level filter. The caption says "185 reporter–item pairs (144 distinct names)".
9. **Fig 7 source table.** The plan (§3.11) used `paper_flotte_schaetzer.csv` (911 as the name-based estimator, plus "nur Body-Kohorten" 563 [511–620]); the task names `paper_flotte_schaetzer_versoehnt.csv`, which was used. It reconciles the 911 / 888 / 876 discrepancy (all three drawn; 876 marked canonical) but does not contain the Body-cohort row, so 563 is not shown. Its `beobachtet_D`/`ci_*` of −1 for the ratio row are treated as "no value". The plan's convergence band 900–1,450 was not drawn because the canonical estimate (876) lies below 900.
10. **General.** No hatching/decal on Fig 1–4, 6, 7 (only Fig 5 uses hatch); two-state distinctions are carried by marker shape (Fig 1, 4, 7) or line style (Fig 2, 3).
11. **Fig 10 (exposure and adoption).** Built by `66_exposition.py` (not by `57_chartdata_paper.py`), which writes `figures/data/fig10_exposure_adoption.json` directly — the same route `65_adoption_robust.py` uses for `fig3b_format_filtered.json`. Three panels (round marker, *cohort*, full report format), three series each, over the `seite` variant (page channel). The feed channel (last 100 revisions wiki-wide, De Marzo's definition) is deliberately **not** drawn: it is 95 % saturated across all features and all six-hour windows and would produce three flat lines. Windows with n < 20 are masked, as in Fig 3, and the population is the same 1,140 coordinating names, so Fig 3 and Fig 10 are read on one scale. The "no page source" counts in the panel annotations are corpus totals over all windows, not the sum of the drawn (masked) windows.
