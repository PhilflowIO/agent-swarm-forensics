#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
65_adoption_robust.py
=====================
Robustheitsprüfung zweier Ansteckungs-/Adoptionsbefunde des Papers (main.tex §Rendezvous, §Prozess):

  Teil 1  Hawkes-Verzweigungszahl ohne Kopierschleife und ohne Duplikatsätze.
          Gleicher Schätzer, gleiche Fenster und Reihen wie 53_mathematik.py (Teil E),
          nur die Ereignismenge wird in drei Stufen ausgedünnt (full | no_copyloop |
          no_copyloop_no_dupsent).
          -> artefakte/paper_robust_hawkes_dedup.csv

  Teil 2  Formatkonvergenz (Fig. 3) mit und ohne Namen, die eine explizite Kontaktspur zeigen
          (inhaltlicher Lesebeweis, Kopierer in der Zitatkaskade, Rendezvous-Sprache).
          -> artefakte/paper_robust_format_gefiltert_6h.csv
          -> paper/figures/data/fig3b_format_filtered.json

Alle Pfade relativ zum Skript-Ort (analyse/scripts/ -> analyse/), wie in 51_prozess.py.
Lauf:  .venv/bin/python scripts/65_adoption_robust.py
Log:   artefakte/_paper_robust_adoption.log
Berührt weder 53_mathematik.py noch 41_lernkurve.py; beide laufen beim Import mit Seiteneffekten,
deshalb sind die benötigten Funktionen hier kopiert (Quellzeilen im Kommentar).
"""
from __future__ import annotations
import os, re, json, math, warnings, collections
import numpy as np
import pandas as pd
from scipy import stats, optimize

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)                      # analyse/
DATA = os.path.join(BASE, "data")
ART = os.path.join(BASE, "artefakte")
FIGDATA = os.path.join(os.path.dirname(BASE), "paper", "figures", "data")
OUT = lambda n: os.path.join(ART, n)
SEED = 20260909
rng = np.random.default_rng(SEED)
LOG = open(OUT("_paper_robust_adoption.log"), "w", encoding="utf-8")


def L(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LOG.write(s + "\n")


def hdr(t):
    L("\n" + "=" * 88 + f"\n{t}\n" + "=" * 88)


# =========================================================== 0. Laden
d = pd.read_parquet(OUT("schwarm_deltas.parquet"))
d["time"] = pd.to_datetime(d["time"], utc=True)
d["delta"] = d["delta"].fillna("")
d = d.sort_values(["time", "page_key", "seq"]).reset_index(drop=True)
labels = pd.read_json(os.path.join(DATA, "labels.jsonl"), lines=True)
labels["first_write"] = pd.to_datetime(labels["first_write"], utc=True)
CP = pd.read_csv(OUT("paper_prozess_zitatkaskade_kopien.csv"))
CP["kopier_zeit"] = pd.to_datetime(CP["kopier_zeit"], utc=True)
L(f"Deltas {len(d)}  Labels {len(labels)}  Kopierereignisse (Kaskade) {len(CP)}  Seed {SEED}")

# Sanity: labels.first_write == min(time) je Label in den Deltas?
fw_delta = d.groupby("label").time.min()
fw_lab = labels.set_index("label").first_write
common = fw_delta.index.intersection(fw_lab.index)
mism = int((fw_delta.loc[common] != fw_lab.loc[common]).sum())
L(f"labels.first_write vs. min(delta.time): {len(common)} gemeinsame Labels, {mism} Abweichungen "
  f"(Labels nur in labels.jsonl: {len(fw_lab.index.difference(fw_delta.index))}, nur in Deltas: {len(fw_delta.index.difference(fw_lab.index))})")

# =========================================================== 1. Hawkes-Schätzer (Kopie aus 53_mathematik.py, Zeilen 392-431)
# Quelle: analyse/scripts/53_mathematik.py  _A (392-396), hawkes_negll (397-407), fit_hawkes (408-416),
#         poisson_ll (417-419), rescale_ks (420-431). Unverändert übernommen, damit die Schätzung identisch ist.
def _A(beta, t):
    s_ = np.logaddexp.accumulate(beta * t)
    logA = np.full(len(t), -np.inf); logA[1:] = s_[:-1] - beta * t[1:]
    return np.exp(logA)


def hawkes_negll(lp, t, T, mu_breaks):
    lp = np.clip(np.asarray(lp, float), -25, 10)
    alpha, beta = math.exp(lp[0]), math.exp(lp[1]); mus = np.exp(lp[2:])
    if alpha >= beta: return 1e12 + (alpha - beta)
    A = _A(beta, t)
    seg = np.searchsorted(mu_breaks, t, side="right") - 1
    lam = mus[seg] + alpha * A
    ll = np.sum(np.log(lam))
    edges = np.concatenate([mu_breaks, [T]]); ll -= np.sum(mus * np.diff(edges))
    ll -= (alpha / beta) * np.sum(1 - np.exp(-beta * (T - t)))
    return -ll


def fit_hawkes(t, T, k_segments=1):
    breaks = np.linspace(0, T, k_segments + 1)[:-1]
    best = None
    for a0, b0 in ((0.5, 1.0), (3.0, 6.0), (0.1, 0.2)):
        x0 = np.log([a0, b0] + [max(len(t) / T, 1e-3)] * k_segments)
        res = optimize.minimize(hawkes_negll, x0, args=(t, T, breaks), method="L-BFGS-B", bounds=[(-25, 10)] * len(x0), options=dict(maxiter=500))
        if best is None or res.fun < best.fun: best = res
    best.x = np.exp(best.x)
    return best, breaks


def poisson_ll(t, T, k_segments):
    edges = np.linspace(0, T, k_segments + 1); cnt, _ = np.histogram(t, edges); w = np.diff(edges)
    lam = cnt / w; return np.sum(cnt[cnt>0] * np.log(lam[cnt>0])) - np.sum(lam * w)


def rescale_ks(params, t, T, breaks):
    alpha, beta = params[0], params[1]; mus = np.asarray(params[2:])
    A = _A(beta, t)
    edges = np.concatenate([breaks, [T]])
    seg_int = np.cumsum(np.concatenate([[0], mus * np.diff(edges)]))
    sg = np.searchsorted(breaks, t, side="right") - 1
    cum_mu = seg_int[sg] + mus[sg] * (t - breaks[sg])
    Lam = cum_mu + (alpha / beta) * (np.arange(len(t)) - A)
    dd = np.diff(Lam); return stats.kstest(dd, stats.expon().cdf).statistic, stats.kstest(dd, stats.expon().cdf).pvalue


# =========================================================== 2. Kopierschleifen-Regel (drei Stufen)
hdr("TEIL 1  Hawkes ohne Kopierschleife / Duplikatsätze")
NORM = lambda s: re.sub(r"\s+", " ", s).strip().lower()   # wie 51_prozess.py Zeile 628
d["norm"] = d.delta.map(NORM)

# Regel A: gleiches Label, identischer normalisierter Delta-Text (nicht leer), frühere Version
#          desselben Labels mit demselben Text liegt <= 3600 s zurück (rollierende Stunde, nicht Kalenderstunde).
same = d[d.norm != ""].sort_values(["label", "norm", "time"])
prev_t = same.groupby(["label", "norm"]).time.shift(1)
gap_s = (same.time - prev_t).dt.total_seconds()
ruleA = set(same.index[gap_s.notna() & (gap_s <= 3600)])
# Regel B: die Version erscheint in der Zitatkaskade als Kopierer (rev_id in paper_prozess_zitatkaskade_kopien.csv, Spalte rev_id;
#          Kaskade = Zeile >= 80 Zeichen, zuvor von einem ANDEREN Label geschrieben; 51_prozess.py Zeilen 626-648)
ruleB = set(d.index[d.rev_id.isin(set(CP.rev_id))])
# Regel B' (Kopierschleife im engeren Sinn): die Version enthält >= 1 Zeile >= 80 Zeichen (normalisiert, nicht mit http beginnend;
#          Kriterien wie 51_prozess.py Z. 633/468), die zuvor schon einmal im Korpus geschrieben wurde — von IRGENDEINEM Label,
#          auch demselben. B' ⊇ B, weil die Kaskadendatei nur Fremd-Label-Kopien enthält (51_prozess.py Z. 641 `if not same_label`);
#          die Schleife des 18.06. läuft aber grossteils label-intern (ein Name schreibt dieselben vier Zeilen auf viele eigene Seiten).
URLRE = re.compile(r"https?://")
seen_line = set(); ruleBp = []
for idx, delta in zip(d.index, d.delta):     # d ist zeitsortiert
    lines = {NORM(x) for x in delta.split("\n")}
    lines = {x for x in lines if len(x) >= 80 and not URLRE.match(x)}
    if lines & seen_line: ruleBp.append(idx)
    seen_line |= lines
ruleBp = set(ruleBp)
copyloop = ruleA | ruleBp
d["copyloop_A"] = d.index.isin(ruleA); d["copyloop_B"] = d.index.isin(ruleB); d["copyloop_Bp"] = d.index.isin(ruleBp); d["copyloop"] = d.index.isin(copyloop)
L(f"Regel A (gleiches Label, gleicher normalisierter Delta-Text, <=60 min nach vorheriger identischer Version): {len(ruleA)} Versionen, "
  f"{d[d.copyloop_A].label.nunique()} Labels, {d[d.copyloop_A].page_key.nunique()} Seiten")
L(f"Regel B (Kopierer in der Zitatkaskade, rev_id-Treffer): {len(ruleB)} Versionen von {CP.rev_id.nunique()} distinkten rev_id in der Kaskadendatei")
L(f"Regel B' (>=1 Zeile >=80 Zeichen zuvor von irgendeinem Label geschrieben): {len(ruleBp)} Versionen, B ⊆ B': {ruleB <= ruleBp}, B' \\ B (label-interne Wiederholungen): {len(ruleBp - ruleB)}")
L(f"A ∩ B': {len(ruleA & ruleBp)}   A ∪ B' = Kopierschleife: {len(copyloop)} Versionen ({len(copyloop)/len(d)*100:.1f} % aller {len(d)}), "
  f"{d[d.copyloop].label.nunique()} Labels, {d[d.copyloop].page_key.nunique()} Seiten")
# Kontrolle gegen die im Paper genannte Kopierschleife 18.06. 20-21 Uhr (1769 Versionen, 293 Seiten)
w_loop = d[(d.time >= pd.Timestamp("2026-06-18T20:00:00Z")) & (d.time < pd.Timestamp("2026-06-18T21:00:00Z"))]
loop4 = w_loop[w_loop.norm.str.contains("regcf_county_2019", regex=False)]
L(f"Fenster 18.06. 20:00-21:00: {len(w_loop)} Versionen auf {w_loop.page_key.nunique()} Seiten; davon Kopierschleife nach Regel A: {int(w_loop.copyloop_A.sum())}, "
  f"Regel B: {int(w_loop.copyloop_B.sum())}, Regel B': {int(w_loop.copyloop_Bp.sum())}, A∪B': {int(w_loop.copyloop.sum())}; "
  f"Versionen mit den vier jqp/investor.gov-Zeilen: {len(loop4)} auf {loop4.page_key.nunique()} Seiten von {loop4.label.nunique()} Labels, davon als Kopierschleife erfasst {int(loop4.copyloop.sum())}")
top_loop = d[d.copyloop_A].groupby("label").size().sort_values(ascending=False).head(5)
L("Top-5 Labels nach Regel A:", top_loop.to_dict())

# Regel C (Duplikatsätze): Sätze >= 40 Zeichen (Split an Zeilenumbruch und .!? + Leerzeichen, normalisiert).
#          Eine Version gilt als "Duplikatsatz-Version", wenn sie >= 1 qualifizierenden Satz enthält und JEDER dieser Sätze
#          bereits in einer früheren Version (beliebiges Label, beliebige Zeit) vorkam -> sie trägt keinen neuen Satz bei.
SENT_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")
seen_sent = set(); ruleC = []
for idx, delta in zip(d.index, d.delta):     # d ist zeitsortiert
    sents = [NORM(s) for s in SENT_SPLIT.split(delta)]
    sents = [s for s in sents if len(s) >= 40]
    if sents and all(s in seen_sent for s in sents):
        ruleC.append(idx)
    seen_sent.update(sents)
ruleC = set(ruleC)
d["dupsent"] = d.index.isin(ruleC)
L(f"Regel C (alle Sätze >=40 Zeichen bereits früher geschrieben, >=1 Satz): {len(ruleC)} Versionen; davon nicht schon Kopierschleife: {len(ruleC - copyloop)}")
L(f"Stufe no_copyloop: {len(d) - len(copyloop)} Versionen verbleiben; Stufe no_copyloop_no_dupsent: {len(d) - len(copyloop | ruleC)} Versionen verbleiben")

VARIANTS = collections.OrderedDict([
    ("full", d),
    ("no_copyloop", d[~d.copyloop]),
    ("no_copyloop_no_dupsent", d[~d.copyloop & ~d.dupsent]),
])
WINDOWS = (("2026-06-16T00:00:00Z", "2026-06-23T00:00:00Z", "Kernwoche 16.–22.06.", 28),
           ("2026-06-18T00:00:00Z", "2026-06-19T00:00:00Z", "Tag 18.06.", 24))

rows = []
for vname, dv in VARIANTS.items():
    first = dv.groupby("label").time.min()      # Erstversion je Label NACH Ausdünnung (Label verschwindet, wenn alle Versionen entfallen)
    series = (("Namen (erste Version)", first), ("Versionen", dv.time))
    for sname, times in series:
        for w0, w1, wname, kmax in WINDOWS:
            tt = times[(times >= pd.Timestamp(w0)) & (times < pd.Timestamp(w1))].sort_values()
            t = ((tt - pd.Timestamp(w0)).dt.total_seconds() / 3600).values.astype(float)
            t = np.sort(t + np.arange(len(t)) * 1e-9)          # identische Zeitstempel minimal versetzen (wie 53_mathematik.py Z. 439)
            T = (pd.Timestamp(w1) - pd.Timestamp(w0)).total_seconds() / 3600
            for kseg in (1, kmax):
                res, br = fit_hawkes(t, T, kseg); alpha, beta = res.x[0], res.x[1]
                ll_h = -res.fun; ll_p = poisson_ll(t, T, kseg)
                aic_h = 2 * (2 + kseg) - 2 * ll_h; aic_p = 2 * kseg - 2 * ll_p
                ksD, ksp = rescale_ks(res.x, t, T, br)
                rows.append(dict(series=sname, window=wname, kseg=kseg, variant=vname, n_events=len(t), alpha=alpha, beta=beta,
                                 branching=alpha / beta, ks_p=ksp, aic_hawkes=aic_h, aic_poisson=aic_p))
                L(f"  {vname:24s} {sname:22s} {wname:20s} k={kseg:2d} n={len(t):5d}  α/β={alpha/beta:.3f}  1/β={60/beta:.1f} min  ΔAIC={aic_h-aic_p:.0f}  KS p={ksp:.2g}")
HW = pd.DataFrame(rows)
HW.to_csv(OUT("paper_robust_hawkes_dedup.csv"), index=False)
L(f"-> {OUT('paper_robust_hawkes_dedup.csv')} ({len(HW)} Zeilen)")

# Abgleich mit paper_math_hawkes.csv (Variante full muss die Originalzahlen reproduzieren)
orig = pd.read_csv(OUT("paper_math_hawkes.csv"))
chk = HW[HW.variant == "full"].merge(orig, left_on=["series", "window", "kseg"], right_on=["quelle", "fenster", "basisrate_segmente"], how="left")
L("Reproduktion full vs. paper_math_hawkes.csv: max |Δn|=%d, max |Δ Verzweigung|=%.4f" % ((chk.n_events - chk.n).abs().max(), (chk.branching - chk.verzweigung).abs().max()))
piv = HW.pivot_table(index=["series", "window", "kseg"], columns="variant", values="branching")[list(VARIANTS)]
L("\nVerzweigungszahl α/β je Reihe/Fenster/k:\n" + piv.round(3).to_string())
pivn = HW.pivot_table(index=["series", "window", "kseg"], columns="variant", values="n_events")[list(VARIANTS)]
L("\nEreigniszahl:\n" + pivn.to_string())

# =========================================================== 3. Formatkonvergenz ohne Kontaktspur
hdr("TEIL 2  Formatkonvergenz (Fig. 3) ohne Namen mit expliziter Kontaktspur")
rev = pd.read_parquet(OUT("paper_lernkurve_revflags.parquet"))       # Flags aus 41_lernkurve.py Zeilen 14-31
rev["time"] = pd.to_datetime(rev["time"], utc=True)
rev = rev.sort_values(["time", "seq"]).reset_index(drop=True)
fa = rev.groupby("label").first().reset_index()                        # allererste Version je Name (41_lernkurve.py Z. 152)
LB = pd.read_csv(OUT("paper_lernkurve_q2_inhaltlicher_lesebeweis.csv"))
Q5 = pd.read_csv(OUT("paper_lernkurve_q5_rendezvous_treffer.csv"))
coordpop = set(LB[LB.coordpop].label)
L(f"Namen gesamt {len(fa)}; Koordinations-Population (coordpop=True in q2_inhaltlicher_lesebeweis.csv): {len(coordpop)}")

COLS = ["sig_endzeile", "please_relay", "cohort", "runde", "uhrenpaar", "zeitstempel", "vollformat", "meldeformat"]
def table6h(fa_sub):
    c = fa_sub[fa_sub.time >= pd.Timestamp("2026-06-16T00:00:00Z")].copy()
    c["f"] = c.time.dt.floor("6h")
    w6 = c.groupby("f")[COLS].mean().mul(100).round(1)
    w6["n"] = c.groupby("f").size()
    return w6.reset_index()

full_tab = table6h(fa[fa.label.isin(coordpop)])
ref = pd.read_csv(OUT("paper_lernkurve_q3_format_erstversion_koordpop_6h.csv")); ref["f"] = pd.to_datetime(ref.f, utc=True)
m = full_tab.merge(ref, on="f", suffixes=("", "_ref"))
maxdev = max((m[c] - m[c + "_ref"]).abs().max() for c in COLS + ["n"])
L(f"Reproduktion der Referenztabelle paper_lernkurve_q3_format_erstversion_koordpop_6h.csv: {len(full_tab)} vs {len(ref)} Fenster, max. Abweichung {maxdev}")

# --- Kontaktspur je Name
# (a) inhaltlicher Lesebeweis: Erstversion nennt CamelCase-Seitennamen >=12 Zeichen einer existierenden Fremdseite (q2_inhaltlicher_lesebeweis.csv, n_fremdseiten_genannt>0)
trace_a = set(LB[LB.n_fremdseiten_genannt > 0].label)
# (b) Kopierer in der Zitatkaskade (kopierer_label), einmal "irgendwann", einmal "in der Erstversion"
trace_b_any = set(CP.kopierer_label.dropna())
trace_b_first = set(CP[CP.rev_id.isin(set(fa.rev_id))].kopierer_label.dropna())
# (c) Treffer in der Rendezvous-Sprache (q5), einmal "irgendwann", einmal "in der Erstversion"
Q5["time"] = pd.to_datetime(Q5.time, utc=True)
trace_c_any = set(Q5.label.dropna())
first_key = set(zip(fa.label, fa.page_key, fa.time))
trace_c_first = set(Q5[[k in first_key for k in zip(Q5.label, Q5.page_key, Q5.time)]].label)
trace_any = trace_a | trace_b_any | trace_c_any
trace_first = trace_a | trace_b_first | trace_c_first
cp = coordpop
L(f"Kontaktspur (a) Lesebeweis in Erstversion: {len(trace_a)} Namen, davon coordpop {len(trace_a & cp)}")
L(f"Kontaktspur (b) Kopierer in Zitatkaskade: irgendwann {len(trace_b_any)} (coordpop {len(trace_b_any & cp)}), in der Erstversion {len(trace_b_first)} (coordpop {len(trace_b_first & cp)})")
L(f"Kontaktspur (c) Rendezvous-Sprache q5: irgendwann {len(trace_c_any)} (coordpop {len(trace_c_any & cp)}), in der Erstversion {len(trace_c_first)} (coordpop {len(trace_c_first & cp)})")
L(f"Vereinigung a∪b∪c, irgendwann: {len(trace_any)} Namen, coordpop {len(trace_any & cp)} von {len(cp)} ({len(trace_any & cp)/len(cp)*100:.1f} %) -> verbleiben {len(cp - trace_any)}")
L(f"Vereinigung a∪b∪c, nur Erstversion: {len(trace_first)} Namen, coordpop {len(trace_first & cp)} -> verbleiben {len(cp - trace_first)}")

VAR2 = collections.OrderedDict([
    ("full", cp),
    ("no_contact_trace", cp - trace_any),          # Hauptvariante: jede Kontaktspur, egal wann
    ("no_contact_trace_firstline", cp - trace_first),   # Sensitivität: nur Spuren in der Erstversion selbst
])
tabs = []
for vname, labs in VAR2.items():
    t6 = table6h(fa[fa.label.isin(labs)]); t6.insert(0, "variant", vname); tabs.append(t6)
FT = pd.concat(tabs, ignore_index=True)
FT.to_csv(OUT("paper_robust_format_gefiltert_6h.csv"), index=False)
L(f"-> {OUT('paper_robust_format_gefiltert_6h.csv')} ({len(FT)} Zeilen)")

# Kennzahlen: Fenster ~18 h (17.06. 00-06) und ~24 h (17.06. 06-12) nach Koordinationsbeginn 16.06. 09:27:10, plus kumulativ
T0 = pd.Timestamp("2026-06-16T09:27:10Z")
L("\nFensterwerte (Fig.-3-Lesart: Fenster 17.06. 00-06 ≈ 18 h, 17.06. 06-12 ≈ 24 h nach 09:27):")
for vname in VAR2:
    for f in ("2026-06-17T00:00:00Z", "2026-06-17T06:00:00Z"):
        r = FT[(FT.variant == vname) & (FT.f == pd.Timestamp(f))]
        if len(r): r = r.iloc[0]; L(f"  {vname:28s} {f[:13]}  n={int(r.n):3d}  runde={r.runde:5.1f}  cohort={r.cohort:5.1f}  meldeformat={r.meldeformat:5.1f}  sig={r.sig_endzeile:5.1f}  please_relay={r.please_relay:5.1f}")
L("Kumulativ (Erstversionen zwischen T0 und T0+h):")
for vname, labs in VAR2.items():
    sub = fa[fa.label.isin(labs) & (fa.time >= T0)]
    for h in (18, 24):
        s = sub[sub.time < T0 + pd.Timedelta(hours=h)]
        L(f"  {vname:28s} <= {h:2d} h  n={len(s):4d}  runde={s.runde.mean()*100:5.1f}  cohort={s.cohort.mean()*100:5.1f}  meldeformat={s.meldeformat.mean()*100:5.1f}")
# Differenz der Kurven (nur Fenster n>=20 in beiden Varianten)
a = FT[FT.variant == "full"].set_index("f"); b = FT[FT.variant == "no_contact_trace"].set_index("f")
both = a.index[(a.n >= 20) & (b.n.reindex(a.index) >= 20)]
L("Maximale Fensterdifferenz full − no_contact_trace (n>=20 in beiden): " +
  ", ".join(f"{c}={((a.loc[both, c] - b.loc[both, c]).abs().max()):.1f} pp" for c in ("runde", "cohort", "meldeformat", "sig_endzeile", "please_relay")))

# --- fig3b JSON (Struktur wie 57_chartdata_paper.py fig3(), Zeilen 207-245; hier je Variante ein Block)
MIN_N = 20
iso = lambda t: pd.Timestamp(t).strftime("%Y-%m-%dT%H:%M:%SZ")
SERIES_DEF = [("cohort", "“cohort”", "invented"), ("runde", "round marker", "invented"), ("meldeformat", "full report format", "invented"),
              ("sig_endzeile", "signature line", "brought"), ("please_relay", "request formula (“please relay”)", "brought")]
def block(q, label, n_names, n_excluded):
    kept = q[q.n >= MIN_N]; masked = q[q.n < MIN_N]; series = []
    for key, lab, fam in SERIES_DEF:
        pts = [[iso(t), (None if n < MIN_N else float(v)), int(n)] for t, v, n in zip(q.f, q[key], q.n)]
        series.append({"key": key, "label": lab, "family": fam, "points": pts, "first": float(q[key].iloc[0]),
                       "max": float(kept[key].max()), "max_at": iso(kept.loc[kept[key].idxmax(), "f"])})
    return {"label": label, "n_names_population": int(n_names), "n_names_excluded": int(n_excluded),
            "n_windows_total": int(len(q)), "n_windows_kept": int(len(kept)),
            "masked_windows": [[iso(t), int(n)] for t, n in zip(masked.f, masked.n)],
            "window_n": [[iso(t), int(n)] for t, n in zip(q.f, q.n)], "names_total_kept": int(kept.n.sum()), "series": series}
fig = {
    "figure": "3b", "title": "Format convergence in newcomers' first contributions — full sample vs. names without explicit contact trace",
    "x": {"name": "6-h window (wall time, UTC)"}, "y": {"name": "share of first contributions carrying the feature, %"}, "min_n": MIN_N,
    "filter_rule": {
        "a_prior_reading": "first revision quotes a CamelCase page name (>=12 chars) of an already existing page created by another name (paper_lernkurve_q2_inhaltlicher_lesebeweis.csv, n_fremdseiten_genannt>0)",
        "b_cascade_copier": "name appears as kopierer_label in paper_prozess_zitatkaskade_kopien.csv (verbatim line >=80 chars previously written by another name)",
        "c_rendezvous_language": "name appears in paper_lernkurve_q5_rendezvous_treffer.csv (regex hits for new-agent/start-here/index/naming/rendezvous/search/recentchanges/guessable phrases)",
        "combination": "no_contact_trace excludes a∪b∪c at any time; no_contact_trace_firstline excludes only traces located in the very first revision",
        "counts": {"coordpop": len(cp), "a": len(trace_a & cp), "b_any": len(trace_b_any & cp), "b_first": len(trace_b_first & cp),
                   "c_any": len(trace_c_any & cp), "c_first": len(trace_c_first & cp), "union_any": len(trace_any & cp), "union_first": len(trace_first & cp)},
    },
    "variants": {vname: block(FT[FT.variant == vname].reset_index(drop=True), vname, len(labs), len(cp) - len(labs)) for vname, labs in VAR2.items()},
    "marks": [{"kind": "vline", "t": iso(T0), "text": "16 Jun 09:27 — coordination begins"},
              {"kind": "span", "t0": iso(T0), "t1": iso(T0 + pd.Timedelta(hours=24)), "text": "first 24 h"}],
    "sources": {"data": "paper_robust_format_gefiltert_6h.csv (variant, f, cohort, runde, meldeformat, sig_endzeile, please_relay, n)",
                "script": "analyse/scripts/65_adoption_robust.py", "seed": SEED},
}
os.makedirs(FIGDATA, exist_ok=True)
with open(os.path.join(FIGDATA, "fig3b_format_filtered.json"), "w", encoding="utf-8") as fh:
    json.dump(fig, fh, ensure_ascii=False, indent=1)
L(f"-> {os.path.join(FIGDATA, 'fig3b_format_filtered.json')}")
LOG.close()
