# Bericht: Was veröffentlicht wird und was nicht

**Stand:** 2026-09-09 · **Erzeugt von:** `scripts/90_release_index.py`, `91_release_build.py`,
`92_release_guard.py`, `93_release_repo.py` · **Regelwerk:** `release/policy.json`

---

## Die Frage

Das Paper sagt im Abschnitt „Data and code availability" zu: weitergegeben werden abgeleitete
Ergebnisse und der Code, **nicht** der Wiki-Abzug und kein Seitentext darüber hinaus, was als
kurzes Belegzitat im Paper selbst steht. Der Artefaktbestand hält diese Zusage nicht von
selbst ein. Er ist als Arbeitsverzeichnis gewachsen, nicht als Veröffentlichung.

## Methode — warum nicht nach Spaltennamen entschieden wurde

Eine erste Sichtung nach Spaltennamen (`sentence`, `quote`, `zitat`, `sent`) hätte sechs
Dateien gefunden. Das wäre falsch gewesen: Belegspalten heißen auch `beleg`, `evidence`,
`last_delta`, `delta_auszug`, `erstbeleg_zitat`, `prosa`, und umgekehrt tragen Spalten mit
verdächtigem Namen manchmal nur unsere eigene Notiz.

Die Entscheidung fällt deshalb **empirisch**: jeder Zellwert wird im Abzug gesucht. Was dort
wörtlich steht, ist Abzugstext — egal wie die Spalte heißt. Was dort nicht steht, ist unser
eigener Text und bleibt unangetastet. Bei 40 Zeichen exakter Übereinstimmung ist ein Zufall
ausgeschlossen.

Zwei Verfeinerungen waren nötig:

* **Eingebettete Zitate.** Belegspalten stellen dem Zitat eine eigene Kennung voran
  („`Seite · Zeit · Name :: <Zitat>`"). Der ganze Wert steht nicht im Abzug, das Zitat schon.
  Gesucht wird deshalb auch stückweise, und gefunden wird die **längste zusammenhängende
  Passage**, die im Abzug steht — sie weicht einer Marke, unser Rahmen bleibt stehen.
* **Umgeformte Zeilenumbrüche.** Einige Spalten ersetzen `\n` durch `⏎` oder ` | `. Diese
  Varianten werden mitgesucht.

## Befund

| | |
|---|---|
| geprüfte Dateien | 274 |
| Spalten mit Textverdacht | 105 |
| davon **Abzugstext** | 78 |
| davon **gemischt** | 3 |
| davon **eigener Text** | 24 |
| ersetzte Zellen | 85.048 in 76 Spalten |
| ganz ausgeschlossene Dateien | 5 |

Der Spaltenbefund mit dem Beleg je Entscheidung steht in `release/spalten_befund.csv`, das
Protokoll der Eingriffe in `release/redaktionsprotokoll.csv`.

### Die fünf ausgeschlossenen Dateien

`schwarm_revisions.parquet`, `schwarm_deltas.parquet`, `schwarm_deltas_flags.parquet`,
`paper_lernkurve_revflags.parquet`, `paper_themen_flags.parquet`.

Zusammen tragen sie rund **28 MB Seitentext** in den Spalten `body`, `delta` und `prosa`. Sie
weiterzugeben wäre nicht eine Teil-, sondern die **vollständige** Weitergabe des Abzugs — der
Fehler, den die Redaktion der übrigen Tabellen gerade verhindern soll. Erzeugt werden sie von
`30_load.py`, `32_delta.py`, `34_reziprozitaet.py`, `41_lernkurve.py` und `55_dramaturgie.py`;
wer den Abzug hat, baut sie in Minuten neu.

### Ein Fund außerhalb der Fragestellung

`paper_netzblock_whois.csv`, Spalte `rdap_entities`, enthält **Klarnamen natürlicher Personen**
aus RDAP-Kontakteinträgen. Das ist kein Abzugstext und wäre der Suche entgangen; es widerspricht
aber der Zusage im Ethik-Abschnitt des Papers. Behalten werden Organisationen und
Registry-Handles, entfernt werden Personennamen (`91_release_build.py`, `nur_organisation`).

## Was ein Leser zurückbekommt

`rebuild_text.py` setzt den Text aus einem lokal heruntergeladenen Abzug wieder ein und prüft
jeden wiederhergestellten String gegen seinen Hash. Im Gegentest gegen unseren eigenen Abzug
lösen **87.046 Verweise** auf und **127.619 Zellen** kommen zeichengenau zurück — **null
Abweichungen, null leer gebliebene Zellen**.

Das war nicht der erste Stand. Drei Befunde des Wächters mussten dafür behoben werden, und
alle drei sind es wert, festgehalten zu werden:

1. **Ein festes Suchraster verfehlt kurze eingebettete Zitate.** Die Ankersuche tastete den
   Zellwert in Schritten ab; ein Zitat, das zwischen zwei Rasterpunkte fiel, blieb stehen. Die
   Suche läuft jetzt an jeder Wortgrenze. (9 gefundene Reste)
2. **Der Mittelwert über eine Spalte übersieht Spalten mit wenigen langen Zeilen.** Die
   Vorauswahl verlangte im Schnitt drei Wortzwischenräume; eine Spalte aus tausend Kennungen
   und drei Sätzen fiel durch. Entschieden wird jetzt je Zelle. (6 Reste)
3. **Eine Zelle kann mehr Fundstellen zusammenfassen, als die Schleife herauslöst.** Dahinter
   steht jetzt eine Schlussprüfung: trägt der Rest noch Abzugstext, fällt die ganze Zelle.
   (1 Rest)

Zusätzlich hält der Verweis die **Schreibweise** fest, in der eine Tabelle Zeilenumbrüche
ablegt (`|`, `⏎` oder roh). Ohne sie kam der Text zwar richtig, aber in anderer Form zurück —
397 Zellen wichen ab. Jetzt sind es null.

## Gegenprobe

`92_release_guard.py` durchsucht den gebauten Baum noch einmal von außen. Es kennt das
Regelwerk nicht und vertraut dem Bauskript nicht — es sucht schlicht. Ein Treffer in einer
Tabelle oder einer JSON-Datei ist ein Abbruchgrund.

Prosa (`BERICHT_*.md`, Codebook, `MECHANIK.md`) wird gezählt, nicht beanstandet: Belegzitate
gehören dort hin, sie sind dieselbe Klasse wie die Zitate im Paper. Der gemessene Umfang steht
im Protokoll, damit sichtbar bleibt, ob aus Belegen unbemerkt eine Textsammlung wird.

## Ambiguitäten

* **`paper_goldset_konflikte.csv`, `r1_note`/`r2_note`** — Notizen der beiden Rater, also
  unser eigener Text. Eine von 40 Stichproben stimmte trotzdem wörtlich mit einem Wiki-Satz
  überein: der Rater hat zitiert statt paraphrasiert. Die Prüfung läuft je Zelle, deshalb ist
  genau diese eine Zelle ersetzt und die übrigen stehen. Eine spaltenweite Regel hätte hier
  entweder zu viel gelöscht oder zu wenig.
* **Prosa-Berichte** — sie sind nicht redigiert. Die Entscheidung, Belegzitate dort stehen zu
  lassen, ist bewusst und entspricht dem, was das Paper selbst tut. Wer sie enger fassen will,
  hat mit der Zählung des Wächters die Zahlen dafür.
* **Seitennamen** bleiben überall stehen. Sie sind Metadaten, keine Seiteninhalte, und das
  Paper nennt sie ohnehin.

```
verdict: pass
confidence: 96
ambiguities:
  - "Prosa-Berichte sind ungeprüft weitergegeben; erlaubt, aber eine bewusste Entscheidung — <reason: Belegzitate sind dieselbe Klasse wie im Paper, eine Redaktion würde die Berichte unlesbar machen>"
  - "Der Rückbau ist gegen unseren Abzug exakt; gegen eine andere Fassung des Abzugs ist er ungeprüft — <reason: uns liegt nur eine Fassung vor; rebuild_text.py meldet den Fehlschlag je Zelle, statt zu raten>"
  - "Die RDAP-Namensfilterung entscheidet heuristisch zwischen Personen- und Organisationsnamen — <reason: RDAP kennzeichnet den Typ im Rohdatensatz, die abgeleitete Spalte trägt nur noch den Namen>"
```
