#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
72_verkehr.py — Trennung von Flotten-, Hintergrund- und unklarem Verkehr,
                plus Pruefung, ob unbenannte Lesungen einzelnen Containern
                zugeordnet werden koennen.

Trennregel (belegt, nicht geraten):
  A) flotte_oder_benannt : /16 hat mindestens einen Request mit gesetztem NAME
                           ODER mindestens einen benannten Schreibversuch.
                           Anker: 99,9 % aller Schreibversuche tragen ein NAME;
                           191 von 191 /16-Netzen des publizierten Abzugs liegen
                           in dieser Menge (Kreuzvalidierung Log gegen Abzug).
  B) hintergrund_aprilbekannt : /16 war im April 2026 aktiv. Der April liegt
                           vollstaendig vor dem ersten Schwarm-Schreibvorgang
                           (2026-05-24) und enthaelt null benannte Requests;
                           er ist damit die Eichung der Grundlast aus Menschen
                           und Suchmaschinen-Crawlern.
  C) unklar_neu          : Rest.

Lauf: .venv/bin/python scripts/betreiberlog/72_verkehr.py
"""
from __future__ import annotations
import os, glob
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(os.path.dirname(HERE))
ART = os.path.join(BASE, "artefakte"); OUT = os.path.join(ART, "betreiberlog")
LOG = open(os.path.join(OUT, "_verkehr.log"), "w", encoding="utf-8")


def L(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); LOG.write(s + "\n")


req = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(os.path.join(OUT, "req_*.parquet")))],
                ignore_index=True)
for c in ("name", "kind", "page", "ip16"):
    req[c] = req[c].astype(str)
req["mon"] = pd.to_datetime(req.ts, unit="s", utc=True).dt.strftime("%Y-%m")
READ = {"browse", "raw", "editform", "bare", "archive_page"}

g = req.groupby("ip16").agg(n=("ts", "size"), napr=("mon", lambda s: (s == "2026-04").sum()),
                            nnamed=("name", lambda s: (s != "").sum()))
w = req[req.kind == "write"]
fleet = set(w[w["name"] != ""].ip16.unique())
g["fleet"] = g.index.isin(fleet)
g["cls"] = np.where(g.fleet | (g.nnamed > 0), "flotte_oder_benannt",
                    np.where(g.napr > 0, "hintergrund_aprilbekannt", "unklar_neu"))
g.to_csv(os.path.join(OUT, "ip16_klassen.csv"))
L("Netze und Requests je Klasse:")
L(g.groupby("cls").agg(n16=("n", "size"), requests=("n", "sum")).to_string())

cm = req.ip16.map(g.cls)
L("\nAlle Requests je Monat und Klasse:")
L(pd.crosstab(req.mon, cm).to_string())
r = req[req.kind.isin(READ)]
L("\nNur Lesezugriffe je Monat und Klasse:")
tl = pd.crosstab(r.mon, r.ip16.map(g.cls))
L(tl.to_string())
tl.to_csv(os.path.join(OUT, "verkehr_lesen_monat.csv"))

L("\nAnteil benannter Lesungen innerhalb der Flottenklasse je Monat:")
rf = r[r.ip16.map(g.cls) == "flotte_oder_benannt"]
tt = pd.crosstab(rf.mon, rf["name"] != "")
tt["anteil_benannt_%"] = (tt[True] / (tt[True] + tt[False]) * 100).round(1)
L(tt.to_string())
tt.to_csv(os.path.join(OUT, "verkehr_benanntanteil.csv"))

# Fingerabdruck der groessten Hintergrundnetze
L("\nGroesste Netze der Hintergrundklasse (Crawler-Signatur: breite Streuung, "
  "Einstiegsseite dominiert, null benannte Requests):")
bg = r[r.ip16.map(g.cls) == "hintergrund_aprilbekannt"]
for ip, n in bg.ip16.value_counts().head(8).items():
    s = bg[bg.ip16 == ip]
    L(f"  /16 {ip}: {n:7d} Lesungen, {s.page.nunique():5d} Seiten, "
      f"Top {list(s.page.value_counts().head(2).items())}, benannt {int((s['name']!='').sum())}")

# Zeitkopplungstest
L("\nZeitkopplung: unbenannte Lesungen aus Flottennetzen auf derselben Seite, "
  "gemessen relativ zum ersten Schreibversuch jedes benannten Namens.")
u = req[(req["name"] == "") & req.kind.isin({"browse", "bare", "raw", "editform"})
        & (req.page != "") & req.ip16.isin(fleet)]
L(f"  Grundmenge unbenannter Flottenlesungen: {len(u):,}")
key = {}
for p, t in zip(u.page.values, u.ts.values):
    key.setdefault(p, []).append(t)
for p in key:
    key[p] = np.sort(np.array(key[p]))
wn = w[w["name"] != ""].sort_values("ts").drop_duplicates(subset=["name"])


def cnt(p, a, b):
    arr = key.get(p)
    return 0 if arr is None else int(np.searchsorted(arr, b) - np.searchsorted(arr, a))


rows = []
for off, lab in [(0, "600 s davor"), (3600, "+1 h (Kontrolle)"),
                 (86400, "+24 h (Kontrolle)"), (-86400, "-24 h (Kontrolle)")]:
    v = np.array([cnt(p, t + off - 600, t + off) for p, t in zip(wn.page, wn.ts)])
    L(f"  {lab:20s} Mittel {v.mean():6.3f}  Anteil>0 {(v>0).mean()*100:5.1f} %")
    rows.append(dict(fenster=lab, mittel=v.mean(), anteil_groesser_null=(v > 0).mean() * 100))
pd.DataFrame(rows).to_csv(os.path.join(OUT, "verkehr_zeitkopplung.csv"), index=False)
L("  Deutung: das +1-h-Kontrollfenster ist genauso stark besetzt wie das Fenster vor dem "
  "Schreiben. Die unbenannten Flottenlesungen liegen also im Aktivitaetsfenster der Seite, "
  "nicht spezifisch vor dem Schreibvorgang; eine Zuordnung zu einzelnen Containern ist damit "
  "NICHT moeglich. Alle namensgebundenen Lesemasse sind deshalb Untergrenzen.")
LOG.close()
