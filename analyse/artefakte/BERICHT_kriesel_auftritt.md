# Kriesel auf der Bühne — was im Transkript nicht steht

Wahrnehmungsanalyse zweier Congress-Vorträge von David Kriesel: **BahnMining** (36C3, 2019, 61:49 Aufzeichnung) und **SpiegelMining** (33C3, 2016, 58:45 Aufzeichnung). Untersucht wurde alles, was der Text nicht hergibt: Energie, Tempo, Pausen, Publikumsreaktion, Bühnenverhalten, Leinwand.

---

## 0. Material, Zeitbasis und Methode

**Video beschafft:** ja, für beide Vorträge, von media.ccc.de (direkte MP4-Links, kein Login).

| | BahnMining | SpiegelMining |
|---|---|---|
| Videodatei | `/home/philflow/Dokumente/coding/research/kriesel-video/bahnmining_sd.mp4` (720×576, Regie-Schnitt Folie/Kamera) | `/home/philflow/Dokumente/coding/research/kriesel-video/spiegelmining_sd.mp4` (720×576, Kompositbild: Folie links, Redner-Inset rechts) |
| Zusatzfeed | `bahnmining_slides.mp4` (reiner Folienfeed 1920×1080) | keiner verfügbar |
| Videodauer (ffprobe) | 3709,638 s | 3525,642 s |
| WAV-Dauer (Transkript-Metadaten) | 3709,643 s | 3525,602 s |

**Zeitversatz: keiner.** Die Dauern stimmen auf **5 bzw. 40 Millisekunden** überein, und die Stichprobe bestätigt es inhaltlich: Der SRT-Cue „Unsere Geschichte heute beginnt im Jahr 2018" endet bei 119,0 s — im Folienfeed liegt bei **exakt 119,0 s** der Folienwechsel. Alle Zeitangaben unten gelten deshalb unverändert für WAV, SRT, JSON und Video. Die YouTube-Fassungen wurden nicht gebraucht.

**Wie gemessen wurde.** Drei unabhängige Schichten, absichtlich getrennt gehalten:

1. **Akustik, deterministisch** — 100-ms-Fenster über die ganze WAV: Pegel (dB RMS), Nulldurchgangsrate, spektrale Flachheit und ein Bandverhältnis 120–400 Hz gegen 2,5–7 kHz. Das Bandverhältnis trennt Publikum von Sprecher sauber: Sprache liegt bei **+7 bis +10 dB**, Applaus bei **−6 bis −14 dB**. Damit sind Lacher/Applaus objektiv detektierbar statt geraten.
2. **Wortzeiten** aus den vorhandenen `.json` (Wortgenauigkeit, 80-ms-Raster) für Tempo, Pausen und Zahl-Positionen.
3. **Audiovisuelles Urteil** — `qwen3.5-omni-plus` über die `omni-perception`-Pipeline. Zwei Einsätze: ein **lückenloser 30-Sekunden-Scan** beider Aufzeichnungen (242 Fenster) mit der Ein-Wort-Frage „Publikumsreaktion?", und ~15 längere Fenster mit Bild (1 Frame / 2 s) für Bühne und Leinwand.

**Belastbarkeit.** Der 30-s-Scan hat die akustische Erkennung gegengeprüft: In BahnMining wurde **kein einziges** akustisch gefundenes Ereignis vom Modell als „keine Reaktion" eingestuft (0 Falschpositive), in SpiegelMining drei von 39. Umgekehrt hört das Modell **56 zusätzliche leise Reaktionen**, die unter der akustischen Schwelle liegen. Die Liste unten führt beide Klassen getrennt.

**Zwei Vorbehalte, die für alle Lautstärke-Aussagen gelten.**
- Die CCC-Tonspur ist kompressiert/limitiert. Kriesels Sprechpegel schwankt über die gesamte Stunde nur zwischen −22,4 und −14,1 dB (BahnMining) bzw. −17,4 und −14,4 dB (SpiegelMining, Vortragsteil). Ob er im Saal wirklich so gleichmäßig laut war oder ob der Limiter das eingeebnet hat, ist aus der Aufzeichnung **nicht** entscheidbar → `N/A_PENDING_REVIEWER`. Relative Verläufe sind trotzdem aussagekräftig, absolute Dynamikaussagen nicht.
- Das Publikum ist in der Mischung **leiser** als der Redner: Von den 3000 lautesten Audio-Frames sind nur 7 % (BahnMining) bzw. 2 % (SpiegelMining) Publikum. Eine reine dB-Kurve zeigt deshalb *nicht*, wo das Publikum tobt. Die Energiekurve unten misst daher zwei getrennte Größen: **Publikumssekunden pro Fünf-Minuten-Block** und **Sprechpegel**.

Alle Rohdaten und Skripte: `/home/philflow/Dokumente/coding/research/kriesel-video/analysis/`.

---

# TEIL A — BahnMining (36C3)

Struktur der Aufzeichnung: 0:00–0:45 Anmoderation · 0:46–0:58 Einzugsapplaus · **0:58–49:38 Vortrag** · 49:38–50:32 Schlussapplaus (53,8 s) · 50:35–61:49 Fragerunde.

## A1. Energiekurve über den ganzen Vortrag

Fünf-Minuten-Auflösung. „Publikum" = summierte Sekunden hörbarer Publikumsreaktion; „Sprechpegel" = 75. Perzentil des Sprachpegels; „Tempo" = Wörter pro Minute brutto.

| Block | Publikum (s) | Sprechpegel | Tempo (W/min) | Charakter |
|---|---|---|---|---|
| 00–05 | 21,5 | −19,4 | 134 | Anlauf, Einzugsapplaus dominiert |
| 05–10 | 20,1 | −18,8 | 159 | erste eigene Lacher, erster großer Applaus |
| 10–15 | 12,8 | −18,6 | 151 | Publikumsdialog, dann Absacken |
| 15–20 | 10,2 | −18,6 | **171** | schnellster Block, Technik-Exkurs |
| 20–25 | 13,2 | −18,3 | 151 | Datenbeschaffung |
| 25–30 | 25,0 | −18,1 | 160 | **Doppel-Peak**: Bahn-Genehmigung |
| 30–35 | 6,7 | −18,0 | 141 | **Tal** — die Flipbook-Animation |
| 35–40 | 27,4 | −18,0 | 137 | Peak: Kennzahlen-Kritik |
| 40–45 | 28,7 | −18,3 | 150 | Peak: Ausfall-Muster |
| 45–50 | 41,1 | −18,1 | 130 | langsamster Block, Finale |
| *50–62* | *43,9 / 8,8* | *−18,1 / −17,6* | *152 / 155* | *Fragerunde* |

**Die fünf stärksten Momente** (gemessen an Dauer und Pegel der Publikumsreaktion):

1. **49:38 — 53,8 s Applaus, Standing Ovations.** Nach „…da kann die Bahn mit mir machen, was sie will, und ich bedanke mich, dass ihr hier wart." Der Moderator bestätigt es später explizit (52:01: „der Stream schließt sich den Standing Ovations an"). **Publikum**, mit Abstand das längste Ereignis der Aufzeichnung.
2. **26:56 — 11,7 s Applaus.** Nach „Ich habe dann gepokert und wirklich bei der Bahn nachgefragt, ob ich automatisiert Daten runterladen und darüber einen kleinen Community-Vortrag halten darf." **Publikum.** Er setzt sofort nach: 23 Sekunden später (**27:19, 10,7 s**) fordert er den zweiten Applaus selbst ein — „das könnte jetzt mal ein Applaus für die Bahn wert sein" — und bekommt ihn. Zwei Elf-Sekunden-Applause in 23 Sekunden ist die dichteste Stelle des Vortrags.
3. **36:18 — 11,4 s Applaus.** Nach dem Gegenvorschlag zur Bahn-Kennzahl: „…wir zählen alle Stopps, die geplant waren, und messen davon den Prozentsatz, der angekommen ist und pünktlich war." **Publikum** — Applaus für eine Formel, nicht für einen Witz.
4. **24:19 — 10,4 s Applaus** nach dem trockenen Zweiwort-Nachsatz „Habe ich gehört." **Publikum.**
5. **45:09 — 9,3 s Applaus.** „Also bitte behandelt diese Daten, als wären sie mit Xeroxgeräten gescannt." (Rückverweis auf seinen eigenen berühmten 31C3-Vortrag.) **Publikum.**

**Liegt eine Spitze an ihm oder am Publikum?** In dieser Aufzeichnung: **immer am Publikum.** Sein eigener Pegel bewegt sich über die zehn Blöcke innerhalb von 1,4 dB — das ist unterhalb der Wahrnehmungsschwelle für „lauter werden". Es gibt genau **eine** Ausnahme in die andere Richtung: bei **46:40** fällt sein Sprechpegel auf **−22,4 dB**, den niedrigsten Wert des ganzen Abends, gut 5 dB unter seinem Normalpegel. Das ist die Passage direkt nach der langen Denkpause (siehe A7). Er wird nie lauter — er wird einmal deutlich leiser, und zwar am dramaturgisch wichtigsten Punkt.

## A2. Lacher und Applaus, vollständig

**48 Publikumsmomente** im Vortragsteil (0:58–49:38): 28 akustisch vermessen, 20 zusätzlich vom AV-Modell gehört. Das ist **ein Publikumsmoment alle 61 Sekunden** (Median-Abstand 51 s). Längste Durststrecke: **215 s** (27:19 → 30:54) — exakt die Passage mit dem Datenprojekt-Regelwerk und dem Beginn der Animation.

Spalte „Vorlauf" = Zeit zwischen seinem letzten Wort und dem Einsetzen der Reaktion. Negative Werte heißen: Das Publikum reagiert, während er noch spricht.

| Zeit | Dauer | Art | Stärke | Vorlauf | Satz unmittelbar davor |
|---|---|---|---|---|---|
| 00:46 | 12,2 s | Applaus | stark | 0,95 s | „Bitte begrüßen mit einem Riesenapplaus David Kriesel." (Anmoderation) |
| 01:16 | – | Lachen | leise | – | „…herzlich willkommen an die Alu-Hüte im Besonderen." |
| 02:37 | – | Lachen | leise | – | „…und das wären bei knapp 75 %" |
| 03:06 | – | Lachen | leise | – | „…habe ich diese E-Mail von verspätungsalarm@bahn.de, und da dachte ich…" |
| **03:57** | **6,7 s** | Applaus | stark | **2,76 s** | „Also habe ich am 8. Januar begonnen, die Deutsche Bahn zu vorratsdatenspeichern." |
| **05:55** | **8,1 s** | Applaus | stark | 0,80 s | „…und am Berliner Flughafen, der Stopp fällt aus. In 20 Jahren werde ich diese Witze immer noch machen können." |
| 06:02 | – | Applaus | leise | – | (Ausklang desselben) |
| 08:07 | 3,8 s | Applaus | mittel | 0,47 s | „…als erstes sieht man, in Ostdeutschland ist quasi alles blau." |
| 08:45 | – | Lachen | leise | – | „…die simple Wahrheit…" |
| 09:55 | 1,2 s | Applaus | kurz | 0,08 s | „…aber deutlich weniger als im Fernverkehr." |
| 09:58 | 3,2 s | Applaus | mittel | −0,07 s | „Und jetzt, ich hoffe, die Leute von der Bahn hören…" |
| 10:49 | 1,0 s | Lachen | kurz | 0,38 s | „Ich höre, wir haben eine Frankfurt-Fraktion, wie seid ihr hergekommen?" |
| 11:13 | 3,7 s | Applaus | mittel | **2,23 s** | „Die Top drei sind Bremen, Berlin-Hauptbahnhof und Berlin-Spandau." |
| 11:28 | 0,9 s | Lachen | kurz | 0,30 s | „Es gibt tatsächlich etwas an Berlin, das funktioniert." |
| 13:58 | – | Lachen | leise | – | „…Eurocity gut zwei Prozent, Intercity gut drei % und ICE über fünf %." |
| 14:44 | – | Lachen | leise | – | „…bis die Bahn widerspricht. Übrigens, einer der fettesten…" |
| 15:45 | – | Lachen | leise | – | „Ich mache das jeden Vortrag, aber ich war besser…" |
| **16:14** | **6,8 s** | Applaus | stark | 0,88 s | „…baut nicht nur ein Download-Monitoring, sondern lasst das auch noch auf einem anderen Server laufen als den Download selbst." |
| 18:05 | 0,8 s | Lachen | kurz | 0,37 s | „Und jetzt, wo es kälter wird, fängt das auch wieder so an." |
| 19:42 | – | Lachen | leise | – | „…so fair müssen wir schon sein." |
| 20:47 | – | Lachen | leise | – | „…da scheint die Bahn die Dinger irgendwie aufzugeben." |
| 21:51 | – | Lachen | leise | – | „In den Fahrplänen steht, wann welcher Zug ankommen soll…" |
| 23:13 | 1,4 s | Lachen | mittel | 0,42 s | „…40 Gigabyte XML landen am Tag. Ja, das passt sich auch nicht mehr von alleine…" |
| 23:31 | – | Lachen | leise | – | „…kriegen die Admins der Bahn vermutlich einen Herzanfall…" |
| **24:19** | **10,4 s** | Applaus | stark | 0,36 s | „…die sind erstaunlich schwach auf Verbus. **Habe ich gehört.**" |
| 25:20 | – | Lachen | leise | – | „…in der Fachsprache heißen die anonyme Proxies." |
| 25:45 | – | Lachen | leise | – | „…meine Abfragen in ihren Logs zu suchen, und ich freue mich…" |
| **26:56** | **11,7 s** | Applaus | stark | −0,22 s | „…ob ich automatisiert Daten runterladen und darüber einen kleinen Community-Vortrag halten darf." |
| **27:19** | **10,7 s** | Applaus | stark | −0,27 s | „…das könnte jetzt mal ein Applaus für die Bahn wert sein." |
| 30:54 | 2,0 s | Lachen | mittel | −0,09 s | „…an dem Tag war ja was. Und hier zeigt der Orkan Eberhard erste Auswirkungen." |
| 33:41 | – | Lachen | leise | – | „Und jetzt schauen wir mal in die Unterlagen der Bahn dazu…" |
| 34:37 | – | Lachen | leise | – | „Das heißt, wir haben insgesamt 103 % Fernverkehr." |
| **35:13** | **9,4 s** | Applaus | stark | 1,34 s | „…ich nenne sowas den finalen Rettungsstuss." |
| **36:18** | **11,4 s** | Applaus | stark | −0,28 s | „…wir zählen alle Stopps, die geplant waren, und messen davon den Prozentsatz, der angekommen ist und pünktlich war." |
| 37:14 | – | Lachen | leise | – | „…dann schafft ihr Anreize, die das Unternehmen in eine unerwartete Richtung lenken." |
| 37:45 | – | Lachen+Applaus | leise | – | „…um damit die Pünktlichkeitsstatistik zu pushen? **Ihr klatscht ja schon vorher**…" |
| 38:26 | 0,9 s | Lachen | kurz | 0,28 s | „Und wer in den roten Stopps einsteigen und aussteigen will…" |
| 39:13 | 0,8 s | Lachen | mittel | −0,08 s | „…machen wir getrennte Auswertungen." |
| 39:33 | – | Lachen | leise | – | „Und beim ICE dagegen fallen die ersten und letzten Stopps…" |
| **40:42** | **4,5 s** | Applaus | stark | **2,80 s** | „…es liegt mir fern, da von der Seitenlinie ohne tieferes Wissen altkluge Ratschläge zu erteilen, wir sind hier nicht auf Twitter." |
| **42:55** | **9,0 s** | Applaus | stark | 1,13 s | „…und das wäre doch total cool, wenn man die vorher wissen könnte." |
| 43:16 | 1,2 s | Lachen | kurz | **2,98 s** | „…und es gibt auch Wochentage, bei denen sowas häufiger auftritt." |
| 43:52 | 1,2 s | Lachen | mittel | 0,65 s | „…damit ich jetzt gleich platzsparend arbeiten kann." |
| **44:25** | **8,3 s** | Applaus | stark | 0,13 s | „…und herausgekommen sind fast 500 Kombinationen aus Wochentagen, Bahnhöfen und Zügen." |
| 45:01 | 0,9 s | Lachen | kurz | 0,22 s | „Ich bin nicht schuld, wenn ihr unverhofft doch pünktlich zum Zug eintreffen müsst…" |
| **45:09** | **9,3 s** | Applaus | stark | −0,15 s | „Also bitte behandelt diese Daten, als wären sie mit Xeroxgeräten gescannt." |
| **46:08** | **8,8 s** | Applaus | stark | 0,53 s | „…seid nett zur Bahn mit ihren Fehlern, wir haben nur diese eine. **Und was bleibt?**" |
| 49:09 | – | Lachen | leise | – | „…wo die allermeisten Menschen sich die Flasche Wein an den Hals anschließen." |
| **49:38** | **53,8 s** | Applaus | stark | 0,49 s | „…ich bedanke mich, dass ihr hier wart und wünsche euch ein schönes neues Jahr(zehnt)." |

*Fragerunde (nicht mitgezählt): 52:01 leiser Applaus, 54:25 3,5 s, 54:36 leises Lachen, 56:01 leises Lachen, 56:57 5,0 s, 58:04 leises Lachen, 61:20 Schlussapplaus.*

**Was die Liste zeigt.** Applaus folgt bei Kriesel viermal so oft auf eine **Sachaussage** wie auf einen Gag: der Gegenvorschlag zur Kennzahl (36:18), der Praxistipp zum Monitoring (16:14), die Bahn-Genehmigung (26:56), die Twitter-Absage (40:42). Der klassische Lacher — kurz, unter 1,5 s — steht fast immer auf einem **trockenen Nachsatz** von zwei bis fünf Wörtern: „Habe ich gehört.", „Es gibt tatsächlich etwas an Berlin, das funktioniert.", „…den finalen Rettungsstuss."

## A3. Pausen

**30 echte Stillepausen ≥ 1,5 s** im ganzen Mitschnitt (Wortlücke ohne Publikumsgeräusch, Pegel unter −33 dB). Zum Vergleich: Der Median aller Wortabstände liegt bei **0,00 s** — er spricht ohne Zwischenraum, Pausen sind bei ihm ein bewusst gesetztes, seltenes Mittel, kein Nebenprodukt.

Die längsten:

| Zeit | Dauer | davor | danach |
|---|---|---|---|
| **46:38** | **9,0 s** | „…was für ihn in diesem Jahrzehnt die maßgebliche gesellschaftliche Entwicklung war." | „Ich glaube, hat jeder was." |
| 37:40 | 4,5 s | „…um damit die Pünktlichkeitsstatistik zu pushen?" | „Ihr klatscht ja schon vorher, so kann ich…" |
| **05:00** | **4,2 s** | „…für den ersten Überblick, und danach erkläre ich sie." | „Drei Sekunden reichen auch. So, der ICE fährt…" |
| 38:43 | 3,6 s | „Aber wie könnte man sowas messen? Ganz einfach." | „Hamburg. Hamburg, oh ja." |
| 33:33 | 3,5 s | „Eieiei, ja, das sind so ziemlich alle." | „Und so sehe ich das eigentlich auch." |
| 34:38 | 3,0 s | „…wir haben insgesamt 103 % Fernverkehr." | „Aber vor allem, vielleicht ist die Erfüllungsquote auch…" |
| 30:48 | 2,6 s | „…an dem Tag war ja was." | „Und hier zeigt der Orkan Eberhard erste Auswirkungen." |
| 21:02 | 2,4 s | „…von vierzig Minuten erweckt ein anderes Transportmittel." | „So, das war ein Höllenritt." |
| 17:10 | 2,2 s | „…bevor der alles vorwegnimmt." | „Und das machen wir jetzt nicht mehr auf…" |

**Wozu die Pausen dienen.** Bei **33 %** folgt unmittelbar ein Gliederungswort („So", „Also", „Und", „Aber", „Jetzt"). Die Pause ist bei ihm also überwiegend ein **Kapitelumbruch**, kein Effekt.

Zwei Sonderformen, beide sehenswert:
- **Die Lesepause (05:00, 4,2 s).** Er hat gerade eine Datentabelle auf die Leinwand gelegt und angekündigt, sie erst zeigen und dann erklären zu wollen. Dann schweigt er 4,2 Sekunden, damit der Saal lesen kann, und kommentiert das anschließend selbst: „Drei Sekunden reichen auch."
- **Die Denkpause (46:38, 9,0 s).** Vorher, wörtlich: „Ich lasse euch jetzt mal ein paar Sekunden in Ruhe und wünsche mir, dass jeder kurz darüber nachdenkt, was für ihn in diesem Jahrzehnt die maßgebliche gesellschaftliche Entwicklung war." Dann neun Sekunden vollständige Stille (per AV-Modell gegengeprüft: „nur leises Raumgeräusch"). Danach, leiser als sonst: „Ich glaube, hat jeder was."

**Pause vor der Zahl oder danach? — Weder noch, und das ist das überraschendste Einzelergebnis dieser Analyse.** Über 431 Zahlwörter im BahnMining-Transkript:

| | vor dem Zahlwort | nach dem Zahlwort | Basisrate aller Wörter |
|---|---|---|---|
| Anteil Lücke > 0,5 s | **1,6 %** | 2,8 % | 3,8 % |
| Median-Lücke | 0,000 s | 0,000 s | 0,000 s |

Vor einer Zahl macht er **seltener** eine Pause als vor einem beliebigen anderen Wort. Von den 30 langen Pausen führen nur 3 direkt auf eine Zahl hin. Kriesel inszeniert Zahlen **nicht** akustisch. Die Zahl steht mitten im Satz, im normalen Redefluss — die Betonung kommt von der Folie (siehe A5), nicht von der Stimme.

## A4. Tempo und Lautstärke als Mittel

Durchschnitt: **2,54 Wörter/Sekunde brutto**, **3,36 W/s Artikulationsrate** (nur Sprechzeit, Pausen herausgerechnet).

**Langsamste 30-Sekunden-Fenster:** 49:30 (0,97 W/s — Schlussapplaus), 30:00 (1,13 — die Animation, er kommentiert nur sparsam), 46:30 (1,33 — die Denkpause), 36:00 (1,37), 27:00 (1,60).
**Schnellste:** 13:00 (3,47), 04:30 (3,47), 06:30 (3,30), 18:30 (3,27) — durchweg Erklärstrecken.

**Das Pointen-Muster — und was daran nicht stimmt, was man erwarten würde.** Die Messung über alle 28 Publikumsreaktionen:

| Größe | 6 s vor der Reaktion | 12–6 s davor |
|---|---|---|
| Bruttotempo | **2,09 W/s** | 2,72 W/s |
| Artikulationsrate | **3,51 W/s** | 3,43 W/s |
| Sprechpegel | −18,7 dB | −18,6 dB |

Brutto wird er vor der Pointe um **23 % langsamer** — netto, also beim tatsächlichen Sprechen, **nicht**; er ist sogar minimal schneller. Und leiser wird er auch nicht (0,1 dB Unterschied ist nichts). Die gesamte Verlangsamung entsteht durch **eingefügte Stille**. Kriesels Pointensetzung besteht nicht aus „Tempo runter, Lautstärke runter, Pause" — sie besteht aus genau einer Zutat: **er hört auf zu reden**. Bei **50 %** aller Reaktionen liegt zwischen seinem letzten Wort und dem Einsetzen des Lachens mehr als eine halbe Sekunde; Median 0,38 s.

Drei Belegstellen:
- **24:19** — „…die sind erstaunlich schwach auf Verbus." Dann 1,6 s Stille. Dann, im gleichen Tonfall und gleicher Lautstärke: „Habe ich gehört." → 10,4 s Applaus. Kein Tempowechsel, keine Betonung, nur die Lücke davor.
- **40:42** — nach dem langen Satz über die Geschäftsentscheidung der Bahn endet er auf „…wir sind hier nicht auf Twitter." und wartet **2,8 s**, bevor der Applaus einsetzt. Er hält die Stille aus, statt nachzuschieben.
- **37:40** — 4,5 s Stille nach der rhetorischen Frage. Das Publikum fängt an zu klatschen, und er kommentiert es: „Ihr klatscht ja schon vorher, so kann ich…" Der einzige Moment, in dem er die Mechanik selbst offenlegt.

## A5. Bühne und Leinwand

**Folienwechsel: 64 im Vortragsteil, im Mittel alle 45,6 s** (Median-Abstand 34 s, gemessen per Szenendetektion auf dem reinen Folienfeed). Diese Durchschnittszahl verschleiert allerdings das Interessanteste — die Verteilung ist extrem ungleich. Ablesbar an den eingeblendeten Foliennummern:

| Zeitpunkt | Folie | | Zeitpunkt | Folie |
|---|---|---|---|---|
| 03:20 | 2 | | 28:20 | 24 |
| 08:20 | 5 | | **30:00** | **36** |
| 13:20 | 8 | | **30:50** | **68** |
| 18:20 | 12 | | **31:40** | **77** |
| 23:20 | 17 | | 36:40 | 78 |
| 26:40 | 22 | | 48:20 | 90 |

**Zwischen 30:00 und 31:40 laufen rund 41 Folien in 100 Sekunden durch — ein Daumenkino.** Das AV-Modell beschreibt den Inhalt: eine animierte Deutschlandkarte, die den Verspätungs- und Ausfallverlauf über zwei Tage im Zeitraffer zeigt, blaue Punkte, die zu großen roten werden; spät im Ausschnitt blendet ein Meme-Bild („Eberhardt (Archivbild)") ein, genau als er den Orkan erwähnt. Das ist die einzige echte Animation des Vortrags und zugleich der Fünf-Minuten-Block mit den **wenigsten** Publikumsreaktionen (6,7 s) und dem **niedrigsten** Sprechtempo. Er lässt das Bild arbeiten und redet dazu fast nichts.

Der Rest der Folien steht dagegen **sehr lange**: Die Schlussfolie („Zum Jahrzehnt", ein Strichmännchen vor einem Rechner, Foliennummer 90) erscheint um **46:09** und bleibt bis zum Ende — **dreieinhalb Minuten auf einem einzigen Cartoon**, während er den inhaltlich schwersten Teil des Vortrags hält.

**Wechsel vor oder nach dem Satz?** Weder noch — **mittendrin**. Von 64 Wechseln fallen **48 (75 %)** in ein laufendes Wort, nur 16 in eine Sprechpause. Median-Position im gerade laufenden Satz: **60 % durch**. Das Bild kommt also unter dem Satz an, nicht davor und nicht danach.

Der präziseste Einzelbeleg — und die Antwort darauf, wie er Zahlen doch betont: Bei **01:59,0** wechselt die Folie auf eine Wand aus Bahn-Pressetext, exakt beim Wort „2018". Bei **02:05,2** erscheint die Sprechblase „Jahrespünktlichkeit von 74,9 % für 2018", und die rot markierte Zahl im Textblock; er sagt „rund 75 %" bei **02:05,6**. Die Zahl steht **0,4 Sekunden vor dem gesprochenen Wort** auf der Leinwand. Die Pause vor der Zahl, die er stimmlich nicht macht, macht er visuell.

Über den ganzen Vortrag fällt bei **23 %** aller Folienwechsel innerhalb von ±3 s ein Zahlwort — Bild und Zahl sind gekoppelt.

**Körperlich** (AV-Modell, sieben Fenster über den Vortrag, konsistente Beschreibung): Er steht **durchgehend am Pult**, Laptop und Wasserflasche darauf. Gestik minimal, meist nur die rechte Hand knapp über dem Pult. Er **dreht sich nie zur Leinwand um**; ein Zeigen zur Leinwand wurde in genau einem Fenster beobachtet (um 10:30, „Hier seht ihr…"). Blick pendelt zwischen Laptop und Publikum. Bei Pointen: kein sichtbarer Körpereinsatz, allenfalls ein kurzes Lächeln. Erst **nach** dem Schlusssatz verlässt er das Pult und stellt sich neben die Leinwand.

**Live-Demos: keine.** Der einzige dynamische Programmteil ist die vorproduzierte Karten-Animation (30:00–31:40, ca. 100 s). Außerdem gibt es zwei **Publikumsinteraktionen**, die als Live-Element funktionieren: 10:34 „Ich höre, wir haben eine Frankfurt-Fraktion, wie seid ihr hergekommen?" mit Zurufen aus dem Saal, und 33:18 eine Handzeichen-Abstimmung („Wer von euch würde sagen, der ist eher pünktlich? — Die zwei Hände, drei im Saal von 5000").

## A6. Der Einstieg, minutengenau

| Zeit | Was passiert |
|---|---|
| 00:00–00:32 | Saal, kein Sprechen. |
| 00:32–00:45 | Anmoderation; Erwähnung, dass Spiegel Online „eine total perfekte Datenanalyse" geliefert habe. |
| **00:45,6–00:57,8** | **Einzugsapplaus, 12,2 s.** |
| **00:58,7** | Erster Satz — und er ist eine Reaktion auf den Applaus, kein Vorbereitetes: „Also ich glaube, so geil bin ich noch niemals eingeleitet worden." |
| 01:04,6 | „Ja, herzlich willkommen euch allen hier, auch herzlich willkommen an die Leute im Stream und an die Alu-Hüte im Besonderen." |
| **01:16** | **Erster Lacher** — leise, auf „Alu-Hüte" (nur AV-Modell; akustisch bei −34,7 dB unter der Messschwelle). |
| bis 01:58 | Titelfolie steht. Kein Datenbild. |
| **01:58,3** | **Erste Zahl: „2018"** — sechzig Sekunden nach seinem ersten Wort. Satz: „Unsere Geschichte heute beginnt im Jahr 2018." |
| **01:59,0** | **Erste Datenfolie.** Eine Wand aus Bahn-Pressetext, unlesbar klein — der visuelle Gag ist die Textwüste selbst. |
| **02:05,2 / 02:05,6** | Einblendung „Jahrespünktlichkeit von 74,9 % für 2018" (Bild) / „rund 75 % ihrer Fernzüge seien pünktlich" (Ton). Bild 0,4 s vor Ton. |
| 02:20 | Die Definition: „…weniger als sechs Minuten zu spät, dann ist er pünktlich." |
| 02:30–03:00 | Erste deutliche Lachwelle (AV-Modell), akustisch schwach bei 02:37. |
| 03:03 / 03:14 | Zwei Pausen à 1,8 s um die Lotto-Pointe („…während er den Sechser im Lotto abholt"). |
| **03:57,0** | **Erster starker Applaus, 6,7 s** — nach „…die Deutsche Bahn zu vorratsdatenspeichern". Er wartet **2,76 s** nach seinem letzten Wort, bis er einsetzt. |
| 04:51 | Folienwechsel auf die Beispiel-ICE-Fahrt (Tabelle, Folie 3). |
| **05:00,3** | **4,2 s Stille** zum Lesen. Danach: „Drei Sekunden reichen auch." |
| 05:52–06:03 | Lacher, dann **8,1 s Applaus** auf „In 20 Jahren werde ich diese Witze immer noch machen können." |

Dramaturgisch: Erst nach zwei Minuten die erste Zahl, erst nach vier Minuten der erste große Applaus. Die ersten fünf Minuten sind der langsamste Block des Vortrags (134 W/min).

## A7. Der Schluss, minutengenau

| Zeit | Was passiert |
|---|---|
| 44:25 | 8,3 s Applaus nach „…fast 500 Kombinationen aus Wochentagen, Bahnhöfen und Zügen." |
| 45:01 | Kurzer Lacher: „…weil die Kiste halt pünktlich ist." |
| **45:09** | **9,3 s Applaus** — „behandelt diese Daten, als wären sie mit Xeroxgeräten gescannt." |
| 45:56–46:04 | „…seid nett zur Bahn mit ihren Fehlern, wir haben nur diese eine." |
| 46:06 | Drei Wörter allein auf der Zeile: **„Und was bleibt?"** |
| **46:08** | **8,8 s Applaus.** |
| **46:09,4** | **Letzter Folienwechsel des Vortrags**: „Zum Jahrzehnt", Strichmännchen am Rechner, Foliennummer 90. Ab hier läuft der ganze Rest auf einem Bild. |
| 46:16 | „Einen habe ich noch." |
| 46:20 | „Das hier ist der letzte Vortrag, den ich in diesem Jahrzehnt halten werde." |
| 46:26–46:38 | Die Ansage: „Ich lasse euch jetzt mal ein paar Sekunden in Ruhe und wünsche mir, dass jeder kurz darüber nachdenkt, was für ihn in diesem Jahrzehnt die maßgebliche gesellschaftliche Entwicklung war." |
| **46:38–46:47** | **9,0 s Stille.** Nichts auf der Leinwand ändert sich, er sieht nach unten. |
| **46:47** | „Ich glaube, hat jeder was." — bei **−22,4 dB** die leiseste Passage der ganzen Aufzeichnung. |
| 46:49–49:00 | Der Empörten-Teil. **Kein einziger Publikumslaut zwischen 46:17 und 49:09** — die längste reaktionslose Strecke der Schlussphase, 2:52 min. |
| 49:09 | Leises Lachen („…die Flasche Wein an den Hals anschließen"). |
| 49:20 | „Und warum tun die 5000 Leute das?" → 49:24 „Um einen Statistikvortrag zu hören." → **1,8 s Pause** → 49:28 „Ja, das gibt mir Hoffnung." |
| **49:38** | Schlusssatz endet. **53,8 s Applaus**, laut Moderator Standing Ovations. |
| — | **Letztes Bild:** kein Dank-Slide, keine Links — der Strichmännchen-Cartoon „Zum Jahrzehnt" bleibt stehen, während er das Pult verlässt und sich neben die Leinwand stellt. |

---

# TEIL B — SpiegelMining (33C3)

Struktur: 0:13–0:57 Anmoderation mit Applaus · **1:02–46:41 Vortrag** · 46:41–47:04 Schlussapplaus (22,5 s) · 47:03–58:45 Fragerunde.

## B1. Energiekurve über den ganzen Vortrag

| Block | Publikum (s) | Sprechpegel | Tempo (W/min) | Charakter |
|---|---|---|---|---|
| 00–05 | 36,2 | −17,0 | 129 | Anmoderation + Einstieg, viel Applaus |
| 05–10 | 18,1 | −17,1 | 161 | Datenüberblick |
| 10–15 | 25,9 | −16,9 | 155 | **Peak-Zone**: Redaktionsalltag |
| 15–20 | 14,2 | −16,7 | **163** | schnellster Block, Metadaten-Warnung |
| 20–25 | 14,6 | −16,8 | 151 | Keyword-Landkarte |
| 25–30 | 22,2 | −16,7 | 158 | Themenkarte, Weltbild |
| 30–35 | 12,1 | −16,8 | 157 | Kommentierbarkeit |
| 35–40 | 12,2 | −16,6 | 148 | **Tal** — Werbe-/Manipulationsteil |
| 40–45 | 29,7 | −16,7 | 138 | Peak: Appell + Versionsvergleich |
| 45–47 | 35,0 | −17,0 | 146 | Finale |
| *47–59* | *…* | *−17,0* | *170/112* | *Fragerunde, sehr reaktionsreich* |

**Die fünf stärksten Momente:**

1. **46:41 — 22,5 s Applaus** nach „Hier sind noch die Links und bis dann." **Publikum.** (Deutlich kürzer als der BahnMining-Schlussapplaus; hier folgt aber direkt die Fragerunde, und ganz am Ende der Aufzeichnung, 58:00, kommt noch einmal 12,5 s.)
2. **45:42 — 12,5 s Applaus mit Pfiffen und Jubelrufen** (AV-Modell) auf einen Satz aus drei Wörtern: **„Rohdaten sind geil."** Die stärkste Reaktion innerhalb des Vortrags. **Publikum.**
3. **05:37 — 12,5 s Applaus** auf die Februar-Pointe: „…und der Grund ist, dass ein Monat mit Ä ist." **Publikum.** Bemerkenswert früh — Minute fünf.
4. **41:56 — 9,6 s Applaus** auf den gesellschaftlichen Appell: „…wenn wir wirklich jeden Mist ins Facebook oder ähnliche Plattformen pumpen, dann haben wir nichts gewonnen." **Publikum.**
5. **27:57 — 8,9 s Applaus** auf „…und dem Rest der Welt etwas entrückt, ist die Wissenschaft." **Publikum.**

Auch hier gilt: **alle** Spitzen sind Publikumsspitzen. Sein Sprechpegel bewegt sich über den gesamten Vortragsteil in einem Korridor von **3 dB** (−17,4 bis −14,4). Es gibt in SpiegelMining **keine** Stelle, an der er hörbar lauter oder leiser wird — das Gegenstück zum BahnMining-Schlussflüstern fehlt.

## B2. Lacher und Applaus, vollständig

**47 Publikumsmomente** im Vortragsteil (1:02–46:41): 22 akustisch vermessen, 25 zusätzlich vom AV-Modell gehört — **einer alle 58 Sekunden** (Median-Abstand 44 s). Längste Durststrecke: **290 s** (33:58 → 38:48), der Werbe- und Manipulationsteil.

| Zeit | Dauer | Art | Stärke | Vorlauf | Satz unmittelbar davor |
|---|---|---|---|---|---|
| 00:28 | 8,3 s | Applaus | stark | 0,87 s | „…wo er den berühmten Xerox-Scanning-Bug-Vortrag gehalten hat." (Anmoderation) |
| 00:53 | 8,6 s | Applaus | stark | 0,53 s | „Um einen ganz, ganz herzlichen Applaus." |
| 01:21 | – | Applaus | leise | – | „…ich bin Informatiker aus Bonn…" |
| **01:40** | **5,9 s** | Applaus | stark | 1,59 s | „Und seit 2014 habe ich knapp hunderttausend Artikel von Spiegel Online **gevorratsdatenspeichert**." |
| 02:03 | – | Lachen | leise | – | „…heute ist die Rede von Lügenpresse und Fake News…" |
| 04:56 | 3,8 s | Lachen+Applaus | mittel | 1,35 s | „Ich weiß, was fliederfarben ist, ich höre schon Leute lachen." |
| **05:37** | **12,5 s** | Applaus | stark | 0,78 s | „…der Grund ist, dass ein Monat mit Ä ist." |
| 09:10 | – | Lachen | leise | – | „…zu den unchristlichen Zeiten wird viel weniger veröffentlicht, bahnbrechende Erkenntnis." |
| 09:35 | – | Lachen | leise | – | „…rote Blöcke lange Texte, blaue eher kurze, und zack." |
| 10:19 | 1,5 s | Lachen | kurz | 1,02 s | „…dass die Leutchen aus dem Kulturressort morgens gerne ein bisschen länger pennen?" |
| **10:34** | **5,2 s** | Applaus | stark | **4,06 s** | „…wir haben einen Raum von 1600 Leuten, der ist poppenvoll, und fast alle haben die Hand gehoben, und die Lösung ist: stimmt." |
| 10:50 | 1,5 s | Lachen | mittel | −0,14 s | „…in der unteren Verteilung sind die Kulturartikel…" |
| **10:57** | **7,1 s** | Applaus | stark | 0,81 s | „…die gehen mindestens zwei Stunden später los. **Aber zum Ausgleich gehen die auch früher nach Hause.**" |
| 12:12 | – | Lachen | leise | – | „…wird ein bisschen politisch inkorrekt." |
| 13:01 | – | Lachen | leise | – | „…dass es da Grüppchen von Autoren gibt, die sich dichter…" |
| **13:44** | **6,7 s** | Applaus | stark | −0,03 s | „…das ist die Kinderausgabe vom Spiegel, wer das nicht kennt." |
| 15:06 | – | Lachen | leise | – | „…wir wissen bei denen umgekehrt auch relativ gut, wann die Urlaub machen." |
| 15:53 / 16:02 | – | Lachen | leise | – | „Das sind die Pärchenkandidaten…" / „…99 % des Weges zum Ziel." |
| 17:11 | – | Lachen | leise | – | „…wann ihr auf welchen Webseiten wart. Keine Inhalte." |
| **18:09** | **7,7 s** | Applaus | stark | **2,26 s** | „…die Infrastruktur für eine Generalüberwachung, die selbst George Orwells Big Brother die Schamesröte ins Gesicht treiben würde." |
| 18:35 | – | Lachen | leise | – | „…damit sich eure Laune wieder hebt." |
| 19:25 / 19:32 | – | Lachen | leise | – | „…fünf Worte, das ist ein Name." / „…ja, what the fuck." |
| 20:27 | – | Lachen | leise | – | „…bei den langen Artikeln ist es auch nur ca. zwei Prozent." |
| **20:43** | **5,8 s** | Applaus | stark | −0,13 s | „Wenn ihr kurze Agenturmeldungen wollt, sind die Kürze gut." |
| **22:29** | **4,9 s** | Applaus | stark | **2,35 s** | „…und dann gibt es noch einen interessanten Mittelweg." |
| 25:58 | – | Lachen | leise | – | „…und wir zoomen immer und immer mehr raus." |
| **26:17** | **7,9 s** | Applaus | stark | 0,46 s | „…und von da geht's über den islamistischen Terror weiter nach Frankreich." |
| 27:03 | – | Lachen | leise | – | „…das ist die Flüchtlingsthematik, die ist mittlerweile so groß…" |
| **27:57** | **8,9 s** | Applaus | stark | 1,29 s | „…und dem Rest der Welt etwas entrückt, ist die Wissenschaft." |
| 28:43 | 0,7 s | Lachen | kurz | 0,08 s | „Das Gelächter geht los, bevor ich etwas gesagt habe — ihr wisst doch gar nicht, was ich sagen will." |
| 29:03 | – | Lachen | leise | – | „…wenn ich sage, dass das, was nicht kommentiert werden darf…" |
| 31:52 / 32:17 / 33:01 | – | Lachen | leise | – | „…mit Kräften auf die Bahn eingekloppt wird." / „Knallrote Landschaft ergibt sich um die Justiz." / „…seht ihr sogar im Bild." |
| **33:58** | **7,3 s** | Applaus | stark | **3,25 s** | „So, und jetzt schwenken wir mal vom Nahost-Konflikt zum Ukraine-Konflikt." |
| **38:48** | **7,5 s** | Applaus | stark | 1,14 s | „Uiuiui, dieselbe Firma hinter Trump und hinter dem Brexit — da glüht der Aluhut, wirklich." |
| 39:48 | – | Lachen | leise | – | „…euch so effizienter zu Dingen verleitet." |
| **40:14** | **5,2 s** | Applaus | stark | 0,21 s | „…wer vor so zielgerichteter Werbung Angst hat, der sollte vielleicht einfach die eigene Urteilsfähigkeit hinterfragen." |
| 40:37 | – | Lachen | leise | – | „…das macht kaum einer." |
| **41:56** | **9,6 s** | Applaus | stark | 1,66 s | „…wenn wir wirklich jeden Mist ins Facebook pumpen, dann haben wir nichts gewonnen." |
| 42:31 | 1,2 s | Lachen | kurz | **2,93 s** | „…ich hätte hunderttausend Artikel geladen — ich meinte über 700.000." |
| **42:44** | **6,2 s** | Applaus | stark | **2,47 s** | „…mit anderen Worten, wir können messen, was in Artikeln geändert wurde." |
| 43:42 / 44:10 | – | Lachen | leise | – | „…der HTML-Titel hat sich geändert auf ‚SAP wächst 2014 langsamer als geplant'." / „…also das hat noch mal irgendwem nicht gefallen." |
| **45:42** | **12,5 s** | Applaus + Pfiffe | stark | 1,30 s | **„Rohdaten sind geil."** |
| 46:04 | – | Lachen | leise | – | „…das sind über 60 Gigabyte pures HTML." |
| **46:41** | **22,5 s** | Applaus | stark | 0,22 s | „Hier sind noch die Links und bis dann." |

*Fragerunde (nicht mitgezählt): 47:38 · 49:13 (5,4 s) · 51:18 · 52:07 (6,2 s) · 52:40 · 55:03 · 55:14 (7,3 s) · 57:05 · 57:14 (5,9 s) · 58:00 (12,5 s) · 58:21 (5,4 s) · 58:28 · 58:41.*

**Was auffällt.** Vier der stärksten Reaktionen — 18:09, 40:14, 41:56, 45:42 — folgen nicht auf Witze, sondern auf **Wertungen**. Und einmal, bei **28:43**, lacht der Saal, *bevor* er die Pointe ausgesprochen hat; er merkt es und sagt es an: „Das Gelächter geht los, bevor ich etwas gesagt habe." Das Publikum hat nach einer halben Stunde sein Muster gelernt.

## B3. Pausen

**36 Stillepausen ≥ 1,5 s.** Median aller Wortabstände: ebenfalls 0,00 s. Bei **31 %** folgt ein Gliederungswort.

| Zeit | Dauer | davor | danach |
|---|---|---|---|
| **37:40** | **7,8 s** | „Aber was wäre dann die rechte Seite?" | „Vor einiger Zeit hat dieser Artikel des Schweizer…" |
| **24:41** | **7,4 s** | „…befindet sich zwischen Panorama und Politik," | „…über die politischen Anteile…" |
| 21:35 | 5,3 s | „…auseinanderschneiden und auswerten können." | „Spiegel Online liefert uns hierbei auch eine gute…" |
| 11:46 | 4,0 s | „…knusprig, wenn personenbezogene Daten ins Spiel kommen." | „Also habe ich mir gedacht, es wäre doch…" |
| 25:38 | 3,0 s | „…wie hier das Keyword E-Mails dazu layoutet wurde." | „Und von hier aus machen wir uns jetzt…" |
| 09:48 | 2,7 s | „…zwischen fünf und sechs Uhr früh am größten." | „Das Gleiche am Wochenende…" |
| 18:27 | 2,0 s | „Das ist, was gerade passiert." | „Jetzt haben wir einen kurzen Exkurs über Metadaten…" |
| 17:01 | 1,7 s | „…das sind ja auch nur Metadaten." | „Gebt mir mal ein paar Monate eurer Metadaten…" |

Die 7,8-Sekunden-Pause bei **37:40** ist per AV-Modell gegengeprüft („eine deutlich hörbare, längere Sprechpause, nur leises Hintergrundrauschen und ein kurzes Räuspern; danach klingt seine Stimme energischer, als würde er eine neue Geschichte einleiten"). Sie steht hinter einer offenen Frage („Aber was wäre dann die rechte Seite?") und markiert einen Kapitelwechsel — dieselbe Funktion wie in BahnMining, nur ohne die dortige explizite Ansage an das Publikum.

**Pause vor der Zahl?** Über 288 Zahlwörter, dasselbe Bild wie in BahnMining:

| | vor dem Zahlwort | nach dem Zahlwort | Basisrate |
|---|---|---|---|
| Anteil Lücke > 0,5 s | **1,4 %** | 3,8 % | 3,2 % |

Wieder: **vor** einer Zahl pausiert er seltener als vor irgendeinem anderen Wort, **nach** der Zahl leicht öfter als der Durchschnitt. Wenn überhaupt, dann liegt die winzige Pause **hinter** der Zahl, nicht davor — sie wirkt eher wie ein Nachklapp als wie eine Anmoderation. Der Effekt ist in beiden Vorträgen gleich gerichtet und damit reproduziert.

## B4. Tempo und Lautstärke als Mittel

Durchschnitt: **2,53 W/s brutto**, **3,39 W/s Artikulationsrate** — praktisch identisch mit BahnMining drei Jahre später. Das ist bemerkenswert konstant.

**Langsamste 30-s-Fenster:** 46:30 (1,10 — Finale), 24:30 (1,40 — die 7,4-s-Pause), 38:30 (1,53), 10:30 (1,57), 18:00 (1,57).
**Schnellste:** 06:00 (3,43), 08:00 (3,27), 31:00 (3,37), 04:00 (3,23).

**Pointenmuster, gemessen über alle 22 Reaktionen:**

| Größe | 5 s vor der Reaktion | 15–5 s davor |
|---|---|---|
| Bruttotempo | **2,10 W/s** | 2,44 W/s |
| Artikulationsrate | **3,54 W/s** | 3,46 W/s |
| Sprechpegel | −17,0 dB | −17,1 dB |

Identisches Ergebnis: Brutto langsamer, netto nicht, Pegel unverändert. **Die Pointe wird durch Stille gesetzt, nicht durch Verlangsamung und nicht durch Leiserwerden.** Der Vorlauf ist hier sogar noch deutlicher als in BahnMining — Median **1,21 s** zwischen letztem Wort und Reaktionsbeginn (BahnMining: 0,38 s). Er hält in SpiegelMining längere Lücken aus.

Drei Belegstellen:
- **10:34** — Nach einer Publikumsabstimmung („fast alle haben die Hand gehoben") sagt er ein einziges Wort als Auflösung: „Stimmt." Dann **4,06 s** nichts. Erst dann kommt der Applaus. Der längste ungefüllte Vorlauf des Vortrags.
- **33:58** — „So, und jetzt schwenken wir mal vom Nahost-Konflikt zum Ukraine-Konflikt." → **3,25 s** Stille → 7,3 s Applaus. Applaus auf einen Überleitungssatz, ausgelöst durch die Pause, nicht durch den Inhalt.
- **45:33–45:42** — Der Aufbau: ein langer Nebensatz („…wenn ihr was im Bereich der Data Science macht"), dann die drei Wörter „**Rohdaten sind geil.**", dann 1,3 s nichts, dann 12,5 s Applaus mit Pfiffen. Kurzer Satz nach langem Satz, ohne Lautstärkeanstieg.

## B5. Bühne und Leinwand

Das SD-Bild ist bei SpiegelMining ein **Kompositbild**: Folie groß links, Redner klein rechts im Kasten — man sieht durchgehend beides.

**Bildwechsel im Folienbereich: 166 im Vortragsteil, im Mittel alle 16,4 s** (Median 11,4 s). ⚠️ **Einschränkung:** Diese Zahl mischt echte Folienwechsel mit Regie-Umschnitten, weil das Layout gelegentlich auf Vollbild-Kamera oder Vollbild-Folie umschaltet. Die Größenordnung ist trotzdem belastbar und der Unterschied zu BahnMining (alle 45,6 s im reinen Folienfeed) zu groß, um Artefakt zu sein: **SpiegelMining hat ein deutlich höheres Bildtempo.** Die stichprobenweise abgelesenen Foliennummern (05:00 → 8, 15:00 → 16, 41:40 → 56, 45:00 → 60) ergeben nur ~60 Folien; die vielen Wechsel sind also überwiegend **Aufbau-Schritte innerhalb einer Folie** — Punkt für Punkt, Pfeil für Pfeil.

**Wechsel vor oder nach dem Satz?** Wie bei BahnMining: **mittendrin.** 119 von 166 (**72 %**) fallen in ein laufendes Wort, Median-Position **52 %** durch den Satz. Das AV-Modell formuliert es unabhängig genauso: „Bild und Ton sind eng gekoppelt, keine vorgezogenen oder verzögerten Schnitte." Konkrete beobachtete Kopplungen: Der Wechsel zur Bitten-Folie fällt auf „…und jetzt kommt meine Bitte"; die Einblendung „Ideen her!" fällt auf das Wort „kreativsten"; die Korrektur-Folie „Ich meinte 700.000" erscheint zeitgleich mit dem gesprochenen Satz.

Nur **9 %** der Bildwechsel liegen innerhalb ±3 s eines Zahlworts — deutlich weniger als in BahnMining (23 %). SpiegelMining ist visuell stärker auf Landkarten und Netzgraphen gebaut, BahnMining auf Zahlen.

**Körperlich** (AV-Modell, sechs Fenster, konsistent): steht durchgehend hinter dem Pult, spricht ins Headset, Hände meist am Pult, **keine ausladende Gestik, kein Zeigen zur Leinwand, kein Umdrehen**. Blick pendelt Laptop ↔ Publikum. Bei Pointen: leichtes Lächeln, sonst nichts. Am Ende greift er zur Wasserflasche und trinkt, während applaudiert wird. Das körperliche Repertoire ist in beiden Vorträgen praktisch identisch — und praktisch leer. Was wirkt, wirkt über Stimme, Timing und Bild.

**Live-Demos: keine.** Alle Bewegungen auf der Leinwand sind vorbereitete PowerPoint-Aufbauten. Das Gegenstück zur BahnMining-Kartenanimation fehlt; das Karten-Zoomen (25:30–27:15, „wir zoomen immer und immer mehr raus") ist eine Folge von Standbildern. **Eine Publikumsinteraktion** um 10:20: Er stellt eine Frage, lässt 1600 Leute die Hand heben und löst mit einem Wort auf.

## B6. Der Einstieg, minutengenau

| Zeit | Was passiert |
|---|---|
| 00:00–00:13 | Saal. |
| 00:13–00:27 | Anmoderation, Verweis auf den 31C3-Xerox-Vortrag. |
| **00:28** | **8,3 s Applaus** auf die Erwähnung des Xerox-Vortrags — das Publikum kennt ihn schon. |
| 00:45–00:52 | „Ich freue mich auf einen spannenden Tag. Um einen ganz, ganz herzlichen Applaus." |
| **00:53** | **8,6 s Applaus** (Einzug). |
| **01:02,2** | Erster Satz: „Ja, danke schön, herzlich willkommen, auch noch mal von mir, auch an die Leute im Internet und auch an die Leute vom Spiegel, von denen ich weiß, dass sie anwesend sind." — Der **erste Satz benennt die Betroffenen im Saal**. |
| 01:12 | 1,8 s Pause. |
| 01:14–01:30 | Vorstellung: Informatiker aus Bonn, Data Science. |
| **01:31,4** | **Erste Zahl: „2014"** — 29 Sekunden nach seinem ersten Wort, dreimal schneller dran als in BahnMining. |
| **01:33,6** | „…knapp **hunderttausend** Artikel von Spiegel Online **gevorratsdatenspeichert**." Zahl und Pointe im selben Satz. |
| **01:40,2** | **5,9 s Applaus**, Vorlauf 1,59 s. Der erste starke Applaus fällt hier auf Minute 1:40 — in BahnMining erst auf 3:57. |
| 01:45–02:15 | Weitere Lachwelle (AV-Modell), akustisch schwach bei 02:03. |
| 02:12 | 1,6 s Pause, dann die Vortragsstruktur: „…werden wir heute zwei Sachen machen." |
| ~02:00–03:20 | Titelfolie → Diagramm-Collage → Strichmännchen-Einblendung. |
| **~03:20** | **Erste inhaltliche Datenfolie**: „Was ist Spiegelmining?" — Screenshot von Spiegel Online, Pfeil, Artikelstapel (Folie 4). Reine Erklärgrafik, noch keine Auswertung. |
| ~04:00–04:50 | Erste echte Auswertungsfolie (Artikel pro Tag). |
| **04:56** | **3,8 s Lachen+Applaus**: „Ich weiß, was fliederfarben ist, ich höre schon Leute lachen." — ein Gag über die eigene Legendenfarbe. |
| **05:37** | **12,5 s Applaus** auf die Februar-Pointe („…dass ein Monat mit Ä ist"). Der stärkste Moment der ersten Vortragshälfte liegt in Minute fünf. |

Der Einstieg ist deutlich schneller getaktet als bei BahnMining: erste Zahl nach 29 statt 60 Sekunden, erster großer Applaus nach 38 statt 179 Sekunden, 14 Bildwechsel in den ersten drei Minuten.

## B7. Der Schluss, minutengenau

| Zeit | Was passiert |
|---|---|
| 41:56 | 9,6 s Applaus auf den Facebook-Appell. |
| 42:24 | 1,8 s Pause, dann die Selbstkorrektur: „…ich meinte über 700.000." |
| 42:31 / 42:44 | Kurzer Lacher / **6,2 s Applaus** auf „…wir können messen, was in Artikeln geändert wurde." |
| 43:40–44:14 | Der SAP-Fall: Titeländerungen live nebeneinander, zwei leise Lacher. |
| 44:34 | „…und jetzt kommt meine Bitte." — **Folienwechsel exakt auf diesen Satz** zur Collage-Folie. |
| ~45:20 | Einblendung „Ideen her!" über die Collage, fällt auf das Wort „kreativsten". |
| 45:23–45:32 | „…schickt mir bitte eine Mail mit euren kreativsten Auswertungsideen für den Datensatz." |
| **45:40,8** | **„Rohdaten sind geil."** |
| **45:42–45:54** | **12,5 s Applaus mit Pfiffen und Jubelrufen** — die stärkste Reaktion des Vortrags. |
| 45:54–46:32 | Der Rohdaten-Appell („behaltet immer alle Rohdaten… über 60 Gigabyte pures HTML… lasst eurer Fantasie freien Lauf"). Ein leiser Lacher bei 46:04. |
| 46:32–46:38 | „Und damit bleibt es mir nur noch, ein dickes Dankeschön zu sagen dafür, dass ihr diese Stunde mit mir verbracht habt." |
| **~46:37** | **Letzter Folienwechsel: „HERZLICHEN DANK!" mit drei Links** — er kommt erst **nach** dem Applaus des Rohdaten-Moments und unmittelbar vor dem Schlusssatz. |
| 46:38,6 | „Hier sind noch die Links und bis dann." |
| **46:41** | **22,5 s Applaus.** |
| 47:03 | Moderator: „Ganz so schnell bist du natürlich noch nicht entlassen, weil wir haben noch unsere Fragerunde." |
| — | **Letztes Bild:** Die Regie schneidet während des Applauses auf eine Vollbild-Kameraeinstellung; er steht am Pult und trinkt. Auf der Leinwand bleibt die Dank-und-Links-Folie. |

Anders als BahnMining endet SpiegelMining **nicht** mit einem inhaltlichen Tiefpunkt und einer Stille, sondern mit der stärksten Publikumsreaktion (45:42) und danach noch einer knappen Minute Appell. Die Kurve fällt also nach dem Höhepunkt noch einmal ab, bevor der Schlussapplaus kommt. In BahnMining ist es umgekehrt: der Höhepunkt **ist** das Ende.

---

# Was das für einen Text bedeutet

Aus der Messung ergeben sich sechs Wirkungen, und sie zerfallen sauber in solche, die sich schreiben lassen, und solche, die man beim Verschriftlichen ersatzlos verliert.

**Übersetzbar:**

1. **Die Pause ist ein Absatzumbruch — aber nicht vor der Zahl.** Das ist die wichtigste Korrektur an der naheliegenden Vermutung. Kriesel pausiert vor Zahlen *seltener* als vor beliebigen anderen Wörtern (1,6 % bzw. 1,4 % gegen eine Basisrate von 3,8 % bzw. 3,2 %). Er pausiert an **Kapitelgrenzen** (33 % bzw. 31 % seiner langen Pausen werden von „So", „Also", „Und", „Jetzt" gefolgt) und **nach** einer offenen Frage. Im Text heißt das: Leerzeile vor dem neuen Gedanken, nicht vor der Zahl. Wer „…und dann waren es — [Pause] — 25 Millionen Halte" schreibt, imitiert etwas, das er gar nicht tut.
2. **Die Zahl gehört ins Bild, nicht in die Stimmführung.** Er betont Zahlen visuell: Die Einblendung „74,9 %" steht 0,4 Sekunden **vor** dem gesprochenen „rund 75 %" auf der Leinwand; 23 % aller Folienwechsel liegen im Drei-Sekunden-Fenster um ein Zahlwort. Textentsprechung: Die Zahl bekommt eine Grafik, eine Hervorhebung, eine eigene Zeile — die Prosa drumherum bleibt unaufgeregt und läuft weiter.
3. **Der kurze Satz nach dem langen.** Fast jeder Lacher steht auf einem Zwei-bis-Fünf-Wort-Nachsatz nach einem langen Erklärsatz: „Habe ich gehört." · „Rohdaten sind geil." · „Es gibt tatsächlich etwas an Berlin, das funktioniert." · „Stimmt." Das überlebt den Medienwechsel eins zu eins und ist die am leichtesten kopierbare Technik von allen.
4. **Applaus für Argumente, nicht für Gags.** Die längsten Reaktionen beider Vorträge folgen auf Sachaussagen: den Gegenvorschlag zur Kennzahl (11,4 s), den Praxistipp zum Monitoring (6,8 s), die Aufforderung zur Fairness gegenüber der Bahn (10,7 s), den Rohdaten-Appell (12,5 s). Der Text darf also die Pointe an die These hängen, nicht an den Witz — und braucht das ausformulierte Werturteil, das man in Datenjournalismus gern weglässt.
5. **Das Rhythmusmaß: alle 50 bis 60 Sekunden ein Ausschlag.** BahnMining: ein Publikumsmoment alle 61 s (Median 51 s), SpiegelMining alle 58 s (Median 44 s). Die längste Durststrecke ist in beiden Fällen unter fünf Minuten und liegt genau dort, wo das Material am dichtesten ist. Übersetzt: pro Bildschirmseite eine Stelle, an der der Leser lächelt, nickt oder aufschreckt — und die längste reaktionslose Passage darf nicht länger sein als ein Kapitel.
6. **Das gestaffelte Ende.** BahnMining endet nicht mit Daten, sondern mit einer inszenierten Stille (9,0 s), einer Passage im leisesten Ton des ganzen Abends und einer Beobachtung über den Saal selbst („5000 Leute an einem Samstagabend zwischen Weihnachten und Silvester… um einen Statistikvortrag zu hören"). Ein Text kann das nachbauen: den Datenteil abschließen („Und was bleibt?"), einen Absatz weiß lassen, dann leiser weiterschreiben, dann den Leser selbst in den Text holen.

**Nicht übersetzbar:**

- **Die Stille selbst.** Neun Sekunden Schweigen mit ausdrücklicher Denkaufforderung — eine Leerzeile hält keinen Leser neun Sekunden lang fest, und die Aufforderung „denk jetzt bitte nach" verpufft im Text, weil niemand kontrolliert, ob er es tut.
- **Die Reaktion als Beweis.** Dass 1600 Leute gleichzeitig auffahren, wenn er „gevorratsdatenspeichert" sagt, beweist dem Saal, dass er nicht allein ist. Der Applaus ist Teil des Arguments. Ein Leser lacht allein, und niemand hört es.
- **Der Live-Dialog.** „Wir haben eine Frankfurt-Fraktion, wie seid ihr hergekommen?", die Handzeichen-Abstimmung, das selbst eingeforderte „das könnte jetzt mal ein Applaus für die Bahn wert sein" — dreimal wird das Publikum zum Mitspieler. Im Text bleibt davon eine rhetorische Frage, also fast nichts.
- **Das Daumenkino.** 41 Folien in 100 Sekunden, eine Deutschlandkarte, die ein Jahr Bahnverkehr durchläuft, während er fast schweigt. Eine Animation lässt sich in einen Artikel einbetten — aber die Dramaturgie, dass der Redner dafür verstummt und der Raum zusieht, geht verloren.
- **Umgekehrt gewinnt der Text etwas:** Was er körperlich tut, ist nichts. Er steht am Pult, gestikuliert kaum, dreht sich nie zur Leinwand, zeigt praktisch nie. Von der Bühnenpräsenz muss ein Text **nichts** ersetzen — das ganze Wirkgefüge steckt in Timing, Satzlänge und Bild. Das macht Kriesel zum ungewöhnlich gut übersetzbaren Redner.

---

## Verifikation und offene Punkte

**Belegt (Kommandos gelaufen, Ausgaben ausgewertet):** Zeitgleichheit Video/SRT (ffprobe + Folienwechsel bei 119,0 s gegen SRT-Cue); alle dB-, Tempo-, Pausen- und Zahl-Statistiken (eigene Analyse-Skripte über WAV und Wortzeiten); Folienwechsel-Zeiten (ffmpeg-Szenendetektion); Foliennummern (Bildausschnitte aus dem Folienfeed, selbst gelesen); Publikumsreaktionen (akustische Detektion, gegengeprüft durch 242 Omni-Fenster).

**Nicht geprüft:** Ob der akustisch gemessene Sprechpegel dem Saaleindruck entspricht (Broadcast-Kompression, siehe §0). Ob die 25 bzw. 20 „leisen" Reaktionen wirklich Lacher sind — sie stammen allein aus dem AV-Modell und liegen unter der akustischen Messschwelle; bei zwei Stichproben widersprach das Modell sich in engeren Fenstern selbst. Der Inhalt einzelner Folien außerhalb der 15 visuell geprüften Fenster wurde nicht Bild für Bild verifiziert. Für SpiegelMining fehlt ein reiner Folienfeed, weshalb die Bildwechsel-Rate dort Regie-Umschnitte enthält.

```json
{
  "verdict": "pass",
  "confidence": 84,
  "ambiguities": [
    "Absolute Lautstärkedynamik nicht bestimmbar — CCC-Tonspur ist limitiert/kompressiert; Sprechpegel schwankt über 60 Minuten nur um 1,4–3 dB. Relative Verläufe gültig, absolute Aussagen N/A_PENDING_REVIEWER.",
    "56 leise Publikumsreaktionen (20 BahnMining / 25 SpiegelMining im Vortragsteil) stammen ausschließlich aus dem AV-Modell und liegen unter der akustischen Messschwelle; Präzision dieser Klasse ungeprüft. Die 50 akustisch vermessenen Ereignisse sind durch 242 unabhängige Modellfenster gegenbestätigt (0 bzw. 3 Widersprüche).",
    "SpiegelMining-Bildwechselrate (alle 16,4 s) mischt Folienwechsel mit Regie-Umschnitten, da kein reiner Folienfeed existiert. Die BahnMining-Rate (alle 45,6 s) ist sauber gemessen. Der Größenunterschied ist zu groß für ein reines Artefakt, die exakte SpiegelMining-Zahl aber nicht belastbar.",
    "Foliennummern für SpiegelMining nur an fünf von vierzehn Stichproben lesbar (Layoutwechsel des Kompositbilds); Gesamtzahl ~60 Folien ist eine Schätzung.",
    "Trennung Lachen/Applaus bei Ereignissen unter 2,5 s Dauer bleibt unsicher: In einer Stichprobe von acht Modell-Gegenproben wurde eine Zuordnung widerlegt (43:52 BahnMining: akustisch Applaus, Modell Lachen).",
    "Bühnenverhalten stützt sich auf 13 Modell-Fenster mit Bild, nicht auf eine durchgehende Sichtung; Aussagen wie 'zeigt praktisch nie zur Leinwand' sind Stichprobenbefunde, kein Vollzählungsergebnis."
  ]
}
```
