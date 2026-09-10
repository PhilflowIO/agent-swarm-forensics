#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
63_fortschritt_robust.py
========================
Robustheitspaket zur Fortschrittsregression (Paper Tab. 3, main.tex ~321-344).

Antwort auf den Reviewer: Effektgroessen + 95%-KI vor p; Ordered Logit mit
Familien-Fixeffekt (Proportional-Odds-Pruefung ueber Schwellenmodelle
P(Runde>=k), k=2..5); Zensur-Sensitivitaet ueber "faellige" Runden bis zur
letzten Wiki-Aktivitaet; Leave-one-family-out; Dedup-Varianten (Kopierziele
der Zitatkaskade, eine Beobachtung je (Familie, Datum)); Benjamini-Hochberg
ueber die Praediktorfamilie; Zukunftsantwort als exakter Permutationstest
der Mittelwertdifferenz mit Permutations-KI (Shift-Inversion).

Eingaben (alle in artefakte/, erzeugt von 51_prozess.py):
  paper_fortschritt_kohorten.csv, paper_prozess_zitatkaskade_kopien.csv
Ausgaben (artefakte/):
  paper_robust_fortschritt_effekte.csv, paper_robust_fortschritt_ordinal.csv,
  paper_robust_fortschritt_zensur.csv, paper_robust_lofo.csv,
  paper_robust_fortschritt_dedup.csv, _paper_robust_fortschritt.log
  + paper/tables/tab_progress.tex, paper/tables/tab_robustness_progress.tex

Lauf:  .venv/bin/python scripts/63_fortschritt_robust.py   (Seed 20260909)
"""
from __future__ import annotations
import os, math, warnings, itertools, json
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.miscmodels.ordinal_model import OrderedModel
from statsmodels.stats.multitest import multipletests
from statsmodels.tools.sm_exceptions import PerfectSeparationError

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
ART = os.path.join(BASE, "artefakte")
TAB = os.path.join(os.path.dirname(BASE), "paper", "tables")
os.makedirs(TAB, exist_ok=True)
OUT = lambda n: os.path.join(ART, n)
LOG = open(OUT("_paper_robust_fortschritt.log"), "w", encoding="utf-8")
SEED = 20260909
RNG = np.random.default_rng(SEED)
N_BOOT = 2000
N_PERM = 100_000
MIN_FAM = 5          # Familien mit < MIN_FAM Kohorten -> "other"
EPS_H = 1.0 / 3600   # 1 s in Stunden fuer log(lebensspanne + eps)


def L(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LOG.write(s + "\n")


# =========================================================== 0. Laden
K = pd.read_csv(OUT("paper_fortschritt_kohorten.csv"))
KOPIEN = pd.read_csv(OUT("paper_prozess_zitatkaskade_kopien.csv"))
L(f"Kohorten gesamt {len(K)}; Familien gesamt {K.aufgabenfamilie.nunique()}")
# Expositionsvariablen (66_exposition.py Teil C): was lag bei Ankunft der Kohorte auf ihren Seiten?
# Optional — fehlt die Datei, laeuft das Skript wie zuvor.
EXPF = OUT("paper_exposition_kohorten.csv")
HAS_EXP = os.path.exists(EXPF)
if HAS_EXP:
    EX = pd.read_csv(EXPF)[["cohort_key", "exp_runde_max_vor", "exp_vorsprung_b", "exp_vorsprung_seiten",
                            "exp_runde_saetze_vor"]]
    K = K.merge(EX, on="cohort_key", how="left")
    for c in ["exp_runde_max_vor", "exp_vorsprung_b", "exp_vorsprung_seiten", "exp_runde_saetze_vor"]:
        K[c] = K[c].fillna(0)
    L(f"Expositionsvariablen zugespielt ({EXPF}): Kohorten mit sichtbarer fremder Rundenangabe vor Ankunft "
      f"{int((K.exp_runde_saetze_vor > 0).sum())}, davon oberhalb des eigenen spaeteren Standes "
      f"{int(K.exp_vorsprung_b.sum())}")
else:
    L("WARNUNG: paper_exposition_kohorten.csv fehlt — Expositionspraediktoren werden uebersprungen "
      "(scripts/66_exposition.py zuerst laufen lassen).")
K["erste_version"] = pd.to_datetime(K.erste_version, utc=True)
K["letzte_version"] = pd.to_datetime(K.letzte_version, utc=True)
K["log_deltas"] = np.log(K.n_deltas)
K["log_leben"] = np.log(K.lebensspanne_real_h + EPS_H)
K["y"] = K.max_runde_belegt.astype(float)
for c in ["clock_wait", "counterapi", "umleitung", "blob_ausbruch", "beobachtung_auf_fremder_seite", "zukunft_erhalten_n"]:
    K[c + "_b"] = (K[c] > 0).astype(int)
for c in ["kadenz_s", "r1_frist_s", "folgefrist_s"]:
    K["log_" + c] = np.log(K[c])

PRED = [  # (Spaltenname, Anzeigename, binaer?)
    ("log_kadenz_s", "Cadence (log s)", False),
    ("log_r1_frist_s", "Initial deadline (log s)", False),
    ("log_folgefrist_s", "Answer deadline (log s)", False),
    ("clock_wait_b", r"\texttt{clock.wait} used", True),
    ("counterapi_b", r"\texttt{counterapi} used", True),
    ("umleitung_b", "Redirect services", True),
    ("blob_ausbruch_b", "Blob egress", True),
    ("beobachtung_auf_fremder_seite_b", "Observation on foreign page", True),
    ("bitten_quote", "Request rate", False),
    ("zukunft_erhalten_n_b", "Future answer received", True),
]
if HAS_EXP:
    # Exposition bei Ankunft. exp_runde_max_vor ist exogen (unabhaengig vom eigenen Ergebnis definiert);
    # exp_vorsprung_b ist relativ zum eigenen spaeteren Stand definiert und deshalb nur als
    # Nebenspezifikation zu lesen (66_exposition.py Teil C, BERICHT_exposition.md §Ambiguitaeten).
    PRED += [
        ("exp_runde_max_vor", "Highest round visible on arrival", False),
        ("exp_vorsprung_b", "Answer ahead visible on arrival", True),
    ]
NAME = {c: n for c, n, _ in PRED}
ISBIN = {c: b for c, _, b in PRED}

K510 = K[K.max_runde_belegt >= 1].copy()
L(f"Teilmenge max_runde_belegt>=1: {len(K510)} Kohorten, {K510.aufgabenfamilie.nunique()} Familien")
L("Verteilung max_runde_belegt (n=510):", K510.max_runde_belegt.value_counts().sort_index().to_dict())


def fam_grouped(df, min_n=MIN_FAM):
    vc = df.aufgabenfamilie.value_counts()
    small = set(vc[vc < min_n].index)
    return df.aufgabenfamilie.where(~df.aufgabenfamilie.isin(small), "other")


# =========================================================== 1. Effektschaetzer
def ols_std(df, col, cov):
    """Standardisierte OLS: y (z) ~ x (z bzw. 0/1) + log_deltas + log_leben + C(fam).
    cov: 'HC1' oder 'cluster'. Rueckgabe dict(beta, lo, hi, p, n, se)."""
    d = df[[col, "y", "log_deltas", "log_leben", "aufgabenfamilie"]].dropna().copy()
    if len(d) < 15 or d[col].nunique() < 2:
        return None
    d["fam"] = fam_grouped(d)
    d["yz"] = (d.y - d.y.mean()) / d.y.std(ddof=1)
    d["x"] = d[col] if ISBIN[col] else (d[col] - d[col].mean()) / d[col].std(ddof=1)
    m = smf.ols("yz ~ x + log_deltas + log_leben + C(fam)", d)
    if cov == "HC1":
        r = m.fit(cov_type="HC1")
    else:
        g = pd.factorize(d.fam)[0]
        r = m.fit(cov_type="cluster", cov_kwds={"groups": g})
    ci = r.conf_int().loc["x"]
    n_fam_true = int(d.loc[d[col] > 0, "aufgabenfamilie"].nunique()) if ISBIN[col] else int(d.aufgabenfamilie.nunique())
    if cov == "cluster" and n_fam_true < 2:
        # Behandelte Kohorten in einer einzigen Familie: Cluster-SE per Konstruktion degeneriert (1 effektiver Cluster)
        return dict(effekt=np.nan, ci_lo=np.nan, ci_hi=np.nan, p=np.nan, se=np.nan, n=int(len(d)), n_fam=int(d.fam.nunique()),
                    n_fam_true=n_fam_true, grund="Cluster-SE degeneriert: behandelte Kohorten in 1 Familie")
    return dict(effekt=float(r.params["x"]), ci_lo=float(ci[0]), ci_hi=float(ci[1]), p=float(r.pvalues["x"]),
                se=float(r.bse["x"]), n=int(len(d)), n_fam=int(d.fam.nunique()), n_fam_true=n_fam_true)


def spearman_ci(df, col):
    d = df[[col, "y"]].dropna()
    n = len(d)
    if n < 8 or d[col].nunique() < 2:
        return None
    rho, p = stats.spearmanr(d[col], d.y)
    z = np.arctanh(np.clip(rho, -0.999999, 0.999999)); se = 1 / math.sqrt(n - 3)
    return dict(effekt=float(rho), ci_lo=float(np.tanh(z - 1.96 * se)), ci_hi=float(np.tanh(z + 1.96 * se)), p=float(p), n=n)


def rank_biserial(y, flag):
    a, b = y[flag], y[~flag]
    if len(a) < 1 or len(b) < 1:
        return np.nan
    u = stats.mannwhitneyu(a, b, alternative="two-sided").statistic  # U der Gruppe True
    return 2 * u / (len(a) * len(b)) - 1  # >0: Gruppe True hoeher


def rb_boot(df, col, cluster):
    d = df[[col, "y", "aufgabenfamilie"]].dropna()
    flag = d[col].values.astype(bool); y = d.y.values
    if flag.sum() < 2 or (~flag).sum() < 2:
        return None
    r = rank_biserial(y, flag)
    p = stats.mannwhitneyu(y[flag], y[~flag], alternative="two-sided").pvalue
    fams = d.aufgabenfamilie.values; uf = np.unique(fams)
    idx_by_f = {f: np.where(fams == f)[0] for f in uf}
    bs = []
    for _ in range(N_BOOT):
        if cluster:
            pick = RNG.choice(uf, size=len(uf), replace=True)
            idx = np.concatenate([idx_by_f[f] for f in pick])
        else:
            idx = RNG.integers(0, len(y), len(y))
        fl = flag[idx]
        if fl.sum() < 1 or (~fl).sum() < 1:
            continue
        bs.append(rank_biserial(y[idx], fl))
    bs = np.array(bs)
    return dict(effekt=float(r), ci_lo=float(np.nanpercentile(bs, 2.5)), ci_hi=float(np.nanpercentile(bs, 97.5)), p=float(p),
                n=int(len(d)), n_true=int(flag.sum()), n_boot_valid=int(len(bs)))


def perm_meandiff(df, col):
    """Exakter Permutationstest der Mittelwertdifferenz (True - False). Alle Kombinationen,
    falls C(n, n1) <= N_PERM, sonst Monte Carlo mit N_PERM Ziehungen. Permutations-KI durch
    Inversion des Shift-Tests: Menge aller delta, fuer die y - delta*flag nicht bei 5% verworfen wird."""
    d = df[[col, "y"]].dropna()
    flag = d[col].values.astype(bool); y = d.y.values; n = len(y); n1 = int(flag.sum())
    if n1 < 1 or n - n1 < 1:
        return None
    obs = y[flag].mean() - y[~flag].mean()
    n_comb = math.comb(n, n1)
    exact = n_comb <= N_PERM

    def perm_stats(yy):
        # Differenz = sum(yy[S])/n1 - (sum(yy)-sum(yy[S]))/(n-n1)
        tot = yy.sum()
        if exact:
            sums = np.fromiter((yy[list(c)].sum() for c in itertools.combinations(range(n), n1)), float, count=n_comb)
        else:
            sums = np.concatenate([yy[RNG.random((b, n)).argsort(axis=1)[:, :n1]].sum(axis=1)
                                   for b in [5000] * (N_PERM // 5000)])
        return sums / n1 - (tot - sums) / (n - n1)

    def pval(yy, stat):
        ps = perm_stats(yy)
        return float((np.abs(ps) >= abs(stat) - 1e-12).mean())

    p = pval(y, obs)
    # KI-Inversion (Shift): grid ueber delta, kleinere MC-Zahl je Punkt
    lo_grid = np.round(np.arange(obs - 4, obs + 4 + 1e-9, 0.05), 3)
    keep = []
    n_mc = 20_000
    for delta in lo_grid:
        yy = y - delta * flag
        stat = yy[flag].mean() - yy[~flag].mean()
        tot = yy.sum()
        sums = np.concatenate([yy[RNG.random((5000, n)).argsort(axis=1)[:, :n1]].sum(axis=1) for _ in range(n_mc // 5000)])
        ps = sums / n1 - (tot - sums) / (n - n1)
        if (np.abs(ps) >= abs(stat) - 1e-12).mean() >= 0.05:
            keep.append(delta)
    ci_lo, ci_hi = (min(keep), max(keep)) if keep else (np.nan, np.nan)
    return dict(effekt=float(obs), ci_lo=float(ci_lo), ci_hi=float(ci_hi), p=p, n=n, n_true=n1,
                exakt=exact, n_perm=int(n_comb if exact else N_PERM),
                mean_true=float(y[flag].mean()), mean_false=float(y[~flag].mean()))


def run_effects(df, subset_label, variant="basis", do_perm=True):
    rows = []
    for col, name, isbin in PRED:
        base = dict(praediktor=col, praediktor_name=name, teilmenge=subset_label, variante=variant, binaer=isbin)
        for cov in ["HC1", "cluster"]:
            r = ols_std(df, col, cov)
            if r: rows.append({**base, "modell": f"OLS_std_FE_{cov}", **r})
        if isbin:
            for cl in [False, True]:
                r = rb_boot(df, col, cl)
                if r: rows.append({**base, "modell": "rankbiserial_" + ("clusterboot" if cl else "boot"), **r})
        else:
            r = spearman_ci(df, col)
            if r: rows.append({**base, "modell": "spearman", **r})
        if col == "zukunft_erhalten_n_b" and do_perm:
            r = perm_meandiff(df, col)
            if r: rows.append({**base, "modell": "permutation_meandiff", **r})
    E = pd.DataFrame(rows)
    # BH ueber die Praediktorfamilie je Modell x Teilmenge x Variante
    E["q_bh"] = np.nan
    for _, idx in E.groupby(["modell", "teilmenge", "variante"]).groups.items():
        p = E.loc[idx, "p"].values
        ok = ~np.isnan(p)
        if ok.sum():
            E.loc[np.array(idx)[ok], "q_bh"] = multipletests(p[ok], method="fdr_bh")[1]
    return E


FEW_FAM = {c: int(K510.loc[K510[c] > 0, "aufgabenfamilie"].nunique()) for c, _, b in PRED if b}
FLAG = {c for c, v in FEW_FAM.items() if v < 5}
L("Binaere Praediktoren: Familien mit behandelten Kohorten (n=510):", FEW_FAM, "-> Cluster-SE-Warnung (<5 Familien):", sorted(FLAG))
SUBSETS = [("alle", K510), ("n_deltas>=5", K510[K510.n_deltas >= 5])]
L(f"Teilmenge n_deltas>=5: {len(SUBSETS[1][1])} Kohorten, {SUBSETS[1][1].aufgabenfamilie.nunique()} Familien")
EFF = pd.concat([run_effects(df, lab) for lab, df in SUBSETS], ignore_index=True)

# =========================================================== 2. Ordered Logit + Schwellenmodelle
def ordinal_models(df, col, label):
    d = df[[col, "y", "log_deltas", "log_leben", "aufgabenfamilie"]].dropna().copy()
    if len(d) < 15 or d[col].nunique() < 2:
        return []
    d["fam"] = fam_grouped(d)
    d["x"] = d[col] if ISBIN[col] else (d[col] - d[col].mean()) / d[col].std(ddof=1)
    X = pd.get_dummies(d[["x", "log_deltas", "log_leben", "fam"]], columns=["fam"], drop_first=True, dtype=float)
    rows = []
    # (a) Proportional-Odds-Modell
    try:
        yo = pd.Categorical(d.y.astype(int), ordered=True)
        om = OrderedModel(yo, X, distr="logit").fit(method="bfgs", maxiter=3000, disp=False)
        ci = om.conf_int().loc["x"]
        rows.append(dict(praediktor=col, praediktor_name=NAME[col], teilmenge=label, modell="ordered_logit_FE",
                         schwelle="alle", effekt=float(om.params["x"]), ci_lo=float(ci[0]), ci_hi=float(ci[1]),
                         p=float(om.pvalues["x"]), se=float(om.bse["x"]), n=int(len(d)), konvergiert=bool(om.mle_retvals.get("converged", True))))
    except Exception as e:
        rows.append(dict(praediktor=col, praediktor_name=NAME[col], teilmenge=label, modell="ordered_logit_FE", schwelle="alle",
                         effekt=np.nan, ci_lo=np.nan, ci_hi=np.nan, p=np.nan, se=np.nan, n=int(len(d)), konvergiert=False, fehler=str(e)[:80]))
    # (b) Schwellenlogits P(y>=k), k=2..5; Familien ohne Varianz im Ziel fallen heraus (FE-Logit-Praxis)
    for k in range(2, 6):
        dk = d.copy(); dk["yk"] = (dk.y >= k).astype(int)
        var = dk.groupby("fam").yk.transform(lambda s: s.nunique() > 1)
        dk = dk[var]
        if dk.yk.nunique() < 2 or len(dk) < 15 or dk.x.nunique() < 2:
            continue
        Xk = pd.get_dummies(dk[["x", "log_deltas", "log_leben", "fam"]], columns=["fam"], drop_first=True, dtype=float)
        Xk = sm.add_constant(Xk)
        try:
            lg = sm.Logit(dk.yk, Xk).fit(method="bfgs", maxiter=2000, disp=False)
            ci = lg.conf_int().loc["x"]
            rows.append(dict(praediktor=col, praediktor_name=NAME[col], teilmenge=label, modell="logit_threshold_FE",
                             schwelle=f">={k}", effekt=float(lg.params["x"]), ci_lo=float(ci[0]), ci_hi=float(ci[1]),
                             p=float(lg.pvalues["x"]), se=float(lg.bse["x"]), n=int(len(dk)), n_pos=int(dk.yk.sum()),
                             n_fam_dropped=int(d.fam.nunique() - dk.fam.nunique()), konvergiert=bool(lg.mle_retvals.get("converged", True))))
        except Exception as e:
            rows.append(dict(praediktor=col, praediktor_name=NAME[col], teilmenge=label, modell="logit_threshold_FE", schwelle=f">={k}",
                             effekt=np.nan, ci_lo=np.nan, ci_hi=np.nan, p=np.nan, se=np.nan, n=int(len(dk)), konvergiert=False, fehler=str(e)[:80]))
    return rows


ORD_rows = []
for lab, df in SUBSETS:
    for col, _, _ in PRED:
        ORD_rows += ordinal_models(df, col, lab)
ORD = pd.DataFrame(ORD_rows)
# Quasi-Separation: SE > 10 auf Logit-Skala -> Schaetzer unbrauchbar, Effekt auf NaN, Grund vermerkt
sep = ORD.se > 10
ORD.loc[sep, ["effekt", "ci_lo", "ci_hi", "p"]] = np.nan
ORD["quasi_separation"] = sep
L(f"Schwellenmodelle mit Quasi-Separation (SE>10, verworfen): {int(sep.sum())}")
# PO-Pruefung: Spannweite der Schwellenkoeffizienten und paarweiser Wald-Test
po_rows = []
for (col, lab), g in ORD[ORD.modell == "logit_threshold_FE"].groupby(["praediktor", "teilmenge"]):
    g = g.dropna(subset=["effekt"])
    if len(g) < 2:
        continue
    b, s = g.effekt.values, g.se.values
    zmax = max(abs(b[i] - b[j]) / math.sqrt(s[i] ** 2 + s[j] ** 2) for i in range(len(b)) for j in range(i + 1, len(b)))
    po_rows.append(dict(praediktor=col, teilmenge=lab, n_schwellen=len(g), beta_min=b.min(), beta_max=b.max(), spannweite=b.max() - b.min(),
                        vorzeichen_einheitlich=bool(np.all(np.sign(b) == np.sign(b[0]))), max_wald_z=zmax, po_verletzt=bool(zmax > 1.96)))
PO = pd.DataFrame(po_rows)
ORD = ORD.merge(PO[["praediktor", "teilmenge", "spannweite", "max_wald_z", "po_verletzt"]], on=["praediktor", "teilmenge"], how="left")
for lab in ["alle", "n_deltas>=5"]:
    for m in ["ordered_logit_FE", "logit_threshold_FE"]:
        idx = ORD[(ORD.teilmenge == lab) & (ORD.modell == m)].index
        for sch, ii in ORD.loc[idx].groupby("schwelle").groups.items():
            p = ORD.loc[ii, "p"].values; ok = ~np.isnan(p)
            if ok.sum():
                ORD.loc[np.array(ii)[ok], "q_bh"] = multipletests(p[ok], method="fdr_bh")[1]
ORD.to_csv(OUT("paper_robust_fortschritt_ordinal.csv"), index=False)
L("\n=== Ordinal / Schwellen (alle) ===")
L(ORD[ORD.teilmenge == "alle"][["praediktor", "modell", "schwelle", "n", "effekt", "ci_lo", "ci_hi", "p", "q_bh", "po_verletzt", "konvergiert"]].to_string())
L("PO-Pruefung:\n" + PO.to_string())

# =========================================================== 3. Zensur-Sensitivitaet
# due_k = erste_version + r1 + (k-1)*kadenz ; r1 fehlt -> Familienmedian, sonst Gesamtmedian (dokumentiert)
Z = K510.copy()
r1_fam = Z.groupby("aufgabenfamilie").r1_frist_s.median()
r1_all = Z.r1_frist_s.median()
Z["r1_used"] = Z.r1_frist_s.fillna(Z.aufgabenfamilie.map(r1_fam)).fillna(r1_all)
Z["r1_imputiert"] = Z.r1_frist_s.isna()
Z = Z[Z.kadenz_s.notna()].copy()
L(f"\n=== Zensur === Kohorten mit Kadenz (n>=1): {len(Z)}; davon R1 imputiert: {int(Z.r1_imputiert.sum())} (Familienmedian/Gesamtmedian {r1_all:.0f}s)")
ZEN_rows = []
for k in range(2, 6):
    due = Z.erste_version + pd.to_timedelta(Z.r1_used + (k - 1) * Z.kadenz_s, unit="s")
    Zk = Z[Z.letzte_version >= due]
    L(f"k={k}: faellig bis letzte Version: {len(Zk)} von {len(Z)} (Anteil y>=k: {(Zk.y >= k).mean():.2f} vs. ungefiltert {(Z.y >= k).mean():.2f})")
    for col, name, isbin in PRED:
        for label, dd in [("ungefiltert_mit_kadenz", Z), ("faellig", Zk)]:
            d = dd[[col, "y", "log_deltas", "log_leben", "aufgabenfamilie"]].dropna().copy()
            base = dict(schwelle=f">={k}", filter=label, praediktor=col, praediktor_name=name, n=int(len(d)), n_pos=int((d.y >= k).sum()))
            if len(d) < 15 or d[col].nunique() < 2 or (d.y >= k).nunique() < 2:
                ZEN_rows.append({**base, "effekt": np.nan, "grund": "zu wenig Daten/keine Varianz"}); continue
            if min((d.y >= k).sum(), (d.y < k).sum()) < 5:
                ZEN_rows.append({**base, "effekt": np.nan, "grund": "Ziel fast ohne Varianz (<5 Faelle in einer Klasse)"}); continue
            if isbin and (min((d[col] > 0).sum(), (d[col] == 0).sum()) < 3 or d.loc[d[col] > 0, "aufgabenfamilie"].nunique() < 2):
                ZEN_rows.append({**base, "effekt": np.nan, "grund": "Praediktor: <3 behandelte Kohorten oder nur 1 Familie"}); continue
            d["fam"] = fam_grouped(d); d["yk"] = (d.y >= k).astype(int)
            d["x"] = d[col] if isbin else (d[col] - d[col].mean()) / d[col].std(ddof=1)
            var = d.groupby("fam").yk.transform(lambda s: s.nunique() > 1); d2 = d[var]
            # Logit mit FE (wo moeglich), sonst lineares Wahrscheinlichkeitsmodell mit Cluster-SE als Fallback
            try:
                if len(d2) < 15 or d2.x.nunique() < 2: raise ValueError("FE-Logit: zu wenig Varianz")
                Xk = sm.add_constant(pd.get_dummies(d2[["x", "log_deltas", "log_leben", "fam"]], columns=["fam"], drop_first=True, dtype=float))
                lg = sm.Logit(d2.yk, Xk).fit(method="bfgs", maxiter=2000, disp=False)
                if lg.bse["x"] > 10: raise ValueError("Quasi-Separation")
                ci = lg.conf_int().loc["x"]
                ZEN_rows.append({**base, "modell": "logit_threshold_FE", "n_modell": int(len(d2)), "effekt": float(lg.params["x"]), "ci_lo": float(ci[0]), "ci_hi": float(ci[1]), "p": float(lg.pvalues["x"])})
            except Exception:
                g = pd.factorize(d.fam)[0]
                m = smf.ols("yk ~ x + log_deltas + log_leben + C(fam)", d)
                r = m.fit(cov_type="cluster", cov_kwds={"groups": g}) if d.fam.nunique() >= 2 else m.fit(cov_type="HC1")
                ci = r.conf_int().loc["x"]
                ZEN_rows.append({**base, "modell": "LPM_FE_" + ("cluster" if d.fam.nunique() >= 2 else "HC1") + "(Fallback)", "n_modell": int(len(d)), "effekt": float(r.params["x"]), "ci_lo": float(ci[0]), "ci_hi": float(ci[1]), "p": float(r.pvalues["x"])})
ZEN = pd.DataFrame(ZEN_rows)
ZEN.to_csv(OUT("paper_robust_fortschritt_zensur.csv"), index=False)
L(ZEN[ZEN["filter"] == "faellig"].dropna(subset=["effekt"])[["schwelle", "praediktor", "modell", "n", "n_modell", "n_pos", "effekt", "ci_lo", "ci_hi", "p"]].to_string())

# =========================================================== 4. Leave-one-family-out
def core_estimates(df):
    out = {}
    for col, _, isbin in PRED:
        r = ols_std(df, col, "cluster")
        if r: out[(col, "OLS_std_FE_cluster")] = r
        if isbin:
            d = df[[col, "y"]].dropna(); fl = d[col].values.astype(bool)
            if fl.sum() >= 2 and (~fl).sum() >= 2:
                out[(col, "rankbiserial")] = dict(effekt=rank_biserial(d.y.values, fl), ci_lo=np.nan, ci_hi=np.nan)
        else:
            r = spearman_ci(df, col)
            if r: out[(col, "spearman")] = r
    return out


FAMS = sorted(K510.aufgabenfamilie.unique())
full = core_estimates(K510)
lofo = {k: [] for k in full}
for f in FAMS:
    est = core_estimates(K510[K510.aufgabenfamilie != f])
    for k in full:
        if k in est and not (isinstance(est[k]["effekt"], float) and math.isnan(est[k]["effekt"])):
            lofo[k].append({**est[k], "familie": f})
LOFO_rows = []
for (col, model), runs in lofo.items():
    R = pd.DataFrame(runs)
    if not len(R) or math.isnan(full[(col, model)]["effekt"]):
        continue
    sgn = np.sign(full[(col, model)]["effekt"])
    row = dict(praediktor=col, praediktor_name=NAME[col], modell=model, voll_effekt=full[(col, model)]["effekt"],
               n_runs=len(R), beta_min=R.effekt.min(), beta_max=R.effekt.max(),
               anteil_gleiches_vorzeichen=float((np.sign(R.effekt) == sgn).mean()),
               anteil_ci_ohne_0=float(((R.ci_lo > 0) | (R.ci_hi < 0)).mean()) if R.ci_lo.notna().any() else np.nan,
               familie_min=R.loc[R.effekt.idxmin(), "familie"], familie_max=R.loc[R.effekt.idxmax(), "familie"])
    LOFO_rows.append(row)
LOFO = pd.DataFrame(LOFO_rows)
LOFO.to_csv(OUT("paper_robust_lofo.csv"), index=False)
L(f"\n=== LOFO ueber {len(FAMS)} Familien (n=510) ===\n" + LOFO.to_string())

# =========================================================== 5. Dedup-Varianten
copy_targets = set(KOPIEN.kopierer_cohort.dropna().unique())
n_targets_in = int(K510.cohort_key.isin(copy_targets).sum())
D1 = K510[~K510.cohort_key.isin(copy_targets)]
dup_fd = int(K510.duplicated(["aufgabenfamilie", "kohorte"]).sum())
L(f"\n=== Dedup === Kopierziele in Kaskade: {len(copy_targets)} Kohorten, davon in n=510: {n_targets_in} -> Variante (i) n={len(D1)}")
L(f"(Familie, Kohortendatum) Duplikate in n=510: {dup_fd} -> Variante (ii) identisch mit Basis (cohort_key = Familie|Datum ist eindeutig)")
DED = pd.concat([run_effects(D1, "alle", variant="ohne_kopierziele", do_perm=True),
                 run_effects(K510, "alle", variant="eine_je_familie_datum(identisch)", do_perm=False)], ignore_index=True)
DED.to_csv(OUT("paper_robust_fortschritt_dedup.csv"), index=False)
L(DED[DED.variante == "ohne_kopierziele"][["praediktor", "modell", "n", "effekt", "ci_lo", "ci_hi", "p", "q_bh"]].to_string())

# =========================================================== 6. Effekte-Tabelle schreiben + Log
EFF.to_csv(OUT("paper_robust_fortschritt_effekte.csv"), index=False)
L("\n=== Effekte (Basis) ===\n" + EFF[["praediktor", "teilmenge", "modell", "n", "effekt", "ci_lo", "ci_hi", "p", "q_bh"]].to_string())

# =========================================================== 7. LaTeX-Tabellen
def tex_esc(s):
    return s.replace("_", r"\_").replace("%", r"\%").replace(">=", r"$\geq$")


def fmt(v, d=2):
    return "---" if v is None or (isinstance(v, float) and math.isnan(v)) else f"{v:.{d}f}"


def num(v, d=2):
    return "---" if v is None or (isinstance(v, float) and math.isnan(v)) else f"\\num{{{v:.{d}f}}}"


def ci_str(r, d=2):
    if r is None: return "---"
    return f"{num(r['effekt'], d)} [{num(r['ci_lo'], d)}, {num(r['ci_hi'], d)}]"


def dname(col):
    return NAME[col] + (r"$^\dagger$" if col in FLAG else "")


def pick(E, col, model, sub="alle", var="basis"):
    g = E[(E.praediktor == col) & (E.modell == model) & (E.teilmenge == sub) & (E.variante == var)]
    return g.iloc[0].to_dict() if len(g) else None


lines = [r"\begin{tabular}{lrllrr}", r"\toprule",
         r"Predictor & $n$ cohorts (reconstructed) & raw effect [95\,\% CI] & controlled $\beta$ (cluster SE) [95\,\% CI] & BH $q$ & LOFO: sign / CI$\not\ni$0 \\",
         r"\midrule"]
for col, name, isbin in PRED:
    raw = pick(EFF, col, "rankbiserial_clusterboot" if isbin else "spearman")
    ctl = pick(EFF, col, "OLS_std_FE_cluster")
    lf = LOFO[(LOFO.praediktor == col) & (LOFO.modell == "OLS_std_FE_cluster")]
    n = int(ctl["n"]) if ctl else (int(raw["n"]) if raw else 0)
    rawlab = ("$r=$" if isbin else r"$\rho=$") + ci_str(raw)
    if isbin and raw: rawlab += f" ({int(raw['n_true'])} yes)"
    lofo_s = f"{lf.anteil_gleiches_vorzeichen.iloc[0]:.2f} / {lf.anteil_ci_ohne_0.iloc[0]:.2f}" if len(lf) else "---"
    q = fmt(ctl["q_bh"], 2) if ctl else "---"
    lines.append(f"{dname(col)} & {n} & {rawlab} & {ci_str(ctl)} & {q} & {lofo_s} \\\\")
perm = pick(EFF, "zukunft_erhalten_n_b", "permutation_meandiff")
if perm:
    lines.append(r"\midrule")
    lines.append(f"Future answer: mean difference in rounds (permutation, {'exact' if perm['exakt'] else 'MC'} $n={int(perm['n_perm'])}$) & {int(perm['n'])} & "
                 f"$\\Delta=${ci_str(perm)} & --- & $p={fmt(perm['p'], 2)}$ & --- \\\\")
lines += [r"\bottomrule", r"\end{tabular}"]
open(os.path.join(TAB, "tab_progress.tex"), "w").write("\n".join(lines) + "\n")

# Robustheitstabelle: eine Zeile je Variante; Zusammenfassung ueber die Praediktorfamilie
def summarize(E, model, sub, var, label, n_note=""):
    g = E[(E.modell == model) & (E.teilmenge == sub) & (E.variante == var)].dropna(subset=["effekt"])
    if not len(g): return None
    pos = g[(g.ci_lo > 0)]; neg = g[(g.ci_hi < 0)]
    q_sig = g[g.q_bh < 0.05]
    return dict(variante=label, n=f"{int(g.n.max())}{n_note}", k=len(g), pos=", ".join(dname(c) for c in pos.praediktor), neg=", ".join(dname(c) for c in neg.praediktor),
                q=len(q_sig), q_names=", ".join(dname(c) for c in q_sig.praediktor))


rob = []
rob.append(summarize(EFF, "OLS_std_FE_HC1", "alle", "basis", "Controlled OLS, family FE, HC1 SE"))
rob.append(summarize(EFF, "OLS_std_FE_cluster", "alle", "basis", "Controlled OLS, family FE, cluster SE"))
rob.append(summarize(EFF, "OLS_std_FE_cluster", "n_deltas>=5", "basis", r"Same, subset $\geq 5$ revisions"))
rob.append(summarize(DED, "OLS_std_FE_cluster", "alle", "ohne_kopierziele", "Same, copy targets of citation cascade removed"))
rob.append(summarize(DED, "OLS_std_FE_cluster", "alle", "eine_je_familie_datum(identisch)", "Same, one cohort per (family, date) (already unique)"))
ORD2 = ORD.assign(variante="basis")
rob.append(summarize(ORD2, "ordered_logit_FE", "alle", "basis", "Ordered logit, family FE"))
for k in range(2, 6):
    rob.append(summarize(ORD2[ORD2.schwelle == f">={k}"], "logit_threshold_FE", "alle", "basis", f"Threshold logit $P(\\text{{round}}\\geq {k})$, family FE"))
ZEN2 = ZEN.assign(variante="basis", teilmenge="alle", q_bh=np.nan, modell="z")
for k in range(2, 6):
    zz = ZEN2[(ZEN2.schwelle == f">={k}") & (ZEN2["filter"] == "faellig") & (ZEN2.modell == "logit_threshold_FE")].dropna(subset=["effekt"]).copy()
    for _, idx in zz.groupby("schwelle").groups.items():
        p = zz.loc[idx, "p"].values; ok = ~np.isnan(p)
        if ok.sum(): zz.loc[np.array(idx)[ok], "q_bh"] = multipletests(p[ok], method="fdr_bh")[1]
    r = summarize(zz, "logit_threshold_FE", "alle", "basis", f"Censoring: cohorts with round {k} due by last revision, $P(\\text{{round}}\\geq {k})$")
    if r: rob.append(r)
lf = LOFO[LOFO.modell == "OLS_std_FE_cluster"]
rob.append(dict(variante=f"Leave-one-family-out ({len(FAMS)} families), controlled OLS cluster SE", n="510",
                k=len(lf), pos="", neg="", q=int((lf.anteil_ci_ohne_0 >= 0.95).sum()),
                q_names=", ".join(dname(c) for c in lf[lf.anteil_ci_ohne_0 >= 0.95].praediktor)))
if perm:
    rob.append(dict(variante="Future answer: permutation mean difference (rounds)", n=str(int(perm["n"])), k=1,
                    pos="" if not perm["ci_lo"] > 0 else "Future answer received", neg="" if not perm["ci_hi"] < 0 else "Future answer received",
                    q=0, q_names=f"$\\Delta=${ci_str(perm)}, $p={fmt(perm['p'])}$"))
rob = [r for r in rob if r]
lines = [r"\begin{tabular}{p{7.2cm}rrp{3.2cm}p{3.6cm}}", r"\toprule",
         r"Variant & $n$ & $k$ & CI excludes 0, positive & CI excludes 0, negative (BH $q<0.05$ in italics) \\", r"\midrule"]
for r in rob:
    negs = r["neg"] or "none"
    if r["q_names"] and not r["variante"].startswith(("Leave", "Future")):
        negs = negs + f" (\\emph{{{r['q_names']}}})" if r["q"] else negs
    if r["variante"].startswith("Leave"):
        negs = f"{r['q']} of {r['k']} with CI$\\not\\ni$0 in $\\geq 95\\,\\%$ of runs" + (f": {r['q_names']}" if r["q_names"] else "")
    if r["variante"].startswith("Future"):
        negs = r["q_names"]
    lines.append(f"{r['variante']} & {r['n']} & {r['k']} & {r['pos'] or 'none'} & {negs} \\\\")
lines += [r"\bottomrule", r"\end{tabular}"]
open(os.path.join(TAB, "tab_robustness_progress.tex"), "w").write("\n".join(lines) + "\n")
L("\nLaTeX-Tabellen geschrieben:", os.path.join(TAB, "tab_progress.tex"), os.path.join(TAB, "tab_robustness_progress.tex"))
json.dump(dict(n510=len(K510), n_ge5=len(SUBSETS[1][1]), fams=len(FAMS), perm=perm, n_copy_targets_in=n_targets_in, n_dedup1=len(D1)),
          open(OUT("paper_robust_fortschritt_summary.json"), "w"), indent=1, default=str)
LOG.close()
