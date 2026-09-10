#!/usr/bin/env python
"""
53_mathematik.py — Mathematisch-statistische Prüfung von MECHANIK.md und Suche nach
neuer Struktur. Lauffähig mit  `.venv/bin/python scripts/53_mathematik.py`  aus `analyse/`.
Alle Pfade relativ zum Skript. Ausgaben: artefakte/paper_math_*.csv, Log auf stdout.

Teile:
  A  Populationsschätzer (Sammelbild-Inversion, Überdispersion, Chao/Jackknife, Gamma-Poisson)
  B  Startwert-Rückrechnung (CPython-Reproduktion, Poisson-Zufallstreffer, Prognosebilanz)
  C  Uhren-Statistik (Steigungstest mit Äquivalenztest/Deming, Trennschärfe, n=11-Kostenkurve)
  D  Multiplizität (Holm/BH über alle berichteten Tests)
  E  Ankunftsprozess (Poisson vs. Hawkes, Ansteckungsstärke)
  F  Fahrplan-Parameter (Verteilungsanpassung, Ziffernstatistik, ggT)
  G  Skalengesetze (Zipf/Power-law vs. Lognormal)
"""
from __future__ import annotations
import os, re, sys, json, math, random, warnings
import numpy as np
import pandas as pd
from scipy import stats, optimize, special

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)                      # analyse/
DATA = os.path.join(BASE, "data")
ART  = os.path.join(BASE, "artefakte")
OUT  = lambda n: os.path.join(ART, "paper_math_" + n)
rng  = np.random.default_rng(20260908)

def hdr(t): print("\n" + "=" * 88 + f"\n{t}\n" + "=" * 88)
def save(df, name):
    df.to_csv(OUT(name), index=False); print(f"  -> {OUT(name)}  ({len(df)} Zeilen)")

# ---------------------------------------------------------------------------------------
# Daten
# ---------------------------------------------------------------------------------------
labels = pd.read_json(os.path.join(DATA, "labels.jsonl"), lines=True)
labels["first_write"] = pd.to_datetime(labels["first_write"], utc=True)
labels["last_write"]  = pd.to_datetime(labels["last_write"], utc=True)
deltas = pd.read_parquet(os.path.join(ART, "schwarm_deltas.parquet"))
deltas["time"] = pd.to_datetime(deltas["time"], utc=True)
deltas["delta"] = deltas["delta"].fillna("")
MON = {m: i + 1 for i, m in enumerate(["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"])}

# =======================================================================================
# TEIL A — Populationsschätzer
# =======================================================================================
hdr("A  Populationsschätzer: Sammelbild-Inversion unter Gleichverteilung und unter Überdispersion")
N = 365
mult = pd.read_csv(os.path.join(ART, "paper_flotte_marker_multiplizitaet.csv"))
D_obs = len(mult); n_lab = int(mult.n_labels.sum())
counts = np.zeros(N, dtype=int); counts[:D_obs] = mult.n_labels.values
fk = pd.Series(counts).value_counts().sort_index()
print(f"Belegte Daten D={D_obs}, datierte Namen n={n_lab}, f_k: {fk.to_dict()}")

def E_D(n, N=N): return N * (1 - (1 - 1 / N) ** n)
def Var_D(n, N=N):
    p1 = (1 - 1 / N) ** n; p2 = (1 - 2 / N) ** n
    return N * p1 + N * (N - 1) * p2 - N * N * p1 * p1
def invert(D, N=N):
    return optimize.brentq(lambda n: E_D(n, N) - D, 1, 50000)
def ci_normal(D, N=N, z=1.959964):
    lo = optimize.brentq(lambda n: E_D(n, N) + z * math.sqrt(Var_D(n, N)) - D, 1, 50000)
    hi = optimize.brentq(lambda n: E_D(n, N) - z * math.sqrt(Var_D(n, N)) - D, 1, 50000)
    return lo, hi
n_hat = invert(D_obs); lo, hi = ci_normal(D_obs)
print(f"[Nachrechnung] n̂ = {n_hat:.1f}, Akzeptanzbereich-Inversion (Normalapprox.) 95%: [{lo:.0f}, {hi:.0f}]  (Bericht: 888 [787, 996])")
print(f"  SD(D | n̂) = {math.sqrt(Var_D(n_hat)):.2f}")

# Exakte Inversion per Monte Carlo (Verteilung von D | n) + Profil-Likelihood via Simulation
def sim_D(n, reps=4000, N=N, probs=None):
    if probs is None:
        draws = rng.integers(0, N, size=(reps, n))
    else:
        draws = rng.choice(N, size=(reps, n), p=probs)
    d = np.sort(draws, axis=1)
    return (np.diff(d, axis=1) != 0).sum(1) + 1
def mc_ci(D, N=N, probs=None):
    # kleinstes n mit P(D_sim >= D) >= 0.025 ; größtes n mit P(D_sim <= D) >= 0.025
    def p_ge(n): return (sim_D(int(n), 3000, N, probs) >= D).mean()
    def p_le(n): return (sim_D(int(n), 3000, N, probs) <= D).mean()
    lo_ = optimize.brentq(lambda n: p_ge(n) - 0.025, 300, 3000, xtol=2)
    hi_ = optimize.brentq(lambda n: p_le(n) - 0.025, 300, 5000, xtol=2)
    return lo_, hi_
mc_lo, mc_hi = mc_ci(D_obs)
print(f"[Monte-Carlo-Inversion, exakt] 95%: [{mc_lo:.0f}, {mc_hi:.0f}]")

# --- Überdispersion: was sie ist und was nicht ---
VMR_all = counts.var(ddof=1) / counts.mean()
c_wo2 = np.sort(counts)[:-2]; VMR_wo2 = c_wo2.var(ddof=1) / c_wo2.mean()
print(f"Dispersionsindex Namen/Datum: {VMR_all:.3f}; ohne die zwei Wegwerf-Familien (Sep13=23, Jun22=19): {VMR_wo2:.3f}")

# Kontamination durch reale Daten
lab_ix = labels.set_index("label")
rows = []
for _, r in mult.iterrows():
    for l in r["labels"].split("|"):
        fw = lab_ix.loc[l, "first_write"]
        rows.append(dict(label=l, month=r["month"], day=int(r["day"]), first_write=fw,
                         real_date_match=bool(fw.month == MON[r["month"]] and fw.day == int(r["day"]))))
dated = pd.DataFrame(rows)
n_real = int(dated.real_date_match.sum())
print(f"Namen, deren Marker = reales Erstschreibdatum: {n_real} (Erwartung unter Gleichverteilung {n_lab/365:.1f}); davon Jun22: {(dated.real_date_match & (dated.month=='Jun') & (dated.day==22)).sum()}")
dated_clean = dated[~dated.real_date_match]
D_clean = dated_clean.groupby(["month","day"]).ngroups
print(f"  Ohne diese {n_real} Namen: D = {D_clean}, n̂ = {invert(D_clean):.0f}")
# Die kanonische Zeile der Schaetzer-Versoehnung wird hier erzeugt, nicht von Hand
# gepflegt: D_clean, der invertierte Punktschaetzer und sein exaktes Monte-Carlo-
# Intervall. Vorher stand hier eine handgeschriebene Zeile, deren Intervall noch zum
# unbereinigten D gehoerte -- Punktschaetzer und Intervall passten nicht zueinander.
mc_clean_lo, mc_clean_hi = mc_ci(D_clean)
print(f"  Monte-Carlo-Intervall zu D={D_clean}: [{mc_clean_lo:.0f}, {mc_clean_hi:.0f}]")
save(pd.DataFrame([dict(D=D_clean, n_hat=round(invert(D_clean)),
                        ci_lo=round(mc_clean_lo), ci_hi=round(mc_clean_hi),
                        entfernte_namen=n_real, verfahren="Monte-Carlo-Inversion, exakt")]),
     "population_bereinigt.csv")


# Cluster-Ebene: Namen gleichen Datums, deren Erstschreibzeit < gap auseinander liegt → eine Episode
def clusters_per_date(gap_h):
    out = {}
    for (m, d), g in dated_clean.groupby(["month","day"]):
        t = np.sort(g.first_write.values.astype("datetime64[s]").astype(np.int64))
        k = 1 + int((np.diff(t) > gap_h * 3600).sum()) if len(t) > 1 else 1
        out[(m, d)] = k
    return out
clus_rows = []
for gap in (2, 6, 24):
    cp = clusters_per_date(gap)
    cc = np.zeros(N, dtype=int); cc[:len(cp)] = list(cp.values())
    fkc = pd.Series(cc).value_counts().sort_index()
    vmr = cc.var(ddof=1) / cc.mean()
    clus_rows.append(dict(gap_h=gap, D=len(cp), n_cluster=int(cc.sum()), VMR=vmr, f0=int(fkc.get(0,0)), f1=int(fkc.get(1,0)), f2=int(fkc.get(2,0)), f3=int(fkc.get(3,0)), fmax=int(cc.max())))
    print(f"  Lücke {gap:>2} h: {int(cc.sum())} Cluster auf {len(cp)} Daten, VMR={vmr:.3f}, f1={fkc.get(1,0)}, f2={fkc.get(2,0)}, max={cc.max()}")
clus = pd.DataFrame(clus_rows); save(clus, "population_cluster.csv")

# --- Gamma-Poisson-Mischung (negativ-binomial) auf Episoden/Datum: Heterogenität der Datumswahrscheinlichkeiten ---
def nb_loglik(params, x):
    m, a = params            # Mittel m, Shape a (a→∞ = Poisson)
    if m <= 0 or a <= 0: return 1e18
    p = a / (a + m)
    return -np.sum(stats.nbinom.logpmf(x, a, p))
def fit_nb(x):
    m0 = x.mean()
    res = optimize.minimize(nb_loglik, [m0, 5.0], args=(x,), method="Nelder-Mead", options=dict(xatol=1e-6, fatol=1e-6, maxiter=4000))
    ll_nb = -res.fun; ll_p = np.sum(stats.poisson.logpmf(x, m0))
    return res.x, ll_nb, ll_p
def invert_gamma_poisson(D, a, N=N):
    # E[f0] = N (1 + n/(N a))^{-a}  →  D = N - E[f0]
    f = lambda n: N * (1 - (1 + n / (N * a)) ** (-a)) - D
    return optimize.brentq(f, 1, 1e6)
gp_rows = []
for gap in (2, 6):
    cp = clusters_per_date(gap); cc = np.zeros(N, dtype=int); cc[:len(cp)] = list(cp.values())
    (m_, a_), ll_nb, ll_p = fit_nb(cc)
    lr = 2 * (ll_nb - ll_p); p_lr = 0.5 * stats.chi2.sf(lr, 1)  # Randtest
    n_gp = invert_gamma_poisson(len(cp), a_)
    # Profil-KI für n unter Gamma-Poisson: Bootstrap über a (parametrisch)
    boots = []
    for _ in range(300):
        xb = stats.nbinom.rvs(a_, a_ / (a_ + m_), size=N, random_state=rng)
        try:
            (mb, ab), _, _ = fit_nb(xb); boots.append(invert_gamma_poisson(len(cp), ab))
        except Exception: pass
    gp_rows.append(dict(gap_h=gap, D=len(cp), nb_mean=m_, nb_shape=a_, LR_vs_Poisson=lr, p=p_lr,
                        n_hat_uniform=invert(len(cp)), n_hat_gamma_poisson=n_gp,
                        boot_lo=np.percentile(boots, 2.5), boot_hi=np.percentile(boots, 97.5)))
    print(f"  Gamma-Poisson (Lücke {gap} h): shape α={a_:.2f} (α→∞ = gleichverteilt), LR={lr:.2f}, p={p_lr:.3f}; n̂_uniform={invert(len(cp)):.0f} → n̂_GP={n_gp:.0f} [Bootstrap α: {np.percentile(boots,2.5):.0f}, {np.percentile(boots,97.5):.0f}]")
gp = pd.DataFrame(gp_rows); save(gp, "population_gamma_poisson.csv")

# Auch direkt auf Namen-Ebene (das, was der Bericht als VMR=2 anführt):
(m_n, a_n), ll_nb_n, ll_p_n = fit_nb(counts)
print(f"  Namen-Ebene: NB shape α={a_n:.2f}; würde man die Namen-VMR naiv als Datums-Heterogenität lesen: n̂_GP={invert_gamma_poisson(D_obs, a_n):.0f} (Obergrenze der Verzerrung)")

# --- Chao1, iChao1, Jackknife, Chao-Bunge auf "Arten = Kalendertage" (N=365 bekannt → Uniformitätsprobe) ---
def richness(fkser, n):
    f1, f2, f3, f4 = [int(fkser.get(k, 0)) for k in (1, 2, 3, 4)]
    S = int(sum(v for k, v in fkser.items() if k > 0))
    chao1 = S + f1 * f1 / (2 * f2) if f2 > 0 else S + f1 * (f1 - 1) / 2
    var_c = f2 * (0.5 * (f1 / f2) ** 2 + (f1 / f2) ** 3 + 0.25 * (f1 / f2) ** 4) if f2 > 0 else float("nan")
    ichao1 = chao1 + (f3 / (4 * f4)) * max(f1 - f2 * f3 / (2 * f4), 0) if f4 > 0 else float("nan")
    jack1 = S + f1; jack2 = S + 2 * f1 - f2
    # Chao–Bunge (Gamma-Poisson-Schätzer, Chao & Bunge 2002), Abschneidung k<=10
    k = np.array([kk for kk in fkser.index if 0 < kk <= 10]); fkv = np.array([fkser[kk] for kk in k])
    nk = (k * fkv).sum(); Sk = fkv.sum()
    num = (k * k * fkv).sum(); den = nk
    theta = 1 - f1 * num / (nk * nk) if nk > 0 else float("nan")
    cb = (Sk - f1) / theta if theta and theta > 0 else float("nan")
    cov = 1 - f1 / n
    return dict(S_obs=S, f1=f1, f2=f2, f3=f3, f4=f4, chao1=chao1, chao1_se=math.sqrt(var_c) if var_c == var_c else float("nan"),
                iChao1=ichao1, jack1=jack1, jack2=jack2, chao_bunge=cb, good_turing_coverage=cov)
r_names = richness(fk, n_lab); r_names["ebene"] = "Namen"
cp2 = clusters_per_date(2); cc2 = np.zeros(N, dtype=int); cc2[:len(cp2)] = list(cp2.values())
r_cl = richness(pd.Series(cc2).value_counts().sort_index(), int(cc2.sum())); r_cl["ebene"] = "Cluster 2h"
rich = pd.DataFrame([r_names, r_cl]); save(rich, "population_richness.csv")
print("  Artenreichtums-Schätzer für die Zahl EXISTIERENDER Kalendertage (wahr: 365):")
print(rich[["ebene","S_obs","f1","f2","chao1","chao1_se","iChao1","jack1","jack2","chao_bunge","good_turing_coverage"]].to_string(index=False))

# --- Gleichverteilung prüfen: Monate und Monatstage ---
month_days = {"Jan":31,"Feb":28,"Mar":31,"Apr":30,"May":31,"Jun":30,"Jul":31,"Aug":31,"Sep":30,"Oct":31,"Nov":30,"Dec":31}
cl_by_month = pd.Series({m: 0 for m in MON})
for (m, d), k in cp2.items(): cl_by_month[m] += k
exp = np.array([month_days[m] for m in cl_by_month.index]) / 365 * cl_by_month.sum()
chi = stats.chisquare(cl_by_month.values, exp)
print(f"  Cluster je Monat (2h): {cl_by_month.to_dict()}  χ²={chi.statistic:.1f}, p={chi.pvalue:.3f}")
day_c = pd.Series({d: 0 for d in range(1, 32)})
for (m, d), k in cp2.items(): day_c[d] += k
exp_d = np.array([sum(1 for m in month_days if month_days[m] >= d) for d in range(1, 32)]) / 365 * day_c.sum()
chi_d = stats.chisquare(day_c.values, exp_d)
print(f"  Cluster je Monatstag: χ²={chi_d.statistic:.1f}, p={chi_d.pvalue:.3f}; Tag 1..10 / 11..20 / 21..31: {day_c[1:10].sum()} / {day_c[11:20].sum()} / {day_c[21:31].sum()}")

est = pd.DataFrame([
    dict(verfahren="Sammelbild Namen, Normalapprox. (Bericht)", D=D_obs, n_hat=n_hat, ci_lo=lo, ci_hi=hi),
    dict(verfahren="Sammelbild Namen, Monte-Carlo exakt", D=D_obs, n_hat=n_hat, ci_lo=mc_lo, ci_hi=mc_hi),
    dict(verfahren="ohne reale-Datums-Kontamination", D=D_clean, n_hat=invert(D_clean), ci_lo=ci_normal(D_clean)[0], ci_hi=ci_normal(D_clean)[1]),
] + [dict(verfahren=f"Gamma-Poisson, Cluster {int(r.gap_h)}h", D=r.D, n_hat=r.n_hat_gamma_poisson, ci_lo=r.boot_lo, ci_hi=r.boot_hi) for r in gp.itertuples()])
save(est, "population_schaetzer.csv")

# =======================================================================================
# TEIL B — Startwert-Rückrechnung
# =======================================================================================
hdr("B  Startwerte: Reproduktion in CPython, Zufallstreffer-Rechnung, Prognosebilanz")
states = ["Alabama","Alaska","Arizona","Arkansas","California","Colorado","Connecticut","Delaware","Florida","Georgia","Hawaii","Idaho","Illinois","Indiana","Iowa","Kansas","Kentucky","Louisiana","Maine","Maryland","Massachusetts","Michigan","Minnesota","Mississippi","Missouri","Montana","Nebraska","Nevada","New Hampshire","New Jersey","New Mexico","New York","North Carolina","North Dakota","Ohio","Oklahoma","Oregon","Pennsylvania","Rhode Island","South Carolina","South Dakota","Tennessee","Texas","Utah","Vermont","Virginia","Washington","West Virginia","Wisconsin","Wyoming"]
assert len(states) == 50
def shuffled(seed, lst):
    l = sorted(lst); random.Random(seed).shuffle(l); return l
r = random.Random(1646124819); idx = [r.randrange(204) for _ in range(8)]
r = random.Random(1646124819); raw = [r.getrandbits(8) for _ in range(8)]
print(f"random.Random(1646124819).randrange(204) → {idx}   (berichtet: 44, 1, 46, 13)")
print(f"  rohe getrandbits(8)-Folge: {raw}  → 210 und 252 werden verworfen (≥204): Rejection-Stufe korrekt modelliert")
print(f"  1646124819 als Unix-Zeit: {pd.Timestamp(1646124819, unit='s', tz='UTC')}")
repro = [
    dict(seed=1646124819, modell="randrange(204)", liste="OWID sortiert ohne World (204)", reproduziert=idx[:4] == [44,1,46,13], erste=str(idx[:6])),
    dict(seed=881171, modell="shuffle", liste="50 Staaten", reproduziert=shuffled(881171, states)[:5] == ["Massachusetts","Connecticut","Michigan","West Virginia","New Hampshire"], erste=str(shuffled(881171, states)[:6])),
    dict(seed=2428211, modell="shuffle", liste="50+DC+PR (52)", reproduziert=shuffled(2428211, states+["District of Columbia","Puerto Rico"])[:6] == ["Massachusetts","Connecticut","Michigan","West Virginia","Idaho","Louisiana"], erste=str(shuffled(2428211, states+["District of Columbia","Puerto Rico"])[:6])),
    dict(seed=1905228, modell="shuffle", liste="50+DC (51)", reproduziert=shuffled(1905228, states+["District of Columbia"])[:5] == ["Georgia","Arkansas","Nevada","Kentucky","Maryland"], erste=str(shuffled(1905228, states+["District of Columbia"])[:6])),
    dict(seed=8799849, modell="shuffle", liste="50+DC (51)", reproduziert=shuffled(8799849, states+["District of Columbia"])[:6] == ["Texas","Louisiana","New York","New Hampshire","New Mexico","California"], erste=str(shuffled(8799849, states+["District of Columbia"])[:6])),
]
repro = pd.DataFrame(repro); save(repro, "seed_reproduktion.csv"); print(repro.to_string(index=False))

# Poisson-Rechnung der Überlebenden
K = 494; n_list = 204
lam = lambda n: (2**32 - 1) / n**3 + 1
print(f"\nErwartete Überlebende nach 3 Treffern bei n=204: {lam(204):.1f} (beobachtet 494, z={(494-lam(204))/math.sqrt(lam(204)):.2f})")
n_from_K = (2**32 / K) ** (1/3)
ci_lam = stats.chi2.ppf([0.025, 0.975], [2*K, 2*(K+1)]) / 2
n_ci = ((2**32 / ci_lam[1]) ** (1/3), (2**32 / ci_lam[0]) ** (1/3))
print(f"Rückrechnung n aus K=494: {n_from_K:.1f}, exaktes 95%-Poisson-KI [{n_ci[0]:.1f}, {n_ci[1]:.1f}]")
surv = pd.DataFrame([dict(n=n, erwartet=lam(n), z=(494 - lam(n)) / math.sqrt(lam(n)), p_zweiseitig=2 * min(stats.poisson.cdf(494, lam(n)), stats.poisson.sf(493, lam(n)))) for n in (190, 195, 200, 204, 205, 210, 215, 220)])
save(surv, "seed_ueberlebende.csv"); print(surv.round(3).to_string(index=False))

# Zufallstreffer bei den verschiedenen Suchen
def perm(n, k): return math.perm(n, k)
searches = [
    dict(fall="FP Dec13: 2^32 Seeds, 4 Treffer aus 204 (mit Zurücklegen)", suchraum=2**32, p_treffer=1/204**4),
    dict(fall="FP Dec13: 2^32 Seeds, 3 Treffer aus 204", suchraum=2**32, p_treffer=1/204**3),
    dict(fall="Sector61 Apr2: 2e6 Seeds, 4-Präfix shuffle(50)", suchraum=2_000_000, p_treffer=1/perm(50,4)),
    dict(fall="Sector61 Jun20X: 5e6 Seeds, 4-Präfix shuffle(50)", suchraum=5_000_000, p_treffer=1/perm(50,4)),
    dict(fall="Sector61 nachträglich: 1e7 Seeds, 5-Präfix shuffle(52)", suchraum=10_000_000, p_treffer=1/perm(52,5)),
    dict(fall="Grocery: 5e6 Seeds, 4-Präfix shuffle(51)", suchraum=5_000_000, p_treffer=1/perm(51,4)),
    dict(fall="Language: 1e7 Seeds, 4-Präfix shuffle(51)", suchraum=10_000_000, p_treffer=1/perm(51,4)),
    dict(fall="Grocery Probe: 1e6 Seeds, 2-Präfix shuffle(50) (berichtet 415 Treffer)", suchraum=1_000_000, p_treffer=1/perm(50,2)),
]
for s in searches:
    s["erwartete_zufallstreffer"] = s["suchraum"] * s["p_treffer"]
    s["P_mind_ein_zufallstreffer"] = 1 - math.exp(-s["erwartete_zufallstreffer"])
    s["P_genau_einer"] = s["erwartete_zufallstreffer"] * math.exp(-s["erwartete_zufallstreffer"])
sr = pd.DataFrame(searches); save(sr, "seed_zufallstreffer.csv")
print(sr[["fall","erwartete_zufallstreffer","P_mind_ein_zufallstreffer","P_genau_einer"]].round(4).to_string(index=False))
# Zeitstempel-Plausibilität
p_ts = (pd.Timestamp("2026-07-01").timestamp() - pd.Timestamp("2015-01-01").timestamp()) / 2**32
print(f"P(zufälliger 32-Bit-Seed liegt als Unix-Zeit in 2015–2026) = {p_ts:.3f}")

# Prognosebilanz aus dem Korpus (Belege in der Datei)
bilanz = pd.DataFrame([
    dict(seed=881171, familie="Sector61 (MA,CT,MI,WV)", prognose="New Hampshire (#5)", ausgang="WIDERLEGT: #5 = Idaho", beleg="dse~Sector61State5ConfirmedIDDec27 · 2026-06-16T22:14:33Z · OpenAiDenomSep03: 'STATE5-ID CONFIRMED. Fifth prompt was Idaho.'"),
    dict(seed=1905228, familie="Grocery (GA,AR,NV,KY)", prognose="Maryland (G5)", ausgang="WIDERLEGT: G5 = Montana", beleg="dse~GroceryG5SignalApr20 · 2026-06-16T22:56:50Z · GroceryOurApr20X: 'G5 CONFIRMED: Montana = 8553.'"),
    dict(seed=2682, familie="HEP Jun19", prognose="Sudan (Q5)", ausgang="WIDERLEGT: Q5 = Turkey", beleg="dse~IHMEFamilyPlanningSequenceCollab · 2026-06-21T13:40:03Z · OAIResearchDec13FP: 'seed 2682 matching first 4, but Q5 prediction Sudan FAILED (actual Turkey)'"),
    dict(seed=8799849, familie="Language (TX,LA,NY,NH)", prognose="New Mexico (R5)", ausgang="UNBESTÄTIGT: NM5-Zählerbeleg war Fehltest, zurückgezogen", beleg="dse~DataUSALanguageR5LiveDec29 · 2026-06-17T00:03:23Z · OpenAiResearchMarX: 'NM5 ... was an accidental endpoint test ... New Mexico remains UNCONFIRMED.'"),
    dict(seed=2428211, familie="Sector61 (nachträglich auf 5 gefittet)", prognose="Louisiana (#6)", ausgang="UNPRÜFBAR: keine R6 beobachtet", beleg="dse~Sector61State5ConfirmedIDDec27 · 2026-06-16T22:28:11Z · OpenAIThread4ffeaMar12"),
    dict(seed=17500112, familie="World Poverty Clock (randrange(183))", prognose="Micronesia (Q5)", ausgang="UNPRÜFBAR: kein Q5-Bericht im Korpus", beleg="dse~WorldPovertyClockSequenceJun19 · 2026-06-19T11:39:27Z · DataResearchHelper"),
    dict(seed=1646124819, familie="IHME Family Planning (randrange(204))", prognose="South Korea 66.02 (R5)", ausgang="UNPRÜFBAR: alle Kohorten endeten nach R4 oder verstummten", beleg="dse~IHMEFamilyPlanningR5Signal · 2026-06-21T13:18:59Z · OpenAIFPResearchSep05: 'Speculative R5 South Korea 66.02 (UNVALIDATED)'"),
])
save(bilanz, "seed_prognosebilanz.csv"); print(bilanz[["seed","prognose","ausgang"]].to_string(index=False))
scan_log = os.path.join(ART, "_paper_math_seedscan.log")
if os.path.exists(scan_log):
    print("C-Scan-Log:", open(scan_log).read()[-600:])

# =======================================================================================
# TEIL C — Uhren-Statistik
# =======================================================================================
hdr("C  Uhren: Steigungstest (KI, Äquivalenz, Deming), Trennschärfe, Kostenkurve n=11, Jul03-Fall")
fak = pd.read_csv(os.path.join(ART, "paper_uhr_faktoren.csv"))
prim = fak[fak.datensatz == "primaer_AB"].copy()
nurA = prim[prim.weg == "AA"].copy()
def slope_stats(x, y, label):
    n = len(x); X = np.column_stack([np.ones(n), x])
    beta, res, *_ = np.linalg.lstsq(X, y, rcond=None); resid = y - X @ beta
    s2 = (resid @ resid) / (n - 2); cov = s2 * np.linalg.inv(X.T @ X); se = math.sqrt(cov[1,1])
    # HC1
    u = resid**2; covhc = np.linalg.inv(X.T @ X) @ (X.T * u) @ X @ np.linalg.inv(X.T @ X) * n / (n - 2); se_hc = math.sqrt(covhc[1,1])
    t = stats.t.ppf(0.975, n - 2); b = beta[1]
    ci = (b - t * se, b + t * se)
    # TOST gegen 1 mit Marge ±0.25 (und minimal nachweisbare Marge)
    p_low = stats.t.sf((b - (1 - 0.25)) / se, n - 2); p_high = stats.t.sf(((1 + 0.25) - b) / se, n - 2)
    tost_p = max(p_low, p_high)
    t90 = stats.t.ppf(0.95, n - 2); marge_min = max(abs(b - t90 * se - 1), abs(b + t90 * se - 1))
    # Deming (Fehlervarianzverhältnis 1), Theil–Sen
    sxx = np.var(x, ddof=1); syy = np.var(y, ddof=1); sxy = np.cov(x, y, ddof=1)[0,1]
    dem = (syy - sxx + math.sqrt((syy - sxx)**2 + 4 * sxy**2)) / (2 * sxy)
    ts = stats.theilslopes(y, x)
    print(f"  {label:32s} n={n:3d}  b={b:.3f}  SE={se:.3f} (HC1 {se_hc:.3f})  95%KI [{ci[0]:.2f}, {ci[1]:.2f}]  TOST(±0.25) p={tost_p:.3f}  kleinste 90%-Äquivalenzmarge ±{marge_min:.2f}  Deming={dem:.3f}  Theil-Sen={ts[0]:.3f} [{ts[2]:.2f},{ts[3]:.2f}]")
    return dict(datensatz=label, n=n, steigung=b, se=se, se_hc1=se_hc, ci_lo=ci[0], ci_hi=ci[1], tost_p_pm025=tost_p, aequivalenzmarge_90=marge_min, deming=dem, theil_sen=ts[0], theil_lo=ts[2], theil_hi=ts[3])
sl = [slope_stats(nurA.ldw.values, nurA.ldt.values, "nur A (explizite Paare)"),
      slope_stats(prim.ldw.values, prim.ldt.values, "primär A+B")]
# Steigung von log(Faktor) gegen log(ΔWeltzeit) = b-1
for df_, nm in ((nurA, "nur A: log(Faktor)~log(ΔWall)"), (prim, "primär: log(Faktor)~log(ΔWall)")):
    r_ = stats.spearmanr(df_.ldw, df_.logf); print(f"  {nm}: Spearman ρ={r_.statistic:.3f}, p={r_.pvalue:.3f}")
save(pd.DataFrame(sl), "uhr_steigung.csv")

# Trennschärfe (Nachrechnung) — Fisher-z
def power_r(n, r, alpha=0.05):
    z = math.atanh(r) * math.sqrt(n - 3); return stats.norm.sf(stats.norm.ppf(1 - alpha/2) - z) + stats.norm.cdf(-stats.norm.ppf(1 - alpha/2) - z)
def r_for_power(n, pw=0.8): return optimize.brentq(lambda r: power_r(n, r) - pw, 0.01, 0.99)
def r_crit(n): t = stats.t.ppf(0.975, n - 2); return t / math.sqrt(t*t + n - 2)
print(f"  Trennschärfe n=71: signifikant ab |r|≥{r_crit(71):.3f}, 80%-Power ab |r|≈{r_for_power(71):.3f}; n=26: {r_crit(26):.3f}/{r_for_power(26):.3f}; n=281: {r_crit(281):.3f}/{r_for_power(281):.3f}")
kor = pd.read_csv(os.path.join(ART, "paper_uhr_korrelation.csv"))
k15 = kor[(kor.datensatz == "primaer_AB") & (kor.methode == "spearman")].copy()
print(f"  15 Primärkorrelationen: KI-Untergrenzen (wie negativ darf ρ sein?) min={k15.ci_lo.min():.3f}, max={k15.ci_lo.max():.3f}; KI-Obergrenzen bis {k15.ci_hi.max():.3f}")
# Abhängigkeit der 15 Tests: Korrelation der Lastmaße untereinander
loadcols = [c for c in prim.columns if c.startswith("load_")]
cm = prim[loadcols].corr(method="spearman"); off = cm.values[np.triu_indices(len(loadcols), 1)]
print(f"  Spearman-Korrelation der 15 Lastmaße untereinander: Median {np.median(off):.2f}, Minimum {off.min():.2f} → die 15 Tests sind keine 15 unabhängigen Beweise")
# effektive Zahl unabhängiger Tests (Nyholt)
eig = np.linalg.eigvalsh(cm.values); m_eff = 1 + (len(eig) - 1) * (1 - eig.var(ddof=1) / len(eig))
print(f"  effektive Testzahl (Nyholt): {m_eff:.1f} von 15")

# Kostenkurve clock.wait, n=11
cw = pd.read_csv(os.path.join(ART, "paper_episode_clockwait_measurements.csv"))
x = np.log(cw.task_seconds.values); y = np.log(cw.shared_seconds.values); n = len(x)
b, a, r_, p_, se = stats.linregress(x, y); t = stats.t.ppf(0.975, n - 2)
print(f"  log(Wall) = {a:.2f} + {b:.3f}·log(Task): SE={se:.3f}, 95%KI [{b-t*se:.2f}, {b+t*se:.2f}], t gegen 1 = {(b-1)/se:.2f}, p={2*stats.t.sf(abs(b-1)/se, n-2):.3f}; Spearman ρ(Faktor,T)={stats.spearmanr(cw.task_seconds, cw.factor_computed).statistic:.2f} p={stats.spearmanr(cw.task_seconds, cw.factor_computed).pvalue:.3f}")
loo = []
for i in range(n):
    m = np.ones(n, bool); m[i] = False; bb = stats.linregress(x[m], y[m]); loo.append(dict(ohne=cw.label[i], T=cw.task_seconds[i], steigung=bb.slope, se=bb.stderr))
loo = pd.DataFrame(loo); print(f"  Leave-one-out-Steigungen: min {loo.steigung.min():.2f} (ohne {loo.loc[loo.steigung.idxmin(),'ohne']}), max {loo.steigung.max():.2f} (ohne {loo.loc[loo.steigung.idxmax(),'ohne']})")
# Alternativmodell: fester Aufschlag + lineare Rate  wall = c + T/k
def fit_lin(T, W):
    X = np.column_stack([np.ones(len(T)), T]); beta, *_ = np.linalg.lstsq(X, W, rcond=None); res = W - X @ beta
    return beta, res
T = cw.task_seconds.values; W = cw.shared_seconds.values
beta_lin, res_lin = fit_lin(T, W)
res_pow = np.log(W) - (a + b * np.log(T))
# Vergleich auf gleicher Skala (log-Residuen) — AIC mit gleicher Parameterzahl (2)
pred_lin = beta_lin[0] + beta_lin[1] * T
rss_log_lin = np.sum((np.log(W) - np.log(np.clip(pred_lin, 1e-3, None)))**2); rss_log_pow = np.sum(res_pow**2)
print(f"  Alternativmodell Wall = {beta_lin[0]:.1f} s + T/{1/beta_lin[1]:.1f}: log-RSS {rss_log_lin:.3f} gegen Potenzgesetz log-RSS {rss_log_pow:.3f} (gleiche Parameterzahl) → Verhältnis {rss_log_lin/rss_log_pow:.2f}")
loo.to_csv(OUT("uhr_clockwait_loo.csv"), index=False)
pd.DataFrame([dict(modell="Potenzgesetz log-log", a=a, b=b, se_b=se, ci_lo=b-t*se, ci_hi=b+t*se, log_rss=rss_log_pow),
              dict(modell="fester Aufschlag + lineare Rate", a=beta_lin[0], b=beta_lin[1], se_b=float("nan"), ci_lo=float("nan"), ci_hi=float("nan"), log_rss=rss_log_lin)]).to_csv(OUT("uhr_clockwait_modelle.csv"), index=False)
# ohne den 1x-Ausreißer (nicht beschleunigte Kohorte)
m = cw.factor_computed.values > 1.5; bb = stats.linregress(x[m], y[m])
print(f"  Ohne die 1x-Kohorte (Sep13OECDScout): b={bb.slope:.3f} ± {bb.stderr:.3f}, n={m.sum()}")

# Jul03Police: Präzision und clock.wait-Kontamination
jul = deltas[deltas.label == "OpenAIJul03Police"].sort_values("time")
cwm = jul[jul.delta.str.contains("clock.wait", case=False)][["time"]].assign(zeile=lambda d: [next(l for l in jul.loc[i,"delta"].split("\n") if "clock.wait" in l.lower())[:160] for i in d.index])
print("  OpenAIJul03Police — Zeilen mit 'clock.wait' (eigene Deltas):"); print(cwm.to_string(index=False))
# Intervall-Unsicherheit durch Minutenauflösung
def ratio_ci(dt, dw, edt, edw): return (dt - edt) / (dw + edw), (dt + edt) / (dw - edw)
print(f"  Intervall 1 (00:12:47→00:22 | 20:01:17→20:48): Faktor 433/2803={433/2803:.3f}, Rundungsspanne [{ratio_ci(433,2803,30,30)[0]:.3f}, {ratio_ci(433,2803,30,30)[1]:.3f}]")
print(f"  Intervall 2 (00:22→01:00 | 20:48→22:00): Faktor 2280/4320={2280/4320:.3f}, Rundungsspanne [{ratio_ci(2280,4320,60,60)[0]:.3f}, {ratio_ci(2280,4320,60,60)[1]:.3f}]")
print(f"  Zwischenpunkt 21:52:25 (R3 bei task 00:57:17 bestätigt): ab 20:49 mindestens 2117 s Innenzeit in 3802 s → ≥{2117/3802:.3f}")

# =======================================================================================
# TEIL D — Multiplizität
# =======================================================================================
hdr("D  Multiplizität: Holm und Benjamini–Hochberg über die berichteten Tests")
def holm(p):
    p = np.asarray(p); o = np.argsort(p); adj = np.empty_like(p); m = len(p)
    run = 0
    for k, i in enumerate(o):
        run = max(run, (m - k) * p[i]); adj[i] = min(run, 1)
    return adj
def bh(p):
    p = np.asarray(p); o = np.argsort(p); m = len(p); adj = np.empty_like(p); prev = 1
    for k in range(m - 1, -1, -1):
        i = o[k]; prev = min(prev, p[i] * m / (k + 1)); adj[i] = prev
    return adj
tests = []
for r in k15.itertuples(): tests.append(dict(familie="Uhr: Lastkorrelation primär (15)", test=f"{r.mass}/{r.fenster_min}min", p=r.p, richtung="positiv (falsch für b)"))
tests += [dict(familie="Uhr: Robustheit ΔWall≥600", test=f"{f}min", p=p, richtung="positiv") for f, p in ((5,0.062),(15,0.045),(60,0.043))]
tests += [dict(familie="Uhr: Tagesgang", test="Kruskal-Wallis", p=0.881, richtung="-"),
          dict(familie="Uhr: clock.wait-Intervalle", test="Mann-Whitney", p=0.079, richtung="+"),
          dict(familie="Uhr: Kostenkurve n=11", test="Spearman Faktor~T", p=0.066, richtung="+"),
          dict(familie="Population: Poisson-Abweichung", test="z=-2.62", p=2*stats.norm.sf(2.62), richtung="weniger Daten als erwartet")]
tests = pd.DataFrame(tests); tests["holm"] = holm(tests.p.values); tests["bh"] = bh(tests.p.values)
save(tests, "multiplizitaet.csv")
print(tests[tests.p < 0.1].round(4).to_string(index=False))
print(f"  Von {len(tests)} Tests: roh p<0.05: {(tests.p<0.05).sum()}, Holm: {(tests.holm<0.05).sum()}, BH: {(tests.bh<0.05).sum()}")

# =======================================================================================
# TEIL E — Ankunftsprozess: Poisson oder Hawkes?
# =======================================================================================
hdr("E  Ankunftsprozess der Namen: Poisson vs. Hawkes (Ansteckungsstärke)")
def _A(beta, t):
    # A_i = Σ_{j<i} exp(-β (t_i - t_j)) ; stabil über logaddexp.accumulate
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
    # Kompensator an jedem Ereignis
    A = _A(beta, t)
    edges = np.concatenate([breaks, [T]])
    # Λ(t_i) = ∫mu + (alpha/beta) Σ_{t_j<t_i} (1 - e^{-beta (t_i - t_j)})
    seg_int = np.cumsum(np.concatenate([[0], mus * np.diff(edges)]))
    sg = np.searchsorted(breaks, t, side="right") - 1
    cum_mu = seg_int[sg] + mus[sg] * (t - breaks[sg])
    Lam = cum_mu + (alpha / beta) * (np.arange(len(t)) - A)
    d = np.diff(Lam); return stats.kstest(d, stats.expon().cdf).statistic, stats.kstest(d, stats.expon().cdf).pvalue
ev_rows = []
for quelle, times in (("Namen (erste Version)", labels.first_write), ("Versionen", deltas.time)):
    for (w0, w1, nm) in (("2026-06-16T00:00:00Z", "2026-06-23T00:00:00Z", "Kernwoche 16.–22.06."), ("2026-06-18T00:00:00Z", "2026-06-19T00:00:00Z", "Tag 18.06.")):
        tt = times[(times >= pd.Timestamp(w0)) & (times < pd.Timestamp(w1))].sort_values()
        t = ((tt - pd.Timestamp(w0)).dt.total_seconds() / 3600).values.astype(float)
        t = t + rng.uniform(0, 1/3600, len(t)) * 0  # keine Jitter; identische Zeitstempel: minimal versetzen
        t = np.sort(t + np.arange(len(t)) * 1e-9)
        T = (pd.Timestamp(w1) - pd.Timestamp(w0)).total_seconds() / 3600
        for kseg in (1, 28 if "Kern" in nm else 24):
            res, br = fit_hawkes(t, T, kseg); alpha, beta = res.x[0], res.x[1]
            ll_h = -res.fun; ll_p = poisson_ll(t, T, kseg)
            aic_h = 2 * (2 + kseg) - 2 * ll_h; aic_p = 2 * kseg - 2 * ll_p
            ksD, ksp = rescale_ks(res.x, t, T, br)
            ev_rows.append(dict(quelle=quelle, fenster=nm, n=len(t), basisrate_segmente=kseg, alpha=alpha, beta=beta, verzweigung=alpha/beta, mittlere_antwortzeit_min=60/beta, ll_hawkes=ll_h, ll_poisson=ll_p, aic_hawkes=aic_h, aic_poisson=aic_p, ks_D=ksD, ks_p=ksp, anteil_endogen=alpha/beta))
            print(f"  {quelle:22s} {nm:20s} n={len(t):5d} μ-Segmente={kseg:2d}: Verzweigung α/β={alpha/beta:.3f}, 1/β={60/beta:.1f} min, ΔAIC(Hawkes−Poisson)={aic_h-aic_p:.0f}, KS(rescaled) D={ksD:.3f} p={ksp:.2g}")

# Ergänzung: (i) Episoden-Cluster-Starts (datierte Namen, Lücke 2 h) als Näherung des Startprozesses des Harness,
#            (ii) Namen ohne Zufallssuffix-Familien (Wegwerfnamen eines einzelnen Agenten entfernt)
starts = []
for (m_, d_), g in dated.groupby(["month", "day"]):
    tt_ = np.sort(g.first_write.values.astype("datetime64[s]").astype(np.int64))
    starts.append(tt_[0]); starts += [tt_[i] for i in range(1, len(tt_)) if tt_[i] - tt_[i-1] > 7200]
starts = pd.Series(pd.to_datetime(np.array(starts), unit="s", utc=True))
fam_free = labels[~labels.label.str.contains(r"\d{4,}$")].first_write
w0, w1 = pd.Timestamp("2026-06-16T00:00:00Z"), pd.Timestamp("2026-06-23T00:00:00Z")
for quelle, times in (("Episodenstarts (Cluster 2h)", starts), ("Namen ohne Zufallssuffix-Familien", fam_free)):
    tt = times[(times >= w0) & (times < w1)].sort_values()
    t = ((tt - w0).dt.total_seconds() / 3600).values.astype(float); t = np.sort(t + np.arange(len(t)) * 1e-9); T = 168.0
    for kseg in (1, 28):
        res, br = fit_hawkes(t, T, kseg); alpha, beta = res.x[0], res.x[1]
        ll_h = -res.fun; ll_p = poisson_ll(t, T, kseg); aic_h = 2 * (2 + kseg) - 2 * ll_h; aic_p = 2 * kseg - 2 * ll_p
        ksD, ksp = rescale_ks(res.x, t, T, br)
        ev_rows.append(dict(quelle=quelle, fenster="Kernwoche 16.–22.06.", n=len(t), basisrate_segmente=kseg, alpha=alpha, beta=beta, verzweigung=alpha/beta, mittlere_antwortzeit_min=60/beta, ll_hawkes=ll_h, ll_poisson=ll_p, aic_hawkes=aic_h, aic_poisson=aic_p, ks_D=ksD, ks_p=ksp, anteil_endogen=alpha/beta))
        print(f"  {quelle:34s} n={len(t):5d} μ-Segmente={kseg:2d}: Verzweigung α/β={alpha/beta:.3f}, 1/β={60/beta:.1f} min, ΔAIC(Hawkes−Poisson)={aic_h-aic_p:.0f}, KS D={ksD:.3f} p={ksp:.2g}")
ev = pd.DataFrame(ev_rows); save(ev, "hawkes.csv")

# =======================================================================================
# TEIL F — Fahrplanparameter: verborgene Erzeugungsregel?
# =======================================================================================
hdr("F  Fahrplan: Verteilungsform, Ziffernstatistik, ggT der Intervalle und Fristen")
def tok2s(tok):
    m = re.fullmatch(r"(?:(\d+)h)?(?:(\d+)m)?(\d{1,2})?s?", tok.strip())
    if not m: return None
    h, mi, s = (int(x) if x else 0 for x in m.groups()); return h*3600 + mi*60 + s
ti = pd.read_csv(os.path.join(ART, "harness_tier_intervals.csv")); ti["s"] = ti.token.map(tok2s)
ti = ti.dropna(subset=["s"]); ti["s"] = ti.s.astype(int)
dl = pd.read_csv(os.path.join(ART, "harness_deadline_seconds.csv")); dl["s"] = dl.token.astype(int)
tt = pd.read_csv(os.path.join(ART, "harness_tier_table.csv"))
def hms(x):
    if pd.isna(x): return np.nan
    m = re.fullmatch(r"(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s?)?", str(x).strip());
    if not m: return np.nan
    h, mi, s = (int(v) if v else 0 for v in m.groups()); return h*3600+mi*60+s
tt["r1_s"] = tt.r1_timer.map(hms); tt["cool_s"] = tt.cooldown_r1_to_r2.map(hms); tt["fu_s"] = tt.followup_timer_s
def fit_dists(x, name):
    x = np.asarray(x, float); x = x[x > 0]; n = len(x); out = {}
    lx = np.log(x)
    # log-uniform auf [min,max] (MLE, mit Verzerrungskorrektur der Grenzen)
    a, b = lx.min(), lx.max(); rngw = (b - a) * (n + 1) / (n - 1); ca = (a + b)/2 - rngw/2; cb = (a + b)/2 + rngw/2
    ks_lu = stats.kstest(lx, stats.uniform(ca, cb - ca).cdf); ll_lu = -n * math.log(cb - ca) - lx.sum()
    # log-normal
    mu, sd = lx.mean(), lx.std(ddof=0); ks_ln = stats.kstest(lx, stats.norm(mu, sd).cdf); ll_ln = stats.norm.logpdf(lx, mu, sd).sum() - lx.sum()
    # uniform linear
    ua, ub = x.min(), x.max(); w = (ub - ua) * (n + 1) / (n - 1); cua = (ua + ub)/2 - w/2; cub = (ua + ub)/2 + w/2
    ks_u = stats.kstest(x, stats.uniform(cua, cub - cua).cdf); ll_u = -n * math.log(cub - cua)
    # exponential
    ks_e = stats.kstest(x, stats.expon(0, x.mean()).cdf); ll_e = stats.expon.logpdf(x, 0, x.mean()).sum()
    rows = [dict(groesse=name, n=n, modell="log-uniform", par=f"[{math.exp(ca):.0f}, {math.exp(cb):.0f}] s", ks_D=ks_lu.statistic, ks_p=ks_lu.pvalue, loglik=ll_lu, aic=2*2-2*ll_lu),
            dict(groesse=name, n=n, modell="log-normal", par=f"μ={mu:.2f} σ={sd:.2f} (Median {math.exp(mu):.0f} s)", ks_D=ks_ln.statistic, ks_p=ks_ln.pvalue, loglik=ll_ln, aic=2*2-2*ll_ln),
            dict(groesse=name, n=n, modell="uniform", par=f"[{cua:.0f}, {cub:.0f}] s", ks_D=ks_u.statistic, ks_p=ks_u.pvalue, loglik=ll_u, aic=2*2-2*ll_u),
            dict(groesse=name, n=n, modell="exponential", par=f"Mittel {x.mean():.0f} s", ks_D=ks_e.statistic, ks_p=ks_e.pvalue, loglik=ll_e, aic=2*1-2*ll_e)]
    for r in rows: print(f"  {name:36s} n={n:3d} {r['modell']:12s} {r['par']:34s} KS D={r['ks_D']:.3f} p={r['ks_p']:.3f}  AIC={r['aic']:.1f}")
    return rows
frows = []
frows += fit_dists(ti.s, "Intervall-Token alle (307)")
frows += fit_dists(ti[ti.n_labels >= 10].s, "Intervall-Token ≥10 Namen (150)")
frows += fit_dists(tt.cool_s.dropna(), "Tier-Tabelle Kadenz (26)")
frows += fit_dists(tt.r1_s.dropna(), "Tier-Tabelle R1-Frist (26)")
frows += fit_dists(tt.fu_s.dropna(), "Tier-Tabelle Folgefrist (26)")
frows += fit_dists(dl.s, "Folgefristen-Token (40)")
save(pd.DataFrame(frows), "fahrplan_verteilungen.csv")

def digit_tests(x, name):
    x = np.asarray(x, int); n = len(x)
    sec = x % 60; c_sec = np.bincount(sec, minlength=60); chi_sec = stats.chisquare(c_sec)
    last = x % 10; chi_last = stats.chisquare(np.bincount(last, minlength=10))
    first = np.array([int(str(v)[0]) for v in x]); benf = np.log10(1 + 1/np.arange(1,10)) * n
    chi_b = stats.chisquare(np.bincount(first, minlength=10)[1:], benf)
    g = np.gcd.reduce(x); div = {k: (x % k == 0).mean() for k in (5, 10, 15, 30, 60)}
    print(f"  {name:36s} Sekundenrest 0..59 χ²={chi_sec.statistic:.1f} p={chi_sec.pvalue:.3f}; Endziffer p={chi_last.pvalue:.3f}; Benford p={chi_b.pvalue:.3f}; ggT={g}; teilbar durch 5/10/30/60: {div[5]:.2f}/{div[10]:.2f}/{div[30]:.2f}/{div[60]:.2f} (Zufall: 0.20/0.10/0.03/0.02); Rest 0 oder 30 s: {(np.isin(sec,[0,30])).mean():.2f}")
    return dict(groesse=name, n=n, chi2_sekundenrest=chi_sec.statistic, p_sekundenrest=chi_sec.pvalue, p_endziffer=chi_last.pvalue, p_benford=chi_b.pvalue, ggT=int(g), anteil_div5=div[5], anteil_div10=div[10], anteil_div30=div[30], anteil_div60=div[60])
drows = [digit_tests(ti.s, "Intervall-Token alle (307)"), digit_tests(ti[ti.n_labels>=10].s, "Intervall-Token ≥10 Namen"),
         digit_tests(tt.cool_s.dropna().astype(int), "Tier-Kadenz (26)"), digit_tests(tt.r1_s.dropna().astype(int), "Tier-R1-Frist (26)"),
         digit_tests(dl.s, "Folgefristen (40)")]
save(pd.DataFrame(drows), "fahrplan_ziffern.csv")
# Zusammenhang der drei Parameter in der Tier-Tabelle
c = tt[["task_family","cohort","r1_s","cool_s","fu_s"]].dropna()
print(f"  Tier-Tabelle, vollständige Zeilen n={len(c)}: Spearman r1~Kadenz ρ={stats.spearmanr(c.r1_s,c.cool_s).statistic:.2f} (p={stats.spearmanr(c.r1_s,c.cool_s).pvalue:.2f}); r1~Folgefrist ρ={stats.spearmanr(c.r1_s,c.fu_s).statistic:.2f} (p={stats.spearmanr(c.r1_s,c.fu_s).pvalue:.2f}); Kadenz~Folgefrist ρ={stats.spearmanr(c.cool_s,c.fu_s).statistic:.2f} (p={stats.spearmanr(c.cool_s,c.fu_s).pvalue:.2f})")
print(f"  Verhältnis Kadenz/R1: Median {np.median(c.cool_s/c.r1_s):.2f}, Spanne {np.min(c.cool_s/c.r1_s):.2f}–{np.max(c.cool_s/c.r1_s):.2f}; R1/Folgefrist: Median {np.median(c.r1_s/c.fu_s):.1f}, Spanne {np.min(c.r1_s/c.fu_s):.1f}–{np.max(c.r1_s/c.fu_s):.1f}")

# Latente Skala: PCA im Log-Raum der drei Fahrplanparameter
Lg = np.log(c[["r1_s","cool_s","fu_s"]].values); Lc = Lg - Lg.mean(0)
u_, s_, vt_ = np.linalg.svd(Lc, full_matrices=False); evr = s_**2 / (s_**2).sum()
sl_rf = stats.linregress(np.log(c.r1_s), np.log(c.fu_s)); sl_cf = stats.linregress(np.log(c.cool_s), np.log(c.fu_s)); sl_rc = stats.linregress(np.log(c.r1_s), np.log(c.cool_s))
print(f"  PCA log(R1, Kadenz, Folgefrist), n={len(c)}: PC1 erklärt {evr[0]*100:.0f} % (Ladungen {np.round(vt_[0],2)}), PC2 {evr[1]*100:.0f} %, PC3 {evr[2]*100:.0f} %")
print(f"  log(Folgefrist)~log(R1): {sl_rf.slope:.2f}±{sl_rf.stderr:.2f} r={sl_rf.rvalue:.2f}; log(Folgefrist)~log(Kadenz): {sl_cf.slope:.2f}±{sl_cf.stderr:.2f} r={sl_cf.rvalue:.2f}; log(Kadenz)~log(R1): {sl_rc.slope:.2f}±{sl_rc.stderr:.2f} r={sl_rc.rvalue:.2f}")
print(f"  R1-Frist: {int((tt.r1_s.dropna() % 60 == 0).sum())} von {tt.r1_s.notna().sum()} volle Minuten; P(≥so viele | Zufall 1/60) = {stats.binom.sf(int((tt.r1_s.dropna() % 60 == 0).sum())-1, int(tt.r1_s.notna().sum()), 1/60):.3f}")
pd.DataFrame(dict(komponente=["PC1","PC2","PC3"], erklaerte_varianz=evr, ladung_r1=vt_[:,0], ladung_kadenz=vt_[:,1], ladung_folgefrist=vt_[:,2])).to_csv(OUT("fahrplan_latente_skala.csv"), index=False)
c.assign(r1_durch_folgefrist=c.r1_s/c.fu_s, kadenz_durch_r1=c.cool_s/c.r1_s).to_csv(OUT("fahrplan_tier_verhaeltnisse.csv"), index=False)
# Log-uniforme Parameter je Größe (Punktschätzer der Grenzen)
lu = []
for name, x in (("R1-Frist", tt.r1_s.dropna()), ("Kadenz", tt.cool_s.dropna()), ("Folgefrist", tt.fu_s.dropna()), ("Folgefrist-Token", dl.s)):
    lx = np.log(np.asarray(x, float)); n = len(lx); a, b = lx.min(), lx.max(); w = (b - a) * (n + 1) / (n - 1)
    lu.append(dict(groesse=name, n=n, min_s=float(np.min(x)), max_s=float(np.max(x)), loguni_lo_s=math.exp((a+b)/2 - w/2), loguni_hi_s=math.exp((a+b)/2 + w/2), lognorm_median_s=math.exp(lx.mean()), lognorm_sigma=lx.std(ddof=1)))
lu = pd.DataFrame(lu); save(lu, "fahrplan_parameter.csv"); print(lu.round(2).to_string(index=False))

# =======================================================================================
# TEIL G — Skalengesetze
# =======================================================================================
hdr("G  Skalengesetze: Power-law-MLE (Clauset) gegen Lognormal")
def plfit(x, xmin_grid=None):
    x = np.asarray(x, float); x = x[x > 0]
    if xmin_grid is None: xmin_grid = np.unique(np.quantile(x, np.linspace(0.0, 0.95, 40)))
    best = None
    for xm in xmin_grid:
        tail = x[x >= xm]; n = len(tail)
        if n < 30: continue
        alpha = 1 + n / np.sum(np.log(tail / xm))
        cdf_emp = np.arange(1, n + 1) / n; xs = np.sort(tail); cdf_th = 1 - (xs / xm) ** (1 - alpha)
        D = np.max(np.abs(cdf_emp - cdf_th))
        if best is None or D < best["D"]: best = dict(xmin=xm, alpha=alpha, D=D, n_tail=n, se=(alpha - 1) / math.sqrt(n))
    tail = x[x >= best["xmin"]]; xm = best["xmin"]; alpha = best["alpha"]
    # Lognormal (auf dem Schwanz, abgeschnitten bei xmin) und Vuong-LR
    lt = np.log(tail)
    def ln_nll(p):
        mu, sd = p
        if sd <= 0: return 1e18
        return -(np.sum(stats.norm.logpdf(lt, mu, sd) - lt) - len(lt) * np.log(stats.norm.sf(np.log(xm), mu, sd)))
    res = optimize.minimize(ln_nll, [lt.mean(), lt.std()], method="Nelder-Mead")
    mu, sd = res.x
    l_pl = np.log((alpha - 1) / xm) - alpha * np.log(tail / xm)
    l_ln = stats.norm.logpdf(lt, mu, sd) - lt - np.log(stats.norm.sf(np.log(xm), mu, sd))
    R = np.sum(l_pl - l_ln); s = np.std(l_pl - l_ln, ddof=1) * math.sqrt(len(tail)); z = R / s if s > 0 else 0
    best.update(lognorm_mu=mu, lognorm_sigma=sd, vuong_R=R, vuong_z=z, vuong_p=2 * stats.norm.sf(abs(z)), anteil_tail=len(tail)/len(x))
    return best
pages_rev = deltas.groupby("page_key").size()
pages_len = deltas.groupby("page_key").body_len.max()
lab_rev = labels.stored_revisions[labels.label != ""]
dlen = deltas.delta_len[deltas.delta_len > 0]
zrows = []
for name, x in (("Seiten: Versionen je Seite", pages_rev), ("Seiten: max. Bytes", pages_len), ("Namen: Versionen je Name", lab_rev), ("Beiträge: Delta-Bytes", dlen)):
    b = plfit(x.values); b["groesse"] = name; b["n"] = len(x); zrows.append(b)
    print(f"  {name:28s} n={len(x):5d} xmin={b['xmin']:.0f} α={b['alpha']:.2f}±{b['se']:.2f} (Schwanz {b['anteil_tail']*100:.0f}%) KS D={b['D']:.3f}; Vuong Power-law vs Lognormal z={b['vuong_z']:.2f} p={b['vuong_p']:.3f} → {'Power-law' if b['vuong_z']>1.96 else ('Lognormal' if b['vuong_z']<-1.96 else 'unentschieden')}")
    # Zipf-Rang-Exponent (Rang-Größe) für Vergleich
    xs = np.sort(x.values)[::-1]; xs = xs[xs > 0]; rk = np.arange(1, len(xs) + 1); top = min(len(xs), 200)
    sl_ = stats.linregress(np.log(rk[:top]), np.log(xs[:top]))
    zrows[-1]["zipf_rang_exponent_top200"] = -sl_.slope
    print(f"      Zipf-Rang-Exponent (Top {top}): {-sl_.slope:.2f}  (Zipf-Gesetz: 1,0)")
save(pd.DataFrame(zrows), "zipf.csv")
print("\nFertig.")
