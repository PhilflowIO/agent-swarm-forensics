#!/usr/bin/env python3
"""
rebuild_text.py — setzt den Seitentext in die veroeffentlichten Tabellen zurueck.

Warum es dieses Skript gibt
---------------------------
Dieses Repository gibt abgeleitete Ergebnisse und den Code weiter, aber nicht den
Wiki-Abzug und keinen Seitentext darueber hinaus. Mehrere Tabellen brauchen fuer
sich genommen aber Volltext -- das Gold-Set etwa besteht aus 400 Saetzen. Statt sie
wegzulassen, ist in ihnen jede Textzelle geleert und daneben ein Verweis abgelegt:

    <spalte>_ref  =  revision|feld|versatz|laenge|sha256-12|schreibweise

Zwei Faelle. Bestand die Zelle nur aus Seitentext, ist sie leer und der Verweis
ersetzt sie ganz. Umschloss unser eigener Text ein Zitat -- Belegspalten der Form
"Seite . Zeit . Name :: <Zitat>" --, steht der Rahmen weiter da und nur die
herausgeloeste Passage ist durch die Marke U+E000 vertreten; mehrere Passagen in
einer Zelle ergeben mehrere Marken und mehrere, durch ";" getrennte Verweise.

Wer den Abzug bei seinen Urhebern herunterlaedt, stellt damit den vollen Bestand
wieder her. Wer ihn nicht hat, sieht keinen Seitentext. Reproduzierbarkeit bleibt
vollstaendig, weitergegeben wird nichts, was nicht uns gehoert.

Voraussetzungen
---------------
1. Abzug herunterladen:  https://collusion.wiki/explorer/download.html
   und nach  <repo>/analyse/data/  entpacken (revisions.jsonl u. a.).
2. Zwischenstufen bauen:
       analyse/.venv/bin/python scripts/30_load.py
       analyse/.venv/bin/python scripts/32_delta.py
   Das erzeugt artefakte/schwarm_deltas.parquet -- die Quelle dieses Skripts.

Aufruf
------
    python rebuild_text.py                 # alle Tabellen unter artefakte/
    python rebuild_text.py --pruefen       # nur pruefen, nichts schreiben
    python rebuild_text.py paper_goldset_sample.csv ...

Ausgabe: die Tabellen werden an Ort und Stelle ergaenzt (die _ref-Spalten bleiben
stehen, damit der Vorgang wiederholbar und nachpruefbar ist).
"""
import argparse, csv, hashlib, sys
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    sys.exit("pandas fehlt:  pip install pandas pyarrow")

B = Path(__file__).resolve().parent
A = B / "artefakte"
QUELLE = A / "schwarm_deltas.parquet"
csv.field_size_limit(sys.maxsize)


MARKE = "\ue000"

# Umkehrung der Schreibweisen, in denen manche Tabellen Zeilenumbrueche ablegen.
RUECKFORM = {"roh": None, "sp_cr_sp": " ⏎ ", "cr": "⏎", "sp_pipe_sp": " | "}


def _rueckform(text, form):
    trenn = RUECKFORM.get(form)
    return text if trenn is None else text.replace("\n", trenn)


def sha12(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:12]


def lade_abzug():
    if not QUELLE.exists():
        sys.exit(
            f"{QUELLE} fehlt.\n"
            "Erst den Abzug nach analyse/data/ legen und dann\n"
            "  python scripts/30_load.py && python scripts/32_delta.py\n"
            "laufen lassen (siehe Kopf dieser Datei)."
        )
    rev = pd.read_parquet(QUELLE, columns=["rev_id", "body", "delta"])
    return {
        r.rev_id: {"delta": r.delta or "", "body": r.body or ""}
        for r in rev.itertuples()
    }


def aus_verweis(ref: str, txt: dict):
    """-> (text, status). status: 'versatz' | 'gesucht' | 'ohne_revision' | 'nicht_gefunden'."""
    try:
        rid, feld, versatz, laenge, h, form = ref.split("|")
        versatz, laenge = int(versatz), int(laenge)
    except ValueError:
        return None, "unlesbarer_verweis"

    if rid != "-" and feld != "-" and versatz >= 0:
        d = txt.get(rid)
        if d:
            kand = d[feld][versatz:versatz + laenge]
            if sha12(kand) == h:
                return _rueckform(kand, form), "versatz"
            # Der Abzug kann seit dem Bau neu geschnitten worden sein: im selben
            # Datensatz nachsuchen, statt still das Falsche zurueckzugeben.
            for f in ("delta", "body"):
                t = d[f]
                fenster = max(0, len(t) - laenge) + 1
                if fenster > 200_000:          # Reissleine gegen sehr grosse Seiten
                    continue
                for i in range(fenster):
                    if sha12(t[i:i + laenge]) == h:
                        return _rueckform(t[i:i + laenge], form), "gesucht"
        return None, "nicht_gefunden"

    # Kein Versatz hinterlegt: der Wert umschloss ein Zitat und ist nicht
    # zeichengenau aus dem Abzug ableitbar.
    return None, "ohne_revision"


def datei_bearbeiten(pfad: Path, txt: dict, nur_pruefen: bool):
    if pfad.suffix == ".csv":
        df = pd.read_csv(pfad, dtype=str, keep_default_na=False, engine="python")
    elif pfad.suffix == ".parquet":
        df = pd.read_parquet(pfad)
    else:
        return None

    ref_spalten = [c for c in df.columns if str(c).endswith("_ref")
                   and str(c)[:-4] in [str(x) for x in df.columns]]
    if not ref_spalten:
        return None

    bericht = []
    for rc in ref_spalten:
        zc = str(rc)[:-4]
        werte, stat = [], {}
        for alt, ref in zip(df[zc].tolist(), df[rc].tolist()):
            alt = "" if alt is None else str(alt)
            ref = "" if ref is None else str(ref)
            if not ref.strip():
                werte.append(alt)
                continue
            teile = [aus_verweis(r, txt) for r in ref.split(";")]
            for _, st in teile:
                stat[st] = stat.get(st, 0) + 1
            if MARKE in alt:
                gefuellt = alt
                for t, _ in teile:
                    gefuellt = gefuellt.replace(MARKE, t if t is not None else "[…]", 1)
                werte.append(gefuellt)
            else:
                t = teile[0][0]
                werte.append(t if t is not None else alt)
        if not nur_pruefen:
            df[zc] = werte
        bericht.append((zc, stat))

    if not nur_pruefen and bericht:
        if pfad.suffix == ".csv":
            df.to_csv(pfad, index=False)
        else:
            df.to_parquet(pfad, index=False)
    return bericht


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dateien", nargs="*", help="Dateinamen unter artefakte/ (leer = alle)")
    ap.add_argument("--pruefen", action="store_true", help="nur pruefen, nichts schreiben")
    args = ap.parse_args()

    txt = lade_abzug()
    print(f"Abzug: {len(txt)} Versionen aus {QUELLE.name}")

    ziele = ([A / n for n in args.dateien] if args.dateien
             else sorted(p for p in A.rglob("*") if p.suffix in (".csv", ".parquet")))

    gesamt, fehler = {}, 0
    for p in ziele:
        if not p.exists():
            print(f"  fehlt: {p.name}")
            fehler += 1
            continue
        b = datei_bearbeiten(p, txt, args.pruefen)
        if not b:
            continue
        for zc, stat in b:
            n = sum(stat.values())
            ok = stat.get("versatz", 0) + stat.get("gesucht", 0)
            print(f"  {p.name:52} {zc:24} {ok}/{n} wiederhergestellt"
                  + ("" if ok == n else f"   offen: "
                     + ", ".join(f"{k}={v}" for k, v in stat.items() if k not in ("versatz", "gesucht"))))
            for k, v in stat.items():
                gesamt[k] = gesamt.get(k, 0) + v

    print("\nSumme:", ", ".join(f"{k}={v}" for k, v in sorted(gesamt.items())) or "nichts zu tun")
    if gesamt.get("nicht_gefunden") or gesamt.get("unlesbarer_verweis"):
        print("\nEinzelne Verweise liefen ins Leere. Haeufigste Ursache: der Abzug unter\n"
              "analyse/data/ ist eine andere Fassung als die, gegen die wir gerechnet haben.\n"
              "Die SHA-256-Summen des von uns benutzten Abzugs stehen in analyse/data/SHA256SUMS.")
    if args.pruefen:
        print("(--pruefen: es wurde nichts geschrieben)")
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main())
