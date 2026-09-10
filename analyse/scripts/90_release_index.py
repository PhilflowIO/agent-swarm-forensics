#!/usr/bin/env python3
"""
90_release_index.py — Spaltenbefund fuer die Veroeffentlichung.

Frage: welche Spalte eines Artefakts traegt WOERTLICHEN Text aus dem Abzug?
Sie wird nicht nach ihrem Namen beantwortet, sondern empirisch: es wird geprueft,
ob der Wert -- oder ein hinreichend langes Stueck davon -- im Abzug wiederzufinden
ist. Was dort steht, ist Weitergabe des Abzugs und muss vor der Veroeffentlichung
durch einen Verweis ersetzt werden (siehe 91_release_build.py).

Warum stueckweise: mehrere Belegspalten stellen dem Zitat eine eigene Kennung
voran ("dse~Seite . Zeit . Name :: <Zitat>"), andere ersetzen Zeilenumbrueche
durch Trennzeichen. Ein Test auf Gleichheit uebersieht beides.

Ausgabe: analyse/release/spalten_befund.csv
Lauf:    analyse/.venv/bin/python scripts/90_release_index.py   (aus analyse/ heraus)
"""
import bisect, csv, sys
from pathlib import Path
import pandas as pd

B = Path(__file__).resolve().parents[1]
A = B / "artefakte"
R = B / "release"
R.mkdir(exist_ok=True)
csv.field_size_limit(sys.maxsize)

MIN_LEN   = 40   # kuerzer ist kein Seitentext, sondern ein Bezeichner
MIN_SPACE = 3
FENSTER   = 60   # Laenge des Suchfensters im Wert
SAMPLE    = 40   # Werte je Spalte fuer die Klassifikation

def log(*a): print(*a, flush=True)

log("Abzug laden ...")
rev = pd.read_parquet(A / "schwarm_deltas.parquet", columns=["rev_id", "body", "delta"])
rev["body"] = rev["body"].fillna(""); rev["delta"] = rev["delta"].fillna("")

def heuhaufen(series):
    parts, offs, ids, pos = [], [], [], 0
    for rid, txt in zip(rev["rev_id"], series):
        parts.append(txt); offs.append(pos); ids.append(rid); pos += len(txt) + 1
    return "\x00".join(parts), offs, ids

HAY = {f: heuhaufen(rev[f]) for f in ("delta", "body")}
for f in HAY: log(f"  Heuhaufen {f}: {len(HAY[f][0])/1e6:.1f} MB")
def norm(s): return " ".join(s.split())
NORM = {f: norm(HAY[f][0]) for f in ("delta", "body")}

def _lokalisiere(feld, p):
    hay, offs, ids = HAY[feld]
    i = bisect.bisect_right(offs, p) - 1
    return ids[i], p - offs[i]

def treffer(wert):
    """(feld, rev_id, start, art) fuer den ganzen Wert, sonst None."""
    for feld in ("delta", "body"):
        p = HAY[feld][0].find(wert)
        if p >= 0:
            rid, off = _lokalisiere(feld, p)
            return feld, rid, off, "ganz"
    nv = norm(wert)
    if len(nv) >= MIN_LEN:
        for feld in ("delta", "body"):
            if nv in NORM[feld]:
                return feld, None, -1, "normalisiert"
    return None

def _varianten(v):
    yield v
    for a, b in ((" ⏎ ", "\n"), ("⏎", "\n"), (" | ", "\n")):
        if a in v: yield v.replace(a, b)

def enthaelt(wert):
    """Enthaelt der Wert irgendwo Abzugstext? -> art oder None."""
    t = treffer(wert)
    if t: return t[3]
    for v in _varianten(wert):
        if v is not wert and treffer(v): return "variante"
        if len(v) <= FENSTER: continue
        schritt = max(1, (len(v) - FENSTER) // 6)
        for i in range(0, len(v) - FENSTER + 1, schritt):
            if treffer(v[i:i + FENSTER]): return "teilstueck"
    return None

def kandidat(vals):
    s = [str(x) for x in vals if x is not None and str(x).strip() not in ("", "nan", "None")]
    if not s: return None
    if max(len(x) for x in s) < MIN_LEN: return None
    if sum(x.count(" ") for x in s) / len(s) < MIN_SPACE: return None
    return s

rows = []
dateien = sorted(p for p in A.rglob("*") if p.is_file() and p.suffix in (".csv", ".parquet"))
log(f"{len(dateien)} Dateien pruefen ...")
for p in dateien:
    relp = str(p.relative_to(A))
    try:
        df = (pd.read_csv(p, dtype=str, keep_default_na=False, engine="python")
              if p.suffix == ".csv" else pd.read_parquet(p))
    except Exception as e:
        rows.append(dict(datei=relp, spalte="<LESEFEHLER>", befund="lesefehler", beispiel_frei=str(e)[:200]))
        continue
    for c in df.columns:
        vals = kandidat(df[c].tolist())
        if not vals: continue
        uniq = list(dict.fromkeys(vals))
        probe = (uniq[:SAMPLE] if len(uniq) <= SAMPLE
                 else [uniq[i] for i in range(0, len(uniq), max(1, len(uniq)//SAMPLE))][:SAMPLE])
        arten, frei = {}, ""
        for v in probe:
            a = enthaelt(v)
            if a: arten[a] = arten.get(a, 0) + 1
            elif not frei: frei = v[:140].replace("\n", "\\n")
        n_tref = sum(arten.values()); anteil = n_tref / len(probe)
        befund = ("abzugstext" if anteil >= 0.5 else "gemischt" if anteil > 0 else "eigen")
        rows.append(dict(datei=relp, spalte=str(c), zeilen=len(df), belegt=len(vals),
                         eindeutig=len(uniq), probe=len(probe), treffer=n_tref,
                         anteil=round(anteil, 3), arten=";".join(f"{k}={v}" for k, v in sorted(arten.items())),
                         befund=befund, maxlen=max(len(x) for x in vals), beispiel_frei=frei))
    log(f"  {relp}")

out = R / "spalten_befund.csv"
pd.DataFrame(rows).to_csv(out, index=False)
log(f"\ngeschrieben: {out}  ({len(rows)} Spalten)")
for b in ("abzugstext", "gemischt", "eigen", "lesefehler"):
    log(f"  {b:12} {sum(1 for r in rows if r.get('befund') == b)}")
