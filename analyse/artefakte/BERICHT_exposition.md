# Exposition bei Ankunft — was auf der Seite stand und was im Änderungsstrom lag

Skript `analyse/scripts/66_exposition.py` (Seed 20260909), Log `artefakte/_paper_exposition.log`.
Ausgaben: `paper_exposition_index.parquet`, `paper_exposition_adoption_gesamt.csv`, `paper_exposition_adoption_6h.csv`, `paper_exposition_risikodifferenz.csv`, `paper_exposition_logit.csv`, `paper_exposition_kohorten.csv`, `paper_exposition_aktualitaet.csv`, `paper_exposition_kernzahlen.json`, `paper/tables/tab_exposure_adoption.tex`, `paper/tables/tab_exposure_recency.tex`, `paper/figures/data/fig10_exposure_adoption.json`.
Anlass: De Marzo, Albore, Garcia, *Copying explains the collective behavior of AI agents in the wild*, `arXiv:2609.09150` (8. September 2026) — dieselbe Flotte, modelliert als Abschreiben proportional zu dem, was sichtbar war.

**Der eine Satz, der über allem steht:** Dieses Paket sagt nichts darüber, was ein Agent *gelesen* hat. Es sagt, was **verfügbar** war. `data/events.jsonl` enthält 19.913 Ereignisse — 14.591 `save`, 5.217 `delete`, 4 `revert` und 101 `probe`; von den 101 Proben ist **keine einzige** erfolgreich (`success_observed == 0` in allen 101 Fällen, `log:6`). Die Leseschicht existiert im Abzug nicht. Jede Zahl unten ist eine **Obergrenze für Übertragung**, nie ein Beleg für Übertragung.

## `body` gegen `delta` — die Trennung, die dieses Paket überhaupt erst erlaubt

Ein Wiki speichert bei jeder Bearbeitung die ganze Seite. Wer `body` einem Autor zuschreibt, schreibt ihm den Text aller Vorgänger zu; genau dieser Fehler hat in einem frühen Durchlauf dieselbe Zahlenreihe unter fünf Namen fünfmal als unabhängigen Beleg gezählt. Für **Autorenschaft** ist `body` deshalb im gesamten Paket verboten und `delta` Pflicht. Für **Exposition** ist `body` der *Vorgängerversion* dagegen genau richtig — er ist der fremde Text, den der Ankommende vorfand.

In diesem Skript gilt strikt: alles, was jemandem *zugeschrieben* wird (`ad_*`), kommt aus seinem eigenen `delta`; alles, was jemandem *sichtbar* war (`exp_*`), kommt aus dem `body` der Vorgängerversion derselben Seite oder aus den `delta` fremder Versionen im Änderungsstrom.

## Methode

Zwei Kanäle, getrennt geführt (`66_exposition.py` Z. 263-277):

| Kanal | Definition | Anteil exponierter Erstversionen (Rundenmarker) |
|---|---|---|
| **Seitenkanal** (primär) | Merkmal steht im vollen Seitentext der unmittelbar vorhergehenden Version **derselben** Seite (`body` bei `seq−1`; leer bei Neuanlage) | 39,4 % |
| **Stromkanal** | Merkmal steht im `delta` einer der letzten *N* Versionen wikiweit, strikt vor dem Zeitstempel; *N* ∈ {30, 100, 300}, Hauptwert 100 wie De Marzo | 95,1 % (N = 100) |
| Vereinigung (De-Marzo-Definition) | Seitenkanal **oder** Stromkanal | 95,6 % |

Merkmalsregexe wörtlich aus `41_lernkurve.py` Z. 14-31 übernommen, nicht neu erfunden; `meldeformat` = Signatur + (Uhrenpaar ∨ Zeitstempel) + (Runde ∨ STATE/CONFIRMED ∨ *cohort*), wie dort Z. 34. Population = die 1.140 Namen der Koordinations-Population (`coordpop`), gemessen an ihrer **Erstversion** — dieselbe Population und dieselbe Einheit wie Fig. 3, damit die Kurven vergleichbar bleiben.

Sortierung stabil nach `(time, page_key, seq)`; gleiche Zeitstempel zählen in der Hauptdefinition **nicht** als „vorher" (Sensitivität `strom_N100_positionen` positionsbasiert: identische Zahlen). Kopierschleifenregel wörtlich aus `65_adoption_robust.py` Z. 122-148 übernommen und exakt reproduziert: A ∪ B′ = **1.897 Versionen (13,0 %)**, identisch mit `BERICHT_robust_adoption.md` (`log:14`).

### Zählungen je Filterstufe (Rundenmarker, Erstversionen der Koordinations-Population, n = 1.140)

| Variante | exponiert | exponiert & übernommen | exponiert & nicht übernommen | nicht exponiert & übernommen |
|---|---|---|---|---|
| Seitenkanal | 449 | 415 | 34 | **249** |
| Seitenkanal ohne die drei Infrastrukturseiten | 448 | 415 | 33 | 249 |
| Strom N = 30 | 1.067 | 655 | 412 | 9 |
| Strom N = 100 | 1.084 | 657 | 427 | 7 |
| Strom N = 300 | 1.095 | 664 | 431 | 0 |
| Strom N = 100 ohne Kopierschleife | 1.084 | 657 | 427 | 7 |
| Seite ∨ Strom N = 100 | 1.090 | 663 | 427 | 1 |

Der Stromkanal ist ab dem 16.06. 12:00 zu **98,8 %** gesättigt (Median: 55 % der letzten 100 Versionen tragen den Rundenmarker, `log:127`); Kopierschleife und Infrastrukturseiten herauszunehmen ändert daran nichts. Die drei meistbeschriebenen Seiten (Begrüßungs-, Start- und Testseite, 3.021 Versionen = 20,7 %) sind deshalb im Hauptwert **enthalten** und nur als Sensitivität ausgeschlossen: für den Seitenkanal ändern sie eine einzige Beobachtung, für den Stromkanal keine.

---

## Teil 1 — Exposition gegen Adoption

**Zitierbarer Satz:** Auf der Seite, auf die er schrieb, fand ein ankommender Name den Rundenmarker in 39,4 % der Fälle vor; wo er dort stand, übernahm ihn der Ankommende in 92,4 % seiner ersten Zeile, wo er fehlte, in 36,0 % (Risikodifferenz 56,4 Prozentpunkte, 95 % KI [52,1; 60,7], Fisher p < 10⁻¹⁵) — 249 der 664 Namen, die den Marker in ihrer ersten Zeile führten (37,5 %), hatten ihn auf ihrer Seite nirgends stehen.

**Der eigentliche Befund liegt in der dritten Reihe.** 93,6 % dieser 249 Namen (233) haben die Seite, auf die sie schrieben, im selben Zug **selbst angelegt** — sie kamen an, erzeugten eine leere Rendezvous-Seite und schrieben sofort im Koordinationsformat. Das ist dieselbe Population, die das Paper heute schon qualitativ beschreibt (180 Namen legen als allerersten Akt eine leere Rendezvous-Seite an). Für sie ist der Seitenkanal per Konstruktion leer, und die einzige verbleibende rekonstruierbare Quelle ist der Änderungsstrom — der zu diesem Zeitpunkt so gesättigt ist, dass er nichts mehr unterscheidet (248 der 249 sind dort „exponiert").

| Merkmal | Herkunft | auf der Seite (n) | dort übernommen | nicht auf der Seite (n) | dort übernommen | Risikodifferenz [95 % KI] | übernommen ohne Seitenquelle |
|---|---|---|---|---|---|---|---|
| Rundenmarker | erfunden | 449 | 92,4 % | 691 | 36,0 % | +56,4 [52,1; 60,7] | 249 von 664 (37,5 %) |
| *cohort* | erfunden | 520 | 59,6 % | 620 | 40,8 % | +18,8 [13,1; 24,5] | 253 von 563 (44,9 %) |
| Meldeformat | erfunden | 526 | 71,1 % | 614 | 43,3 % | +27,8 [22,3; 33,3] | 266 von 640 (41,6 %) |
| Signaturzeile | mitgebracht | 549 | 86,3 % | 591 | 54,8 % | +31,5 [26,6; 36,5] | 324 von 798 (40,6 %) |
| Bitte-Formel | mitgebracht | 518 | 59,7 % | 622 | 37,0 % | +22,7 [17,0; 28,4] | 230 von 539 (42,7 %) |

**Zitierbarer Satz zur Trennschärfe:** Der Anteil „übernommen ohne Seitenquelle" liegt bei den auf dem Wiki *erfundenen* Merkmalen (37,5 / 44,9 / 41,6 %) im selben Bereich wie bei den *mitgebrachten* (40,6 / 42,7 %) — die Exposition trennt die beiden Herkünfte also nicht, und die Kurve taugt als Obergrenze für Übertragung, nicht als Nachweis.

Logistisch, ab 16.06., mit Zeittrend und dem Stromkanal als **Intensität** statt als Schalter (`paper_exposition_logit.csv`): Seitenkanal OR 27,97 [17,89; 43,74] für den Rundenmarker, 1,96 [1,54; 2,50] für *cohort*, 3,23 [2,49; 4,20] für das Meldeformat; der Anteil des Merkmals in den letzten 100 Versionen trägt zusätzlich (OR je vollem Anteilsschritt 64,6 [28,0; 148,9] bzw. 10,7 [3,3; 34,4] bzw. 7,7 [3,9; 14,9]). Pseudo-R² 0,43 / 0,04 / 0,12 — beim Rundenmarker erklärt Sichtbarkeit viel, bei *cohort* fast nichts.

Abbildung: `paper/figures/fig10_exposure_adoption.pdf`, drei Reihen je Merkmal über 6-h-Fenster.

---

## Teil 2 — Die Zahl, die das Paper bisher nennt

**Zitierbarer Satz:** Die bisher berichteten 12,5 % „nachweisliches vorheriges Lesen" (143 der 1.140 koordinierenden Namen, die in ihrer ersten Zeile einen fremden CamelCase-Seitennamen ab zwölf Zeichen zitieren) sind keine untere Schranke für *Lesen*, sondern eine sehr enge untere Schranke für *belegte Textübernahme*; die rekonstruierte **Verfügbarkeit** desselben Materials liegt bei 39,4 % über den Seitenkanal und bei 95,6 % über die weiteste sinnvolle Definition (Seite oder letzte 100 Versionen) — die Lücke zwischen 12,5 % und 95,6 % ist genau der Bereich, den der fehlende Lesezugriff offenlässt.

Das erzeugende Skript der 12,5 % liegt nicht im Repo; die Zahl ist aus `paper_lernkurve_q2_inhaltlicher_lesebeweis.csv` reproduziert (143/1140 = 12,54 %, `log:8`) und bleibt als das stehen, was sie ist: eine Zitatspur, keine Leseschranke.

---

## Teil 3 — Expositionsvariable für die Fortschrittsregression

**Zitierbarer Satz:** Auf den Seiten, auf die eine Kohorte schrieb, lag bei ihrer Ankunft in 61,9 % der Fälle bereits eine fremde Rundenangabe und in 56,8 % eine Angabe oberhalb ihres eigenen später dokumentierten Standes — die Behandlungsvariable hat damit 317 behandelte Kohorten in 28 Aufgabenfamilien statt der acht selbstberichteten Fälle in vier Familien, und auch mit dieser Stärke bleibt die Fortschrittsregression ohne robusten positiven Effekt.

Konstruktion (`66_exposition.py` Teil C): je Kohorte alle Seiten, auf die sie schrieb; darauf alle Rundensätze aus `paper_prozess_rundensaetze_delta.csv` (erzeugt von `51_prozess.py` Z. 204) mit Zeitstempel **vor** der ersten Version der Kohorte und von einem Label einer **anderen** Kohorte. Daraus vier Größen: `exp_runde_max_vor` (höchste sichtbare Runde, exogen), `exp_runde_saetze_vor`, `exp_vorsprung_seiten`, `exp_vorsprung_b` (sichtbare Runde > eigener späterer Stand).

Ergebnis in `63_fortschritt_robust.py` (Tab. 3 und Robustheitstabelle), alle dortigen Varianten mitgelaufen:

| Prädiktor | roh (Spearman ρ / rank-biserial) | kontrolliert (OLS, Familien-FE, HC1) | BH q |
|---|---|---|---|
| Höchste sichtbare Runde bei Ankunft | ρ = 0,37 [0,29; 0,44], p = 3,4·10⁻¹⁸ | +0,07 [−0,01; 0,14] | 0,34 |
| Fremde Antwort voraus sichtbar | r = 0,08 [−0,11; 0,24] (317 behandelt) | −0,12 [−0,28; 0,03] | 0,34 |

Die rohe Assoziation ist stark und BH-signifikant, verschwindet aber unter Kontrolle von Schreibmenge, Lebensspanne und Aufgabenfamilie fast vollständig: wer viel und lange schrieb, sah viel und dokumentierte viel. In der Ordered-Logit- und in den vier Schwellenmodellen bleibt nichts Positives; im Leave-one-family-out ist keine der beiden Variablen in ≥ 95 % der 35 Läufe von null getrennt. Zwei Zellen zeigen ein **negatives** Vorzeichen mit KI ohne null (`exp_vorsprung_b`, Cluster-SE, n = 510 und n = 494; Schwellenmodell P(Runde ≥ 5)) — das ist Zensur, nicht Schaden: `exp_vorsprung_b` ist relativ zum eigenen späteren Stand definiert und deshalb bei niedrigem Stand fast immer wahr.

**Ambiguität, die man nicht wegrechnen kann:** `exp_vorsprung_b` ist per Definition an das Ergebnis gekoppelt und taugt nur als Nebenspezifikation. Die exogene Variable ist `exp_runde_max_vor`; sie ist die, die in den Text gehört.

---

## Teil 4 — Aktualität gegen aufgelaufene Beliebtheit

**Zitierbarer Satz:** Die Seitenwahl ist von **Aktualität** getrieben, nicht von Beliebtheit: die gewählte Seite war im Median vor 2,2 Minuten zuletzt bearbeitet worden, eine zufällig gezogene bestehende Seite vor 2.878 Minuten; 71,0 % aller Beiträge gingen auf eine Seite, auf der in den letzten zehn Minuten jemand geschrieben hatte, und im bedingten Logit sinkt die Wahlwahrscheinlichkeit je e-fachem Alter auf das 0,38-fache [0,37; 0,39].

Schätzer: bedingtes Logit über 9.995 Wahlsituationen (jede Version auf einer bereits bestehenden Seite) mit je 20 gezogenen Alternativen (McFadden-Stichprobe, konsistent), Prädiktoren log(1 + Minuten seit letzter Bearbeitung) und log(1 + bisherige Versionen); McFadden-R² 0,78.

Die Beliebtheitskurve reproduziert De Marzos Form: gegen eine Seite mit einer einzigen bisherigen Version steigt die Wahlwahrscheinlichkeit bei zwei Versionen um den Faktor **2,37** [2,18; 2,57] — De Marzo berichten ~2,3 — und flacht dann ab (3,66 → 5,40 → 6,91 → 7,71 in den Bins 3-5, 6-10, 11-25, 26-50, ohne die drei Infrastrukturseiten). Über 50 Versionen **kehrt sie sich um**: Faktor 3,15 [2,42; 4,09]. Mit den Infrastrukturseiten drin steht dort stattdessen 24,79 — die Begrüßungsseite allein besetzt diesen Bin, und ihre 2.327 Versionen sind eine Eigenschaft des Wikis, keine Wahlentscheidung der Flotte.

**Was das für den Schelling-Punkt bedeutet:** Aktualität erklärt einen erheblichen Teil davon, *auf welche bestehende Seite* geschrieben wurde. Sie erklärt nicht, wie eine Seite entsteht: 44,9 % der koordinierenden Namen schrieben ihre erste Zeile auf eine Seite, die sie selbst gerade angelegt hatten, und trafen dort trotzdem im selben Namensraum aufeinander. Der Aktualitätsbefund und das Fokuspunkt-Argument stehen nebeneinander, sie ersetzen sich nicht.

---

## Ambiguitätenliste

1. **Exposition ist keine Übertragung.** Ein Merkmal kann auf der Seite gestanden haben und trotzdem aus dem Prompt stammen. Alle Kurven sind Obergrenzen. `N/A_PENDING_REVIEWER` bleibt jede Aussage über tatsächliches Lesen.
2. **Der Stromkanal ist gesättigt und trägt deshalb keine Information.** Ab 16.06. 12:00 sind 98,8 % der Erstversionen im Sinne der De-Marzo-Definition „exponiert". Wer daraus Übertragung liest, liest Sättigung. Die Intensitätsvariante (Anteil der letzten 100 Versionen) ist der einzige informative Weg, den Strom zu benutzen.
3. **Der rekonstruierte Seitenzustand ist selbst eine Untergrenze.** 20.995 von 35.555 der Flotte zurechenbaren Speicherversuchen haben keine archivierte Version, 1.246 gelöschte Seiten haben keinen Inhalt. Was in einer nicht archivierten Zwischenversion stand, ist unsichtbar — auch für uns.
4. **`exp_vorsprung_b` ist endogen** (relativ zum eigenen späteren Stand definiert); das negative Vorzeichen in zwei Cluster-SE-Zellen ist Zensurartefakt, kein Effekt. Exogen ist nur `exp_runde_max_vor`.
5. **Die Kohortenzuordnung erbt alle Unschärfen von `51_prozess.py`:** 1.124 von 3.103 Namen tragen beide Schlüssel; Namen sind keine Container.
6. **Die Merkmalsregexe sind Heuristiken** mit gemessener Güte auf dem 400-Satz-Gold-Set (Ankunftserkennung Precision 0,99 / Recall 0,47); der Rundenmarker `[RG][1-9]` trifft auch Fließtext-Zufälle, was Exposition eher über- als unterschätzt.
7. **Die drei Infrastrukturseiten** bleiben im Hauptwert enthalten; Ausschluss ändert im Seitenkanal eine Beobachtung, im Stromkanal keine, im Beliebtheitsmodell den obersten Bin von 24,79 auf 3,15.
8. **Die 20 gezogenen Alternativen je Wahlsituation** sind uniform aus den zu diesem Zeitpunkt bestehenden Seiten gezogen; das ist konsistent, aber weniger effizient als der volle Alternativensatz, und die Standardfehler sind entsprechend konservativ zu lesen.
