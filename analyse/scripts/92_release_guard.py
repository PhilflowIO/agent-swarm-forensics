#!/usr/bin/env python3
"""
92_release_guard.py — Torwaechter vor der Veroeffentlichung.

Prueft den gebauten Baum (analyse/release/dist/) noch einmal von aussen: steht dort
irgendwo Text, der woertlich aus dem Abzug stammt? Diese Pruefung kennt das
Regelwerk aus policy.json nicht und vertraut 91_release_build.py nicht -- sie
sucht einfach.

  * Tabellen (csv, parquet): ein einziger Treffer ist ein Fehler. Exit 1.
  * Prosa (BERICHT_*.md, Codebook, MECHANIK): Zitate sind dort ausdruecklich
    erlaubt (dieselbe Klasse wie die Belegzitate im Paper). Sie werden gezaehlt
    und ihr Umfang berichtet, nicht beanstandet -- damit sichtbar bleibt, ob aus
    Belegen unbemerkt eine Textsammlung geworden ist.
  * JSON/JSONL: wie Tabellen behandelt, jeder Stringwert wird geprueft.

Lauf: analyse/.venv/bin/python scripts/92_release_guard.py
"""
import bisect, csv, json, sys
from pathlib import Path
import pandas as pd

B = Path(__file__).resolve().parents[1]
A = B / "artefakte"
DIST = B / "release" / "dist" / "artefakte"
csv.field_size_limit(sys.maxsize)

MIN_LEN, FENSTER = 40, 60
PROSA = (".md", ".log", ".txt")

def log(*a): print(*a, flush=True)
if not DIST.exists(): sys.exit(f"{DIST} fehlt -- erst scripts/91_release_build.py laufen lassen.")

log("Abzug laden ...")
rev = pd.read_parquet(A / "schwarm_deltas.parquet", columns=["rev_id", "body", "delta"])
rev["body"] = rev["body"].fillna(""); rev["delta"] = rev["delta"].fillna("")
def heuhaufen(s):
    parts, offs, ids, pos = [], [], [], 0
    for rid, t in zip(rev["rev_id"], s):
        parts.append(t); offs.append(pos); ids.append(rid); pos += len(t) + 1
    return "\x00".join(parts), offs, ids
HAY = {f: heuhaufen(rev[f]) for f in ("delta", "body")}

def gefunden(w):
    for f in ("delta", "body"):
        p = HAY[f][0].find(w)
        if p >= 0:
            hay, offs, ids = HAY[f]
            return f, ids[bisect.bisect_right(offs, p) - 1]
    return None

def _wortgrenzen(v):
    yield 0
    for i in range(1, len(v)):
        if v[i - 1].isspace() and not v[i].isspace():
            yield i

def _var(v):
    yield v
    for a, b in ((" ⏎ ", "\n"), ("⏎", "\n"), (" | ", "\n")):
        if a in v: yield v.replace(a, b)

def traegt_abzugstext(s):
    if len(s) < MIN_LEN or s.count(" ") < 3: return None
    for v in _var(s):
        t = gefunden(v)
        if t: return t
        # Wortgenau statt im Raster: ein festes Raster verfehlt kurze eingebettete
        # Zitate, und genau die soll diese Gegenprobe finden.
        if len(v) > FENSTER:
            for i in _wortgrenzen(v):
                if i > len(v) - FENSTER: break
                t = gefunden(v[i:i + FENSTER])
                if t: return t
    return None

def strings_json(o):
    if isinstance(o, str): yield o
    elif isinstance(o, dict):
        for v in o.values(): yield from strings_json(v)
    elif isinstance(o, list):
        for v in o: yield from strings_json(v)

verstoesse, prosa_stat = [], []
for p in sorted(x for x in DIST.rglob("*") if x.is_file()):
    relp = str(p.relative_to(DIST))
    if p.suffix in PROSA:
        txt = p.read_text(encoding="utf-8", errors="replace")
        zeilen = [z.strip() for z in txt.split("\n")]
        tref = [z for z in zeilen if len(z) >= MIN_LEN and traegt_abzugstext(z)]
        if tref:
            prosa_stat.append(dict(datei=relp, zeilen=len(zeilen), zitatzeilen=len(tref),
                                   zitatzeichen=sum(len(z) for z in tref)))
        continue
    if p.suffix in (".json", ".jsonl"):
        werte = []
        if p.suffix == ".json":
            werte = list(strings_json(json.loads(p.read_text(encoding="utf-8"))))
        else:
            for z in p.read_text(encoding="utf-8").splitlines():
                if z.strip(): werte += list(strings_json(json.loads(z)))
        for w in set(werte):
            t = traegt_abzugstext(w)
            if t: verstoesse.append(dict(datei=relp, spalte="-", wert=w[:120], quelle=f"{t[0]}#{t[1]}"))
        continue
    if p.suffix not in (".csv", ".parquet"): continue
    df = (pd.read_csv(p, dtype=str, keep_default_na=False, engine="python")
          if p.suffix == ".csv" else pd.read_parquet(p))
    for c in df.columns:
        if str(c).endswith("_ref"): continue
        vals = [str(v) for v in df[c].tolist() if v is not None and str(v).strip() not in ("", "nan", "None")]
        if not vals or max(len(v) for v in vals) < MIN_LEN: continue
        for w in dict.fromkeys(vals):
            t = traegt_abzugstext(w)
            if t:
                verstoesse.append(dict(datei=relp, spalte=str(c), wert=w[:120], quelle=f"{t[0]}#{t[1]}"))
                break
    log(f"  {relp}")

log("\n===== Ergebnis =====")
if prosa_stat:
    log(f"Prosa mit Belegzitaten ({len(prosa_stat)} Dateien) -- erlaubt, hier zur Kontrolle:")
    for r in sorted(prosa_stat, key=lambda r: -r["zitatzeichen"])[:15]:
        log(f"  {r['datei']:44} {r['zitatzeilen']:>4} Zitatzeilen, {r['zitatzeichen']:>7} Zeichen")
    log(f"  Summe: {sum(r['zitatzeichen'] for r in prosa_stat)} Zeichen in "
        f"{sum(r['zitatzeilen'] for r in prosa_stat)} Zeilen")
if verstoesse:
    log(f"\nFEHLER: {len(verstoesse)} Spalten/Werte tragen weiterhin Abzugstext:")
    for v in verstoesse[:40]:
        log(f"  {v['datei']} :: {v['spalte']}  <- {v['quelle']}\n      {v['wert']}")
    pd.DataFrame(verstoesse).to_csv(B / "release" / "guard_verstoesse.csv", index=False)
    sys.exit(1)
log("\nOK -- keine Tabelle und keine JSON-Datei traegt Abzugstext.")
