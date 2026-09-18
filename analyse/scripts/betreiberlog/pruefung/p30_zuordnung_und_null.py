#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
p30_zuordnung_und_null.py — Teil 3 der Gegenpruefung.

  L  Die Rotationsbehauptung des Berichts nachgerechnet.
     lese-spalte.md:378-379 behauptet "die Flotte rotiert die Egress-IP pro Request
     — 672 753 verschiedene volle IPs bei einem Median von 1 Request je IP".
     Kein Skript im Repo rechnet das. Hier wird es nachgerechnet.
  M  Alternativzuordnung: unbenannte Lesungen ueber die volle IP an einen Namen
     binden (Fenster 60 s / 300 s, nur eindeutige Faelle), Kernmessung wiederholen.
  N  Permutations-Nullverteilung: Lesezeitpunkte behalten, gelesene Seiten aus dem
     Seitenpool derselben Stunde ziehen. Antwortet auf "wie oft trifft ein zufaellig
     gewaehlter Lesezugriff eine Traegerseite, einfach weil es so viele gab".

Lauf: .venv/bin/python scripts/betreiberlog/pruefung/p30_zuordnung_und_null.py
"""
from __future__ import annotations
import os, sys, math
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p00_lib import (READ_CONTENT, READ_STRICT, MERKMALE, HERKUNFT, hasm, rd_ci,
                     lade, seitenzustand, mask_at_factory, vier_felder, PRUEF)

LOG = open(os.path.join(PRUEF, "_p30.log"), "w", encoding="utf-8")


def L(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True); LOG.write(s + "\n")


def hdr(t):
    L("\n" + "=" * 88 + "\n" + t + "\n" + "=" * 88)


RNG = np.random.default_rng(20260917)

hdr("0  Laden")
req, ix, coord = lade()
coord["label"] = coord.label.astype(str)
PSTATE = seitenzustand(ix)
mask_at = mask_at_factory(PSTATE)
COORDSET = set(coord.label)
req["mon"] = pd.to_datetime(req.ts, unit="s", utc=True).dt.strftime("%Y-%m")
w = req[(req.kind == "write") & (req.name != "")]
FLEET16 = set(w.ip16.unique())
L(f"Flotten-/16-Netze: {len(FLEET16)}")

# =========================================================== L Rotation
hdr("L  Die Rotationsbehauptung nachgerechnet")
fl = req[req.ip16.isin(FLEET16)]
junfl = fl[(fl.mon == "2026-06") & fl.kind.isin(READ_CONTENT)]
unj = junfl[junfl.name == ""]
vc = unj.ip.value_counts()
L(f"Juni, Lesezugriffe aus Flottennetzen: {len(junfl):,}, davon unbenannt {len(unj):,} "
  f"({len(unj)/len(junfl)*100:.1f} %)")
L(f"BEHAUPTUNG (lese-spalte.md:378-379): 672 753 verschiedene volle IPs, Median 1 Request je IP.")
L(f"GEMESSEN: {unj.ip.nunique():,} verschiedene volle IPs; Median {vc.median():.0f} Requests je IP, "
  f"p10 {vc.quantile(.1):.0f}, p90 {vc.quantile(.9):.0f}, max {vc.max():,}")
L(f"Alle Flotten-Requests im ganzen Log: {len(fl):,} auf {fl.ip.nunique():,} vollen IPs, "
  f"Median {fl.ip.value_counts().median():.0f} Requests je IP")
nm = fl[fl.name != ""].copy()
nm["b60"] = nm.ts // 60
g60 = nm.groupby(["ip", "b60"]).name.nunique()
L(f"Eindeutigkeit: (volle IP x 60-s-Fenster) traegt genau einen Namen in "
  f"{(g60==1).mean()*100:.1f} % von {len(g60):,} Faellen (Mittel {g60.mean():.2f} Namen).")
pd.DataFrame(dict(kennzahl=["ips_unbenannt_juni", "median_req_je_ip", "ips_gesamt_flotte",
                            "anteil_ip60s_eindeutig_%"],
                  wert=[unj.ip.nunique(), float(vc.median()), fl.ip.nunique(),
                        float((g60 == 1).mean() * 100)])).to_csv(
    os.path.join(PRUEF, "l_rotation.csv"), index=False)

# =========================================================== M Alternativzuordnung
hdr("M  Alternativzuordnung unbenannter Lesungen ueber die volle IP")
anchors = nm[["ip", "ts", "name"]].sort_values(["ip", "ts"])
ip_arr = {}
for ipv, g in anchors.groupby("ip", sort=False):
    ip_arr[ipv] = (g.ts.values.astype(np.int64), g.name.values.astype(object))

unread = fl[(fl.name == "") & fl.kind.isin(READ_CONTENT) & (fl.page != "")][["ip", "ts", "kind", "page"]]
L(f"Unbenannte Flottenlesungen gesamt: {len(unread):,}")


def zuordnen(W):
    out_name = np.empty(len(unread), dtype=object); out_name[:] = None
    ips = unread.ip.values; tss = unread.ts.values.astype(np.int64)
    for i in range(len(unread)):
        e = ip_arr.get(ips[i])
        if e is None:
            continue
        t, nmv = e
        lo = np.searchsorted(t, tss[i] - W, "left"); hi = np.searchsorted(t, tss[i] + W, "right")
        if hi <= lo:
            continue
        cand = set(nmv[lo:hi])
        if len(cand) == 1:
            out_name[i] = next(iter(cand))
    return out_name


for W, tag in [(60, "60s"), (300, "300s")]:
    nmv = zuordnen(W)
    ok = pd.notna(pd.Series(nmv))
    L(f"\nFenster +/-{W} s: eindeutig zugeordnet {int(ok.sum()):,} von {len(unread):,} "
      f"({ok.mean()*100:.1f} %)")
    add = unread[ok.values].copy(); add["name"] = pd.Series(nmv)[ok].values
    add = add[add.name.isin(COORDSET)]
    L(f"  davon auf coordpop-Namen: {len(add):,}")
    if not len(add):
        continue
    # zusammenfuehren mit den benannten Lesungen
    named = req[req.name.isin(COORDSET) & req.kind.isin(READ_CONTENT)][["name", "ts", "kind", "page"]]
    allr = pd.concat([named, add[["name", "ts", "kind", "page"]]], ignore_index=True)
    t0map = dict(zip(coord.label, coord.t0.astype("int64")))
    allr["t0"] = allr.name.map(t0map)
    allr = allr[allr.t0.notna()]; allr["t0"] = allr.t0.astype("int64")
    allr = allr[allr.ts < allr.t0]
    allr["mask"] = [mask_at(p, int(t)) for p, t in zip(allr.page, allr.ts)]
    allr = allr[allr["mask"] > 0]
    L(f"  Pre-t0-Lesezugriffe nach Alternativzuordnung: {len(allr):,} "
      f"(benannt allein waren es 21 893)")
    rows = []
    for m in MERKMALE:
        hit = set(allr.loc[[hasm(mm, m) for mm in allr["mask"]], "name"].unique())
        coord["_g"] = coord.label.isin(hit)
        d = vier_felder(coord, "_g", "ad_" + m); d.update(merkmal=m, variante=f"alt_{tag}_weit")
        rows.append(d)
        sub = allr[allr.kind.isin(READ_STRICT)]
        hit = set(sub.loc[[hasm(mm, m) for mm in sub["mask"]], "name"].unique())
        coord["_g"] = coord.label.isin(hit)
        d = vier_felder(coord, "_g", "ad_" + m); d.update(merkmal=m, variante=f"alt_{tag}_eng")
        rows.append(d)
    mt = pd.DataFrame(rows)
    mt.to_csv(os.path.join(PRUEF, f"m_altzuordnung_{tag}.csv"), index=False)
    L(mt.pivot(index="variante", columns="merkmal", values="rd").round(1).to_string())
    L("n(gelesen):")
    L(mt.pivot(index="variante", columns="merkmal", values="n_gelesen").to_string())

# =========================================================== N Permutation
hdr("N  Permutations-Nullverteilung der Traegertreffer")
rl = pd.read_parquet(os.path.join(PRUEF, "lesezugriffe_coordpop.parquet"))
pre = rl[(rl.lead > 0) & (rl["mask"] > 0)].copy()
L(f"Grundmenge: {len(pre):,} Pre-t0-Lesezugriffe von {pre.name.nunique():,} Namen")

# Seitenpool je Stunde: welche dse-Seiten wurden in dieser Stunde ueberhaupt gelesen
readall = req[req.kind.isin(READ_CONTENT) & (req.page != "")][["ts", "page"]].copy()
readall["h"] = readall.ts // 3600
pool = {}
for h, g in readall.groupby("h"):
    pages = g.page.values
    pool[h] = pages
L(f"Stundenpools aufgebaut: {len(pool):,} Stunden")

pre["h"] = pre.ts // 3600
obs = {m: int(pre.loc[pre["c_" + m], "name"].nunique()) for m in MERKMALE}
obs_rd = {}
for m in MERKMALE:
    coord["_g"] = coord.label.isin(set(pre.loc[pre["c_" + m], "name"].unique()))
    obs_rd[m] = vier_felder(coord, "_g", "ad_" + m)["rd"]

NPERM = 200
names = pre.name.values
hs = pre.h.values
tss = pre.ts.values.astype(np.int64)
null_hits = {m: [] for m in MERKMALE}
null_rd = {m: [] for m in MERKMALE}
hkeys = np.array(sorted(pool.keys()))
for it in range(NPERM):
    drawn = np.empty(len(pre), dtype=object)
    for h in np.unique(hs):
        idx = np.where(hs == h)[0]
        p = pool.get(h)
        if p is None or len(p) == 0:
            j = np.searchsorted(hkeys, h); j = min(max(j, 0), len(hkeys) - 1)
            p = pool[hkeys[j]]
        drawn[idx] = p[RNG.integers(0, len(p), size=len(idx))]
    masks = np.array([mask_at(pg, int(t)) for pg, t in zip(drawn, tss)])
    for m in MERKMALE:
        hit = np.array([(mm > 0) and hasm(mm, m) for mm in masks])
        s = set(names[hit])
        null_hits[m].append(len(s))
        coord["_g"] = coord.label.isin(s)
        null_rd[m].append(vier_felder(coord, "_g", "ad_" + m)["rd"])
    if (it + 1) % 50 == 0:
        L(f"  {it+1}/{NPERM} Permutationen")

rows = []
for m in MERKMALE:
    a = np.array(null_hits[m], dtype=float); b = np.array(null_rd[m], dtype=float)
    rows.append(dict(merkmal=m, herkunft=HERKUNFT[m],
                     beobachtet_n_leser=obs[m], null_n_leser_mittel=a.mean(),
                     null_n_leser_p2_5=np.percentile(a, 2.5), null_n_leser_p97_5=np.percentile(a, 97.5),
                     beobachtet_rd=obs_rd[m], null_rd_mittel=np.nanmean(b),
                     null_rd_p2_5=np.nanpercentile(b, 2.5), null_rd_p97_5=np.nanpercentile(b, 97.5),
                     p_einseitig=float((b >= obs_rd[m]).mean())))
nt = pd.DataFrame(rows)
nt.to_csv(os.path.join(PRUEF, "n_permutation.csv"), index=False)
L("\nBeobachtet gegen Permutations-Null (Seiten zufaellig aus dem Stundenpool gezogen):")
L(nt.round(2).to_string(index=False))
L("\nfertig p30.")
LOG.close()
