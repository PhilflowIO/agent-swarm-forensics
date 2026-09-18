# Herkunft der Betreiber-Requestlogs

Diese Dateien sind **nicht unser Werk und werden von uns nicht weitergegeben.**
Der Betreiber des ProWiki (`wikiservice.at/dse`) veröffentlicht sein Requestlog
selbst und dauerhaft. Wer unsere Zahlen nachrechnen will, lädt die Dateien dort
herunter und prüft seine Kopie gegen die Summen unten; damit ist bewiesen, dass
gegen denselben Bestand gerechnet wurde, ohne dass wir fremde Daten verbreiten.
Dasselbe Verfahren benutzt das Paper bereits für den Wiki-Abzug
(`analyse/data/SHA256SUMS`, `paper/main.tex` §Data and code availability).

## Bezugsquelle

Verzeichnis: <https://www.wikiservice.at/dse/>
Abrufdatum aller acht Dateien: **17. September 2026** (lokale Änderungszeit der
Kopien: 2026-09-17 17:17 MESZ).

| Datei | URL | Bytes | SHA-256 |
|---|---|---:|---|
| `log_2604` | <https://www.wikiservice.at/dse/log_2604> | 81.128.945 | `290954658efb6e8a5b97628e4de2f9289050faf9e2b35c8c1e7292fa70c015dd` |
| `log_2605` | <https://www.wikiservice.at/dse/log_2605> | 100.489.144 | `39a49e88c39a99e9a388d11f54a22ce8f080e445d285c11147eb0b0b9aaf624f` |
| `log_2606` | <https://www.wikiservice.at/dse/log_2606> | 659.325.749 | `1dcd2537bb192e421e025848ee4d15ad25470a4d9721275f98365648ce99ca49` |
| `log_2607` | <https://www.wikiservice.at/dse/log_2607> | 258.161.919 | `395ff497d0dfc93f803593ae703958ea68eb414c5bbb29435e3cfdcdc90d97ec` |
| `refer_2604` | <https://www.wikiservice.at/dse/refer_2604> | 95.700 | `1262851eea5f0c8ac6abeb53030566e3137676a568b4d1849125637f7283bcbb` |
| `refer_2605` | <https://www.wikiservice.at/dse/refer_2605> | 92.382 | `1972a7a676234d101f41d1e1904dcb642eec5c44f6d1101943ea55ddc5d70ecb` |
| `refer_2606` | <https://www.wikiservice.at/dse/refer_2606> | 303.305 | `9d2a4fdb06fed2e55d577a2afb511ddc81ea8b070feacbd7ecb86068a936c746` |
| `refer_2607` | <https://www.wikiservice.at/dse/refer_2607> | 1.947.173 | `b0c1d9b11a43e16598349a733c549dc77c805dbb0e20c8c043ab6dc9270d969c` |

Maschinenlesbar in `SHA256SUMS` (Format von `analyse/data/SHA256SUMS`):

    cd analyse/data/betreiberlogs && sha256sum -c SHA256SUMS

## Stabilität zum Abrufzeitpunkt

Zwei Größenmessungen (`stat -c %s`) im Abstand von drei Sekunden ergaben für alle
acht Dateien identische Werte; keine Datei wuchs während des Abrufs. Die
Änderungszeit aller acht Kopien liegt in derselben Minute (2026-09-17 17:17 MESZ).

Der Server bestätigt dieselben Größen und weist alle acht Dateien als
abgeschlossene Monate aus (`curl -sIL`, 2026-09-17):

| Datei | `Content-Length` | `Last-Modified` |
|---|---:|---|
| `log_2604` | 81.128.945 | Thu, 30 Apr 2026 21:59:23 GMT |
| `log_2605` | 100.489.144 | Sun, 31 May 2026 21:59:48 GMT |
| `log_2606` | 659.325.749 | Tue, 30 Jun 2026 21:59:57 GMT |
| `log_2607` | 258.161.919 | Fri, 31 Jul 2026 21:59:55 GMT |
| `refer_2604` | 95.700 | Thu, 30 Apr 2026 20:34:31 GMT |
| `refer_2605` | 92.382 | Sun, 31 May 2026 19:39:20 GMT |
| `refer_2606` | 303.305 | Tue, 30 Jun 2026 21:58:11 GMT |
| `refer_2607` | 1.947.173 | Fri, 31 Jul 2026 21:38:19 GMT |

Jede `Last-Modified`-Zeit fällt auf die letzte Minute des jeweiligen Monats
(21:59 UTC = 23:59 Wiener Sommerzeit). Die vier von uns benutzten Monate sind
also geschlossen und werden nicht mehr fortgeschrieben.

## Warum ein späterer Abruf abweichen kann

Der Betreiber schreibt fortlaufend weiter. Am selben Tag lagen unter derselben
Adresse auch `log_2608` (247.570.599 B, `Last-Modified` 31 Aug 2026 23:26 GMT)
und `log_2609` (244.478.882 B, `Last-Modified` **17 Sep 2026 16:07 GMT**, also
wenige Minuten vor unserem Abruf) — der September wuchs beim Abruf noch. Daraus
folgt zweierlei:

1. Für die vier Vorfallsmonate April–Juli 2026 ist eine spätere Kopie
   höchstwahrscheinlich bytegleich; die Summen oben sind die Probe darauf.
2. Eine Rotation, eine nachträgliche Bereinigung oder ein Verzeichniswechsel
   beim Betreiber bleibt möglich. Schlägt `sha256sum -c` fehl, ist die fremde
   Kopie eine **andere Fassung** und nicht unsere Rechengrundlage; die Abweichung
   gehört dann benannt, nicht überrechnet.

Das Log deckt ausschließlich das Wiki `/dse` ab und enthält keine Antwortinhalte;
Seitentexte stehen im `text=`-Parameter bereits beim Betreiber als literale
Zeichenkette `text=(NN)` (Beleg und die 414 Ausnahmen:
`analyse/betreiberlogs-befunde/freigabe-und-herkunft.md`).
