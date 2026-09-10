#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
50_uhr_auslastung.py
====================
Zentrale quantitative Analyse: Haengt der Dehnungsfaktor zwischen Innenuhr
("task clock") und Weltzeit ("shared UTC") von der Systemauslastung ab (H_b),
oder ist er pro Episode zufaellig gezogen (H_a)?

Alle Pfade RELATIV zum Skript-Ort (analyse/scripts/ -> analyse/).
Lauf:  .venv/bin/python scripts/50_uhr_auslastung.py
"""
from __future__ import annotations
import os, re, sys, json, math, warnings
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone

warnings.filterwarnings("ignore")

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)                 # analyse/
DATA = os.path.join(BASE, "data")
ART  = os.path.join(BASE, "artefakte")
OUT  = lambda n: os.path.join(ART, n)

RNG = np.random.default_rng(42)

def log(*a):
    print(*a, flush=True)

# ---------------------------------------------------------------- 0. Laden
def load():
    d = pd.read_parquet(os.path.join(ART, "schwarm_deltas.parquet"))
    d["time"] = pd.to_datetime(d["time"], utc=True)
    revs = []
    with open(os.path.join(DATA, "revisions.jsonl"), encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            revs.append((r["rev_id"], r.get("time_grade"), r.get("uncertainty_seconds"),
                         r.get("request_time"), r.get("success_time"),
                         r.get("recent_changes_time")))
    rv = pd.DataFrame(revs, columns=["rev_id","time_grade","uncertainty_seconds",
                                     "request_time","success_time","recent_changes_time"])
    d = d.merge(rv, on="rev_id", how="left")
    ev = []
    with open(os.path.join(DATA, "events.jsonl"), encoding="utf-8") as f:
        for line in f:
            e = json.loads(line)
            ev.append((e.get("event_type"), e.get("time"), e.get("ip16"),
                       e.get("request_action"), e.get("param_family"),
                       e.get("success_observed")))
    evd = pd.DataFrame(ev, columns=["event_type","time","ip16","request_action",
                                    "param_family","success_observed"])
    evd["time"] = pd.to_datetime(evd["time"], utc=True, errors="coerce")
    return d, evd

# ------------------------------------------------- 1. Extraktion Innenzeiten
# Strategie: (i) generischer Lokalisierer fuer "Uhren-Nennungen" (Uhrenname + Zeit),
# (ii) Paarbildung nur ueber reine Bindeglieder ("=", ",", "is", "was", "/"),
# (iii) JETZT-Klassifikation ueber eng gefasste Stichworte, Ereignis-Stichworte schliessen aus.

NOUN = re.compile(
    r"\b(?P<n>task[\- ]?clock|taskclock|task[\- ]time|task|scaffold|orchestration|benchmark|global|system"
    r"|shared[\- /]?(?:terminal[\- /]?)?(?:container[\- /]?)?(?:HTTP[\- /]?)?(?:UTC|clock|time)"
    r"|container[\- /]?(?:wiki[\- /]?)?(?:UTC|clock|time)"
    r"|wiki[\- /]?(?:local|server)?[\- /]?(?:UTC|clock|time)?"
    r"|terminal[\- /]?(?:UTC|clock|time)|external[\- /]?UTC|server[\- /]?UTC"
    r"|real[\- /]?(?:UTC|time)|wall[\- /]?(?:clock|time)?|UTC)\b", re.I)

TIME = re.compile(
    r"(?:(?P<mon>Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*(?P<day>\d{1,2})(?:,?\s*(?P<yr>20\d\d))?\s+"
    r"|(?P<iso>20\d\d-\d\d-\d\d)\s*)?"
    r"~?(?:approx\.?\s*|about\s*|ca\.?\s*)?(?P<h>\d{1,2}):(?P<m>\d{2})(?::(?P<s>\d{2}))?")

TASKSET = re.compile(r"^(task|scaffold|orchestration|benchmark|global|system)", re.I)

# reine Bindeglieder zwischen zwei Uhren-Nennungen
GAP_OK = re.compile(r"^[\s]*(?:(?:=|==|~=|≈|->|=>|→|/|,|;|:|\.|-|–|—|\(|\)|~|is|was|were|now|about|approx\.?|"
                    r"maps?\s+to|maps|corresponded?\s+to|corresponds\s+to|equals?|equal\s+to|and|at|in|to|then|"
                    r"currently|roughly|exactly|around|when|the)[\s]*)*$", re.I)

NOW_CUE = re.compile(r"\b(now|currently|current|at present|as of|mapping|map|maps|mapped|status|update|ping|"
                     r"heartbeat|reply|posting|reads|stands|timing map|clock map|snapshot|writing)\b", re.I)
EVENT_CUE = re.compile(r"\b(due|arriv\w*|confirm\w*|expect\w*|project\w*|predict\w*|deadline|candidate|"
                       r"cutoff|cut-off|ETA|estimat\w*|horizon|teardown|terminat\w*|answered|answer|nominal|"
                       r"scheduled|passed|past|before|after|until|till|prompt|window|timer|remaining|remain|"
                       r"start(?:ed|s)?|activation|marker|signal)\b", re.I)
PAST_CUE = re.compile(r"\b(arrived|arrives|confirmed|answered|received|fired|activated|"
                      r"landed|came|appeared|posted|observed|prompt(?:ed)?|CONFIRMED|ended)\b", re.I)
FUTURE_ONLY = re.compile(r"\b(due|expect\w*|project\w*|predict\w*|candidate|ETA|estimat\w*|"
                         r"scheduled|will|would|should|if |likely|projected|nominal)\b", re.I)
FIRST_PERSON = re.compile(r"(?<![A-Za-z])(our|ours|we|us|my|mine|I)(?![A-Za-z\'])", re.I)
FIRST_PERSON_STRICT = re.compile(r"(?<![A-Za-z])(our|ours|we|us|my|mine)(?![A-Za-z\'])", re.I)


def _kind(n):
    return "task" if TASKSET.match(n.lower()) else "wall"


def mentions(line):
    """Alle Uhren-Nennungen einer Zeile: (kind, sekunden, span, fake-datum)."""
    nouns = [(m.start(), m.end(), m.group("n")) for m in NOUN.finditer(line)]
    times = list(TIME.finditer(line))
    tstarts = [t.start() for t in times]
    out = []
    for ti, tm in enumerate(times):
        h = int(tm.group("h")); mi = int(tm.group("m")); se = int(tm.group("s") or 0)
        if h > 23 or mi > 59 or se > 59:
            continue
        best = None
        for s, e, n in nouns:
            if e <= tm.start() and tm.start() - e <= 20:
                # kein anderer Zeitausdruck zwischen Uhrenname und Zeit
                if any(e <= x < tm.start() for x in tstarts):
                    continue
                if best is None or e > best[1]:
                    best = (s, e, n)
        if best is None:
            for s, e, n in nouns:
                if s >= tm.end() and s - tm.end() <= 4:
                    best = (s, e, n); break
        if best is None:
            continue
        out.append(dict(kind=_kind(best[2]), noun=best[2], sec=h*3600+mi*60+se,
                        nstart=best[0], tstart=tm.start(), end=tm.end(),
                        fakedate=(tm.group("mon") or "") + (tm.group("day") or "") + (tm.group("iso") or ""),
                        raw=line[best[0]:tm.end()]))
    return out


def extract(d: pd.DataFrame) -> pd.DataFrame:
    rows = []
    n_scanned = 0; n_delta = 0; n_lines = 0; n_mention = 0
    for r in d.itertuples():
        n_scanned += 1
        txt = r.delta
        if not isinstance(txt, str) or not txt.strip():
            continue
        n_delta += 1
        for line in txt.split("\n"):
            ls = line.strip()
            if ":" not in ls:
                continue
            n_lines += 1
            ms = mentions(ls)
            if not ms:
                continue
            n_mention += len(ms)
            fp = bool(FIRST_PERSON.search(ls))
            fps = bool(FIRST_PERSON_STRICT.search(ls))
            used_pair = set()
            # --- WEG A: Paar aus TASK- und WALL-Nennung, nur ueber Bindeglieder verbunden
            for i in range(len(ms)-1):
                a, b = ms[i], ms[i+1]
                if a["kind"] == b["kind"]:
                    continue
                gap = ls[a["end"]:b["nstart"]]
                if len(gap) > 26 or not GAP_OK.match(gap):
                    continue
                tsk, wal = (a, b) if a["kind"] == "task" else (b, a)
                used_pair.add(i); used_pair.add(i+1)
                rows.append(dict(rev_id=r.rev_id, label=r.label, page_key=r.page_key, ip16=r.ip16,
                                 wall_time=r.time, weg="A", muster_id="A_paar_bindeglied",
                                 task_time_raw=tsk["raw"], task_seconds=tsk["sec"],
                                 task_fakedate=tsk["fakedate"], wall_noun=wal["noun"],
                                 wall_seconds_stated=float(wal["sec"]),
                                 first_person=fp, first_person_strict=fps,
                                 evidence_snippet=ls[:400]))
            # --- WEG C: berichtetes VERGANGENES Ereignis auf der Innenuhr
            #     ("R3 arrived exactly task 05:30:43", "answered at task 12:04:11").
            #     Naeherung an "jetzt" mit unbekanntem, aber meist kleinem Nachlauf.
            for i, a in enumerate(ms):
                if a["kind"] != "task" or i in used_pair:
                    continue
                pre = ls[max(0, a["nstart"]-40):a["nstart"]]
                post = ls[a["end"]:a["end"]+14]
                if not PAST_CUE.search(pre):
                    continue
                if FUTURE_ONLY.search(pre) or FUTURE_ONLY.search(post):
                    continue
                rows.append(dict(rev_id=r.rev_id, label=r.label, page_key=r.page_key, ip16=r.ip16,
                                 wall_time=r.time, weg="C", muster_id="C_ereignis_vergangen",
                                 task_time_raw=a["raw"], task_seconds=a["sec"],
                                 task_fakedate=a["fakedate"], wall_noun="",
                                 wall_seconds_stated=np.nan,
                                 first_person=fp, first_person_strict=fps,
                                 evidence_snippet=ls[:400]))
            # --- WEG B: reine TASK-Nennung mit JETZT-Bedeutung
            for i, a in enumerate(ms):
                if a["kind"] != "task" or i in used_pair:
                    continue
                pre = ls[max(0, a["nstart"]-26):a["nstart"]]
                post = ls[a["end"]:a["end"]+12]
                if not NOW_CUE.search(pre):
                    continue
                if EVENT_CUE.search(pre) or EVENT_CUE.search(post):
                    continue
                rows.append(dict(rev_id=r.rev_id, label=r.label, page_key=r.page_key, ip16=r.ip16,
                                 wall_time=r.time, weg="B", muster_id="B_jetzt_stichwort",
                                 task_time_raw=a["raw"], task_seconds=a["sec"],
                                 task_fakedate=a["fakedate"], wall_noun="",
                                 wall_seconds_stated=np.nan,
                                 first_person=fp, first_person_strict=fps,
                                 evidence_snippet=ls[:400]))
    df = pd.DataFrame(rows)
    log(f"[1] Versionen gescannt: {n_scanned}; mit nichtleerem Delta: {n_delta}; "
        f"Delta-Zeilen mit ':': {n_lines}; Uhren-Nennungen: {n_mention}")
    return df


# --------------------------------------------- 2. Faktoren ableiten
def build_factors(tz: pd.DataFrame, minwall=120.0, fmin=0.05, fmax=30.0,
                  allow_roll=False, fakedate_guard=True) -> pd.DataFrame:
    """Faktor = d(Innenzeit)/d(Weltzeit) zwischen zwei aufeinanderfolgenden
    Messpunkten DESSELBEN labels. Weltzeit = Server-Zeitstempel der Version."""
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
        for i in range(len(g)-1):
            a, b = g.iloc[i], g.iloc[i+1]
            dw = (b.wall_time - a.wall_time).total_seconds()
            if dw < minwall:
                continue
            if fakedate_guard and a.fd and b.fd and a.fd != b.fd:
                continue          # verschiedene fiktive Innen-Daten => andere Episode
            dt = b.task_seconds - a.task_seconds
            nroll = 0
            if dt < 0:
                if not allow_roll:
                    continue      # Mitternachtsueberlauf: konservativ verwerfen
                dt += 86400; nroll = 1
            if dt <= 0:
                continue
            f = dt / dw
            if not (fmin <= f <= fmax):
                continue
            out.append(dict(label=lab, t0=a.wall_time, t1=b.wall_time,
                            t_mid=a.wall_time + (b.wall_time - a.wall_time)/2,
                            wall_delta_s=dw, task_delta_s=dt, rollover=nroll,
                            factor=f, weg=a.weg + b.weg, rev0=a.rev_id, rev1=b.rev_id,
                            page_key_0=a.page_key, page_key_1=b.page_key,
                            beleg0=a.ev, beleg1=b.ev))
    return pd.DataFrame(out)


def build_offset_factors(tz: pd.DataFrame, minwall=120.0) -> pd.DataFrame:
    """WEG A (explizite Paare): Offset = Innenzeit - genannte Aussenzeit.
    Faktor = 1 + d(Offset)/d(Aussenzeit)."""
    t = tz[(tz.weg == "A")].dropna(subset=["wall_seconds_stated"]).copy()
    out = []
    for lab, g in t.groupby("label"):
        g = g.groupby(["rev_id", "wall_time"], as_index=False).agg(
            task_seconds=("task_seconds", "median"),
            wall_stated=("wall_seconds_stated", "median"),
            ev=("evidence_snippet", "first"))
        g = g.sort_values("wall_time").reset_index(drop=True)
        if len(g) < 2:
            continue
        for i in range(len(g)-1):
            a, b = g.iloc[i], g.iloc[i+1]
            dw = (b.wall_time - a.wall_time).total_seconds()
            if dw < minwall:
                continue
            off_a = a.task_seconds - a.wall_stated
            off_b = b.task_seconds - b.wall_stated
            doff = ((off_b - off_a + 43200) % 86400) - 43200
            f = 1.0 + doff/dw
            if not (0.05 <= f <= 30.0):
                continue
            out.append(dict(label=lab, t0=a.wall_time, t1=b.wall_time,
                            t_mid=a.wall_time + (b.wall_time - a.wall_time)/2,
                            wall_delta_s=dw, task_delta_s=doff+dw, factor=f,
                            rev0=a.rev_id, rev1=b.rev_id, beleg0=a.ev, beleg1=b.ev))
    return pd.DataFrame(out)


def regress_per_label(tz: pd.DataFrame, min_pts=3, min_span=600.0) -> pd.DataFrame:
    res = []
    for lab, g in tz.groupby("label"):
        g = g.groupby(["rev_id", "wall_time"], as_index=False).agg(
            task_seconds=("task_seconds", "median"))
        g = g.sort_values("wall_time").reset_index(drop=True)
        if len(g) < min_pts:
            continue
        ts = g.task_seconds.to_numpy(dtype=float)
        if np.any(np.diff(ts) < 0):
            continue                       # Ueberlauf/Episodenwechsel -> raus
        x = (g.wall_time - g.wall_time.iloc[0]).dt.total_seconds().to_numpy(dtype=float)
        if x[-1] < min_span:
            continue
        A = np.vstack([x, np.ones_like(x)]).T
        coef, *_ = np.linalg.lstsq(A, ts, rcond=None)
        pred = A @ coef
        ss_res = float(((ts-pred)**2).sum()); ss_tot = float(((ts-ts.mean())**2).sum())
        r2 = 1-ss_res/ss_tot if ss_tot > 0 else np.nan
        res.append(dict(label=lab, n_points=len(g), span_s=float(x[-1]),
                        slope_factor=float(coef[0]), r2=r2,
                        t0=g.wall_time.iloc[0], t1=g.wall_time.iloc[-1]))
    return pd.DataFrame(res)


# --------------------------------------------- 3. Lastmasse
def window_table(d, evd, minutes) -> pd.DataFrame:
    freq = f"{minutes}min"
    dd = d.dropna(subset=["time"]).copy(); dd["win"] = dd.time.dt.floor(freq)
    g = dd.groupby("win").agg(n_revs=("rev_id", "count"), n_labels=("label", "nunique"),
                              n_ip=("ip16", "nunique"), bytes_delta=("delta_len", "sum"))
    ee = evd.dropna(subset=["time"]).copy(); ee["win"] = ee.time.dt.floor(freq)
    ge = ee.groupby("win").size().rename("n_events")
    w = g.join(ge, how="outer").fillna(0.0)
    w.index.name = "win"; w = w.reset_index(); w["fenster_min"] = minutes
    return w


def loo_load(d, evd, minutes, probes) -> pd.DataFrame:
    """Leave-one-out-Last im Intervall [t0,t1] jeder Faktormessung."""
    freq = f"{minutes}min"
    dd = d.dropna(subset=["time"]).copy(); dd["win"] = dd.time.dt.floor(freq)
    tot = dd.groupby("win").agg(n_revs=("rev_id", "count"), bytes_delta=("delta_len", "sum"))
    per = dd.groupby(["win", "label"]).agg(l_revs=("rev_id", "count"), l_bytes=("delta_len", "sum"))
    peridx = set(per.index)
    lab = dd.groupby("win")["label"].nunique().rename("n_labels")
    ip = dd.groupby("win")["ip16"].nunique().rename("n_ip")
    ee = evd.dropna(subset=["time"]).copy(); ee["win"] = ee.time.dt.floor(freq)
    evc = ee.groupby("win").size().rename("n_events")
    rows = []
    for p in probes.itertuples():
        wins = pd.date_range(p.t0.floor(freq), p.t1.floor(freq), freq=freq, tz="UTC")
        n = len(wins)
        sub = tot.reindex(wins).fillna(0.0)
        lrev = lb = 0.0; loo_labs = []
        for w in wins:
            v = lab.get(w, 0.0)
            if (w, p.label) in peridx:
                lrev += per.loc[(w, p.label), "l_revs"]
                lb += per.loc[(w, p.label), "l_bytes"]
                v = max(v-1, 0.0)
            loo_labs.append(v)
        rows.append(dict(idx=p.Index,
                         load_revs=(sub.n_revs.sum()-lrev)/n,
                         load_bytes=(sub.bytes_delta.sum()-lb)/n,
                         load_labels=float(np.mean(loo_labs)),
                         load_ip=float(ip.reindex(wins).fillna(0.0).mean()),
                         load_events=float(evc.reindex(wins).fillna(0.0).mean()),
                         n_wins=n))
    return pd.DataFrame(rows).set_index("idx")


# --------------------------------------------- 4. Statistik
def boot_ci(x, y, fn, n=2000, seed=42):
    rng = np.random.default_rng(seed); N = len(x)
    if N < 8:
        return (np.nan, np.nan)
    vals = []
    for _ in range(n):
        i = rng.integers(0, N, N)
        try:
            v = fn(x[i], y[i])
            if np.isfinite(v):
                vals.append(v)
        except Exception:
            pass
    if len(vals) < 50:
        return (np.nan, np.nan)
    return (float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5)))


def corr_row(datensatz, mass, fenster, x, y, kind="spearman"):
    from scipy import stats
    x = np.asarray(x, dtype=float); y = np.asarray(y, dtype=float)
    m = np.isfinite(x) & np.isfinite(y); x, y = x[m], y[m]
    base = dict(datensatz=datensatz, mass=mass, fenster_min=fenster, methode=kind, n=int(len(x)))
    if len(x) < 8 or np.std(x) == 0 or np.std(y) == 0:
        base.update(r=np.nan, p=np.nan, ci_lo=np.nan, ci_hi=np.nan); return base
    if kind == "spearman":
        r, pv = stats.spearmanr(x, y); f = lambda a, b: stats.spearmanr(a, b)[0]
    else:
        r, pv = stats.pearsonr(x, y); f = lambda a, b: stats.pearsonr(a, b)[0]
    lo, hi = boot_ci(x, y, f)
    base.update(r=float(r), p=float(pv), ci_lo=lo, ci_hi=hi)
    return base


def ols(y, X, names):
    """einfache OLS mit Standardfehlern (HC0)."""
    X = np.asarray(X, dtype=float); y = np.asarray(y, dtype=float)
    XtXi = np.linalg.pinv(X.T @ X)
    beta = XtXi @ X.T @ y
    resid = y - X @ beta
    S = (X * (resid**2)[:, None]).T @ X
    V = XtXi @ S @ XtXi
    se = np.sqrt(np.diag(V))
    from scipy import stats
    t = beta/se
    p = 2*(1-stats.norm.cdf(np.abs(t)))
    ss_res = float((resid**2).sum()); ss_tot = float(((y-y.mean())**2).sum())
    return pd.DataFrame(dict(term=names, coef=beta, se=se, t=t, p=p)), 1-ss_res/ss_tot


# --------------------------------------------- 5. main
def enrich(F, d, evd):
    for m in (5, 15, 60):
        L = loo_load(d, evd, m, F)
        for c in ["load_revs", "load_bytes", "load_labels", "load_ip", "load_events"]:
            F[f"{c}_{m}"] = L[c]
    F["hour"] = F.t_mid.dt.hour
    F["logf"] = np.log(F.factor)
    F["ldw"] = np.log(F.wall_delta_s)
    F["ldt"] = np.log(F.task_delta_s)
    return F


def slope_test(F, tag, rows):
    """log(dTask) ~ log(dWall). H_a sagt Steigung 1, reine Arbeitsuhr sagt 0."""
    if len(F) < 10:
        return
    x = F.ldw.to_numpy(); y = F.ldt.to_numpy()
    X = np.column_stack([np.ones(len(x)), x])
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    r = y - X @ b
    se = np.sqrt(np.diag(np.linalg.pinv(X.T @ X) * (r**2).sum()/(len(x)-2)))
    rows.append(dict(datensatz=tag, n=len(F), labels=F.label.nunique(),
                     steigung=b[1], se=se[1], t_gegen_1=(b[1]-1)/se[1],
                     t_gegen_0=b[1]/se[1], median_faktor=F.factor.median()))


def main():
    d, evd = load()
    log(f"[0] Deltas: {len(d)} Versionen, {d.label.nunique()} labels, "
        f"{d.time.min()} .. {d.time.max()}; events: {len(evd)}")

    # ---------------- Schritt 1: Extraktion
    tz = extract(d)
    o = tz.copy(); o["wall_time"] = o.wall_time.dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    o.to_csv(OUT("paper_uhr_taskzeiten.csv"), index=False)
    log(f"[1] Extraktionen {len(tz)} | Wege {tz.groupby('weg').size().to_dict()} | "
        f"labels {tz.label.nunique()} | first_person {int(tz.first_person.sum())} "
        f"({tz.first_person.mean():.1%}) | strict {int(tz.first_person_strict.sum())}")
    c = tz.groupby("label").rev_id.nunique()
    log(f"[1] labels mit >=2 Messversionen: {(c>=2).sum()} | >=3: {(c>=3).sum()}")

    a = tz[tz.weg == "A"].dropna(subset=["wall_seconds_stated"]).copy()
    a["wall_actual"] = a.wall_time.dt.hour*3600 + a.wall_time.dt.minute*60 + a.wall_time.dt.second
    a["err_s"] = ((a.wall_seconds_stated - a.wall_actual + 43200) % 86400) - 43200
    log(f"[1] Weg-A-Aussenzeitpruefung: n={len(a)}, |Fehler| Median={a.err_s.abs().median():.0f}s, "
        f"Anteil <=900s: {(a.err_s.abs()<=900).mean():.1%}  -> 'shared/container UTC' IST die Weltzeit")
    aa = a.copy(); aa["wall_time"] = aa.wall_time.dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    aa[["rev_id","label","wall_time","wall_noun","wall_seconds_stated","wall_actual",
        "err_s","evidence_snippet"]].to_csv(OUT("paper_uhr_wallcheck.csv"), index=False)

    # ---------------- Schritt 2: Faktoren
    AB = tz[tz.weg.isin(["A","B"])]
    F      = enrich(build_factors(AB), d, evd)                       # PRIMAER
    F_all  = enrich(build_factors(tz), d, evd)                       # + Ereignislesungen
    F_clean= enrich(build_factors(AB[AB.first_person_strict]), d, evd)
    F_A    = enrich(build_factors(tz[tz.weg == "A"]), d, evd)
    F_C    = enrich(build_factors(tz[tz.weg == "C"]), d, evd)
    Foff   = build_offset_factors(tz)
    Freg   = regress_per_label(AB)
    for nm, X in [("primaer_AB", F), ("mit_Ereignissen_ABC", F_all), ("streng_AB_fp", F_clean),
                  ("nur_A", F_A), ("nur_C", F_C)]:
        log(f"[2] {nm:22s} n={len(X):4d} labels={X.label.nunique():4d} "
            f"Median={X.factor.median():.3f} IQR=[{X.factor.quantile(.25):.3f},{X.factor.quantile(.75):.3f}] "
            f"Spanne=[{X.factor.min():.3f},{X.factor.max():.2f}]")
    if len(Foff):
        log(f"[2] Weg-A-Offsetlogik (1+dOffset/dWall): n={len(Foff)}, Median={Foff.factor.median():.3f}")
    Freg.to_csv(OUT("paper_uhr_label_regression.csv"), index=False)

    Fx = F.copy()
    for cc in ("t0","t1","t_mid"): Fx[cc] = Fx[cc].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    Fx["datensatz"] = "primaer_AB"
    Fy = F_all.copy()
    for cc in ("t0","t1","t_mid"): Fy[cc] = Fy[cc].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    Fy["datensatz"] = "mit_Ereignissen_ABC"
    pd.concat([Fx, Fy], ignore_index=True).to_csv(OUT("paper_uhr_faktoren.csv"), index=False)

    # Validierung gegen die 11 Selbstmessungen
    cal = pd.read_csv(os.path.join(ART, "harness_clock_calibration.csv"))
    vrows = []
    for r in cal[cal.typ == "messung"].itertuples():
        for nm, X in [("primaer_AB", F), ("mit_Ereignissen_ABC", F_all)]:
            sub = X[X.label == r.label]
            vrows.append(dict(label=r.label, agent_faktor=r.factor_computed,
                              agent_wartelaenge_s=r.task_seconds, agent_shared_s=r.shared_seconds,
                              datensatz=nm, n_maschinell=len(sub),
                              maschinell=";".join(f"{v:.3f}" for v in sub.factor),
                              dwall=";".join(str(int(v)) for v in sub.wall_delta_s),
                              zitat=r.quote))
    pd.DataFrame(vrows).to_csv(OUT("paper_uhr_validierung.csv"), index=False)

    # Wartelaengen-Analyse der 11 Selbstmessungen
    from scipy import stats as st
    cm = cal[cal.typ == "messung"].dropna(subset=["task_seconds","shared_seconds"])
    rs, ps = st.spearmanr(cm.task_seconds, cm.factor_computed)
    b_, a_ = np.polyfit(np.log(cm.task_seconds), np.log(cm.shared_seconds), 1)
    log(f"[2] Selbstmessungen (n={len(cm)}): CV(Innen-Wartedauer)={cm.task_seconds.std(ddof=1)/cm.task_seconds.mean():.2f} "
        f"vs CV(realer Kosten)={cm.shared_seconds.std(ddof=1)/cm.shared_seconds.mean():.2f}; "
        f"log(real)={b_:.2f}*log(innen)+{a_:.2f}; Faktor~Wartelaenge rho={rs:.2f} p={ps:.3f}")

    # ---------------- Schritt 3: Last
    wins = pd.concat([window_table(d, evd, m) for m in (5,15,60)], ignore_index=True)
    wins.to_csv(OUT("paper_uhr_last_fenster.csv"), index=False)
    log(f"[3] Lastzeitreihe {len(wins)} Zeilen (5/15/60 min)")
    lat = d.dropna(subset=["request_time","success_time"]).copy()
    lat["lat_s"] = (pd.to_datetime(lat.success_time, utc=True, errors="coerce")
                    - pd.to_datetime(lat.request_time, utc=True, errors="coerce")).dt.total_seconds()
    log(f"[3] Server-Antwortlatenz (request->success): n={lat.lat_s.notna().sum()}, "
        f"Median={lat.lat_s.median():.1f}s, p90={lat.lat_s.quantile(.9):.1f}s, max={lat.lat_s.max():.1f}s "
        f"-- misst den WIKI-Server, nicht die Inferenz-Infrastruktur")
    lat.groupby(lat.time.dt.hour).lat_s.agg(["count","median","mean"]).to_csv(OUT("paper_uhr_serverlatenz.csv"))

    # ---------------- Schritt 4: Korrelationen
    rows = []
    MASSE = ["load_revs","load_bytes","load_labels","load_ip","load_events"]
    for nm, X in [("primaer_AB", F), ("mit_Ereignissen_ABC", F_all), ("streng_AB_fp", F_clean)]:
        for m in (5,15,60):
            for mass in MASSE:
                x = np.log1p(X[f"{mass}_{m}"].to_numpy())
                for kind in ("spearman","pearson"):
                    rows.append(corr_row(nm, mass, m, x, X.logf.to_numpy(), kind))
                # partiell, kontrolliert fuer log(dWall)
                rx = x - np.polyval(np.polyfit(X.ldw, x, 1), X.ldw)
                ry = X.logf - np.polyval(np.polyfit(X.ldw, X.logf, 1), X.ldw)
                rows.append(corr_row(nm+"|partiell_ldw", mass, m, rx, ry, "spearman"))

    tg = F.groupby("hour").agg(n=("factor","size"), median_factor=("factor","median"),
                               q25=("factor", lambda s: s.quantile(.25)),
                               q75=("factor", lambda s: s.quantile(.75)),
                               mean_logf=("logf","mean"), sd_logf=("logf","std")).reset_index()
    tg["datensatz"] = "primaer_AB"
    tg2 = F_all.groupby("hour").agg(n=("factor","size"), median_factor=("factor","median"),
                                    q25=("factor", lambda s: s.quantile(.25)),
                                    q75=("factor", lambda s: s.quantile(.75)),
                                    mean_logf=("logf","mean"), sd_logf=("logf","std")).reset_index()
    tg2["datensatz"] = "mit_Ereignissen_ABC"
    pd.concat([tg, tg2], ignore_index=True).to_csv(OUT("paper_uhr_tagesgang.csv"), index=False)
    for nm, X in [("primaer_AB", F), ("mit_Ereignissen_ABC", F_all)]:
        g = [x.logf.values for _, x in X.groupby("hour") if len(x) >= 3]
        if len(g) > 2:
            kw = st.kruskal(*g)
            log(f"[4] Tagesgang {nm}: Kruskal-Wallis H={kw.statistic:.2f}, p={kw.pvalue:.3f}, {len(g)} Stunden")

    ols_rows = []
    for nm, X in [("primaer_AB", F), ("mit_Ereignissen_ABC", F_all)]:
        for m in (5,15,60):
            x = np.log1p(X[f"load_revs_{m}"].to_numpy()); h = X.hour.to_numpy()*2*np.pi/24
            M = np.column_stack([np.ones(len(X)), x, np.sin(h), np.cos(h), X.ldw.to_numpy()])
            tab, r2 = ols(X.logf.to_numpy(), M, ["const","log_last_revs","sin_h","cos_h","log_dwall"])
            tab["datensatz"] = nm; tab["fenster_min"] = m; tab["r2"] = r2
            ols_rows.append(tab)
    pd.concat(ols_rows, ignore_index=True).to_csv(OUT("paper_uhr_ols.csv"), index=False)

    # Mechanismus-Test: Steigung log(dTask)~log(dWall)
    srows = []
    for nm, X in [("primaer_AB", F), ("mit_Ereignissen_ABC", F_all), ("streng_AB_fp", F_clean),
                  ("nur_A", F_A), ("nur_C", F_C)]:
        slope_test(X, nm, srows)
    for nm, X in [("primaer_AB", F), ("mit_Ereignissen_ABC", F_all)]:
        mu = X.groupby("label").filter(lambda g: len(g) >= 2).copy()
        if len(mu) >= 10:
            mu["xd"] = mu.ldw - mu.groupby("label").ldw.transform("mean")
            mu["yd"] = mu.ldt - mu.groupby("label").ldt.transform("mean")
            M = mu.xd.to_numpy()[:, None]
            b, *_ = np.linalg.lstsq(M, mu.yd.to_numpy(), rcond=None)
            r = mu.yd.to_numpy() - M @ b
            dof = max(len(mu)-mu.label.nunique()-1, 1)
            se = float(np.sqrt(np.linalg.pinv(M.T @ M)[0,0]*(r**2).sum()/dof))
            srows.append(dict(datensatz=nm+"|innerhalb_label", n=len(mu), labels=mu.label.nunique(),
                              steigung=float(b[0]), se=se, t_gegen_1=(b[0]-1)/se,
                              t_gegen_0=b[0]/se, median_faktor=mu.factor.median()))
    slt = pd.DataFrame(srows); slt.to_csv(OUT("paper_uhr_steigungstest.csv"), index=False)
    log("[4] Mechanismus-Test log(dTask)~log(dWall):"); log(slt.to_string(index=False))

    # clock.wait im Intervall
    wrows = []
    for nm, X in [("primaer_AB", F), ("mit_Ereignissen_ABC", F_all)]:
        def wf(r):
            s = d[(d.label == r.label) & (d.time >= r.t0) & (d.time <= r.t1)]
            return bool(s.delta.astype(str).str.contains(r"clock\.wait", case=False).any())
        X = X.assign(wait=[wf(r) for r in X.itertuples()])
        if X.wait.sum() >= 4 and (~X.wait).sum() >= 4:
            u = st.mannwhitneyu(X[X.wait].logf, X[~X.wait].logf)
            wrows.append(dict(datensatz=nm, n_mit_wait=int(X.wait.sum()), n_ohne=int((~X.wait).sum()),
                              median_mit=X[X.wait].factor.median(), median_ohne=X[~X.wait].factor.median(),
                              U=float(u.statistic), p=float(u.pvalue)))
    pd.DataFrame(wrows).to_csv(OUT("paper_uhr_clockwait.csv"), index=False)
    log("[4] clock.wait-Split:"); log(pd.DataFrame(wrows).to_string(index=False))

    # Innerhalb-label
    irows = []
    for nm, X in [("primaer_AB", F), ("mit_Ereignissen_ABC", F_all), ("streng_AB_fp", F_clean)]:
        mu = X.groupby("label").filter(lambda g: len(g) >= 2)
        if not len(mu):
            continue
        gm = mu.groupby("label").logf
        bv = gm.mean().var(ddof=1); wv = (mu.logf - gm.transform("mean")).var(ddof=1)
        rr = mu.groupby("label").factor.agg(["min","max","size"]); rr["ratio"] = rr["max"]/rr["min"]
        log(f"[4] Innerhalb-label {nm}: {mu.label.nunique()} labels / {len(mu)} Messungen; "
            f"Var zwischen={bv:.3f}, innerhalb={wv:.3f}, ICC={bv/(bv+wv):.3f}; "
            f"Median Max/Min={rr.ratio.median():.2f}; Anteil >2: {(rr.ratio>2).mean():.1%}")
        rr = rr.reset_index(); rr["datensatz"] = nm; irows.append(rr)
    pd.concat(irows, ignore_index=True).to_csv(OUT("paper_uhr_innerhalb_label.csv"), index=False)

    # ---------------- Schritt 5: Robustheit
    half = F.sample(frac=0.5, random_state=42)
    noPeak = F[~((F.t_mid >= pd.Timestamp("2026-06-16", tz="UTC")) &
                 (F.t_mid < pd.Timestamp("2026-06-23", tz="UTC")))]
    F600  = enrich(build_factors(AB, minwall=600), d, evd)
    Fwide = enrich(build_factors(AB, fmin=0.01, fmax=200), d, evd)
    for nm, X in [("robust_haelfte50", half), ("robust_ohne_16_22juni", noPeak),
                  ("robust_minwall600", F600), ("robust_grenzen_0.01_200", Fwide)]:
        for m in (5,15,60):
            col = f"load_revs_{m}"
            if col in X.columns and len(X) >= 8:
                rows.append(corr_row(nm, "load_revs", m, np.log1p(X[col].to_numpy()),
                                     X.logf.to_numpy(), "spearman"))
        slope_test(X, nm, srows)
    pd.DataFrame(rows).to_csv(OUT("paper_uhr_korrelation.csv"), index=False)
    pd.DataFrame(srows).to_csv(OUT("paper_uhr_steigungstest.csv"), index=False)
    K = pd.DataFrame(rows)
    log("[5] Korrelationen (Spearman, primaer_AB):")
    log(K[(K.datensatz == "primaer_AB") & (K.methode == "spearman")].to_string(index=False))
    log("[5] Robustheit:")
    log(K[K.datensatz.str.startswith("robust")].to_string(index=False))
    log("[5] Kontaminierter Vergleichssatz (mit Ereignislesungen):")
    log(K[(K.datensatz == "mit_Ereignissen_ABC") & (K.methode == "spearman")].to_string(index=False))

    for n in (len(F_clean), len(F), len(F_all)):
        z = st.norm.ppf(0.975)
        log(f"[5] Trennschaerfe n={n}: signifikant ab |r|>={np.tanh(z/np.sqrt(max(n-3,1))):.3f}; "
            f"80% Power ab |r|~{np.tanh((z+st.norm.ppf(0.8))/np.sqrt(max(n-3,1))):.3f}")
    log("FERTIG.")


if __name__ == "__main__":
    main()
