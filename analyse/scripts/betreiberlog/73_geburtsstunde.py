#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
73_geburtsstunde.py — Leseverkehr auf den Koordinationsseiten des 16. Juni 2026.

Das Paper datiert den Beginn der Koordination auf 2026-06-16T09:27:10Z, Seite
DataUSAStateSequenceCollab2027 (main.tex Z. 292). Hier wird der LESEVERKEHR auf
dieser und den weiteren Koordinationsseiten aus dem Betreiberlog rekonstruiert.

Koordinationsseiten = Seiten mit mindestens einer Version im Fenster
09:26-10:47 des 16.06., deren Delta mindestens ein Koordinationsmerkmal traegt
(Merkmalsmasken aus artefakte/paper_exposition_index.parquet, erzeugt von
66_exposition.py Z. 119-127).

Lauf: .venv/bin/python scripts/betreiberlog/73_geburtsstunde.py
"""
from __future__ import annotations
import os, glob, json
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(os.path.dirname(HERE))
ART = os.path.join(BASE, "artefakte"); OUT = os.path.join(ART, "betreiberlog")
LOG = open(os.path.join(OUT, "_geburtsstunde.log"), "w", encoding="utf-8")


def L(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); LOG.write(s + "\n")


req = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(os.path.join(OUT, "req_*.parquet")))],
                ignore_index=True)
for c in ("name", "kind", "page", "ip16"):
    req[c] = req[c].astype(str)
req["t"] = pd.to_datetime(req.ts, unit="s", utc=True)
READ = {"browse", "raw", "editform", "bare", "archive_page"}
req["is_read"] = req.kind.isin(READ)

ix = pd.read_parquet(os.path.join(ART, "paper_exposition_index.parquet"))
ix["time"] = pd.to_datetime(ix["time"], utc=True)
EPOCH = pd.Timestamp("1970-01-01", tz="UTC")
ix["ts"] = ((ix.time - EPOCH).dt.total_seconds()).astype(np.int64)

T0 = pd.Timestamp("2026-06-16T09:27:10Z")
WA, WB = pd.Timestamp("2026-06-16T09:26:00Z"), pd.Timestamp("2026-06-16T10:47:00Z")
win = ix[(ix.time >= WA) & (ix.time <= WB) & ix.page_key.str.startswith("dse~")]
L(f"Versionen im Fenster {WA}..{WB}: {len(win)} auf {win.page_key.nunique()} Seiten")
koord = win[win.mask_delta > 0]
KS = [p[4:] for p in sorted(koord.page_key.unique())]
L(f"davon mit Koordinationsmerkmal im Delta: {len(koord)} Versionen auf {len(KS)} Seiten")
L("Koordinationsseiten: " + ", ".join(KS))

wn = req[(req.kind == "write") & (req["name"] != "")]
first_write = wn.groupby("name").ts.min()

rows = []
for p in KS:
    pk = "dse~" + p
    anl = int(ix[ix.page_key == pk].ts.min())
    sub = req[req.page == p]
    rd = sub[sub.is_read & (sub.ts >= anl)]
    rd24 = rd[rd.ts < anl + 86400]
    named = rd24[rd24["name"] != ""]
    first = int(rd24.ts.min()) - anl if len(rd24) else None
    leser = set(named["name"].unique())
    # Leser, deren ERSTER Schreibversuch NACH ihrem ersten Lesen dieser Seite liegt
    danach = 0
    for n, g in named.groupby("name"):
        fw = first_write.get(n)
        if fw is not None and fw > int(g.ts.min()):
            danach += 1
    rows.append(dict(seite=p, angelegt=pd.Timestamp(anl, unit="s", tz="UTC"),
                     versionen_gesamt=int((ix.page_key == pk).sum()),
                     lesungen_24h=len(rd24), benannte_lesungen=len(named),
                     benannte_leser=len(leser), unbenannte_lesungen=int((rd24["name"] == "").sum()),
                     erste_lesung_s=first,
                     leser_die_danach_schrieben=danach))
kt = pd.DataFrame(rows).sort_values("angelegt")
L("\n" + kt.to_string(index=False))
kt.to_csv(os.path.join(OUT, "geburtsstunde_koordinationsseiten.csv"), index=False)

P0 = "DataUSAStateSequenceCollab2027"
anl0 = int(ix[ix.page_key == "dse~" + P0].ts.min())
L(f"\n{P0} angelegt {pd.Timestamp(anl0, unit='s', tz='UTC')}")
sp = req[(req.page == P0)].sort_values("ts")
L(f"Requests auf dieser Seite insgesamt: {len(sp)}; Lesezugriffe: {int(sp.is_read.sum())}")
for h in (0.25, 0.5, 1, 2, 4, 8, 12, 24, 72):
    s = sp[(sp.ts >= anl0) & (sp.ts < anl0 + int(h * 3600)) & sp.is_read]
    L(f"  +{h:5.2f} h: {len(s):5d} Lesungen, {s[s['name']!='']['name'].nunique():3d} benannte Leser, "
      f"{int((s['name']=='').sum()):5d} unbenannte Lesungen")
L("\nErste 40 Requests auf dieser Seite ab Anlage:")
L(sp[sp.ts >= anl0][["t", "ip", "name", "kind"]].head(40).to_string(index=False))
sp.to_csv(os.path.join(OUT, "geburtsstunde_erstseite_alle.csv"), index=False)

# Wer las die Seite am 16.06., und was tat er danach?
d16 = sp[(sp.ts >= anl0) & (sp.ts < anl0 + 86400) & sp.is_read & (sp["name"] != "")]
L(f"\nBenannte Leser der Erstseite in 24 h: {d16['name'].nunique()}")
erst = d16.groupby("name").ts.min()
fw = erst.index.map(lambda n: first_write.get(n, np.nan))
df = pd.DataFrame({"erstes_lesen": erst.values, "erster_schreibversuch": fw}, index=erst.index)
df["las_vor_erstem_schreiben"] = df.erster_schreibversuch > df.erstes_lesen
L(f"  davon mit erstem Schreibversuch NACH diesem Lesen: {int(df.las_vor_erstem_schreiben.sum())}")
L(f"  davon hatten vorher schon geschrieben: {int((~df.las_vor_erstem_schreiben).sum())}")
df.to_csv(os.path.join(OUT, "geburtsstunde_erstseite_leser.csv"))
json.dump({"koordinationsseiten": KS, "erstseite": P0,
           "anlage": str(pd.Timestamp(anl0, unit="s", tz="UTC"))},
          open(os.path.join(OUT, "geburtsstunde.json"), "w"), indent=1)
LOG.close()
