# Robustheitsprüfung Uhr / Fahrplanskala / CVD-Horizont (Reviewer-Runde)

Skript: `analyse/scripts/64_uhr_robust.py` (seed 20260909, Log `analyse/artefakte/_paper_robust_uhr.log`).
Betroffene Paper-Stellen: `paper/main.tex` Z. 139-141 (Clock-rate measurement), Z. 212-235 (Three clocks), Z. 237-256 (Death).
Alle Zahlen unten stammen aus dem Lauf vom 2026-09-09 und stehen im Log.

## Zitierfähige Kernsätze

- **A (Uhr).** Auf Namensebene (53 Namen, Median je Name) liegt der Streckfaktor bei 0,481 (IQR 0,355–1,155) gegenüber 0,435 (IQR 0,335–0,881) auf Paarebene (71 Paare); der Cluster-Bootstrap über Namen gibt für den Paar-Median [0,40; 0,53], für den Namens-Median [0,40; 0,70] und für die log-log-Steigung [0,65; 1,14] (Paarebene) bzw. [0,53; 1,13] (Namensebene). Keines der 22 negativen Innen-Deltas ist mit einem Mitternachtsübergang innerhalb von 6 h vereinbar; die +24-h-Korrektur ändert den Datensatz daher nicht (n = 71, Median 0,435), und die Einschränkung auf sicher kurze Intervalle (< 2 h Weltzeit) ergibt n = 62, Median 0,454 (IQR 0,351–0,802).
- **B (Fahrplanskala).** Die 15 vollständigen Zeilen der Tier-Tabelle sind mit Seite, Zeitstempel, Name und Zitat belegt; 37 der 45 Werte stehen wörtlich im kuratierten Zitat, 7 sind aus Uhrzeiten im Zitat abgeleitet oder per Korpussuche belegt, 1 Wert (Folgefrist 83 s, Nov20/Nov21 SLOW) bleibt `N/A_PENDING_REVIEWER`. Die Leave-one-row-out-PCA liefert PC1 zwischen 0,755 und 0,815 (voll: 0,784); der Zeilen-Bootstrap [0,65; 0,90].
- **C (CVD-Horizont).** Als Intervall formuliert: In der schnellen Klasse (17 s) liegt der Tod zwischen dem letzten Lebenszeichen R1+91:03 und der nie gemeldeten R6 bei R1+91:53 (50 s), in der mittleren Klasse (22 s) zwischen R1+107:32 und R1+108:05 (33 s). Nur server-belegte Zeilen (eigener Post mit Server-Zeitstempel, ohne die drei Audit-Kohorten): schnell n = 8, Fenster der letzten Lebenszeichen 62 s, CV 0,006; mittel n = 12, Fenster 120 s, CV 0,005 — identisch mit den Zahlen im Paper, weil alle 23 Kohorten einen eigenen Überlebenspost haben und die Audits nur zusätzliche Information sind.

---

## Teil A — Streckfaktoren

### Methode

1. **Rekonstruktion.** `build_factors` aus `50_uhr_auslastung.py` Z. 213-251 wurde re-implementiert und auf `paper_uhr_taskzeiten.csv` (Wege A+B) angewendet. Ergebnis: 71 Paare, 53 Namen, Faktoren bis auf 1e-9 identisch mit `paper_uhr_faktoren.csv` (`datensatz == primaer_AB`) — Log-Zeile `[A0] … identische Faktoren=True`. Eine Falle dabei: `task_fakedate` ist im Original ein String (leer = ""), im CSV NaN; NaN ist wahrheitswertig und hätte in der Bedingung `a.fd and b.fd and a.fd != b.fd` (Z. 236) Paare fälschlich verworfen. Das Skript füllt deshalb mit "".
2. **Namensebene.** Je Name der Median seiner Faktoren (→ 53 Werte); Steigung auf Namensebene als OLS über die Namensmediane von log ΔWall und log ΔTask, zusätzlich eine gewichtete Paar-OLS (Gewicht 1/Paare je Name).
3. **Cluster-Bootstrap.** 4000 Ziehungen von Namen mit Zurücklegen, alle Paare des Namens mitgenommen; Perzentil-Intervalle für Median, Q25, Q75 und Steigung auf beiden Ebenen.
4. **Mitternacht.** Drei Varianten: (i) Ausschluss (Status quo, `allow_roll=False`); (ii) +24 h nur, wenn das korrigierte Innen-Delta ≤ 6 h **und** das Welt-Delta ≤ 6 h ist („wall-equivalent“: ein echter Mitternachtsübergang innerhalb eines kurzen Fensters ergibt nach Korrektur ein Innen-Delta in der Größenordnung des Welt-Deltas); (iii) nur Intervalle mit Welt-Delta < 2 h. Zur Einordnung zusätzlich die uneingeschränkte +24-h-Korrektur (entspricht dem `allow_roll=True`-Zweig, der im Original nie aufgerufen wird).

### Zahlen

| Datensatz | Ebene | n | Median | IQR | Steigung ± SE | Cluster-Bootstrap Median | Cluster-Bootstrap Steigung |
|---|---|---|---|---|---|---|---|
| primär A+B | Paare | 71 (53 Namen) | 0,435 | 0,335–0,881 | 0,906 ± 0,112 | [0,402; 0,525] | [0,653; 1,140] |
| primär A+B | Namen | 53 | 0,481 | 0,355–1,155 | 0,851 ± 0,122 (gewichtete Paar-OLS 0,893) | [0,396; 0,697] | [0,534; 1,132] |
| nur A (weg = AA) | Paare | 39 (32 Namen) | 0,435 | 0,369–0,775 | 1,029 ± 0,164 | [0,402; 0,547] | [0,716; 1,332] |
| nur A (weg = AA) | Namen | 32 | 0,481 | 0,382–1,152 | 0,934 ± 0,151 (gewichtet 0,995) | [0,407; 0,720] | [0,577; 1,260] |

Konzentration: kein Name trägt mehr als 3 Paare; 38 der 53 Namen haben genau 1 Paar; nur 12,7 % der Paare stammen von Namen mit ≥ 3 Paaren. Die Paarebene ist also kaum von Einzelnamen dominiert — was erklärt, warum Paar- und Namens-Median nahe beieinander liegen; der Unterschied im oberen Quartil (0,88 vs. 1,16) kommt von Mehrfach-Namen, deren Median höher liegt als ihr einzelnes „schnelles“ Paar.

Mitternacht (`paper_robust_uhr_mitternacht.csv`, Kandidaten in `paper_robust_uhr_mitternacht_kandidaten.csv`):

| Variante | n | Namen | Rollover | Median | IQR | Steigung |
|---|---|---|---|---|---|---|
| Ausschluss (Status quo) | 71 | 53 | 0 | 0,435 | 0,335–0,881 | 0,906 |
| +24 h, eingeschränkt (≤ 6 h) | 71 | 53 | 0 | 0,435 | 0,335–0,881 | 0,906 |
| nur Welt-Delta < 2 h | 62 | 46 | 0 | 0,454 | 0,351–0,802 | 0,848 |
| +24 h uneingeschränkt (nur Einordnung) | 86 | 63 | 15 | 0,519 | 0,355–2,468 | 1,165 |

Es gibt 22 negative Innen-Deltas (ΔWall ≥ 120 s, gleiche fiktive Daten). **Keines** ist mit einem Mitternachtsübergang in einem ≤ 6-h-Fenster vereinbar: die korrigierten Faktoren streuen 0,91 – 259 (Median 12,75). Das bestätigt die Paper-Begründung („+24 h indistinguishable from an episode change“), jetzt mit Zahl.

### Was das für das Paper heißt

- Der Median 0,435 ist robust gegen die Ebene (0,48 auf Namensebene) und gegen Mitternacht; das Cluster-Intervall des Paar-Medians [0,40; 0,53] sollte neben dem Punktwert stehen.
- Die IQR-Obergrenze ist die instabilste Größe (Paare 0,88, Namen 1,16, Cluster-Bootstrap Q75 auf Namensebene bis 2,46). Der Satz „consistent across all clean subsets“ gilt für den Median, nicht für die IQR.
- **Inkonsistenz im Paper (P2):** Die Steigung „1.03 [0.70, 1.36]“ (main.tex Z. 226) stammt aus `53_mathematik.py` Z. 284/303 für **nur A, n = 39** (`paper_math_uhr_steigung.csv`, Zeile „nur A (explizite Paare)“), nicht aus dem im selben Absatz genannten Primärsatz n = 71, dessen Steigung 0,906 [0,68; 1,13] ist (`paper_uhr_steigungstest.csv`, Zeile primaer_AB). Beides ist verträglich mit 1 und unverträglich mit 0; das Paper sollte aber sagen, welcher Satz gemeint ist. Cluster-Bootstrap: nur A [0,72; 1,33], primär [0,65; 1,14].

## Teil B — Latente Fahrplanskala

### Extraktionsregel

`harness_tier_table.csv` ist **kuratiert**: `28_tiertable.py` Z. 5-38 enthält die 33 Zeilen als Literale (Familie, Kohorte, R1-Timer, Kadenz R1→R2, Folgefrist, Seite, Zeitstempel, Name, wörtliches Zitat); es gibt keinen Regex-Extraktor, das Zitat ist der Beleg. `26_config.py` (`harness_episode_configs.csv`, 12 Zeilen) ist ein unabhängiger Regex-Lauf (Z. 11 `RX_CD`) und wurde für die Provenienzsuche nicht benötigt. Die PCA in `53_mathematik.py` Z. 521-528 nimmt die 15 Zeilen mit allen drei Werten (`dropna`) und rechnet eine SVD im zentrierten Log-Raum; PC1 = 0,784.

Provenienz je Wert (`paper_robust_fahrplan_provenienz.csv`, Kürzel in `tab_scheduler_rows.tex`): **Q** = Token wörtlich im Zitat (37/45); **D** = aus zwei Uhrzeiten im Zitat abgeleitet (2: Jul03-Kadenz 51m55 = 00:04:38 − 22:58:25 − 14m18; Mar08-R1 10m00 = 15:49:19 − 15:39:19); **C** = per Korpussuche mit Kohortenwort im Treffer belegt (5: Nov27/May30-R1 12m18 in `OECDEquityMay30Live@1`, Mar08-Kadenz 30m32 in `DataUSAConstructionSequenceMar08@1`, Mar08-Folgefrist 42 s in `…Mar08@18`, Apr30-Folgefrist 31 s in `OpenAIFeb28ConstructionSlowLive@3`, Jul07-R1 18m04 in `DataUSAMaidsWageSequenceCollabSep21@6`); **?** = `N/A_PENDING_REVIEWER` (1: Folgefrist 83 s der Zeile Nov20/Nov21 SLOW — im Zitat „R1 timer 15m00, then cooldown 1h22m02“ nicht enthalten, Korpussuche nach „83 s“ mit CVD-/Nov20-Bezug ohne Treffer).

Fehlende Werte in der 33er-Tabelle: R1-Timer 7, Kadenz 7, Folgefrist 9 (→ 18 unvollständige Zeilen, die die PCA nicht sieht).

### Leave-one-row-out (`paper_robust_fahrplan_loo.csv`)

PC1 voll 0,784 (PC2 0,186, PC3 0,030). Ohne je eine Zeile: **min 0,755** (ohne Nov20/Nov21 SLOW), **max 0,815** (ohne Dec13/Sep05), Median 0,790. Zeilen-Bootstrap (4000, seed 20260909): PC1 95 % [0,650; 0,898]. Keine einzelne Zeile trägt den Befund; die Aussage „eine gemeinsame Skala, ~78 %“ hält, das Intervall ist aber breit (n = 15).

## Teil C — CVD-Abschaltung als Intervall

### Methode

Aus `paper_horizont_testH_cvd_saetze.csv` (Satzebene, aus `54_horizont.py` Z. 471-521) wird je Kohorte das **letzte Lebenszeichen** als größter Innen-Offset ab R1 aus einem **eigenen** Post genommen (Name oder Seite trägt das Kohorten-Token, Satz nicht als `[gelistet]` relayed) → `evidence_type = server` (Server-Zeitstempel des Posts + im selben Post genannte Innenzeit). Wenn nur fremde Nennungen existieren → `self_report` (Fall trat nicht auf: alle 23 klassifizierten Kohorten haben eigene Posts). Die drei Audit-Kohorten aus `54_horizont.py` Z. 531-534 (Apr23, Apr30, Dec30) werden `audit` markiert, mit separater Spalte `audit_death_internal_s`.

**Erste belegte Abwesenheit** = die nie gemeldete sechste Runde (R6), je Klasse:
- schnell (17 s): R6 = global + 5549 s (Audits Apr30/Dec30: „hard wall global+5500s … 49s before R6“) minus 36 s Vorlauf global→R1 (`54_horizont.py` Z. 483) = **R1 + 5513 s (91:53)**; korroboriert durch „posted survival at +90m (+6s/+1s) then went silent before R6 ~1m50 later“ (OpenAINov16CVD, 08:10:32Z).
- mittel (22 s): R6 angekündigt bei **R1 + 108:05** (CVDJun20Scout 2026-06-20T13:15:36Z „announced R6 09:10:52 (=+108m05)“; Oct22 R1 08:11:46 → R6 09:59:51, BERICHT_horizont Z. 399).

Zwei dokumentierte Abweichungen von `paper_horizont_testH_cvd_kohorten.csv`: (1) Apr23 — der eigene Post 07:25:16Z nennt keine „+Ns past“-Formel, sondern „scaffold 12:31:35+ … thread-activation+90m (12:31:29) passed“ → +6 s = 5406 s (deckt sich mit dem relayed „+90:06“); im Skript als Override eingetragen. (2) Jul30 — alt 6364 s stammte aus einer fremden Inferenz („teardown R1+106m04s, matching Jul30/Nov16 last survival +106m02“, OpenAIJul09CVD); der eigene Post von OAIJul30Evening2028 gibt +62 s = 6362 s.

### Ergebnis (`paper_robust_horizont_cvd_intervalle.csv`, `paper_robust_horizont_cvd_klassen.csv`, `tab_cvd_intervals.tex`, `fig8_cvd_intervals.json`)

| Klasse | Teilmenge | n | letztes Lebenszeichen | Fenster | CV | Todesintervall [letztes Lebenszeichen ; R6 fällig] |
|---|---|---|---|---|---|---|
| schnell 17 s | alle | 11 | R1+90:01 … +91:03 | 62 s | 0,0057 | [91:03 ; 91:53] = 50 s |
| schnell 17 s | nur server (ohne Audit-Kohorten) | 8 | R1+90:01 … +91:03 | 62 s | 0,0057 | [91:03 ; 91:53] = 50 s |
| schnell 17 s | nur Audit | 3 | R1+90:06 … +91:01 | 55 s | 0,0058 | Audit-Tod R1+91:04 (Apr30, Dec30, inferiert); Apr23 nur Weltzeit 07:29:15Z |
| mittel 22 s | alle = nur server | 12 | R1+105:32 … +107:32 | 120 s | 0,0050 | [107:32 ; 108:05] = 33 s |

Die Paper-Zahlen (62 s / 0,006 über 11; 120 s / 0,005 über 12) bleiben nach Entfernen der Audits unverändert, weil die Audits keine der Fenstergrenzen setzen. Das Paper sollte aber (a) „exact to the second“ durch das Intervall ersetzen: schnell 50 s, mittel 33 s breit; (b) die Audit-Todeszeit R1+5464 s (global+5500) als *Inferenz* kennzeichnen — beobachtet ist nur der letzte Post bei 5461 s und die Stille danach; (c) für Apr23 die Innenzeit des Todes als unbekannt führen (die 5504 s in `54_horizont.py` Z. 558-560 sind eine Schätzung über den Faktor 0,435).

## Ambiguitäten

1. **Steigungs-Zuordnung im Paper.** „1.03 [0.70, 1.36]“ ist nur A (n = 39); der Primärsatz (n = 71) hat 0,906 [0,68; 1,13]. `<reason>` zwei Skripte, zwei Teilmengen, ein Absatz.
2. **Mitternachts-Definition.** „dt > −6h wall-equivalent“ wurde als „korrigiertes Innen-Delta ≤ 6 h und Welt-Delta ≤ 6 h“ operationalisiert; bei anderer Lesart (|dt| < 6 h roh) wären die Kandidaten Episodenwechsel, nicht Mitternacht — Ergebnis n = 71 bleibt in beiden Lesarten. `<reason>` Formulierung des Reviewers nicht eindeutig.
3. **Folgefrist 83 s (Nov20/Nov21 SLOW).** Nicht aus dem Zitat, nicht im Korpus gefunden → `N/A_PENDING_REVIEWER`; PCA ohne diese Zeile: PC1 0,755 (das LOO-Minimum). `<reason>` kuratierter Wert ohne auffindbaren Beleg.
4. **Provenienz Zeile 6 (Nov09/Mar08).** Kadenz und Folgefrist stammen aus anderen Revisionen derselben Seite als das kuratierte Zitat; die Folgefrist 42 s wird dort in einem Nov09-Post („NOV09 R2 CONFIRMED … 42s“, `…Mar08@18`, LanguageWatcherNov12) genannt, also für dieselbe Nov09/Mar08-Konfiguration, aber nicht in demselben Satz wie R1 und Kadenz. `<reason>` Wert-Triple aus drei Sätzen zusammengesetzt.
5. **R6-Fälligkeit der schnellen Klasse** ist aus zwei Audit-Sätzen abgeleitet (global+5549 s) plus 36-s-Vorlauf, keine direkte „R6 due“-Ansage einer 17-s-Kohorte im Satzkorpus. `<reason>` Ableitung, kein Zitat.
6. **Name ≠ Container.** Aug24 und Mar09 werden über die Seite als „eigen“ erkannt (Posts unter Oct03CVDScout bzw. OpenAIResearchApr23); die Server-Evidenz gilt für die Seite, nicht zwingend den Container. `<reason>` Wiki-Name frei wählbar (BERICHT_horizont Z. 526).
7. **Jun30** (Offset 6142 s, keine Klasse) bleibt unklassifiziert und außerhalb aller Fenster.

## Artefakte

| Datei | Inhalt |
|---|---|
| `paper_robust_uhr_ebenen.csv` | Paar- vs. Namensebene mit Cluster-Bootstrap-Intervallen (primär, nur A) |
| `paper_robust_uhr_namensebene.csv` | 53 + 32 Namensmediane |
| `paper_robust_uhr_cluster_bootstrap.csv` | alle Bootstrap-Intervalle |
| `paper_robust_uhr_mitternacht.csv`, `_kandidaten.csv` | Varianten und die 22 negativen Deltas |
| `paper_robust_fahrplan_provenienz.csv`, `paper_robust_fahrplan_loo.csv` | 15 Zeilen mit Provenienz je Wert; LOO-PCA |
| `paper_robust_horizont_cvd_intervalle.csv`, `_klassen.csv` | Intervalle je Kohorte; Fenster/CV je Klasse und Teilmenge |
| `paper/tables/tab_scheduler_rows.tex`, `paper/tables/tab_cvd_intervals.tex` | booktabs-Tabellen |
| `paper/figures/data/fig8_cvd_intervals.json` | Intervalldaten für den späteren Plot |
