#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
p20_konfundierung.py — Teil 2 der Gegenpruefung.

  G  Ueberlappung Lesevariable x Expositionsvariable des Papers (exp_*__seite).
     Wenn 'gelesen' im Wesentlichen 'eigene Seite trug es schon' ist, misst die
     neue Spalte nichts Neues.
  H  Zeit-Placebo, korrekt gerechnet (Lesen NACH t0).
  I  Kalenderzeit: t0 vor/nach dem 16. Juni; Adoption folgt einem Trend.
  J  Kontrollierte Schaetzung: Logit ad ~ gelesen + log(n_pre) + Kalenderzeit
     + Schreibvolumen + Lebensdauer + Aufgabenfamilie (Vorbild tab:progress).
  K  Die 249 mit der fehlenden Kontrollgruppe: Nicht-Uebernehmer ohne eigene Quelle.

Lauf: .venv/bin/python scripts/betreiberlog/pruefung/p20_konfundierung.py
"""
from __future__ import annotations
import os, sys, re, math
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p00_lib import (READ_CONTENT, READ_STRICT, MERKMALE, HERKUNFT, rd_ci, wilson,
                     lade, vier_felder, PRUEF, OUT, ART)

LOG = open(os.path.join(PRUEF, "_p20.log"), "w", encoding="utf-8")


def L(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True); LOG.write(s + "\n")


def hdr(t):
    L("\n" + "=" * 88 + "\n" + t + "\n" + "=" * 88)


hdr("0  Laden")
req, ix, coord = lade()
rl = pd.read_parquet(os.path.join(PRUEF, "lesezugriffe_coordpop.parquet"))
L(f"Lesezugriffe coordpop {len(rl):,}; coordpop {len(coord)}")
coord["label"] = coord.label.astype(str)
base_all = rl[rl["mask"] > 0]              # alle Zeitpunkte, nicht nur vor t0
pre = base_all[base_all.lead > 0]


def gset(sub, m):
    return set(sub.loc[sub["c_" + m], "name"].astype(str).unique())


def taf(flag, m):
    coord["_g"] = flag
    d = vier_felder(coord, "_g", "ad_" + m)
    d.update(merkmal=m)
    return d


# =========================================================== G Ueberlappung
hdr("G  Ist 'gelesen' nur die Expositionsvariable des Papers?")
rows = []
for m in MERKMALE:
    g = coord.label.isin(gset(pre, m))
    e = coord["exp_" + m].astype(bool)
    gf = coord.label.isin(gset(pre[~pre.eigene], m))           # nur fremde Seiten
    ge = coord.label.isin(gset(pre[pre.eigene], m))            # nur eigene Seiten
    rows.append(dict(merkmal=m, herkunft=HERKUNFT[m],
                     n_gelesen=int(g.sum()), n_exp=int(e.sum()),
                     beide=int((g & e).sum()),
                     gelesen_ohne_exp=int((g & ~e).sum()),
                     exp_ohne_gelesen=int((~g & e).sum()),
                     phi=float(np.corrcoef(g.astype(float), e.astype(float))[0, 1]),
                     anteil_gelesen_der_exp_ist=(g & e).sum() / max(g.sum(), 1) * 100,
                     n_gelesen_eigene=int(ge.sum()), n_gelesen_fremd=int(gf.sum())))
gt = pd.DataFrame(rows)
gt.to_csv(os.path.join(PRUEF, "g_ueberlappung.csv"), index=False)
L(gt.round(2).to_string(index=False))

L("\nGeschichtet nach Expositionsstatus der EIGENEN Seite — RD des Lesens innerhalb der Schicht:")
rows = []
for m in MERKMALE:
    for scope, sub in [("weit_alle", pre), ("weit_fremd", pre[~pre.eigene])]:
        g = coord.label.isin(gset(sub, m))
        for ev, lab in [(False, "eigene Seite trug es NICHT"), (True, "eigene Seite trug es")]:
            sel = coord[coord["exp_" + m].astype(bool) == ev].copy()
            gg = sel.label.isin(gset(sub, m))
            a = sel["ad_" + m].astype(bool)
            n11, n10 = int((gg & a).sum()), int((gg & ~a).sum())
            n01, n00 = int((~gg & a).sum()), int((~gg & ~a).sum())
            r, lo, hi = rd_ci(n11, n11 + n10, n01, n01 + n00)
            rows.append(dict(merkmal=m, scope=scope, schicht=lab, n=len(sel),
                             n_gelesen=n11 + n10, rd=r, rd_lo=lo, rd_hi=hi))
gs = pd.DataFrame(rows)
gs.to_csv(os.path.join(PRUEF, "g_geschichtet.csv"), index=False)
L(gs.round(1).to_string(index=False))

# =========================================================== H Zeit-Placebo
hdr("H  Zeit-Placebo: Lesen NACH dem ersten Schreibversuch")
wins = [("vor  0..600 s", 0, 600), ("vor  0..3600 s", 0, 3600), ("vor unbegrenzt", 0, 10**12),
        ("NACH 0..600 s", -600, 0), ("NACH 600..3600 s", -3600, -600),
        ("NACH 1h..6h", -21600, -3600), ("NACH 24h..48h", -172800, -86400)]
rows = []
for tag, lo, hi in wins:
    for scope, sc in [("weit", base_all), ("weit_fremd", base_all[~base_all.eigene])]:
        sub = sc[(sc.lead > lo) & (sc.lead <= hi)]
        for m in MERKMALE:
            d = taf(coord.label.isin(gset(sub, m)), m)
            d.update(fenster=tag, scope=scope)
            rows.append(d)
ht = pd.DataFrame(rows)
ht.to_csv(os.path.join(PRUEF, "h_zeitplacebo.csv"), index=False)
for scope in ["weit", "weit_fremd"]:
    L(f"\nScope {scope} — RD (pp):")
    L(ht[ht.scope == scope].pivot(index="fenster", columns="merkmal", values="rd")
      .reindex([w[0] for w in wins]).round(1).to_string())
    L("n(gelesen):")
    L(ht[ht.scope == scope].pivot(index="fenster", columns="merkmal", values="n_gelesen")
      .reindex([w[0] for w in wins]).to_string())

# =========================================================== I Kalenderzeit
hdr("I  Kalenderzeit als Konfundierer")
coord["t0_dt"] = pd.to_datetime(coord.t0, unit="s", utc=True)
T16 = pd.Timestamp("2026-06-16T09:27:10Z")
coord["epoche"] = np.where(coord.t0_dt < T16, "vor_16-06", "ab_16-06")
L(coord.groupby("epoche").agg(n=("label", "size"),
                              ad_runde=("ad_runde", "mean"),
                              gelesen_runde=("gelesen_runde", "mean")).round(3).to_string())
L("\nAdoption und Lesestatus je Kalenderwoche des ersten Schreibversuchs (Rundenmarker):")
coord["woche"] = coord.t0_dt.dt.strftime("%G-W%V")
wk = coord.groupby("woche").agg(n=("label", "size"), ad=("ad_runde", "mean"),
                                gel=("gelesen_runde", "mean")).round(3)
L(wk.to_string())
wk.to_csv(os.path.join(PRUEF, "i_wochen.csv"))

L("\nRD geschichtet nach Epoche (Rundenmarker und alle Merkmale):")
rows = []
for m in MERKMALE:
    for ep in ["vor_16-06", "ab_16-06"]:
        for scope, sub in [("weit", pre), ("weit_fremd", pre[~pre.eigene])]:
            sel = coord[coord.epoche == ep]
            gg = sel.label.isin(gset(sub, m))
            a = sel["ad_" + m].astype(bool)
            n11, n10 = int((gg & a).sum()), int((gg & ~a).sum())
            n01, n00 = int((~gg & a).sum()), int((~gg & ~a).sum())
            r, lo, hi = rd_ci(n11, n11 + n10, n01, n01 + n00)
            rows.append(dict(merkmal=m, epoche=ep, scope=scope, n=len(sel),
                             n_gelesen=n11 + n10, rd=r, rd_lo=lo, rd_hi=hi))
it = pd.DataFrame(rows)
it.to_csv(os.path.join(PRUEF, "i_epochen.csv"), index=False)
L(it.round(1).to_string(index=False))

# =========================================================== J Regression
hdr("J  Kontrollierte Schaetzung (Vorbild tab:progress)")
# Kovariaten
wn = req[(req.kind == "write") & (req.name != "")]
nw = wn.groupby("name").size()
last = req[req.name != ""].groupby("name").ts.max()
coord["n_write"] = coord.label.map(nw).fillna(0)
coord["lebensdauer_s"] = (coord.label.map(last) - coord.t0).clip(lower=0).fillna(0)
coord["n_pre"] = coord.label.map(pre.groupby("name").size()).fillna(0)
coord["n_rev"] = coord.label.map(ix.groupby("label").size()).fillna(0)


def familie(pk):
    s = str(pk).split("~")[-1]
    mm = re.match(r"^(DataUSA|OECD|UNAIDS|WorldBank|Eurostat|Sector|Clothing|Federal|State|Grocery|Cashiers|Maids)", s)
    return mm.group(1) if mm else "sonstige"


coord["familie"] = coord.seite_rev.map(familie)
L("Aufgabenfamilien: " + str(coord.familie.value_counts().to_dict()))
L("Kovariaten-Medianwerte: " + str(coord[["n_write", "lebensdauer_s", "n_pre", "n_rev"]].median().to_dict()))

try:
    import statsmodels.formula.api as smf
    import statsmodels.api as sm
    coord["lg_npre"] = np.log1p(coord.n_pre)
    coord["lg_nwrite"] = np.log1p(coord.n_write)
    coord["lg_leben"] = np.log1p(coord.lebensdauer_s)
    coord["lg_nrev"] = np.log1p(coord.n_rev)
    coord["t0_tage"] = (coord.t0 - coord.t0.min()) / 86400.0
    rows = []
    for m in MERKMALE:
        for scope, sub in [("weit", pre), ("weit_fremd", pre[~pre.eigene]),
                           ("eng_fremd", pre[(~pre.eigene) & pre.kind.isin(READ_STRICT)])]:
            coord["G"] = coord.label.isin(gset(sub, m)).astype(int)
            coord["Y"] = coord["ad_" + m].astype(int)
            for tag, formel in [
                ("roh", "Y ~ G"),
                ("+lesemenge", "Y ~ G + lg_npre"),
                ("+zeit", "Y ~ G + lg_npre + t0_tage"),
                ("+volumen+leben", "Y ~ G + lg_npre + t0_tage + lg_nwrite + lg_nrev + lg_leben"),
                ("+familie", "Y ~ G + lg_npre + t0_tage + lg_nwrite + lg_nrev + lg_leben + C(familie)"),
                ("+eigene_exposition", "Y ~ G + lg_npre + t0_tage + lg_nwrite + lg_nrev + lg_leben + C(familie) + EXP"),
            ]:
                coord["EXP"] = coord["exp_" + m].astype(int)
                try:
                    r = smf.logit(formel, data=coord).fit(disp=0, maxiter=200)
                    b = r.params.get("G", np.nan); se = r.bse.get("G", np.nan)
                    rows.append(dict(merkmal=m, scope=scope, modell=tag, beta_G=b,
                                     lo=b - 1.96 * se, hi=b + 1.96 * se,
                                     or_G=math.exp(b) if b == b else np.nan,
                                     p=r.pvalues.get("G", np.nan)))
                except Exception as e:
                    rows.append(dict(merkmal=m, scope=scope, modell=tag, beta_G=np.nan,
                                     lo=np.nan, hi=np.nan, or_G=np.nan, p=np.nan))
    jt = pd.DataFrame(rows)
    jt.to_csv(os.path.join(PRUEF, "j_regression.csv"), index=False)
    for scope in ["weit", "weit_fremd", "eng_fremd"]:
        L(f"\nScope {scope} — Logit-Koeffizient von 'gelesen' (log-Odds, 95 %):")
        s = jt[jt.scope == scope]
        L(s.pivot(index="modell", columns="merkmal", values="beta_G").round(2).to_string())
        L("  p-Werte:")
        L(s.pivot(index="modell", columns="merkmal", values="p").round(4).to_string())
except ImportError:
    L("statsmodels fehlt — N/A_PENDING_REVIEWER")

# =========================================================== K die 249
hdr("K  Die 249 — mit der fehlenden Kontrollgruppe")
for m in ["runde", "cohort", "meldeformat", "sig_endzeile", "please_relay"]:
    ohne = coord[~coord["exp_" + m].astype(bool)].copy()
    ohne["gf"] = ohne.label.isin(gset(pre[~pre.eigene], m))
    ohne["ga"] = ohne.label.isin(gset(pre, m))
    a = ohne["ad_" + m].astype(bool)
    k1, n1 = int(ohne.gf[a].sum()), int(a.sum())
    k0, n0 = int(ohne.gf[~a].sum()), int((~a).sum())
    p1, l1, h1 = wilson(k1, n1); p0, l0, h0 = wilson(k0, n0)
    r, lo, hi = rd_ci(k1, n1, k0, n0)
    L(f"\n{m} ({HERKUNFT[m]}): Namen ohne Quelle auf der eigenen Seite = {len(ohne)}")
    L(f"   UEBERNEHMER   n={n1:4d}  las fremde Traegerseite: {k1:4d} ({p1:.1f} % [{l1:.1f}-{h1:.1f}])")
    L(f"   NICHT-Uebern. n={n0:4d}  las fremde Traegerseite: {k0:4d} ({p0:.1f} % [{l0:.1f}-{h0:.1f}])")
    L(f"   Differenz: {r:+.1f} pp [{lo:+.1f}, {hi:+.1f}]  <- das fehlt im Bericht")

L("\nfertig p20.")
coord.to_csv(os.path.join(PRUEF, "coord_p20.csv"), index=False)
LOG.close()
