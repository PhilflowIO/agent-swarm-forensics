#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
74_exposition_vs_lesen.py — Exposition (rekonstruiert) gegen Lesen (gemessen).

Prueft die tragende Klammer aus main.tex Z. 292-328 / Z. 434 direkt:
  * Verfuegbarkeit ueber den Seitenkanal  39,4 %   (66_exposition.py, tab:exposure)
  * Verfuegbarkeit ueber den Strom N=100 95,1 %
  * nachweisbares Zitat                   12,5 %
  * NEU: gemessener Lesezugriff auf eine Traegerseite vor dem ersten Schreibversuch

Zusatzfrage: Wenn das Merkmal auf der EIGENEN Seite stand — hat der Name diese Seite
ueberhaupt gelesen? Das ist der direkte Test, ob "Exposition" Lesen bedeutet.

Lauf: .venv/bin/python scripts/betreiberlog/74_exposition_vs_lesen.py
      (setzt 70_parse.py und 71_lesespalte.py voraus)
"""
from __future__ import annotations
import os, glob, json, math
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(os.path.dirname(HERE))
ART = os.path.join(BASE, "artefakte"); OUT = os.path.join(ART, "betreiberlog")
LOG = open(os.path.join(OUT, "_exposition_vs_lesen.log"), "w", encoding="utf-8")


def L(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); LOG.write(s + "\n")


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"),) * 3
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p * 100, (c - h) * 100, (c + h) * 100


C = pd.read_csv(os.path.join(OUT, "kernmessung_namen.csv"))
MERK = ["runde", "cohort", "meldeformat", "sig_endzeile", "please_relay"]
alt = json.load(open(os.path.join(ART, "paper_exposition_kernzahlen.json")))
gesamt = pd.read_csv(os.path.join(ART, "paper_exposition_adoption_gesamt.csv"))

req = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(os.path.join(OUT, "req_*.parquet")))],
                ignore_index=True)
for c in ("name", "kind", "page"):
    req[c] = req[c].astype(str)
READ = {"browse", "raw", "editform", "bare", "archive_page"}
STRICT = {"browse", "raw"}

L("Die Klammer des Papers, um die gemessene Spalte erweitert (n = %d koordinierende Namen):" % len(C))
rows = []
for m in MERK:
    seite = float(gesamt[(gesamt.variante == "seite") & (gesamt.merkmal == m)].anteil_exponiert.iloc[0])
    strom = float(gesamt[(gesamt.variante == "strom_N100") & (gesamt.merkmal == m)].anteil_exponiert.iloc[0])
    k = int(C["gelesen_" + m].sum())
    p, lo, hi = wilson(k, len(C))
    rows.append(dict(merkmal=m, exposition_seite_pct=seite, exposition_strom100_pct=strom,
                     gelesen_traegerseite_n=k, gelesen_traegerseite_pct=p,
                     ci_lo=lo, ci_hi=hi))
T = pd.DataFrame(rows)
L(T.round(2).to_string(index=False))
T.to_csv(os.path.join(OUT, "klammer_exposition_lesen.csv"), index=False)
L(f"\nBisherige Untergrenze 'nachweisbares Zitat' (paper_exposition_kernzahlen.json, "
  f"lesebeweis_alt_p): {alt['lesebeweis_alt_p']:.1f} %")

# --- Hat ein exponierter Name seine eigene Seite gelesen?
L("\nWenn das Merkmal auf der EIGENEN Seite stand: wurde diese Seite vor dem ersten "
  "Schreibversuch gelesen?")
rl = req[(req["name"] != "") & req.kind.isin(READ) & (req.page != "")]
rl = rl[rl["name"].isin(set(C.label))]
t0 = dict(zip(C.label, C.t0))
rl = rl.assign(t0=rl["name"].map(t0))
rl = rl[rl.ts < rl.t0]
paare = set(zip(rl["name"], rl.page))
C["eigene_seite"] = C.seite_rev.str.replace("^dse~", "", regex=True)
C["las_eigene_seite"] = [(n, p) in paare for n, p in zip(C.label, C.eigene_seite)]
rows = []
for m in MERK:
    sub = C[C["exp_" + m]]
    k = int(sub.las_eigene_seite.sum())
    p, lo, hi = wilson(k, len(sub))
    rows.append(dict(merkmal=m, exponiert_auf_eigener_seite=len(sub),
                     davon_eigene_seite_gelesen=k, pct=p, ci_lo=lo, ci_hi=hi))
E = pd.DataFrame(rows)
L(E.round(2).to_string(index=False))
E.to_csv(os.path.join(OUT, "exposition_eigene_seite_gelesen.csv"), index=False)

# --- enge Lesedefinition zur Robustheit
L("\nRobustheit: enge Lesedefinition (nur action=browse und action=raw) gegen weite "
  "(zusaetzlich editform, bare, archive_page).")
L("Verteilung der Lesearten der koordinierenden Namen vor dem ersten Schreibversuch:")
L(str(rl.kind.value_counts().to_dict()))
L(f"Namen mit mindestens einer engen Lesung vorher: "
  f"{rl[rl.kind.isin(STRICT)]['name'].nunique()} von {len(C)}")
L(f"Namen mit mindestens einer weiten Lesung vorher: {rl['name'].nunique()} von {len(C)}")
C.to_csv(os.path.join(OUT, "kernmessung_namen.csv"), index=False)
LOG.close()

# ============================================================ Robustheitsvarianten
# Wird als eigener Block gefahren: dieselbe Vier-Felder-Tafel unter engerer
# Lesedefinition bzw. ohne action=archive (dort wird eine ALTE Version gelesen,
# unsere Merkmalsmaske ist aber die des jeweils aktuellen Standes -> Uebererfassung).
LOG = open(os.path.join(OUT, "_exposition_vs_lesen.log"), "a", encoding="utf-8")
ix = pd.read_parquet(os.path.join(ART, "paper_exposition_index.parquet"))
ix["time"] = pd.to_datetime(ix["time"], utc=True)
EPOCH = pd.Timestamp("1970-01-01", tz="UTC")
ixd = ix[ix.page_key.str.startswith("dse~")].sort_values(["page_key", "time"], kind="mergesort")
PST = {}
for pk, gg in ixd.groupby("page_key", sort=False):
    PST[pk[4:]] = (((gg.time - EPOCH).dt.total_seconds()).values.astype(np.int64),
                   gg.mask_body.values.astype(np.int64))
BASIS = ["sig_endzeile", "please_relay", "cohort", "runde", "state_conf", "uhrenpaar", "zeitstempel"]
BIT = {k: 1 << i for i, k in enumerate(BASIS)}


def meld(mask):
    return bool(mask & BIT["sig_endzeile"]) and bool(mask & (BIT["uhrenpaar"] | BIT["zeitstempel"])) \
        and bool(mask & (BIT["runde"] | BIT["state_conf"] | BIT["cohort"]))


def hasm(mask, m):
    return meld(mask) if m == "meldeformat" else bool(mask & BIT[m])


def mask_at(page, ts):
    e = PST.get(page)
    if e is None:
        return -1
    t, mm = e
    j = np.searchsorted(t, ts, side="right") - 1
    return int(mm[j]) if j >= 0 else 0


def rd_ci(k1, n1, k0, n0, z=1.96):
    p1, p0 = k1 / n1, k0 / n0
    se = math.sqrt(p1 * (1 - p1) / n1 + p0 * (1 - p0) / n0)
    return (p1 - p0) * 100, (p1 - p0 - z * se) * 100, (p1 - p0 + z * se) * 100


rl2 = rl.copy()
rl2["mask"] = [mask_at(p, int(t)) for p, t in zip(rl2.page, rl2.ts)]
out = []
for var, sel in [("weit", rl2), ("eng_browse_raw", rl2[rl2.kind.isin(STRICT)]),
                 ("ohne_archive", rl2[rl2.kind != "archive_page"])]:
    for m in MERK:
        car = sel[sel["mask"] > 0]
        names = set(car.loc[[hasm(x, m) for x in car["mask"]], "name"].unique())
        gl = C.label.isin(names).values
        ad = C["ad_" + m].values.astype(bool)
        n11, n10 = int((gl & ad).sum()), int((gl & ~ad).sum())
        n01, n00 = int((~gl & ad).sum()), int((~gl & ~ad).sum())
        r, lo, hi = rd_ci(n11, n11 + n10, n01, n01 + n00)
        out.append(dict(variante=var, merkmal=m, gelesen=n11 + n10,
                        p_ad_gelesen=n11 / (n11 + n10) * 100,
                        p_ad_nicht=n01 / (n01 + n00) * 100, rd=r, rd_lo=lo, rd_hi=hi,
                        uebernommen_ohne_lesebeleg=n01))
R = pd.DataFrame(out)
L("\nRobustheit der Vier-Felder-Tafel:")
L(R.round(2).to_string(index=False))
R.to_csv(os.path.join(OUT, "kernmessung_robustheit.csv"), index=False)
LOG.close()
