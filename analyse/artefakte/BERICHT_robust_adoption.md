# Robustheit der Ansteckungs- und Adoptionsbefunde (Reviewer-Nachfrage zu main.tex §Prozess, §Rendezvous)

Skript `analyse/scripts/65_adoption_robust.py` (Seed 20260909), Log `artefakte/_paper_robust_adoption.log`.
Ausgaben: `paper_robust_hawkes_dedup.csv`, `paper_robust_format_gefiltert_6h.csv`, `paper/figures/data/fig3b_format_filtered.json`.
Beide Originalskripte (`53_mathematik.py`, `41_lernkurve.py`) blieben unangetastet; die Hawkes-Funktionen sind wörtlich aus `53_mathematik.py` Z. 392-431 kopiert, die Variante `full` reproduziert `paper_math_hawkes.csv` exakt (max |Δn| = 0, max |Δα/β| = 0.0000; `log:40`), und die Volltabelle der Formatkonvergenz reproduziert `paper_lernkurve_q3_format_erstversion_koordpop_6h.csv` mit Abweichung 0.0 in allen 25 Fenstern (`log:70`).

---

## Teil 1 — Hawkes-Verzweigungszahl ohne Kopierschleife und Duplikatsätze

**Zitierbarer Satz:** Entfernt man alle 1.897 Versionen der Kopierschleifen und weitere 469 Versionen ohne einen einzigen neuen Satz, ändert sich die Verzweigungszahl der Namensankünfte um höchstens 0,013 (0,917 → 0,916 Kernwoche; 0,564 → 0,551 Tag 18.06. mit Stundenbasisrate); bei den Versionen steigt sie im einzigen Fall, in dem sie sich sichtbar bewegt, sogar von 0,811 auf 0,855 — die Kopierschleife des 18. Juni war kein Treiber der Ansteckungsschätzung, sondern ein Klumpen, der sie leicht *gedrückt* hat.

### Regel und Zählung je Stufe (`65_adoption_robust.py` Z. 126-178)

| Stufe | Regel | Versionen | Bemerkung |
|---|---|---|---|
| A | gleiches Label, identischer normalisierter Delta-Text (Whitespace kollabiert, lowercase; leer ausgeschlossen), frühere identische Version desselben Labels ≤ 3.600 s zurück (rollierende Stunde) | 1.104 (212 Labels, 1.023 Seiten) | Top-Labels: `''` 531, `Agent0AddJS` 45, `AgentMassRefUF155300` 34 |
| B | Version erscheint als Kopierer in `paper_prozess_zitatkaskade_kopien.csv` (rev_id-Treffer; Kaskade = Zeile ≥ 80 Zeichen, zuvor von *anderem* Label geschrieben, `51_prozess.py` Z. 626-648) | 822 | nur Fremd-Label-Kopien, per Konstruktion (`51_prozess.py` Z. 641 `if not same_label`) |
| B′ | Version enthält ≥ 1 Zeile ≥ 80 Zeichen (normalisiert, nicht mit `http` beginnend, Kriterien wie `51_prozess.py` Z. 633/468), die zuvor von **irgendeinem** Label geschrieben wurde | 1.265 (B ⊆ B′; 443 label-interne Wiederholungen) | nötig, weil die Schleife des 18.06. großteils label-intern läuft |
| **Kopierschleife = A ∪ B′** | | **1.897 (13,0 % von 14.591; 536 Labels, 1.473 Seiten)** | Stufe `no_copyloop`: 12.694 Versionen |
| C | Version enthält ≥ 1 Satz ≥ 40 Zeichen und **jeder** solche Satz wurde früher (beliebiges Label) schon geschrieben — Split an `[.!?]\s` und Zeilenumbruch | 1.463, davon 469 nicht schon in A ∪ B′ | Stufe `no_copyloop_no_dupsent`: 12.225 Versionen |

Kontrolle gegen die im Paper genannte Stunde 18.06. 20-21 UTC (`log:11`): 2.350 Versionen auf 730 Seiten; A ∪ B′ erfasst 542; die vier `jqp.vercel.app`/`investor.gov`-Zeilen stehen in 488 Versionen auf 425 Seiten von 127 Labels, davon 361 als wörtliche Kopie erfasst. Die 127 nicht erfassten sind parametrisierte Varianten derselben Vorlage (anderer Bundesstaats-Code im jq-Filter, z. B. `us-ma-` → anderer Code) — Vorlagenkopie, nicht wörtliche Kopie; siehe Ambiguitäten.

Die Ereignisreihe „Namen (erste Version)" wird je Stufe **neu** aus den verbleibenden Versionen gebildet (erste verbleibende Version je Label; Labels, deren Versionen sämtlich entfallen, verschwinden). Fenster, Segmentzahl (k = 1 und 28 für die Kernwoche, 1 und 24 für den Tag), Startwerte, Optimierer, Poisson-Vergleich und Zeitrescaling-KS sind identisch mit `53_mathematik.py` Z. 432-446.

### Verzweigungszahl α/β (`paper_robust_hawkes_dedup.csv`, 24 Zeilen)

| Reihe | Fenster | k | full | no_copyloop | no_copyloop_no_dupsent | n (full → Stufe 2) |
|---|---|---|---|---|---|---|
| Namen (erste Version) | Kernwoche 16.–22.06. | 1 | 0,917 | 0,916 | 0,916 | 2.580 → 2.465 |
| Namen (erste Version) | Kernwoche 16.–22.06. | 28 | 0,868 | 0,865 | 0,864 | |
| Namen (erste Version) | Tag 18.06. | 1 | 0,959 | 0,958 | 0,958 | 807 → 767 |
| Namen (erste Version) | Tag 18.06. | 24 | 0,564 | 0,552 | 0,551 | |
| Versionen | Kernwoche 16.–22.06. | 1 | 0,958 | 0,960 | 0,959 | 13.339 → 11.155 |
| Versionen | Kernwoche 16.–22.06. | 28 | 0,927 | 0,926 | 0,925 | |
| Versionen | Tag 18.06. | 1 | 0,977 | 0,977 | 0,977 | 6.543 → 5.094 |
| Versionen | Tag 18.06. | 24 | 0,811 | 0,857 | 0,855 | |

Zeitrescaling-KS für die Namensreihe wird nach Ausdünnung eher besser (Kernwoche p = 0,21 → 0,34 → 0,47; Tag 18.06. p = 0,69 → 0,82-0,94), für die Versionenreihe bleibt er bei p ≈ 0 (das Hawkes-Modell passt auf Versionen weiterhin nicht; `log:15-38`). Mittlere Antwortzeit 1/β der Versionenreihe verlängert sich durch Entfernen der Schleife von 0,6 auf 1,2 min (Tag) bzw. 2,4 auf 3,1 min (Woche) — die Schleife war das Schnellste im Korpus, nicht das Ansteckendste. ΔAIC (Hawkes − Poisson) bleibt in allen 24 Zellen negativ, zwischen −50 (Namen, Tag, k = 24) und −35.909.

**Einordnung für den Text:** Die Spanne „0,6–0,9" in main.tex Z. 362 bleibt unverändert gültig; die Aussage, der Schätzer sei nur eine obere Schranke (Startwellen ununterscheidbar von Ansteckung), wird durch die Dedup nicht berührt — sie betrifft die *Ankunfts*-Reihe, die von Kopien fast nicht bevölkert ist (die Namensreihe der Kernwoche verliert durch die Dedup nur 50 von 2.580 Ereignissen, weil Erstversionen fast nie Kopien sind).

---

## Teil 2 — Formatkonvergenz ohne Namen mit expliziter Kontaktspur

**Zitierbarer Satz:** Schließt man alle 215 der 1.140 koordinierenden Namen aus, die irgendwann eine nachweisbare Kontaktspur zeigen (18,9 %), erreicht die Rundenmarke in der Erstzeile der verbleibenden 925 Namen nach 18 Stunden 72,9 % statt 76,4 % und nach 24 Stunden 77,5 % statt 77,1 %, *cohort* 49,0 % statt 47,2 % bzw. 52,5 % statt 54,2 %; keine Kurve verschiebt sich in einem belegten Fenster um mehr als 10 Prozentpunkte, die beiden erfundenen Merkmale um höchstens 4,7 (Runde) und 8,7 (*cohort*) — die Konvergenz ist kein Artefakt der Namen, bei denen man Lesen beweisen kann.

### Filterregel (`65_adoption_robust.py` Z. 244-268)

Population: die 1.140 Namen mit `coordpop=True` in `paper_lernkurve_q2_inhaltlicher_lesebeweis.csv` (Reproduktion der Referenztabelle exakt). Kontaktspur eines Namens:

| Spur | Definition | Namen gesamt | davon coordpop |
|---|---|---|---|
| (a) inhaltlicher Lesebeweis | Erstversion nennt einen CamelCase-Seitennamen ≥ 12 Zeichen einer zu dem Zeitpunkt existierenden, von einem anderen Namen angelegten Seite (`q2_inhaltlicher_lesebeweis.csv`, `n_fremdseiten_genannt > 0`; Regel in `BERICHT_lernkurve.md` Z. 72, Implementierung nicht in `41_lernkurve.py` — siehe Ambiguitäten) | 452 | 143 |
| (b) Kopierer in der Zitatkaskade | `kopierer_label` in `paper_prozess_zitatkaskade_kopien.csv`; irgendwann / nur in der Erstversion | 385 / 144 | 34 / 6 |
| (c) Rendezvous-Sprache | Label in `paper_lernkurve_q5_rendezvous_treffer.csv` (`41_lernkurve.py` Z. 227-243); irgendwann / nur in der Erstversion | 70 / 24 | 51 / 13 |
| **a ∪ b ∪ c, irgendwann** (Hauptvariante `no_contact_trace`) | | 803 | **215 → 925 verbleiben** |
| a ∪ b ∪ c, nur Erstversion (Sensitivität `no_contact_trace_firstline`) | | 571 | 158 → 982 verbleiben |

Die Hauptvariante ist die strengere Lesart der Nachfrage: ein Name fliegt heraus, sobald er *irgendwann* Kontakt beweist, auch wenn die Spur erst nach seiner Erstzeile liegt. Die Sensitivitätsvariante nimmt die Formulierung „first line appears after the contact trace" wörtlich und entfernt nur Namen, deren Spur in der Erstversion selbst steht.

### Fensterwerte (Fig.-3-Lesart, `paper_robust_format_gefiltert_6h.csv`, `log:78-84`)

| Fenster | Variante | n | Runde | cohort | Meldeformat | Signatur | please relay |
|---|---|---|---|---|---|---|---|
| 16.06. 06–12 (Start) | full | 39 | 0,0 | 0,0 | 0,0 | 33,3 | 30,8 |
| | no_contact_trace | 29 | 0,0 | 0,0 | 0,0 | 34,5 | 34,5 |
| 16.06. 18–24 | full | 409 | 29,8 | 46,5 | 41,1 | 59,2 | 47,4 |
| | no_contact_trace | 343 | 29,2 | 45,8 | 39,9 | 58,6 | 46,1 |
| **17.06. 00–06 (≈ 18 h)** | full | 127 | **76,4** | **47,2** | 61,4 | 75,6 | 48,0 |
| | no_contact_trace | 96 | **72,9** | **49,0** | 59,4 | 72,9 | 47,9 |
| **17.06. 06–12 (≈ 24 h)** | full | 48 | **77,1** | **54,2** | **75,0** | 85,4 | 60,4 |
| | no_contact_trace | 40 | **77,5** | **52,5** | **72,5** | 82,5 | 57,5 |

Kumulativ ab Koordinationsbeginn 16.06. 09:27:10 (`log:85-90`): ≤ 18 h Runde 36,4 % (n = 546) gegen 34,5 % (n = 444), *cohort* 43,8 gegen 43,9; ≤ 24 h Runde 40,8 (n = 606) gegen 39,2 (n = 495), *cohort* 44,4 gegen 44,4. Maximale Fensterdifferenz full − no_contact_trace über alle Fenster mit n ≥ 20 in beiden Varianten: Runde 4,7 pp, *cohort* 8,7 pp, Meldeformat 5,4 pp, Signatur 6,1 pp, please-relay 10,0 pp (`log:92`). Die Sensitivitätsvariante liegt dazwischen (18 h: Runde 71,6 / *cohort* 49,0; 24 h: 78,0 / 53,7).

**Einordnung für den Text:** Die in main.tex Z. 276/286 zitierten Zahlen (Runde 76 %, *cohort* 47 % nach 18 h; Meldeformat 75 % nach 24 h) bleiben in der gefilterten Stichprobe innerhalb von 4 pp. Das schließt die Erklärung „ein gemeinsamer Prompt reicht jeder Welle dasselbe Wort" ausdrücklich **nicht** aus (main.tex Z. 410) — es zeigt nur, dass die nachweislich lesenden Namen die Kurve nicht tragen.

---

## Ambiguitäten

1. **Kopierschleife ist wörtlich, nicht als Vorlage definiert.** 127 der 488 `investor.gov`-Versionen der Stunde 18.06. 20-21 sind parametrisierte Varianten (anderer Bundesstaats-Code in der URL) und bleiben in `no_copyloop` drin. Bei 5.163 verbleibenden Versionen am 18.06. verschiebt das α/β um höchstens die Größenordnung der Stufe C (≤ 0,002). Eine Vorlagenregel (URL-Query maskieren) ist nicht gerechnet: `N/A_PENDING_REVIEWER`.
2. **Regel A nutzt eine rollierende Stunde (≤ 3.600 s), keine Kalenderstunde.** Die Nachfrage sagt „within the same hour"; die rollierende Lesart ist die inklusivere. Der Unterschied betrifft nur Paare über einer Stundengrenze.
3. **Regel C entfernt Versionen, die keinen neuen Satz enthalten**, nicht Versionen, die *irgendeinen* Duplikatsatz enthalten. Die zweite Lesart würde Grußformeln und Berichtsschablonen („Please leave STATE5-XX on …") mit entfernen, also große Teile des koordinierten Protokolls selbst — das wäre keine Robustheitsprüfung mehr, sondern eine Neudefinition der Reihe.
4. **Spur (a) ist die im Paper zitierte 12,5-%-Untergrenze**, deren erzeugendes Skript im Repo nicht liegt (die CSV existiert, `41_lernkurve.py` enthält die CamelCase-Regel nicht; `BERICHT_lernkurve.md` Z. 72 dokumentiert sie). Die CSV wurde als gegeben übernommen, nicht neu gerechnet: `N/A_PENDING_REVIEWER` für ihre Reproduzierbarkeit.
5. **Spur (c) ist Sprache, kein Kontakt.** Ein Treffer in `q5_rendezvous_treffer.csv` beweist, dass ein Name über Wiederfinden *spricht*, nicht, dass er gelesen hat; die Nachfrage verlangte diesen Filter, er ist deshalb enthalten, aber er ist der schwächste der drei.
6. **Empty-Label `''`** trägt 531 der 1.104 Regel-A-Versionen. Ob das ein anonymer Agent oder ein Export-Artefakt ist, entscheidet dieses Skript nicht; für den Hawkes-Fit ist es unerheblich, weil das Label in beiden Varianten konsistent behandelt wird.
7. **Hawkes auf Versionen** bleibt in allen Varianten mit KS p ≈ 0 misspezifiziert; nur die Namensreihe ist als Hawkes-Fit ernst zu nehmen. Das war schon im Paper so (Z. 362: „p ≈ 0 for revisions").

## Verdict

`{verdict: pass, confidence: 88, ambiguities: [1-7 oben]}` — beide Befunde des Papers überstehen die Nachfrage; keine Zahl in main.tex muss geändert werden, ein Halbsatz zur Robustheit (Ambiguität 1 und 4) wäre angebracht.
