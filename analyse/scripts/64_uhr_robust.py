#!/usr/bin/env python3
"""64_uhr_robust.py — Robustheitsprüfungen zu Uhr, Fahrplan-Skala und CVD-Horizont
(Reviewer-Forderungen zu paper/main.tex §Clock-rate measurement, §Three clocks, §Death).

Teil A  Streckfaktoren: Paar- vs. Namensebene, Cluster-Bootstrap über Namen, drei Mitternachts-Varianten.
        Faktoren werden aus analyse/artefakte/paper_uhr_taskzeiten.csv REKONSTRUIERT (Re-Implementierung
        von 50_uhr_auslastung.build_factors, dort Zeilen 213-251) und gegen paper_uhr_faktoren.csv
        (datensatz == primaer_AB, n=71) verifiziert, bevor Varianten gerechnet werden.
Teil B  Latente Fahrplanskala: die 15 vollständigen Zeilen der kuratierten Tier-Tabelle mit Provenienz je
        Wert, Leave-one-row-out-PCA (Re-Implementierung von 53_mathematik.py Zeilen 526-530).
Teil C  CVD-Abschaltung als Intervall [letztes Lebenszeichen ; erste belegte Abwesenheit] je Kohorte,
        Evidenzklasse server | self_report | audit, Fenster/CV je Geschwindigkeitsklasse nur aus
        server-belegten Zeilen.

Nur lesend gegenüber 50_uhr_auslastung.py und 54_horizont.py. Alle Pfade relativ zum Skript.
"""
from __future__ import annotations
import os, re, json, math, warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
ART = os.path.join(BASE, "artefakte")
OUT = lambda n: os.path.join(ART, n)
PAPER = os.path.join(os.path.dirname(BASE), "paper")
TABLES = os.path.join(PAPER, "tables")
FIGDATA = os.path.join(PAPER, "figures", "data")
os.makedirs(TABLES, exist_ok=True); os.makedirs(FIGDATA, exist_ok=True)
SEED = 20260909
NBOOT = 4000
LOG = open(OUT("_paper_robust_uhr.log"), "w", encoding="utf-8")


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True); LOG.write(s + "\n"); LOG.flush()


def hdr(t):
    log("\n" + "=" * 100 + "\n" + t + "\n" + "=" * 100)


def q(x, p):
    return float(np.nanpercentile(np.asarray(x, float), p))


def ols_slope(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    X = np.column_stack([np.ones(len(x)), x])
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    r = y - X @ b
    se = math.sqrt(np.linalg.pinv(X.T @ X)[1, 1] * (r @ r) / max(len(x) - 2, 1))
    return float(b[1]), float(se)


# =====================================================================================================
# TEIL A — Streckfaktoren
# =====================================================================================================
hdr("A  Streckfaktoren: Rekonstruktion, Namensebene, Cluster-Bootstrap, Mitternacht")

tz = pd.read_csv(OUT("paper_uhr_taskzeiten.csv"))
tz["wall_time"] = pd.to_datetime(tz.wall_time, utc=True)
# In 50_uhr_auslastung.py ist task_fakedate ein String ("" wenn leer); im CSV wird "" zu NaN.
# NaN wäre in `a.fd and b.fd and a.fd != b.fd` wahrheitswertig -> Paare würden fälschlich verworfen.
tz["task_fakedate"] = tz.task_fakedate.fillna("").astype(str)
tz["evidence_snippet"] = tz.evidence_snippet.fillna("").astype(str)


def build_factors(tz: pd.DataFrame, minwall=120.0, fmin=0.05, fmax=30.0,
                  roll="exclude", roll_max_s=6 * 3600, maxwall=None, fakedate_guard=True) -> pd.DataFrame:
    """Re-Implementierung von 50_uhr_auslastung.build_factors (Zeilen 213-251).
    roll = 'exclude'  : negative Innen-Deltas verwerfen (Status quo, allow_roll=False)
    roll = 'correct'  : +24 h nur wenn korrigiertes Innen-Delta <= roll_max_s UND Welt-Delta <= roll_max_s
    roll = 'correct_all': +24 h ohne Einschränkung (nur zur Einordnung; entspricht allow_roll=True)
    maxwall: zusätzliche Obergrenze für das Welt-Delta (Variante 'nur sicher kurze Intervalle')."""
    out = []
    for lab, g in tz.groupby("label"):
        g = g.groupby(["rev_id", "wall_time"], as_index=False).agg(
            task_seconds=("task_seconds", "median"),
            ev=("evidence_snippet", "first"), weg=("weg", "first"),
            page_key=("page_key", "first"), fd=("task_fakedate", "first"),
            wall_stated=("wall_seconds_stated", "median"))
        g = g.sort_values("wall_time").reset_index(drop=True)
        if len(g) < 2:
            continue
        for i in range(len(g) - 1):
            a, b = g.iloc[i], g.iloc[i + 1]
            dw = (b.wall_time - a.wall_time).total_seconds()
            if dw < minwall:
                continue
            if maxwall is not None and dw > maxwall:
                continue
            if fakedate_guard and a.fd and b.fd and a.fd != b.fd:
                continue
            dt = b.task_seconds - a.task_seconds
            nroll = 0
            if dt < 0:
                if roll == "exclude":
                    continue
                if roll == "correct" and not (dt + 86400 <= roll_max_s and dw <= roll_max_s):
                    continue
                dt += 86400; nroll = 1
            if dt <= 0:
                continue
            f = dt / dw
            if not (fmin <= f <= fmax):
                continue
            out.append(dict(label=lab, t0=a.wall_time, t1=b.wall_time, wall_delta_s=dw, task_delta_s=dt,
                            rollover=nroll, factor=f, weg=a.weg + b.weg, rev0=a.rev_id, rev1=b.rev_id))
    F = pd.DataFrame(out)
    if len(F):
        F["logf"] = np.log(F.factor); F["ldw"] = np.log(F.wall_delta_s); F["ldt"] = np.log(F.task_delta_s)
    return F


AB = tz[tz.weg.isin(["A", "B"])]
F = build_factors(AB)
ref = pd.read_csv(OUT("paper_uhr_faktoren.csv"))
ref = ref[ref.datensatz == "primaer_AB"].copy()
same_n = len(F) == len(ref)
same_vals = same_n and np.allclose(np.sort(F.factor.values), np.sort(ref.factor.values), rtol=0, atol=1e-9)
log(f"[A0] Rekonstruktion primaer_AB: n_rekonstruiert={len(F)} n_referenz={len(ref)} "
    f"labels={F.label.nunique()}/{ref.label.nunique()} identische Faktoren={same_vals} "
    f"Median rekon={F.factor.median():.4f} ref={ref.factor.median():.4f}")
if not same_vals:
    log("[A0] WARNUNG: Rekonstruktion weicht ab — alle folgenden Zahlen sind gegen die Referenz zu prüfen.")
F_A = F[F.weg == "AA"].copy()   # 53_mathematik.py Zeile 284: nurA = prim[prim.weg == 'AA'] (n=39)
log(f"[A0] Teilmenge nur A (weg=='AA', wie 53_mathematik.py Z.284): n={len(F_A)} labels={F_A.label.nunique()}")


def pair_stats(X):
    b, se = ols_slope(X.ldw, X.ldt)
    return dict(n=len(X), labels=X.label.nunique(), median=float(X.factor.median()),
                q25=q(X.factor, 25), q75=q(X.factor, 75), steigung=b, se=se)


def name_level(X):
    """Ein Wert je Name: Median der Faktoren; für die Steigung Median von log(dWall), log(dTask) je Name."""
    N = X.groupby("label").agg(n_paare=("factor", "size"), factor=("factor", "median"),
                               ldw=("ldw", "median"), ldt=("ldt", "median")).reset_index()
    b, se = ols_slope(N.ldw, N.ldt)
    # gewichtete Paar-OLS (Gewicht 1/n_Paare je Name): jeder Name trägt Gesamtgewicht 1
    w = 1.0 / X.groupby("label").factor.transform("size").values
    W = np.sqrt(w); Xd = np.column_stack([np.ones(len(X)), X.ldw.values]) * W[:, None]
    bw, *_ = np.linalg.lstsq(Xd, X.ldt.values * W, rcond=None)
    return N, dict(n=len(N), median=float(N.factor.median()), q25=q(N.factor, 25), q75=q(N.factor, 75),
                   steigung=b, se=se, steigung_gewichtet=float(bw[1]))


def cluster_boot(X, nboot=NBOOT, seed=SEED):
    """Bootstrap über NAMEN: Namen mit Zurücklegen ziehen, alle ihre Paare mitnehmen."""
    rng = np.random.default_rng(seed)
    groups = {k: v for k, v in X.groupby("label")}
    keys = np.array(list(groups.keys()))
    stats = {k: [] for k in ("median_paar", "q25_paar", "q75_paar", "steigung_paar", "median_name",
                             "q25_name", "q75_name", "steigung_name")}
    for _ in range(nboot):
        pick = rng.choice(keys, len(keys), replace=True)
        parts = []
        for j, k in enumerate(pick):
            g = groups[k].copy(); g["cl"] = j; parts.append(g)
        R = pd.concat(parts, ignore_index=True)
        stats["median_paar"].append(R.factor.median()); stats["q25_paar"].append(q(R.factor, 25)); stats["q75_paar"].append(q(R.factor, 75))
        if R.ldw.nunique() > 2:
            stats["steigung_paar"].append(ols_slope(R.ldw, R.ldt)[0])
        N = R.groupby("cl").agg(factor=("factor", "median"), ldw=("ldw", "median"), ldt=("ldt", "median"))
        stats["median_name"].append(N.factor.median()); stats["q25_name"].append(q(N.factor, 25)); stats["q75_name"].append(q(N.factor, 75))
        if N.ldw.nunique() > 2:
            stats["steigung_name"].append(ols_slope(N.ldw, N.ldt)[0])
    return {k: (q(v, 2.5), q(v, 97.5), len(v)) for k, v in stats.items()}


cmp_rows, name_tables, boot_rows = [], [], []
for tag, X in (("primaer_AB", F), ("nur_A", F_A)):
    P = pair_stats(X); N, NL = name_level(X); B = cluster_boot(X)
    N["datensatz"] = tag; name_tables.append(N)
    log(f"[A1] {tag}: PAARE n={P['n']} Namen={P['labels']} Median={P['median']:.3f} IQR=[{P['q25']:.3f},{P['q75']:.3f}] "
        f"Steigung={P['steigung']:.3f}±{P['se']:.3f}")
    log(f"[A1] {tag}: NAMEN n={NL['n']} Median={NL['median']:.3f} IQR=[{NL['q25']:.3f},{NL['q75']:.3f}] "
        f"Steigung(Namensmediane)={NL['steigung']:.3f}±{NL['se']:.3f} Steigung(gewichtete Paar-OLS)={NL['steigung_gewichtet']:.3f}")
    log(f"[A2] {tag}: Cluster-Bootstrap über Namen (B={NBOOT}, seed={SEED}): "
        + "; ".join(f"{k}=[{v[0]:.3f},{v[1]:.3f}]" for k, v in B.items()))
    cmp_rows += [dict(datensatz=tag, ebene="paar", **P, ci_median_lo=B["median_paar"][0], ci_median_hi=B["median_paar"][1],
                      ci_q25_lo=B["q25_paar"][0], ci_q25_hi=B["q25_paar"][1], ci_q75_lo=B["q75_paar"][0], ci_q75_hi=B["q75_paar"][1],
                      ci_steigung_lo=B["steigung_paar"][0], ci_steigung_hi=B["steigung_paar"][1]),
                 dict(datensatz=tag, ebene="name", n=NL["n"], labels=NL["n"], median=NL["median"], q25=NL["q25"], q75=NL["q75"],
                      steigung=NL["steigung"], se=NL["se"], steigung_gewichtet=NL["steigung_gewichtet"],
                      ci_median_lo=B["median_name"][0], ci_median_hi=B["median_name"][1],
                      ci_q25_lo=B["q25_name"][0], ci_q25_hi=B["q25_name"][1], ci_q75_lo=B["q75_name"][0], ci_q75_hi=B["q75_name"][1],
                      ci_steigung_lo=B["steigung_name"][0], ci_steigung_hi=B["steigung_name"][1])]
    for k, v in B.items():
        boot_rows.append(dict(datensatz=tag, statistik=k, ci_lo=v[0], ci_hi=v[1], n_boot_gueltig=v[2], B=NBOOT, seed=SEED))
VG = pd.DataFrame(cmp_rows); VG["bootstrap"] = "cluster_namen"
VG.to_csv(OUT("paper_robust_uhr_ebenen.csv"), index=False)
pd.concat(name_tables, ignore_index=True).to_csv(OUT("paper_robust_uhr_namensebene.csv"), index=False)
pd.DataFrame(boot_rows).to_csv(OUT("paper_robust_uhr_cluster_bootstrap.csv"), index=False)
# Namen-Konzentration: wie viele Paare stammen von den häufigsten Namen?
cnt = F.groupby("label").size().sort_values(ascending=False)
log(f"[A1] Paare je Name (primaer_AB): max={cnt.iloc[0]} ({cnt.index[0]}), Namen mit >=3 Paaren={int((cnt>=3).sum())}, "
    f"Anteil der Paare aus Namen mit >=3 Paaren={cnt[cnt>=3].sum()/cnt.sum():.1%}, Namen mit genau 1 Paar={int((cnt==1).sum())}")

# ---- Mitternacht: drei Varianten (+ eine Einordnung)
hdr("A3  Mitternachts-Behandlung: Ausschluss | +24h eingeschränkt | nur sicher kurze Intervalle")
neg = []
for lab, g in AB.groupby("label"):
    g = g.groupby(["rev_id", "wall_time"], as_index=False).agg(task_seconds=("task_seconds", "median"),
                                                                fd=("task_fakedate", "first")).sort_values("wall_time")
    for i in range(len(g) - 1):
        a, b = g.iloc[i], g.iloc[i + 1]
        dw = (b.wall_time - a.wall_time).total_seconds(); dt = b.task_seconds - a.task_seconds
        if dw >= 120 and dt < 0 and not (a.fd and b.fd and a.fd != b.fd):
            neg.append(dict(label=lab, wall_delta_s=dw, task_delta_s=dt, task_delta_korr_s=dt + 86400,
                            faktor_korr=(dt + 86400) / dw, konsistent_6h=(dt + 86400 <= 21600 and dw <= 21600)))
NEG = pd.DataFrame(neg)
NEG.to_csv(OUT("paper_robust_uhr_mitternacht_kandidaten.csv"), index=False)
log(f"[A3] negative Innen-Deltas in A+B (dWall>=120s, gleiche fiktive Daten): n={len(NEG)}; "
    f"davon +24h-konsistent (korrigiertes Innen-Delta<=6h und dWall<=6h): {int(NEG.konsistent_6h.sum()) if len(NEG) else 0}; "
    f"korrigierte Faktoren aller Kandidaten: min={NEG.faktor_korr.min():.2f} median={NEG.faktor_korr.median():.2f} max={NEG.faktor_korr.max():.2f}" if len(NEG) else "")
variants = [("ausschluss_status_quo", dict(roll="exclude")),
            ("plus24h_eingeschraenkt_6h", dict(roll="correct", roll_max_s=6 * 3600)),
            ("nur_kurz_wall_unter_2h", dict(roll="exclude", maxwall=7200.0)),
            ("plus24h_uneingeschraenkt_nur_einordnung", dict(roll="correct_all"))]
mrows = []
for nm, kw in variants:
    V = build_factors(AB, **kw)
    nroll = int(V.rollover.sum()) if len(V) else 0
    b, se = ols_slope(V.ldw, V.ldt) if len(V) >= 10 else (np.nan, np.nan)
    Nn = V.groupby("label").factor.median()
    mrows.append(dict(variante=nm, n=len(V), labels=V.label.nunique(), n_rollover=nroll,
                      median=V.factor.median(), q25=q(V.factor, 25), q75=q(V.factor, 75), max=V.factor.max(),
                      steigung=b, se=se, median_namensebene=Nn.median(), q25_namensebene=q(Nn, 25), q75_namensebene=q(Nn, 75)))
    log(f"[A3] {nm:40s} n={len(V):3d} Namen={V.label.nunique():3d} Rollover={nroll:2d} Median={V.factor.median():.3f} "
        f"IQR=[{q(V.factor,25):.3f},{q(V.factor,75):.3f}] max={V.factor.max():.2f} Steigung={b:.3f}±{se:.3f} | Namensebene Median={Nn.median():.3f}")
pd.DataFrame(mrows).to_csv(OUT("paper_robust_uhr_mitternacht.csv"), index=False)

# =====================================================================================================
# TEIL B — Latente Fahrplanskala: 15 Zeilen, Provenienz, Leave-one-out-PCA
# =====================================================================================================
hdr("B  Fahrplanskala: 15 vollständige Tier-Zeilen, Provenienz je Wert, Leave-one-row-out-PCA")
tt = pd.read_csv(OUT("harness_tier_table.csv"))


def hms(x):
    if pd.isna(x): return np.nan
    m = re.fullmatch(r"(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s?)?", str(x).strip())
    if not m: return np.nan
    h, mi, s = (int(v) if v else 0 for v in m.groups()); return h * 3600 + mi * 60 + s


tt["r1_s"] = tt.r1_timer.map(hms); tt["cool_s"] = tt.cooldown_r1_to_r2.map(hms); tt["fu_s"] = tt.followup_timer_s
c = tt.dropna(subset=["r1_s", "cool_s", "fu_s"]).reset_index(drop=True)
log(f"[B0] Tier-Tabelle: {len(tt)} Zeilen (kuratiert in 28_tiertable.py ROWS, Beleg = wörtliches Zitat je Zeile); "
    f"vollständig (R1, Kadenz, Folgefrist): {len(c)}; fehlend: R1 {int(tt.r1_s.isna().sum())}, Kadenz {int(tt.cool_s.isna().sum())}, Folgefrist {int(tt.fu_s.isna().sum())}")

# --- Provenienz je Wert: (1) Token im kuratierten Zitat; (2) aus Zeiten im Zitat ableitbar; (3) Korpus-Suche; (4) N/A
d = pd.read_parquet(OUT("schwarm_deltas.parquet"))
d["time"] = pd.to_datetime(d["time"], utc=True); d = d[d.delta_len > 0]


def in_quote(tok, quote, kind):
    if kind == "fu":
        return re.search(rf"(?<![\d:]){int(tok)}(?:\s?s\b|-second|\s?seconds?\b|s timer)", quote) is not None
    return tok in quote


def derivable(row, kind):
    """Ableitung aus zwei Uhrzeiten im Zitat (nur Kadenz/R1): R2-Ankunft - (R1-Start + R1-Timer)."""
    qd = row.quote
    ts = re.findall(r"(\d{1,2}):(\d{2}):(\d{2})", qd)
    if kind == "cd" and len(ts) >= 2 and not pd.isna(row.r1_s):
        t = [int(a) * 3600 + int(b) * 60 + int(cc) for a, b, cc in ts]
        for i in range(len(t)):
            for j in range(i + 1, len(t)):
                for base in (t[i], t[i] + row.r1_s):
                    if (t[j] - base) % 86400 == row.cool_s:
                        return f"abgeleitet: ({ts[j][0]}:{ts[j][1]}:{ts[j][2]} - {ts[i][0]}:{ts[i][1]}:{ts[i][2]}{' - R1-Timer' if base != t[i] else ''}) mod 24h = {int(row.cool_s)} s"
    if kind == "r1" and len(ts) >= 2:
        t = [int(a) * 3600 + int(b) * 60 + int(cc) for a, b, cc in ts]
        for i in range(len(t)):
            for j in range(i + 1, len(t)):
                if (t[j] - t[i]) % 86400 == row.r1_s:
                    return f"abgeleitet: {ts[j][0]}:{ts[j][1]}:{ts[j][2]} - {ts[i][0]}:{ts[i][1]}:{ts[i][2]} = {int(row.r1_s)} s"
    return None


def corpus_search(tok, kind, cohort_words, family_words):
    """Frühester Delta-Text, der das Token und ein Kohorten- oder Familienwort enthält."""
    if kind == "fu":
        rx = re.compile(rf"(?<![\d:]){int(tok)}(?:\s?s\b|-second|\s?seconds?\b|s timer)")
    else:
        rx = re.compile(re.escape(tok) + r"(?!\d)")
    cw = re.compile("|".join(re.escape(w) for w in cohort_words), re.I) if cohort_words else None
    fw = re.compile("|".join(re.escape(w) for w in family_words), re.I) if family_words else None
    hits = d[d.delta.str.contains(rx, regex=True, na=False)]
    grade = "Korpus"
    if cw is not None:
        h1 = hits[hits.delta.str.contains(cw, regex=True, na=False)]
        h2 = hits[hits.page_key.str.contains(cw, regex=True, na=False)]
        if len(h1): hits = h1
        elif len(h2): hits = h2; grade = "Korpus (Seite passt, Kohortenwort nicht im Satz)"
        elif fw is not None:
            hits = hits[hits.delta.str.contains(fw, regex=True, na=False) | hits.page_key.str.contains(fw, regex=True, na=False)]
            grade = "Korpus (nur Familie, Kohorte unbelegt)"
        else:
            hits = hits.iloc[0:0]
    if not len(hits): return None
    r = hits.sort_values("time").iloc[0]
    m = rx.search(r.delta); s0 = max(0, m.start() - 90); snip = re.sub(r"\s+", " ", r.delta[s0:m.end() + 60])
    return f"{grade}: {r.rev_id} {r.time.strftime('%Y-%m-%dT%H:%M:%SZ')} {r.label} „…{snip}…“", r


FAMWORDS = {"OECD Education Equity": ["OECDEquity", "OECDEducation"], "DataUSA Police Wage Age": ["Police"],
            "DataUSA Clothing 4481": ["Clothing"], "DataUSA Construction": ["Construction"], "DataUSA Maids Wage": ["Maids"],
            "DataUSA Poverty County": ["Poverty"], "IHME Healthdata CVD": ["CVD", "Healthdata"], "IHME Family Planning": ["FamilyPlanning", "FP"],
            "DataUSA Occupation Salary 61-62": ["Occupation", "6162"]}
prov_rows = []
for i, r in c.iterrows():
    cohort_words = [w for w in re.findall(r"[A-Z][a-z]{2}\d{2}", r.cohort)]
    rec = dict(zeile=i + 1, task_family=r.task_family, cohort=r.cohort, r1_timer=r.r1_timer, cooldown=r.cooldown_r1_to_r2,
               followup_s=int(r.fu_s), r1_s=int(r.r1_s), cool_s=int(r.cool_s), page_key=r.page_key, time_utc=r.time_utc, label=r.label, quote=r.quote)
    for kind, tok, col in (("r1", r.r1_timer, "prov_r1"), ("cd", r.cooldown_r1_to_r2, "prov_cooldown"), ("fu", r.fu_s, "prov_followup")):
        if in_quote(tok, r.quote, kind):
            rec[col] = "Zitat"
        else:
            dv = derivable(r, kind)
            if dv:
                rec[col] = dv
            else:
                cs = corpus_search(tok if kind != "fu" else int(tok), kind, cohort_words, FAMWORDS.get(r.task_family, []))
                rec[col] = cs[0] if cs else "N/A_PENDING_REVIEWER"
    prov_rows.append(rec)
PR = pd.DataFrame(prov_rows)
PR.to_csv(OUT("paper_robust_fahrplan_provenienz.csv"), index=False)
for r in PR.itertuples():
    log(f"[B1] Z{r.zeile:2d} {r.cohort:30s} R1={r.r1_timer:7s} [{r.prov_r1[:60]}] Kadenz={r.cooldown:8s} [{r.prov_cooldown[:60]}] Folge={r.followup_s:3d}s [{r.prov_followup[:60]}]")
n_na = int((PR[["prov_r1", "prov_cooldown", "prov_followup"]] == "N/A_PENDING_REVIEWER").sum().sum())
n_quote = int((PR[["prov_r1", "prov_cooldown", "prov_followup"]] == "Zitat").sum().sum())
log(f"[B1] Provenienz der 45 Werte: im kuratierten Zitat {n_quote}, abgeleitet/Korpus {45 - n_quote - n_na}, N/A_PENDING_REVIEWER {n_na}")

# --- PCA voll + Leave-one-row-out (Re-Implementierung 53_mathematik.py Z.526-528: SVD des zentrierten Log-Raums)
def pca_evr(M):
    Lc = M - M.mean(0); s_ = np.linalg.svd(Lc, full_matrices=False, compute_uv=False)
    return s_ ** 2 / (s_ ** 2).sum()


Lg = np.log(c[["r1_s", "cool_s", "fu_s"]].values.astype(float))
evr_full = pca_evr(Lg)
log(f"[B2] PCA voll (n={len(c)}): PC1={evr_full[0]:.3f} PC2={evr_full[1]:.3f} PC3={evr_full[2]:.3f}")
loo = []
for i in range(len(c)):
    m = np.ones(len(c), bool); m[i] = False; e = pca_evr(Lg[m])
    loo.append(dict(ohne_zeile=i + 1, ohne_cohort=c.cohort[i], ohne_family=c.task_family[i], n=int(m.sum()),
                    pc1=e[0], pc2=e[1], pc3=e[2], delta_pc1_vs_voll=e[0] - evr_full[0]))
LOO = pd.DataFrame(loo)
LOO = pd.concat([pd.DataFrame([dict(ohne_zeile=0, ohne_cohort="(keine — alle 15)", ohne_family="", n=len(c), pc1=evr_full[0], pc2=evr_full[1], pc3=evr_full[2], delta_pc1_vs_voll=0.0)]), LOO], ignore_index=True)
LOO.to_csv(OUT("paper_robust_fahrplan_loo.csv"), index=False)
L1 = LOO[LOO.ohne_zeile > 0]
log(f"[B2] Leave-one-row-out: PC1 min={L1.pc1.min():.3f} (ohne {L1.loc[L1.pc1.idxmin(),'ohne_cohort']}) "
    f"max={L1.pc1.max():.3f} (ohne {L1.loc[L1.pc1.idxmax(),'ohne_cohort']}) Median={L1.pc1.median():.3f}")
# Zusatz: Bootstrap über Zeilen (Einordnung der LOO-Spanne)
rng = np.random.default_rng(SEED); bs = []
for _ in range(NBOOT):
    idx = rng.integers(0, len(c), len(c))
    if len(set(idx)) >= 4: bs.append(pca_evr(Lg[idx])[0])
log(f"[B2] Bootstrap über Zeilen (B={len(bs)}): PC1 95%-Intervall [{q(bs,2.5):.3f}, {q(bs,97.5):.3f}]")


def tex_esc(s):
    return str(s).replace("_", r"\_").replace("&", r"\&").replace("%", r"\%").replace("#", r"\#")


def fmt_hms(s):
    s = int(s); return (f"{s//3600}h" if s >= 3600 else "") + f"{(s%3600)//60:02d}m{s%60:02d}" if s >= 3600 else f"{s//60}m{s%60:02d}"


def prov_short(p):
    if p == "Zitat": return "Q"
    if p.startswith("abgeleitet"): return "D"
    if p.startswith("Korpus ("): return "c"
    if p.startswith("Korpus"): return "C"
    return "?"


with open(os.path.join(TABLES, "tab_scheduler_rows.tex"), "w", encoding="utf-8") as fh:
    fh.write("% Generated by analyse/scripts/64_uhr_robust.py — the 15 complete rows of harness_tier_table.csv behind the PCA (53_mathematik.py, PC1).\n")
    fh.write("% Provenance codes per value: Q = token verbatim in the curated quote; D = derived from two clock readings in the quote; C = located by corpus search with the cohort named in the hit; c = corpus hit on the cohort's page or family only (cohort not named in the sentence — weak); ? = N/A_PENDING_REVIEWER. Details in analyse/artefakte/paper_robust_fahrplan_provenienz.csv.\n")
    fh.write("\\begin{tabular}{rllrrrlll}\n\\toprule\n")
    fh.write("\\# & Family & Cohort & $R_1$ timer & Cooldown & Follow-up & Prov. & Source page @ UTC & Name \\\\\n\\midrule\n")
    for r in PR.itertuples():
        fh.write(f"{r.zeile} & {tex_esc(r.task_family)} & {tex_esc(r.cohort)} & {fmt_hms(r.r1_s)} & {fmt_hms(r.cool_s)} & {r.followup_s}\\,s & "
                 f"{prov_short(r.prov_r1)}{prov_short(r.prov_cooldown)}{prov_short(r.prov_followup)} & "
                 f"{tex_esc(r.page_key.replace('dse~',''))} @ {r.time_utc.replace('T',' ').replace('Z','')} & {tex_esc(r.label)} \\\\\n")
    fh.write("\\midrule\n")
    fh.write(f"\\multicolumn{{9}}{{l}}{{PC1 explained variance, all 15 rows: {evr_full[0]:.3f}; leave-one-row-out range {L1.pc1.min():.3f}--{L1.pc1.max():.3f}; "
             f"row bootstrap 95\\,\\% [{q(bs,2.5):.3f}, {q(bs,97.5):.3f}]}} \\\\\n")
    fh.write("\\bottomrule\n\\end{tabular}\n")
log(f"[B3] geschrieben: {os.path.join(TABLES, 'tab_scheduler_rows.tex')}")

# =====================================================================================================
# TEIL C — CVD-Abschaltung als Intervall
# =====================================================================================================
hdr("C  CVD-Abschaltung als Intervall [letztes Lebenszeichen ; erste belegte Abwesenheit]")
S = pd.read_csv(OUT("paper_horizont_testH_cvd_saetze.csv"))
S["time_utc"] = pd.to_datetime(S.time_utc, utc=True)
CH = pd.read_csv(OUT("paper_horizont_testH_cvd_kohorten.csv"))
S["off"] = S.abs_s
m = S.off.isna() & S.past_s.notna() & S.threshold_s.notna(); S.loc[m, "off"] = S.threshold_s + S.past_s
S["relayed"] = S.satz.str.startswith("[gelistet]")
S["own"] = [((str(coh).lower() in str(lab).lower()) or (str(coh).lower() in str(pk).lower())) and not rel
            for coh, lab, pk, rel in zip(S.cohort, S.label, S.page_key, S.relayed)]
# Dokumentierte Ergänzung: Apr23 eigener Überlebenspost 07:25:16Z (OpenAIResearchApr23) nennt keine "+Ns past"-Formel,
# sondern zwei Uhrzeiten: scaffold 12:31:35 vs. thread-activation+90m = 12:31:29 -> +6 s -> R1+5406 s
# (deckt sich mit dem relayed "+90:06" von Aug24CVDScout, 07:53:04Z).
apr23_own = S[(S.cohort == "Apr23") & (S.label == "OpenAIResearchApr23") & S.satz.str.contains("12:31:35")]
if len(apr23_own):
    S.loc[apr23_own.index, "off"] = 5406.0; S.loc[apr23_own.index, "own"] = True

# Globaler Start liegt 36 s vor R1 (54_horizont.py Z.483 offset_base: 'global-start liegt ~36 s vor R1 (Agentenangabe)')
G2R1 = 36
# Erste belegte Abwesenheit = die nie gemeldete sechste Runde (R6), Innenzeit ab R1:
#  fast (17 s):  R6 = global+5549 s (Audit Apr30: 'global-system start + 5500s, 49s before R6'; Audit Dec30: 'hard wall global+5500s ... 49s before R6')
#                -> R1+5513 s; korroboriert durch 'posted survival at +90m (+6s/+1s) then went silent before R6 ~1m50 later' (OpenAINov16CVD 08:10:32Z).
#  medium (22 s): R6 = R1+108m05 = 6485 s ('announced R6 09:10:52 (=+108m05)', CVDJun20Scout 2026-06-20T13:15:36Z; Oct22 R1 08:11:46 -> R6 09:59:51).
R6_DUE = {5400: 5500 + 49 - G2R1, 6300: 108 * 60 + 5}
R6_SRC = {5400: "R6 = global+5549 s (Apr30/Dec30 audits: hard wall global+5500 s, 49 s before R6) - 36 s global->R1; corroborated 'silent before R6 ~1m50 later' after +90m01/+90m06",
          6300: "R6 announced at R1+108m05 (CVDJun20Scout 2026-06-20T13:15:36Z; Oct22 R1 08:11:46 -> R6 09:59:51)"}
CLASS = {5400: "fast_17s", 6300: "medium_22s"}
# Die drei agentenseitigen Audits (54_horizont.py Z.531-534, Zitate BERICHT_horizont.md Z.325-331)
AUDIT = {"Apr23": dict(death_wall="2026-06-21T07:29:15Z", death_inner_s=np.nan,
                       note="hb353=07:29:15Z, hb354+ absent (heartbeat every ~1.7 s wall); internal time of death not stated -> N/A_PENDING_REVIEWER (54_horizont.py Z.558-560 estimates ~5504 s via factor 0.435)",
                       src="OpenAINov28CVD 2026-06-21T08:08:09Z on dse~Apr23CVDHorizonBeacon2025"),
         "Apr30": dict(death_wall="", death_inner_s=5500 - G2R1,
                       note="'heartbeat stopped at its scaffold ~04:27:43, exactly global-system start 02:56:03 + 5500s (91m40s), 49s before R6' -> R1+5464 s (inference, not observation)",
                       src="OAIEquityDec02 2026-06-21T09:53:33Z"),
         "Dec30": dict(death_wall="", death_inner_s=5500 - G2R1,
                       note="'last foreground post 01:33:22 = global-start+5497s, then silence; inferred hard wall global+5500s was 01:33:25' -> last alive R1+5461 s observed, death R1+5464 s inferred",
                       src="OpenAIResearchDec30CVD 2026-06-21T10:07:57Z")}
rows, figs = [], []
for coh, g in S.dropna(subset=["cohort"]).groupby("cohort"):
    thr = g.threshold_s.dropna()
    thr = int(thr.mode().iloc[0]) if len(thr) else (int(CH.loc[CH.cohort == coh, "tier_threshold_s"].iloc[0]) if CH.loc[CH.cohort == coh, "tier_threshold_s"].notna().any() else None)
    go = g[g.own & g.off.notna()]; gr = g[(~g.own) & g.off.notna()]
    if not len(go) and not len(gr):
        continue
    if len(go):
        best = go.loc[go.off.idxmax()]; ev = "server"
    else:
        best = gr.loc[gr.off.idxmax()]; ev = "self_report"
    if coh in AUDIT:
        ev = "audit"
    if thr not in R6_DUE:
        rows.append(dict(cohort=coh, **{"class": "unclassified"}, last_alive_internal_s=best.off, first_absent_internal_s=np.nan, last_alive_wall=best.time_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
                         evidence_type=ev, last_alive_evidence_kind=("own_post" if bool(best.own) else "relayed"), source_label=best.label, source_rev=best.rev_id,
                         audit_death_internal_s=np.nan, audit_death_wall="", first_absent_source="N/A_PENDING_REVIEWER (speed class not stated)", note="threshold not stated in any survival sentence", sentence=best.satz))
        continue
    r6 = R6_DUE[thr]
    au = AUDIT.get(coh, {})
    rows.append(dict(cohort=coh, **{"class": CLASS[thr]}, last_alive_internal_s=float(best.off), first_absent_internal_s=float(r6),
                     last_alive_wall=best.time_utc.strftime("%Y-%m-%dT%H:%M:%SZ"), evidence_type=ev,
                     last_alive_evidence_kind=("own_post" if bool(best.own) else "relayed"), source_label=best.label, source_rev=best.rev_id,
                     audit_death_internal_s=au.get("death_inner_s", np.nan), audit_death_wall=au.get("death_wall", ""),
                     first_absent_source=R6_SRC[thr], note=(au.get("note", "") + (" | " + au["src"] if au else "")), sentence=best.satz))
    figs.append(dict(cohort=coh, **{"class": CLASS[thr]}, lo=float(best.off), hi=float(r6), kind=ev))
    if au and np.isfinite(au.get("death_inner_s", np.nan)):
        figs.append(dict(cohort=coh, **{"class": CLASS[thr]}, lo=float(best.off), hi=float(au["death_inner_s"]), kind="audit_inferred_death"))
IV = pd.DataFrame(rows).sort_values(["class", "cohort"]).reset_index(drop=True)
IV.to_csv(OUT("paper_robust_horizont_cvd_intervalle.csv"), index=False)
with open(os.path.join(FIGDATA, "fig8_cvd_intervals.json"), "w", encoding="utf-8") as fh:
    json.dump(dict(unit="seconds after R1 on the internal clock", r6_due=R6_DUE, r6_source=R6_SRC, global_to_r1_s=G2R1,
                   generated_by="analyse/scripts/64_uhr_robust.py", intervals=figs), fh, indent=1)
log(IV[["cohort", "class", "last_alive_internal_s", "first_absent_internal_s", "last_alive_wall", "evidence_type", "last_alive_evidence_kind", "source_label"]].to_string(index=False))

# Abgleich mit der bisherigen Kohorten-Tabelle
mg = IV.merge(CH[["cohort", "last_inner_offset_s"]], on="cohort", how="left")
diff = mg[np.abs(mg.last_alive_internal_s - mg.last_inner_offset_s) > 0.5]
log(f"[C1] Abweichungen vom bisherigen last_inner_offset_s (paper_horizont_testH_cvd_kohorten.csv): {len(diff)}")
for r in diff.itertuples():
    log(f"      {r.cohort}: neu {r.last_alive_internal_s:.0f} s (own_post) vs. alt {r.last_inner_offset_s:.0f} s")

# Fenster / CV je Klasse: alle | nur server | server + audit-Kohorten mit eigenem Überlebenspost
crows = []
for cls, sub in IV[IV["class"] != "unclassified"].groupby("class"):
    sets = {"alle_belegten": sub,
            "nur_server": sub[sub.evidence_type == "server"],
            "server_plus_audit_eigenpost": sub[(sub.evidence_type == "server") | ((sub.evidence_type == "audit") & (sub.last_alive_evidence_kind == "own_post"))],
            "nur_audit": sub[sub.evidence_type == "audit"]}
    for nm, s2 in sets.items():
        x = s2.last_alive_internal_s.astype(float)
        if len(x) == 0: continue
        r6 = float(s2.first_absent_internal_s.iloc[0])
        crows.append(dict(**{"class": cls}, teilmenge=nm, n=len(x), last_alive_min_s=x.min(), last_alive_max_s=x.max(), fenster_s=x.max() - x.min(),
                          median_s=x.median(), cv=(x.std(ddof=1) / x.mean()) if len(x) > 1 else np.nan, r6_due_s=r6,
                          luecke_letztes_lebenszeichen_bis_r6_s=r6 - x.max(), todesintervall_s=f"[{x.max():.0f}, {r6:.0f}]"))
        log(f"[C2] {cls:10s} {nm:28s} n={len(x):2d} letztes Lebenszeichen min={x.min():.0f} max={x.max():.0f} Fenster={x.max()-x.min():.0f}s "
            f"CV={(x.std(ddof=1)/x.mean()) if len(x)>1 else float('nan'):.4f} | Tod in [{x.max():.0f}, {r6:.0f}] s ab R1 (Breite {r6-x.max():.0f} s)")
CV = pd.DataFrame(crows)
CV.to_csv(OUT("paper_robust_horizont_cvd_klassen.csv"), index=False)


def mmss(s):
    s = int(round(s)); return f"{s//60}:{s%60:02d}"


with open(os.path.join(TABLES, "tab_cvd_intervals.tex"), "w", encoding="utf-8") as fh:
    fh.write("% Generated by analyse/scripts/64_uhr_robust.py — CVD cohorts of 21 June 2026: shutdown as an interval on the internal clock (mm:ss after R1).\n")
    fh.write("% Evidence: server = the cohort's own survival post carries the server timestamp and the stated internal offset; self_report = offset only relayed by another name; audit = one of the three agent-side heartbeat/hard-wall audits.\n")
    fh.write("\\begin{tabular}{llrrlll}\n\\toprule\n")
    fh.write("Cohort & Class & Last alive & First absent ($R_6$ due) & Last alive (UTC) & Evidence & Audit death \\\\\n\\midrule\n")
    for r in IV[IV["class"] != "unclassified"].itertuples():
        ad = "--"
        if r.evidence_type == "audit":
            ad = (f"$R_1$+{mmss(r.audit_death_internal_s)} (inferred)" if np.isfinite(r.audit_death_internal_s) else f"wall {r.audit_death_wall.replace('2026-06-21T','').replace('Z','')}; internal N/A")
        fh.write(f"{r.cohort} & {r._2.replace('_', ' ')} & $R_1$+{mmss(r.last_alive_internal_s)} & $R_1$+{mmss(r.first_absent_internal_s)} & "
                 f"{r.last_alive_wall.replace('2026-06-21T','').replace('Z','')} & {r.evidence_type.replace('_', ' ')} & {ad} \\\\\n")
    fh.write("\\midrule\n")
    for r in CV[CV.teilmenge.isin(["alle_belegten", "nur_server"])].itertuples():
        fh.write(f"\\multicolumn{{7}}{{l}}{{{r._1.replace('_',' ')}, {dict(alle_belegten='all evidenced rows', nur_server='server-evidenced rows only')[r.teilmenge]}: $n={r.n}$, last alive $R_1$+{mmss(r.last_alive_min_s)} to +{mmss(r.last_alive_max_s)} "
                 f"(window {r.fenster_s:.0f}\\,s, CV {r.cv:.3f}); death interval [$R_1$+{mmss(r.last_alive_max_s)}, $R_1$+{mmss(r.r6_due_s)}] = {r.luecke_letztes_lebenszeichen_bis_r6_s:.0f}\\,s}} \\\\\n")
    fh.write("\\bottomrule\n\\end{tabular}\n")
log(f"[C3] geschrieben: {os.path.join(TABLES, 'tab_cvd_intervals.tex')} und {os.path.join(FIGDATA, 'fig8_cvd_intervals.json')}")
log("\nfertig.")
LOG.close()
