# Kriesel-Rhetorik: Befunde und Bauanleitung

**Quellen**
- `BahnMining – Pünktlichkeit ist eine Zier` (36C3, 2019). Anmoderation bis 00:58, Vortrag 00:58–49:37, Q&A 50:33–61:19.
- `SpiegelMining – Reverse Engineering von Spiegel-Online` (33C3, 2016). Anmoderation bis 01:02, Vortrag 01:02–46:40, Q&A 47:03–58:20.

Alle Zeitangaben sind Absolutzeiten aus den `.srt`-Dateien (Format `[mm:ss]`), also inklusive Anmoderation. Wenn im Text von „Minute X des Vortrags" die Rede ist, ist die Zeit ab Sprechbeginn gemeint, sonst die Absolutzeit.

**Belegqualität — bitte lesen.** Beide Transkripte sind maschinell erzeugt (Whisper). Sie enthalten hörbare Fehler: „David Griessel", „Zufahrt" (= Zugfahrt), „Rettungsstuss", „Pufala-Wende" (= Pofalla-Wende), „Gaffy" (= Gephi), „SkyKit Learn" (= scikit-learn), „Fliederfarben", „schwach auf Verbus" (= auf der Brust). Wörtliche Zitate unten sind **Transkript-Wortlaut**, nicht garantierter Sprech-Wortlaut. Für die rhetorische Analyse ist das unschädlich (Satzbau, Reihenfolge, Wortwahl sind stabil), für ein Zitat in einer Publikation müsste man gegen die `.wav` prüfen. Zwei Stellen habe ich unten explizit als vermutlich verhörte Passage markiert.

**Messmethode für Publikumsreaktionen.** Die Transkripte enthalten keine `[Lachen]`/`[Applaus]`-Marker. Lachen und Applaus erzeugen aber Sprechpausen, und Sprechpausen sind in den SRT-Zeitstempeln als Lücke zwischen Untertitel-Ende und nächstem Untertitel-Beginn messbar. Ich habe alle Lücken ≥ 1,6 s berechnet. Bei einem durchgehend frei gesprochenen Vortrag ist eine Lücke von 5–11 s praktisch immer eine Publikumsreaktion; 2–4 s sind Folienwechsel oder kurzes Auflachen und damit nicht eindeutig. Wo ich unten von „Lacher" spreche, steht die gemessene Pausenlänge dabei. Das ist ein **Proxy, kein Marker** — die Reaktionsart (Lachen vs. Applaus vs. Stille zum Nachdenken) ist aus der Pausenlänge allein nicht ableitbar. An drei Stellen kommentiert Kriesel die Reaktion selbst, dort ist sie belegt.

---

# TEIL A — BEFUNDE

## 1. Der Einstieg

### BahnMining

**Womit er anfängt:** mit einem Witz über die Anmoderation, dann mit sich selbst — aber sehr knapp.

```
[00:58] Also ich glaube, so geil bin ich noch niemals eingeleitet worden.
[01:04] Ja, herzlich willkommen euch allen hier, auch herzlich willkommen an die
        Leute im Stream und an die Alu-Hüte im Besonderen.
[01:14] Die Alo-Hüte glühen aber leider noch nicht, vielleicht kriegen wir das im
        Verlaufe dieses Vortrages noch hin.
[01:20] Mein Name ist David Kriesel, ich bin Informatiker aus der Nähe von Bonn,
        und im richtigen Leben ist es meinem Beruf, interessante Sachen in
        grösseren Datenmengen zu finden.
```

Die Selbstvorstellung ist **22 Sekunden lang** (01:20–01:42) und enthält keinen einzigen Kompetenzbeleg außer „Informatiker" und „Data Scientist". Kein Lebenslauf, keine Referenzen, keine Institution. Statt Autorität baut er Zugehörigkeit: „Ich bin Rheinländer, und bei uns sagt man, ab zweimal ist es Tradition und beim dritten Mal ist es Brauchtum." [01:42]

**Bis zur ersten Zahl: 62 Sekunden.**

```
[01:55] Unsere Geschichte heute beginnt im Jahr 2018.
[02:00] Am Ende des Jahres 2018 hat nämlich die Bahn gesagt, rund 75 % ihrer
        Fernzüge seien pünktlich gewesen.
```

Die erste Zahl ist **nicht seine**. Sie ist die Behauptung des Gegenübers. Der ganze Vortrag hängt danach an dieser einen fremden Zahl.

**Bis zum ersten messbaren Lacher: 106 Sekunden** (3,7 s Pause bei 02:44), ausgelöst durch eine Untertreibung am Ende eines nüchternen Satzes:

```
[02:31] ...und das wären bei knapp 75 % in 2018 so der Fall gewesen, und das hat
        mich in meiner persönlichen Erfahrung irgendwie gestört.
```

Der erste **große** Lacher kommt bei 03:54 (9,7 s) und ist ein Wortwitz, der gleichzeitig das ganze Projekt benennt:

```
[03:49] Also habe ich am 8. Januar begonnen, die Deutsche Bahn zu
        Vorratsdatenspeichern.
```

**Struktur des Einstiegs (00:58–04:50, knapp 4 Minuten):**
1. Wer ich bin — 22 s, minimal.
2. Die fremde Zahl — 75 %.
3. Wie die Zahl definiert ist — „wenn ein Zug bei einem Stopp weniger als sechs Minuten zu spät ankommt, dann ist er pünktlich. Das ist wirklich die Definition, und wir übernehmen das einfach" [02:16].
4. Warum ich zweifle — persönlich, nicht analytisch: „für mehr als die Hälfte meiner Fahrten habe ich diese E-Mail von verspätungsalarm.bahn.de" [02:48].
5. Warum ich es nicht nachprüfen konnte — die veröffentlichten Statistiken reichen nicht [03:16–03:49].
6. Also habe ich selbst gemessen — der Pointensatz.
7. Vertrag mit dem Publikum: was kommt, in welcher Reihenfolge, mit welchem Vorbehalt [04:04–04:50].

### SpiegelMining

Radikal schneller. Erste Zahl nach **29 Sekunden**, und sie ist gleichzeitig der erste Lacher (7,5 s Pause bei 01:39):

```
[01:14] Es ist schön, wieder hier zu sein, mein Name ist David Kriesel, ich bin
        Informatiker aus Bonn und ich mache beruflich, es wurde schon gesagt,
        Data Science und Machine Learning...
[01:31] Und seit 2014 habe ich knapp hunderttausend Artikel von Spiegel Online
        Gevorratsdaten speichert.
        → 7,5 s Pause
[01:46] Und das habe ich einfach niemandem erzählt.
```

Der Aufbau hier ist eine **Enthüllung statt einer Frage**. Bahn beginnt mit einem Widerspruch („die sagen 75 %, mein Gefühl sagt was anderes"), Spiegel beginnt mit einem Geständnis („ich habe zweieinhalb Jahre heimlich mitgeschrieben"). Beide Male ist der erste Lacher **auf eine Zahl gesetzt**, nicht auf einen Gag.

Ebenfalls in der ersten Minute [01:02]: „auch an die Leute vom Spiegel, von denen ich weiss, dass sie anwesend sind." Er sagt vor dem ersten Befund, dass die Betroffenen im Raum sitzen. Das ist keine Höflichkeit, es ist eine Selbstbindung: alles Folgende wird vor deren Ohren gesagt.

**Der Einstiegs-Vertrag** ist bei Spiegel explizit nummeriert [02:14–02:54]: „Erstens, wir werden den Datensatz durchleuchten und was über Spiegel online lernen, und zwar so, dass ihr das auch mit nach Hause nehmen und beim Lesen dann anwenden könnt. Und zweitens, wir werden Einblick erhalten, wie die Datensammelwut von heute funktioniert" — plus „zusätzlich werde ich [...] ein bisschen aufs Gesellschaftliche eingehen."

**Vergleich der beiden Einstiege**

| | BahnMining | SpiegelMining |
|---|---|---|
| Selbstvorstellung | 22 s | 17 s |
| bis erste Zahl | 62 s | 29 s |
| bis erster messbarer Lacher | 106 s (3,7 s) | 37 s (7,5 s) |
| Auslöser des ersten Lachers | Untertreibung | die Zahl selbst |
| Öffnungsfigur | fremde Behauptung anzweifeln | eigene heimliche Sammlung offenlegen |
| Vertrag ans Publikum | bei 04:04 | bei 02:14 |

## 2. Der Spannungsbogen

### BahnMining — 13 Abschnitte

| # | Zeit | Dauer | Thema | **Funktion** |
|---|---|---|---|---|
| 1 | 00:58–01:55 | 1' | Begrüßung, Person | Zugehörigkeit statt Autorität; Erwartung senken |
| 2 | 01:55–03:55 | 2' | 75 %, Definition, persönlicher Zweifel | **Konflikt setzen** — fremde Zahl gegen eigenes Erleben |
| 3 | 03:55–04:50 | 1' | Was kommt, Disclaimer | Vertrag + Vorab-Entschärfung der Angreifbarkeit |
| 4 | 04:50–06:20 | 1,5' | Eine ICE-Fahrt als Tabelle | **Atomeinheit erklären** — was ist ein „Stopp" |
| 5 | 06:20–15:00 | 9' | Bahnhöfe → Pünktlichkeit → Verspätungsquellen → Zugarten → **Ausfälle 5 %** | Eskalationstreppe: jede Runde ein Grad heißer; endet auf dem ersten echten Befund |
| 6 | 15:00–21:04 | 6' | Zeitreihen, Sommer-ICE, 40-Minuten-Stufe | Muster über Zeit; drei Praxistipps als Belohnung; endet mit „So, das war ein Höllenritt" |
| 7 | 21:04–28:00 | 7' | **Methoden-Einschub, Punkt 1–7** | Ruhephase + Vertrauensaufbau vor dem Hauptangriff |
| 8 | 28:00–31:55 | 4' | Verifikation extern + intern (Tagesanimation, Orkan) | **Lizenz zum Angriff** — erst jetzt darf er die Bahn kritisieren |
| 9 | 31:55–37:00 | 5' | **Höhepunkt 1**: Ausfälle fehlen in der Statistik → eigene Metrik → 72,5 % | Der Vorwurf, vollständig belegt |
| 10 | 37:00–41:00 | 4' | **Höhepunkt 2**: Fehlanreiz → „Scheuerwende", vorhergesagt und in Daten bestätigt | Vom Messfehler zum Verhalten — die härtere Aussage |
| 11 | 41:00–45:00 | 4' | 500 Zugbindungs-Kombinationen | **Nutzwert-Klimax** — der Zuhörer bekommt etwas mit |
| 12 | 45:00–46:06 | 1' | Fairness-Coda, „seid nett zur Bahn" | Versöhnung; Ton runterfahren |
| 13 | 46:06–49:37 | 3,5' | Jahrzehnt, „Aufstieg der Empörten", Appell | **Themenwechsel nach oben** — der eigentliche Grund für alles |

### SpiegelMining — 12 Abschnitte

| # | Zeit | Dauer | Thema | **Funktion** |
|---|---|---|---|---|
| 1 | 01:02–01:50 | 1' | Begrüßung + Enthüllung 100.000 Artikel | Sofortiger Einschlag |
| 2 | 01:50–03:02 | 1' | Stimmungsumbruch „Lügenpresse", Vertrag | **Relevanz jetzt** — warum das Thema brennt |
| 3 | 03:02–04:21 | 1,5' | Wie das Sammeln funktioniert | Methode früh und kurz; endet auf „das war's, Spiegel Mining in wenigen Minuten" |
| 4 | 04:21–08:20 | 4' | Rubriken, Artikel/Tag, Länge → „Reichweite statt Tiefe" | Aufwärmen an einfachen Features; erste Folgerung + Wertungsverzicht |
| 5 | 08:26–11:33 | 3' | Heatmap Wochentag×Stunde; 3 Lektionen; Kulturressort | **Methoden-Lehre im Beispiel** — inkl. Selbstwiderlegung |
| 6 | 11:33–16:16 | 5' | Autoren-Netzwerk → Teams → Urlaube → Pärchenkandidaten | **Höhepunkt 1** — Eskalation ins Persönliche |
| 7 | 16:16–18:25 | 2' | Metadaten, Vorratsdatenspeicherung, Orwell | **Ernst-Block** — kein einziger Gag, direkt nach dem größten Lacher |
| 8 | 18:29–21:00 | 2,5' | Autoren oben/unten → Agenturmeldungen | Erklärte Erholung: „damit sich eure Laune wieder hebt" |
| 9 | 21:01–28:20 | 7' | Keyword-Landkarte bauen, Zoomfahrt nach außen | **Staunen** — Maßstab, kein Argument |
| 10 | 28:28–36:20 | 8' | Kommentierbarkeit auf der Landkarte | **Höhepunkt 2** — „unsere westliche Filterbubble, die kann man messen" |
| 11 | 36:22–41:54 | 5,5' | Wahlkampf, Cambridge-Analytica-Entzauberung, Facebook-Likes | Erwartungsdämpfung, dann Umdrehung aufs Publikum |
| 12 | 41:54–46:40 | 5' | Überraschung 700.000 / Änderungsmessung; Bitte; „Rohdaten sind geil"; Dank | Öffnung statt Abschluss |

### Rhythmus der Höhepunkte

Gemessen an den größten Publikumspausen (ohne Anfangs- und Schlussapplaus):

**BahnMining:** 05:54 (8,7 s), 11:11 (5,8 s), 24:19 (9,8 s), 26:56 (10,1 s), 27:19 (9,3 s), 29:59 (10,1 s), 35:12 (9,3 s), 36:19 (11,2 s), 45:09 (8,2 s), 46:07 (8,2 s), 46:38 (9,0 s).
**SpiegelMining:** 10:30 (9,4 s), 10:56 (8,3 s), 18:07 (9,8 s), 26:17 (7,4 s), 27:56 (10,2 s), 33:55 (10,8 s), 38:46 (8,6 s), 41:54 (11,4 s), 45:40 (13,7 s).

Zwei Beobachtungen:

**Erstens: keine gleichmäßige Verteilung, sondern Trauben.** Bei BahnMining liegen vier der stärksten Reaktionen zwischen 24:19 und 30:00 — mitten im Methoden-Einschub, der eigentlich der trockenste Teil ist. Kriesel legt seine dichteste Lacherzone genau dorthin, wo die Aufmerksamkeit sonst wegbrechen würde. Bei SpiegelMining sind es 10:30–10:56 (Kulturressort) und 33:55–38:46 (Filterbubble, Aluhut).

**Zweitens: der stärkste Ausschlag steht unmittelbar vor der Hauptzahl, nicht danach.** BahnMining 36:19, 11,2 Sekunden:

```
[36:08] Das wären hier 50 %, also nehmt das nicht auf die leichte Schulter, das
        ist jetzt wirklich grosse Mathematik bahnbrechend sozusagen.
        → 11,2 s
[36:30] Und wenn man mit den Ausfällen ehrlich umgeht, dann liegt die Bahn nicht
        bei den 76-inhalb-Pünktlichkeit [...] sondern bei 72,5.
```

Der Witz ist eine **Verzögerungsschraube**: er unterbricht direkt vor der Zahl, das Publikum lacht elf Sekunden, und die Zahl landet in einem völlig leeren Raum. Kein Applaus danach — die Zahl steht allein.

### Das wiederkehrende Mikro-Muster

Das dominierende Muster ist **nicht** „Beobachtung → Vermutung → Widerlegung → Auflösung". Es ist eine Zangenbewegung:

> **Befund → eigene Reaktion in Alltagssprache → Selbstangriff (was dagegen spricht) → Gegenprüfung → engere, härtere Behauptung → Handlungsanweisung**

Der entscheidende Schritt ist der dritte: Kriesel führt den Einwand des Gegners selbst ein, bevor jemand anders es tun kann. Was danach noch steht, steht fest.

**Beleg 1 — ICE-Ausfälle (BahnMining, 13:39–14:14, sechs Schritte in 35 Sekunden):**
```
[13:39] Und das ist der Prozentsatz der Ausfälle, und hier ist er, und das war für
        mich überraschend.                                    ← Befund
[13:59] Also wenn ihr einen ICE bucht, dann taucht er in einem von zwanzig Mal
        einfach nicht auf.                                    ← Übersetzung
[14:05] Und das fand ich ganz schön stramm. Mich hat das überrascht.
                                                              ← eigene Reaktion
[14:14] Ich weise fairerweise nochmals darauf hin, dass das eine Auswertung von
        aussen ist. Es besteht die Möglichkeit, dass das nicht stimmt oder da ewig
        viele Extrafahrten dann für die Ausfälle gefahren werden...
                                                              ← Selbstangriff
[14:19] ...aber alle diese Stopps standen in deren Daten explizit als ausgefallen
        drin, die Daten sehen insgesamt realistisch aus, und im Spiegel hatten sie
        auch neulich eine Auswertung, wo sie auf ähnliche Werte kamen.
                                                              ← Gegenprüfung
[14:36] Also schlage ich vor, wir betrachten das mal als gegeben, bis die Bahn
        widerspricht.                                         ← engere Behauptung
[14:09] Mein Praxistipp an euch lautet also, Vorsicht mit den ICEs.
                                                              ← Anweisung
```

**Beleg 2 — lange Fahrten (BahnMining, 18:25–19:44).** Hier dreht der Selbstangriff die Richtung des ganzen Abschnitts um: Der Befund („später in der Fahrt sinkt die Pünktlichkeit") wäre eine Anklage. Kriesel nutzt ihn als **Verteidigung**:
```
[18:53] Das habt ihr euch wahrscheinlich jetzt alle schon selbst gedacht, warum
        sage ich das also, weil euch die Bahn ein bisschen in Schutz nehmen möchte.
[18:58] Man sieht nämlich häufiger in den Medien irgendwelche Untersuchungen von
        Fahrten zwischen weit entfernteren Metropolen [...] die machen die Bahn
        schlimmer, als sie ist, weil sie durch weiter Entfernung eben nur den
        Datenteil mit der hohen Verspätung auswählen.
[19:16] Und ganz ehrlich, also die häufigen Probleme mit den japanischen
        Hochgeschwindigkeitszügen sind aus meiner Sicht auch einfach Stuss [...]
        also das ist nicht vergleichbar, so fair müssen wir schon sein.
[19:39] Trotzdem hier wieder mein Praxistipp für euch, Vorsicht mit Zügen, die
        bereits lange unterwegs sind.
```
(Der Satz „weil euch die Bahn ein bisschen in Schutz nehmen möchte" ist eine verhörte Passage; gemeint ist offensichtlich „weil ich euch gegenüber die Bahn ein bisschen in Schutz nehmen möchte".)

**Beleg 3 — Scheuerwende (BahnMining, 37:00–40:56).** Hier kommt zusätzlich eine **Falsifikationsbedingung**, die vor dem Blick in die Daten formuliert wird:
```
[37:17] Wenn die Bahn einen unpünktlichen Zug einfach spontan ausfallen lässt,
        dann steht die nach ihrer eigenen Messmethode danach besser da...  ← Hypothese
[37:30] Also müssen wir uns die Frage stellen, wo genau lohnt es sich für die Bahn
        am meisten, ein paar Ausfälle zu erzeugen...
[39:10] Wenn Ausfälle aufgrund technischen Betriebes entstehen, würde man ja
        erwarten, dass es am Start einer Fahrt statistisch weniger Ausfälle gibt,
        und dann werden das so über die Zeit mehr.        ← Vorhersage bei Nullhypothese
[39:23] Und beim IC ist das auch genauso. Die Ausfälle steigen nach hinten an.
                                                          ← Kontrollgruppe bestätigt
[39:28] Und beim ICE dagegen fallen die ersten und letzten Stops häufiger aus...
                                                          ← Abweichung nur dort
[39:38] Und ich habe dieses Verhalten auch von zwei unabhängigen Quellen bestätigt
        bekommen...                                       ← externe Stütze
[40:12] Und aus Gründen der Neutralität muss ich dazu sagen, die Bahn hat natürlich
        ein Interesse daran, dass das ganze Zugnetz ungefähr im Plan ist [...] ist
        eben deren Geschäftsentscheidung...               ← Selbstangriff
[40:46] Und was ich hier kritisieren möchte, ist aber, dass ausschliesslich die
        positive Seite des Manövers danach in der Statistik auftaucht und die
        negative einfach verschwindet. Das stört.         ← engere Behauptung
```

**Beleg 4 — Kulturressort (SpiegelMining, 10:07–11:33).** Dasselbe Muster, aber der Selbstangriff kippt das Ergebnis komplett:
```
[10:12] Wer von euch denkt, dass die Leutchen aus dem Kulturressort morgens bitte
        gerne ein bisschen länger pennen als die anderen?   ← Vorurteil abfragen
[10:21] ...fast alle an die Hand gehoben, und die Lösung ist stimmt.  ← bestätigt
[11:04] ...ich war bei Spiegel Online eingeladen im Oktober, und da habe ich das
        auch so gesagt, und dann haben Sie gesagt, David, nein, nein.
[11:16] Manche Artikel werden natürlich auch vorab gescheduled, das will ich hier
        fairerweise dazu sagen, und ich mache das auch als Ermahnung, dass ihr [...]
        immer noch mal selbst nachdenken müsst, was ihr aus solchen Auswertungen
        wirklich folgern könnt, besonders dann, wenn ihr schon mit dem Vorurteil da
        reingegangen seid, so wie wir jetzt.
```

**Beleg 5 — Cambridge Analytica (SpiegelMining, 37:40–41:04).** Selbstangriff gegen die *Sensation*, nicht gegen den eigenen Befund:
```
[38:40] Uiuiui, dieselbe Firma hinter Trump und hinter dem Brexit, da glüht der
        Aluhut, wirklich.                                   ← Sensation zitieren
[39:15] Generell würde ich sagen, tiefer hängen. Es ist überhaupt nicht klar, was
        die Firma den beiden Wahlkämpfen überhaupt wirklich gebracht hat. Die Infos
        kommen nämlich im Wesentlichen von der Firma selbst...  ← Entzauberung
[40:02] Es ist nicht so, dass Big Data die Leute fernsteuert, das müssen wir schon
        festhalten.
[41:04] Und das bedeutet, ja, Data Science-Techniken können Wahlen beeinflussen.
                                                            ← was übrig bleibt
[41:26] Wisst ihr, was die Firma aus dem Artikel genommen hat [...] Das waren
        überhaupt keine staatlichen Überwachungsdaten, das waren Facebook-Likes,
        also Daten, die die Leute selbst über sich ins Netz gestellt hatten.
                                                            ← Drehung aufs Publikum
```

## 3. Wie er eine Zahl setzt

Das Verfahren hat vier Schritte, und er lässt selten einen aus.

**(1) Die Zahl wird angekündigt, bevor sie kommt.** „Und es fehlt noch eine Grösse, die wir messen können und die wir messen werden, und über die schweigt sich die Bahn auf ihren Webseiten aus." [13:24] Dann erst der Wert. Zwischen Ankündigung und Zahl liegen 15 Sekunden Erwartung.

**(2) Die Zahl kommt in ihrer Rohform.** „Eurocity gut zwei Prozent, Intercity gut drei % und ICE über fünf %." [13:52]

**(3) Sofortige Übersetzung in eine erlebbare Häufigkeit.** Das ist der wichtigste Schritt und er folgt fast immer im nächsten Satz:

| Rohzahl | Übersetzung | Zeit |
|---|---|---|
| über 5 % ICE-Ausfälle | „dann taucht er in einem von zwanzig Mal einfach nicht auf" | 13:59 |
| ~8 % im Sommer | „fast an jedem zwölften Stopp taucht so ein ICE in der warmen Zeit dann einfach nicht auf" | 17:33 |
| 456 Minuten | „das sind mehr als siebeneinhalb Stunden, und der war nicht ausgefallen" | 14:51 |
| Ausfall im Datensatz | „ihr steht da mit leerem Blick, und er kommt einfach nicht" | 33:03 |
| 700 Artikel/Woche | „also so 100 am Tag, und das ist schon ziemlich viel Output" | 06:06 |
| Metadaten | „wer eure besten Freunde sind, ob ihr eine Affäre habt, wie ihr sexuell orientiert seid, ob ihr schwanger seid..." | 17:11 |

**(4) Ein Vergleichsanker, gegen den die Zahl sich reibt.** Meist die Zahl des Gegenübers: 72,5 % gegen die angekündigten 76,5 % und die aktuellen 75 % [36:30]. Oder gegen sich selbst: „bei den langen Artikeln ist auch nur ca. zwei %, bei zwei % eine Nachrichtenagentur mit dabei und bei den kurzen Artikeln ist bei knapp achtzig % eine Nachrichtenagentur mit dabei" [20:22].

### Die Alltagsvergleiche, wörtlich

**BahnMining**
- „ich bin wohl dieser eine Typ, der aufpassen muss, nicht vom Blitz getroffen zu werden, während er den Sechser im Lotto abholt" [02:48]
- „Also habe ich am 8. Januar begonnen, die Deutsche Bahn zu Vorratsdatenspeichern." [03:49]
- „Ich bin sicher, das sind diese blühenden Landschaften, von denen Altkanzler Kohl immer sprach." [08:04]
- „die simple Wahrheit ist, ich wohne nur schlecht" [08:31]
- „Es gibt tatsächlich etwas an Berlin, das funktioniert." [11:25]
- „dann taucht er in einem von zwanzig Mal einfach nicht auf" [13:59]
- „fast an jedem zwölften Stopp" [17:33]
- „diesen Moment kriegen die Admins der Bahn vermutlich einen Herzanfall, und wenn die damit fertig sind, dann werden die in ihre Logs schauen [...] und dann werden die ihren Anwalt anrufen, um mir eine riesige Rechnung zu schicken" [23:11]
- „In diesem Moment kriegen die Admins zwar keinen Herzanfall mehr, aber die sind trotzdem enttäuscht, weil sich dafür keine Rechnung mehr lohnt." [24:46]
- „An dieser Stelle hören die Admins der Bahn vermutlich auf, meine Abfragen in ihren Logs zu suchen, und ich freue mich, dass die jetzt wieder voll beim Vortrag dabei sind." [25:40]
- „das sind die Lumpensammler sozusagen" [29:33]
- „Der beste Apparat zur Mustererkennung, den wir zurzeit haben, das ist nun mal das Gehirn, und da gibt es nur eine Breitbandleitung hin, und das sind die Augen." [31:48]
- „Das heisst, wir haben insgesamt 103 % Fernverkehr." [34:34]
- „ich nenne sowas den finalen Rettungsstuss" [34:59]
- „also nehmt das nicht auf die leichte Schulter, das ist jetzt wirklich grosse Mathematik bahnbrechend sozusagen" [36:08]
- „der Zug schmeißt die Fahrgäste raus, dreht an Ort und Stelle um und ist wieder pünktlich" [38:10]
- „Und wer in den roten Stopps einsteigen und aussteigen will, der steht halt mit leerem Blick am Gleis." [38:23]
- „die Scheuerwende oder aber [...] die Pufala-Wende" [39:38]
- „Also bitte behandelt diese Daten, als wären sie mit Xeroxgeräten gescannt." [45:04]
- „seid nett zur Bahn mit ihren Fehlern, wir haben nur diese eine" [45:56]

**SpiegelMining**
- „Feature ist einfach das Fachwort für ein Artikelmerkmal." [03:53]
- „das ist die Kinderausgabe vom Spiegel, wer das nicht kennt" (über Bento) [13:35]
- „der Spiegel-Chefredakteur ist kürzlich auch grau geworden" [14:04]
- „man weiss schon, womit man gegoogelt werden will als Redakteur" [20:00]
- „Keywords, die fast ausschliesslich zusammen vorkommen, die sind sozusagen verheiratet" [22:09]
- „mit so ganz strammen, dicken Federn. Ich meine jetzt wirklich Federn im physikalischen Sinne, die die Keywords zueinander hinziehen." [22:47]
- „Wolfgang Schäuble ist da direkt nah als Aufpasser dazuloutet worden. Interessanterweise hat er keine Farbe, der ist grau, und das ist nicht altersbedingt..." [25:02]
- „dem Rest der Welt etwas entrückt, ist die Wissenschaft [...] und ganz weit weg vom Hauptkontinent ist der Sport" [27:46 / 28:06]
- „da könnt ihr auch selbst drin rumforschen, wie in Google Maps so drin rumscrollen" [28:18]
- „Es gibt ja nur eine Breitbandverbindung ins Gehirn, und das sind die Augen." [33:26]
- „Russenbashen ist okay." [34:06]
- „so illegal das auch ist" (über Firmen, die Urlaubsüberschneidungen auswerten) [16:00]
- „eine Generalüberwachung, die selbst George Orwells Big Brother, die Schamesröte ins Gesicht treiben würde" [17:56]
- „endlich kriegen nur noch diejenigen wieagra Spam, die das Produkt auch wirklich benötigen" [39:49]
- „Rohdaten sind geil." [45:40]

**Auffällig:** Das Bild „nur eine Breitbandleitung ins Gehirn, und das sind die Augen" kommt in **beiden** Vorträgen wortgleich vor (31:48 bzw. 33:26). Es ist offenbar sein Standard-Argument für Visualisierung — ein Satz, den er wiederverwendet, weil er trägt.

**Zweites Muster:** Vier der stärksten Vergleiche sind **wiederkehrende Figuren mit Fortsetzung**. Die Bahn-Admins tauchen dreimal auf (23:11, 24:46, 25:40) und entwickeln sich vom Herzinfarkt über Enttäuschung zur Rückkehr in den Saal. Der Vergleich wird zur Nebenfigur, nicht zum einmaligen Gag.

## 4. Wie er über Unsicherheit spricht

Das ist der dichteste Befund. Kriesel gibt Nicht-Wissen **so oft und so beiläufig** zu, dass es aufhört, eine Schwäche zu sein, und zur Marke wird. Ich zähle allein im BahnMining-Vortrag (ohne Q&A) elf Stellen.

### Die Grundfigur: Vorab-Kapitulation

Er räumt Fehlbarkeit ein, **bevor** irgendein Befund gefallen ist:

```
[04:34] Und ein Disclaimer vorweg, ich habe mit der Bahn nicht über die Auswertung
        gesprochen, behaltet im Hinterkopf, am Ende ist das ein kleines
        Hobbyprojekt, und es kann durchaus sein, dass ich Fehler gemacht habe, aber
        da wir auch noch über die Vertrauenswürdigkeit der Daten reden, könnt ihr
        selbst entscheiden, ob ihr meinen Daten vertraut oder nicht.
```

Der Satz hat drei Teile und **keiner** ist eine Entschuldigung: Umfang klären („kleines Hobbyprojekt"), Fehler zugestehen, **und dann die Prüfung an das Publikum abgeben**. Die Abgabe ist der Trick. Wer die Prüfmittel liefert, wirkt nicht unsicher, sondern souverän. Direkt davor steht der Vorspann dazu: „Das muss ja nicht sein, dass alles stimmt, was man so runterlädt." [04:19]

### Katalog der Formulierungen

**Typ A — Vorbehalt mit Weiterarbeit** (der Befund bleibt trotzdem stehen):
- „Ich weise fairerweise nochmals darauf hin, dass das eine Auswertung von aussen ist. Es besteht die Möglichkeit, dass das nicht stimmt..." [14:14]
- „Also schlage ich vor, wir betrachten das mal als gegeben, bis die Bahn widerspricht." [14:36]
- „Aber wenn man das so anguckt, wir müssen noch ein bisschen abwarten, es ist noch nicht raus, ob das wirklich so wird. Also in zwei, drei Monaten wissen wir mehr..." [18:07]
- „Exakt die gleichen Werte werdet ihr nie kriegen." [28:48]
- „...wobei ich das auch nur reverse enginiere, die dokumentieren nicht alles. [...] Also auch das mit dem Körnchen Salz." [55:42 / 55:57]

**Typ B — offenes Nichtverstehen, ohne Absicherung:**
- „Aber vor allem, vielleicht ist die Erfüllungsquote auch was anderes, was ich hier nicht verstehe, keine Ahnung..." [34:41]
- „...und ob Sie wirklich so offen sind oder einfach vergessen haben zu googeln, weiss ich nicht." [27:06]
- „...das kann ich aus den Zahlen nicht ablesen, das müsst ihr dann für euch selbst entscheiden." [30:00]
- „aber nageln mich jetzt darauf nicht fest, ich habe es jetzt nicht im Kopf" [51:16]
- „Das taucht bei mir gar nicht auf, deswegen, da war ich mir auch nicht komplett sicher [...] Deswegen, wenn es falsch ist, stimmt es zumindest überein. Es kann sein, dass sie drin sind, ich bin mir nicht völlig sicher." [52:10–52:43]
- „ich habe mich da in die Theorie nicht eingearbeitet, es würde mich wundern, wenn du da eine Stabilität drüber nachweisen könntest [...] und wenn es schlecht aussieht, dann drückt man nochmal auf den Startknopf. Also so ist wirklich die Praxis." [56:33–56:53]
- „Dafür habe ich auch nichts Mass gefunden [...] aber nee, habe ich noch nicht gemacht." [49:54–50:04]

**Typ C — eigener Fehler, sofort in Nutzen umgemünzt.** Das ist die stärkste Figur. Der Fehler wird nicht bedauert, sondern zum Geschenk an den Leser:
```
[15:31] Man sieht zum Beispiel, dass ich zwischendurch Mist gebaut habe und ein
        paar Tage Daten verloren habe, wer meinen letzten Vortrag hier gesehen hat,
        dem wird das bekannt vorkommen.
[15:41] Ich mache das jeden Vortrag, aber ich war besser, diesmal war ich so klug,
        und dann habe ich mir ein vernünftiges Download-Monitoring gebaut, ja, und
        dann dachte ich, ich wäre cool, und dann habe ich es irgendwie geschafft,
        den Debian-Server [...] komplett zu crashen [...] und ich war da gerade in
        Urlaub und habe das nicht gemerkt.
[16:04] Also diesmal technischer Tipp für euch, baut nicht nur ein
        Download-Monitoring, sondern lasst das auch noch auf einem anderen Server
        laufen als den Download selbst.
```
Dasselbe bei SpiegelMining [05:23]: Datenloch → „also wenn ihr Daten aufnehmt, dann programmiert euch bitte mal irgendeine Form von Warnsystem, das anschlägt, wenn länger keine Daten mehr eintrudeln."

Der Fehler kostet ihn nichts, weil er ihn **als Erfahrung verkauft**. Und er relativiert seine eigene Verbesserung sofort wieder („diesmal war ich so klug [...] und dann habe ich es irgendwie geschafft, den Server zu crashen").

**Typ D — Selbstironie über frühere eigene Arbeit:**
- „Also bitte behandelt diese Daten, als wären sie mit Xeroxgeräten gescannt." [45:04] — Verweis auf seinen eigenen berühmten Xerox-Vortrag, in dem er einen Scanner-Bug fand, der Zahlen verfälschte. Er sagt damit: *meine Daten können genauso kaputt sein wie die, über die ich mich berühmt gemacht habe.*

**Typ E — Korrektur nach oben.** Er kann Unsicherheit auch als Dramaturgie nutzen: „habe ich euch vorhin gesagt, ich hätte hunderttausend Artikel von Spiegel online geladen, ich meinte über 700.000" [42:15]. Die Untertreibung am Anfang wird zur Überraschung am Ende.

**Typ F — Umgang mit Widerspruch aus dem Publikum.** Der wichtigste Beleg, weil hier die Autorität real auf dem Spiel steht. Ein Zuhörer greift den Bahnhofs-Befund methodisch an [53:03]:
```
[53:30] Also das ist eine exakt sehr geile Frage, weil diese Auswertung war in der
        Tat ein bisschen tricky, genau aus dem Grund.
[53:37] Vielleicht ist der Bahnhof Frankfurt die Verspätung gar nicht schuld,
        sondern die Gleise beim Rein- und Rausfahren zum Beispiel.
        [erklärt dann die Korrektur, die er tatsächlich eingebaut hat]
[54:19] Also danke für diese Frage.
[54:29] Da habe ich mir nämlich lange durch Gedanken zu gemacht [...] aber das
        hätte ich mir selbst als Statistik zerrissen, wenn ich da einen bei
        erwischt hätte, aber deswegen perfekt, dass es aufgefallen ist.
```
Er bedankt sich **zweimal** für einen Angriff, den er abwehren kann. Und bei SpiegelMining gibt er im Zweifel einfach nach: „Ja, wenn du genug Dimensionen benutzt, ist es eigentlich äquivalent." [56:12] — Zustimmung zum Fragesteller, ohne Gesichtswahrungsmanöver.

### Warum das keine Autorität kostet — vier Mechanismen

1. **Die Unsicherheit ist immer präzise begrenzt.** Nie „ich bin mir bei allem nicht sicher", sondern „bei *dieser* Kennzahl weiß ich nicht, wie sie definiert ist". Der Rest bleibt unberührt.
2. **Sie kommt vor dem Befund, nicht danach.** Vorab ist es Souveränität, hinterher wäre es Rückzug.
3. **Sie ist an ein Prüfangebot gekoppelt.** „könnt ihr selbst entscheiden, ob ihr meinen Daten vertraut" — und dann liefert er in Abschnitt 8 tatsächlich die Verifikation nach.
4. **Sie steht neben harten Aussagen.** Wer im selben Vortrag „keine Ahnung" und „das ist der finale Rettungsstuss" sagt, macht beide Aussagen glaubwürdiger. Die Kalibrierung ist das Signal, nicht die Bescheidenheit.

## 5. Wie er Methode erklärt

### Wann

**BahnMining: einmal, in der Mitte, geblockt.** Der Methoden-Einschub liegt bei 21:04–28:00, also nach 40 % des Vortrags — nach der ersten Befundwelle, vor dem Hauptangriff. Das ist kein Zufall: er braucht die Methodik als **Beleglizenz** für Abschnitt 9. Ohne den Nachweis, dass seine Zahlen mit denen der Bahn übereinstimmen, wäre der Vorwurf ab 31:55 haltlos.

**SpiegelMining: früh und dünn, dann verteilt.** Die Sammelmethode steht bei 03:02–04:21, dauert 80 Sekunden, und danach kommt Methodik nur noch **eingebettet in Befunde** (die drei Data-Science-Lektionen bei 08:48, die Federmetapher bei 22:47, die Visualisierungs-These bei 33:13).

Der Unterschied ist erklärbar: BahnMining greift eine Organisation an und braucht Beweislast. SpiegelMining will Bewusstsein erzeugen und braucht nur Plausibilität.

### Wie tief

Sehr flach — mit einer Ausnahme. Die einzige Stelle mit echter Rechnung ist die Nebenrechnung zum Download-Volumen [22:35–23:11]:

```
[22:38] Wir haben sechshalbtausend Bahnhöfe in Deutschland, für jeden müssen wir
        einzeln beides abrufen, also mal zwei, und jetzt sagen wir mal, wir machen
        das alle zehn Minuten [...] und das macht dann 6600 mal zwei mal 144, das
        sind knapp zwei Millionen Abrufe am Tag, so ein Abruf hat im Durchschnitt
        22 kb [...] und wir würden dann so bei 40 Gigabyte XML landen am Tag.
[23:11] Ja, das passt sich auch nicht mehr von alleine, für das ganze Jahr wären
        das dann 14 Terabyte in 700 Millionen Requests...
```

Und selbst die ist eine **Absurditätsrechnung**: das Ergebnis ist nicht die richtige Zahl, sondern der Beweis, dass der naive Weg unmöglich ist. Die Rechnung dient der Pointe („Herzanfall der Admins"), nicht der Reproduzierbarkeit.

Werkzeugnamen fallen fast nie im Vortrag, sondern erst in der Q&A auf Nachfrage („Python PyData Stack [...] Pandas [...] Tableau [...] Gaffy" [50:28–51:05]). Im Vortragskörper selbst: kein Code, keine Bibliothek, kein Algorithmusname. Die Ausnahme ist die Feder-Simulation, und die wird als Physik erklärt, nicht als Graph-Layout.

### Ein- und Ausstiegssignale, wörtlich

**Einstieg (BahnMining):**
```
[21:09] Ich schlage vor, wir machen jetzt einen Einschub und ich versuche, euch ein
        paar Anhaltspunkte zu geben, was ihr beachten solltet, wenn ihr
        Datenprojekte selber hochzieht.
[21:16] Und ich werde das kurz halten, sodass wir wieder in die Daten eintauchen
        können bald.
```
Zwei Sätze, drei Leistungen: Ankündigung, Nutzenversprechen („euch"), **Rückfahrkarte** („bald wieder in die Daten"). Er verspricht das Ende des Exkurses im selben Atemzug wie seinen Anfang.

**Ausstieg (BahnMining):**
```
[27:50] Und ich führe das jetzt mal vor, und dann könnt ihr entscheiden, ob ihr
        meinen Daten vertraut, und ausserdem ist das jetzt unsere Ausrede, dass wir
        diesen Einschub verlassen und endlich wieder in die Daten reingucken.
```
Er nennt den Exkurs selbst eine Belastung („unsere Ausrede", „endlich"). Damit stellt er sich neben das Publikum statt darüber.

**Weitere Signale:**
- **Nummerierung als Fortschrittsbalken:** „Punkt 1, organisiert den Download gut" [21:20] … „Punkt zwei handelt verantwortungsvoll" [23:55] … „Punkt drei fliegt unter dem Radar" [24:54] … „Punkt vier" [25:59] … „Punkt fünf, habe trotz Hindernissen den Mut, es einfach zu tun" [26:26] … „Punkt sechs, seid fair bei der Auswertung" [27:31] … „Und das Wichtigste zuletzt, Punkt sieben, guckt, ob ihr euren eigenen Daten vertrauen könnt" [27:43]. Sieben Punkte in sieben Minuten. Der Leser weiß jederzeit, wie weit es noch ist.
- **Entlastung vor Überforderung:** „Damit ich euch nicht abschrecke, so ein Aufwand müsst ihr nicht bei jedem Datenprojekt treiben, das war vielleicht ein bisschen Overkill, weil ich das mal ausprobieren wollte mit den Proxys." [25:49]
- **Fachsatz, dann Umgangssprach-Übersetzung im nächsten Satz:**
  ```
  [20:00] ...dann habe ich geguckt, wie viel Prozent bauen auf dem Rest ihrer Fahrt
          fünf % der Verspätung ab und existieren noch, also sind nicht ausgefallen.
  [20:23] Hört sich jetzt kompliziert an, aber kurz, wie viel Prozent werden noch
          mal spürbar besser, oder war es das jetzt?
  ```
- **Fachbegriff erst nach der Sache:** Er zeigt erst den Vergleich mit den Bahn-Kennzahlen, *dann* sagt er, wie das heißt: „Das heisst externe Verifikation, weil wir was Externes zum Vergleichen hatten, jetzt kommt die interne" [29:04].
- **Begriff bei Erstnennung glossieren:** „Feature ist einfach das Fachwort für ein Artikelmerkmal." [03:53] · „in der Fachsprache heissen die anonyme Proxies" [25:09] · „das heisst dann Voter-Targeting" [36:59].
- **Metapher kalibrieren:** „mit so ganz strammen, dicken Federn. Ich meine jetzt wirklich Federn im physikalischen Sinne" [22:47] — er sagt dazu, wie wörtlich das Bild zu nehmen ist.
- **Rückblick als Ausstieg (SpiegelMining):** „Und jetzt können wir die Gelegenheit nutzen und einen Schritt zurücktreten und gucken, was wir bis jetzt gemacht haben" [21:01] · „Jetzt treten wir wieder einen Schritt zurück" [35:32] · „Und wir halten jetzt mal inne, und dann machen wir uns noch mal klar, was wir gerade gesehen haben" [16:16].
- **Selbstabwertung als Ausstieg aus technischem Frust:** „Also, Data Science kann technisch nervig sein, sagt nicht, ich hätte euch nicht gewarnt." [19:25]

### Der Abschluss der Methode ist immer ein Vertrauensangebot

Punkt 7 des Einschubs ist nicht „so rechnet man richtig", sondern:
```
[27:43] Und das Wichtigste zuletzt, Punkt sieben, guckt, ob ihr ehren eigenen Daten
        vertrauen könnt, und das ist gar nicht so einfach.
[28:00] Am besten schafft ihr Vertrauen in euren Datensatz, indem ihr mal eine
        Analyse komplett nachbaut, die die Quelle des Datensatzes [...] schon mal
        gemacht hat.
```
Und dann führt er es vor: Bahn-Monatswerte nachgerechnet, Abweichung 0,1 Prozentpunkte, die zwei größten Abweichungen benannt und **beide gegen sich selbst erklärt** (später gestartet, Tage verloren) [28:26–28:48]. Danach: „Ansonsten scheint bei mir die Bahn sogar generell minimal besser wegzukommen." [28:43] — er sagt sogar, in welche Richtung sein Fehler geht.

## 6. Der Humor

### Woraus er entsteht — sechs Quellen

**(1) Selbstironie / Selbstabwertung** — die häufigste.
- „In 20 Jahren werde ich diese Witze immer noch machen können." [05:51, 8,7 s] — über den BER-Gag, den er gerade gemacht hat.
- „Ich mache das jeden Vortrag" [15:41] — Datenverlust.
- „Jetzt versagt meine Singstimme." [24:57, SpiegelMining]
- „Jetzt habe ich mir einen PowerPoint abgeschossen." [58:27]
- „Also bitte behandelt diese Daten, als wären sie mit Xeroxgeräten gescannt." [45:04, 8,2 s]

**(2) Untertreibung direkt nach einer großen Zahl.**
- „also nehmt das nicht auf die leichte Schulter, das ist jetzt wirklich grosse Mathematik bahnbrechend sozusagen" [36:08, 11,2 s] — über eine Division.
- „Die zwei Hände, drei im Saal von 5000 Mann, okay, ist messbar" [33:19]
- „Es geht, ja, es ist keine Raketenwissenschaftliche." [61:10]
- „bahnbrechende Erkenntnis, auch der Spiegel-Online-Redakteur möchte immer schlafen" [09:04]

**(3) Die Absurdität der Daten selbst** — der Witz gehört dem Befund, nicht dem Sprecher.
- „Das heisst, wir haben insgesamt 103 % Fernverkehr." [34:34, 3,0 s]
- „Es gibt tatsächlich etwas an Berlin, das funktioniert." [11:25, 2,3 s] — davor: „Das hat mich sehr kalt erwischt, dass mir völlig unverhofft ein Nachweis dieser Grössenordnung gelungen ist." [11:17, 5,8 s]
- „Als der Artikel rauskam, wuchs nämlich nicht SAP, sondern der SAP-Chef wuchs langsamer als geplant." [43:47, 2,7 s]
- „Russenbashen ist okay." [34:06, 10,8 s] — größter Lacher des SpiegelMining-Vortrags und gleichzeitig der Befund.

**(4) Amtsdeutsch entlarven, indem man es beim Namen nennt.**
- „ich nenne sowas den finalen Rettungsstuss" [34:59, 9,3 s]
- „die Scheuerwende oder aber [...] die Pufala-Wende" [39:38]
- „deren Putschversuch und deren Demokratur" [26:30]

**(5) Komplizenschaft mit dem Publikum** — der Witz setzt geteiltes Wissen voraus.
- „auch herzlich willkommen an die Leute im Stream und an die Alu-Hüte im Besonderen. Die Alo-Hüte glühen aber leider noch nicht, vielleicht kriegen wir das im Verlaufe dieses Vortrages noch hin." [01:04–01:14] — und er löst das ein: „da glüht der Aluhut, wirklich" [38:46, SpiegelMining].
- „die sind erstaunlich schwach auf Verbus. Habe ich gehört." [24:07 / 24:18, 9,8 s] — der Nachsatz macht den Lacher.
- „es liegt mir fern, da jetzt von der Seitenlinie ohne tieferes Wissen altkluge Ratschläge zu erteilen, wir sind hier nicht auf Twitter" [40:20]
- „Ich würde ja mitlachen, aber ich bin mit dem Flugzeug hier in Hamburg." [32:05, 2,7 s]

**(6) Metahumor über die Reaktion selbst** — nur live möglich.
- „Drei Sekunden reichen auch." [05:04, 4,2 s] — nachdem er fünf Sekunden zum Lesen angeboten hat.
- „Ihr klatscht ja schon vorher, so kann ich nicht arbeiten." [37:45, 4,5 s]
- „das Gelächter geht los, bevor ich etwas gesagt habe, ihr wisst doch gar nicht, was ich sagen will" [28:30]
- „Aber ganz ehrlich, das könnte jetzt mal ein Applaus für die Bahn wert sein" [27:15, 9,3 s] — er ordnet Applaus für die Gegenseite an.

### Wo der Humor im Bogen sitzt

**Regel 1 — direkt VOR dem Zahlenschlag als Verzögerung.** Belegt an der stärksten Stelle des Vortrags: die 11,2-Sekunden-Pause bei 36:19 sitzt zwischen der neuen Metrik und der Zahl 72,5 %. Die Zahl fällt in absolute Stille.

**Regel 2 — direkt NACH einem Vorwurf als Druckablass.** Nach dem Verlesen des Bahn-Zitats über Ausfälle kommt binnen 30 Sekunden „103 % Fernverkehr" [34:34] und „finaler Rettungsstuss" [34:59]. Ohne das würde der Abschnitt in Empörung kippen — genau das, was Kriesel im Schlussteil kritisiert.

**Regel 3 — der ernsteste Block ist humorfrei und wird explizit ein- und ausgeleitet.** Bei SpiegelMining läuft 16:16–18:25 (Metadaten, Vorratsdatenspeicherung, Orwell) ohne einen einzigen Gag. Er kommt aus dem größten Lacher-Block des Vortrags (Urlaube/Affären, 15:07–16:03) und beginnt mit einer Bremse:
```
[16:16] Und wir halten jetzt mal inne, und dann machen wir uns noch mal klar, was
        wir gerade gesehen haben und was die gesellschaftlichen Implikationen sind.
```
Und danach schaltet er hörbar zurück:
```
[18:29] Jetzt haben wir einen kurzen Exkurs über Metadaten gemacht, und wir gehen
        jetzt zurück zu Spiegel Online, damit sich eure Laune wieder hebt.
```
Das ist die klarste dramaturgische Ansage in beiden Vorträgen: **Lachen — Ernst — Ansage, dass jetzt wieder gelacht werden darf.**

**Regel 4 — im Schlussteil verschwindet der Humor.** BahnMining ab 46:20 (Jahrzehnt-Reflexion) enthält keinen Gag mehr. Der letzte Lacher liegt bei 46:38 (9,0 s, nach „Ich glaube, hat jeder was"), danach folgen drei Minuten ohne eine einzige Pointe. Die letzte Aussage bekommt keinen Schutz durch Humor.

**Regel 5 — Selbstironie steht immer dort, wo er sonst überlegen wirken würde.** Direkt nach dem Lufthansa-Lacher: „Ich würde ja mitlachen, aber ich bin mit dem Flugzeug hier in Hamburg." [32:05] Direkt nach den Datenvorbehalten: der Xerox-Vergleich. Direkt nach dem Bahn-Verriss: „ich bin jedenfalls, obwohl ich das alles gesehen habe, mit der Bahn zum Kongress gefahren" [45:48].

## 7. Haltung zu den Betroffenen

Das ist der übertragbarste Befund. Kriesel greift die Bahn und den Spiegel hart an, ohne dass es je nach Häme klingt. Neun konkrete Mechanismen, jeweils belegt.

**(1) Die Definition des Gegenübers wird freiwillig übernommen.**
```
[02:16] Die sagen, wenn ein Zug bei einem Stopp weniger als sechs Minuten zu spät
        ankommt, dann ist er pünktlich.
[02:25] Das ist wirklich die Definition, und wir übernehmen das einfach, dann
        müssen wir da nicht handeln irgendwie.
```
Er misst den Gegner an dessen eigenem Maßstab. Der Kritisierte kann die Methodik nicht bestreiten, weil es seine eigene ist. (Erst in der Q&A wird auf Nachfrage klar, dass er auch strengere Maße durchgerechnet hat — er hätte also die Möglichkeit gehabt, härter zu messen, und hat es im Vortrag nicht getan.)

**(2) Die Entlastung kommt VOR dem Angriff, unaufgefordert und mit Nachdruck.**
```
[09:16] ...aber wenn ich sage, dass ich hier primär über den Fernverkehr heute
        rede, dann muss ich auch fair sein und das Folgende sagen, der Nahverkehr,
        den wir jetzt auslassen, erreicht fast flächendeckend Pünktlichkeitswerte
        von besser als 90 %.
[09:41] Behalte das bitte über den Rest des Vortrages im Hinterkopf, die Bahn hat
        auch gute Seiten und bringt gerade im Nahverkehr eine ziemliche Menge Leute
        jeden Tag zu ihrem Job, da geht sicher auch mal was schief, aber deutlich
        weniger als im Fernverkehr.
[09:54] Und jetzt, ich hoffe, die Leute von der Bahn hören zu und hören das jetzt
        gerade.
```
Drei Sätze, 38 Sekunden, mitten in der ersten Befundwelle. Und der letzte Satz macht die Entlastung zur Botschaft an die Betroffenen selbst.

**(3) Der eigene Ausgangsverdacht wird öffentlich widerlegt.**
```
[08:31] ...und ich habe euch ja gesagt, dass ich das ganze Projekt überhaupt erst
        gestartet habe, weil ich dachte, die Statistik der Bahn wäre falsch, weil
        meine Züge so häufig unpünktlich sind, die simple Wahrheit ist, ich wohne
        nur schlecht.
```
Die Motivation für den ganzen Vortrag war ein Irrtum, und er sagt das nach acht Minuten, in einem Halbsatz, ohne Drama.

**(4) Er verteidigt den Kritisierten gegen Dritte.**
```
[18:58] ...wenn ihr sowas seht, lasst mich euch sagen, die machen die Bahn
        schlimmer, als sie ist...
[19:16] ...die häufigen Probleme mit den japanischen Hochgeschwindigkeitszügen sind
        aus meiner Sicht auch einfach Stuss [...] also das ist nicht vergleichbar,
        so fair müssen wir schon sein.
[13:07] ...aber man muss auch fair sein, die fahren internationaler als der Rest
        der Züge, und wenn die direkt von aussen Verspätung mitbringen, kann die
        Bahn da nichts für, und solche Fälle gibt es.
[31:26] ...aber wir sehen, nicht immer ist die Bahn schuld.
```

**(5) Er ordnet Applaus für den Kritisierten an.**
```
[26:47] Ich habe dann gepokert und wirklich bei der Bahn nachgefragt, ob ich
        automatisiert Daten drunter laden [...] darf.
[27:06] Und Sie haben es mir genehmigt, ohne weitere Auflagen, ohne Auflagen...
[27:15] Aber ganz ehrlich, das könnte jetzt mal ein Applaus für die Bahn wert sein
        → 9,3 s Applaus
[27:29] Ich hoffe, die hören zu.
```

**(6) Die Kritik wird auf einen einzigen Satz eingegrenzt — und die Wertung ist zwei Wörter lang.**
```
[40:12] Und aus Gründen der Neutralität muss ich dazu sagen, die Bahn hat natürlich
        ein Interesse daran, dass das ganze Zugnetz ungefähr im Plan ist. Also
        werden die sich denken, dass bei so einem Manöver nicht so viele Passagiere
        von den Ausfällen betroffen sind [...] ist eben deren Geschäftsentscheidung,
        und es liegt mir fern, da jetzt von der Seitenlinie ohne tieferes Wissen
        altkluge Ratschläge zu erteilen, wir sind hier nicht auf Twitter.
[40:46] Und was ich hier kritisieren möchte, ist aber, dass ausschliesslich die
        positive Seite des Manövers danach in der Statistik auftaucht und die
        negative einfach verschwindet.
[40:56] Das stört.
```
Er kritisiert nicht das Verhalten, sondern die **Buchführung über das Verhalten**. Und die Wertung ist „Das stört." — nicht „Das ist ein Skandal."

**(7) Das Recht der Gegenseite wird ausdrücklich anerkannt, bevor das eigene reklamiert wird.**
```
[35:32] Jetzt treten wir wieder einen Schritt zurück, und natürlich sehe ich auch,
        dass der Spiegel Themenbereiche einfach aufgrund von Erfahrungen der
        Vergangenheit sperren kann.
[35:42] Und generell müssen wir auch zugeben, es ist das gute Recht von Spiegel
        Online, zu entscheiden, wo und in welcher Form sie anderen auf Ihrer Seite
        eine Plattform geben und wo sie das eben nicht tun.
[35:53] Aber genauso ist es halt auch unser gutes Recht, diese Systematik hier mal
        sichtbar zu machen.
```
Recht gegen Recht, nicht Gut gegen Böse. Und direkt danach die Rückgabe der Deutung: „Ob das jetzt was über Spiegel Online aussagt oder über seine Leser oder irgendwie ein gesamtgesellschaftliches Problem ist, das müsst ihr dann wieder selbst entscheiden." [36:11]

**(8) Häme wird als Methodenfehler deklariert, nicht als Geschmacksfrage.**
```
[08:00] Und bevor das jetzt hier falsch ankommt, ich sage das ohne jede Wertung im
        Sinne von gut oder schlecht, das ist ja eine valide Strategie für ein
        Medium, und ich beschreibe einfach nur gemessene Daten, und es ist
        keineswegs der Zweck der Veranstaltung, irgendwie substanzlos in Richtung
        von Spiegel Online zu haten.
[08:15] Wer hatet, wird nicht ernst genommen, das habe ich ja in meinem letzten
        Vortrag schon ausführlich beschrieben.
[08:19] Und die meisten Sachen, die hier im Vortrag noch kommen, denkt daran, die
        sind bei den anderen wahrscheinlich ähnlich.
```
Der letzte Satz ist der wichtigste: **er verhindert, dass der Untersuchte zum Sündenbock wird.** Was er beim Spiegel findet, findet man anderswo auch — das Objekt ist zufällig, das Muster nicht.

**(9) Der Fehler des Betroffenen wird als Menschlichkeit gelesen.**
```
[43:47] Als der Artikel rauskam, wuchs nämlich nicht SAP, sondern der SAP-Chef
        wuchs langsamer als geplant.
[43:57] Sowas finde ich an sich ganz sympathisch, denn es zeigt, dass bei Spiegel
        Online noch Menschen an den Texten sitzen und keine Computer...
```
Und: „Ich muss übrigens mal was Positives sagen, die Spiegel-Plus-Artikel sind im Median 1100 Worte lang, also man muss schon sagen, da kriegt ihr auch was fürs Geld." [49:18] — unaufgefordert, in der Q&A, wo niemand danach gefragt hat.

**Zusätzlich: er bleibt im Boot.** „Ich bin jedenfalls, obwohl ich das alles gesehen habe, mit der Bahn zum Kongress gefahren und werde das auch auf dem Rückweg machen." [45:48] · „Ich war bei Spiegel Online eingeladen im Oktober [...] das war eigentlich ein ziemlich cooler Termin, also sportlicher als die Kollegen bei Xerox, sage ich mal." [55:14] · Und er anonymisiert: „Jetzt wisst ihr auch, warum ich die Autoren hier anonymisiert habe." [15:42]

**Für den ehrenamtlichen Wiki-Administrator in unserem Text** heißt das konkret: Punkt (2), (6), (8) und (9) sind die tragenden. Die Entlastung muss vor dem Befund stehen und darf keine Floskel sein. Die Kritik darf nicht der Person, sondern nur einer benennbaren Mechanik gelten. Es muss gesagt werden, dass andere Wikis dasselbe Problem hätten. Und der Fehler, den man findet, sollte als Folge von Bedingungen lesbar sein, unter denen jeder denselben Fehler machen würde.

## 8. Der Schluss

### BahnMining — zwei Schlüsse hintereinander

**Erster Schluss (Sachebene), 45:00–46:06:**
```
[45:17] Und wenn ihr doch pünktlich da sein müsst, dann ist das ja auch ein gutes
        Zeichen, weil es nichts anderes bedeutet, als dass die Bahn was verbessert,
        Verbesserungen passieren, nämlich durchaus.
[45:28] Dieses Jahr wurde zum Beispiel die ECE-Trasse zwischen München und Berlin
        ausgebaut [...] und wenn das rundläuft, ist das echt meine Alternative zum
        Flug.
[45:41] Es ist also nicht alles schlecht.
[45:43] Also ich hoffe, auch ich bin bei aller Kritik fair mit der Bahn umgegangen
        heute.
[45:48] Ich bin jedenfalls, obwohl ich das alles gesehen habe, mit der Bahn zum
        Kongress gefahren und werde das auch auf dem Rückweg machen.
[45:56] Und für heute möchte ich damit die Bahnbetrachtung abschliessen mit den
        Worten, seid nett zur Bahn mit ihren Fehlern, wir haben nur diese eine.
```
Der Sachteil endet mit einem **Fürsprache-Satz**, nicht mit einem Ergebnis. Er sagt ausdrücklich, dass er den Abschnitt abschließt („für heute möchte ich damit die Bahnbetrachtung abschliessen") — der Leser weiß, dass jetzt etwas anderes kommt.

**Der Scharnier-Satz, 46:06:** „Und was bleibt?" — 8,2 Sekunden Pause. Drei Wörter, und der Vortrag wechselt die Ebene.

**Zweiter Schluss (Bedeutungsebene), 46:20–49:30.** Er verlässt das Thema komplett: Jahrzehnt-Bilanz, „Aufstieg der Empörten", Paradox zwischen propagierter Rationalität und akzeptierter Empörung, Appell an eine andere Streitkultur, Absage an Medien/Stars/Politiker als Träger davon, und dann die Begründung für die ganze Veranstaltung:
```
[48:22] Und das ist der Grund, warum ich das hier mache. Ich versuche, euch zu
        inspirieren, eure eigenen Analysen zu strittigen Themen anzustellen [...]
        und ich hoffe, ich habe euch bewiesen, dass das absolut keine
        Raketenwissenschaft ist.
```

**Der letzte inhaltliche Satz, 49:01–49:28:**
```
[49:01] Und heute Abend stehe ich hier in einem Saal mit 5000 Leuten voll belegt,
        da sitzen sie noch neben der Tribüne, mit 5000 Leuten, die sich am
        Samstagabend zwischen Weihnachten und Silvester hier hinsetzen, also da, wo
        die allermeisten Menschen einfach gar nichts tun und sich die Flasche Wein
        an den Hals anschliessen.
[49:20] Und warum tun die 5000 Leute das?
[49:24] Um einen Statistikvortrag zu hören.
[49:28] Ja, das gibt mir Hoffnung.
```
Und dann, als Abgang: „Ich werde glücklich heimfahren, da kann die Bahn mit mir machen, was sie will, und ich bedanke mich, dass ihr hier wart und wünsche euch ein schönes neues Jahr." [49:30]

**Was der Schlusssatz leistet — vier Dinge gleichzeitig:**
1. Er **beweist die These des Schlussteils mit dem Publikum selbst als Datenpunkt.** Die Behauptung war: Analyse statt Empörung ist möglich. Der Beleg: 5000 Leute sitzen freiwillig in einem Statistikvortrag. Er misst noch im letzten Satz.
2. Er **gibt dem Zuhörer eine Rolle** — nicht Konsument des Befunds, sondern Beleg für die Hoffnung.
3. Er **schließt den Bahn-Faden im Nebensatz** („da kann die Bahn mit mir machen, was sie will") — versöhnt, entwaffnet, ohne Groll. Der Angriff wird zurückgenommen, ohne widerrufen zu werden.
4. Er **macht sich selbst klein**: der letzte Ich-Satz ist „ich bedanke mich, dass ihr hier wart."

### SpiegelMining — Öffnung statt Abschluss

```
[45:23] Also meine Bitte an euch, jeder, der hier zuguckt, schickt mir bitte eine
        Mail mit seinen kreativsten Auswertungsideen für den Datensatz.
[45:33] Und in dem Zusammenhang habe ich noch eine Message, die ihr euch auch
        mitnehmen könnt, wenn ihr was im Bereich der Data Science macht, Rohdaten
        sind geil.
        → 13,7 s (größte Pause des Vortrags)
[45:54] Behaltet immer alle Rohdaten, wenn ihr es irgendwie vom Speicher bezahlen
        könnt, dann könnt ihr nämlich im Nachhinein alles Mögliche tun.
[46:10] Darum bitte, bitte, lasst eurer phantasie freien Lauf, erfindet neue
        Features [...] vielleicht ist nicht alles, was ihr wollt, möglich, und
        vielleicht schaue ich auch nicht alles sofort, ich bin ja auch berufstätig
        [...] aber ich versuche, was möglich zu machen, also einfach einschicken,
        seid kreativ.
[46:32] Und damit bleibt es mir nur noch, ein dickes Dankeschön zu sagen dafür,
        dass ihr diese Stunde mit mir verbracht habt.
```

**Der letzte inhaltliche Satz ist „seid kreativ."** Er leistet:
1. **Übergabe der Werkzeuge statt Übergabe eines Ergebnisses.** Der Vortrag endet nicht mit dem, was er weiß, sondern mit dem, was noch nicht ausgewertet ist.
2. **Absenkung der eigenen Position** — im selben Absatz sagt er, dass er wahrscheinlich nicht alles schaffen wird und berufstätig ist.
3. Er verwandelt Zuhörer in Mitarbeiter. Die Q&A liefert prompt drei Vorschläge, die er annimmt („Guter Punkt. Machen wir so." [52:08], „könntest du mir bitte damit eine E-Mail schicken?" [57:06]).

### Gemeinsames Prinzip beider Schlüsse

**Der letzte inhaltliche Satz handelt nicht vom Untersuchungsgegenstand, sondern vom Leser.** Bahn: „Und warum tun die 5000 Leute das? Um einen Statistikvortrag zu hören. Ja, das gibt mir Hoffnung." Spiegel: „seid kreativ." In beiden Fällen ist der Analysegegenstand am Ende nicht mehr das Thema. Das Thema ist, was der Zuhörer damit macht.

---

# TEIL B — DIE BAUANLEITUNG

Zielformat: **deutscher Blogartikel über eine Datenanalyse**, Richtgröße 3.000–3.800 Wörter. Die Wortbudgets summieren sich auf ca. 3.400. Wer kürzer schreibt, kürzt proportional — aber Baustein 3, 6, 9 und 12 dürfen nie ganz wegfallen, das sind die tragenden.

Jeder Baustein hat: **(a) Funktion** — was er im Kopf des Lesers bewirkt · **(b) Länge** · **(c) Füllregel** — die operative Anweisung.

---

### Baustein 1 — Die fremde Behauptung
**(a) Funktion.** Den Konflikt aufmachen, bevor der Autor überhaupt existiert. Der Leser soll wissen, worüber gestritten wird, nicht wer schreibt.
**(b) Länge.** 60–100 Wörter, 1–2 Absätze.
**(c) Regel.** Beginne mit einer Zahl oder Aussage, **die nicht von dir stammt** — die offizielle Version, die Selbstbeschreibung, die verbreitete Annahme. Nenne sie ohne Ironie. Nenne im selben Atemzug, **wie sie definiert ist**, und übernimm die Definition ausdrücklich („wir übernehmen das einfach"). Wer die Definition des Gegenübers benutzt, kann später nicht auf Methodik verklagt werden.
*Nicht mit deinem Befund anfangen. Nicht mit deiner Methode. Nicht mit dir.*

### Baustein 2 — Der persönliche Reibungspunkt
**(a) Funktion.** Motivation liefern und zugleich die eigene Fehlbarkeit vorführen. Der Leser soll denken: „der hat sich geärgert, nicht der hat ein Programm geschrieben."
**(b) Länge.** 80–120 Wörter.
**(c) Regel.** Erzähle in einem Satz die konkrete Alltagserfahrung, die zum Zweifel führte — mit einem greifbaren Detail (eine E-Mail, eine Uhrzeit, ein Ort). Erlaube dir dabei genau ein Bild („der eine Typ, der aufpassen muss, nicht vom Blitz getroffen zu werden, während er den Sechser im Lotto abholt"). Erkläre dann **in zwei Sätzen, warum die öffentlich verfügbaren Daten nicht reichten**, um den Zweifel zu klären. Das ist die Rechtfertigung für alles Folgende.

### Baustein 3 — Der Vertrag
**(a) Funktion.** Erwartung setzen und die Angreifbarkeit vorwegnehmen. Nach diesem Baustein weiß der Leser, was er bekommt und was er nicht bekommt.
**(b) Länge.** 100–140 Wörter.
**(c) Regel.** Drei Elemente, in dieser Reihenfolge:
1. **Was kommt** — nummeriert („erstens Befunde, zweitens wie man das selbst macht, drittens was das bedeutet").
2. **Was der Leser mitnimmt** — konkret, nicht „Erkenntnisse", sondern „Sie werden beim nächsten Mal X anders machen".
3. **Der Vorbehalt** — Umfang klein reden („ein Nebenprojekt"), Fehler zugeben („es kann sein, dass ich mich irre"), und **die Prüfung abgeben** („Sie können am Ende selbst entscheiden, ob Sie meinen Zahlen trauen — Baustein 9 liefert Ihnen dafür das Material").
Der dritte Teil ist keine Bescheidenheit, sondern ein Versprechen, das später eingelöst werden muss. Wer ihn schreibt, muss Baustein 9 liefern.

### Baustein 4 — Die Atomeinheit
**(a) Funktion.** Der Leser lernt, was ein einzelner Datenpunkt ist, bevor ihm Millionen davon zugemutet werden. Ohne diesen Baustein sind alle späteren Zahlen bedeutungslos.
**(b) Länge.** 120–180 Wörter, **plus eine Abbildung**.
**(c) Regel.** Zeige **einen einzigen echten oder erfundenen Fall** vollständig — eine Zeile, ein Datensatz, eine Fahrt, eine Sitzung. Beschrifte jede Spalte, die später vorkommt, und nur die. Nenne dann in **einem** Satz die Gesamtmenge („meine Tabelle hat 25 Millionen Zeilen"). Reihenfolge zwingend: erst der eine Fall, dann die Million.
**Text-Entsprechung zur Live-Geste.** Kriesel sagt „Ich gebe euch mal kurz fünf Sekunden für den ersten Überblick" [05:00] und lässt schweigen. Im Text: eine Abbildung mit einer Bildunterschrift, die **die Frage stellt statt die Antwort zu geben** („Fällt Ihnen die vorletzte Zeile auf?"), und die Auflösung erst im nächsten Absatz. Die Pause selbst ist nicht übertragbar.

### Baustein 5 — Die Eskalationstreppe
**(a) Funktion.** Vertrautwerden mit den Daten, in aufsteigender Temperatur. Am Ende dieses Bausteins soll der erste echte Befund stehen — und der Leser soll das Gefühl haben, er habe ihn selbst kommen sehen.
**(b) Länge.** 500–700 Wörter, 4–6 Stationen.
**(c) Regel.** Baue drei bis fünf **bewusst langweilige** Auswertungen vor die erste interessante. Sag ausdrücklich, dass sie langweilig sind („das ist nicht, um euch zu langweilen, aber wir müssen ja erst mal reinkommen" [06:33]). Jede Station braucht genau einen Satz Ergebnis und höchstens einen Satz Kommentar. Die Reihenfolge ist: **Größe → Verteilung → Vergleich → Abweichung → der erste Befund.** Der erste Befund muss die Stelle sein, an der auch du überrascht warst — und das sagst du: „das war für mich überraschend" [13:39].

### Baustein 6 — Die Zangenbewegung (Kernbaustein, mehrfach verwendet)
**(a) Funktion.** Einen Befund so absichern, dass er nicht mehr angreifbar ist. Dieser Baustein ist kein Abschnitt, sondern eine **Form**, die du bei jedem wichtigen Befund wiederholst — im Blogtext drei- bis viermal.
**(b) Länge.** 120–200 Wörter pro Anwendung.
**(c) Regel.** Sechs Schritte, keiner darf fehlen:
1. **Befund** — die Rohzahl, nackt.
2. **Übersetzung** — dieselbe Zahl als erlebbare Häufigkeit („einer von zwanzig", „jeder zwölfte", „mehr als siebeneinhalb Stunden").
3. **Eigene Reaktion** in Alltagssprache — ein kurzer Satz, subjektiv („das fand ich ganz schön stramm").
4. **Selbstangriff** — der stärkste Einwand gegen deinen eigenen Befund, von dir formuliert, bevor der Leser ihn hat. Nicht der schwächste. Der stärkste.
5. **Gegenprüfung** — warum der Einwand den Befund nicht kippt, mit Beleg: unabhängige Quelle, Kontrollgruppe, Größenordnungsargument.
6. **Engere Behauptung** — was jetzt noch steht, in einer schärferen und schmaleren Formulierung als in Schritt 1 („wir betrachten das mal als gegeben, bis X widerspricht").
Wer Schritt 4 auslässt, schreibt einen Verriss. Wer Schritt 6 auslässt, schreibt eine Relativierung. Nur beide zusammen ergeben eine belastbare Aussage.

### Baustein 7 — Die Belohnung
**(a) Funktion.** Der Leser bekommt etwas, das er heute anwenden kann. Ohne diesen Baustein ist der Text ein Bericht; mit ihm ist er ein Werkzeug.
**(b) Länge.** 20–40 Wörter pro Stück, **3–6 Stück über den Text verteilt**, plus eine Sammelliste von 60–80 Wörtern vor dem Schlussteil.
**(c) Regel.** Nach jedem Befundblock eine handlungsfähige Konsequenz in **einem** Satz, immer in derselben Formulierung eingeleitet, damit sie wiedererkennbar wird (Kriesel: „Mein Praxistipp an euch lautet also..." [14:09], „Praxistipp für euch also..." [20:56], „hier mein nächster Praxistipp für euch..." [17:55]). Die Wiederholung des Wortlauts ist Absicht — sie macht die Tipps im Text auffindbar.
Vor dem Schlussteil eine **Sammelliste aller Tipps** in einem Absatz, damit der Leser sie zusammen hat [vgl. 41:03].

### Baustein 8 — Der Methoden-Einschub
**(a) Funktion.** Vertrauen aufbauen und den Leser in die Lage versetzen, es selbst zu tun. Und: Ruhephase vor dem Hauptangriff.
**(b) Länge.** 400–550 Wörter. Nicht mehr.
**(c) Regel.**
- **Platzierung:** nach der ersten Befundwelle, vor dem härtesten Befund — bei etwa 40 % der Textlänge.
- **Eintrittssignal mit Rückfahrkarte:** ankündigen, Nutzen benennen, Ende versprechen, alles in zwei Sätzen („Ich halte es kurz, damit wir schnell wieder in die Daten kommen").
- **Nummerierung als Fortschrittsbalken.** Fünf bis sieben Punkte, jeder mit einer imperativen Überschrift von 3–5 Wörtern („Organisiere den Download gut", „Handle verantwortungsvoll", „Sei fair bei der Auswertung"). Der Leser sieht jederzeit, wie weit es noch ist.
- **Eine einzige Rechnung**, und die muss eine Pointe haben — sie soll zeigen, dass der naive Weg absurd ist, nicht wie man richtig rechnet.
- **Keine Werkzeugnamen im Fließtext.** Bibliotheken, Versionen, Repos gehören in eine Fußnote oder einen Kasten am Ende.
- **Jeder Fachbegriff wird bei Erstnennung glossiert** oder er kommt nicht vor. Oder besser: erst die Sache erklären, dann sagen, wie sie heißt.
- **Austrittssignal:** den Exkurs selbst als Zumutung benennen und die Rückkehr feiern („und damit haben wir die Ausrede, endlich wieder in die Daten zu gucken").

### Baustein 9 — Die Verifikation
**(a) Funktion.** Die Lizenz für den Hauptangriff. Ohne diesen Baustein ist alles Folgende eine Meinung.
**(b) Länge.** 250–350 Wörter.
**(c) Regel.** Zwei Prüfungen, in dieser Reihenfolge:
1. **Extern** — rechne eine Zahl nach, **die die Gegenseite selbst veröffentlicht hat**, mit deren eigener Methode. Zeige die Abweichung. Nenne die **zwei größten Abweichungen** und erkläre beide **zu deinen Lasten** („da fehlen mir Tage"). Sag, in welche Richtung dein Restfehler geht („bei mir kommt die Bahn sogar minimal besser weg").
2. **Intern** — zeige, dass die Daten sich plausibel verhalten, an einem Ereignis, dessen Ausgang unabhängig bekannt ist (ein Sturm, ein Ausfalltag, ein Feiertag). Wenn deine Daten das Ereignis zeigen, funktionieren sie.
Schließe mit einem Satz, der die Grenze zieht: „Exakt dieselben Werte werden Sie nie bekommen."
**Und dann der einzige Satz, der wirklich zählt:** *Danach*, und nur danach, darfst du angreifen.

### Baustein 10 — Der Hauptbefund
**(a) Funktion.** Das eigentliche Ergebnis. Der Grund, warum es den Text gibt.
**(b) Länge.** 400–550 Wörter.
**(c) Regel.**
- **Erst die Intuition des Lesers abholen.** Kriesel bittet um Handzeichen („ihr steht am Bahnsteig und der Zug fällt aus — ist der pünktlich oder unpünktlich?" [33:03]). *Text-Entsprechung:* Stelle die Frage direkt an den Leser und beantworte sie im nächsten Absatz **so, wie er geantwortet hätte** („Sie würden sagen: unpünktlich. Ich auch."). Die Abstimmung selbst ist nicht übertragbar; das Vorwegnehmen der Antwort ist es.
- **Dann das Originalzitat der Gegenseite.** Wörtlich, ungekürzt, ohne Kommentar davor. Kriesel liest die Bahn-Unterlagen vor und sagt vorher nur: „ihr müsst das nicht lesen, ich lese euch das vor" [33:39].
- **Dann die sachliche Zerlegung**, Punkt für Punkt, mit einem Nichtverstehens-Eingeständnis darin („vielleicht ist die Erfüllungsquote auch was anderes, was ich hier nicht verstehe, keine Ahnung" [34:41]).
- **Dann eine Alternative bauen, nicht nur kritisieren.** Kriesel schlägt eine eigene Metrik vor und rechnet sie durch. Kritik ohne Gegenvorschlag bleibt Meckern.
- **Dann die Zahl** — und davor eine Untertreibung oder einen Absatzbruch als Verzögerung. Die Zahl steht allein in einem kurzen Absatz. Kein Kommentar dahinter.

### Baustein 11 — Der Mechanismus dahinter
**(a) Funktion.** Vom Messfehler zum Verhalten. Die härtere und interessantere Aussage — und die, bei der die Fairness am meisten gebraucht wird.
**(b) Länge.** 350–450 Wörter.
**(c) Regel.**
1. **Anreiz benennen**, nicht Absicht unterstellen. „Wenn X gemessen wird, lohnt sich Y" — nicht „die wollten betrügen."
2. **Vorhersage formulieren, bevor du in die Daten schaust.** Schreib auf, was man sehen müsste, wenn der Anreiz *nicht* wirkt. Das ist der stärkste Absatz, den ein Datentext haben kann.
3. **Kontrollgruppe zeigen**, bei der die Nullhypothese hält.
4. **Abweichung zeigen**, bei der sie nicht hält.
5. **Externe Bestätigung**, falls vorhanden.
6. **Perspektivwechsel:** erkläre in zwei bis drei Sätzen, warum das Verhalten aus Sicht des Betroffenen rational ist.
7. **Kritik auf einen Satz eingrenzen** und die Wertung auf zwei Wörter reduzieren. („Das stört.")

### Baustein 12 — Die Fairness-Coda
**(a) Funktion.** Den Ton zurücknehmen, ohne den Befund zurückzunehmen. Der Leser soll den Text ohne Wut verlassen.
**(b) Länge.** 120–180 Wörter.
**(c) Regel.** Vier Sätze, in dieser Reihenfolge:
1. **Eine echte Verbesserung nennen**, die es beim Untersuchten gibt — nicht symbolisch, sondern konkret und überprüfbar.
2. **Die eigene Fairness zur Frage machen**, nicht zur Behauptung: „Ich hoffe, ich bin bei aller Kritik fair umgegangen." Konjunktiv, nicht Feststellung.
3. **Zeigen, dass du weiter dabei bleibst** — Nutzer, Mitglied, Kunde, Kollege. Wer nach der Kritik abspringt, hat einen Verriss geschrieben; wer bleibt, hat Kritik geübt.
4. **Ein Fürsprache-Satz.** („Seid nett zur Bahn mit ihren Fehlern, wir haben nur diese eine.")

**Sonderfall Einzelperson** (unser ehrenamtlicher Wiki-Admin). Wenn der Betroffene keine Organisation ist, sondern ein Mensch, der das unbezahlt macht, verschiebt sich der Schwerpunkt: die Entlastung muss **vor** den Befund, nicht nur in die Coda. Drei zusätzliche Pflichten:
- **Die Bedingungen vor der Person.** Nenne, unter welchen Umständen die Arbeit stattfindet (unbezahlt, nebenbei, ohne Team), bevor du sagst, was daran nicht funktioniert. Nicht als Entschuldigung — als Kontext.
- **Der Universalitätssatz.** Sag ausdrücklich, dass ein anderer an derselben Stelle dasselbe Ergebnis produziert hätte (Kriesels „die sind bei den anderen wahrscheinlich ähnlich" [08:19]). Ohne diesen Satz wird der Einzelne zum Sündenbock.
- **Die Menschlichkeitslesart.** Wo der Befund ein Fehler ist, lies ihn als Beleg dafür, dass da ein Mensch arbeitet — so wie Kriesel den falschen SAP-Titel liest [43:57]. Das ist keine Beschönigung, es ist die zutreffendere Beschreibung.

### Baustein 13 — Der Ebenenwechsel
**(a) Funktion.** Den Text über seinen Gegenstand hinausheben. Erklären, warum es die Analyse gab.
**(b) Länge.** 250–350 Wörter.
**(c) Regel.** Beginne mit einer kurzen Frage als Scharnier („Und was bleibt?"). Wechsle dann **das Thema**, nicht die Tonlage — es geht jetzt nicht mehr um den Untersuchungsgegenstand. **Keine Pointen mehr ab hier.** Formuliere genau eine These über etwas Größeres, die der Text belegt hat, ohne dass du sie vorher ausgesprochen hast. Sag, warum du die Analyse wirklich gemacht hast. Und mach dabei einen Anspruch klein: „ich hoffe, ich habe Ihnen gezeigt, dass das keine Raketenwissenschaft ist."

### Baustein 14 — Der letzte Satz
**(a) Funktion.** Den Leser mit einer Rolle entlassen, nicht mit einem Ergebnis.
**(b) Länge.** 60–100 Wörter.
**(c) Regel.** Der letzte inhaltliche Satz **handelt vom Leser, nicht vom Gegenstand**. Zwei erprobte Formen:
- **Beleg-Form (BahnMining):** Nimm eine beobachtbare Tatsache über deine Leser und benutze sie als Datenpunkt für die These aus Baustein 13. („Warum tun die 5000 Leute das? Um einen Statistikvortrag zu hören. Das gibt mir Hoffnung.")
- **Öffnungs-Form (SpiegelMining):** Gib die Werkzeuge weiter und bitte um Beiträge. Sag dabei ehrlich, was du selbst nicht mehr schaffst.
In beiden Fällen: der Untersuchungsgegenstand darf im letzten Satz höchstens noch im Nebensatz vorkommen, und dann versöhnt. Der allerletzte Ich-Satz ist ein Dank, keine Bilanz.

---

## Verteilungsregeln über den ganzen Text

**Unsicherheit — Dosis und Ort.** Rechne mit **einer Unsicherheitsäußerung pro 400 Wörter**, das sind bei 3.400 Wörtern acht bis neun. Drei Typen mischen:
- *Vorbehalt mit Weiterarbeit* — „das ist von außen gemessen, es kann falsch sein, aber X und Y stützen es, also nehmen wir es als gegeben, bis widersprochen wird."
- *Offenes Nichtverstehen* — „was diese Kennzahl genau meint, verstehe ich nicht."
- *Eigener Fehler, in Nutzen umgemünzt* — Fehler erzählen, dann die Regel daraus für den Leser ableiten. Diese Form mindestens einmal.
Und: **jede Unsicherheit muss präzise begrenzt sein.** Nie „vielleicht stimmt alles nicht." Immer „bei dieser einen Kennzahl weiß ich es nicht."

**Humor — Dosis und Ort.** Rechne mit **einer Pointe pro 250–350 Wörter** im Befundteil, **null im Schlussteil** (Baustein 13/14) und **null im ernstesten Block**, falls es einen gibt. Quellen in dieser Rangfolge: Selbstironie vor Untertreibung vor Datenabsurdität vor Sprachentlarvung. Nie auf Kosten des Betroffenen.
**Zwei Positionsregeln:** (1) Eine Untertreibung direkt **vor** die größte Zahl setzen, dann Absatzbruch, dann die Zahl allein. (2) Nach jedem harten Vorwurf innerhalb von zwei Sätzen einen Druckablass — sonst kippt der Text in Empörung, und Empörung ist genau das, wogegen Kriesel argumentiert.
**Und wenn es ernst wird, sag es an.** „Jetzt halten wir kurz inne" vor dem ernsten Teil, „damit die Laune wieder steigt" danach. Der Leser darf wissen, in welchem Modus er ist.

**Zahlen — Dichte.** Höchstens **zwei nackte Zahlen pro Absatz**, jede mit Übersetzung in eine erlebbare Häufigkeit im selben oder nächsten Satz. Prozentzahlen immer zusätzlich als „einer von N".

**Bilder — Wiederverwendung statt Feuerwerk.** Nimm zwei bis drei Vergleiche und **führe sie weiter**, statt zehn einmalige zu streuen. Kriesels Bahn-Admins tauchen dreimal auf und entwickeln sich. Ein Bild, das dreimal wiederkommt, wird zur Figur; zehn Bilder, die einmal kommen, werden zum Rauschen.

**Absätze.** Kurz. Kriesel spricht in Sätzen von 15–35 Wörtern, sehr oft mit „und" beginnend, fast nie mit Nebensatzkaskaden. Im Text heißt das: 2–4 Sätze pro Absatz, Absatzbruch als Ersatz für die Sprechpause.

---

## Was NICHT geht — die Imitationsfallen

**1. Den Humor kopieren, ohne die Belege zu haben.** Kriesels Witze funktionieren, weil unter jedem einer eine geprüfte Zahl liegt. „103 % Fernverkehr" ist nur komisch, wenn die 103 % stimmen. Ein Gag ohne Beleg ist Spott, und Spott kostet genau die Glaubwürdigkeit, die der Text braucht.

**2. Die Bescheidenheit ohne die Verifikation.** „Es kann sein, dass ich mich irre" ist nur souverän, wenn danach der Nachweis kommt, dass man es nachgeprüft hat. Ohne Baustein 9 ist derselbe Satz eine Vorab-Ausrede, und der Leser merkt den Unterschied sofort.

**3. Die Fairness als Floskel.** „Ich will hier niemandem etwas unterstellen, aber..." ist das Gegenteil von Kriesels Verfahren. Seine Entlastungen sind **überprüfbare Aussagen** („der Nahverkehr erreicht über 90 %"), keine rhetorischen Verbeugungen. Wenn die Entlastung nichts kostet, ist sie keine.

**4. Sieben Punkte, weil er sieben Punkte hatte.** Die Nummerierung funktioniert, weil jeder Punkt eine eigene Handlungsanweisung ist. Eine Liste aus Themenüberschriften ist ein Inhaltsverzeichnis, kein Fortschrittsbalken.

**5. Die Live-Elemente einfach übersetzen.** Vier Dinge sind **nicht übertragbar** und sollten weder imitiert noch schlecht ersetzt werden:
- **Handzeichen-Abfragen.** Im Text gibt es keine Abstimmung. Text-Entsprechung: Frage stellen und die Antwort des Lesers im nächsten Absatz vorwegnehmen („Sie würden sagen X. Ich auch."). Das funktioniert. Ein „Was meinen Sie?" ohne Auflösung funktioniert nicht.
- **Applaus- und Lachpausen.** Nicht ersetzbar. Der Absatzbruch ist das nächstliegende Äquivalent, hat aber ein Zehntel der Wirkung. Wer die Wirkung braucht, muss sie durch Satzkürze erzeugen, nicht durch Formatierung.
- **Live-Zoomfahrten und Animationen.** Die Keyword-Landkarten-Sequenz [25:41–28:20] ist eine reine Bewegungserfahrung. Text-Entsprechung: eine Bildstrecke mit drei bis vier Stufen und Bildunterschriften, die jeweils nur **einen** Satz sagen. Der Rausch-Effekt geht dabei verloren; das ist ehrlicher, als ihn mit Adjektiven simulieren zu wollen.
- **Metahumor über die Publikumsreaktion.** „Ihr klatscht ja schon vorher" hat im Text keine Entsprechung. Weglassen.
- **Die Q&A.** Kriesels stärkste Unsicherheits-Belege stehen in der Fragerunde. Text-Entsprechung: ein Abschnitt „Was ich nicht weiß" oder „Was mir vorgeworfen werden kann" vor dem Schluss, in dem du die drei stärksten offenen Fragen selbst stellst und ehrlich beantwortest — auch mit „das habe ich nicht geprüft."

**6. Das Ergebnis vor die Methode ziehen, weil man ungeduldig ist.** Die Reihenfolge Atomeinheit → langweilige Auswertungen → Befund → Methode → Verifikation → Hauptbefund ist keine Konvention, sondern eine Kette von Berechtigungen. Wer den Hauptbefund nach vorn zieht, hat ihn nicht mehr belegt, sondern nur behauptet.

**7. Den Ebenenwechsel als Moralpredigt.** Baustein 13 funktioniert bei Kriesel, weil er (a) das Thema wechselt statt es zu überhöhen, (b) keine Forderung stellt, sondern eine Beobachtung teilt, und (c) sich selbst dabei kleinmacht. Wer stattdessen aus der Datenanalyse eine gesellschaftliche Forderung ableitet, verliert die Position, die der ganze Text aufgebaut hat: die des Messenden, nicht die des Urteilenden.

**8. Zu viele Bilder.** Siehe oben: drei wiederkehrende Vergleiche schlagen zwölf einmalige. Die Versuchung ist groß, weil Kriesels Vergleichsliste in Teil A lang aussieht — aber sie verteilt sich auf 48 Minuten, und die stärksten kommen mehrfach.

**9. Die Selbstironie überziehen.** Kriesel macht sich klein an genau den Stellen, an denen er sonst überlegen wirken würde — nach einem Verriss, nach einer großen Zahl, nach einem Lacher auf Kosten anderer. Dauernde Selbstabwertung erzeugt das Gegenteil: einen Text, dem man nichts glaubt, weil sein Autor sich selbst nichts glaubt.
