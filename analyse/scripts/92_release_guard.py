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

# ---------------------------------------------------------------- Netzkennungen
# Zweite, unabhaengige Gegenprobe: keine nicht freigegebene Betreiberlog-Datei, keine
# Adresse und kein /16 ausserhalb der belegten Cloud-Bereiche -- weder in den Artefakten
# noch in dem, was 93_release_repo.py zusaetzlich veroeffentlicht. Werte werden nie
# ausgegeben, nur ihr Ort.
import ipaddress, re
POL = json.loads((B / "release" / "policy.json").read_text(encoding="utf-8"))
NETZ = POL["netzkennungen"]
W = pd.read_csv(A / "paper_netzblock_whois.csv", dtype=str, keep_default_na=False)
BELEGT = set()
for bereich in W.loc[W["anbieter"].isin(NETZ["freigegebene_anbieter"]), "range"]:
    lo, hi = (int(ipaddress.IPv4Address(x.strip())) >> 16 for x in bereich.split("-"))
    BELEGT |= {f"{n >> 8}.{n & 255}" for n in range(lo, hi + 1)}
UNBELEGT16 = set()
for p in A.rglob("*.csv"):
    kopf = p.open(encoding="utf-8", errors="replace").readline().strip().split(",")
    sp = [s for s in kopf if s in NETZ["ip16_spalten"]]
    if sp:
        UNBELEGT16 |= set(pd.read_csv(p, dtype=str, keep_default_na=False, usecols=sp).stack())
UNBELEGT16 = {v for v in UNBELEGT16 if re.fullmatch(r"\d{1,3}\.\d{1,3}", v)} - BELEGT
IP4 = re.compile(r"(?<![\d.])(\d{1,3})\.(\d{1,3})\.\d{1,3}\.\d{1,3}(?![\d.])")
P16_KONTEXT = re.compile(r"(?:`(\d{1,3}\.\d{1,3})`|(?<![\w.])(\d{1,3}\.\d{1,3})(?=/16|\.x|\.\*|\.0\.0|`))")
PSEUDO16 = re.compile(r"netz-[0-9a-f]{8}")

def netz_treffer(txt):
    n = sum(1 for m in IP4.finditer(txt) if f"{m.group(1)}.{m.group(2)}" not in BELEGT)
    n += sum(1 for m in P16_KONTEXT.finditer(txt) if (m.group(1) or m.group(2)) in UNBELEGT16)
    # Markdown-Tabellen: nur Spalten, deren Kopf eine Netzkennung ankuendigt -- eine
    # Statistikspalte mit 0.64 ist kein Netz.
    spalten = set()
    for z in txt.split("\n"):
        if not z.lstrip().startswith("|"):
            spalten = set(); continue
        zellen = [c.strip().strip("`") for c in z.split("|")]
        if not spalten and any(c in NETZ["ip16_spalten"] for c in zellen):
            spalten = {j for j, c in enumerate(zellen) if c in NETZ["ip16_spalten"]}; continue
        n += sum(1 for j in spalten if j < len(zellen) and zellen[j] in UNBELEGT16)
    return n

netz_verstoesse = []
for p in sorted(x for x in DIST.rglob("*") if x.is_file()):
    relp = str(p.relative_to(DIST))
    if relp.split("/")[0] in POL["betreiberlog_verzeichnisse"] and relp not in POL["betreiberlog_freigabe"]:
        netz_verstoesse.append(dict(datei=relp, art="Betreiberlog-Datei nicht freigegeben", n=1)); continue
    if p.suffix in (".csv", ".parquet"):
        df = (pd.read_csv(p, dtype=str, keep_default_na=False, engine="python")
              if p.suffix == ".csv" else pd.read_parquet(p))
        for c in df.columns:
            s = df[c].astype(str)
            if str(c) in NETZ["ip16_spalten"]:
                n = int((~s.isin(BELEGT) & ~s.str.fullmatch(PSEUDO16) & s.str.fullmatch(r"\d{1,3}\.\d{1,3}")).sum())
                if relp in NETZ["block_spalten"]:
                    n = int((~df["anbieter"].isin(NETZ["freigegebene_anbieter"]) & ~s.str.fullmatch(PSEUDO16)).sum())
            else:
                n = int(s.map(netz_treffer).sum()) if s.str.contains(IP4).any() else 0
            if n: netz_verstoesse.append(dict(datei=relp, art=f"Netzkennung in Spalte {c}", n=n))
    elif p.suffix in PROSA + (".json", ".jsonl"):
        n = netz_treffer(p.read_text(encoding="utf-8", errors="replace"))
        if n: netz_verstoesse.append(dict(datei=relp, art="Netzkennung im Text", n=n))

ROOT = B.parent
SKRIPTE = (".py", ".json", ".md", ".sql", ".sh", ".c", ".txt", ".csv")
for p in [*sorted((ROOT / "paper" / "tables").rglob("*.tex")),
          *sorted(x for x in (B / "scripts").rglob("*")
                  if x.is_file() and x.suffix in SKRIPTE and "__pycache__" not in x.parts),
          ROOT / "paper" / "main.tex", ROOT / "MECHANIK.md", ROOT / "README.md"]:
    if p.exists() and (n := netz_treffer(p.read_text(encoding="utf-8", errors="replace"))):
        netz_verstoesse.append(dict(datei=str(p.relative_to(ROOT)), art="Netzkennung im Text", n=n))

# Der Skriptbaum wird ungefiltert veroeffentlicht. Betreiberlog-Ausgaben gehoeren
# nach artefakte/ (dort greift die Sperre), nie neben den Code.
for p in sorted((B / "scripts" / "betreiberlog").rglob("*")):
    if p.is_file() and p.suffix != ".py" and "__pycache__" not in p.parts:
        netz_verstoesse.append(dict(datei=str(p.relative_to(ROOT)),
                                    art="Datendatei im Betreiberlog-Skriptbaum", n=1))

log(f"\nNetzkennungen: {len(BELEGT)} belegte Cloud-/16, {len(UNBELEGT16)} bekannte unbelegte /16 geprueft.")
if netz_verstoesse:
    log(f"FEHLER: {len(netz_verstoesse)} Stellen mit Betreiberlog-Datei oder unbelegter Netzkennung:")
    for v in netz_verstoesse[:40]:
        log(f"  {v['datei']} :: {v['art']} ({v['n']}x)")
    verstoesse += [dict(datei=v["datei"], spalte=v["art"], wert=f"{v['n']} Treffer", quelle="netzkennung")
                   for v in netz_verstoesse]

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
