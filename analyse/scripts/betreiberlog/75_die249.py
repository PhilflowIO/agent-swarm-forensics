#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
75_die249.py — Der verraeterische Fall des Papers, am Log geprueft.

main.tex Z. 325-328 (tab:exposure): 249 von 664 Uebernehmern des Rundenmarkers
(37,5 %) benutzten ihn, obwohl er auf ihrer Seite nirgends stand. Frage: haben
diese Namen anderswo eine Seite gelesen, die ihn trug — und wann?

Lauf: .venv/bin/python scripts/betreiberlog/75_die249.py
"""
from __future__ import annotations
import os, glob, math
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(os.path.dirname(HERE))
ART = os.path.join(BASE, "artefakte"); OUT = os.path.join(ART, "betreiberlog")
LOG = open(os.path.join(OUT, "_die249.log"), "w", encoding="utf-8")


def L(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); LOG.write(s + "\n")


def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p * 100, (c - h) * 100, (c + h) * 100


C = pd.read_csv(os.path.join(OUT, "kernmessung_namen.csv"))
req = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(os.path.join(OUT, "req_*.parquet")))],
                ignore_index=True)
for c in ("name", "kind", "page"):
    req[c] = req[c].astype(str)
READ = {"browse", "raw", "editform", "bare", "archive_page"}

ix = pd.read_parquet(os.path.join(ART, "paper_exposition_index.parquet"))
ix["time"] = pd.to_datetime(ix["time"], utc=True)
EPOCH = pd.Timestamp("1970-01-01", tz="UTC")
ixd = ix[ix.page_key.str.startswith("dse~")].sort_values(["page_key", "time"], kind="mergesort")
PST = {pk[4:]: (((g.time - EPOCH).dt.total_seconds()).values.astype(np.int64),
                g.mask_body.values.astype(np.int64)) for pk, g in ixd.groupby("page_key", sort=False)}
BASIS = ["sig_endzeile", "please_relay", "cohort", "runde", "state_conf", "uhrenpaar", "zeitstempel"]
BIT = {k: 1 << i for i, k in enumerate(BASIS)}


def mask_at(page, ts):
    e = PST.get(page)
    if e is None:
        return -1
    t, mm = e
    j = np.searchsorted(t, ts, side="right") - 1
    return int(mm[j]) if j >= 0 else 0


sel = C[C.ad_runde & ~C.exp_runde].copy()
L(f"Uebernehmer des Rundenmarkers ohne Quelle auf der eigenen Seite: {len(sel)} "
  f"(Paper: 249 von 664, tab:exposure)")
rl = req[(req["name"].isin(set(sel.label))) & req.kind.isin(READ) & (req.page != "")].copy()
t0 = dict(zip(sel.label, sel.t0))
rl["t0"] = rl["name"].map(t0)
rl = rl[rl.ts < rl.t0].copy()
rl["mask"] = [mask_at(p, int(t)) for p, t in zip(rl.page, rl.ts)]
rl["traeger"] = (rl["mask"] > 0) & ((rl["mask"] & BIT["runde"]) > 0)
rl["vorlauf_s"] = rl.t0 - rl.ts

leser = set(rl["name"].unique())
traeger = set(rl[rl.traeger]["name"].unique())
k, n = len(traeger), len(sel)
p, lo, hi = wilson(k, n)
L(f"  las ueberhaupt eine Seite vor dem ersten Schreibversuch: {len(leser)} "
  f"({len(leser)/n*100:.1f} %)")
L(f"  las eine Seite, die den Rundenmarker in diesem Moment trug: {k} "
  f"({p:.1f} %, 95 % {lo:.1f}-{hi:.1f})")
L(f"  las, aber nie eine Traegerseite: {len(leser - traeger)} ({(len(leser)-k)/n*100:.1f} %)")
L(f"  las gar nichts: {n - len(leser)} ({(n-len(leser))/n*100:.1f} %)")
L("\n  -> Obergrenze fuer 'aus dem gemeinsamen Prompt mitgebracht': "
  f"{n-k} von {n} ({(n-k)/n*100:.1f} %). Untergrenze fuer 'ueber das Wiki uebertragen': "
  f"{k} von {n} ({p:.1f} %). Die Zuordnung ist einseitig: unbenannte Lesungen sind nicht "
  "zuordenbar (72_verkehr.py), gemessenes Lesen kann also nur unterschaetzt sein.")

tr = rl[rl.traeger]
if len(tr):
    L("\n  Vorlauf zwischen Traegerlesung und erstem Schreibversuch (s): "
      + str(tr.groupby("name").vorlauf_s.min().quantile([.1, .25, .5, .75, .9]).round(0).to_dict()))
    L("  meistgelesene Traegerseiten: " + str(tr.page.value_counts().head(10).to_dict()))
    L("  Lesearten: " + str(tr.kind.value_counts().to_dict()))
rl.to_csv(os.path.join(OUT, "die249_lesezugriffe.csv"), index=False)
sel["las_traegerseite_runde"] = sel.label.isin(traeger)
sel.to_csv(os.path.join(OUT, "die249_namen.csv"), index=False)
LOG.close()

# ---- Vergleich erfunden gegen mitgebracht fuer die 'ohne Quelle auf der eigenen Seite'-Gruppe
LOG = open(os.path.join(OUT, "_die249.log"), "a", encoding="utf-8")
L("\nAlle fuenf Merkmale, Gruppe 'uebernommen ohne Quelle auf der eigenen Seite':")
rows = []
for m, h in [("runde", "invented"), ("cohort", "invented"), ("meldeformat", "invented"),
             ("sig_endzeile", "brought"), ("please_relay", "brought")]:
    s = C[C["ad_" + m] & ~C["exp_" + m]]
    k = int(s["gelesen_" + m].sum()); n = len(s)
    p, lo, hi = wilson(k, n)
    rows.append(dict(merkmal=m, herkunft=h, n_ohne_quelle=n, las_traegerseite=k,
                     pct=p, ci_lo=lo, ci_hi=hi))
    L(f"  {m:13s} {h:8s} n={n:4d}  las anderswo Traegerseite {k:3d} ({p:.1f} %, 95 % {lo:.1f}-{hi:.1f})")
pd.DataFrame(rows).to_csv(os.path.join(OUT, "ohne_quelle_alle_merkmale.csv"), index=False)
LOG.close()
