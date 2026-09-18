#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rebuild_log.py -- stellt den vollen Betreiberlog-Korpus aus einer lokal
heruntergeladenen Kopie wieder her.

Warum es dieses Skript gibt
---------------------------
Wir geben weiter, was uns gehoert, und nichts sonst. Das Betreiber-Requestlog
gehoert nicht uns: es traegt in jeder Zeile eine volle IPv4-Adresse und deckt
vier Monate Zugriffe echter Menschen auf ein 25 Jahre altes Wiki ab, dazu den
Tagesrhythmus des Administrators. Veroeffentlicht wird deshalb nur der
Flottenausschnitt (`data/betreiberlogs/freigabe/`, siehe dort `LIESMICH.md`),
in dem alles Nicht-Flottige geloescht und keine Volladresse enthalten ist.

Damit trotzdem jede Zahl der vier Berichte unter
`analyse/betreiberlogs-befunde/` nachrechenbar bleibt, tut dieses Skript fuer
das Log, was `analyse/release/rebuild_text.py` fuer den Wiki-Abzug tut: wer die
Quelldateien bei ihrem Urheber herunterlaedt, baut damit den vollen Korpus
zurueck. Wer sie nicht hat, sieht keine einzige Adresse.

Voraussetzung
-------------
Die vier Monatsdateien beim Betreiber holen und nach
`analyse/data/betreiberlogs/` legen:

    cd analyse/data/betreiberlogs
    for m in 2604 2605 2606 2607; do
        curl -O "https://www.wikiservice.at/dse/log_$m"
        curl -O "https://www.wikiservice.at/dse/refer_$m"
    done
    sha256sum -c SHA256SUMS

Herkunft, Abrufdatum, Groessen und die Vorbehalte gegen eine spaetere Kopie
stehen in `analyse/data/betreiberlogs/HERKUNFT.md`.

Aufruf
------
    python rebuild_log.py               # Summen pruefen, Korpus bauen, Rundlauf pruefen
    python rebuild_log.py --pruefen     # nur pruefen, nichts schreiben
    python rebuild_log.py --summen      # nur die SHA-256-Summen pruefen

Der Rundlauf
------------
Jede Zeile des Flottenausschnitts traegt

    rec_ref = <datei>|<satznummer>|<zeichen>|<sha256-12>

Satznummer ist die laufende Nummer des Datensatzes in der Quelldatei, gezaehlt
wie in `10_normalisieren.py` (nur geglueckte Datensaetze). Das Skript streamt
die Quelldatei und den Ausschnitt im Gleichschritt -- beide laufen in derselben
Ordnung -- und prueft Laenge und Hash jedes einzelnen Satzes. Nur wenn diese
Probe fuer alle Zeilen aufgeht, ist bewiesen, dass die fremde Kopie dieselbe
Fassung ist, gegen die wir gerechnet haben.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import sys
from pathlib import Path

try:
    import pyarrow.parquet as pq
except ImportError:
    sys.exit("pyarrow fehlt:  analyse/.venv/bin/pip install pyarrow")

HIER = Path(__file__).resolve().parent
BASE = HIER.parents[2]
ROH = BASE / "analyse" / "data" / "betreiberlogs"
FREI = ROH / "freigabe"
MONATE = ["2604", "2605", "2606", "2607"]

_spec = importlib.util.spec_from_file_location("norm10", HIER / "10_normalisieren.py")
_norm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_norm)


def sha12(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:12]


def summen_pruefen() -> int:
    """-> Zahl der Abweichungen."""
    datei = ROH / "SHA256SUMS"
    if not datei.exists():
        print(f"  {datei} fehlt -- ohne sie ist keine Aussage moeglich.")
        return 1
    fehler = 0
    for zeile in datei.read_text(encoding="utf-8").splitlines():
        if not zeile.strip():
            continue
        soll, name = zeile.split()[0], zeile.split()[-1]
        p = ROH / name
        if not p.exists():
            print(f"  {name:12} FEHLT -- bei <https://www.wikiservice.at/dse/{name}> holen")
            fehler += 1
            continue
        h = hashlib.sha256()
        with p.open("rb") as fh:
            for block in iter(lambda: fh.read(1 << 20), b""):
                h.update(block)
        ist = h.hexdigest()
        if ist == soll:
            print(f"  {name:12} OK   {p.stat().st_size} B")
        else:
            print(f"  {name:12} ABWEICHUNG\n      erwartet {soll}\n      gefunden {ist}")
            fehler += 1
    return fehler


def korpus_bauen():
    print("Normalisiere die vier Monatsdateien nach data/betreiberlogs/normalisiert/ ...")
    _norm.run()


def rundlauf() -> tuple[int, int]:
    """-> (geprueft, fehler).  Prueft jede Zeile des Ausschnitts gegen die Quelle."""
    geprueft = fehler = 0
    for monat in MONATE:
        ausschnitt = FREI / f"flotte_requests_{monat}.parquet"
        quelle = ROH / f"log_{monat}"
        if not ausschnitt.exists():
            print(f"  flotte_requests_{monat}.parquet fehlt -- 80_freigabe_flotte.py laufen lassen")
            fehler += 1
            continue
        if not quelle.exists():
            print(f"  log_{monat} fehlt -- ohne die Quelle ist kein Rundlauf moeglich")
            fehler += 1
            continue
        roh = _norm.iter_records(quelle)
        roh_no, roh_rec = -1, ""
        n = f_monat = 0
        pf = pq.ParquetFile(ausschnitt)
        for b in pf.iter_batches(batch_size=200_000, columns=["rec_ref"]):
            for ref in b.to_pydict()["rec_ref"]:
                n += 1
                try:
                    datei, no, laenge, h = ref.split("|")
                    no, laenge = int(no), int(laenge)
                except ValueError:
                    f_monat += 1
                    continue
                if datei != f"log_{monat}":
                    f_monat += 1
                    continue
                while roh_no < no:
                    try:
                        roh_no, roh_rec = next(roh)
                    except StopIteration:
                        roh_no, roh_rec = 1 << 62, ""
                        break
                if roh_no != no or len(roh_rec) != laenge or sha12(roh_rec) != h:
                    f_monat += 1
        geprueft += n
        fehler += f_monat
        print(f"  log_{monat}: {n - f_monat}/{n} Verweise aufgeloest"
              + ("" if not f_monat else f"   FEHLER: {f_monat}"))
    return geprueft, fehler


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pruefen", action="store_true", help="nur pruefen, nichts schreiben")
    ap.add_argument("--summen", action="store_true", help="nur die SHA-256-Summen pruefen")
    a = ap.parse_args()

    print("SHA-256-Summen der lokalen Kopie (Soll: data/betreiberlogs/SHA256SUMS)")
    s_fehler = summen_pruefen()
    if a.summen:
        return 1 if s_fehler else 0
    if s_fehler:
        print("\nDie lokale Kopie ist eine andere Fassung als unsere. Der Rueckbau wird\n"
              "nicht dieselben Zahlen ergeben; die Abweichung gehoert benannt, nicht\n"
              "ueberrechnet. Einzelheiten: data/betreiberlogs/HERKUNFT.md")

    if not a.pruefen:
        korpus_bauen()

    print("\nRundlauf: jeder Verweis des Flottenausschnitts gegen die Quelle")
    geprueft, fehler = rundlauf()
    print(f"\nSumme: {geprueft} Verweise geprueft, {fehler} Fehler")
    if fehler:
        print("Haeufigste Ursache: die lokale Kopie unter data/betreiberlogs/ ist eine\n"
              "andere Fassung als die, gegen die der Ausschnitt gebaut wurde.")
    if a.pruefen:
        print("(--pruefen: es wurde nichts geschrieben)")
    return 1 if (fehler or s_fehler) else 0


if __name__ == "__main__":
    sys.exit(main())
