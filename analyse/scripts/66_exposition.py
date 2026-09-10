#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
66_exposition.py
================
Was war bei Ankunft SICHTBAR? — Rekonstruktion der Exposition (nicht des Lesens).

Motivation: De Marzo et al., arXiv:2609.09150, modellieren dieselbe Flotte als
Abschreiben proportional zu dem, was sichtbar war (Seitentext + die letzten 100
Versionen wikiweit). Unser Abzug enthaelt keinen einzigen erfolgreichen
Lesezugriff (events.jsonl: 101 Zugriffsereignisse, alle fehlgeschlagene Proben),
aber er enthaelt den vollen Seitentext jeder Version. Exposition ist damit
rekonstruierbar, Lesen bleibt unbeobachtet. Jede Zahl hier ist eine OBERGRENZE
fuer Uebertragung, nie ein Beleg fuer Uebertragung.

Teile:
  A  Expositionsindex je Version: page_state_before (= body der Vorgaengerversion
     derselben Seite) und feed_before (= die letzten N Versionen wikiweit),
     N in {30, 100, 300}, Hauptwert 100 wie De Marzo.
     -> artefakte/paper_exposition_index.parquet
  B  Exposition gegen Adoption in der Erstversion je Name, 6-h-Fenster, je Merkmal
     vier Zellen; die interessante Zelle ist "uebernommen ohne sichtbare Quelle".
     -> artefakte/paper_exposition_adoption_6h.csv
     -> artefakte/paper_exposition_adoption_gesamt.csv
     -> paper/figures/data/fig10_exposure_adoption.json
     -> paper/tables/tab_exposure_adoption.tex
  C  Expositionsvariable je rekonstruierter Kohorte: lag bei ihrer Ankunft auf einer
     ihrer Seiten eine fremde Rundenangabe oberhalb ihres spaeteren Standes?
     -> artefakte/paper_exposition_kohorten.csv  (Praediktoren fuer 63_fortschritt_robust.py)
  D  Aktualitaet gegen aufgelaufene Beliebtheit in der Seitenwahl
     (De Marzo: Aktualitaet treibt, Beliebtheit steigt um ~2,3x und ist dann flach).
     Bedingtes Logit mit gezogenen Alternativen (McFadden), plus Bin-Variante.
     -> artefakte/paper_exposition_aktualitaet.csv
     -> paper/tables/tab_exposure_recency.tex

WICHTIG zur Trennung von `body` und `delta`:
  Ein Wiki speichert bei jeder Bearbeitung die ganze Seite. Fuer AUTORENSCHAFT ist
  `body` deshalb verboten (er enthaelt den Text aller Vorgaenger) und `delta`
  Pflicht — so haelt es das ganze uebrige Paket. Fuer EXPOSITION ist `body` der
  Vorgaengerversion dagegen genau richtig: es ist der fremde Text, den der
  Ankommende vorfand. Beide Verwendungen sind hier strikt getrennt: alles, was
  jemandem zugeschrieben wird, kommt aus `delta`; alles, was jemandem sichtbar war,
  kommt aus `body` der Vorgaengerversion bzw. aus `delta` fremder Versionen im Strom.

Alle Pfade RELATIV zum Skript-Ort (analyse/scripts/ -> analyse/), Muster wie
51_prozess.py Zeilen 22-27.
Lauf:  .venv/bin/python scripts/66_exposition.py      (Seed 20260909)
Log:   artefakte/_paper_exposition.log
Beruehrt keines der bestehenden Skripte; benoetigte Regeln sind hier kopiert,
Quellzeile jeweils im Kommentar.
"""
from __future__ import annotations
import os, re, json, math, warnings, collections
import numpy as np
import pandas as pd
from scipy import stats, optimize

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)                       # analyse/
DATA = os.path.join(BASE, "data")
ART = os.path.join(BASE, "artefakte")
PAPER = os.path.join(os.path.dirname(BASE), "paper")
TAB = os.path.join(PAPER, "tables")
FIGDATA = os.path.join(PAPER, "figures", "data")
os.makedirs(TAB, exist_ok=True); os.makedirs(FIGDATA, exist_ok=True)
OUT = lambda n: os.path.join(ART, n)
SEED = 20260909
rng = np.random.default_rng(SEED)
LOG = open(OUT("_paper_exposition.log"), "w", encoding="utf-8")


def L(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LOG.write(s + "\n")


def hdr(t):
    L("\n" + "=" * 88 + f"\n{t}\n" + "=" * 88)


# =========================================================== 0. Laden
hdr("0  Laden")
d = pd.read_parquet(OUT("schwarm_deltas.parquet"))
d["time"] = pd.to_datetime(d["time"], utc=True)
d["delta"] = d["delta"].fillna("")
d["body"] = d["body"].fillna("")
# Stabil sortieren: gleiche Zeitstempel deterministisch aufloesen (Handoff §6.1)
d = d.sort_values(["time", "page_key", "seq"], kind="mergesort").reset_index(drop=True)
L(f"Versionen {len(d)}  Seiten {d.page_key.nunique()}  Namen {d.label.nunique()}  "
  f"Zeitraum {d.time.min()} .. {d.time.max()}")

events = pd.read_json(os.path.join(DATA, "events.jsonl"), lines=True)
zug = events[events.event_type == "probe"]
L("events.jsonl:", len(events), "Ereignisse:", events.event_type.value_counts().to_dict())
L(f"Zugriffsereignisse (event_type=='probe'): {len(zug)}, davon success_observed==1: "
  f"{int((zug.success_observed == 1).sum())}, ==0: {int((zug.success_observed == 0).sum())} "
  "-> kein einziger belegter Lesezugriff; die Leseschicht ist im Abzug nicht vorhanden, "
  "nur Schreiben (save) und Loeschen (delete). Deshalb diese Rekonstruktion.")
L("Anforderungsarten der Proben:", zug.request_action.value_counts().to_dict())

LB = pd.read_csv(OUT("paper_lernkurve_q2_inhaltlicher_lesebeweis.csv"))
COORDPOP = set(LB[LB.coordpop].label.dropna())
L(f"Koordinations-Population (coordpop, wie Fig. 3 / 65_adoption_robust.py Z. 227): {len(COORDPOP)} Namen")
L(f"Bisherige Kennzahl 'nachweisliches vorheriges Lesen' = zitierter CamelCase-Fremdseitenname >=12 Zeichen "
  f"in der Erstversion: {int((LB[LB.coordpop].n_fremdseiten_genannt > 0).sum())} von {len(COORDPOP)} = "
  f"{(LB[LB.coordpop].n_fremdseiten_genannt > 0).mean()*100:.1f} %")

# Die drei Infrastrukturseiten des Wikis (Begruessung, Start, Test) — Handoff §7
INFRA = ["dse~WillkommenImWiki", "dse~StartSeite", "dse~TestSeite"]
L(f"Infrastrukturseiten {INFRA}: {int(d.page_key.isin(INFRA).sum())} Versionen "
  f"({d.page_key.isin(INFRA).mean()*100:.1f} %); groesster archivierter Seitentext dort "
  f"{d[d.page_key.isin(INFRA)].body_len.max():,} Zeichen, korpusweit {d.body_len.max():,} Zeichen, "
  f"Summe aller Seitentexte {d.body_len.sum()/1e6:.1f} MB")

# =========================================================== 1. Merkmalsregexe
# Uebernommen aus 41_lernkurve.py Zeilen 14-31 (NICHT neu erfunden).
PAT = {
    "sig_endzeile": r"(?m)--\s*[A-Za-z][A-Za-z0-9_]{3,}\s*$",
    "please_relay": r"(?i)please\s+(?:post|relay|share|signal|report|append|confirm|reply|leave)",
    "cohort":       r"(?i)\bcohort\b",
    "runde":        r"\b[RG][1-9]\b",
    "state_conf":   r"(?i)(?:\bR[1-9]\s*CONFIRMED\b|\bCONFIRMED[0-9]?\s*=|\bSTATE[0-9]-)",
    "uhrenpaar":    r"(?i)(task[- ]clock|container UTC|shared UTC|wiki[- ]local|scaffold (?:time|clock))",
    "zeitstempel":  r"\b[0-2]?\d:[0-5]\d:[0-5]\d\b",
}
RX = {k: re.compile(p) for k, p in PAT.items()}
BASIS = list(PAT)
# "meldeformat" wie 41_lernkurve.py Z. 34: Signatur + (Uhrenpaar|Zeitstempel) + (Runde|STATE/CONFIRMED|cohort)
MERKMALE = ["runde", "cohort", "meldeformat", "sig_endzeile", "please_relay"]
HERKUNFT = {"runde": "invented", "cohort": "invented", "meldeformat": "invented",
            "sig_endzeile": "brought", "please_relay": "brought"}


def flags_of(text: str) -> int:
    """Bitmaske der Basismerkmale eines Textes."""
    m = 0
    for i, k in enumerate(BASIS):
        if RX[k].search(text):
            m |= (1 << i)
    return m


BIT = {k: 1 << i for i, k in enumerate(BASIS)}


def meldeformat(mask: int) -> bool:
    return bool(mask & BIT["sig_endzeile"]) and bool(mask & (BIT["uhrenpaar"] | BIT["zeitstempel"])) \
        and bool(mask & (BIT["runde"] | BIT["state_conf"] | BIT["cohort"]))


def has(mask, merkmal):
    return meldeformat(mask) if merkmal == "meldeformat" else bool(mask & BIT[merkmal])


# =========================================================== 2. Kopierschleifen-Regel
# Wortgleich uebernommen aus 65_adoption_robust.py Zeilen 122-148 (Regel A und B'),
# damit dieselbe Schleife gefiltert wird wie dort — keine zweite Regel (Handoff §4).
hdr("2  Kopierschleife (Regel A und B' aus 65_adoption_robust.py Z. 122-148)")
NORM = lambda s: re.sub(r"\s+", " ", s).strip().lower()
d["norm"] = d.delta.map(NORM)
same = d[d.norm != ""].sort_values(["label", "norm", "time"])
prev_t = same.groupby(["label", "norm"]).time.shift(1)
gap_s = (same.time - prev_t).dt.total_seconds()
ruleA = set(same.index[gap_s.notna() & (gap_s <= 3600)])
URLRE = re.compile(r"https?://")
seen_line = set(); ruleBp = []
for idx, delta in zip(d.index, d.delta):
    lines = {NORM(x) for x in delta.split("\n")}
    lines = {x for x in lines if len(x) >= 80 and not URLRE.match(x)}
    if lines & seen_line:
        ruleBp.append(idx)
    seen_line |= lines
ruleBp = set(ruleBp)
d["copyloop"] = d.index.isin(ruleA | ruleBp)
L(f"Regel A {len(ruleA)}, Regel B' {len(ruleBp)}, A u B' = {int(d.copyloop.sum())} Versionen "
  f"({d.copyloop.mean()*100:.1f} %) — Abgleich mit BERICHT_robust_adoption.md: 1897 Versionen (13,0 %)")
w = d[(d.time >= pd.Timestamp("2026-06-18T20:00:00Z")) & (d.time < pd.Timestamp("2026-06-18T21:00:00Z"))]
L(f"Fenster 18.06. 20-21 Uhr: {len(w)} Versionen auf {w.page_key.nunique()} Seiten, davon Kopierschleife {int(w.copyloop.sum())}")

# =========================================================== 3. TEIL A  Expositionsindex
hdr("A  Expositionsindex: page_state_before und feed_before")

# --- A1 eigene Version (Autorenschaft: NUR delta)
d["mask_delta"] = [flags_of(x) for x in d.delta]

# --- A2 Seitenzustand vor der Version = body der Version mit seq-1 derselben Seite.
# Exakt und schnell: body ist fast immer ein reiner Anhang an den Vorgaenger-body;
# dann gilt flags(body) = flags(vorheriger body) | flags(angehaengter Teil). Nur wenn
# der neue body den alten NICHT als Praefix hat (Loeschung/Umbau), wird voll gerechnet.
mask_body = np.zeros(len(d), dtype=np.int64)
prev_body: dict[str, str] = {}
prev_mask: dict[str, int] = {}
n_full = 0
order = d.sort_values(["page_key", "seq"], kind="mergesort").index
for idx in order:
    pk = d.at[idx, "page_key"]; b = d.at[idx, "body"]
    pb = prev_body.get(pk); pm = prev_mask.get(pk, 0)
    if pb is not None and len(b) >= len(pb) and b.startswith(pb):
        m = pm | flags_of(b[len(pb):])
    else:
        m = flags_of(b); n_full += 1
    mask_body[idx] = m
    prev_body[pk] = b; prev_mask[pk] = m
d["mask_body"] = mask_body
L(f"Seitenmasken: {len(d)} Versionen, davon {n_full} voll neu gerechnet (kein Praefix des Vorgaengers)")

# Zustand VOR der Version: Maske der Version mit seq-1 derselben Seite, 0 bei seq==min
d = d.sort_values(["page_key", "seq"], kind="mergesort")
d["mask_page_before"] = d.groupby("page_key")["mask_body"].shift(1).fillna(0).astype(np.int64)
d["neuanlage"] = d.groupby("page_key")["seq"].shift(1).isna()
d = d.sort_values(["time", "page_key", "seq"], kind="mergesort").reset_index(drop=True)
L(f"Neuanlagen (kein sichtbarer Seitenzustand): {int(d.neuanlage.sum())} von {len(d)} "
  f"({d.neuanlage.mean()*100:.1f} %)")

# --- A3 Aenderungsstrom: die letzten N Versionen wikiweit STRIKT vor dem Zeitstempel.
# Hauptdefinition strikt in der Zeit (gleiche Zeitstempel zaehlen nicht als "vorher"),
# Sensitivitaet positionsbasiert (Reihenfolge der stabilen Sortierung).
tv = d.time.values
first_at_t = np.searchsorted(tv, tv, side="left")     # Index der ersten Version mit gleichem Zeitstempel
pos = np.arange(len(d))
NS = (30, 100, 300)
bitcols = {}
for i, k in enumerate(BASIS):
    bitcols[k] = ((d.mask_delta.values >> i) & 1).astype(np.int64)


def feed_masks(end_idx: np.ndarray, N: int, keep: np.ndarray) -> np.ndarray:
    """OR-Maske der Merkmale der Versionen [end_idx-N, end_idx-1], nur wo keep==True."""
    out = np.zeros(len(d), dtype=np.int64)
    start = np.maximum(end_idx - N, 0)
    for i, k in enumerate(BASIS):
        c = np.concatenate([[0], np.cumsum(bitcols[k] * keep)])
        cnt = c[end_idx] - c[start]
        out |= (cnt > 0).astype(np.int64) << i
    return out


def feed_share(end_idx: np.ndarray, N: int, key: str) -> np.ndarray:
    """Anteil der letzten N Versionen vor dem Zeitstempel, deren Delta das Merkmal traegt."""
    start = np.maximum(end_idx - N, 0)
    c = np.concatenate([[0], np.cumsum(bitcols[key])])
    cnt = c[end_idx] - c[start]
    n = np.maximum(end_idx - start, 1)
    return cnt / n


keep_all = np.ones(len(d), dtype=np.int64)
keep_nl = (~d.copyloop.values).astype(np.int64)                    # ohne Kopierschleife
keep_ni = (~d.page_key.isin(INFRA).values).astype(np.int64)        # ohne Infrastrukturseiten
for N in NS:
    d[f"mask_feed{N}"] = feed_masks(first_at_t, N, keep_all)
    d[f"mask_feed{N}_pos"] = feed_masks(pos, N, keep_all)
for k in BASIS:
    d[f"share100_{k}"] = feed_share(first_at_t, 100, k)
d["mask_feed100_noloop"] = feed_masks(first_at_t, 100, keep_nl)
d["mask_feed100_noinfra"] = feed_masks(first_at_t, 100, keep_ni)

# Seitenzustand ohne Infrastrukturseiten (dort wird der Zustand auf 0 gesetzt)
d["mask_page_before_noinfra"] = np.where(d.page_key.isin(INFRA), 0, d.mask_page_before)

# Zwei Kanaele, getrennt gefuehrt. Der Seitenkanal ist der PRIMAERE: er ist der Text,
# den der Ankommende auf genau der Seite vorfand, auf die er schrieb. Der Stromkanal
# (letzte N Versionen wikiweit) ist die weiteste denkbare Sichtbarkeitsannahme und,
# wie Teil B zeigt, ab dem 16.06. praktisch gesaettigt — er trennt deshalb nichts.
PRIMAER = "seite"
VARIANTEN = {                     # Name -> (Spalte Seitenzustand, Spalte Strom)
    "seite":                    ("mask_page_before", None),
    "seite_ohne_infraseiten":   ("mask_page_before_noinfra", None),
    "strom_N30":                (None, "mask_feed30"),
    "strom_N100":               (None, "mask_feed100"),
    "strom_N300":               (None, "mask_feed300"),
    "strom_N100_positionen":    (None, "mask_feed100_pos"),
    "strom_N100_ohne_kopierschleife": (None, "mask_feed100_noloop"),
    "strom_N100_ohne_infraseiten":    (None, "mask_feed100_noinfra"),
    "seite_oder_strom_N100":    ("mask_page_before", "mask_feed100"),   # Definition wie De Marzo
    "seite_oder_strom_N30":     ("mask_page_before", "mask_feed30"),
}

idx_cols = ["rev_id", "page_key", "label", "seq", "time", "neuanlage", "copyloop"] + \
           [f"share100_{k}" for k in BASIS] + [
            "mask_delta", "mask_body", "mask_page_before", "mask_page_before_noinfra",
            "mask_feed30", "mask_feed100", "mask_feed300", "mask_feed100_pos",
            "mask_feed100_noloop", "mask_feed100_noinfra"]
IDX = d[idx_cols].copy()
for merk in MERKMALE:
    IDX["ad_" + merk] = [has(m, merk) for m in d.mask_delta]
    for vn, (pc, fc) in VARIANTEN.items():
        e = np.zeros(len(d), dtype=bool)
        if pc: e |= np.array([has(m, merk) for m in d[pc]])
        if fc: e |= np.array([has(m, merk) for m in d[fc]])
        IDX[f"exp_{merk}__{vn}"] = e
IDX.to_parquet(OUT("paper_exposition_index.parquet"), index=False)
L(f"-> {OUT('paper_exposition_index.parquet')} ({len(IDX)} Zeilen, {len(IDX.columns)} Spalten)")
for merk in MERKMALE:
    L(f"  {merk:14s} sichtbar auf der Seite {IDX[f'exp_{merk}__seite'].mean()*100:5.1f} %   "
      f"im Strom (N=100) {IDX[f'exp_{merk}__strom_N100'].mean()*100:5.1f} %   "
      f"im eigenen Delta {IDX['ad_'+merk].mean()*100:5.1f} %")

# =========================================================== 4. TEIL B  Exposition gegen Adoption
hdr("B  Exposition gegen Adoption in der Erstversion je Name")
fa = IDX.sort_values(["time", "page_key", "seq"], kind="mergesort").groupby("label", as_index=False).first()
L(f"Erstversionen: {len(fa)} Namen; davon Koordinations-Population {int(fa.label.isin(COORDPOP).sum())}")
fa_cp = fa[fa.label.isin(COORDPOP)].copy()
L(f"Neuanlage als Erstversion (kein Seitenzustand sichtbar): {fa_cp.neuanlage.mean()*100:.1f} % der coordpop-Namen")

rows6, rowsG = [], []
for vn in VARIANTEN:
    for merk in MERKMALE:
        a = fa_cp["ad_" + merk].values
        e = fa_cp[f"exp_{merk}__{vn}"].values
        rowsG.append(dict(variante=vn, merkmal=merk, herkunft=HERKUNFT[merk], n=len(fa_cp),
                          exp_ad=int((e & a).sum()), exp_noad=int((e & ~a).sum()),
                          noexp_ad=int((~e & a).sum()), noexp_noad=int((~e & ~a).sum())))
    c = fa_cp[fa_cp.time >= pd.Timestamp("2026-06-16T00:00:00Z")].copy()
    c["f"] = c.time.dt.floor("6h")
    for f, g in c.groupby("f"):
        for merk in MERKMALE:
            a = g["ad_" + merk].values; e = g[f"exp_{merk}__{vn}"].values
            rows6.append(dict(variante=vn, merkmal=merk, f=f, n=len(g),
                              exp_ad=int((e & a).sum()), exp_noad=int((e & ~a).sum()),
                              noexp_ad=int((~e & a).sum()), noexp_noad=int((~e & ~a).sum())))
G = pd.DataFrame(rowsG)
W6 = pd.DataFrame(rows6)
for T in (G, W6):
    T["anteil_exponiert"] = (T.exp_ad + T.exp_noad) / T.n * 100
    T["anteil_uebernommen"] = (T.exp_ad + T.noexp_ad) / T.n * 100
    T["adoption_wenn_exponiert"] = np.where(T.exp_ad + T.exp_noad > 0, T.exp_ad / (T.exp_ad + T.exp_noad) * 100, np.nan)
    T["adoption_wenn_nicht_exponiert"] = np.where(T.noexp_ad + T.noexp_noad > 0, T.noexp_ad / (T.noexp_ad + T.noexp_noad) * 100, np.nan)
    T["anteil_ohne_sichtbare_quelle"] = np.where(T.exp_ad + T.noexp_ad > 0, T.noexp_ad / (T.exp_ad + T.noexp_ad) * 100, np.nan)
G.to_csv(OUT("paper_exposition_adoption_gesamt.csv"), index=False)
W6.to_csv(OUT("paper_exposition_adoption_6h.csv"), index=False)
L(f"-> {OUT('paper_exposition_adoption_gesamt.csv')} ({len(G)}), {OUT('paper_exposition_adoption_6h.csv')} ({len(W6)})")

L("\nGesamt (Koordinations-Population, alle Varianten):")
L(G[["variante", "merkmal", "n", "exp_ad", "exp_noad", "noexp_ad", "noexp_noad",
     "adoption_wenn_exponiert", "adoption_wenn_nicht_exponiert", "anteil_ohne_sichtbare_quelle"]]
  .round(1).to_string(index=False))

# Risikodifferenz und exaktes 2x2 je Merkmal (Hauptvariante)
hdr("B2  Exponiert gegen nicht exponiert: Risikodifferenz, Odds Ratio, Fisher")
rows = []
for merk in MERKMALE:
    r = G[(G.variante == PRIMAER) & (G.merkmal == merk)].iloc[0]
    a, b_, c_, dd = r.exp_ad, r.exp_noad, r.noexp_ad, r.noexp_noad
    p1 = a / (a + b_) if a + b_ else np.nan
    p0 = c_ / (c_ + dd) if c_ + dd else np.nan
    se = math.sqrt(p1 * (1 - p1) / max(a + b_, 1) + p0 * (1 - p0) / max(c_ + dd, 1))
    orr, pf = stats.fisher_exact([[a, b_], [c_, dd]])
    rows.append(dict(merkmal=merk, herkunft=HERKUNFT[merk], n_exp=int(a + b_), n_noexp=int(c_ + dd),
                     p_exp=p1 * 100, p_noexp=p0 * 100, rd=(p1 - p0) * 100,
                     rd_lo=(p1 - p0 - 1.96 * se) * 100, rd_hi=(p1 - p0 + 1.96 * se) * 100,
                     odds_ratio=orr, p_fisher=pf,
                     n_ohne_quelle=int(c_), anteil_ohne_quelle=c_ / max(a + c_, 1) * 100))
RD = pd.DataFrame(rows)
RD.to_csv(OUT("paper_exposition_risikodifferenz.csv"), index=False)
L(RD.round(3).to_string(index=False))
L(f"-> {OUT('paper_exposition_risikodifferenz.csv')}")

# ---------- B3  Sichtbarkeit als Praediktor, Strom als Intensitaet statt als Schalter
hdr("B3  Logistische Adoption: Seitenkanal (Schalter) und Stromkanal (Intensitaet)")
import statsmodels.api as sm
share_cols = {"runde": "share100_runde", "cohort": "share100_cohort",
              "meldeformat": "share100_sig_endzeile", "sig_endzeile": "share100_sig_endzeile",
              "please_relay": "share100_please_relay"}
T0 = pd.Timestamp("2026-06-16T09:27:10Z")
rows_lg = []
for merk in MERKMALE:
    sub = fa_cp[fa_cp.time >= pd.Timestamp("2026-06-16T00:00:00Z")].copy()
    sub["y"] = sub["ad_" + merk].astype(int)
    sub["seite"] = sub[f"exp_{merk}__seite"].astype(int)
    sub["strom_anteil"] = sub[share_cols[merk]].astype(float)
    sub["stunden"] = (sub.time - T0).dt.total_seconds() / 3600.0
    X = sm.add_constant(sub[["seite", "strom_anteil", "stunden"]])
    if sub.y.nunique() < 2 or sub.seite.nunique() < 2:
        continue
    r = sm.Logit(sub.y, X).fit(disp=0, cov_type="HC1")
    for t in ["seite", "strom_anteil", "stunden"]:
        ci = r.conf_int().loc[t]
        rows_lg.append(dict(merkmal=merk, term=t, n=int(len(sub)), beta=float(r.params[t]),
                            se=float(r.bse[t]), or_=float(np.exp(r.params[t])),
                            or_lo=float(np.exp(ci[0])), or_hi=float(np.exp(ci[1])), p=float(r.pvalues[t]),
                            pseudo_r2=float(r.prsquared)))
LG = pd.DataFrame(rows_lg)
LG.to_csv(OUT("paper_exposition_logit.csv"), index=False)
L("Logit je Merkmal: y = Merkmal im eigenen Delta der Erstversion (ab 16.06.);")
L("  seite = Merkmal stand im Seitentext der Vorgaengerversion; strom_anteil = Anteil der letzten 100")
L("  Versionen wikiweit mit dem Merkmal; stunden = Stunden seit 16.06. 09:27 (Zeittrend).")
L(LG.round(4).to_string(index=False))
L(f"-> {OUT('paper_exposition_logit.csv')}")

# Saettigung des Stromkanals dokumentieren
sat = fa_cp[fa_cp.time >= pd.Timestamp("2026-06-16T12:00:00Z")]
for merk in ["runde", "cohort"]:
    L(f"Saettigung Strom N=100, {merk}: ab 16.06. 12:00 sind "
      f"{sat[f'exp_{merk}__strom_N100'].mean()*100:.1f} % der Erstversionen exponiert "
      f"(Median Anteil im Strom {sat[share_cols[merk]].median()*100:.1f} %)")

# =========================================================== 5. TEIL C  Kohorten-Exposition
hdr("C  Expositionsvariable je rekonstruierter Kohorte")
K = pd.read_csv(OUT("paper_fortschritt_kohorten.csv"))
K["erste_version"] = pd.to_datetime(K.erste_version, utc=True)
Z = pd.read_csv(OUT("paper_prozess_label_zuordnung.csv"))
lab2coh = dict(zip(Z.label.astype(str), Z.cohort))
RM = pd.read_csv(OUT("paper_prozess_rundensaetze_delta.csv"))
RM["time"] = pd.to_datetime(RM.time, utc=True)
RM["coh_of_label"] = RM.label.astype(str).map(lab2coh)
L(f"Kohorten {len(K)}; Rundensaetze auf Deltas {len(RM)} (aus 51_prozess.py Z. 204)")

dd = d.copy()
dd["cohort"] = dd.label.astype(str).map(lab2coh)
coh_pages = dd[dd.cohort.notna()].groupby("cohort").page_key.apply(set).to_dict()
coh_t0 = dd[dd.cohort.notna()].groupby("cohort").time.min().to_dict()

# Rundenangaben je (Seite, Zeit): nur Saetze mit erkanntem Rundenmarker, fremdes Label
RMv = RM[["page_key", "label", "coh_of_label", "time", "num", "cls", "sent"]].dropna(subset=["num"])
RMv = RMv[RMv.num.between(1, 10)]
by_page = {pk: g.sort_values("time") for pk, g in RMv.groupby("page_key")}

rows = []
for _, k in K.iterrows():
    coh = k.cohort_key
    pages = coh_pages.get(coh, set())
    t0 = coh_t0.get(coh, k.erste_version)
    mx_sicht, n_hoeher, n_seiten_hoeher, n_sicht = 0, 0, 0, 0
    for pk in pages:
        g = by_page.get(pk)
        if g is None: continue
        gv = g[(g.time < t0) & (g.coh_of_label != coh)]
        if gv.empty: continue
        n_sicht += len(gv)
        m = int(gv.num.max())
        mx_sicht = max(mx_sicht, m)
        hoch = gv[gv.num > k.max_runde_belegt]
        n_hoeher += len(hoch)
        n_seiten_hoeher += int(len(hoch) > 0)
    rows.append(dict(cohort_key=coh, aufgabenfamilie=k.aufgabenfamilie,
                     n_seiten_kohorte=len(pages), erste_version=t0,
                     max_runde_belegt=k.max_runde_belegt,
                     exp_runde_max_vor=mx_sicht,
                     exp_runde_saetze_vor=n_sicht,
                     exp_vorsprung_saetze=n_hoeher,
                     exp_vorsprung_seiten=n_seiten_hoeher,
                     exp_vorsprung_b=int(mx_sicht > k.max_runde_belegt)))
KE = pd.DataFrame(rows)

# Zusaetzlich: war bei Ankunft ueberhaupt Koordinationsformat sichtbar? (aus dem Index)
first_rev_of_coh = dd[dd.cohort.notna()].sort_values(["time", "page_key", "seq"], kind="mergesort") \
                     .groupby("cohort", as_index=False).first()[["cohort", "rev_id"]]
fx = first_rev_of_coh.merge(IDX[["rev_id", f"exp_runde__{PRIMAER}", f"exp_cohort__{PRIMAER}",
                                 f"exp_meldeformat__{PRIMAER}", "neuanlage"]], on="rev_id", how="left")
fx = fx.rename(columns={"cohort": "cohort_key", f"exp_runde__{PRIMAER}": "exp_runde_sichtbar_b",
                        f"exp_cohort__{PRIMAER}": "exp_cohort_sichtbar_b",
                        f"exp_meldeformat__{PRIMAER}": "exp_meldeformat_sichtbar_b",
                        "neuanlage": "ankunft_auf_neuer_seite"})
KE = KE.merge(fx, on="cohort_key", how="left")
for c in ["exp_runde_sichtbar_b", "exp_cohort_sichtbar_b", "exp_meldeformat_sichtbar_b", "ankunft_auf_neuer_seite"]:
    KE[c] = KE[c].fillna(False).astype(int)
KE.to_csv(OUT("paper_exposition_kohorten.csv"), index=False)
L(f"-> {OUT('paper_exposition_kohorten.csv')} ({len(KE)} Zeilen)")
L(f"Kohorten mit sichtbarer fremder Rundenangabe vor Ankunft: {int((KE.exp_runde_saetze_vor>0).sum())} "
  f"({(KE.exp_runde_saetze_vor>0).mean()*100:.1f} %); mit sichtbarer Angabe OBERHALB des eigenen spaeteren Standes: "
  f"{int(KE.exp_vorsprung_b.sum())} ({KE.exp_vorsprung_b.mean()*100:.1f} %)")
K5 = KE[KE.max_runde_belegt >= 1]
L(f"Teilmenge max_runde_belegt>=1 (n={len(K5)}): Vorsprung sichtbar {int(K5.exp_vorsprung_b.sum())} "
  f"({K5.exp_vorsprung_b.mean()*100:.1f} %); Familien mit >=1 solcher Kohorte: "
  f"{K5[K5.exp_vorsprung_b==1].aufgabenfamilie.nunique()}")
L("Vergleich mit der bisherigen Behandlungsvariable 'Zukunftsantwort erhalten' (8 Faelle, davon 6 mit Ergebnis): "
  f"die Expositionsvariable hat {int(K5.exp_vorsprung_b.sum())} behandelte Kohorten in {K5[K5.exp_vorsprung_b==1].aufgabenfamilie.nunique()} Familien")
L("\nexp_runde_max_vor Verteilung:", KE.exp_runde_max_vor.value_counts().sort_index().to_dict())

# =========================================================== 6. TEIL D  Aktualitaet gegen Beliebtheit
hdr("D  Seitenwahl: Aktualitaet gegen aufgelaufene Beliebtheit (De Marzo-Gegenprobe)")
NALT = 20
rows_choice = []
last_t: dict[str, float] = {}
cnt: dict[str, int] = {}
pages_list: list[str] = []
tsec = (d.time.values.astype("datetime64[s]").astype(np.int64)).astype(float)
pk_arr = d.page_key.values
for i in range(len(d)):
    pk = pk_arr[i]; t = tsec[i]
    if pk in cnt and len(pages_list) > NALT:
        alt = rng.choice(len(pages_list), size=NALT, replace=False)
        chosen = [pk] + [pages_list[j] for j in alt if pages_list[j] != pk][:NALT]
        for j, p in enumerate(chosen):
            rows_choice.append((i, j == 0, math.log1p(max(t - last_t[p], 0.0) / 60.0), math.log1p(cnt[p]), cnt[p]))
    last_t[pk] = t
    if pk not in cnt:
        cnt[pk] = 0; pages_list.append(pk)
    cnt[pk] += 1
CH = pd.DataFrame(rows_choice, columns=["choice_id", "gewaehlt", "log_alter_min", "log_bestand", "bestand"])
L(f"Wahlsituationen (Version auf bereits bestehender Seite): {CH.choice_id.nunique()}, "
  f"Alternativen je Situation {NALT} gezogen (McFadden), Zeilen {len(CH)}")


def clogit(X: np.ndarray, cid: np.ndarray, y: np.ndarray):
    """Bedingtes Logit ueber gezogene Alternativen; Rueckgabe (beta, se, ll)."""
    uid, inv = np.unique(cid, return_inverse=True)
    ny = y.astype(bool)

    def nll(b):
        v = X @ b
        mx = np.zeros(len(uid)); np.maximum.at(mx, inv, v)
        e = np.exp(v - mx[inv])
        s = np.zeros(len(uid)); np.add.at(s, inv, e)
        return -float(np.sum(v[ny] - mx - np.log(s)))

    b0 = np.zeros(X.shape[1])
    r = optimize.minimize(nll, b0, method="BFGS")
    H = r.hess_inv if isinstance(r.hess_inv, np.ndarray) else np.eye(len(b0))
    se = np.sqrt(np.clip(np.diag(H), 0, None))
    return r.x, se, -r.fun


Xa = CH[["log_alter_min", "log_bestand"]].values
b, se, ll = clogit(Xa, CH.choice_id.values, CH.gewaehlt.values)
ll0 = -CH.choice_id.nunique() * math.log(NALT + 1)
L(f"Bedingtes Logit, Praediktoren [log(1+Alter in min), log(1+Bestand)]:")
for nm, bb, ss in zip(["log_alter_min", "log_bestand"], b, se):
    L(f"  {nm:16s} beta={bb:+.4f}  se={ss:.4f}  z={bb/ss:+.1f}  exp(beta)={math.exp(bb):.3f}")
L(f"  LL={ll:.1f}  LL0={ll0:.1f}  McFadden R2={1-ll/ll0:.3f}")

BINS = [(1, 1), (2, 2), (3, 5), (6, 10), (11, 25), (26, 50), (51, 10**9)]
BINLAB = ["1", "2", "3-5", "6-10", "11-25", "26-50", ">50"]
def binof(k):
    for i, (lo, hi) in enumerate(BINS):
        if lo <= k <= hi: return i
    return 0
CH["bin"] = CH.bestand.map(binof)
D = np.zeros((len(CH), len(BINS) - 1))
for i in range(1, len(BINS)):
    D[:, i - 1] = (CH.bin.values == i).astype(float)
Xb = np.column_stack([CH.log_alter_min.values, D])
b2, se2, ll2 = clogit(Xb, CH.choice_id.values, CH.gewaehlt.values)
L(f"\nBin-Variante (Referenz: Bestand = 1 Version), Aktualitaet kontrolliert:")
rows_rec = [dict(term="log_alter_min", beta=b2[0], se=se2[0], faktor=math.exp(b2[0]),
                 lo=math.exp(b2[0] - 1.96 * se2[0]), hi=math.exp(b2[0] + 1.96 * se2[0]),
                 n_choices=int(CH.choice_id.nunique()))]
L(f"  log_alter_min     beta={b2[0]:+.4f} se={se2[0]:.4f} Faktor je e-fachem Alter {math.exp(b2[0]):.3f}")
for i, lab in enumerate(BINLAB[1:]):
    rows_rec.append(dict(term=f"bestand_{lab}", beta=b2[1 + i], se=se2[1 + i], faktor=math.exp(b2[1 + i]),
                         lo=math.exp(b2[1 + i] - 1.96 * se2[1 + i]), hi=math.exp(b2[1 + i] + 1.96 * se2[1 + i]),
                         n_choices=int(CH.choice_id.nunique())))
    L(f"  Bestand {lab:6s}    beta={b2[1+i]:+.4f} se={se2[1+i]:.4f} Faktor gegen Bestand=1: {math.exp(b2[1+i]):.2f} "
      f"[{math.exp(b2[1+i]-1.96*se2[1+i]):.2f}, {math.exp(b2[1+i]+1.96*se2[1+i]):.2f}]")
rows_rec.insert(0, dict(term="log_alter_min (ohne Bins)", beta=b[0], se=se[0], faktor=math.exp(b[0]),
                        lo=math.exp(b[0] - 1.96 * se[0]), hi=math.exp(b[0] + 1.96 * se[0]),
                        n_choices=int(CH.choice_id.nunique())))
rows_rec.insert(1, dict(term="log_bestand (ohne Bins)", beta=b[1], se=se[1], faktor=math.exp(b[1]),
                        lo=math.exp(b[1] - 1.96 * se[1]), hi=math.exp(b[1] + 1.96 * se[1]),
                        n_choices=int(CH.choice_id.nunique())))
# Gegenprobe ohne die drei Infrastrukturseiten (sie stellen 20,7 % aller Versionen
# und besetzen den obersten Bestandsbin fast allein — ohne sie ist die Frage "flach ab 50?" erst ehrlich)
mask_ok = ~d.page_key.isin(INFRA).values
CHi = CH[[mask_ok[i] for i in CH.choice_id]].copy()
L(f"\nOhne die drei Infrastrukturseiten als Ziel: {CHi.choice_id.nunique()} von {CH.choice_id.nunique()} Wahlsituationen")
bi, sei, _ = clogit(CHi[["log_alter_min", "log_bestand"]].values, CHi.choice_id.values, CHi.gewaehlt.values)
L(f"  log_alter {bi[0]:+.4f} (se {sei[0]:.4f}), log_bestand {bi[1]:+.4f} (se {sei[1]:.4f})")
Di = np.zeros((len(CHi), len(BINS) - 1))
for i in range(1, len(BINS)):
    Di[:, i - 1] = (CHi.bin.values == i).astype(float)
b3v, se3, _ = clogit(np.column_stack([CHi.log_alter_min.values, Di]), CHi.choice_id.values, CHi.gewaehlt.values)
L(f"  Bin-Variante ohne Infrastrukturseiten: log_alter {b3v[0]:+.4f} (se {se3[0]:.4f})")
for i, lab in enumerate(BINLAB[1:]):
    rows_rec.append(dict(term=f"bestand_{lab} (ohne Infraseiten)", beta=b3v[1 + i], se=se3[1 + i],
                         faktor=math.exp(b3v[1 + i]), lo=math.exp(b3v[1 + i] - 1.96 * se3[1 + i]),
                         hi=math.exp(b3v[1 + i] + 1.96 * se3[1 + i]), n_choices=int(CHi.choice_id.nunique())))
    L(f"    Bestand {lab:6s} Faktor gegen Bestand=1: {math.exp(b3v[1+i]):.2f} "
      f"[{math.exp(b3v[1+i]-1.96*se3[1+i]):.2f}, {math.exp(b3v[1+i]+1.96*se3[1+i]):.2f}]")
REC = pd.DataFrame(rows_rec)
REC.to_csv(OUT("paper_exposition_aktualitaet.csv"), index=False)
# Anteil der Erstwahl auf einer Seite, die in den letzten 10 Minuten bearbeitet wurde
frisch = CH[CH.gewaehlt].log_alter_min.map(lambda x: math.expm1(x))
L(f"Gewaehlte Seiten: Median Alter seit letzter Bearbeitung {frisch.median():.1f} min; "
  f"Anteil <=10 min {(frisch<=10).mean()*100:.1f} %, <=60 min {(frisch<=60).mean()*100:.1f} %")
nicht = CH[~CH.gewaehlt].log_alter_min.map(lambda x: math.expm1(x))
L(f"Gezogene Alternativen: Median Alter {nicht.median():.1f} min; Anteil <=10 min {(nicht<=10).mean()*100:.1f} %")
L(f"-> {OUT('paper_exposition_aktualitaet.csv')}")

# =========================================================== 7. LaTeX-Fragmente
hdr("7  LaTeX-Fragmente und Abbildungsdaten")
esc = lambda s: str(s).replace("_", r"\_").replace("%", r"\%")
NAMEN = {"runde": "round marker", "cohort": r"\emph{cohort}", "meldeformat": "full report format",
         "sig_endzeile": "signature line", "please_relay": "request formula"}
feed_share_exp = {m: float(G[(G.variante == "strom_N100") & (G.merkmal == m)].iloc[0].anteil_exponiert)
                  for m in MERKMALE}
lines = [r"\begin{tabular}{llrrrrrr}", r"\toprule",
         r"& & \multicolumn{2}{c}{On the page} & \multicolumn{2}{c}{Not on the page} & & In the \\",
         r"\cmidrule(lr){3-4}\cmidrule(lr){5-6}",
         r"Feature & Origin & $n$ & adopted & $n$ & adopted & \multicolumn{1}{c}{No page source} & feed \\",
         r"\midrule"]
for merk in MERKMALE:
    r = RD[RD.merkmal == merk].iloc[0]
    lines.append(f"{NAMEN[merk]} & {r.herkunft} & {int(r.n_exp)} & {r.p_exp:.1f}\\,\\% & "
                 f"{int(r.n_noexp)} & {r.p_noexp:.1f}\\,\\% & "
                 f"{int(r.n_ohne_quelle)} of {int(r.n_ohne_quelle + round(r.n_exp * r.p_exp / 100))} "
                 f"({r.anteil_ohne_quelle:.1f}\\,\\%) & {feed_share_exp[merk]:.1f}\\,\\% \\\\")
lines += [r"\bottomrule", r"\end{tabular}"]
open(os.path.join(TAB, "tab_exposure_adoption.tex"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
L(f"-> {os.path.join(TAB, 'tab_exposure_adoption.tex')}")

TERM_EN = {
    "log_alter_min (ohne Bins)": r"$\log(1+\text{minutes since last edit})$, without bins",
    "log_bestand (ohne Bins)": r"$\log(1+\text{prior revisions})$, without bins",
    "log_alter_min": r"$\log(1+\text{minutes since last edit})$",
}
def term_en(t):
    if t in TERM_EN: return TERM_EN[t]
    if t.startswith("bestand_"):
        rest = t[len("bestand_"):]
        suf = ""
        if rest.endswith(" (ohne Infraseiten)"):
            rest = rest[:-len(" (ohne Infraseiten)")]; suf = ", infrastructure pages excluded"
        return f"prior revisions {rest.replace('>', r'$>$').replace('-', r'--')}{suf}"
    return esc(t)


lines = [r"\begin{tabular}{lrrr}", r"\toprule",
         r"Term & $\hat\beta$ & Multiplier & 95\,\% CI \\", r"\midrule"]
for i, r in REC.iterrows():
    if r.term == "bestand_2":
        lines.append(r"\midrule \multicolumn{4}{l}{\emph{Prior revisions in bins, reference = 1 revision, recency controlled}} \\")
    if r.term == "bestand_2 (ohne Infraseiten)":
        lines.append(r"\midrule \multicolumn{4}{l}{\emph{Same, the three infrastructure pages excluded as targets}} \\")
    lines.append(f"{term_en(r.term)} & ${r.beta:+.3f}$ & {r.faktor:.2f} & [{r.lo:.2f}, {r.hi:.2f}] \\\\")
lines += [r"\bottomrule", r"\end{tabular}"]
open(os.path.join(TAB, "tab_exposure_recency.tex"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
L(f"-> {os.path.join(TAB, 'tab_exposure_recency.tex')}")

iso = lambda t: pd.Timestamp(t).tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%SZ")
MIN_N = 20
h = W6[W6.variante == PRIMAER]
series = []
for merk in ["runde", "cohort", "meldeformat"]:
    g = h[h.merkmal == merk].sort_values("f")
    series.append({
        "key": merk, "label": {"runde": "round marker", "cohort": "“cohort”",
                               "meldeformat": "full report format"}[merk],
        "points": [[iso(t), (None if n < MIN_N else float(v1)), (None if n < MIN_N else float(v2)),
                    (None if n < MIN_N else float(v3)), int(n)]
                   for t, v1, v2, v3, n in zip(g.f, g.exp_ad / g.n * 100, g.exp_noad / g.n * 100,
                                               g.noexp_ad / g.n * 100, g.n)],
        "gesamt": {k: float(v) for k, v in
                   G[(G.variante == PRIMAER) & (G.merkmal == merk)].iloc[0]
                   [["exp_ad", "exp_noad", "noexp_ad", "noexp_noad", "anteil_ohne_sichtbare_quelle"]].items()},
    })
json.dump({
    "figure": 10,
    "title": "Exposure and adoption in newcomers' first contributions",
    "x": {"name": "6-h window (wall time, UTC)"},
    "y": {"name": "share of first contributions, %"},
    "min_n": MIN_N,
    "definition": ("exposed = feature present in the page text of the immediately preceding revision of the page "
                   "written to (page channel; the feed channel of the last 100 revisions wiki-wide is saturated "
                   "and reported separately); adopted = feature present in the newcomer's own delta. "
                   "Exposure is availability, not reading."),
    "series": series,
    "window_n": [[iso(t), int(n)] for t, n in zip(h[h.merkmal == "runde"].sort_values("f").f,
                                                  h[h.merkmal == "runde"].sort_values("f").n)],
    "sources": {"data": f"paper_exposition_adoption_6h.csv (variante={PRIMAER})"},
}, open(os.path.join(FIGDATA, "fig10_exposure_adoption.json"), "w"), indent=1)
L(f"-> {os.path.join(FIGDATA, 'fig10_exposure_adoption.json')}")

# =========================================================== 8. Zitierfaehige Saetze
hdr("8  Zitierfaehige Kernzahlen")
r_run = RD[RD.merkmal == "runde"].iloc[0]
r_coh = RD[RD.merkmal == "cohort"].iloc[0]
r_mel = RD[RD.merkmal == "meldeformat"].iloc[0]
KERN = dict(
    n_coordpop=len(fa_cp),
    runde=dict(p_exp=float(r_run.p_exp), p_noexp=float(r_run.p_noexp), rd=float(r_run.rd),
               rd_lo=float(r_run.rd_lo), rd_hi=float(r_run.rd_hi),
               ohne_quelle_n=int(r_run.n_ohne_quelle), ohne_quelle_p=float(r_run.anteil_ohne_quelle)),
    cohort=dict(p_exp=float(r_coh.p_exp), p_noexp=float(r_coh.p_noexp), rd=float(r_coh.rd),
                rd_lo=float(r_coh.rd_lo), rd_hi=float(r_coh.rd_hi),
                ohne_quelle_n=int(r_coh.n_ohne_quelle), ohne_quelle_p=float(r_coh.anteil_ohne_quelle)),
    meldeformat=dict(p_exp=float(r_mel.p_exp), p_noexp=float(r_mel.p_noexp), rd=float(r_mel.rd),
                     ohne_quelle_n=int(r_mel.n_ohne_quelle), ohne_quelle_p=float(r_mel.anteil_ohne_quelle)),
    kohorten_vorsprung_n=int(KE.exp_vorsprung_b.sum()),
    kohorten_vorsprung_p=float(KE.exp_vorsprung_b.mean() * 100),
    kohorten510_vorsprung_n=int(K5.exp_vorsprung_b.sum()),
    kohorten510_vorsprung_fam=int(K5[K5.exp_vorsprung_b == 1].aufgabenfamilie.nunique()),
    aktualitaet_beta=float(b[0]), aktualitaet_se=float(se[0]),
    bestand_beta=float(b[1]), bestand_se=float(se[1]),
    lesebeweis_alt_p=float((LB[LB.coordpop].n_fremdseiten_genannt > 0).mean() * 100),
)
json.dump(KERN, open(OUT("paper_exposition_kernzahlen.json"), "w"), indent=1)
L(json.dumps(KERN, indent=1))
L(f"-> {OUT('paper_exposition_kernzahlen.json')}")
LOG.close()
