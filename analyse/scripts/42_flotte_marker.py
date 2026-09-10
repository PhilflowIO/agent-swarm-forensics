#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
42_flotte_marker.py
===================
A. Marker-Multiplizitaet: fiktive (Monat,Tag)-Marker in Label-Namen, kalendergueltig,
   genau ein distinkter Marker je Label -> paper_flotte_marker_multiplizitaet.csv
   (wird nur ueberschrieben, wenn die Regeneration die vorhandene Tabelle exakt trifft,
   sonst *_regen.csv + Diff im Log).
B. Sammelbild-Schaetzer (Inversion E[D|n] = N(1-(1-1/N)^n), N=365, ganzzahliger
   Akzeptanzbereich) fuer die daraus ableitbaren Zeilen von paper_flotte_schaetzer*.csv
   -> paper_flotte_schaetzer_regen.csv. Nicht ableitbare Zeilen werden NICHT erzeugt.
C. Sensitivitaet: nur Labels, deren Marker in >= 2 archivierten Revisionen steht
   (Revisionszahl je Label aus revisions.jsonl, gegen labels.jsonl.stored_revisions geprueft)
   -> paper_robust_marker_min2rev.csv (month, day, n_labels) + paper_robust_marker_D.csv.

Alle Pfade RELATIV zum Skript-Ort (analyse/scripts/ -> analyse/).
Lauf:  .venv/bin/python scripts/42_flotte_marker.py
Log:   artefakte/_paper_flotte.log
"""
from __future__ import annotations
import os, re, io, math, calendar, collections
import pandas as pd
from scipy import optimize

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
DATA = os.path.join(BASE, "data")
ART = os.path.join(BASE, "artefakte")
OUT = lambda n: os.path.join(ART, n)
LOG = open(OUT("_paper_flotte.log"), "w", encoding="utf-8")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s); LOG.write(s + "\n"); LOG.flush()


# ---------------------------------------------------------------------------------------
# Extraktionsregel (empirisch gegen die vorhandene Tabelle abgeglichen, 333/333 Zeilen):
#   (a) Monatskuerzel + genau zwei Ziffern, nicht von einer weiteren Ziffer gefolgt (Jan01, Sep13)
#   (b) ausgeschriebener Monat + zwei Ziffern (June14, April19, March13)
#   (c) ausgeschriebener Monat + ausgeschriebener Tag (MayTen, JuneSeven, MayTwo)
#   NICHT: Kuerzel + Wort (JanTen, AprNineteen), "Sept08", Ein-Ziffer-Formen (Jul9).
#   Kalendergueltig (Tag <= Monatslaenge, Feb <= 28); ein Label zaehlt nur mit genau
#   EINEM distinkten gueltigen Marker.
# ---------------------------------------------------------------------------------------
MONS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MI = {m: i + 1 for i, m in enumerate(MONS)}
ONES = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]
TEENS = ["Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
WORDS = {ONES[i]: i for i in range(1, 10)}
WORDS.update({w: 10 + i for i, w in enumerate(TEENS)})
WORDS.update({"Twenty" + ONES[i]: 20 + i for i in range(1, 10)})
WORDS.update({"Twenty": 20, "Thirty": 30, "ThirtyOne": 31})
WRX = "|".join(sorted(WORDS, key=len, reverse=True))
FULL = r"(January|February|March|April|May|June|July|August|September|October|November|December)"
ABBR = r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
RX = re.compile(ABBR + r"(\d{2})(?!\d)()|" + FULL + r"(?:(\d{2})(?!\d)|(" + WRX + r")(?![a-z]))")


def valid(m: str, d: int) -> bool:
    return 1 <= d <= calendar.monthrange(2027, MI[m])[1]  # 2027: kein Schaltjahr, Feb=28


def markers(s: str, check: bool = True) -> set[tuple[str, int]]:
    out = set()
    for m1, d1, w1, m2, d2, w2 in RX.findall(s):
        m = (m1 or m2)[:3]
        d = int(d1 or d2) if (d1 or d2) else WORDS[w1 or w2]
        if (not check) or valid(m, d):
            out.add((m, d))
    return out


def table(labels: pd.Series, check: bool = True) -> pd.DataFrame:
    """Eine Zeile je belegtem (Monat,Tag); labels alphabetisch, '|'-getrennt."""
    bucket: dict[tuple[str, int], set[str]] = collections.defaultdict(set)
    for l in labels:
        ms = markers(l, check)
        if len(ms) == 1:
            bucket[next(iter(ms))].add(l)
    rows = [dict(month=m, day=d, n_labels=len(v), labels="|".join(sorted(v)))
            for (m, d), v in bucket.items()]
    df = pd.DataFrame(rows)
    df["_k"] = df.month.map(MI)
    return df.sort_values(["_k", "day"]).drop(columns="_k").reset_index(drop=True)


# ---------------------------------------------------------------------------------------
# Sammelbild-Inversion, ganzzahliger Akzeptanzbereich
#   n_hat = kleinstes ganzes n mit E[D|n] >= D
#   [lo, hi] = ganze n mit |D - E[D|n]| <= 1.96 * SD(D|n)   (Normalapproximation)
# Reproduziert exakt die berichteten Werte fuer D in {335, 353, 294, 287, 333}.
# ---------------------------------------------------------------------------------------
N = 365
Z = 1.959964


def E_D(n, N=N): return N * (1 - (1 - 1 / N) ** n)
def Var_D(n, N=N):
    p1 = (1 - 1 / N) ** n; p2 = (1 - 2 / N) ** n
    return N * p1 + N * (N - 1) * p2 - N * N * p1 * p1
def invert(D):
    return optimize.brentq(lambda n: E_D(n) - D, 1, 50000)
def ci(D):
    lo = optimize.brentq(lambda n: E_D(n) + Z * math.sqrt(Var_D(n)) - D, 1, 50000)
    hi = optimize.brentq(lambda n: E_D(n) - Z * math.sqrt(Var_D(n)) - D, 1, 50000)
    return lo, hi
def est_row(verfahren, D, bemerkung=""):
    lo, hi = ci(D)
    return dict(verfahren=verfahren, beobachtet_D=int(D), n_hat=math.ceil(invert(D)),
                ci_lo=math.ceil(lo), ci_hi=math.floor(hi), bemerkung=bemerkung)


# =======================================================================================
# Daten
# =======================================================================================
labels = pd.read_json(os.path.join(DATA, "labels.jsonl"), lines=True)
revs = pd.read_json(os.path.join(DATA, "revisions.jsonl"), lines=True)
log(f"labels.jsonl: {len(labels)} Labels; revisions.jsonl: {len(revs)} Revisionen, {revs.label.nunique()} distinkte Labels")

rev_count = revs.label.value_counts()
lab_rc = labels.set_index("label")["stored_revisions"]
mism = (lab_rc - rev_count.reindex(lab_rc.index).fillna(0)).abs()
assert mism.max() == 0, f"stored_revisions != Revisionszahl fuer {int((mism > 0).sum())} Labels"
log("Pruefung: labels.stored_revisions == count(revisions.jsonl by label) fuer alle Labels: OK")

# =======================================================================================
# A  Marker-Multiplizitaet
# =======================================================================================
log("\n== A  Marker-Multiplizitaet (kalendergueltig, genau ein Marker je Label) ==")
mult = table(labels.label, check=True)
D_full = len(mult); n_full = int(mult.n_labels.sum())
log(f"D = {D_full} belegte (Monat,Tag), n = {n_full} datierte Labels, max. Belegung {int(mult.n_labels.max())}")

target = OUT("paper_flotte_marker_multiplizitaet.csv")
buf = io.StringIO(); mult.to_csv(buf, index=False); new_txt = buf.getvalue()
if os.path.exists(target):
    old_raw = open(target, "rb").read()
    old_txt = old_raw.decode("utf-8").replace("\r\n", "\n")   # Original hat CRLF-Zeilenenden
    if old_txt == new_txt:
        if old_raw.decode("utf-8") == new_txt:
            log(f"Regeneration BYTE-IDENTISCH mit {target} -> Datei unveraendert gelassen")
        else:
            log(f"Regeneration INHALTSGLEICH mit {target} (nur Zeilenenden CRLF vs LF) -> Datei unveraendert gelassen")
    else:
        old = pd.read_csv(target)
        same_rows = old.merge(mult, on=["month", "day", "n_labels", "labels"], how="inner")
        log(f"ABWEICHUNG: alt {len(old)} Zeilen, neu {len(mult)} Zeilen, identische Zeilen {len(same_rows)}")
        ok = set(map(tuple, old[["month", "day", "n_labels"]].values))
        nk = set(map(tuple, mult[["month", "day", "n_labels"]].values))
        for k in sorted(ok ^ nk): log("   diff (month,day,n_labels):", k, "nur-alt" if k in ok else "nur-neu")
        regen = OUT("paper_flotte_marker_multiplizitaet_regen.csv")
        open(regen, "w", encoding="utf-8").write(new_txt)
        log(f"-> {regen}  (Original unangetastet)")
else:
    open(target, "w", encoding="utf-8").write(new_txt); log(f"-> {target} (neu)")

# =======================================================================================
# B  Schaetzer-Zeilen, soweit aus dieser Extraktion ableitbar
# =======================================================================================
log("\n== B  Sammelbild-Schaetzer (ganzzahlige Inversion) ==")
mult_all = table(labels.label, check=False)          # inkl. kalenderungueltiger Marker (Jul77, Jul99)
D_all = len(mult_all)
invalid = sorted((m, d) for m, d in zip(mult_all.month, mult_all.day) if not valid(m, d))
log(f"D ohne Kalenderpruefung = {D_all}; ungueltige Marker: {invalid}")
est = pd.DataFrame([
    est_row("Labels, alle (m,d)-Marker", D_all, "enthaelt " + "/".join(f"{m}{d}" for m, d in invalid) + " (kalenderungueltig)"),
    est_row("Labels, nur kalendergueltig", D_full, "Fassung in MECHANIK.md v1"),
])
for r in est.itertuples():
    log(f"  {r.verfahren}: D={r.beobachtet_D}  n_hat={r.n_hat}  95% [{r.ci_lo}, {r.ci_hi}]")
est.to_csv(OUT("paper_flotte_schaetzer_regen.csv"), index=False)
log(f"-> {OUT('paper_flotte_schaetzer_regen.csv')}")
log("  NICHT regeneriert (Ableitung aus diesem Skript nicht belegbar): 'Labels + Seitennamen' (D=353),")
log("  'Kohortennennungen im Text' (D=294), 'nur Body-Kohorten' (D=287), 'Verhaeltnis Labels:Kohorten',")
log("  'bereinigt: minus 20 reale Schreibdaten' (Monte-Carlo-Intervall, vgl. 53_mathematik.py Teil A).")

# =======================================================================================
# C  Sensitivitaet: Marker in >= 2 archivierten Revisionen
# =======================================================================================
log("\n== C  Sensitivitaet: nur Labels mit >= 2 archivierten Revisionen ==")
keep = labels.loc[labels.stored_revisions >= 2, "label"]
mult2 = table(keep, check=True)
D_min2 = len(mult2); n_min2 = int(mult2.n_labels.sum())
mult2[["month", "day", "n_labels"]].to_csv(OUT("paper_robust_marker_min2rev.csv"), index=False)
log(f"-> {OUT('paper_robust_marker_min2rev.csv')}  ({D_min2} Zeilen)")

rows = [dict(variante="alle Labels", min_revisions=1, D=D_full, n_labels=n_full),
        dict(variante="Labels mit >= 2 Revisionen", min_revisions=2, D=D_min2, n_labels=n_min2)]
for r in rows:
    lo, hi = ci(r["D"])
    r.update(n_hat=math.ceil(invert(r["D"])), ci_lo=math.ceil(lo), ci_hi=math.floor(hi))
    log(f"  {r['variante']}: D = {r['D']}, datierte Labels = {r['n_labels']}, n_hat = {r['n_hat']} [{r['ci_lo']}, {r['ci_hi']}]")
pd.DataFrame(rows).to_csv(OUT("paper_robust_marker_D.csv"), index=False)
log(f"-> {OUT('paper_robust_marker_D.csv')}")
log(f"\nD (alle) = {D_full}   D (>=2 Revisionen) = {D_min2}")
LOG.close()
