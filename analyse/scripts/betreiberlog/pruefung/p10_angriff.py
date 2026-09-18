#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
p10_angriff.py — Gegenpruefung der Lesemessung aus 71_lesespalte.py.

Bausteine:
  A  Reproduktion der Basiszahl (+24,2 pp) — ohne sie ist alles andere wertlos.
  B  Zirkelschluss-Test: woher kommt der Trefferbeleg? Eigene Seite / fremde Seite,
     Editformular / browse. Wenn der Effekt an editform-auf-eigener-Seite haengt,
     misst er Schreibabsicht.
  C  Fenstervariation 30 s / 120 s / 600 s / 3600 s / unbegrenzt.
  D  Kreuz-Placebo-Matrix: Traegerlesen von Merkmal X gegen Adoption von Merkmal Y.
     Wenn off-diagonal ~ diagonal, misst die Lesevariable allgemeine Aktivitaet.
  E  Zeit-Placebo: Lesen NACH t0 (t0+1h .. t0+2h) gegen Adoption bei t0.
     Rueckwaerts in der Zeit kann nichts uebertragen; jede Assoziation ist Konfundierung.
  F  Dosis: nur Lesemenge (Anzahl Pre-Reads) ohne jeden Merkmalsbezug.

Lauf: .venv/bin/python scripts/betreiberlog/pruefung/p10_angriff.py
Ausgabe: artefakte/betreiberlog/pruefung/*.csv, Log _p10.log
"""
from __future__ import annotations
import os, sys, math
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p00_lib import (READ_CONTENT, READ_STRICT, MERKMALE, HERKUNFT, hasm, rd_ci,
                     lade, seitenzustand, mask_at_factory, vier_felder, PRUEF, OUT)

LOG = open(os.path.join(PRUEF, "_p10.log"), "w", encoding="utf-8")


def L(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True); LOG.write(s + "\n")


def hdr(t):
    L("\n" + "=" * 88 + "\n" + t + "\n" + "=" * 88)


hdr("0  Laden")
req, ix, coord = lade()
L(f"Requests {len(req):,}  coordpop {len(coord)}")
PSTATE = seitenzustand(ix)
mask_at = mask_at_factory(PSTATE)
L(f"Seitenzustands-Zeitreihen {len(PSTATE):,}")

COORDSET = set(coord.label.astype(str))

# --- eigene Seiten je Name: alles was der Name je geschrieben hat -------------
own = {}
for lab, g in ix[ix.page_key.str.startswith("dse~")].groupby("label"):
    own.setdefault(str(lab), set()).update(p[4:] for p in g.page_key.unique())
wr = req[(req.kind == "write") & (req.name != "")]
for nm, g in wr[wr.name.isin(COORDSET)].groupby("name"):
    own.setdefault(str(nm), set()).update(x for x in g.page.unique() if x)
L(f"Namen mit bekannter eigener Seitenmenge: {len(own):,}")

# --- Lesetabelle der coordpop-Namen -----------------------------------------
READALL = READ_CONTENT
rl = req[req.name.isin(COORDSET) & req.kind.isin(READALL)][["name", "ts", "kind", "page"]].copy()
t0map = dict(zip(coord.label.astype(str), coord.t0.astype("int64")))
rl["t0"] = rl.name.map(t0map)
rl = rl[rl.t0.notna()]
rl["t0"] = rl.t0.astype("int64")
rl["lead"] = rl.t0 - rl.ts                   # >0: vor t0
L(f"Lesezugriffe (weit) benannter coordpop-Namen: {len(rl):,}; davon vor t0: {int((rl.lead>0).sum()):,}")

# Maske je Lesezugriff (nur einmal berechnen — teuer)
rl["mask"] = [mask_at(p, int(t)) for p, t in zip(rl.page, rl.ts)]
rl["eigene"] = [p in own.get(n, ()) for n, p in zip(rl.name, rl.page)]
for m in MERKMALE:
    rl["c_" + m] = [(mm > 0) and hasm(mm, m) for mm in rl["mask"]]
rl.to_parquet(os.path.join(PRUEF, "lesezugriffe_coordpop.parquet"))
L("Trefferanteile je Merkmal ueber alle Pre-t0-Lesezugriffe:")
pre_all = rl[rl.lead > 0]
for m in MERKMALE:
    L(f"   {m:14s} {pre_all['c_'+m].mean()*100:5.1f} % der Lesezugriffe trafen eine Traegerseite")


def gelesen_flags(sub, m):
    return set(sub.loc[sub["c_" + m], "name"].unique())


def tafel(sub, m, tag):
    s = gelesen_flags(sub, m)
    coord["_g"] = coord.label.astype(str).isin(s)
    d = vier_felder(coord, "_g", "ad_" + m)
    d.update(variante=tag, merkmal=m, herkunft=HERKUNFT[m])
    return d


# ============================================================ A Reproduktion
hdr("A  Reproduktion der Basiszahl")
base = pre_all[pre_all["mask"] > 0]
rows = [tafel(base, m, "basis_weit") for m in MERKMALE]
bt = pd.DataFrame(rows)
L(bt[["merkmal", "herkunft", "n_gelesen", "p_ad_gelesen", "n_nicht", "p_ad_nicht", "rd", "rd_lo", "rd_hi"]]
  .round(1).to_string(index=False))
L("Soll laut Bericht lese-spalte.md Z.191: Rundenmarker n_gelesen 560, 70,5 % / 580, 46,4 %, RD +24,2 (18,6-29,7)")

# ============================================================ B Zirkelschluss
hdr("B  Zirkelschluss: woher stammt der Trefferbeleg?")
scopes = {
    "weit_alle":            dict(kinds=READ_CONTENT, eigene=None),
    "weit_nur_fremd":       dict(kinds=READ_CONTENT, eigene=False),
    "weit_nur_eigene":      dict(kinds=READ_CONTENT, eigene=True),
    "eng_alle":             dict(kinds=READ_STRICT,  eigene=None),
    "eng_nur_fremd":        dict(kinds=READ_STRICT,  eigene=False),
    "nur_editform_alle":    dict(kinds={"editform"}, eigene=None),
    "nur_editform_fremd":   dict(kinds={"editform"}, eigene=False),
    "nur_editform_eigene":  dict(kinds={"editform"}, eigene=True),
    "ohne_editform_alle":   dict(kinds=READ_CONTENT - {"editform"}, eigene=None),
    "ohne_editform_fremd":  dict(kinds=READ_CONTENT - {"editform"}, eigene=False),
}
rows = []
for tag, cfg in scopes.items():
    sub = base[base.kind.isin(cfg["kinds"])]
    if cfg["eigene"] is not None:
        sub = sub[sub.eigene == cfg["eigene"]]
    for m in MERKMALE:
        rows.append(tafel(sub, m, tag))
bz = pd.DataFrame(rows)
bz.to_csv(os.path.join(PRUEF, "b_zirkelschluss.csv"), index=False)
piv = bz.pivot(index="variante", columns="merkmal", values="rd").round(1)
pivn = bz.pivot(index="variante", columns="merkmal", values="n_gelesen")
L("Risikodifferenz (pp) je Leseart-Scope:")
L(piv.reindex(list(scopes)).to_string())
L("\nn (gelesen) je Scope:")
L(pivn.reindex(list(scopes)).to_string())

L("\nZusammensetzung des Trefferbelegs beim Rundenmarker (basis_weit, n pro Name eindeutig):")
sr = base[base.c_runde]
gs = set(sr.name.unique())
nur_eigene = gs - set(sr[~sr.eigene].name.unique())
nur_editform = gs - set(sr[sr.kind != "editform"].name.unique())
eigene_editform_only = gs - set(sr[~((sr.eigene) & (sr.kind == "editform"))].name.unique())
L(f"  Namen mit Traegertreffer gesamt: {len(gs)}")
L(f"  davon Treffer AUSSCHLIESSLICH auf eigener Seite: {len(nur_eigene)} ({len(nur_eigene)/len(gs)*100:.1f} %)")
L(f"  davon Treffer AUSSCHLIESSLICH per editform: {len(nur_editform)} ({len(nur_editform)/len(gs)*100:.1f} %)")
L(f"  davon Treffer AUSSCHLIESSLICH per editform auf eigener Seite: {len(eigene_editform_only)} "
  f"({len(eigene_editform_only)/len(gs)*100:.1f} %)")

# ============================================================ C Fenster
hdr("C  Vorlauf-Fenster")
rows = []
for w, tag in [(30, "30s"), (120, "2min"), (600, "10min"), (3600, "1h"), (86400, "24h"), (10**12, "unbegrenzt")]:
    for kindtag, kinds in [("weit", READ_CONTENT), ("eng", READ_STRICT),
                           ("weit_fremd", READ_CONTENT), ("eng_fremd", READ_STRICT)]:
        sub = base[(base.lead <= w) & base.kind.isin(kinds)]
        if kindtag.endswith("fremd"):
            sub = sub[~sub.eigene]
        for m in MERKMALE:
            d = tafel(sub, m, f"{kindtag}@{tag}")
            d["fenster_s"] = w; d["leseart"] = kindtag
            rows.append(d)
cf = pd.DataFrame(rows)
cf.to_csv(os.path.join(PRUEF, "c_fenster.csv"), index=False)
for kindtag in ["weit", "eng", "weit_fremd", "eng_fremd"]:
    s = cf[cf.leseart == kindtag]
    L(f"\nLeseart {kindtag} — RD (pp) je Fenster:")
    L(s.pivot(index="variante", columns="merkmal", values="rd").round(1).to_string())
    L("n(gelesen):")
    L(s.pivot(index="variante", columns="merkmal", values="n_gelesen").to_string())

# ============================================================ D Kreuz-Placebo
hdr("D  Kreuz-Placebo-Matrix: Traegerlesen X -> Adoption Y")
for tag, sub in [("weit", base), ("weit_fremd", base[~base.eigene]),
                 ("eng_fremd", base[(~base.eigene) & base.kind.isin(READ_STRICT)])]:
    rows = []
    for mx in MERKMALE:
        s = gelesen_flags(sub, mx)
        coord["_g"] = coord.label.astype(str).isin(s)
        r = {"gelesen_X": mx}
        for my in MERKMALE:
            r["ad_" + my] = vier_felder(coord, "_g", "ad_" + my)["rd"]
        rows.append(r)
    mat = pd.DataFrame(rows).set_index("gelesen_X").round(1)
    mat.to_csv(os.path.join(PRUEF, f"d_kreuzplacebo_{tag}.csv"))
    L(f"\nScope {tag} — RD (pp), Zeile = gelesenes Traegermerkmal, Spalte = uebernommenes Merkmal:")
    L(mat.to_string())
    dia = np.array([mat.loc[m, "ad_" + m] for m in MERKMALE])
    off = mat.values[~np.eye(len(MERKMALE), dtype=bool)]
    L(f"  Diagonale Mittel {dia.mean():.1f} pp | Nebendiagonale Mittel {np.nanmean(off):.1f} pp "
      f"| Ueberschuss {dia.mean()-np.nanmean(off):+.1f} pp")

# ============================================================ E Zeit-Placebo
hdr("E  Zeit-Placebo: Lesen NACH t0")
rows = []
windows = [("vor_0_600", (0, 600)), ("nach_0_600", (-600, 0)),
           ("nach_3600_7200", (-7200, -3600)), ("nach_24h_25h", (-90000, -86400)),
           ("vor_unbegrenzt", (0, 10**12))]
for tag, (lo, hi) in windows:
    sub = base[(base.lead > lo) & (base.lead <= hi)] if lo >= 0 else base[(base.lead > lo) & (base.lead <= hi)]
    for m in MERKMALE:
        d = tafel(sub, m, tag)
        rows.append(d)
ez = pd.DataFrame(rows)
ez.to_csv(os.path.join(PRUEF, "e_zeitplacebo.csv"), index=False)
L(ez.pivot(index="variante", columns="merkmal", values="rd").reindex([w[0] for w in windows]).round(1).to_string())
L("\nn(gelesen):")
L(ez.pivot(index="variante", columns="merkmal", values="n_gelesen").reindex([w[0] for w in windows]).to_string())

# ============================================================ F Dosis ohne Merkmal
hdr("F  Reine Lesemenge ohne jeden Merkmalsbezug")
cnt = pre_all.groupby("name").size()
coord["n_pre"] = coord.label.astype(str).map(cnt).fillna(0).astype(int)
coord["las_ueberhaupt"] = coord.n_pre > 0
rows = []
for m in MERKMALE:
    d = vier_felder(coord, "las_ueberhaupt", "ad_" + m)
    d.update(merkmal=m, variante="las_irgendeine_seite")
    rows.append(d)
    for thr in (2, 5, 10, 25):
        coord["_g"] = coord.n_pre >= thr
        d = vier_felder(coord, "_g", "ad_" + m)
        d.update(merkmal=m, variante=f"n_pre>={thr}")
        rows.append(d)
fd = pd.DataFrame(rows)
fd.to_csv(os.path.join(PRUEF, "f_dosis.csv"), index=False)
L(fd.pivot(index="variante", columns="merkmal", values="rd").round(1).to_string())
L("\nVerteilung n_pre: " + str(coord.n_pre.describe().round(1).to_dict()))
L("Adoptionsrate nach n_pre-Quartil (Rundenmarker):")
coord["q"] = pd.qcut(coord.n_pre.rank(method="first"), 4, labels=["Q1", "Q2", "Q3", "Q4"])
L(coord.groupby("q", observed=True).agg(n=("label", "size"), n_pre_med=("n_pre", "median"),
                                        ad_runde=("ad_runde", "mean"),
                                        gelesen_runde=("gelesen_runde", "mean")).round(3).to_string())

coord.drop(columns=["_g"], errors="ignore").to_csv(os.path.join(PRUEF, "coord_erweitert.csv"), index=False)
L("\nfertig p10.")
LOG.close()
