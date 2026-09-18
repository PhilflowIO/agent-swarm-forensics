#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
p40_tautologie.py — Teil 4: der harte Tautologie-Nachweis und feine Zeitkontrolle.

  O  Wieviel des Trefferbelegs ist der Abruf des Editformulars GENAU DER SEITE,
     auf die der Name Sekunden spaeter seine erste Version schrieb? Das ist
     wortgleich die Expositionsvariable des Papers (mask_page_before), nur ueber
     das Log gemessen. Ein Effekt, der daran haengt, ist keine neue Messung.
  P  Feine Kalenderzeit: alle 1140 t0 liegen in einer einzigen Woche. Schichtung
     in 6-h-Buckets statt Epochen.
  Q  Merkmalsunspezifische Kontrolle: Lesen einer Seite, die IRGENDEIN
     Koordinationsmerkmal trug, gegen Adoption des Rundenmarkers.

Lauf: .venv/bin/python scripts/betreiberlog/pruefung/p40_tautologie.py
"""
from __future__ import annotations
import os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p00_lib import (READ_CONTENT, READ_STRICT, MERKMALE, HERKUNFT, hasm, rd_ci, wilson,
                     lade, vier_felder, PRUEF)

LOG = open(os.path.join(PRUEF, "_p40.log"), "w", encoding="utf-8")


def L(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True); LOG.write(s + "\n")


def hdr(t):
    L("\n" + "=" * 88 + "\n" + t + "\n" + "=" * 88)


hdr("0  Laden")
req, ix, coord = lade()
coord["label"] = coord.label.astype(str)
coord["erstseite"] = coord.seite_rev.astype(str).str.replace("^dse~", "", regex=True)
rl = pd.read_parquet(os.path.join(PRUEF, "lesezugriffe_coordpop.parquet"))
pre = rl[(rl.lead > 0) & (rl["mask"] > 0)].copy()
es = dict(zip(coord.label, coord.erstseite))
pre["ist_erstseite"] = [p == es.get(n, "\x00") for n, p in zip(pre.name, pre.page)]
L(f"Pre-t0-Lesezugriffe {len(pre):,}; davon auf der eigenen Erstseite "
  f"{int(pre.ist_erstseite.sum()):,} ({pre.ist_erstseite.mean()*100:.1f} %)")

# =========================================================== O Tautologie
hdr("O  Der Trefferbeleg ist ueberwiegend der Griff zum eigenen Editformular")
rows = []
for m in MERKMALE:
    tr = pre[pre["c_" + m]]
    alle = set(tr.name.unique())
    erst = set(tr.loc[tr.ist_erstseite, "name"].unique())
    erst_edit = set(tr.loc[tr.ist_erstseite & (tr.kind == "editform"), "name"].unique())
    erst_edit_60 = set(tr.loc[tr.ist_erstseite & (tr.kind == "editform") & (tr.lead <= 60), "name"].unique())
    nur_erst = alle - set(tr.loc[~tr.ist_erstseite, "name"].unique())
    rows.append(dict(merkmal=m, herkunft=HERKUNFT[m], n_traeger_leser=len(alle),
                     mit_erstseite=len(erst), mit_erstseite_editform=len(erst_edit),
                     mit_erstseite_editform_unter60s=len(erst_edit_60),
                     NUR_erstseite=len(nur_erst),
                     anteil_nur_erstseite=len(nur_erst) / max(len(alle), 1) * 100))
ot = pd.DataFrame(rows)
ot.to_csv(os.path.join(PRUEF, "o_tautologie.csv"), index=False)
L(ot.round(1).to_string(index=False))

L("\nUebereinstimmung 'las die eigene Erstseite mit Merkmal' mit exp_<merkmal> des Papers:")
rows = []
for m in MERKMALE:
    tr = pre[pre["c_" + m] & pre.ist_erstseite]
    g = coord.label.isin(set(tr.name.unique()))
    e = coord["exp_" + m].astype(bool)
    rows.append(dict(merkmal=m, n_log=int(g.sum()), n_exp_paper=int(e.sum()),
                     uebereinstimmung=int((g == e).sum()) / len(coord) * 100,
                     g_und_e=int((g & e).sum()), g_ohne_e=int((g & ~e).sum()),
                     e_ohne_g=int((~g & e).sum())))
L(pd.DataFrame(rows).round(1).to_string(index=False))

L("\nRD, wenn die eigene Erstseite als Lesequelle AUSGESCHLOSSEN wird:")
rows = []
for m in MERKMALE:
    for tag, sub in [("alle_quellen", pre),
                     ("ohne_erstseite", pre[~pre.ist_erstseite]),
                     ("ohne_erstseite_eng", pre[(~pre.ist_erstseite) & pre.kind.isin(READ_STRICT)]),
                     ("NUR_erstseite", pre[pre.ist_erstseite])]:
        coord["_g"] = coord.label.isin(set(sub.loc[sub["c_" + m], "name"].unique()))
        d = vier_felder(coord, "_g", "ad_" + m); d.update(merkmal=m, variante=tag)
        rows.append(d)
oz = pd.DataFrame(rows)
oz.to_csv(os.path.join(PRUEF, "o_ohne_erstseite.csv"), index=False)
L(oz.pivot(index="variante", columns="merkmal", values="rd").round(1).to_string())
L("95-%-Untergrenze:")
L(oz.pivot(index="variante", columns="merkmal", values="rd_lo").round(1).to_string())
L("95-%-Obergrenze:")
L(oz.pivot(index="variante", columns="merkmal", values="rd_hi").round(1).to_string())
L("n(gelesen):")
L(oz.pivot(index="variante", columns="merkmal", values="n_gelesen").to_string())

# =========================================================== P Feine Zeit
hdr("P  Kalenderzeit fein: alle t0 liegen in einer Woche")
coord["t0_dt"] = pd.to_datetime(coord.t0, unit="s", utc=True)
L("Spannweite t0: " + str(coord.t0_dt.min()) + " .. " + str(coord.t0_dt.max()))
coord["bucket"] = coord.t0_dt.dt.floor("6h").astype(str)
bc = coord.groupby("bucket").agg(n=("label", "size"), ad_runde=("ad_runde", "mean"),
                                 gel=("gelesen_runde", "mean")).round(3)
L(bc.to_string())
bc.to_csv(os.path.join(PRUEF, "p_zeitbuckets.csv"))

L("\nMantel-Haenszel-artig: RD je 6-h-Bucket (nur Buckets mit n>=40), Rundenmarker:")
for tag, sub in [("weit", pre), ("weit_fremd", pre[~pre.ist_erstseite]),
                 ("eng_fremd", pre[(~pre.ist_erstseite) & pre.kind.isin(READ_STRICT)])]:
    hit = set(sub.loc[sub["c_runde"], "name"].unique())
    rows = []
    num = den = 0.0
    for b, g in coord.groupby("bucket"):
        if len(g) < 40:
            continue
        gg = g.label.isin(hit); a = g.ad_runde.astype(bool)
        n1, n0 = int(gg.sum()), int((~gg).sum())
        if n1 == 0 or n0 == 0:
            continue
        p1 = (gg & a).sum() / n1; p0 = ((~gg) & a).sum() / n0
        wgt = n1 * n0 / (n1 + n0)
        num += wgt * (p1 - p0); den += wgt
        rows.append(dict(bucket=b, n=len(g), n_gelesen=n1, rd=(p1 - p0) * 100))
    L(f"  {tag}: gepoolte RD ueber Zeitschichten = {num/den*100:+.1f} pp "
      f"(ungeschichtet {vier_felder(coord.assign(_g=coord.label.isin(hit)), '_g', 'ad_runde')['rd']:+.1f} pp)")
    for r in rows:
        L(f"      {r['bucket']}  n={r['n']:4d}  gelesen={r['n_gelesen']:4d}  RD={r['rd']:+6.1f} pp")

# =========================================================== Q unspezifisch
hdr("Q  Merkmalsunspezifische Kontrolle")
pre["c_irgendein"] = pre[["c_" + m for m in MERKMALE]].any(axis=1)
for tag, sub in [("weit", pre), ("ohne_erstseite", pre[~pre.ist_erstseite])]:
    hit = set(sub.loc[sub.c_irgendein, "name"].unique())
    coord["_g"] = coord.label.isin(hit)
    L(f"\nScope {tag}: 'las eine Seite mit IRGENDEINEM Koordinationsmerkmal' "
      f"n={int(coord['_g'].sum())}")
    for m in MERKMALE:
        d = vier_felder(coord, "_g", "ad_" + m)
        L(f"   -> Adoption {m:14s} ({HERKUNFT[m]:11s}) RD {d['rd']:+6.1f} pp "
          f"[{d['rd_lo']:+.1f}, {d['rd_hi']:+.1f}]")

L("\nfertig p40.")
LOG.close()
