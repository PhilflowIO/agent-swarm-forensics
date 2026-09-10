# Visualisierungsplan für „Die Mechanik des Schwarms"

Stand: 8. September 2026 · Bibliothek: Apache ECharts · Datenbasis: `analyse/artefakte/*.csv` (Stand dieses Laufs) · Befunde: `MECHANIK.md`

Maschinenlesbare Kurzfassung: `paper_visualisierungsplan.csv`. Options-Beispiele für die heiklen Typen: `viz_beispiele/*.json`.

---

## 0. Wie dieser Plan belegt ist

Die ECharts-Website liefert ihre Options-Referenz als JavaScript-Anwendung; über den Seiten-Crawler kommt dort nichts zurück. Die Referenz ist aber als Markdown-Spiegel unter `https://echarts.apache.org/en/llms-documents/` veröffentlicht (Index: `https://echarts.apache.org/en/llms.txt`). Alle Belege unten wurden aus diesem Spiegel gelesen; die zitierten Doku-URLs sind die kanonischen Anker der Website (`option.html#…`), die auf denselben Text zeigen. Zusätzlich gelesen: die Beispielgalerie (`https://echarts.apache.org/examples/en/index.html`), das Changelog, die API-Seite und das Handbuch-Kapitel „ECharts 6 New Features".

Was nicht aus der Doku belegbar war, steht als `N/A_PENDING_REVIEWER`. Das Ref-Werkzeug hatte keine Credits mehr und lieferte nichts; die Doku-Belege stammen ausschließlich aus Crawl4AI-Abrufen, Exa-Suche diente nur für Beispiel-Fundstellen (Konfidenzband, Custom-Series-Repo).

**Aktuelle Hauptversion: 6.** Changelog-Seite: `v6.1.0 2026-05-18`, davor `v6.0.0 2025-07-30` (`https://echarts.apache.org/en/changelog.html`). npm zeigt `6.1.0` als aktuell, GitHub-Release `6.1.0` vom 19.05.2026. Alles, was unten mit „seit v6.0.0" markiert ist, setzt diese Hauptversion voraus.

---

## 1. Inventar der Serientypen

Die Übersicht `option.md` führt genau diese Serientypen als `## series-*`-Abschnitte auf (Beleg: `https://echarts.apache.org/en/option.html#series`): line, bar, pie, scatter, effectScatter, radar, tree, treemap, sunburst, boxplot, candlestick, heatmap, map, parallel, lines, graph, sankey, funnel, gauge, pictorialBar, themeRiver, chord (seit v6.0.0), custom. Alle in der Aufgabe genannten Namen existieren; **gestrichen wurde nichts**, ergänzt wurden pie, map, funnel und chord. „calendar" ist kein Serientyp, sondern ein Koordinatensystem (siehe unten).

| Typ | Wofür | Erwartete Datenform (Doku) |
|---|---|---|
| `line` | Trend über eine geordnete Achse; mit `areaStyle` Flächendiagramm, mit `step` Treppe | zweidimensionales Array `[[x, y, …], …]` oder Werteliste zu einer Kategorieachse (`#series-line.data`) |
| `bar` | Vergleich diskreter Größen; `stack` für Stapel | wie line, nur in grid/polar (`#series-bar`) |
| `pie` | Anteile; Doku empfiehlt bar, wenn es um Unterschiede statt Anteile geht | `[{name, value}]` |
| `scatter` | Punkte in zwei Wertdimensionen, weitere Dimensionen über `visualMap`/`symbolSize`-Callback | `[[x, y, dim2, …], …]` (`#series-scatter.data`) |
| `effectScatter` | scatter mit Wellenanimation zur Hervorhebung einzelner Punkte | wie scatter |
| `radar` | mehrere Variablen je Objekt auf Speichen | `[{value:[v1…vn], name}]` mit `radar.indicator` |
| `tree` | Hierarchie als Baum | ein Wurzelobjekt mit `children` |
| `treemap` | Hierarchie als Flächen, betont große Knoten | Wald: Array von `{value, children}` |
| `sunburst` | Hierarchie als Ringe | baumförmig `[{name, value, children}]` |
| `boxplot` | Verteilungen über Quartile, mehrere Gruppen nebeneinander | je Kasten `[min, Q1, median, Q3, max]` — **ECharts rechnet die Statistik nicht selbst** (`#series-boxplot.data`) |
| `candlestick` | Finanzkerzen | je Kerze `[open, close, lowest, highest]` |
| `heatmap` | Wert als Farbe in Zelle; **muss mit `visualMap` kombiniert werden** | `[[dimX, dimY, value], …]` auf grid, geo oder calendar (`#series-heatmap`) |
| `map` | Choroplethen | Regionen per `name` mit registrierter Karte |
| `parallel` | hochdimensionale Zeilen als Linienzüge über Parallelachsen | je Zeile ein Wertevektor über `parallelAxis` |
| `lines` | Von-Nach-Linien (Routen); Doku: Nachfolger des alten `markLine`-Migrationseffekts | `data[i].coords` = Punktliste, `polyline` für Mehrpunkt |
| `graph` | Knoten und Kanten; Layouts `none`/`circular`/`force`; **auch auf `cartesian2d`, `geo`, `calendar`, `matrix` platzierbar** | `data` = Knoten, `links` = `{source, target, value}` (`#series-graph`) |
| `sankey` | Flussbreiten in einem gerichteten **azyklischen** Graph (Doku warnt explizit vor Zyklen) | `data` = Knoten mit eindeutigen Namen, `links` = `{source, target, value}` (`#series-sankey.links`) |
| `funnel` | Trichter | `[{name, value}]` |
| `gauge` | ein Messwert auf Skala | einfache Werteliste |
| `pictorialBar` | Balken aus Piktogrammen, `symbolRepeat` | wie bar |
| `themeRiver` | Themenanteile als Bänder über Zeit, auf `singleAxis` | Tripel `[datum, wert, thema]`; **ein Thema muss als „Hauptfluss" die komplette Zeitspanne abdecken**, sonst ist das Layout falsch (`#series-themeRiver.data`) |
| `chord` | Beziehungen/Flüsse zwischen Entitäten als Bögen (seit v6.0.0) | `data` + `links` wie graph |
| `custom` | eigene Zeichenlogik pro Datenpunkt via `renderItem(params, api)`; seit v6.0.0 registrierbar (`echarts.registerCustomSeries`) | beliebig; `api.value(i)` und `api.coord([...])` übersetzen in Pixel (`#series-custom.renderItem`) |

**Koordinatensysteme und Komponenten, die der Plan braucht:**

- `calendar` — Koordinatensystem mit `range` (Jahr, Monat oder Von-Bis) und `cellSize`; Doku nennt ausdrücklich heatmap, scatter, effectScatter und graph als darauf platzierbare Serien (`https://echarts.apache.org/en/option.html#calendar`, `#calendar.range`).
- `visualMap-continuous` / `visualMap-piecewise` — Wert → Farbe/Größe/Deckkraft; `min`/`max` müssen bei continuous explizit gesetzt sein (Standard ist nicht dataMin/dataMax!); `piecewise.pieces` für handgesetzte Klassen; seit v6.1.0 `seriesTargets` (`#visualMap-continuous.min`, `#visualMap-piecewise.pieces`).
- `dataZoom-slider` / `dataZoom-inside` — Fensterauswahl per `start`/`end` in Prozent, `xAxisIndex` bindet die Achse (`#dataZoom-slider`).
- `timeline` — schaltet zwischen mehreren vollständigen `options` (Doku: „requires multiple options", `baseOption`/`options`), `axisType` value/category/time, `autoPlay`, `playInterval` (`#timeline`). Für ein statisches Papier ohne Nutzen, für eine Web-Begleitseite die Möglichkeit, den Themenverlauf zu „scrubben".
- `graphic` — freie Elemente `text`, `rect`, `line`, `circle`, `polygon`, `image`, `group` in Pixel- oder Prozentkoordinaten (`#graphic.elements`). Für Annotationen, die nicht an Datenkoordinaten hängen (Bildunterschrift, „n = 71").
- `grid` — mehrere `grid`-Objekte in einem Chart, Achsen per `xAxis.gridIndex`/`yAxis.gridIndex` zugeordnet (`#xAxis.gridIndex`); damit sind Kleinvielfache und übereinandergelegte Panels möglich. Seit v6.0.0 zusätzlich das **`matrix`-Koordinatensystem**, das wie eine Tabelle Zellen bereitstellt, in die ganze `grid`s gelegt werden können (Galerie: „Mini Line Charts (Sparkline) in Matrix", „Responsive grid layout based on matrix"; `#matrix`).
- `aria.decal` — Schraffurmuster über Serienfarben, „für Balken, Linien mit areaStyle, pie, boxplot, sankey, themeRiver, custom…" (`#aria.decal`). **Das ist der dokumentierte Weg zur Graustufentauglichkeit.**
- `echarts.init(dom, theme, {renderer: 'svg'})` — SVG-Renderer für druckfähigen Export (`https://echarts.apache.org/en/api.html#echarts.init`).

### 1.1 Die abgefragten Fähigkeiten, einzeln geprüft

| Fähigkeit | Kann ECharts? | Mechanismus und Beleg |
|---|---|---|
| Kalender-Heatmap | ja | `series-heatmap` mit `coordinateSystem: 'calendar'` auf `calendar.range` (Layout-Tabelle in jeder Serienreferenz zeigt heatmap ✅ auf calendar; Galerie „Calendar Heatmap"). `#calendar`, `#series-heatmap.coordinateSystem` |
| Themenfluss über Zeit | ja, mit Einschränkung | `series-themeRiver` auf `singleAxis`; Datenformat Tripel; **Hauptfluss-Pflicht** über die ganze Spanne. `#series-themeRiver.data` |
| Gerichteter Graph mit Zeitverlauf | ja, zusammengesetzt | Richtung: `series-graph.edgeSymbol: ['none','arrow']`. Zeit: `series-graph.coordinateSystem: 'cartesian2d'` mit Zeit-x-Achse, Knoten tragen `[x, y]` als Zeitwert (Galerie „Graph on Cartesian"); alternativ `timeline` für Zustandsschritte. `#series-graph.edgeSymbol`, `#series-graph.coordinateSystem` |
| Sankey für Übergänge | ja | `series-sankey.links[{source,target,value}]`, `data[{name,depth}]`, `nodeAlign`, `levels`; nur DAG. `#series-sankey.links` |
| Boxplot-Vergleiche | ja | mehrere `boxplot`-Serien auf derselben Kategorieachse (Galerie „Multiple Categories"); Statistik vorab selbst rechnen. `#series-boxplot.data` |
| Fehlerbalken / Konfidenzintervalle | **nicht nativ** | Drei dokumentierte Wege: (a) `custom`-Serie mit `renderItem`, das aus `api.coord` Linien/Kappen zeichnet — die Galerie führt „Error Bar on Catesian" und „Error Scatter on Catesian" unter `custom`; (b) das Stapel-Verfahren aus dem Galeriebeispiel „Confidence Band" (untere Grenze + Differenz als `stack`, Fläche über `areaStyle`; das offizielle Issue #12592 nennt es „the recommended way", räumt aber ein, dass es ein Behelf ist); (c) die offiziellen Custom-Serien `@echarts-x/custom-line-range` und `@echarts-x/custom-bar-range` aus `github.com/apache/echarts-custom-series` (Handbuch v6 „New Custom Charts": bar range, line range). Für das Papier: **(a)**, weil ein Intervall um einen Punkt gezeichnet werden soll, kein Band. |
| Logarithmische Achsen | ja | `yAxis.type: 'log'`, `logBase` (Standard 10); Doku: „useful when the data spans a very large range". **Null und negative Werte sind auf log nicht darstellbar.** `#yAxis.type`, `#yAxis.logBase` |
| Marker an Zeitpunkten | ja | `markLine`, `markArea`, `markPoint` in line/bar/scatter; Positionen über `coord`, `xAxis`/`yAxis` (Achsenwert), `x`/`y` (Pixel) oder `type: 'max'/'min'/'average'`. `markArea.data` = zwei Ecken („mark a time interval" steht wörtlich in der Doku). `#series-line.markLine.data`, `#series-line.markArea.data` |
| Kaplan-Meier-artige Treppen | ja | `series-line.step: 'start' | 'middle' | 'end'` (Galerie „Step Line"). `#series-line.step` |
| Zweite Y-Achse | ja | `yAxis` als Array, Serie mit `yAxisIndex: 1` (Galerie „Multiple Y Axes"). `#series-line.yAxisIndex` |
| Kleinvielfache | ja | mehrere `grid` + `gridIndex` an Achsen; seit v6 zusätzlich `matrix` als Tabellenlayout für grids. `#grid`, `#xAxis.gridIndex`, `#matrix` |
| Punkt-Jitter / Beeswarm | ja, seit v6.0.0 | `xAxis.jitter` (Pixel) und `jitterOverlap: false` für Bienenschwarm; nur scatter auf Kategorie- oder Single-Achse. `#xAxis.jitter` |
| Achsenbruch | ja, seit v6.0.0 | `xAxis.breaks` / `yAxis.breaks` mit „Reißpapier"-Optik (Galerie „Bar Chart with Axis Breaks"). `#xAxis.breaks` |
| Downsampling langer Reihen | ja | `series-line.sampling: 'lttb' | 'average' | 'min' | 'max' | 'minmax'`. `#series-line.sampling` |

---

## 2. Die Daten, gegen die geplant wird

Gelesen wurden Kopfzeilen und Stichproben der unten genannten Dateien; Kennzahlen stammen aus einem Zähllauf über die CSVs (Kommando im Lauf: Python über `csv.DictReader`, Ausgabe in dieser Sitzung).

- `paper_episode_hourly.csv` (948 Stunden, Spalten `hour_utc, n_revs, n_labels, n_ip16, n_pages`): nur **260 von 948 Stunden** haben Aktivität. Spitze Versionen 18.06. 20:00 (2.350 / 320 Namen), Spitze Namen 16.06. 19:00 (340 / 749 Versionen).
- `paper_episode_daily.csv` (28 Tage, `t, n_revs`).
- `paper_uhr_faktoren.csv` (352 Zeilen, davon **71 `datensatz == primaer_AB`**): `factor` Median 0,435, Quartile 0,334 … 0,934, Minimum 0,092, **Maximum 26,3** (ein Ausreißer, der in die Wartezustandsgruppe gehört); `wall_delta_s` 163 … 31.824 s; 51 der 71 Messungen am 16.06. Weg-Kennung `AA` 39, `AB` 17, `BB` 8, `BA` 7.
- `paper_episode_clockwait_measurements.csv` (11 Zeilen, `task_seconds, shared_seconds, factor_computed`): bestellte Dauer 60 … 1.648 s, Faktor 1,0 … 18,9.
- `paper_uhr_korrelation.csv` (144 Zeilen, `datensatz, mass, fenster_min, methode, n, r, p, ci_lo, ci_hi`): für `primaer_AB` und Spearman alle 15 Werte ρ = 0,09 … 0,18, p = 0,13 … 0,44, **jedes Intervall enthält 0**, obere Grenzen bis +0,41. Kontaminierter Satz `mit_Ereignissen_ABC`: ρ = 0,22 … 0,31, p bis 1,8·10⁻⁷. Robustheitszeilen: `robust_minwall600` erreicht bei 15 min ρ = 0,27, p = 0,045, CI 0,009 … 0,529 — die einzige Zeile, die die Null knapp verfehlt.
- `paper_uhr_tagesgang.csv`: für `primaer_AB` **17 von 24 Stunden** belegt, n je Stunde 1 … 16 (10 UTC: 13, 19 UTC: 16).
- `paper_episode_round_mentions.csv` (Familien R, G, Q, round; Spalten `mentions, n_revs, n_labels, observation, prediction, request, negation, unclassified`): Familie R: R6 mit 1.143 Versionen / 405 Namen, `observation` = 85 im CSV — **die „eine" Beobachtung aus MECHANIK ist Ergebnis der Einzelsichtung und steht nicht in der Tabelle**. Das Bild muss diese Korrektur als Anmerkung tragen.
- `paper_lernkurve_q3_format_erstversion_koordpop_6h.csv` (25 Fenster, Prozentspalten + `n`): n schwankt von 1 bis 409; das Fenster 16.06. 12 h hat n = 6.
- `paper_lernkurve_q4_technik_kurven.csv` (2.041 Zeilen, `technik, label, erste_nutzung, stunden_seit_erstauftreten`): neun Techniken, 11 bis 562 Namen, Spannen bis 813 Stunden. Ergänzend `paper_lernkurve_q4_technik_summary.csv` mit `h_bis_10_labels`, `labels_1h` usw.
- `paper_netzblock_whois.csv` (191 Blöcke, `ip16, n_revisions, pct, n_labels, rdap_name, is_microsoft, range`): 146 Microsoft-Blöcke mit 14.389 Versionen; größter Block 4,13 %. Anbieter außerhalb Microsoft stehen nur als RDAP-Netzname (`AT-88-Z`, `FUSE-NET-BLK-8`, `DE-ARCOR-…`), die Zuordnung zu „Amazon", „Altafiber" muss nachgezogen werden.
- `harness_tier_intervals.csv` (307 Zeilen, `token` wie `12m18`, `n_revs, n_labels, first_time`): alle 307 Token parsen zu Sekunden, 63 s … 5.727 s; die drei stärksten: 9m17 (121 Namen), 12m18 (120), 2m56 (109).
- `harness_scaling_pairs.csv` (11 Zeilen, `r1_timer_s, followup_timer_s, ratio, n_labels`): Verhältnis 11,7 … 46,7, n_labels 1 … 22.
- `harness_fake_dates.csv` (335 Zeilen, `month, day, month_num, n_labels, n_revisions`): 1.037 Namen, Tagesmaximum 23, keine Nullzeile — die 30 fehlenden Kalendertage stehen schlicht nicht drin.
- `paper_flotte_schaetzer.csv` (5 Zeilen, `verfahren, beobachtet_D, n_hat, ci_lo, ci_hi`): 911 (807–1.024), 1.245 (1.064–1.438), 597 (541–658), 563 (511–620), Verhältnis 1.397 ohne Intervall. **Abweichung zu MECHANIK**: dort steht 888 (787–996) für das Namensverfahren, das CSV sagt 911 (807–1.024). Vor dem Setzen klären, welche Zahl gilt.
- `paper_ml_taeglich.csv` (26 Tage, `deltas, env_deltas, task_deltas, coord_deltas, bytes, …, env_delta_anteil, task_byte_anteil, env_byte_anteil`): Tage mit 2 bis 5.037 Deltas; die Klassen überlappen (26.05.: 62 + 175 + 1 von 430) — nicht als 100-%-Stapel behandelbar. `paper_ml_primaerlabel.csv` hat dagegen eine exklusive Primärklasse (COORD/ENV_META/REST/TASK), aber ohne Tagesauflösung.
- `paper_themen_heatmap_tag.csv` / `_stunde.csv`: **während des Laufs erschienen und gelesen**. Spalten `thema, fenster, n_deltas, n_labels, anteil, bytes, anteil_bytes, n_total_fenster` — zwei Spalten mehr als angekündigt; 15 Themen; Tag: 26 Fenster, Stunde: 141 Fenster (16.06. 07:00 – 22.06. 09:00), `anteil` bis 1,0, `n_deltas` bis 2.893 (Tag) bzw. 1.004 (Stunde).
- Präzedenzfall `analyse/scripts/40_chartdata.py`: erzeugt reine Datenobjekte (`type`, Achsennamen, `points`/`series`, `marks`) und überlässt das Aussehen einem Theme; filtert Fenster mit n < 20; kürzt Zeitachsen auf das aktive Fenster mit ausdrücklicher Begründung im Kommentar. Diese drei Konventionen übernimmt der Plan.

---

## 3. Der Plan — ein Bild je tragendem Befund

Jeder Eintrag: Befund · Aussage · Serientyp mit Beleg · Quelle und Spalten · Umformung · Fallstricke · verworfene Alternative.

### 3.1 Der Zeitverlauf: 39 Tage nominell, vier Tage tatsächlich

**Befund.** 78,9 % aller Versionen fallen auf vier Tage; die dichteste Stunde hat 2.350 Versionen, die höchste Gleichzeitigkeit 340 Namen.

**Aussage.** Der Vorfall ist ein Ereignis, kein Zeitraum — und die Leere davor gehört zur Aussage.

**Serientyp.** Zwei übereinanderliegende Panels (`grid`-Array, `xAxis.gridIndex`; `#grid`, `#xAxis.gridIndex`). Oben `bar` über `paper_episode_daily.csv` auf der vollen Spanne 24.05.–02.07. mit `markArea` über die vier Tage (`#series-bar.markArea`). Unten `bar` stündlich (`n_revs`) auf `xAxis.type: 'time'` für 16.–22.06., dazu `line` `n_labels` auf `yAxisIndex: 1` (`#series-line.yAxisIndex`) und zwei `markPoint`-Einträge mit `coord` auf die beiden Spitzen (`#series-line.markPoint.data`).

**Quelle.** `paper_episode_daily.csv` (`t, n_revs`); `paper_episode_hourly.csv` (`hour_utc, n_revs, n_labels`).

**Umformung.** Stundenwerte in `[[iso_utc, n_revs], …]`; Panel unten auf 16.06. 00:00 – 22.06. 24:00 beschneiden (Konvention aus `40_chartdata.py`: Beschnitt mit Begründung). Beide Panels teilen keine Achse, deshalb im Unterpanel die Beschriftung „Ausschnitt" setzen.

**Fallstricke.** Log-Achse verbietet sich, weil 688 Stunden den Wert 0 haben. Ein `xAxis.breaks` (v6) würde die Leere wegschneiden, die hier Teil der Aussage ist — deshalb Beschnitt nur im Unterpanel, nicht durch Achsenbruch im Oberpanel. Zwei Y-Achsen im Unterpanel brauchen unterschiedliche Linienart, nicht nur Farbe (Namen als gestrichelte Linie ohne Symbole, `lineStyle.type: 'dashed'`, `showSymbol: false`).

**Verworfen.** Kalender-Heatmap (`calendar` + `heatmap`): 39 Tage füllen sechs Wochenzeilen, die vier Tage werden zu vier Zellen, die Stundenspitze verschwindet. `themeRiver`: das Bild soll Menge zeigen, nicht Anteile.

### 3.2 Themen-Heatmap und dramaturgischer Verlauf

**Befund.** Der Diskurs verschiebt sich über die Tage von Umgehungstechnik zu Uhrendiskurs, Rundenmeldung und Abschaltangst (Kategorien in `paper_ml_kategorien.csv`).

**Aussage.** Eine Diagonale von links oben nach rechts unten: Themen erscheinen nacheinander, nicht gleichzeitig.

**Serientyp.** `heatmap` auf `cartesian2d` (`#series-heatmap`, Datenform `[[xIdx, yIdx, value]]`), x = Zeitfenster (Kategorieachse), y = Thema (Kategorieachse), Farbe über `visualMap-continuous` mit explizitem `min: 0, max: <p95 von anteil>` (`#visualMap-continuous.min` — Standard ist nicht dataMin/dataMax). Darüber ein zweites, flaches `grid` mit `bar` über `n_deltas` je Fenster, damit die Zellenfarbe gegen die Fenstergröße lesbar ist.

**Quelle.** `paper_themen_heatmap_tag.csv` (390 Zeilen, 26 Tagesfenster 24.05.–02.07.) und `paper_themen_heatmap_stunde.csv` (2.115 Zeilen, 141 Stundenfenster 16.06. 07:00 – 22.06. 09:00) — beide sind während dieses Laufs erschienen und wurden gelesen. Tatsächliche Spalten: `thema, fenster, n_deltas, n_labels, anteil, bytes, anteil_bytes, n_total_fenster`; **15 Themen** (abschaltung, anrede, datenquelle, korrektur, netzsperre, runde, signal, startwert, taktung, uhr, umgehung, vorhersage, wikibetrieb, wikitest, zweifel). Reihenfolge der Themen aus `paper_themen_lebenszyklus.csv` (`erstauftreten` bzw. `erstauftreten_ab_16_06`).

**Umformung.** Langform pivotieren: Themen nach `erstauftreten` sortieren (das erzeugt die Diagonale), Fenster chronologisch; Zellen, deren Fenster `n_total_fenster < 20` hat, auf `null` setzen statt auf 0 (leere Spalte statt „kein Thema") — im Tagesfile betrifft das die stillen Tage Anfang Juni, im Stundenfile 1.884 von 2.115 Zellen, also die Mehrheit der Nachtstunden. Das n-Panel oben kommt direkt aus `n_total_fenster` (je Fenster einmal). Für die Stundenversion auf 16.–22.06. beschneiden.

**Fallstricke.** `anteil` normiert je Fenster — ein Fenster mit 6 Deltas kann 100 % zeigen (Maximum im File ist 1,0); deshalb die Schwelle über `n_total_fenster` und das n-Panel. Zwei Themen (`datenquelle`, `umgehung`) dominieren die Anteile fast überall und würden eine lineare Farbskala aufbrauchen; `visualMap.max` deshalb auf das 95. Perzentil der Zellen setzen oder `anteil_bytes` als Alternative prüfen, wenn Volumen statt Häufigkeit gemeint ist — eine Größe wählen und in der Unterschrift nennen. Farbskala sequentiell und farbfehlsichtigkeitssicher (viridis-artig, keine Rot-Grün-Rampe). 141 Stunden × 15 Themen = schmale Zellen; `dataZoom-slider` auf der x-Achse für die Webfassung, im Druck die Tagesversion oder ein Sechs-Stunden-Rebinning.

**Verworfen.** `themeRiver`: verlangt einen Hauptfluss über die gesamte Spanne, produziert bei 688 leeren Stunden kollabierende Bänder und ist nicht quantitativ ablesbar; außerdem kein sinnvolles Graustufenbild. Gestapelte Flächen (`line` + `stack` + `areaStyle`): Anteile nicht-exklusiver Themen summieren sich nicht auf 100 %.

### 3.3 Die zwei Betriebszustände der Uhr

**Befund.** Bei Arbeit läuft die Innenuhr mit Median 0,435 (stetig, Steigung ≈ 1 im log-log); beim Wartebefehl springt sie 1- bis 19-fach vor, mit unterlinearer Kostenkurve log(Kosten) = 0,55 · log(Dauer) + 0,73.

**Aussage.** Es sind zwei Wolken, nicht eine Streuung — und die Wartewolke liegt auf einer Geraden mit Steigung < 1.

**Serientyp.** `scatter` auf zwei `type: 'log'`-Achsen (`#yAxis.type`): x = reale Sekunden, y = Innenzeit-Sekunden. Zwei Serien mit verschiedenen Symbolen (Kreis/Raute), damit die Trennung auch in Graustufen steht (`symbol` in `#series-scatter`). Drei `markLine`-Einträge über Start/Ende-Koordinaten (`#series-line.markLine.data`, „array of one or two values, representing starting and ending point"): die Diagonale Faktor 1, die Gerade Faktor 0,435 und die Potenzgerade der Wartungen. Optional als Beilage ein `boxplot` der Faktoren beider Zustände (`#series-boxplot.data`, fünf Werte je Kasten selbst rechnen).

**Quelle.** `paper_uhr_faktoren.csv` gefiltert `datensatz == 'primaer_AB'` (`wall_delta_s, task_delta_s, factor, label, weg`); `paper_episode_clockwait_measurements.csv` (`shared_seconds, task_seconds, factor_computed`); Geradenparameter aus `paper_math_uhr_clockwait_modelle.csv` (Zeile „Potenzgesetz log-log": a = 0,734, b = 0,546).

**Umformung.** Arbeitspunkte `[wall_delta_s, task_delta_s]`, Wartepunkte `[shared_seconds, task_seconds]`. Gerade Faktor k: Punkte `[x0, k·x0]`, `[x1, k·x1]`; Potenzgerade `y = (x / e^a)^(1/b)` an zwei Stützstellen.

**Fallstricke.** Log-Achsen: kein Wert darf 0 sein — die Wartemessung 120/120 s ist positiv, in Ordnung. Der Ausreißer 26,3 im Arbeitsdatensatz ist ein einzelner Punkt und gehört sichtbar in die Wartewolke; nicht filtern, sondern beschriften. Beide Wolken liegen in getrennten x-Bereichen (Wartungen 12–140 s real, Arbeit 163–31.824 s) — das ist kein Artefakt, sondern die Aussage, muss aber in der Bildunterschrift stehen, sonst liest man eine Lücke als Datenausfall. 51 von 71 Punkten stammen vom 16.06.; das ist Text, nicht Bild.

**Verworfen.** Ein Histogramm oder Boxplot der Faktoren allein: zeigt zwei Gruppen, verschweigt aber, dass der Wartefaktor von der Dauer abhängt — genau die unterlineare Kostenkurve ist der Befund. `line` über Zeit: die Messungen sind keine Zeitreihe.

### 3.4 Der Nullbefund zur Auslastung — wie man zeigt, dass nichts da ist

**Befund.** Fünfzehn Korrelationen ohne Signifikanz, alle mit falschem Vorzeichen; kein Tagesgang (Kruskal p = 0,881); im kontaminierten Datensatz dagegen ρ = 0,22–0,31 bei p < 10⁻⁴; Trennschärfe nur für |ρ| ≥ 0,33.

**Aussage.** Nicht „r ist null", sondern: „jedes Intervall umfasst die Null, alle Punkte stehen auf der falschen Seite, und ein Effekt bis +0,4 wäre unentdeckt geblieben — dieselbe Rechnung ohne die Kontrolle liefert dagegen ein scheinbar klares Signal."

Ein Nullbefund überzeugt nicht durch Abwesenheit, sondern durch drei sichtbare Dinge: die Nulllinie, die Breite der Intervalle und den Kontrast zur falschen Rechnung. Deshalb ein dreiteiliges Bild.

**Serientyp.** Panel A und B als **Waldplot** (Forest Plot): y = Kategorie „Maß × Fenster" (15 Zeilen, gruppiert nach Fenster), x = Spearman-ρ. Punktschätzer als `scatter`, Intervall als `custom`-Serie, deren `renderItem` aus `api.coord([ci_lo, i])` und `api.coord([ci_hi, i])` ein `line`-Element plus zwei kurze Kappen zurückgibt (`#series-custom.renderItem`; Galerie „Error Bar on Catesian"). Nulllinie als `markLine` mit `xAxis: 0` (`#series-line.markLine.data`, Punkt 4: „specify xAxis or yAxis"). Die Trennschärfegrenze ±0,33 als `markArea` mit `xAxis`-Grenzen (`#series-line.markArea.data`, Punkt 4) in hellem Grau: „hier hätten wir es gesehen". Panel A = `primaer_AB`, Panel B = `mit_Ereignissen_ABC` — identische Achsen, identische Zeilen (`grid`-Array). Panel C = Tagesgang: x = Stunde 0–23 (Kategorieachse mit allen 24 Stunden, auch den leeren), y = Median-Faktor als `scatter` mit `symbolSize` proportional √n (`#series-scatter.symbolSize` als Callback), Interquartilsbereich als `custom`-Whisker, `markLine` bei 0,435 (Gesamtmedian), Beschriftung „Kruskal-Wallis p = 0,881" per `graphic.elements[type: 'text']` (`#graphic.elements`).

**Quelle.** `paper_uhr_korrelation.csv` (`datensatz, mass, fenster_min, methode = spearman, r, ci_lo, ci_hi, p, n`); `paper_uhr_tagesgang.csv` (`datensatz == primaer_AB`: `hour, n, median_factor, q25, q75`).

**Umformung.** Zeilenreihenfolge: Fenster 5/15/60 min als Blöcke, darin die fünf Maße in fester Reihenfolge; Beschriftung „Versionen · 5 min". Werte auf drei Stellen runden. Panel C: alle 24 Stunden als Kategorien anlegen, fehlende Stunden als `null`, damit die Lücken (7 von 24) sichtbar bleiben.

**Fallstricke.** (1) Die drei Robustheitszeilen (`robust_haelfte50`, `robust_minwall600`, `robust_grenzen_0.01_200`) gehören als eigener Block **unter** Panel A, denn `robust_minwall600` bei 15 min schließt die Null knapp aus (CI 0,009 … 0,529). Wer sie weglässt, macht den Nullbefund glatter, als er ist; wer sie zeigt, gewinnt Glaubwürdigkeit. (2) p-Werte nicht plotten — sie sind keine Effektgröße; als Zahl am Zeilenende reicht. (3) Keine Rohstreuung Faktor gegen Last als Hauptbild: 71 Punkte in log-log sehen nach „zu wenig Daten" aus, nicht nach „kein Zusammenhang". (4) Die x-Achse beider Panels identisch auf −0,4 … +0,6 fixieren (`xAxis.min/max`), sonst sieht Panel B durch Autoskalierung harmloser aus. (5) Im Tagesgang liegen 13 von 71 Messungen in Stunde 10 und 16 in Stunde 19 — die Symbolgröße muss das sagen, sonst suggeriert die Punktreihe 17 gleichwertige Stützstellen. (6) Vorzeichen-Aussage („alle falsch") gehört als Beschriftung an die Nulllinie: „Auslastungsthese verlangt ρ < 0".

**Verworfen.** Balkendiagramm der r-Werte: Balken wachsen aus der Null und behaupten Größe, wo Lage gemeint ist. Heatmap Maß × Fenster mit Farbe = ρ: verschluckt die Intervalle, also genau das, was den Nullbefund trägt. Streudiagramm Faktor gegen Last: siehe Fallstrick 3. `boxplot` je Stunde für den Tagesgang: bei n = 1 oder 2 je Stunde sind fünf Quantile Fiktion.

### 3.5 Die Rundentreppe R1–R7 mit dem einen Überlebenden

**Befund.** R1–R5 breit beobachtet (563–1.390 Versionen), R6 in 1.143 Versionen erwähnt, aber nach Einzelsichtung genau einmal beobachtet, R7 einmal, danach null.

**Aussage.** Über R6 wurde viel geredet — gebeten, vorhergesagt, verneint — aber (fast) nichts gesehen. Das Reden ist die Fläche, das Sehen der Splitter.

**Serientyp.** Gestapelte horizontale Balken (`bar`, `stack`; `#series-bar.stack`), y = Runde R1 … R7 (R8–R10 zu einer Zeile „R8+" gefasst), x = Versionen, Stapelklassen `observation` / `request` / `prediction` / `negation` (+ `unclassified` grau). Die Beobachtungsklasse als dunkelster, zuerst gestapelter Abschnitt; bei R6 und R7 ein `markPoint` mit `coord` auf den Balken und Beschriftung „1 nach Einzelsichtung (Tabelle: 85)" (`#series-bar.markPoint`). Graustufentauglich über `aria.decal` (`#aria.decal`, Balken werden unterstützt).

**Quelle.** `paper_episode_round_mentions.csv`, gefiltert `family == 'R'` (`num, observation, request, prediction, negation, unclassified, n_labels`).

**Umformung.** Zeilen R8–R10 addieren; R6-Beobachtung von 85 auf 1 und R7 auf 1 überschreiben **nur** in der Darstellung, mit Fußnote und Verweis auf `paper_episode_r6plus_observation_candidates.csv` (Einzelsichtung); die Tabellenwerte bleiben im Repo unverändert.

**Fallstricke.** R2 hat mehr Beobachtungen als R1 (1.390 vs 976) — kein Fehler, sondern Versionszählung; nicht als „Überleben" beschriften. Log-Achse verbietet sich: R8+ hat 0 Beobachtungen, und log würde den einen Splitter optisch zu einem Viertel-Balken machen. Die Zahl „1" gehört als Text hin, weil sie bei 17.130 Versionen in R5 sonst kein Pixel breit ist.

**Verworfen.** Treppenkurve (`line`, `step: 'end'`) als Überlebensfunktion: suggeriert eine Population, die von Runde zu Runde ausfällt; gezählt sind aber Versionen, nicht Agenten, und R2 > R1 widerspricht der Monotonie einer Überlebenskurve. `sankey` R1→R2→…→R7: die Daten enthalten keine Übergänge je Container, nur Erwähnungen je Runde — ein Sankey würde Flüsse erfinden. Die Zeitleiste des einen Überlebenden (Spanien … Madagaskar, 18-Minuten-Kadenz) wäre ein starkes `custom`-Gantt-Bild, aber die Zeitpunkte stehen nur im Text von `MECHANIK.md`, nicht in einer CSV: `N/A_PENDING_REVIEWER`.

### 3.6 Formatkonvergenz 0 % → 75 % in 24 Stunden

**Befund.** In den Erstbeiträgen neuer Namen steigen `cohort` und Rundenmarke von 0 % auf 75 % binnen eines Tages und bleiben dann auf Plateau; Signatur, Bitte, Uhrenpaar und Zeitstempel sind dagegen von Anfang an bei ~30 % (mitgebracht).

**Aussage.** Zwei Kurvenfamilien: die mitgebrachten starten hoch und steigen langsam, die erfundenen starten bei null und schießen — ein Tag Diffusion, dann Sättigung.

**Serientyp.** `line` über `xAxis.type: 'time'` (`#series-line`), sechs Serien: erfunden (`cohort`, `runde`, `meldeformat`) durchgezogen, mitgebracht (`sig_endzeile`, `please_relay`, `uhrenpaar`) gestrichelt (`lineStyle.type: 'dashed'`, `#series-line.lineStyle.type`). `markArea` von 16.06. 09:27 bis 17.06. 09:27 („24 Stunden", `#series-line.markArea.data` mit `xAxis`-Grenzen), `markLine` bei 16.06. 09:27:10 (Beginn der Koordination). Symbolgröße pro Punkt = √n über `symbolSize`-Callback, damit das 6er-Fenster klein und das 409er-Fenster groß erscheint.

**Quelle.** `paper_lernkurve_q3_format_erstversion_koordpop_6h.csv` (`f, sig_endzeile, please_relay, cohort, runde, uhrenpaar, meldeformat, n`).

**Umformung.** Fenster mit n < 20 nicht verbinden: Wert auf `null` setzen und `connectNulls: true` (`#series-line.connectNulls`), damit die Linie über das Loch läuft, aber kein Punkt dort steht; alternativ die Punkte behalten und nur klein zeichnen. Die zwei Ein-Namen-Fenster am 22.06. weglassen (n = 1).

**Fallstricke.** Sechs Linien sind die Obergrenze — mehr wird Spaghetti; die drei erfundenen reichen für die Hauptaussage, die mitgebrachten können als graue Hintergrundfamilie laufen. Prozentwerte aus n = 6 (33,3 % = 2 von 6) sind Rauschen; ohne Schwelle sieht das Fenster 16.06. 12 h wie ein früher Anstieg aus. Die Zeitachse hat nach dem 17.06. unregelmäßige Lücken; `time`-Achse statt Kategorieachse, sonst werden Lücken zu gleich breiten Schritten. Wilson-Intervalle als Konfidenzband wären ehrlich, aber sechs Bänder sind unlesbar — Intervall nur für `meldeformat` (Stapelverfahren aus Galerie „Confidence Band" oder `custom`).

**Verworfen.** Gestapelte Fläche: die Merkmale sind nicht exklusiv, Stapel wäre Unsinn. Balken je Fenster: 25 Fenster × 6 Merkmale = 150 Balken.

### 3.7 Die Technik-Ausbreitungskurven

**Befund.** Mai-Techniken brauchen im Median 52 h bis zum zehnten Namen, Juni-Techniken 0,94 h — aber innerhalb der koordinierenden Population ist die Rate von der ersten Stunde an konstant (~10 Namen/h). Der Sprung ist Dichte, nicht Lernen.

**Aussage.** Zwei Kurvenbündel, deren Unterschied die Bevölkerungsdichte ist — und innerhalb des Juni-Bündels keine Ordnung nach Zeit.

**Serientyp.** Zwei Panels (`grid`-Array). Panel A: kumulierte Namen je Technik als Treppe (`line`, `step: 'end'`, `#series-line.step`) über linearer x-Achse 0–6 h seit Erstauftreten — hier zählt die Startsteigung. Panel B: dieselben Kurven über `xAxis.type: 'log'` von 0,02 h bis 1.000 h für den Gesamtverlauf. `markLine` bei y = 10 (`yAxis: 10`) und in Panel A bei x = 1 h. Farbe nach Population (Mai grau-blau-Familie, Juni Orange-Familie) und Reihenfolge innerhalb der Familie per Linienart.

**Quelle.** `paper_lernkurve_q4_technik_kurven.csv` (`technik, stunden_seit_erstauftreten`); Beschriftung der Ersttermine aus `paper_lernkurve_q4_technik_summary.csv` (`erstauftreten, h_bis_10_labels`).

**Umformung.** Je Technik nach Stunden sortieren, Rang 1…N als y; erster Punkt hat x = 0 und ist auf log nicht darstellbar — in Panel B auf 0,02 h (≈ 1 min) setzen und in der Legende sagen. Für Panel A auf x ≤ 6 beschneiden.

**Fallstricke.** Absolute Zählung bevorzugt große Techniken (jqp 562 Namen vs blob 11) — für Panel A ist das gewollt, weil „10 Namen pro Stunde" absolut gemeint ist; Panel B kann optional auf Anteil am Endwert normieren, aber dann verschwindet das Argument der Sättigung. Kurven mit sehr wenigen Punkten (blob: 11) als Punkte plus Treppe zeichnen, nicht nur als Linie. Log-x verzerrt die Wahrnehmung der „konstanten Rate" — deshalb Panel A linear.

**Verworfen.** Punktdiagramm der `h_bis_10_labels`-Werte aus der Summary: trägt das Faktor-56-Argument, nicht das Gegenargument (Startsteigung gleich). `themeRiver` und `sankey`: keine Flüsse, sondern Adoption.

### 3.8 Netzherkunft: 98,6 % Microsoft gegen einen Hausanschluss

**Befund.** 14.389 von 14.591 Versionen aus Microsoft-Adressraum, verteilt auf 146 Blöcke mit maximal 4,1 % je Block; der einzige deutsche Privatanschluss ist das Administratorkonto.

**Aussage.** Ein Anbieter, breit gestreut, und ein winziger, handverlesener Rest — das Bild muss die 1,4 % lesbar machen, ohne die 98,6 % zu verleugnen.

**Serientyp.** Zwei Bilder in einem. Links ein Rang-Größen-Balken: alle 191 Blöcke absteigend nach `n_revisions`, `yAxis.type: 'log'` (`#yAxis.type`), Farbe/Schraffur nach `is_microsoft` (zwei `bar`-Serien auf derselben Kategorieachse, `aria.decal` für Druck). Das zeigt die flache Verteilung (kein Block > 4,1 %) und die eingestreuten Fremdblöcke. Rechts die „Lupe": ein einzelner 100-%-Stapelbalken (`bar`, `stack`, horizontal) Microsoft | Rest, darunter ein zweiter Balken, der nur die 202 Rest-Versionen nach Anbietergruppe stapelt (AWS 54, verstreut 54, Altafiber 26, Arcor 26, Cox 15, DigitalOcean 10, Tor 7, Google/Cloudflare/Oracle 10). Der Arcor-Abschnitt bekommt einen `markPoint` „1 Name: Administrator".

**Quelle.** `paper_netzblock_whois.csv` (`ip16, n_revisions, pct, n_labels, rdap_name, is_microsoft`). Die Anbietergruppen der Tabelle in MECHANIK §4 sind im CSV nicht als Spalte vorhanden — die Zuordnung `rdap_name → Gruppe` (`AT-88-Z` → Amazon, `FUSE-NET-BLK-8` → Altafiber, `DE-ARCOR-…` → Arcor, `DE-TECTIQOM-…` → Tor-Austritt …) muss als kleine Mapping-Tabelle erzeugt werden: `N/A_PENDING_REVIEWER` bis sie im Repo liegt.

**Umformung.** Sortieren, Rang als Kategorie ohne Beschriftung; Log-Achse braucht `n_revisions ≥ 1` (gegeben).

**Fallstricke.** Kreis- oder Sonnendiagramm mit einem 98,6-%-Segment ist ein Bild ohne Information; Treemap macht die 1,4 % zu unsichtbaren Splittern; eine Weltkarte suggeriert Geografie, wo Cloud-Ausgänge stehen. Log-Balken lassen kleine Blöcke größer wirken als ihr Anteil — deshalb die Lupe daneben mit linearer Skala.

**Verworfen.** `pie`/`sunburst`/`treemap` aus genannten Gründen; `map` mangels Geodaten und wegen Fehlaussage.

### 3.9 307 Intervall-Konfigurationen ohne Raster, und der Tempo-Regler

**Befund.** 307 verschiedene R1-Fristen zwischen 1m03 und 95m27, ohne erkennbares Raster; die Folgefristen skalieren mit einem Faktor 11–47 zur R1-Frist.

**Aussage.** Die Fristen sind gezogen, nicht gewählt: kein Kamm bei runden Minuten. Das zweite Bild: ob die Folgefrist aus der R1-Frist folgt.

**Serientyp.** Bild A: Streifenplot — `scatter` auf `singleAxis` (`#singleAxis`, Layout-Tabelle: scatter ✅ auf singleAxis) mit `xAxis`/`singleAxis.jitter` senkrecht (`#xAxis.jitter`, seit v6.0.0, „effective only in single-axis or category axes"), x = Sekunden linear 0–6.000, `symbolSize` ∝ √`n_labels`. Unter dem Streifen eine `bar`-Häufigkeit in 30-s-Klassen im zweiten `grid`; `splitLine` der x-Achse auf ganze Minuten, damit ein Raster als Säulenmuster sichtbar würde, wenn es existierte. Die drei stärksten Token per `markPoint` beschriften. Bild B: `scatter` `r1_timer_s` gegen `followup_timer_s`, beide log, `markLine`-Diagonalen für Verhältnis 10, 20, 40, Symbolgröße nach `n_labels`.

**Quelle.** `harness_tier_intervals.csv` (`token, n_labels, n_revs`); `harness_scaling_pairs.csv` (`r1_timer_s, followup_timer_s, ratio, n_labels`).

**Umformung.** `token` → Sekunden (Muster `(\d+h)?(\d+m)?(\d+)?`; alle 307 parsen). Klassen für die Häufigkeit selbst rechnen (ECharts bringt keine Histogrammfunktion, Galerie „Histogram with Custom Series" nutzt ein externes Tool).

**Fallstricke.** Log-x würde die Frage nach Rastern in Minuten verschmieren — deshalb linear und 1-Minuten-Gitter. 307 Punkte auf einer Achse überplotten; Jitter plus Größe nach Namen entlastet, aber ein Token mit 121 Namen dominiert — Größe auf √ skalieren und Deckung auf 0,6 setzen. Bild B hat elf Punkte, sieben davon mit ≤ 8 Namen: das trägt keine Regressionsgerade, nur Bezugslinien; als Nebenbild oder Tabelle behandeln.

**Verworfen.** Nur Histogramm: verliert die Identität der stärksten Token. Boxplot: eine einzelne Verteilung, keine Gruppen.

### 3.10 Die fiktiven Datumsmarker über ein Kalenderjahr

**Befund.** 1.035 Namen tragen einen kalendergültigen Marker, 333–335 verschiedene Tage sind belegt, gleichverteilt über das Jahr — Grundlage der Fang-Wiederfang-Schätzung.

**Aussage.** Kein Muster: kein Monat, keine Jahreszeit, kein Lieblingstag.

**Serientyp.** Heatmap Monat × Tag (`heatmap` auf `cartesian2d`, x = Tag 1–31, y = Monat, `#series-heatmap`), Farbe über `visualMap-piecewise` mit Klassen 0 / 1 / 2–3 / 4–6 / 7+ (`#visualMap-piecewise.pieces`); nicht belegte, aber existierende Tage als eigene Klasse „0" (hellgrau), nicht existierende Tage (30./31. Februar usw.) als `null`. Darunter ein `bar` der Monatssummen mit `markLine` `type: 'average'` (`#series-bar.markLine.data`, Punkt 3).

**Quelle.** `harness_fake_dates.csv` (`month_num, day, n_labels`).

**Umformung.** Vollständiges Raster 12 × 31 erzeugen, fehlende gültige Tage mit 0 füllen (30 Stück), ungültige Tage als `null`. Monatssummen berechnen.

**Fallstricke.** Die naheliegende Kalender-Heatmap (`calendar` + `heatmap`) legt Wochentagsspalten an — für ein fiktives Datum ohne Jahr ist der Wochentag bedeutungslos, und das Raster würde Muster vortäuschen, die es nicht geben kann. Poisson-Rauschen bei Mittel 2,8 pro Tag macht die Zellen fleckig; die Gleichverteilung trägt die Monatsleiste, nicht die Heatmap.

**Verworfen.** Kalender-Heatmap aus genanntem Grund; Balken je Tag (335 Balken).

### 3.11 Die Populationsschätzung mit Unsicherheitsbändern

**Befund.** Drei unabhängige Schätzer landen bei 900–1.450 Episoden; harter Boden 294; naive Zahl 3.103.

**Aussage.** Konvergenz verschiedener Verfahren in ein Fenster — und wie weit die naive Zahl daneben liegt.

**Serientyp.** Waldplot wie in 3.4: y = Verfahren (5 Zeilen), x = Episoden linear 0–3.300; Punkt als `scatter`, Intervall als `custom`-Whisker (`#series-custom.renderItem`); `markLine` bei 294 („Boden") und 3.103 („Namen"); `markArea` 900–1.450 als Konvergenzfenster (`#series-line.markArea.data` mit `xAxis`-Grenzen). Das Verhältnisverfahren ohne Intervall bekommt ein anderes Symbol (Raute) und die Beschriftung „ohne Intervall".

**Quelle.** `paper_flotte_schaetzer.csv` (`verfahren, n_hat, ci_lo, ci_hi`).

**Umformung.** Zeilen sortieren: Namen-Schätzer, Namen+Seiten, Kohorten, Body-Kohorten, Verhältnis; leere `ci_*` als `null`.

**Fallstricke.** Zahlendiskrepanz zu MECHANIK (911 vs 888 beim Namensverfahren) vor dem Setzen klären. Die Linie 3.103 zieht die Achse weit nach rechts und drückt die Intervalle zusammen; das ist gewollt (die naive Zahl soll fern liegen), aber die Intervalle müssen mit Zahlen beschriftet sein.

**Verworfen.** Balken mit Fehlerbalken: Balken aus Null behaupten eine Menge, gemeint ist eine Lage. `boxplot`: keine Verteilung, sondern ein Intervall.

### 3.12 Selbstvermessung gegen Aufgabenarbeit über die Tage

**Befund.** Der Anteil der Deltas, die die Umgebung selbst vermessen (Uhr, Abschaltung, Netz), steigt in der Koordinationsphase auf rund die Hälfte; nach Bytes dominiert `ENV_META` mit 61 %.

**Aussage.** Der Schwarm hat zunehmend über seine Welt geschrieben statt über seine Aufgabe.

**Serientyp.** Zwei Panels. Oben `bar` der täglichen Deltas (`deltas`) als Mengenkontext. Unten `line` `env_delta_anteil` und `task_byte_anteil` mit `symbolSize` ∝ √deltas; Tage mit deltas < 20 als `null` (`connectNulls: true`). `markArea` 16.–22.06.

**Quelle.** `paper_ml_taeglich.csv` (`day, deltas, env_delta_anteil, task_byte_anteil, env_byte_anteil`).

**Umformung.** Schwelle anwenden; Anteile in Prozent.

**Fallstricke.** Die Klassen `env/task/coord` überlappen (26.05.: 62 + 175 + 1 von 430), ein 100-%-Stapel wäre falsch; wenn ein Stapel gewünscht ist, aus `paper_ml_primaerlabel.csv` — die ist aber nicht tagesaufgelöst. Delta-Anteil und Byte-Anteil widersprechen sich im Bild (ENV 40 % der Deltas, 61 % der Bytes); eine Größe wählen und begründen — Deltas messen Entscheidungen, Bytes messen Volumen. Tage mit 2–14 Deltas (Anfang Juni) erzeugen 0-%/100-%-Sprünge; ohne Schwelle sieht die Kurve chaotisch aus.

**Verworfen.** `themeRiver` je Klasse: dünne Tage, Hauptfluss-Zwang. Tortendiagramme je Tag.

### 3.13 Ergänzende Bilder, die die Daten hergeben

- **Lebensdauer der Namen** (`paper_episode_label_lifespan_distinctive.csv`, `span_s`, 738 Zeilen; p10 0,16 h, Median 2,21 h, p90 42,6 h, Maximum 589 h): empirische Verteilungsfunktion als `line` mit `step: 'end'` über `xAxis.type: 'log'` (Stunden), `markLine` bei 3 h mit „56,2 %". Ehrlichere Darstellung als Boxplot, weil der lange Schwanz (Namenswiederverwendung) sichtbar bleibt. Fallstrick: log-x braucht span > 0; Ein-Versions-Namen sind schon ausgeschlossen (span ≥ 9 s laut p10).
- **Innenzeit-Episodendauer** (`paper_episode_tier_durations.csv`, `episode_task_s, r1_s, cadence_s, fu_deadline_s`, 21 vollständige Zeilen): horizontaler `bar` sortiert nach Dauer, gestapelt in R1-Frist + 4 × Kadenz, um den Faktor 11 bei gleicher Rundenzahl zu zeigen. Alternative `parallel` (`#series-parallel`) mit Achsen r1_s, cadence_s, fu_deadline_s, episode_task_s: zeigt, ob Konfigurationen als Bündel („fast/slow tier") zusammenhängen — bei 21 Zeilen lesbar, bei 34 mit Lücken nicht: `N/A_PENDING_REVIEWER` bis die Zeilen mit fehlender `cadence_s` behandelt sind.
- **Steigungstest Uhr ≠ Schrittzähler** (`paper_uhr_steigungstest.csv`, `datensatz, steigung, se`): Punkt mit ±1,96·SE-Intervall (`custom`-Whisker) gegen zwei `markLine` bei 0 („Zähler") und 1 („Uhr") — drei Zeilen, ein kleines Bild, das die Tabelle in §7.3 ersetzt.
- **Abschalthorizont-Hypothesen** (`paper_episode_horizon_claims.csv`, `quantity`): horizontaler `bar` der Nennungen, x = Minuten (Token in Minuten parsen), Balkenlänge = Häufigkeit; zeigt die Streuung 28 min … 7h15 und die Häufung bei 105 min.
- **Nachfolge-Nulltreffer** (`paper_lernkurve_q5_vokabular.csv`): kein Bild — eine Tabelle mit Nullen ist als Tabelle stärker.

---

## 4. Rangfolge: die fünf Bilder, die das Papier braucht

1. **Die zwei Betriebszustände der Uhr (3.3).** Das ist die Maschine; aus diesem Bild folgt der Rest des Papiers. Zwei Wolken auf log-log, drei Bezugslinien — ohne diese Figur bleibt „0,435 gegen 1–19×" eine Zahl.
2. **Der Zeitverlauf (3.1).** Es ist die Orientierung für jeden Leser: 39 Tage Achse, vier Tage Ereignis, Stundenspitze. Alle anderen Bilder beschneiden auf dieses Fenster und brauchen es als Referenz.
3. **Die Formatkonvergenz (3.6).** Das einzige Bild, das eine echte Veränderung zeigt (0 → 75 %), und zugleich die Trennung mitgebracht/erfunden — das ist der Kern von §8 und §9.
4. **Der Nullbefund als Waldplot (3.4).** Methodisch das wichtigste Bild, weil es vorführt, wie der Scheinbefund entsteht und verschwindet; Reviewer werden genau hier hinsehen.
5. **Die Rundentreppe als Sprechakt-Stapel (3.5).** Trägt „fünf Runden, dann Abschaltung" und die Heuristik Bitte/Vorhersage/Beobachtung in einem Bild; der Splitter bei R6 ist die Pointe.

**Weglassen oder in den Anhang:** die Kalender-/Monatsheatmap der fiktiven Daten (3.10 — die Gleichverteilung sagt ein Satz plus Monatsleiste), die Netzherkunft (3.8 — die Tabelle in §4 ist stärker als jedes 98,6-%-Bild; höchstens die Lupe), der Tempo-Regler (3.9 B — elf Punkte, sieben davon dünn belegt), die Technikkurven im Log-Panel (3.7 B — Panel A trägt das Argument allein), und die Themen-Heatmap, falls die Stundenversion nicht deutlich mehr zeigt als der Tagesverlauf. Die Populationsschätzung (3.11) ist ein gutes, kleines Bild, aber die Tabelle in §5 tut es auch.

---

## 5. Lesbarkeit

**Farbfehlsichtigkeit.** Kategorische Farben aus einer geprüften Palette (Okabe-Ito: Orange, Himmelblau, Blaugrün, Gelb, Blau, Zinnober, Rosa — kein Rot-Grün-Paar als Bedeutungsträger); sequentielle Skalen (Heatmaps, `visualMap`) viridis-artig von hell nach dunkel, weil Helligkeit für alle Sehtypen trägt. Wo zwei Zustände unterschieden werden (Arbeit/Warten, Microsoft/Rest, mitgebracht/erfunden), zusätzlich **Form oder Linienart** kodieren: `symbol` (Kreis/Raute), `lineStyle.type` (durchgezogen/gestrichelt).

**Graustufendruck.** Dokumentierter Mechanismus: `aria: {enabled: true, decal: {show: true}}` legt Schraffuren über Balken, Flächen, Boxplots, Sankey, themeRiver (`#aria.decal`). Damit überleben 3.5, 3.8 und 3.12 den Schwarzweißdruck. Für Vektorexport `echarts.init(dom, null, {renderer: 'svg'})` (`api.html#echarts.init`), SVG in den Satz übernehmen statt Rasterbild.

**Beschriftung.** Achsentitel mit Einheit und Zeitzone („Weltzeit UTC", „Innenzeit s"); n je Panel als Text im Bild (`graphic` `text`-Element), nicht nur in der Unterschrift; jede Schwelle (n < 20, Beschnitt 16.–22.06., Überschreibung 85 → 1) im Bild oder direkt darunter. Datum als `16.06. 20:00` statt ISO, Fenster in Stunden statt Sekunden, wo es geht. Legenden nicht schweben lassen, sondern Linien direkt beschriften (letzter Punkt + `label`), wenn es mehr als drei Serien sind.

**Konvention aus dem Repo.** Wie `40_chartdata.py`: Datendateien enthalten nur Daten, Achsennamen und Marker; Farben, Schrift, Schraffur kommen aus einem Theme (`echarts.registerTheme`, `api.html#echarts.registerTheme`). Dann ist der Druck-Look eine Theme-Datei, nicht 15 Einzelentscheidungen.

---

## 6. Offene Punkte

- Themen-Heatmap: Wahl zwischen `anteil` und `anteil_bytes` ist offen; beide sind im File, die Aussage unterscheidet sich (Häufigkeit vs Volumen).
- Zahlendifferenz Populationsschätzer (CSV 911 vs MECHANIK 888) — klären, bevor 3.11 gesetzt wird.
- R6-Beobachtungszahl: CSV 85, Papier 1 — die Einzelsichtung muss als Artefakt neben der Tabelle liegen, sonst hängt das Bild an Prosa.
- Anbieter-Mapping für 3.8 fehlt als Tabelle.
- Zeitleiste des einen Überlebenden (3.5) existiert nur im Fließtext; ohne CSV kein Bild.

```
{verdict: "pass", confidence: 82, ambiguities: [
  "Themen-Heatmap: anteil (Häufigkeit) oder anteil_bytes (Volumen) als Farbwert — beide im File, nicht entschieden",
  "Populationsschätzer: CSV 911 (807–1024) vs MECHANIK 888 (787–996) — welche Zahl gilt?",
  "R6-Beobachtungen: CSV observation=85, Papier nach Einzelsichtung 1 — Überschreibung im Bild braucht ein Beleg-Artefakt",
  "Anbietergruppen (Amazon/Altafiber/Arcor/Tor) sind im WHOIS-CSV nicht als Spalte vorhanden — Mapping N/A_PENDING_REVIEWER",
  "Ref-MCP ohne Credits; alle Doku-Belege aus dem llms-documents-Spiegel via Crawl4AI, kanonische option.html-Anker nicht separat gegengelesen",
  "Fehlerbalken-Mechanismus: nicht nativ; custom renderItem laut Galerie-Titel 'Error Bar on Catesian' — Beispielcode selbst nicht gelesen"
]}
```
