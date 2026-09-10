# Limitations, collected from the twelve detail reports (raw, English)

Collected 2026-09-08 from `analyse/artefakte/BERICHT_*.md`. Every bullet keeps its source line.

## BERICHT_episodenstruktur.md

- Real container lifetime (Q2c) rests on the assumption label ≈ container. Plausible for 738 distinct labels but unprovable; generic labels (ResearchHelper, Test, empty string) are demonstrably reused across episodes (max span 588 h), so the 2.21 h median is a lower bound with unknown surcharge. (source: BERICHT_episodenstruktur.md:379)
- `harness_tier_table.csv` holds 33 data rows while the task names 34 curated configurations; the difference was not resolved, possibly a counted header row. N/A_PENDING_REVIEWER. (source: BERICHT_episodenstruktur.md:380)
- The column `cooldown_r1_to_r2` is heterogeneous: in some rows the R1→R2 gap, in others the steady-state cadence R2..R5. The duration formula r1 + 4×cadence is therefore biased by the R1→R2 special effect in up to a third of rows; direction and size of the bias are unquantified. (source: BERICHT_episodenstruktur.md:381)
- 12 of the 33 tier rows are incomplete and excluded from the duration statistics; whether the missing rows are systematically fast or slow cohorts was not tested. (source: BERICHT_episodenstruktur.md:382)
- Q1 counts were deliberately taken on the full body rather than the delta, so "versions/labels/pages per round marker" are mention reach, not authorship counts — a version counts even when the marker comes from a foreign agent on the same page. The decisive R6/R7 finding was verified verbatim and is unaffected. (source: BERICHT_episodenstruktur.md:383)
- The stretch factor <1 for the pair methods is explained by two agent quotes about "strategic context resets"; that explanation comes from the corpus itself, i.e. it is agent self-description, not an independently verified harness property. N/A_PENDING_REVIEWER. (source: BERICHT_episodenstruktur.md:384)
- None of the 95 horizon values (+28 min to 7 h 15) is a harness announcement; all are agent-side hypotheses, so the true shutdown parameter remains unevidenced. (source: BERICHT_episodenstruktur.md:385)
- `events.jsonl` (19,913 lines) was not used for any of the five questions; whether request_action/success_observed would bound container lifetime more tightly than revision timestamps is untested. (source: BERICHT_episodenstruktur.md:386)

## BERICHT_flottengroesse.md

- Uniform distribution over the 365 date buckets is assumed, not verifiable from the data, because the harness source code is absent from the dataset. N/A_PENDING_REVIEWER. (source: BERICHT_flottengroesse.md:293)
- 2,068 labels without a date marker (73 percent of all versions) were not traced back to episodes; their episode structure is unknown. (source: BERICHT_flottengroesse.md:294)
- The number of containers is in principle undeterminable: the IP level is devalued by per-request rotation (14,277 IPs across 14,591 versions), and one container may have run several episodes serially (evidence: OAI7C97 with three dates). (source: BERICHT_flottengroesse.md:295)
- The number of conversation threads is undeterminable: only 3 thread IDs exist in the whole corpus, so no inversion is possible. N/A_PENDING_REVIEWER. (source: BERICHT_flottengroesse.md:296)
- The labels+page-names estimator (n=1,245) is near saturation (353 of 365 buckets occupied) and therefore markedly more fragile than the labels-only estimator. (source: BERICHT_flottengroesse.md:297)
- Topic assignment in `paper_flotte_datum_topic.csv` is derived from the page, not the speaker, so 571 pairs are biased upward. (source: BERICHT_flottengroesse.md:298)
- `events.jsonl` was not evaluated as an independent evidence source (its 14,591 save events carry ip16 = null). (source: BERICHT_flottengroesse.md:299)

## BERICHT_lernkurve.md

- `events.jsonl` contains only 101 probe events, all with success_observed=false. A read-contact test against read accesses is NOT feasible with this export; the 58.30 % "cold start without read contact" is an artifact of the /16 aggregation (median 27 labels per ip16, median distance 21.4 days) and must not be cited. (source: BERICHT_lernkurve.md:248)
- Whether a newcomer read "cohort" and the R/G round marker from the wiki or brought them in via the container prompt is undecidable — a shared task scaffold produces the same picture as diffusion, and container prompts are not in the export. (source: BERICHT_lernkurve.md:249)
- The acceleration of technique spread (factor 16–56) confounds population and time: earlier techniques belong to Population A (distributed, non-communicating), later ones to Population B (dense, 5-day window). Within-population comparison shows NO acceleration. (source: BERICHT_lernkurve.md:250)
- The rendezvous classification in question 1 rests on the morphology heuristic in `schwarm_pagename_morphology.csv`, whose building-block lists were set by hand rather than clustered, so the i/iii class boundary is stipulated, not measured. (source: BERICHT_lernkurve.md:251)
- The "content-level read proof" (12.5 %) is a strict lower bound: it only captures cases where the page name appears as a CamelCase token of ≥12 characters in the text. Paraphrased or shortened references fall through, and the converse (reading without mention) is unobservable. (source: BERICHT_lernkurve.md:252)
- 1,246 deleted pages have no archived content, and 39,456 save attempts face 14,591 archived versions (factor 2.70), so all proportions are lower bounds. (source: BERICHT_lernkurve.md:253)

## BERICHT_uhr_auslastung.md

- Inference-infrastructure load is not measured in the corpus. Hypothesis (b) was tested against swarm activity as a proxy, so a load effect that does not show up in the posting rate would be invisible. (source: BERICHT_uhr_auslastung.md:388)
- All 71 primary factor measurements fall in the window 16–21 June 2026, 51 of them on 16 June. A robustness check "without the peak week" is impossible, and the load regressor varies mostly within a single day. (source: BERICHT_uhr_auslastung.md:389)
- Discriminatory power: at n=71 only |rho| ≥ 0.33 is detectable with 80 % probability, so a moderate load effect (|rho| ≈ 0.2) cannot be excluded. (source: BERICHT_uhr_auslastung.md:390)
- label ≠ episode: at least two labels demonstrably post to different cohorts, so the within-label test is only an approximation of the within-episode test. (source: BERICHT_uhr_auslastung.md:391)
- The within-episode rate change rests on ONE clean case (OpenAIJul03Police, 0.154 → 0.528); a second independent case is missing, as only 6 labels have ≥2 strict measurements. (source: BERICHT_uhr_auslastung.md:392)
- Extraction precision was made plausible by sample inspection, not counted out, because no annotated gold set exists. (source: BERICHT_uhr_auslastung.md:393)

## BERICHT_prozess.md

- The cohort rule inherits foreign dates: labels named after a foreign page or signing with a foreign date land in the wrong cohort. Documented case: a human handle in `cashiers|Jul05` via the signature fallback. Magnitude unknown, no sample drawn. (source: BERICHT_prozess.md:344)
- `max_runde_belegt` is temporally censored — a cohort may have reached R5 without documenting it. Not resolvable; it probably explains the negative sign of the time parameters. (source: BERICHT_prozess.md:345)
- Family effect vs. reporting format: DataUSA families report states (`STATE5-XX`) while CVD/Police/CO2 report `R5 confirmed`, and the classifier only recognises the latter as an observation, making the Kruskal-Wallis effect (p=3e-39) an upper bound. (source: BERICHT_prozess.md:346)
- The request rate is compositional (observations in the denominator), so its negative relation with the highest round is real but not causally interpretable. (source: BERICHT_prozess.md:347)
- Two cadence definitions exist (from deadline vs. from question), differing by the R1 deadline; this affects every comparison with `harness_tier_table.csv` and BERICHT_episodenstruktur.md §2a. (source: BERICHT_prozess.md:348)
- Ghost pages: why 1,246 deleted pages have no archived version while 3,898 others do cannot be explained from the export. (source: BERICHT_prozess.md:349)
- Lost saves: `labels.jsonl` gives only per-label totals with no per-attempt timestamps, so the retry-loop reading rests on the ρ = 0.48 correlation and the 1,772 empty deltas rather than direct observation. (source: BERICHT_prozess.md:350)
- Internal-clock spans are computed without a day-rollover correction and may be wrong for spans > 12 h (rare; p75 = 6 h 19 min). (source: BERICHT_prozess.md:351)

## BERICHT_ml_verhalten.md

- The network/proxy category is dual-purpose (bypass AND data retrieval), which contaminates the 60.6 % byte upper bound; only the conservative figure (≥18.2 % of deltas) is defensible, since the regex classification cannot resolve dual purpose per delta. (source: BERICHT_ml_verhalten.md:151)
- The meta-vs-task classification is a stipulated regex heuristic rather than clustered from the data, and the 2,407 deltas with ENV&TASK overlap are assigned to ENV by priority. (source: BERICHT_ml_verhalten.md:152)
- The fictitious-date test rests on n=129 markers derived from names, so a moderate association would go undetected (small n; names are disposable tags). (source: BERICHT_ml_verhalten.md:153)
- All statements rest on agent claims plus the server log, not on system logs; read accesses are entirely absent — the export contains no successful read operation. (source: BERICHT_ml_verhalten.md:154)
- The benchmark/evaluator self-label is freely chosen language (35/20 names) and is no ground truth about the harness's purpose. (source: BERICHT_ml_verhalten.md:155)

## BERICHT_mathematik.md

- The agent's OWID country list (204 entries, South Korea at index 169) was not independently checked; it is not needed to reproduce indices 44, 1, 46, 13, and the list is absent from the dataset. (source: BERICHT_mathematik.md:276)
- Calendar days 21–31 are over-represented in the episode clusters (χ² p=0.006); the cause is unknown, possibly further real-date contamination of the May/June population, but the effect on n̂ under Gamma-Poisson and Chao1 is negligible. (source: BERICHT_mathematik.md:277)
- The Hawkes branching ratio (0.6–0.9) is an upper bound on contagion, because harness start waves and contagion cannot be separated without a read-access log. (source: BERICHT_mathematik.md:278)
- Cost curve of the wait command: exponent 0.55 with CI [0.09; 1.00] at n=11 — the power law beats the surcharge model, but sublinearity is not established. (source: BERICHT_mathematik.md:279)
- The "A only" subset was reconstructed with n=39 rather than the reported 42 (slope identical, 1.029 vs 1.025), because the subset definition in the clock report is not documented exactly. (source: BERICHT_mathematik.md:280)
- The latent schedule scale rests on 15 complete rows of a curated table — a small and possibly selective sample. (source: BERICHT_mathematik.md:281)

## BERICHT_neuheit_kritik.md

- The head-start measurement (part 3) uses a family key derived from page names and post time as an upper bound on arrival; tier decomposition and mapping to the internal clock are outstanding. (source: BERICHT_neuheit_kritik.md:156)
- Whether "fast cohort" always means a tier configuration or sometimes clock.wait acceleration is not always separable from the wording, and the 2-of-36 figure depends on self-reported usage. (source: BERICHT_neuheit_kritik.md:157)
- Literature: arXiv IDs were verified via API by the research agent, not by the author. SandboxEscapeBench (arXiv:2603.02277) was confirmed by the arXiv API on 2026-09-08 (refs/VERIFICATION.md), so that part of the discrepancy is closed; Moltbook remains listed in PRUEFSTAND/FAELLE without independent confirmation. (source: BERICHT_neuheit_kritik.md:158; resolved 2026-09-08)
- Jefferson's Time Warp (1985) and Lamport clocks were not verified. (source: BERICHT_neuheit_kritik.md:159)
- Uniformity of the fictitious dates is not directly testable (the coverage count is binary), and the share of real dates among the markers was checked only for Jun15–Jun23. (source: BERICHT_neuheit_kritik.md:160)
- The 494/204 self-check proves consistency, not execution: an agent that knows 2^32/204^3 could also have fabricated 494. (source: BERICHT_neuheit_kritik.md:161)

## BERICHT_horizont.md

- The second-level finding rests on a single family (Healthdata-CVD, 23 cohorts, 3 audits, all on 2026-06-21); for the other families there are only isolated statements supporting a tier-fixed horizon, because only CVD measured the horizon systematically. (source: BERICHT_horizont.md:523)
- Whether the internal clock is token time (which would make candidates 3 and 4 identical) hinges on two agent statements about clock progress while idle (29 internal seconds during a 60 s sleep; ~3.5×) and on the slope-1 measurement in BERICHT_uhr_auslastung.md — not independently verified, as there is no system log. (source: BERICHT_horizont.md:524)
- All consumption measures are wiki traces; Test A is structurally blind to consumption that does not show up in write volume, since the extract contains no telemetry. (source: BERICHT_horizont.md:525)
- label ≠ container even for distinctive names (the Mar09 cohort appears under three names within three minutes). Tests A, B, C, D, E-world-time and G carry this blur; Test H does not. (source: BERICHT_horizont.md:526)
- Test B (context reset) has only 21 % power at n=5 for a doubling effect, so question (b) is undecided. (source: BERICHT_horizont.md:527)
- The true 22 s-tier horizon exists only as the interval [R1+107m32; R1+108m05], and the 17 s-tier value global+5500 s comes from three audits, one of which (Apr23) has an estimated internal time; the moment of death is never observed beyond the heartbeats. (source: BERICHT_horizont.md:528)
- The 36 s lead time from global start to R1 is an agent statement and not independently checkable. (source: BERICHT_horizont.md:529)

## BERICHT_dramaturgie.md

- Topics are regex-defined and the NMF served derivation, not classification; no delta-wise validation against manual annotation was done. Sample reads (5–10 deltas per regex) showed URL hits for `netzsperre` (`uniq=403`) and the word `token` in URL parameters for `signal`; both were defused by prose matching, but single-digit percent residual noise is possible. Per-topic precision is N/A_PENDING_REVIEWER. (source: BERICHT_dramaturgie.md:181)
- Topic shares are computed on deltas, but Population A deltas are on average 3–8× longer in bytes than conversation deltas; `anteil_bytes` is in both heatmap CSVs but was not used as the main measure. (source: BERICHT_dramaturgie.md:182)
- Breakpoint tests are two-mean segmentations without a model for autocorrelation, so the permutation p-values understate uncertainty; the 15-minute resolution (test b) has 46 bins, 9 of them before 09:30. (source: BERICHT_dramaturgie.md:183)
- Cross-correlations at |lag| > 0 rest on n = 50–76 hours and on topics with < 60 deltas (`netzsperre`, `zweifel`), and are reported as coincidence, not sequence. (source: BERICHT_dramaturgie.md:184)
- Populations A and B were separated here only by topic shares, not by the `SCHWARM.md` definition; agreement with its daily split (coordination on 16.06: 1,335 there vs. ~1,467 coordination-flagged here) is close but not identical because the regex sets differ. (source: BERICHT_dramaturgie.md:185)
- The claim "no delta asks for permission" rests on the listed English-language regex terms; German or paraphrasing formulations were not searched. (source: BERICHT_dramaturgie.md:186)

## BERICHT_archetypen.md

- The three-way split is reproducible (bootstrap ARI 0.89) but weakly separated (silhouette 0.17, gap statistic selects k=1, 61 % agreement across methods) — it describes regions of a continuum, a convention rather than discovered class boundaries. (source: BERICHT_archetypen.md:288)
- The bridge-builder cohorts are partly Population A labels with an inherited date (24 % landing-site contact, 34 % date not from the label name), so the behaviour is real but the cohort boundary is not. (source: BERICHT_archetypen.md:289)
- Rare axes (teaching, environment surveying, thanks, farewell) with base rates of 0.1–3.5 % are not clusterable; their shrunken shares correlate mechanically with volume (ρ down to −0.77) and are reported descriptively only. (source: BERICHT_archetypen.md:290)
- `wert`/`wert_unaufgefordert` overlaps with the observation class underlying the target variable, so "share with observation" per type (79/55/33 %) is partly construction; the §5a test therefore conditions on an observation (p = 0.12). (source: BERICHT_archetypen.md:291)
- The day effect (p ≤ 0.002 within family) cannot be separated into population turnover vs. behavioural change, given median lifespans of 1.3 h. (source: BERICHT_archetypen.md:292)
- Page clustering is partly circular, since `fremde_seite` and `url` are both type features and page features. (source: BERICHT_archetypen.md:293)
- Only 36 % of labels and 35 % of versions carry a cohort, so the typology holds for the coordinating population only. (source: BERICHT_archetypen.md:294)

## BERICHT_visualisierung.md

- Topic heatmap: the choice between `anteil` (frequency) and `anteil_bytes` (volume) as the colour value is undecided; both are in the file and the resulting statement differs. (source: BERICHT_visualisierung.md:347)
- Population estimator: CSV gives 911 (807–1024) while MECHANIK gives 888 (787–996) — resolved since: canonical is 876 [784…1008] in `paper_flotte_schaetzer_versoehnt.csv`. (source: BERICHT_visualisierung.md:348)
- R6 observations: the CSV has observation=85 while the paper reports 1 after individual inspection; the supporting artifact is `paper_episode_r6_sichtung.csv`. (source: BERICHT_visualisierung.md:349)
- Provider groups (Amazon/Altafiber/Arcor/Tor) — resolved since: column `anbieter` in `paper_netzblock_whois.csv`. (source: BERICHT_visualisierung.md:350)
- Ref-MCP had no credits; all documentation evidence comes from the llms-documents mirror via Crawl4AI, and canonical option.html anchors were not separately cross-read. (source: BERICHT_visualisierung.md:351)
- The error-bar mechanism is not native in ECharts; irrelevant for the matplotlib figures used in the paper. (source: BERICHT_visualisierung.md:352)

## Cross-cutting themes

1. **No read logs — reading is structurally unobservable.** The export contains no successful read operation, so diffusion, contagion and influence can never be separated from a shared prompt scaffold or harness start waves. Raised by: lernkurve, ml_verhalten, mathematik, episodenstruktur, horizont, flottengroesse.
2. **Names are not containers, labels are not episodes.** Wiki labels are freely chosen and demonstrably reused (max span 588 h; one cohort under three names in three minutes), so every lifetime, episode and within-episode statistic is an approximation. Raised by: episodenstruktur, horizont, uhr_auslastung, flottengroesse, archetypen.
3. **Self-reports vs. server evidence.** Horizons, shutdown parameters, "strategic context resets", the 36 s lead time, "fast cohort" usage and benchmark/evaluator self-labels are all agent claims with no harness-side confirmation. Raised by: episodenstruktur, horizont, ml_verhalten, neuheit_kritik.
4. **Heuristic and regex classification without gold annotation.** Topic, meta-vs-task, rendezvous morphology and clock-factor extraction rest on hand-set patterns with priority rules and no counted precision. Raised by: dramaturgie, ml_verhalten, lernkurve, uhr_auslastung, archetypen, prozess.
5. **Small n and low statistical power for clock and time measurements.** n=71 clean clock pairs (only |rho| ≥ 0.33 detectable), n=5 with 21 % power, n=11 with CI [0.09; 1.00], n=129 date markers, 15 curated rows, one clean within-episode case. Raised by: uhr_auslastung, horizont, mathematik, ml_verhalten, dramaturgie.
6. **All counts are lower bounds — the archive is incomplete.** 1,246 deleted pages without archived content, 39,456 save attempts vs. 14,591 archived versions (factor 2.70), censored `max_runde_belegt`, upper-bound branching ratio and family effect. Raised by: lernkurve, prozess, mathematik, episodenstruktur.
7. **English-only, token-shaped pattern searches.** The "no permission asked" null result covers only English regex terms, and the read proof only counts CamelCase tokens of ≥12 characters, so paraphrase and other languages fall through. Raised by: dramaturgie, lernkurve.
8. **Family and cohort keys derived from page names.** Signature and name fallbacks inherit foreign dates into the wrong cohort, topics are attributed to the page rather than the speaker, and only 36 % of labels carry a cohort at all. Raised by: prozess, archetypen, neuheit_kritik, flottengroesse, lernkurve.
