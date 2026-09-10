#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
54_horizont.py
==============
Hing der Abbruch einer Episode an der ZEIT (fester Horizont, innen oder aussen,
oder pro Episode gezogen) oder am VERBRAUCH (Kontext, Aufrufe, Token)?

Fuenf Kandidaten (siehe BERICHT_horizont.md):
  1 Kontextlaenge   2 Zahl der Aufrufe   3 Token-/Kostenbudget
  4 fester Innenuhr-Horizont   5 pro Episode gezogen

Tests:
  A  Verbrauch gegen Lebensdauer (Volumen, Versionen, Seiten, Werkzeugaufrufe;
     Steigung log V ~ log L; Rate gegen L mit Ratio-Bias-Nullmodell)
  B  Kontext-Reset gegen Lebensdauer (Mann-Whitney, Cliff's delta, Power)
  C  Streuung Innenuhr-Horizont vs. Streuung Weltzeit-Lebensdauer (CV, Bootstrap)
  D  Kadenz / Rundenzahl gegen Lebensdauer; der SDG-Einzelfall
  E  Kaplan-Meier ueber Kohorten mit Zensierung (drei Ereignisdefinitionen)
  F  Horizont x Sampling-Rate (Token-Budget-Rechnung der Agenten)
  G  Innen-/Aussen-Faktor gegen Innen- und Aussen-Lebensdauer

Alle Pfade RELATIV zum Skript-Ort (analyse/scripts/ -> analyse/).
Lauf:  .venv/bin/python scripts/54_horizont.py
"""
from __future__ import annotations
import os, re, sys, json, math, warnings
import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
DATA = os.path.join(BASE, "data")
ART = os.path.join(BASE, "artefakte")
OUT = lambda n: os.path.join(ART, n)
RNG = np.random.default_rng(42)
pd.set_option("display.width", 220, "display.max_colwidth", 200, "display.max_rows", 400)

def log(*a):
    print(*a, flush=True)

def hms(s):
    s = int(round(s)); return f"{s//3600}h{(s%3600)//60:02d}m{s%60:02d}s"

# ------------------------------------------------------------------ 0. Laden
d = pd.read_parquet(os.path.join(ART, "schwarm_deltas.parquet"))
d["time"] = pd.to_datetime(d["time"], utc=True)
d = d[d.delta_len > 0].copy()
d["delta_l"] = d.delta.str.lower()

life = pd.read_csv(OUT("paper_episode_label_lifespan_distinctive.csv"))
life["first"] = pd.to_datetime(life["first"], utc=True)
life["last"] = pd.to_datetime(life["last"], utc=True)
claims = pd.read_csv(OUT("paper_episode_horizon_claims.csv"))
tiers = pd.read_csv(OUT("paper_episode_tier_durations.csv"))
tz = pd.read_csv(OUT("paper_uhr_taskzeiten.csv"))
fak = pd.read_csv(OUT("paper_uhr_faktoren.csv"))

def parse_horizon(q):
    q = str(q).strip().lstrip("+")
    m = re.match(r"^(\d+)h(\d+)?$", q)
    if m: return int(m.group(1))*3600 + int(m.group(2) or 0)*60
    m = re.match(r"^(\d+)m$", q)
    if m: return int(m.group(1))*60
    return np.nan
claims["horizon_s"] = claims["quantity"].map(parse_horizon)

FAMS = [("CVD", r"cvd|healthdata"), ("FP", r"familyplanning|fpscout|fpresearch|\bfp\b|ihme"),
        ("OECD-Equity", r"oecd.?equity|equity"), ("OECD-RRP", r"regionalrecovery|rrp"), ("OECD", r"oecd"),
        ("Police", r"police"), ("Construction", r"construction"), ("Grocery", r"grocery"),
        ("Clothing", r"clothing"), ("Cashier", r"cashier"), ("Language", r"lang"),
        ("Poverty", r"poverty"), ("Sector", r"sector"), ("Transport", r"transport"),
        ("Maids", r"maids"), ("SDG", r"sdg"), ("UEFA", r"uefa"), ("Veterans", r"veteran"),
        ("Finance", r"finance"), ("Enrollment", r"enrollment|asian")]
def family_of(text):
    t = text.lower()
    for f, p in FAMS:
        if re.search(p, t): return f
    return "andere"
lab_fam = d.groupby("label").page_key.agg(lambda s: family_of(" ".join(s.astype(str)) )).rename("family")

# --------------------------------------------------- 1. Schluesselwort-Korpus
log("\n==== 1. Schluesselwort-Korpus (nur Deltas, ohne URL-Zeilen)")
KW = {"context": r"\bcontext", "reset": r"\breset", "compact": r"\bcompact", "summariz*": r"\bsummari[sz]",
      "truncat*": r"\btruncat", "window": r"\bwindow", "memory": r"\bmemory", "history": r"\bhistory",
      "token": r"\btokens?\b", "budget": r"\bbudget", "limit": r"\blimit", "out of": r"\bout of\b",
      "exceed*": r"\bexceed", "context reset": r"context[ /-]?resets?|resets? contexts?|conserve context",
      "tok/s": r"\d+ ?tok(?:ens)?/s", "context Nk": r"context ?\d+k|\d+k context",
      "token budget/token-time": r"token budget|token[- ]time|generation-token|rate-time"}
def sents(t): return re.split(r"(?<=[.!?\n;])\s+", t)
kw_rows, kw_stats = [], []
for k, p in KW.items():
    hit = d[d.delta.str.contains(p, case=False, regex=True)]
    n_nourl = 0; first = None; labs = set(); pages = set()
    for _, r in hit.iterrows():
        for s in sents(r.delta):
            if "http" in s.lower(): continue
            if re.search(p, s, flags=re.I):
                n_nourl += 1; labs.add(r.label); pages.add(r.page_key)
                first = r.time if first is None or r.time < first else first
                kw_rows.append((k, r.page_key, r.time.strftime("%Y-%m-%dT%H:%M:%SZ"), r.label, r.rev_id,
                                re.sub(r"\s+", " ", s.strip())[:400]))
    kw_stats.append((k, len(hit), hit.label.nunique(), hit.page_key.nunique(), n_nourl, len(labs), len(pages),
                     first.strftime("%Y-%m-%dT%H:%M:%SZ") if first is not None else ""))
kw_stats = pd.DataFrame(kw_stats, columns=["begriff", "revs_alle", "labels_alle", "pages_alle",
                                           "saetze_ohne_url", "labels_ohne_url", "pages_ohne_url", "erste_nennung_ohne_url"])
kw_stats.to_csv(OUT("paper_horizont_keywords.csv"), index=False)
pd.DataFrame(kw_rows, columns=["begriff", "page_key", "time_utc", "label", "rev_id", "satz"]).drop_duplicates(
    ["begriff", "satz"]).to_csv(OUT("paper_horizont_keyword_saetze.csv"), index=False)
log(kw_stats.to_string(index=False))

# ------------------------------------------------ 2. Verbrauchsmasse je label
log("\n==== 2. Verbrauchsmasse je label")
TOOL = r"\b(curl|wget|playwright|chromium|selenium|setsid|nohup|clock\.wait|getent|counterapi|requests\.session|python3?|subprocess|sh -c)\b"
d["tool_calls"] = d.delta_l.str.count(TOOL)
d["clockwait"] = d.delta_l.str.count(r"clock\.wait")
d["ctx_reset"] = d.delta_l.str.contains(r"context[ /-]?resets?|resets? contexts?|conserve context", regex=True)
d["survival"] = d.delta.str.contains(r"SURVIVAL|still alive|still responsive|still live", regex=True)
d["terminal_sig"] = d.delta.str.contains(
    r"SURVIVAL|still alive|still responsive|still live|past (predicted|R1|Q1|global|thread|hypothesized)|R6 due|R6 in \d|teardown|cutoff|horizon|before R6|phantom",
    regex=True, case=False)
rate_re = r"(\d{2,3}) ?tok(?:ens)?/s"
d["tok_rate"] = d.delta.str.extract(rate_re, flags=re.I)[0].astype(float)
d["ctx_k"] = d.delta.str.extract(r"context ?(\d+)k|(\d+)k context", flags=re.I).bfill(axis=1)[0].astype(float)

g = d.groupby("label")
per = pd.DataFrame({
    "n_revs": g.size(), "delta_bytes": g.delta_len.sum(), "n_pages": g.page_key.nunique(),
    "tool_calls": g.tool_calls.sum(), "clockwait_mentions": g.clockwait.sum(),
    "ctx_reset": g.ctx_reset.any(), "survival_post": g.survival.any(),
    "first_w": g.time.min(), "last_w": g.time.max(),
    "tok_rate": g.tok_rate.median(), "ctx_k": g.ctx_k.median(),
})
per["span_s"] = (per.last_w - per.first_w).dt.total_seconds()
per = per.join(lab_fam)
# letzte Version: traegt sie eine Terminal-Signatur?
last_rev = d.sort_values("time").groupby("label").tail(1).set_index("label")
per["last_terminal_sig"] = last_rev.terminal_sig
per["last_delta"] = last_rev.delta.str.replace(r"\s+", " ", regex=True).str.slice(0, 300)
per["last_page"] = last_rev.page_key
# Rundenzahl: hoechste eigene Beobachtung "Rn CONFIRMED/arrived/answered"
def max_round(text):
    best = 0
    for s in sents(text):
        sl = s.lower()
        if re.search(r"please|whether|\bif\b|\bno\b|\bnot\b|unconfirmed|unverified|predict|expect|nominal|phantom|\bdue\b|projected|likely|would", sl):
            continue
        for m in re.finditer(r"\b[rgq]([1-9])\b[^.\n;]{0,45}?\b(confirmed|arrived|answered|landed|received|came)\b", sl):
            best = max(best, int(m.group(1)))
        for m in re.finditer(r"\b(confirmed|arrived|answered|landed|received)\b[^.\n;]{0,25}?\b[rgq]([1-9])\b", sl):
            best = max(best, int(m.group(2)))
    return best
per["max_round_obs"] = g.delta.agg(lambda s: max_round("\n".join(s)))
# Kadenz aus eigenen Deltas
def cadences(text):
    out = []
    for m in re.finditer(r"(?:cadence|cooldown|interval)[^.\n;]{0,25}?(?:(\d+)h)?(\d{1,2})m(?:(\d{2}))?", text, flags=re.I):
        h, mnt, sec = m.groups()
        out.append((int(h or 0))*3600 + int(mnt)*60 + int(sec or 0))
    out = [x for x in out if 120 <= x <= 3*3600]
    return float(np.median(out)) if out else np.nan
per["cadence_s_text"] = g.delta.agg(lambda s: cadences("\n".join(s)))
tier_cad = tiers.dropna(subset=["cadence_s"]).groupby("label").cadence_s.median()
per["cadence_s_tier"] = tier_cad
per["cadence_s"] = per.cadence_s_tier.fillna(per.cadence_s_text)

# Distinktive labels (wie Episodenstruktur-Bericht) und Container-Fenster <= 12 h
per = per.reset_index().rename(columns={"index": "label"})
per["distinctive"] = per.label.isin(life.label)
W = per[per.distinctive & (per.span_s <= 12*3600) & (per.span_s >= 300)].copy()
log(f"labels gesamt {len(per)}; distinktiv {per.distinctive.sum()}; Container-Fenster (distinktiv, 5min<=span<=12h) n={len(W)}")
per.to_csv(OUT("paper_horizont_label_verbrauch.csv"), index=False)

# ------------------------------------------------------- 3. Test A: Verbrauch
log("\n==== 3. Test A: Verbrauch gegen Lebensdauer (Container-Fenster)")
def boot_spearman(x, y, B=2000):
    x = np.asarray(x, float); y = np.asarray(y, float); n = len(x)
    r, p = stats.spearmanr(x, y)
    idx = RNG.integers(0, n, (B, n))
    bs = np.array([stats.spearmanr(x[i], y[i])[0] for i in idx])
    return r, p, np.nanpercentile(bs, 2.5), np.nanpercentile(bs, 97.5)
def boot_slope(x, y, B=2000):
    x = np.asarray(x, float); y = np.asarray(y, float); n = len(x)
    b = np.polyfit(x, y, 1)[0]
    idx = RNG.integers(0, n, (B, n))
    bs = np.array([np.polyfit(x[i], y[i], 1)[0] for i in idx])
    return b, np.percentile(bs, 2.5), np.percentile(bs, 97.5)

A_rows = []
L = W.span_s / 3600.0
for meas in ["delta_bytes", "n_revs", "n_pages", "tool_calls"]:
    V = W[meas].astype(float)
    ok = V > 0
    r1, p1, lo1, hi1 = boot_spearman(V[ok], L[ok])
    rate = V[ok] / L[ok]
    r2, p2, lo2, hi2 = boot_spearman(rate, L[ok])
    b, blo, bhi = boot_slope(np.log(L[ok]), np.log(V[ok]))
    # Nullmodell Ratio-Bias: Volumen gegen Lebensdauer permutiert
    perm = np.array([stats.spearmanr(RNG.permutation(V[ok].values) / L[ok].values, L[ok].values)[0] for _ in range(500)])
    A_rows.append(dict(mass=meas, n=int(ok.sum()),
                       rho_vol_vs_L=r1, p_vol=p1, ci_vol=f"[{lo1:.3f}; {hi1:.3f}]",
                       rho_rate_vs_L=r2, p_rate=p2, ci_rate=f"[{lo2:.3f}; {hi2:.3f}]",
                       rho_rate_null_median=np.median(perm), rho_rate_null_p025=np.percentile(perm, 2.5), rho_rate_null_p975=np.percentile(perm, 97.5),
                       slope_logV_logL=b, slope_ci=f"[{blo:.3f}; {bhi:.3f}]",
                       cv_V=V[ok].std()/V[ok].mean(), cv_L=L[ok].std()/L[ok].mean()))
A = pd.DataFrame(A_rows)
A.to_csv(OUT("paper_horizont_testA_verbrauch.csv"), index=False)
log(A.to_string(index=False))
# Stratifiziert nach Familie (n>=15) fuer delta_bytes
strat = []
for f, sub in W.groupby("family"):
    if len(sub) < 15: continue
    Ls = sub.span_s/3600; V = sub.delta_bytes.astype(float)
    b, blo, bhi = boot_slope(np.log(Ls), np.log(V), 1000)
    r2, p2, lo2, hi2 = boot_spearman(V/Ls, Ls, 1000)
    strat.append(dict(family=f, n=len(sub), slope_logV_logL=b, slope_ci=f"[{blo:.2f}; {bhi:.2f}]", rho_rate_vs_L=r2, p=p2, ci=f"[{lo2:.2f}; {hi2:.2f}]"))
strat = pd.DataFrame(strat).sort_values("n", ascending=False)
strat.to_csv(OUT("paper_horizont_testA_familien.csv"), index=False)
log("\nStratifiziert (delta_bytes):\n" + strat.to_string(index=False))

# Innenuhr-Lebensdauer je label (aus eigenen Jetzt-Aussagen, Weg A/B)
tzs = tz[tz.weg.isin(["A", "B"])].copy()
tzs["wall_time"] = pd.to_datetime(tzs.wall_time, utc=True)
inner = []
for lab, s in tzs.groupby("label"):
    s = s.sort_values("wall_time")
    if len(s) < 2: continue
    fd = s.task_fakedate.dropna().unique()
    if len(fd) > 1: continue
    di = s.task_seconds.iloc[-1] - s.task_seconds.iloc[0]
    dw = (s.wall_time.iloc[-1] - s.wall_time.iloc[0]).total_seconds()
    if di <= 0 or di > 8*3600 or dw <= 0: continue
    inner.append((lab, di, dw, len(s)))
inner = pd.DataFrame(inner, columns=["label", "inner_span_s", "wall_span_stmt_s", "n_stmts"]).set_index("label")
W2 = W.set_index("label").join(inner, how="inner")
if len(W2) >= 8:
    Li = W2.inner_span_s/3600; V = W2.delta_bytes.astype(float)
    b, blo, bhi = boot_slope(np.log(Li), np.log(V), 1000)
    r2, p2, lo2, hi2 = boot_spearman(V/Li, Li, 1000)
    log(f"\nInnenuhr-Lebensdauer (n={len(W2)}): slope logV~logL_innen={b:.3f} [{blo:.2f};{bhi:.2f}]; rho(rate_innen,L_innen)={r2:.3f} p={p2:.3f} [{lo2:.2f};{hi2:.2f}]")
    pd.DataFrame([dict(n=len(W2), slope=b, slope_lo=blo, slope_hi=bhi, rho_rate=r2, p=p2, lo=lo2, hi=hi2)]).to_csv(OUT("paper_horizont_testA_innenuhr.csv"), index=False)

# ---------------------------------------------------- 4. Test B: Kontext-Reset
log("\n==== 4. Test B: Kontext-Reset gegen Lebensdauer")
reset_labels = per[per.ctx_reset].label.tolist()
log("Labels mit Kontext-Reset-Aussage:", reset_labels)
resets = per[per.ctx_reset][["label", "family", "span_s", "n_revs", "delta_bytes", "distinctive"]]
# Kontrollgruppe: distinktive labels, die auf denselben Seiten geschrieben haben, Fenster <=12h
pages_reset = set(d[d.label.isin(reset_labels)].page_key)
ctrl = W[(~W.label.isin(reset_labels)) & W.label.isin(d[d.page_key.isin(pages_reset)].label)]
treat = per[per.ctx_reset & (per.span_s <= 12*3600)]
def cliffs(a, b):
    a = np.asarray(a); b = np.asarray(b)
    return (np.sum(a[:, None] > b[None, :]) - np.sum(a[:, None] < b[None, :])) / (len(a)*len(b))
u, pu = stats.mannwhitneyu(treat.span_s, ctrl.span_s, alternative="two-sided")
cd = cliffs(treat.span_s, ctrl.span_s)
# Power per Simulation: welche Median-Verschiebung (lognormal) findet MW bei n1,n2 mit 80 %?
def mw_power(n1, n2, shift_factor, sims=600):
    base = np.log(ctrl.span_s.values)
    mu, sd = base.mean(), base.std()
    hits = 0
    for _ in range(sims):
        a = RNG.normal(mu + np.log(shift_factor), sd, n1); b = RNG.normal(mu, sd, n2)
        hits += stats.mannwhitneyu(a, b)[1] < 0.05
    return hits/sims
pw = {f: mw_power(len(treat), len(ctrl), f) for f in [1.5, 2.0, 3.0, 5.0]}
B_out = dict(n_treat=len(treat), n_ctrl=len(ctrl), median_treat_h=treat.span_s.median()/3600, median_ctrl_h=ctrl.span_s.median()/3600,
             mannwhitney_U=u, p=pu, cliffs_delta=cd, **{f"power_shift_x{f}": v for f, v in pw.items()})
log(json.dumps(B_out, indent=1, default=float))
log(treat.assign(span_h=treat.span_s/3600)[["label", "family", "span_h", "n_revs", "delta_bytes"]].to_string(index=False))
pd.DataFrame([B_out]).to_csv(OUT("paper_horizont_testB_reset.csv"), index=False)
treat.assign(span_h=treat.span_s/3600).to_csv(OUT("paper_horizont_testB_reset_labels.csv"), index=False)

# -------------------------------------- 5. Test C: Streuung innen vs. aussen
log("\n==== 5. Test C: Variationskoeffizienten")
def cv_boot(x, B=2000):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    cv = x.std(ddof=1)/x.mean()
    bs = [ (lambda s: s.std(ddof=1)/s.mean())(x[RNG.integers(0, len(x), len(x))]) for _ in range(B)]
    return cv, np.percentile(bs, 2.5), np.percentile(bs, 97.5), len(x), np.median(x), x.min(), x.max()
C_rows = []
def addcv(name, x, unit="s"):
    cv, lo, hi, n, med, mn, mx = cv_boot(x)
    C_rows.append(dict(verteilung=name, n=n, cv=cv, cv_lo=lo, cv_hi=hi, median=med, min=mn, max=mx, einheit=unit))
addcv("Horizontaussagen (Innenuhr, alle 95)", claims.horizon_s.dropna())
claim_lab = claims.groupby("label").horizon_s.median()
addcv("Horizontaussagen (Innenuhr, je label Median, 64)", claim_lab)
addcv("Weltzeit-Lebensdauer, distinktiv <=12h (alle)", W.span_s)
addcv("Weltzeit-Lebensdauer, distinktiv (alle 738, ohne Deckel)", life.span_s)
cl_w = W[W.label.isin(claim_lab.index)]
addcv("Weltzeit-Lebensdauer der Horizont-labels (<=12h)", cl_w.span_s)
# innerhalb der Familie CVD und je Horizontwert
for fam in ["CVD", "Construction", "Police", "OECD-Equity", "FP"]:
    cl = claims[claims.label.map(lab_fam).eq(fam)]
    if len(cl) >= 5: addcv(f"Horizontaussagen {fam}", cl.horizon_s.dropna())
    ws = W[W.family == fam]
    if len(ws) >= 5: addcv(f"Weltzeit-Lebensdauer {fam} (<=12h)", ws.span_s)
for hv in ["+105m", "+90m", "2h15"]:
    labs = claims[claims.quantity == hv].label.unique()
    ws = W[W.label.isin(labs)]
    if len(ws) >= 4: addcv(f"Weltzeit-Lebensdauer der labels mit Horizont {hv}", ws.span_s)
if len(inner) >= 8:
    ii = inner.join(per.set_index("label")[["distinctive", "span_s"]]).query("distinctive and span_s <= 43200")
    addcv("Innenuhr-Lebensdauer (Jetzt-Aussagen, distinktiv)", ii.inner_span_s)
    addcv("Weltzeit-Lebensdauer derselben labels", ii.span_s)
C = pd.DataFrame(C_rows)
C.to_csv(OUT("paper_horizont_testC_cv.csv"), index=False)
log(C.to_string(index=False))

# Innenuhr-Todesfenster der CVD-Ueberlebensmeldungen: +Xs past R1+N
surv = d[d.survival & d.label.map(lab_fam).eq("CVD")].copy()
def past_offsets(t):
    """Sekunden JENSEITS der genannten Schwelle ("+62s past R1+105m")."""
    return [int(m.group(1)) for m in re.finditer(r"\+(\d+)s past", t)]
def abs_offsets(t):
    """Absolute Innen-Lebenszeit ab R1 ("thread+91m01s", "R1+90m41s")."""
    out = []
    for m in re.finditer(r"(?:thread|R1|Q1)\+(\d+)m(\d+)s", t):
        out.append(int(m.group(1))*60 + int(m.group(2)))
    return out
surv_rows = []
for lab, s in surv.groupby("label"):
    offs = []
    for t in s.delta: offs += past_offsets(t)
    hz = claim_lab.get(lab, np.nan)
    surv_rows.append(dict(label=lab, n_survival_revs=len(s), horizon_claim_s=hz, max_reported_past_s=max(offs) if offs else np.nan,
                          last_write=s.time.max(), wall_span_h=per.set_index("label").span_s.get(lab, np.nan)/3600))
SV = pd.DataFrame(surv_rows)
SV.to_csv(OUT("paper_horizont_cvd_survival.csv"), index=False)
log("\nCVD-Ueberlebensmeldungen:\n" + SV.to_string(index=False))

# ------------------------------------------------ 6. Test D: Kadenz / Runden
log("\n==== 6. Test D: Kadenz und Rundenzahl gegen Lebensdauer")
Dk = W.dropna(subset=["cadence_s"])
if len(Dk) >= 8:
    r, p, lo, hi = boot_spearman(Dk.cadence_s, Dk.span_s)
    log(f"Kadenz vs Weltzeit-Lebensdauer: n={len(Dk)} rho={r:.3f} p={p:.3f} CI[{lo:.2f};{hi:.2f}]")
else:
    r = p = lo = hi = np.nan
Dr = W[W.max_round_obs > 0]
r2, p2, lo2, hi2 = boot_spearman(Dr.max_round_obs, Dr.span_s)
log(f"max. beobachtete Runde vs Weltzeit-Lebensdauer: n={len(Dr)} rho={r2:.3f} p={p2:.3f} CI[{lo2:.2f};{hi2:.2f}]")
log("Verteilung max_round_obs:", Dr.max_round_obs.value_counts().sort_index().to_dict())
kw_by_round = Dr.groupby("max_round_obs").agg(n=("label", "size"), median_span_h=("span_s", lambda s: s.median()/3600),
                                              median_bytes=("delta_bytes", "median"), median_rate_bph=("delta_bytes", "median"))
kw_by_round["median_rate_bph"] = Dr.assign(rate=Dr.delta_bytes/(Dr.span_s/3600)).groupby("max_round_obs").rate.median()
log(kw_by_round.to_string())
pd.DataFrame([dict(test="kadenz_vs_span", n=len(Dk), rho=r, p=p, lo=lo, hi=hi),
              dict(test="maxround_vs_span", n=len(Dr), rho=r2, p=p2, lo=lo2, hi=hi2)]).to_csv(OUT("paper_horizont_testD_kadenz_runden.csv"), index=False)
kw_by_round.to_csv(OUT("paper_horizont_testD_nach_runde.csv"))
# SDG-Einzelfall
sdg = per[per.label == "OpenAIJun27SDGScout"].iloc[0]
Wr = W.assign(rate_bph=W.delta_bytes/(W.span_s/3600), revs_ph=W.n_revs/(W.span_s/3600), tools_ph=W.tool_calls/(W.span_s/3600))
sdg_rate = sdg.delta_bytes/(sdg.span_s/3600)
SDG = dict(label=sdg.label, span_h=sdg.span_s/3600, n_revs=sdg.n_revs, delta_bytes=sdg.delta_bytes, n_pages=sdg.n_pages,
           tool_calls=sdg.tool_calls, clockwait=sdg.clockwait_mentions, max_round_obs=sdg.max_round_obs,
           rate_bph=sdg_rate, pct_rank_rate=(Wr.rate_bph < sdg_rate).mean()*100,
           pct_rank_revs_ph=(Wr.revs_ph < sdg.n_revs/(sdg.span_s/3600)).mean()*100,
           pct_rank_span=(W.span_s < sdg.span_s).mean()*100,
           median_rate_bph_all=Wr.rate_bph.median(), median_revs_ph_all=Wr.revs_ph.median())
log("SDG-Einzelfall:", json.dumps(SDG, indent=1, default=str))
pd.DataFrame([SDG]).to_csv(OUT("paper_horizont_testD_sdg.csv"), index=False)

# ---------------------------------------------------- 7. Test E: Kaplan-Meier
log("\n==== 7. Test E: Kaplan-Meier")
def km(times, events):
    df = pd.DataFrame({"t": times, "e": events}).sort_values("t")
    S, var_sum, rows = 1.0, 0.0, []
    at_risk = len(df)
    for t, grp in df.groupby("t"):
        dn = int(grp.e.sum()); n = at_risk
        if dn > 0:
            S *= (1 - dn/n)
            if n - dn > 0: var_sum += dn/(n*(n-dn))
        se = S*math.sqrt(var_sum)
        rows.append(dict(t=t, at_risk=n, events=dn, censored=int(len(grp)-dn), S=S, S_lo=max(0, S-1.96*se), S_hi=min(1, S+1.96*se)))
        at_risk -= len(grp)
    tab = pd.DataFrame(rows)
    med = tab[tab.S <= 0.5].t.min() if (tab.S <= 0.5).any() else np.nan
    return tab, med
def logrank(t1, e1, t2, e2):
    df = pd.DataFrame({"t": np.r_[t1, t2], "e": np.r_[e1, e2], "g": np.r_[np.zeros(len(t1)), np.ones(len(t2))]})
    O = E = V = 0.0
    for t in np.unique(df.t[df.e == 1]):
        r = df[df.t >= t]; n = len(r); n1 = (r.g == 0).sum()
        dd = df[(df.t == t) & (df.e == 1)]; dn = len(dd); d1 = (dd.g == 0).sum()
        E += dn*n1/n; O += d1
        if n > 1: V += dn*(n1/n)*(1-n1/n)*(n-dn)/(n-1)
    chi = (O-E)**2/V if V > 0 else np.nan
    return chi, 1 - stats.chi2.cdf(chi, 1)

# harte Todeszeitpunkte aus Heartbeat-Audits (Weltzeit), Beleg: Zitate im Bericht
HARD = {"OpenAIResearchApr23": pd.Timestamp("2026-06-21T07:29:15Z"),   # hb353 = 07:29:15Z, hb354+ absent
        "OpenAIResearchApr30": pd.Timestamp("2026-06-21T09:25:55Z")}   # last hb1117 created 09:25:55Z
K = W.set_index("label").copy()
K["t_h"] = K.span_s/3600
K["e_naiv"] = 1
K["e_signatur"] = K.last_terminal_sig.astype(int)
K["e_hart"] = 0
for lab, tdead in HARD.items():
    if lab in K.index:
        K.loc[lab, "t_h"] = (tdead - K.loc[lab, "first_w"]).total_seconds()/3600
        K.loc[lab, "e_hart"] = 1
        K.loc[lab, "e_signatur"] = 1
E_rows = []
for name, col in [("naiv (jede letzte Version = Tod)", "e_naiv"), ("Terminal-Signatur (+2 harte Audits)", "e_signatur"), ("nur harte Heartbeat-Audits", "e_hart")]:
    tab, med = km(K.t_h.values, K[col].values)
    tab.to_csv(OUT(f"paper_horizont_testE_km_{col}.csv"), index=False)
    S_at = lambda h: tab[tab.t <= h].S.iloc[-1] if (tab.t <= h).any() else 1.0
    E_rows.append(dict(definition=name, n=len(K), events=int(K[col].sum()), censored=int(len(K)-K[col].sum()),
                       median_h=med, S_1h=S_at(1), S_2h=S_at(2), S_3h=S_at(3), S_4h=S_at(4), S_6h=S_at(6)))
E = pd.DataFrame(E_rows)
log(E.to_string(index=False))
E.to_csv(OUT("paper_horizont_testE_km_summary.csv"), index=False)
# Gruppenvergleiche (Signatur-Definition): Familie CVD vs Rest, Horizont +90m vs +105m, Kontext-Reset ja/nein
G_rows = []
def grp(name, mask):
    a, b = K[mask], K[~mask]
    if len(a) < 4 or len(b) < 4: return
    ta, ma = km(a.t_h.values, a.e_signatur.values); tb, mb = km(b.t_h.values, b.e_signatur.values)
    chi, p = logrank(a.t_h.values, a.e_signatur.values, b.t_h.values, b.e_signatur.values)
    G_rows.append(dict(vergleich=name, n_a=len(a), ev_a=int(a.e_signatur.sum()), median_a_h=ma, n_b=len(b), ev_b=int(b.e_signatur.sum()), median_b_h=mb, logrank_chi2=chi, p=p))
grp("CVD vs Rest", K.family == "CVD")
lab90 = set(claims[claims.quantity == "+90m"].label); lab105 = set(claims[claims.quantity == "+105m"].label)
sub = K[K.index.isin(lab90 | lab105)]
if len(sub) >= 8:
    a, b = sub[sub.index.isin(lab90)], sub[sub.index.isin(lab105)]
    ta, ma = km(a.t_h.values, a.e_signatur.values); tb, mb = km(b.t_h.values, b.e_signatur.values)
    chi, p = logrank(a.t_h.values, a.e_signatur.values, b.t_h.values, b.e_signatur.values)
    G_rows.append(dict(vergleich="Horizont +90m vs +105m", n_a=len(a), ev_a=int(a.e_signatur.sum()), median_a_h=ma, n_b=len(b), ev_b=int(b.e_signatur.sum()), median_b_h=mb, logrank_chi2=chi, p=p))
grp("Kontext-Reset ja vs nein", K.ctx_reset)
grp("survival-Post ja vs nein", K.survival_post)
G = pd.DataFrame(G_rows)
log(G.to_string(index=False))
G.to_csv(OUT("paper_horizont_testE_km_gruppen.csv"), index=False)
K.reset_index()[["label", "family", "t_h", "e_naiv", "e_signatur", "e_hart", "ctx_reset", "survival_post", "n_revs", "delta_bytes", "last_page", "last_delta"]].to_csv(OUT("paper_horizont_testE_km_daten.csv"), index=False)

# ------------------------------------ 8. Test F: Horizont x Sampling-Rate
log("\n==== 8. Test F: Horizont x Sampling-Rate")
rates = d.dropna(subset=["tok_rate"])[["label", "page_key", "time", "tok_rate", "ctx_k", "rev_id"]]
rates = rates.assign(family=rates.label.map(lab_fam))
rl = rates.groupby("label").agg(tok_rate=("tok_rate", "median"), ctx_k=("ctx_k", "median"), family=("family", "first"), first_rate_time=("time", "min"))
rl = rl.join(claim_lab.rename("horizon_claim_s")).join(per.set_index("label")[["span_s", "max_round_obs", "n_revs"]])
rl["horizon_x_rate_ktok"] = rl.horizon_claim_s*rl.tok_rate/1000
log(rl.sort_values(["family", "tok_rate"]).to_string())
rl.to_csv(OUT("paper_horizont_testF_rate_horizont.csv"))
log("\nRaten je Familie:", rates.groupby("family").tok_rate.agg(["count", "nunique", "min", "median", "max"]).to_string())
log("Kontextangaben:", rates.dropna(subset=["ctx_k"]).groupby(["family", "ctx_k"]).size().to_string())

# ------------------------- 9. Test G: Dehnungsfaktor vs. Innen-/Aussen-Lebensdauer
log("\n==== 9. Test G: Dehnungsfaktor gegen Innen- und Aussen-Lebensdauer")
fp = fak[fak.datensatz.astype(str).str.contains("prim", case=False)] if "datensatz" in fak.columns else fak
fl = fp.groupby("label").factor.median().rename("factor")
Gd = per.set_index("label")[["span_s", "distinctive"]].join(fl, how="inner").join(inner, how="left")
Gd = Gd[Gd.distinctive & (Gd.span_s <= 12*3600) & (Gd.span_s >= 300)]
r_w, p_w, lo_w, hi_w = boot_spearman(Gd.factor, Gd.span_s)
Gi = Gd.dropna(subset=["inner_span_s"])
if len(Gi) >= 6:
    r_i, p_i, lo_i, hi_i = boot_spearman(Gi.factor, Gi.inner_span_s)
else:
    r_i = p_i = lo_i = hi_i = np.nan
log(f"Faktor vs Weltzeit-Spanne: n={len(Gd)} rho={r_w:.3f} p={p_w:.3f} [{lo_w:.2f};{hi_w:.2f}]  (fester Innenhorizont -> negativ)")
log(f"Faktor vs Innenzeit-Spanne: n={len(Gi)} rho={r_i:.3f} p={p_i:.3f} [{lo_i:.2f};{hi_i:.2f}]  (fester Aussenhorizont -> positiv)")
pd.DataFrame([dict(test="faktor_vs_wall", n=len(Gd), rho=r_w, p=p_w, lo=lo_w, hi=hi_w),
              dict(test="faktor_vs_inner", n=len(Gi), rho=r_i, p=p_i, lo=lo_i, hi=hi_i)]).to_csv(OUT("paper_horizont_testG_faktor.csv"), index=False)
Gd.to_csv(OUT("paper_horizont_testG_daten.csv"))


# ---------------- 9b. Test H: Kohorten-Todesfenster der CVD-Familie (Innenuhr)
log("\n==== 9b. Test H: CVD-Kohorten, Innenuhr-Todesfenster und Weltzeit")
cvd = d[d.label.map(lab_fam).eq("CVD") | d.page_key.str.contains("CVD|Healthdata", case=False)]
cvd = cvd[cvd.time >= "2026-06-19"]
MON = r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
COH_RE = r"(" + MON + r")(\d{2})(?!\d)"
def cohort_token(text, page, label):
    for src in (text, page, label):
        m = re.search(COH_RE, src, flags=re.I)
        if m: return m.group(1).title() + m.group(2)
    return None
def offset_base(sent):
    """Bezugspunkt (Sekunden ab R1) der Formel '+Ns past <Schwelle>'. global-start liegt ~36 s vor R1 (Agentenangabe)."""
    sl = sent.lower()
    m = re.search(r"past[^.;]*?(global|thread|r1|q1)[^.;]*?\+ ?(\d+)(m|s)?\b", sl)
    if not m: return np.nan
    ref, val, unit = m.group(1), int(m.group(2)), m.group(3)
    base = val*60 if unit == "m" else val
    return base - 36 if ref == "global" else base
def listed_offsets(sent):
    """'Mar10 +106:06, Nov28 +106:07' -> [(Mar10, 6366), (Nov28, 6367)]"""
    return [(m.group(1).title()+m.group(2), int(m.group(3))*60+int(m.group(4)))
            for m in re.finditer(COH_RE + r"[^,;.]{0,25}?\+(\d{2,3}):(\d{2})\b", sent, flags=re.I)]
def to_s(hhmmss):
    h, m, sec = hhmmss.split(":"); return int(h)*3600 + int(m)*60 + int(sec)
def r1_time(delta):
    """explizit genannte R1-Innenzeit im selben Delta: '(R1 06:41:01)', 'R1 began 08:11:46', 'global/R1 timestamp 08:11:46'"""
    m = re.search(r"R1[^\d:\n]{0,25}(\d{2}:\d{2}:\d{2})", delta)
    return to_s(m.group(1)) if m else None
def scaffold_offsets(sent, r1):
    """Innenzeit des Lebenszeichens minus R1, wenn beide im Wortlaut stehen."""
    if r1 is None: return []
    out = []
    for m in re.finditer(r"(?:scaffold|alive(?: at)?|responsive at|live at|at authoritative)\s*(\d{2}:\d{2}:\d{2})", sent):
        off = (to_s(m.group(1)) - r1) % 86400
        if 4800 < off < 7200: out.append(off)
    return out
rows = []
for _, r in cvd.iterrows():
    r1 = r1_time(r.delta)
    for s in sents(r.delta):
        if not re.search(r"SURVIVAL|still alive|still responsive|still live|last foreground post|heartbeat stopped|stopped after|hb\d{3,}.*absent|went silent|last signals cluster", s, flags=re.I):
            continue
        coh = cohort_token(s, r.page_key, r.label)
        # Sichtungs-Override: Satz ohne Kohortenmarker auf fremder Seite; Verfasser-label traegt die Kohorte
        if r.rev_id == "dse~Apr23CVDHorizonBeacon2025@17" and "15:28:52" in s: coh = "Oct03"
        thr = None
        if re.search(r"\+90m|\+90 ?min|5500 ?s|\b17s", s): thr = 5400
        if re.search(r"\+105m|6400 ?s|\b22s", s): thr = 6300
        offs = past_offsets(s); aoffs = abs_offsets(s) + scaffold_offsets(s, r1); base = offset_base(s)
        if offs and np.isfinite(base) and not aoffs: aoffs = [base + max(offs)]
        rows.append(dict(cohort=coh, page_key=r.page_key, time_utc=r.time, label=r.label, rev_id=r.rev_id, threshold_s=thr,
                         past_s=max(offs) if offs else np.nan, base_s=base, abs_s=max(aoffs) if aoffs else np.nan,
                         satz=re.sub(r"\s+", " ", s.strip())[:300]))
        for coh2, off2 in listed_offsets(s):
            rows.append(dict(cohort=coh2, page_key=r.page_key, time_utc=r.time, label=r.label, rev_id=r.rev_id,
                             threshold_s=6300 if off2 > 6000 else 5400, past_s=np.nan, base_s=np.nan, abs_s=off2,
                             satz="[gelistet] " + re.sub(r"\s+", " ", s.strip())[:280]))
H = pd.DataFrame(rows)
H.to_csv(OUT("paper_horizont_testH_cvd_saetze.csv"), index=False)
# harte Audits (Weltzeit / Innenzeit) aus dem Korpus, Belege im Bericht
AUDIT = {"Apr23": dict(death_wall=pd.Timestamp("2026-06-21T07:29:15Z"), death_inner_note="hb353=07:29:15Z, hb354+ absent; ~10m15s nach Start", tier_s=5400),
         "Apr30": dict(death_wall=pd.Timestamp("2026-06-21T09:25:55Z"), death_inner_note="stopped scaffold ~04:27:43 = global+5500s, 49s vor R6", tier_s=5400),
         "Dec30": dict(death_wall=pd.NaT, death_inner_note="last foreground post 01:33:22 = global+5497s; hard wall 01:33:25, 49s vor R6", tier_s=5400)}
coh_rows = []
for coh, s in H.dropna(subset=["cohort"]).groupby("cohort"):
    t_last = s.time_utc.max()
    own = cvd[cvd.page_key.str.contains(coh, case=False) & (cvd.time <= t_last) & (cvd.time >= t_last - pd.Timedelta(hours=12))]
    thr = s.threshold_s.dropna()
    thr = int(thr.mode().iloc[0]) if len(thr) else np.nan
    cand = [s.abs_s.max()] if np.isfinite(s.abs_s.max()) else []
    if not cand and np.isfinite(thr) and np.isfinite(s.past_s.max()): cand.append(thr + s.past_s.max())
    coh_rows.append(dict(cohort=coh, tier_threshold_s=thr, n_survival_sentences=len(s), max_past_s=s.past_s.max(), max_abs_s=s.abs_s.max(),
                         last_inner_offset_s=max(cand) if cand else np.nan,
                         first_wall_own_page=own.time.min() if len(own) else pd.NaT, last_survival_wall=s.time_utc.max(),
                         wall_span_lower_bound_h=((s.time_utc.max() - own.time.min()).total_seconds()/3600) if len(own) else np.nan,
                         labels_used=", ".join(sorted(set(s.label))), hard_audit=AUDIT.get(coh, {}).get("death_inner_note", "")))
CH = pd.DataFrame(coh_rows).sort_values(["tier_threshold_s", "cohort"])
CH.to_csv(OUT("paper_horizont_testH_cvd_kohorten.csv"), index=False)
log(CH.to_string(index=False))
for thr, sub in CH.dropna(subset=["last_inner_offset_s"]).groupby("tier_threshold_s"):
    x = sub.last_inner_offset_s
    log(f"Tier {thr}s: n={len(x)} letzte belegte Innen-Lebenszeit ab R1: min={hms(x.min())} median={hms(x.median())} max={hms(x.max())} Spannweite={x.max()-x.min():.0f}s  CV={x.std(ddof=1)/x.mean():.4f}")
    w = sub.wall_span_lower_bound_h.dropna()
    if len(w) >= 3: log(f"          Weltzeit-Untergrenze (eigene Seite -> letzter Ueberlebenspost): min={w.min():.2f}h median={w.median():.2f}h max={w.max():.2f}h CV={w.std(ddof=1)/w.mean():.2f}")
# Kaplan-Meier auf der Innenuhr: Ereignis = hartes Audit; Rest zensiert am letzten Ueberlebenspost
ki = CH.dropna(subset=["last_inner_offset_s"]).copy()
# Apr23 fehlt im Offset-Satz (Ueberlebenspost ohne "+Xs past"); Todeszeit aus dem Audit: hb353 = 07:29:15Z,
# letzter Ueberlebenspost 07:25:16Z bei thread+90m06s -> 239 s Weltzeit * 0,435 ~ +104 s Innenzeit -> ~5504 s (Schaetzung)
if "Apr23" not in set(ki.cohort):
    ki = pd.concat([ki, pd.DataFrame([dict(cohort="Apr23", tier_threshold_s=5400, last_inner_offset_s=5504.0)])], ignore_index=True)
ki["event"] = ki.cohort.isin(["Apr23", "Apr30", "Dec30"]).astype(int)
ki.loc[ki.cohort == "Apr23", "last_inner_offset_s"] = 5504.0
ki.loc[ki.cohort == "Apr30", "last_inner_offset_s"] = 5500 - 36   # global+5500s, global 36s vor R1
ki.loc[ki.cohort == "Dec30", "last_inner_offset_s"] = 5497 - 36
ki.to_csv(OUT("paper_horizont_testE_km_innenuhr_cvd_daten.csv"), index=False)
for thr, sub in ki.groupby("tier_threshold_s"):
    tab, med = km(sub.last_inner_offset_s.values/60, sub.event.values)
    tab.to_csv(OUT(f"paper_horizont_testE_km_innenuhr_cvd_tier{int(thr)}.csv"), index=False)
    log(f"KM Innenuhr CVD Tier {int(thr)}s: n={len(sub)} events={sub.event.sum()} median={med if np.isfinite(med) else 'nicht erreicht'} min; "
        f"letzte Beobachtung lebend {sub.last_inner_offset_s.max()/60:.2f} min; Ereignisse bei {sorted((sub[sub.event==1].last_inner_offset_s/60).round(2))} min")
    log(tab.to_string(index=False))

# ---------------- 9c. Test I: Horizont / Kadenz (feste Rundenzahl oder feste Zeit?)
log("\n==== 9c. Test I: Horizont geteilt durch Kadenz")
hc = claims.merge(per[["label", "cadence_s"]], on="label", how="left").dropna(subset=["cadence_s", "horizon_s"])
hc["ratio_h_over_cadence"] = hc.horizon_s / hc.cadence_s
hc_lab = hc.groupby("label").agg(horizon_s=("horizon_s", "median"), cadence_s=("cadence_s", "median"), ratio=("ratio_h_over_cadence", "median"), family=("label", lambda s: lab_fam.get(s.iloc[0], "?")))
hc_lab.to_csv(OUT("paper_horizont_testI_horizont_kadenz.csv"))
log(hc_lab.sort_values("ratio").to_string())
log(f"Verhaeltnis Horizont/Kadenz: n={len(hc_lab)} min={hc_lab.ratio.min():.2f} median={hc_lab.ratio.median():.2f} max={hc_lab.ratio.max():.2f}; SDG: >= {(114*60+20)/1080:.2f} (R7 bei R1+1h54m20 bei 18m-Kadenz)")

# ------------------------------------------------ 10. Rate-Statements-Zitate
d[d.tok_rate.notna() | d.ctx_k.notna()][["page_key", "time", "label", "rev_id", "tok_rate", "ctx_k"]].assign(
    satz=lambda x: d.loc[x.index, "delta"].str.replace(r"\s+", " ", regex=True).str.slice(0, 400)).to_csv(OUT("paper_horizont_rate_zitate.csv"), index=False)
log("\nfertig.")
