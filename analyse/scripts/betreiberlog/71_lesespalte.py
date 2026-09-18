#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
71_lesespalte.py — Die fehlende Lese-Spalte, gemessen statt rekonstruiert.

Grundlage: die Betreiber-Requestlogs (Pass 1 in 70_parse.py) und der publizierte
Abzug (data/*.jsonl) samt der bestehenden Pipeline-Definitionen:

  * Koordinations-Population (1140 Namen): artefakte/paper_lernkurve_q2_inhaltlicher_lesebeweis.csv,
    Spalte `coordpop` — erzeugt von 41_lernkurve.py, uebernommen in 66_exposition.py Z. 104-105
    (dort: "Koordinations-Population (coordpop, wie Fig. 3 / 65_adoption_robust.py Z. 227)").
  * Merkmalsregexe und Merkmalsmasken: artefakte/paper_exposition_index.parquet,
    erzeugt von 66_exposition.py Z. 119-127 (dort uebernommen aus 41_lernkurve.py Z. 14-31).
    Wir erfinden KEINE neuen Muster.
  * Adoption in der Erstversion: Spalten ad_<merkmal> derselben Datei.

Teile:
  1  Grundinventar der Lesezugriffe (Monat, Wiki, benannt/unbenannt, Seitenklasse,
     Verkehrsklasse).
  2  Kernmessung: Vier-Felder-Tafel gelesen x uebernommen fuer die 1140 Namen,
     analog tab:exposure, mit Wilson-Intervallen und Risikodifferenz-Intervall.
  3  Die 249 Uebernehmer des Rundenmarkers ohne Quelle auf der eigenen Seite:
     haben sie anderswo gelesen, was und wann?
  4  Geburtsstunde der Koordination: Leseverkehr auf den zwoelf Koordinationsseiten.

Lauf:  .venv/bin/python scripts/betreiberlog/71_lesespalte.py
Ausgaben: artefakte/betreiberlog/*.csv|json, Log artefakte/betreiberlog/_lesespalte.log
"""
from __future__ import annotations
import os, json, glob, math, collections
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(os.path.dirname(HERE))
ART = os.path.join(BASE, "artefakte")
OUT = os.path.join(ART, "betreiberlog")
DATA = os.path.join(BASE, "data")
os.makedirs(OUT, exist_ok=True)
LOG = open(os.path.join(OUT, "_lesespalte.log"), "w", encoding="utf-8")


def L(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True); LOG.write(s + "\n")


def hdr(t):
    L("\n" + "=" * 88 + "\n" + t + "\n" + "=" * 88)


READ_CONTENT = {"browse", "raw", "editform", "bare", "archive_page"}
READ_STRICT = {"browse", "raw"}          # exakt die im Auftrag genannte Definition
FEEDKINDS = {"rc", "other:rss", "other:recentchanges"}
FEEDPAGES = {"RecentChanges", "AktuelleAenderungen"}

# =========================================================== 0 Laden
hdr("0  Laden")
req = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(os.path.join(OUT, "req_*.parquet")))],
                ignore_index=True)
for c in ("name", "kind", "page", "wiki", "script", "query", "ip", "ip16"):
    req[c] = req[c].astype(str)
req["t"] = pd.to_datetime(req.ts, unit="s", utc=True)
L(f"Requests gesamt {len(req):,}  Zeitraum {req.t.min()} .. {req.t.max()}")
L("Wikis im Log:", dict(req.wiki.value_counts().head(5)))
L("Arten:", dict(req.kind.value_counts().head(14)))

ix = pd.read_parquet(os.path.join(ART, "paper_exposition_index.parquet"))
ix["time"] = pd.to_datetime(ix["time"], utc=True)
L(f"Expositionsindex {len(ix):,} Versionen, {ix.page_key.nunique():,} Seiten, {ix.label.nunique():,} Namen")

lb = pd.read_csv(os.path.join(ART, "paper_lernkurve_q2_inhaltlicher_lesebeweis.csv"))
COORD = lb[lb.coordpop].copy()
COORD["erste_version"] = pd.to_datetime(COORD.erste_version, utc=True)
L(f"Koordinations-Population {len(COORD)} Namen (Quelle: paper_lernkurve_q2_inhaltlicher_lesebeweis.csv, coordpop)")

pages = pd.read_json(os.path.join(DATA, "pages.jsonl"), lines=True)
rev = pd.read_json(os.path.join(DATA, "revisions.jsonl"), lines=True,
                   dtype={"ip16": str})
rev["time"] = pd.to_datetime(rev.time, utc=True)

MERKMALE = ["runde", "cohort", "meldeformat", "sig_endzeile", "please_relay"]
HERKUNFT = {"runde": "invented", "cohort": "invented", "meldeformat": "invented",
            "sig_endzeile": "brought", "please_relay": "brought"}

# =========================================================== 1 Grundinventar
hdr("1  Grundinventar der Lesezugriffe")
req["mon"] = req.t.dt.strftime("%Y-%m")
req["is_read"] = req.kind.isin(READ_CONTENT)
req["is_read_strict"] = req.kind.isin(READ_STRICT)
req["is_feed"] = req.kind.isin(FEEDKINDS) | (req.kind.isin(READ_CONTENT) & req.page.isin(FEEDPAGES))
req["named"] = req.name != ""

L("Lesezugriffe je Monat (weite Definition = browse|raw|editform|bare|archive_page):")
t1 = req.groupby("mon").agg(requests=("ts", "size"), lesen_weit=("is_read", "sum"),
                            lesen_eng=("is_read_strict", "sum"), feed=("is_feed", "sum"),
                            schreiben=("kind", lambda s: (s == "write").sum()),
                            suchen=("kind", lambda s: (s == "search").sum()))
L(t1.to_string())
t1.to_csv(os.path.join(OUT, "inventar_monat.csv"))

rd = req[req.is_read].copy()
L(f"\nLesezugriffe gesamt (weit) {len(rd):,}, davon mit gesetztem NAME {int(rd['named'].sum()):,} "
  f"({rd['named'].mean()*100:.1f} %)")
L("Leseart x benannt:")
L(pd.crosstab(rd.kind, rd['named']).to_string())

# --- Seitenklassen: Altbestand = Seite, die schon im April-Log angefragt wurde
apr = req[(req.mon == "2026-04") & (req.page != "")]
ALT = set(apr.page.unique())
L(f"\nAltbestand (im April-Log angefragte Seitennamen): {len(ALT):,} Seiten")
schwarm_pages = set(pages[pages.wiki == "dse"].name.astype(str))
L(f"Seiten des Abzugs im Wiki dse: {len(schwarm_pages):,}")
L(f"Ueberschneidung Altbestand x Abzugsseiten: {len(ALT & schwarm_pages):,}")
rd["klasse"] = np.where(rd.page.isin(ALT), "altbestand",
                        np.where(rd.page.isin(schwarm_pages), "schwarmseite",
                                 np.where(rd.page == "", "ohne_seite", "sonstige_neue")))
L("\nLesezugriffe je Monat und Seitenklasse:")
t2 = pd.crosstab(rd.mon, rd.klasse)
L(t2.to_string())
t2.to_csv(os.path.join(OUT, "inventar_seitenklasse.csv"))

# --- Verkehrsklassen
# Beleg-Anker: 99.9 % aller Schreibversuche tragen ein NAME-Feld, und 3000 der 3103
# Namen des Abzugs kommen im NAME-Feld vor -> NAME ist der Flotten-Anker.
w = req[req.kind == "write"]
L(f"\nSchreibversuche im Log {len(w):,}, davon mit NAME {int((w.name!='').sum()):,} "
  f"({(w.name!='').mean()*100:.1f} %)")
labels_export = set(rev[rev.wiki == "dse"].label.dropna().astype(str))
lognames = set(req[req['named']].name.unique())
L(f"Namen im Log {len(lognames):,}; Labels im Abzug (dse) {len(labels_export):,}; "
  f"Schnitt {len(lognames & labels_export):,} ({len(lognames & labels_export)/max(len(labels_export),1)*100:.1f} % der Abzugs-Labels)")
fleet16 = set(w[w.name != ""].ip16.unique())
L(f"/16-Netze mit mindestens einem benannten Schreibversuch: {len(fleet16)}")
exp16 = set(rev[rev.wiki == "dse"].ip16.dropna().astype(str))
L(f"/16 des Abzugs (dse): {len(exp16)}, davon in fleet16: {len(exp16 & fleet16)} "
  f"({len(exp16 & fleet16)/max(len(exp16),1)*100:.1f} %) — Kreuzvalidierung Log gegen Abzug")

req["f16"] = req.ip16.isin(fleet16)
req["verkehr"] = np.where(req['named'], "benannt_agent",
                          np.where(req.f16, "unbenannt_flottennetz", "unbenannt_fremd"))
t3 = pd.crosstab(req.mon, req.verkehr)
L("\nVerkehrsklassen je Monat (alle Requests):")
L(t3.to_string())
L("\nApril ist vollstaendig vor dem Vorfall (erster Schwarm-Schreibvorgang 2026-05-24) "
  "und dient als Grundlast-Eichung:")
L((t3.div(t3.sum(axis=1), axis=0) * 100).round(2).to_string())
t3.to_csv(os.path.join(OUT, "inventar_verkehr.csv"))
t4 = pd.crosstab(rd.mon, np.where(rd['named'], "benannt_agent",
                                  np.where(rd.ip16.isin(fleet16), "unbenannt_flottennetz", "unbenannt_fremd")))
L("\nNur Lesezugriffe, Verkehrsklassen je Monat:")
L(t4.to_string())
t4.to_csv(os.path.join(OUT, "inventar_verkehr_lesen.csv"))

# =========================================================== 2 Kernmessung
hdr("2  Kernmessung: gelesen x uebernommen fuer die 1140 koordinierenden Namen")

# 2a Merkmalszustand jeder Seite ueber die Zeit (mask_body nach jeder Version)
BASIS = ["sig_endzeile", "please_relay", "cohort", "runde", "state_conf", "uhrenpaar", "zeitstempel"]
BIT = {k: 1 << i for i, k in enumerate(BASIS)}


def meldeformat(mask):
    return bool(mask & BIT["sig_endzeile"]) and bool(mask & (BIT["uhrenpaar"] | BIT["zeitstempel"])) \
        and bool(mask & (BIT["runde"] | BIT["state_conf"] | BIT["cohort"]))


def hasm(mask, m):
    return meldeformat(mask) if m == "meldeformat" else bool(mask & BIT[m])


ixd = ix[ix.page_key.str.startswith("dse~")].sort_values(["page_key", "time"], kind="mergesort")
PSTATE = {}
for pk, g in ixd.groupby("page_key", sort=False):
    PSTATE[pk[4:]] = (g.time.values.astype("datetime64[s]").astype(np.int64),
                      g.mask_body.values.astype(np.int64))
L(f"Seitenzustands-Zeitreihen aufgebaut fuer {len(PSTATE):,} dse-Seiten")


def mask_at(page: str, ts: int) -> int:
    e = PSTATE.get(page)
    if e is None:
        return -1                      # Seite im Abzug unbekannt (z.B. spaeter geloescht)
    times, masks = e
    j = np.searchsorted(times, ts, side="right") - 1
    return int(masks[j]) if j >= 0 else 0


# 2b Erstversion je koordinierendem Namen
first_rev = (ix.sort_values("time").groupby("label", as_index=False).first())
fr = first_rev.set_index("label")
COORD = COORD[COORD.label.isin(fr.index)].copy()
COORD["t_rev"] = COORD.label.map(fr.time)
COORD["seite_rev"] = COORD.label.map(fr.page_key)
for m in MERKMALE:
    COORD["ad_" + m] = COORD.label.map(fr["ad_" + m]).astype(bool)
    COORD["exp_" + m] = COORD.label.map(fr["exp_" + m + "__seite"]).astype(bool)
L(f"Koordinierende Namen mit Erstversion im Index: {len(COORD)}")

# 2c Erster Schreibversuch im Log je Name (kann vor der archivierten Version liegen)
wn = req[(req.kind == "write") & (req['named'])]
first_write_log = wn.groupby("name").ts.min()
COORD["t_write_log"] = COORD.label.map(first_write_log)
# ACHTUNG: pandas 3 legt datetime64[us] ab; .astype("int64") liefert MIKROsekunden.
# Deshalb explizit ueber die Epoche rechnen.
EPOCH = pd.Timestamp("1970-01-01", tz="UTC")
COORD["t_rev_s"] = ((COORD.t_rev - EPOCH).dt.total_seconds()).astype(np.int64)
COORD["t0"] = np.minimum(COORD.t_write_log.fillna(9e18), COORD.t_rev_s).astype(np.int64)
L(f"Namen mit Schreibversuch im Log: {int(COORD.t_write_log.notna().sum())} von {len(COORD)} "
  f"({COORD.t_write_log.notna().mean()*100:.1f} %)")
d_pre = (COORD.t_rev_s - COORD.t0)
L(f"Vorlauf erster Log-Schreibversuch vor erster archivierter Version: Median {d_pre.median():.0f} s, "
  f"p90 {d_pre.quantile(.9):.0f} s, max {d_pre.max():.0f} s")

# 2d Lesezugriffe je Name vor t0
rl = req[req['named'] & (req.is_read | req.is_feed)][["name", "ts", "kind", "page", "is_read", "is_feed"]]
rl = rl[rl["name"].isin(set(COORD.label))]
L(f"Lesezugriffe benannter koordinierender Namen gesamt: {len(rl):,}")

t0map = dict(zip(COORD.label, COORD.t0))
rl = rl.assign(t0=rl['name'].map(t0map))
pre = rl[rl.ts < rl.t0].copy()
L(f"davon VOR dem ersten Schreibversuch: {len(pre):,} auf {pre.page.nunique():,} Seiten, "
  f"{pre['name'].nunique():,} Namen")

pre["mask"] = [mask_at(p, int(t)) for p, t in zip(pre.page, pre.ts)]
recs = {}
for m in MERKMALE:
    carr = pre[pre.is_read & (pre["mask"] > 0)].copy()
    carr["hit"] = [hasm(mm, m) for mm in carr["mask"]]
    recs[m] = set(carr[carr.hit].name.unique())
    L(f"  Merkmal {m}: {len(recs[m])} Namen haben VOR ihrem ersten Schreibversuch eine Seite "
      f"gelesen, die das Merkmal in diesem Moment trug")

COORD["las_irgendwas"] = COORD.label.isin(set(pre[pre.is_read]['name'].unique()))
COORD["las_feed"] = COORD.label.isin(set(pre[pre.is_feed]['name'].unique()))
L(f"\nKoordinierende Namen mit IRGENDEINEM Seitenlesen vor dem ersten Schreibversuch: "
  f"{int(COORD.las_irgendwas.sum())} von {len(COORD)} ({COORD.las_irgendwas.mean()*100:.1f} %)")
L(f"... mit Abruf des Aenderungsstroms (RecentChanges/rc/rss) vorher: "
  f"{int(COORD.las_feed.sum())} ({COORD.las_feed.mean()*100:.1f} %)")


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"),) * 3
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p * 100, (c - h) * 100, (c + h) * 100


def rd_ci(k1, n1, k0, n0, z=1.96):
    if n1 == 0 or n0 == 0:
        return (float("nan"),) * 3
    p1, p0 = k1 / n1, k0 / n0
    se = math.sqrt(p1 * (1 - p1) / n1 + p0 * (1 - p0) / n0)
    return (p1 - p0) * 100, (p1 - p0 - z * se) * 100, (p1 - p0 + z * se) * 100


rows = []
for m in MERKMALE:
    COORD["gelesen_" + m] = COORD.label.isin(recs[m])
    g = COORD["gelesen_" + m].values
    a = COORD["ad_" + m].values
    n11, n10, n01, n00 = int((g & a).sum()), int((g & ~a).sum()), int((~g & a).sum()), int((~g & ~a).sum())
    p1, l1, h1 = wilson(n11, n11 + n10)
    p0, l0, h0 = wilson(n01, n01 + n00)
    r, rl_, rh = rd_ci(n11, n11 + n10, n01, n01 + n00)
    rows.append(dict(merkmal=m, herkunft=HERKUNFT[m], n=len(COORD),
                     gelesen=n11 + n10, gelesen_ad=n11, gelesen_noad=n10,
                     nichtgelesen=n01 + n00, nichtgelesen_ad=n01, nichtgelesen_noad=n00,
                     p_ad_wenn_gelesen=p1, ci_lo_gelesen=l1, ci_hi_gelesen=h1,
                     p_ad_wenn_nicht=p0, ci_lo_nicht=l0, ci_hi_nicht=h0,
                     rd=r, rd_lo=rl_, rd_hi=rh,
                     uebernommen_ohne_lesebeleg=n01,
                     anteil_uebernehmer_ohne_lesebeleg=n01 / max(n11 + n01, 1) * 100))
tab = pd.DataFrame(rows)
L("\nVier-Felder-Tafel gelesen x uebernommen (Analogon zu tab:exposure):")
L(tab.round(2).to_string(index=False))
tab.to_csv(os.path.join(OUT, "kernmessung_gelesen_adoption.csv"), index=False)

COORD.to_csv(os.path.join(OUT, "kernmessung_namen.csv"), index=False)

# =========================================================== 3 Die 249
hdr("3  Die Uebernehmer ohne Quelle auf der eigenen Seite")
for m in ["runde", "cohort", "meldeformat"]:
    sel = COORD[COORD["ad_" + m] & ~COORD["exp_" + m]]
    L(f"\nMerkmal {m}: {len(sel)} Namen uebernahmen es, obwohl es auf ihrer Seite nicht stand "
      f"(Abgleich tab:exposure / paper_exposition_kernzahlen.json)")
    gl = sel["gelesen_" + m].sum()
    L(f"  davon hatten VOR dem ersten Schreibversuch eine ANDERE Seite gelesen, die es trug: "
      f"{int(gl)} ({gl/max(len(sel),1)*100:.1f} %)")
    L(f"  davon hatten ueberhaupt irgendeine Seite gelesen: {int(sel.las_irgendwas.sum())} "
      f"({sel.las_irgendwas.mean()*100:.1f} %)")
    L(f"  davon hatten den Aenderungsstrom abgerufen: {int(sel.las_feed.sum())} "
      f"({sel.las_feed.mean()*100:.1f} %)")
    sel.to_csv(os.path.join(OUT, f"ohne_quelle_{m}.csv"), index=False)

# Was genau lasen die 249 des Rundenmarkers, und wie lange vor dem Schreiben?
sel = COORD[COORD.ad_runde & ~COORD.exp_runde]
pre_sel = pre[pre['name'].isin(set(sel.label))].copy()
L(f"\nLesezugriffe dieser {len(sel)} Namen vor ihrem ersten Schreibversuch: {len(pre_sel):,}")
if len(pre_sel):
    pre_sel["vorlauf_s"] = pre_sel.t0 - pre_sel.ts
    L("  Vorlauf (s) Quantile: " + str(pre_sel.vorlauf_s.quantile([.1, .25, .5, .75, .9]).round(0).to_dict()))
    L("  meistgelesene Seiten: " + str(pre_sel.page.value_counts().head(10).to_dict()))
    pre_sel.to_csv(os.path.join(OUT, "ohne_quelle_runde_lesezugriffe.csv"), index=False)

# =========================================================== 4 Geburtsstunde
hdr("4  Geburtsstunde der Koordination")
T0 = pd.Timestamp("2026-06-16T09:27:10Z")
# Die zwoelf Koordinationsseiten: Seiten, auf denen zwischen 09:27 und 10:47 geschrieben wurde
win = ix[(ix.time >= T0 - pd.Timedelta(minutes=1)) & (ix.time <= pd.Timestamp("2026-06-16T10:47:00Z"))]
kseiten = sorted(set(p[4:] for p in win.page_key.unique() if p.startswith("dse~")))
L(f"Seiten mit Versionen im Fenster 09:26-10:47 des 16.06.: {len(kseiten)} -> {kseiten}")

r16 = req[(req.t >= pd.Timestamp("2026-06-16T00:00:00Z")) & (req.t < pd.Timestamp("2026-06-17T00:00:00Z"))]
rows = []
for p in kseiten:
    anl = ix[ix.page_key == "dse~" + p].time.min()
    anl_ts = int(anl.timestamp())
    sub = r16[(r16.page == p)]
    reads = sub[sub.is_read]
    after = reads[reads.ts >= anl_ts]
    first = after.ts.min() if len(after) else np.nan
    leser = set(after[after['name'] != ""]['name'].unique())
    # Leser, die danach selbst schrieben
    schrieb = set(wn[wn['name'].isin(leser)].name.unique())
    rows.append(dict(seite=p, angelegt=anl, n_versionen=int((ix.page_key == "dse~" + p).sum()),
                     lesezugriffe_tag=len(reads), lesezugriffe_nach_anlage=len(after),
                     erste_lesung_s_nach_anlage=(first - anl_ts) if first == first else np.nan,
                     benannte_leser=len(leser), unbenannte_lesungen=int((after['name'] == "").sum()),
                     leser_die_spaeter_schrieben=len(schrieb)))
kt = pd.DataFrame(rows).sort_values("angelegt")
L(kt.to_string(index=False))
kt.to_csv(os.path.join(OUT, "geburtsstunde_seiten.csv"), index=False)

# Detailspur der Erstseite
P0 = "DataUSAStateSequenceCollab2027"
sp = r16[(r16.page == P0)].sort_values("ts")
L(f"\nAlle Requests auf {P0} am 16.06.: {len(sp)}")
L(sp.assign(t=sp.t)[["t", "ip", "name", "kind"]].head(60).to_string(index=False))
sp.to_csv(os.path.join(OUT, "geburtsstunde_erstseite.csv"), index=False)

# Kumulative Leser in den ersten Stunden
anl0 = int(ix[ix.page_key == "dse~" + P0].time.min().timestamp())
for h in (1, 2, 4, 8, 12, 24):
    s = sp[(sp.ts >= anl0) & (sp.ts < anl0 + h * 3600) & sp.is_read]
    L(f"  +{h:2d} h: {len(s):4d} Lesezugriffe, {s[s['name']!='']['name'].nunique():3d} benannte Leser, "
      f"{int((s['name']=='').sum()):3d} unbenannt")

json.dump({"n_coordpop": int(len(COORD)),
           "las_irgendwas": int(COORD.las_irgendwas.sum()),
           "las_feed": int(COORD.las_feed.sum()),
           "tafel": tab.to_dict("records")},
          open(os.path.join(OUT, "kernzahlen_lesespalte.json"), "w"), indent=1, default=float)
L("\nfertig.")
LOG.close()
