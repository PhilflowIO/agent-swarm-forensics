#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
80_freigabe_flotte.py -- baut den lokalen, noch nicht freigegebenen Ausschnitt des
Betreiber-Requestlogs: ausschliesslich Flottenverkehr, ohne Klartext-Adressen.

Aufruf:
    analyse/.venv/bin/python analyse/scripts/betreiberlog/80_freigabe_flotte.py

Eingabe : analyse/data/betreiberlogs/normalisiert/requests_26{04..07}.parquet
          analyse/artefakte/betreiberlog_identitaet/bi07_netzklassen.csv
Ausgabe : analyse/data/betreiberlogs/freigabe/flotte_requests_26MM.parquet
          analyse/data/betreiberlogs/freigabe/LIESMICH.md
          analyse/data/betreiberlogs/freigabe/freigabe_bilanz.json

WARUM LOESCHEN UND NICHT HASHEN
-------------------------------
Das Quelllog traegt in jeder Zeile eine volle IPv4-Adresse. Es enthaelt vier
Monate Zugriffe echter Menschen auf ein 25 Jahre altes Entwickler-Wiki, den
Tagesrhythmus des Administrators samt seines Wohn-Netzblocks und
Suchmaschinen-Crawler. Ein Hash einer IPv4-Adresse ist **keine**
Anonymisierung: der Raum hat 2^32 Elemente, eine vollstaendige Regenbogentabelle
ueber alle Adressen ist auf einem Laptop in Sekunden erzeugt und deckt jeden
Hash ohne Salz sofort auf. Ein Salz, das wir mitliefern muessten, damit der
Ausschnitt nachpruefbar bleibt, hebt den Schutz wieder auf; ein Salz, das wir
nicht mitliefern, macht die Spalte fuer Dritte wertlos. Deshalb:

  * Nicht-Flottenzeilen werden **geloescht**, nicht pseudonymisiert.
  * Im Ausschnitt bleibt der Anbieter-Praefix (/16) im Klartext -- er ist
    Eigentum eines Cloud-Anbieters, keine Person, und die Analyse braucht ihn.
  * Die Volladresse wird durch eine laufende, undurchsichtige Kennung
    (`adr_id`) ersetzt. Die Zuordnung Kennung -> Adresse entsteht nur im
    Arbeitsspeicher dieses Laufs, ist zufaellig permutiert (os.urandom-Seed)
    und wird **nicht** gespeichert. Quellverweise erlauben dennoch eine
    Rueckverknuepfung; dies ist keine Anonymisierung.
    Erhalten bleibt genau das, was die Auswertung braucht: ob zwei Requests
    von derselben Adresse kamen.

UEBERNOMMENE FLOTTENDEFINITION -- NICHTS NEU ERFUNDEN
-----------------------------------------------------
Quelle: `analyse/scripts/betreiberlog/bi07_netze.py:31`

    flotte = d["namen_2606"] >= 50 and d["req_2606"] > 0

Ein /16-Block gilt als Flottenblock, wenn er im Juni aktiv ist und >= 50
verschiedene Wiki-Namen traegt -- Preferences setzt in diesem Log nur ein Agent.
Das sind 146 Bloecke (`bi07_netzklassen.json`, Feld `flotte_bloecke_n`), auf die
im Juni 55,23 % aller Requests entfallen. Die Blockdefinition ist die
tragfaehigste der vier Kandidaten, weil sie Flotte, Dauercrawler und Rest an
**im Log messbaren** Merkmalen trennt statt an einer Namensliste
(`bi07_netze.py:6-10`); `03_flotten_ips.py` ist bewusst nur ein Ein-Tages-Sieb
zur Saatgewinnung (`03_flotten_ips.py:54`: Fenster 24.05.), `06_flotte_gesamt.py`
ist ein Request-Detektor, der die stummen Lesezugriffe der Flotte nicht sieht,
und `60_netzbloecke.py` klassifiziert gar nicht, es aggregiert nur.

Die Blockzugehoerigkeit allein genuegt nicht: dieselben Azure-/16 tragen vor
und nach dem Vorfall eine Grundlast fremden Verkehrs (April: 13.520 Requests aus
158 Adressen, null Wiki-Namen). Deshalb zweite, konjunktive Bedingung:

  Zeitfenster  2026-05-24T05:55:31Z .. 2026-07-02T23:59:59Z

Untergrenze = erster beweisbarer Flottenrequest
(`analyse/betreiberlogs-befunde/erstkontakt-domain.md`, Kurzfassung).
Obergrenze = Ende des Vorfallstags; die letzte archivierte Revision liegt
2026-07-02T17:51:22Z (`paper/main.tex:115`), ab dem 3. Juli tragen die
Flottenbloecke null Wiki-Namen und fallen auf die Grundlast zurueck.

SEITENTEXT
----------
Der Betreiber redigiert Seitentexte selbst: der `text=`-Parameter traegt die
literale Zeichenkette `(NN)`. In 414 von 126.266 Faellen ist das misslungen und
echter Seitentext steht im Log. Diese Werte werden hier auf `(NN)` gesetzt --
das Paper gibt keinen Seitentext weiter, der ueber kurze Belegzitate hinausgeht
(`paper/main.tex` §Data and code availability).
"""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import os
import random
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

HIER = Path(__file__).resolve().parent
BASE = HIER.parents[2]
ROH = BASE / "analyse" / "data" / "betreiberlogs"

# Der Satzzusammenbau lebt an genau einer Stelle: im Normalisierer.
_spec = importlib.util.spec_from_file_location("norm10", HIER / "10_normalisieren.py")
_norm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_norm)
iter_records = _norm.iter_records
NORM = BASE / "analyse" / "data" / "betreiberlogs" / "normalisiert"
OUT = BASE / "analyse" / "data" / "betreiberlogs" / "freigabe"
NETZ = BASE / "analyse" / "artefakte" / "betreiberlog_identitaet" / "bi07_netzklassen.csv"
MONATE = ["2604", "2605", "2606", "2607"]

LO = int(datetime(2026, 5, 24, 5, 55, 31, tzinfo=timezone.utc).timestamp())
HI = int(datetime(2026, 7, 2, 23, 59, 59, tzinfo=timezone.utc).timestamp())

IPV4 = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
TEXT = re.compile(r"(^|&)(text=)([^&]*)")
# Agenten haben ihre eigene Egress-Adresse in Suchbegriffe und RecentChanges-
# Cursor geschrieben. Das sind Cloud-Adressen, keine Menschen -- trotzdem wird
# hier maskiert: der Ausschnitt verspricht "keine Volladresse", und ein
# Versprechen mit 28 Ausnahmen ist von aussen nicht mehr pruefbar.
IPV4_IM_TEXT = re.compile(r"(?<![0-9.])(\d{1,3}\.\d{1,3})\.\d{1,3}\.\d{1,3}(?![0-9.])")

SCHEMA = pa.schema([
    ("ts_utc", pa.int64()),
    ("ip16", pa.string()),
    ("adr_id", pa.int32()),
    ("host", pa.string()),
    ("host_raw", pa.string()),
    ("killed", pa.bool_()),
    ("script", pa.string()),
    ("wiki", pa.string()),
    ("name", pa.string()),
    ("action_kind", pa.string()),
    ("action_raw", pa.string()),
    ("action_detail", pa.string()),
    ("page_id", pa.string()),
    ("raw_params", pa.string()),
    ("rec_ref", pa.string()),
])

LESEN = ["ts_utc", "ip", "host", "host_raw", "killed", "script", "wiki", "name",
         "action_kind", "action_raw", "action_detail", "page_id", "raw_params",
         "src_file", "rec_no"]


def fleet_bloecke():
    if not NETZ.exists():
        sys.exit(f"{NETZ} fehlt -- erst bi03_identitaet.py und bi07_netze.py laufen lassen.")
    bl = {r["ip16"] for r in csv.DictReader(NETZ.open(encoding="utf-8"))
          if r["klasse"] == "flotte"}
    if not bl:
        sys.exit("bi07_netzklassen.csv enthaelt keine Klasse 'flotte'.")
    return bl


def praefix(ip: str) -> str:
    p = ip.split(".")
    return p[0] + "." + p[1]


def batches(monat):
    pf = pq.ParquetFile(NORM / f"requests_{monat}.parquet")
    for b in pf.iter_batches(batch_size=200_000, columns=LESEN):
        yield b.to_pydict()


def pass1(bloecke, bilanz):
    """Welche Volladressen bleiben im Ausschnitt? Nur Zaehlen, nichts schreiben."""
    adressen = set()
    for monat in MONATE:
        for d in batches(monat):
            for ip, ts in zip(d["ip"], d["ts_utc"]):
                if not IPV4.match(ip or ""):
                    bilanz["verworfen_adresse_unbrauchbar"] += 1
                    continue
                if praefix(ip) not in bloecke:
                    bilanz["verworfen_kein_flottenblock"] += 1
                    continue
                if not (LO <= ts <= HI):
                    bilanz["verworfen_ausserhalb_fenster"] += 1
                    continue
                adressen.add(ip)
    return adressen


def kennungen(adressen):
    """Laufende, undurchsichtige Kennung je Volladresse.

    Die Reihenfolge ist zufaellig permutiert, damit die Kennung auch nichts
    ueber das erste Auftreten verraet. Der Seed kommt aus os.urandom und wird
    nirgends festgehalten -- der Lauf ist absichtlich nicht wiederholbar.
    """
    ad = sorted(adressen)
    rnd = random.Random(int.from_bytes(os.urandom(32), "big"))
    ids = list(range(1, len(ad) + 1))
    rnd.shuffle(ids)
    return dict(zip(ad, ids))


def redigiere(q: str, bilanz) -> str:
    if "text=" not in q:
        return q

    def _r(m):
        if m.group(3) == "(NN)":
            return m.group(0)
        bilanz["seitentext_nachredigiert"] += 1
        return m.group(1) + m.group(2) + "(NN)"

    return TEXT.sub(_r, q)


def maskiere_adressen(wert: str, bilanz) -> str:
    if not wert:
        return wert

    def _m(m):
        bilanz["volladressen_im_nutztext_maskiert"] += 1
        return m.group(1) + ".x.x"

    return IPV4_IM_TEXT.sub(_m, wert)


def sha12(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:12]


LIESMICH = """# Vorbereiteter Request-Ausschnitt — NICHT ZUR VEROEFFENTLICHUNG FREIGEGEBEN

Stand nach Cross-Review vom 18.09.2026: Die Auswahl beruht auf Cloud-/16 und
Vorfallsfenster. Sie beweist keine requestgenaue Flottenzugehoerigkeit. Die
Adresskennungen sind ueber `rec_ref` mit dem oeffentlichen Quelllog verknuepfbar.
Dieser lokale Ausschnitt ist bis zu einer gesonderten Herkunfts- und
Datenschutzpruefung von der veroeffentlichten v4-Fassung ausgeschlossen.

Erzeugt von `analyse/scripts/betreiberlog/80_freigabe_flotte.py`, geprueft von
`analyse/scripts/betreiberlog/81_freigabe_pruefen.py`, zurueckgebaut von
`analyse/scripts/betreiberlog/rebuild_log.py`.

## Was hier liegt und was nicht

Dies ist ein **heuristisch ausgewaehlter lokaler** Teil des Betreiberlogs: {freigegeben} von {gelesen} Requests ({anteil:.1f} %), aus
{bloecke} Cloud-/16-Bloecken, im Fenster {von} .. {bis}.
Geloescht -- nicht pseudonymisiert -- wurden {kein_block} Requests ausserhalb
der Flottenbloecke (Menschen, Suchmaschinen-Crawler, der Administrator) und
{ausser_fenster} Requests, die zwar aus einem Flottenblock kamen, aber vor oder
nach dem Vorfall, wo dieselben Bloecke fremde Grundlast tragen.

Das Quelllog selbst geben wir nicht weiter. Es steht dauerhaft beim Betreiber:
<https://www.wikiservice.at/dse/>; unsere Kopie ist ueber
`analyse/data/betreiberlogs/SHA256SUMS` nachpruefbar
(Herkunft, Stabilitaet und Vorbehalte: `analyse/data/betreiberlogs/HERKUNFT.md`).

## Warum hier kein Hash steht

Jede Zeile des Quelllogs traegt eine volle IPv4-Adresse. **Ein Hash einer
IPv4-Adresse ist keine Anonymisierung**: der Adressraum hat 2^32 Elemente, eine
vollstaendige Tabelle aller Hashes ist auf einem Laptop in Sekunden erzeugt, und
damit ist jeder ungesalzene Hash sofort zurueckgerechnet. Ein Salz, das wir
mitliefern, hebt den Schutz auf; eines, das wir zurueckhalten, macht die Spalte
fuer Dritte wertlos. Also:

* Nicht-Flottenzeilen sind **geloescht**.
* `ip16` ist der Anbieter-Praefix im Klartext -- Eigentum eines Cloud-Anbieters,
  keine Person, und die Analyse braucht ihn.
* `adr_id` ist eine laufende, undurchsichtige Kennung je verschiedener
  Volladresse ({adressen} Stueck). Die Zuordnung Kennung -> Adresse entstand nur
  im Arbeitsspeicher des Bauens, war zufaellig permutiert und ist **nicht**
  gespeichert. Ueber die mitgelieferten Quellverweise ist die Zuordnung dennoch
  rekonstruierbar; dies ist Pseudonymisierung, keine Anonymisierung. Erhalten
  bleibt, ob zwei Requests von derselben Adresse kamen. Die Kennungen sind
  zwischen zwei Baulaeufen nicht vergleichbar.
* Die Spalten `ip` und `client_host` des internen Korpus fehlen hier ganz;
  `client_host` war in jeder Zeile des Ausschnitts mit `ip` identisch.

## Seitentext

Das Log enthaelt keine Antwortinhalte. Seitentexte redigiert der Betreiber
selbst: der `text=`-Parameter traegt die literale Zeichenkette `(NN)`. In
{nachredigiert} Faellen war das misslungen; dort steht jetzt ebenfalls `(NN)`.
In {maskiert} Faellen hatten Agenten ihre eigene Egress-Adresse in Suchbegriffe
oder RecentChanges-Cursor geschrieben; dort sind die letzten beiden Oktette
durch `x.x` ersetzt.

## Spalten

| Spalte | Bedeutung |
|---|---|
| `ts_utc` | Unix-Sekunden UTC, Feld `TS` der Rohzeile |
| `ip16` | Anbieter-Praefix /16, Klartext |
| `adr_id` | zufaellige Kennung je Volladresse; ueber die Quelle verknuepfbar |
| `host`, `host_raw`, `script`, `wiki` | Ziel der Anfrage (durchgaengig `dse`) |
| `killed` | der Betreiber hat den Request serverseitig abgebrochen |
| `name` | Wiki-Name, den der Request gesetzt hat (Agentenname) |
| `action_kind`, `action_raw`, `action_detail` | Klassifikation aus `10_normalisieren.py` |
| `page_id` | angesprochene Seite |
| `raw_params` | Query-String, redigiert wie oben |
| `rec_ref` | `<datei>|<satznummer>|<zeichen>|<sha256-12>` -- loest `rebuild_log.py` gegen eine lokale Kopie auf |

## Vollen Korpus zurueckbauen

    analyse/.venv/bin/python analyse/scripts/betreiberlog/rebuild_log.py --pruefen

Mit einer eigenen Kopie der vier Betreiberdateien unter
`analyse/data/betreiberlogs/` stellt das Skript den vollstaendigen normalisierten
Korpus wieder her; jede Zahl der vier Berichte unter
`analyse/betreiberlogs-befunde/` ist damit nachrechenbar, ohne dass wir
Personendaten verbreiten.
"""


def schreibe_liesmich(bilanz):
    (OUT / "LIESMICH.md").write_text(LIESMICH.format(
        freigegeben=f"{bilanz['freigegeben']:,}".replace(",", "."),
        gelesen=f"{bilanz['gelesen_gesamt']:,}".replace(",", "."),
        anteil=100 * bilanz["freigegeben"] / bilanz["gelesen_gesamt"],
        bloecke=bilanz["flottenbloecke"],
        von=bilanz["fenster_von"], bis=bilanz["fenster_bis"],
        kein_block=f"{bilanz['verworfen_kein_flottenblock']:,}".replace(",", "."),
        ausser_fenster=f"{bilanz['verworfen_ausserhalb_fenster']:,}".replace(",", "."),
        adressen=f"{bilanz['distinkte_adressen']:,}".replace(",", "."),
        nachredigiert=bilanz["seitentext_nachredigiert"],
        maskiert=bilanz["volladressen_im_nutztext_maskiert"]), encoding="utf-8")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    bloecke = fleet_bloecke()
    bilanz = {
        "flottenbloecke": len(bloecke),
        "fenster_von": datetime.fromtimestamp(LO, timezone.utc).isoformat().replace("+00:00", "Z"),
        "fenster_bis": datetime.fromtimestamp(HI, timezone.utc).isoformat().replace("+00:00", "Z"),
        "gelesen_gesamt": 0,
        "freigegeben": 0,
        "verworfen_kein_flottenblock": 0,
        "verworfen_ausserhalb_fenster": 0,
        "verworfen_adresse_unbrauchbar": 0,
        "seitentext_nachredigiert": 0,
        "volladressen_im_nutztext_maskiert": 0,
        "je_monat": {},
    }

    print("Durchlauf 1 von 2: Adressen zaehlen (es wird nichts geschrieben)", flush=True)
    adressen = pass1(bloecke, bilanz)
    karte = kennungen(adressen)
    bilanz["distinkte_adressen"] = len(karte)
    print(f"  {len(karte)} verschiedene Volladressen im Ausschnitt", flush=True)

    print("Durchlauf 2 von 2: Ausschnitt schreiben", flush=True)
    for monat in MONATE:
        ziel = OUT / f"flotte_requests_{monat}.parquet"
        writer = pq.ParquetWriter(ziel, SCHEMA, compression="zstd")
        n = 0
        batch = {f.name: [] for f in SCHEMA}

        def flush():
            nonlocal batch
            if not batch["ts_utc"]:
                return
            writer.write_table(pa.table(
                {k: pa.array(v, type=SCHEMA.field(k).type) for k, v in batch.items()},
                schema=SCHEMA))
            batch = {f.name: [] for f in SCHEMA}

        # Parquet-Zeilen und Rohsaetze laufen beide in rec_no-Ordnung; sie werden
        # im Gleichschritt verschraenkt, damit der Verweis den SHA-256-Praefix
        # des Rohsatzes tragen kann, ohne dass irgendetwas im Speicher gehalten
        # werden muesste.
        roh = iter_records(ROH / f"log_{monat}")
        roh_no, roh_rec = -1, ""
        for d in batches(monat):
            bilanz["gelesen_gesamt"] += len(d["ts_utc"])
            for i, ip in enumerate(d["ip"]):
                ts = d["ts_utc"][i]
                if not IPV4.match(ip or "") or praefix(ip) not in bloecke \
                        or not (LO <= ts <= HI):
                    continue
                ziel_no = d["rec_no"][i]
                while roh_no < ziel_no:
                    roh_no, roh_rec = next(roh)
                if roh_no != ziel_no:
                    sys.exit(f"Rohsatz {ziel_no} in log_{monat} nicht gefunden "
                             f"(bei {roh_no}) -- ist die lokale Kopie dieselbe? "
                             f"Siehe data/betreiberlogs/SHA256SUMS.")
                q = maskiere_adressen(redigiere(d["raw_params"][i] or "", bilanz), bilanz)
                batch["ts_utc"].append(ts)
                batch["ip16"].append(praefix(ip))
                batch["adr_id"].append(karte[ip])
                for k in ("host", "host_raw", "killed", "script", "wiki", "name",
                          "action_kind", "action_raw", "action_detail"):
                    batch[k].append(d[k][i])
                batch["page_id"].append(maskiere_adressen(d["page_id"][i] or "", bilanz))
                batch["raw_params"].append(q)
                batch["rec_ref"].append(
                    f"{d['src_file'][i]}|{ziel_no}|{len(roh_rec)}|{sha12(roh_rec)}")
                n += 1
                if len(batch["ts_utc"]) >= 200_000:
                    flush()
        flush()
        writer.close()
        bilanz["je_monat"][monat] = n
        bilanz["freigegeben"] += n
        print(f"  {ziel.name}: {n} Zeilen", flush=True)

    # Die Zuordnungstabelle stirbt hier. Sie war nie auf einem Datentraeger.
    karte.clear()
    del karte, adressen

    schreibe_liesmich(bilanz)
    (OUT / "freigabe_bilanz.json").write_text(
        json.dumps(bilanz, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(bilanz, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
