# Robustheit der Fortschrittsregression — Effektgrößen, Ordinalmodelle, Zensur, Leave-one-family-out

**Frage.** Das Paper (main.tex, Tab. 3, Z. 321–344) behauptet, dass nach Kontrolle des Schreibvolumens
nichts den dokumentierten Fortschritt einer Kohorte (`max_runde_belegt`, ordinal 1–7) vorhersagt. Der
Reviewer verlangt: Effektgrößen mit 95-%-KI statt p-Werten, Familien-Fixeffekte und familien-geclusterte
Unsicherheit, ein Ordinalmodell mit Proportional-Odds-Prüfung, eine Zensur-Sensitivität, Leave-one-family-out,
Dedup-Varianten, BH-FDR über die Prädiktorfamilie und die Zukunftsantwort als exakten Permutationstest.
Die zulässige Schlussfolgerung ist **„keine robuste positive Assoziation mit dokumentiertem Fortschritt"**,
nie „Effekt ausgeschlossen".

**Analysecode:** `analyse/scripts/63_fortschritt_robust.py` (relative Pfade, `.venv/bin/python
scripts/63_fortschritt_robust.py`, Seed 20260909, Laufzeit ca. 80 s). Protokoll: `artefakte/_paper_robust_fortschritt.log`
(250 Zeilen, im Folgenden `log:NN`). Tabellen: `artefakte/paper_robust_fortschritt_{effekte,ordinal,zensur,dedup}.csv`,
`artefakte/paper_robust_lofo.csv`; LaTeX: `paper/tables/tab_progress.tex` (ersetzt Tab. 3) und
`paper/tables/tab_robustness_progress.tex` (nur `tabular`, booktabs, `\num`; kompiliert mit tectonic).

**Headline-Satz für das Paper:**
> Über alle Spezifikationen — HC1- und familien-geclusterte OLS mit Familien-Fixeffekt, Ordered Logit,
> Schwellen-Logits P(Runde ≥ k), Zensur-gefilterte Teilmengen, Leave-one-family-out über 35 Familien,
> Entfernung der Kopierziele der Zitatkaskade und Benjamini–Hochberg über zehn Prädiktoren — zeigt **kein
> Prädiktor eine robuste positive Assoziation mit dokumentiertem Fortschritt**. Der einzige Kandidat
> (`counterapi`, β = 0,19 SD [0,04; 0,35] unter Cluster-SE) überlebt weder die FDR-Korrektur (q = 0,13) noch
> das Ordinalmodell (KI schließt 0 ein) noch ein Schwellenmodell; die einzige Assoziation, die in fast jeder
> Spezifikation die Null ausschließt, ist **negativ** (Bittenquote, kompositionell). Die Zukunftsantwort
> (6 Kohorten) hat eine Permutations-Mittelwertdifferenz von −0,56 Runden [−1,46; 0,29], p = 0,27 — das KI ist
> breit und schließt einen Vorteil von bis zu +0,3 Runden nicht aus.

---

## 1. Datengrundlage und Filterstufen

| Stufe | n Kohorten | n Familien | Quelle |
|---|---|---|---|
| Rekonstruierte Kohorten gesamt (`paper_fortschritt_kohorten.csv`) | 907 | 37 | `log:1` |
| mit ≥ 1 Fortschrittsbeobachtung (`max_runde_belegt ≥ 1`) — **Basis** | 510 | 35 | `log:2` |
| davon mit ≥ 5 Versionen | 256 | 27 | `log:5` |
| davon **nicht** Kopierziel in der Zitatkaskade (Dedup i) | 494 | — | `log:132` |
| eine Kohorte je (Familie, Datum) (Dedup ii) | 510 (identisch) | — | `log:133` |
| mit Kadenz-Angabe (Zensur-Analyse) | 99 | — | `log:81` |
| mit fälliger Runde k bis zur letzten Version: k = 2 / 3 / 4 / 5 | 82 / 77 / 72 / 69 | — | `log:82-85` |

Verteilung des Ziels in der Basis: R1 17, R2 110, R3 134, R4 157, R5 91, R7 1 (`log:3`).

**Abweichung zum Paper:** main.tex Z. 139 spricht von „40 families"; die Kohortentabelle enthält 37
Familien (`log:1`), in der Basis 35. Die drei fehlenden Familien haben offenbar Labels, aber keine
Kohorte mit Datum + Familie. Leave-one-family-out läuft daher über 35, nicht 40 Familien. → Paper-Text anpassen
oder Zahl in 51_prozess.py nachprüfen (`N/A_PENDING_REVIEWER`, ob 40 Labels-Familien oder Kohorten-Familien meint).

## 2. Methode

Alle Schätzer in `63_fortschritt_robust.py`; Zeilenangaben beziehen sich auf diese Datei.

- **Prädiktoren (10):** Kadenz, R1-Frist, Antwortfrist (jeweils log Sekunden, z-standardisiert),
  `clock.wait`, `counterapi`, Umleitungsdienste, Blob-Ausbruch, Beobachtung auf fremder Seite, Zukunftsantwort
  (jeweils binär > 0), Bittenquote (z-standardisiert). Definition Z. 73–84.
- **Kontrollierte OLS** (Z. 100–123): `y_z ~ x + log(n_deltas) + log(lebensspanne_h + 1 s) + C(Familie)`;
  Familien mit < 5 Kohorten in der jeweiligen Teilmenge werden zu „other" zusammengelegt (Z. 93–96).
  β ist in SD-Einheiten des Ziels (kontinuierlich: je SD des Prädiktors; binär: Differenz ja/nein). SE einmal HC1,
  einmal Cluster nach Familie. **Schutz:** Liegen alle behandelten Kohorten eines binären Prädiktors in einer
  einzigen Familie, ist die Cluster-SE per Konstruktion degeneriert und wird nicht berichtet (Z. 117–120).
- **Roh-Effekte:** Spearman ρ mit Fisher-z-KI (Z. 125–132); Rank-biserial r mit 2000-fach Bootstrap-KI, einmal
  zeilenweise, einmal als Cluster-Bootstrap über Familien (Z. 143–165).
- **Zukunftsantwort:** Permutationstest der Mittelwertdifferenz; C(510, 6) ≈ 2,4·10¹³ Kombinationen > 100 000,
  daher Monte Carlo mit 100 000 Permutationen; Permutations-KI durch Inversion des Shift-Tests auf einem
  0,05-Runden-Gitter mit je 20 000 Permutationen (Z. 168–211).
- **Ordered Logit** (statsmodels `OrderedModel`, logit) mit denselben Kontrollen und Familien-Dummies
  (Z. 249–265); **Schwellen-Logits** P(Runde ≥ k), k = 2..5, Familien ohne Zielvarianz fallen heraus
  (FE-Logit-Praxis, Z. 267–289). Schätzungen mit SE > 10 (Quasi-Separation) werden verworfen (Z. 296–299;
  10 von 95 Modellen, `log:6`). **PO-Prüfung:** Spannweite der Schwellenkoeffizienten und paarweiser Wald-z;
  PO gilt als verletzt bei max |z| > 1,96 (Z. 300–310).
- **Zensur** (Z. 324–367): `due_k = erste_version + R1 + (k−1)·Kadenz`; R1 fehlt bei 74 der 99 Kadenz-Kohorten
  und wird durch den Familienmedian, sonst Gesamtmedian (532 s) ersetzt (`log:81`). Behalten werden Kohorten mit
  `letzte_version ≥ due_k`; Schwellen-Logit wie oben, mit Mindestfallzahlen (≥ 5 je Zielklasse, binäre
  Prädiktoren ≥ 3 behandelte Kohorten in ≥ 2 Familien, Z. 344–347).
- **LOFO** (Z. 369–407): jede der 35 Familien einmal weggelassen; für kontrollierte OLS (Cluster-SE), Spearman
  und Rank-biserial: min/max β, Anteil gleiches Vorzeichen, Anteil KI ohne 0.
- **Dedup** (Z. 409–419): (i) Kopierziele (`kopierer_cohort` in `paper_prozess_zitatkaskade_kopien.csv`, 33
  Kohorten, 16 davon in der Basis) entfernt; (ii) `(aufgabenfamilie, kohorte)` ist bereits eindeutig
  (0 Duplikate, `cohort_key = Familie|Datum`), Variante identisch mit Basis.
- **BH-FDR** je Modell × Teilmenge × Variante über die Prädiktorfamilie (Z. 236–243).

## 3. Kernzahlen (Basis n = 510)

Kontrollierte OLS mit Familien-FE, Cluster-SE (`paper_robust_fortschritt_effekte.csv`, `log:175-211`):

| Prädiktor | n | β [95 % KI] | q_BH | LOFO: Vorzeichen / KI∌0 |
|---|---|---|---|---|
| Kadenz (log s) | 99 | −0,07 [−0,29; 0,15] | 0,91 | 1,00 / 0,00 |
| R1-Frist (log s) | 68 | −0,10 [−0,20; 0,01] | 0,24 | 1,00 / 0,14 |
| Antwortfrist (log s) | 217 | 0,02 [−0,16; 0,21] | 0,92 | 0,94 / 0,00 |
| `clock.wait` (98 ja) | 510 | 0,04 [−0,11; 0,19] | 0,91 | 0,97 / 0,00 |
| `counterapi` (81 ja) | 510 | **0,19 [0,04; 0,35]** | 0,13 | 1,00 / 0,97 |
| Umleitung (7 ja) | 510 | −0,07 [−0,79; 0,65] | 0,92 | 0,94 / 0,00 |
| Blob-Ausbruch (9 ja, **1 Familie**) | 510 | nicht schätzbar (Cluster degeneriert); HC1: 0,14 [−0,55; 0,83] | — | — |
| Beobachtung fremde Seite (354 ja) | 510 | 0,01 [−0,11; 0,12] | 0,92 | 0,69 / 0,00 |
| Bittenquote | 510 | **−0,10 [−0,19; −0,00]** | 0,20 | 1,00 / 0,74 |
| Zukunftsantwort (6 ja, 4 Familien) | 510 | −0,16 [−0,76; 0,44] | 0,91 | 0,97 / 0,00 |

**Was die Null ausschließt — und wo es kippt:**

- `counterapi`: KI ohne 0 unter HC1 (0,19 [0,00; 0,38]), Cluster-SE, im ≥5-Versionen-Subset
  (0,24 [0,01; 0,46]) und ohne Kopierziele (0,14 [0,00; 0,29]); in 97 % der LOFO-Läufe. **Aber:** q_BH = 0,13
  (Cluster) bzw. 0,24 (HC1); Cluster-Bootstrap des Roh-Effekts r = 0,14 [−0,03; 0,35] schließt 0 ein;
  Ordered Logit 0,50 [−0,02; 1,01]; kein Schwellenmodell mit KI ohne 0 (`log:30`: ≥3: 0,76 [−0,02; 1,54]).
  Das ist ein Kandidat mit konsistentem Vorzeichen, aber ohne Robustheit gegen Mehrfachtest und Modellwahl.
- Bittenquote: negativ, KI ohne 0 in HC1, Cluster, Spearman (−0,14 [−0,22; −0,05], q = 0,007), Ordered Logit
  (−0,26 [−0,45; −0,08], q = 0,05), Schwelle ≥4 (−0,39 [−0,64; −0,14], q = 0,02) und ≥5; LOFO 74 % (Cluster)
  bzw. 97 % (Spearman). Die Größe ist kompositionell (Bitten verdrängen Beobachtungen im selben Text) und wird
  im Paper bereits so eingeordnet.
- Blob-Ausbruch: alle 9 Kohorten liegen in **einer** Familie (`log:4`); der scheinbar enge Cluster-KI aus dem
  ersten Lauf war ein Artefakt eines einzigen effektiven Clusters und ist bewusst entfernt. Roh: r = −0,25.
- Die drei Zeitparameter: roh negativ mit KI ohne 0 (Spearman), kontrolliert mit Familien-FE nahe 0 — die
  Roh-Korrelation ist Familienzugehörigkeit.

**Ordered Logit / PO** (`paper_robust_fortschritt_ordinal.csv`, `log:8-79`, Ordered-Logit-Zeilen `log:10,15,20,…`): alle 20 Modelle konvergiert; PO
in keinem Fall verletzt nach Wald-Kriterium (max |z| = 1,81 bei Blob, ansonsten < 1,7), der Ordered Logit
bleibt primär. Einziger Prädiktor mit KI ohne 0: Bittenquote (negativ). Spannweiten der Schwellenkoeffizienten
sind für die seltenen Binärprädiktoren riesig (Blob 16,8; Umleitung 16,8; Zukunft 10,8), weil einzelne
Schwellen quasi-separiert sind — dort sagt das Schwellenmodell nichts.

**Zensur** (`paper_robust_fortschritt_zensur.csv`, `log:81-109`): Nur 99 Kohorten haben eine Kadenz; 82/77/72/69
überleben den Fälligkeitsfilter für k = 2..5. Der Anteil erreichter Runden steigt durch den Filter nur leicht
(k = 4: 0,45 → 0,51; k = 5: 0,19 → 0,23), d. h. **Zensur erklärt die Rohsignale nicht** — die meisten
Kohorten hatten Zeit für die Runde und haben sie trotzdem nicht dokumentiert. In den gefilterten
Schwellen-Logits schließt nur die Bittenquote bei k = 4 die Null aus (−0,80 [−1,49; −0,11]); `counterapi` bei
k = 5: 2,39 [−0,36; 5,15]. k = 2 ist nicht schätzbar (81 von 82 positiv).

**Dedup** (`paper_robust_fortschritt_dedup.csv`, `log:132-171`): ohne die 16 Kopierziele ändert sich kein
Vorzeichen; `counterapi` 0,14 [0,00; 0,29], Bittenquote −0,11 [−0,20; −0,01]. Variante (ii) ist identisch.

**Zukunftsantwort** (`log:211`, `log:248`, `log:171`): Δ = −0,56 Runden [−1,46; 0,29], p = 0,27 (MC 100 000);
≥5 Versionen: −0,25 [−1,20; 0,70], p = 0,69; ohne Kopierziele: −0,58 [−1,48; 0,32], p = 0,27. Mittelwert 2,83
(6 Empfänger) vs. 3,39 (504 andere).

## 4. Empfohlene Formulierung im Paper

Tab. 3 durch `tab_progress.tex` ersetzen; Caption-Hinweis: „† treated cohorts fall in fewer than five task
families (blob egress: one family; future answer: four); family-clustered standard errors are not reported
where they would rest on a single cluster." Text: „nothing predicts" → „no predictor shows a robust positive
association with documented progress (Table 3, Appendix Table X): the one candidate, `counterapi` (β = 0.19 SD
[0.04, 0.35]), does not survive false-discovery control (q = 0.13), the ordinal model, or any threshold model;
the only association stable across specifications is the negative, compositional request rate."

## 5. Unschärfen (nicht auflösbar aus den Daten)

1. **Familienzahl 40 vs. 37/35** (§1) — Paper-Text oder Zählweise klären.
2. **Zensur in Innen- vs. Außenzeit:** `due_k` addiert Fristsekunden (Innenuhr) auf reale Zeitstempel; bei
   Uhrdehnung (Faktor 1–19, `BERICHT_uhr_auslastung.md`) ist die reale Fälligkeit später als angesetzt. Der
   Filter ist damit **zu großzügig** (behält zu viele Kohorten), was den Befund „Zensur erklärt es nicht" in
   Richtung konservativ verschiebt; eine Dehnungskorrektur je Kohorte gibt es nicht.
3. **R1-Imputation** bei 74 von 99 Kadenz-Kohorten (Median 532 s gegenüber Kadenzen von ~1 000–7 500 s) — Einfluss
   auf `due_k` klein, aber nicht geprüft.
4. **Cluster-Bootstrap mit 35 Familien, davon 6 mit ≥ 40 Kohorten:** die Perzentil-KI sind bei so schiefer
   Clustergröße eher zu schmal; BCa nicht gerechnet.
5. **Permutations-KI** ist ein Shift-Modell-KI (Annahme: additiver Effekt), Gitterauflösung 0,05 Runden.
6. **Ordered Logit mit ~20 Familien-Dummies bei n = 68–99** (Zeitparameter): schwach identifiziert; die KI sind
   entsprechend breit und sollten nicht als Nullbeleg gelesen werden.
7. `max_runde_belegt = 7` (1 Kohorte) bleibt als eigene Kategorie im Ordered Logit; Zusammenlegung mit 5 wurde
   nicht getestet.
