"""Build the per-figure data files for the arXiv preprint.

Reads analyse/artefakte/*.csv (paths relative to the repo root), applies the
transformations laid out in analyse/artefakte/BERICHT_visualisierung.md and
writes one JSON per figure to paper/figures/data/fig<N>_<slug>.json.

Every JSON holds data, axis names and marks only; no styling. Rendering is
done by 58_figures_paper.py. No new statistics are computed here: rows are
filtered, reshaped and joined, and the reference lines use parameters that
already exist in the tables (medians, model coefficients) or in MECHANIK.md
(cited in the "sources" block of each file).
"""
from __future__ import annotations

import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / "analyse" / "artefakte"
OUT = ROOT / "paper" / "figures" / "data"
OUT.mkdir(parents=True, exist_ok=True)

MIN_N = 20  # windows with fewer names are masked (convention from 40_chartdata.py)


def csv(name: str) -> pd.DataFrame:
    return pd.read_csv(ART / name)


def write(name: str, obj: dict) -> None:
    p = OUT / f"{name}.json"
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=1, default=_json_default))
    print(f"{p.relative_to(ROOT)}  {p.stat().st_size:,} B")


def _json_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return None if math.isnan(o) else float(o)
    if isinstance(o, (pd.Timestamp, datetime)):
        return o.isoformat()
    raise TypeError(type(o))


def iso(ts) -> str:
    return pd.Timestamp(ts).tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%SZ")


# --------------------------------------------------------------------------
# Fig 1 — two operating states of the internal clock (plan §3.3)
# --------------------------------------------------------------------------
def fig1() -> None:
    f = csv("paper_uhr_faktoren.csv")
    work = f[f["datensatz"] == "primaer_AB"].copy()
    assert len(work) == 71, len(work)
    wait = csv("paper_episode_clockwait_measurements.csv")
    assert len(wait) == 11, len(wait)
    models = csv("paper_math_uhr_clockwait_modelle.csv").set_index("modell")
    pw = models.loc["Potenzgesetz log-log"]
    a, b = float(pw["a"]), float(pw["b"])  # log(shared) = a + b*log(task)

    median_factor = float(work["factor"].median())
    q25, q75 = (float(work["factor"].quantile(q)) for q in (0.25, 0.75))
    outlier = work.loc[work["factor"].idxmax()]

    x_min, x_max = 8.0, 40000.0  # covers 12 s (wait) to 31,824 s (work)

    def factor_line(k: float) -> list[list[float]]:
        return [[x_min, k * x_min], [x_max, k * x_max]]

    def power_line(x0: float, x1: float) -> list[list[float]]:
        # shared = e^a * task^b  ->  task = (shared / e^a) ** (1/b)
        return [[x, (x / math.exp(a)) ** (1.0 / b)] for x in (x0, x1)]

    write("fig1_clock_two_states", {
        "figure": 1,
        "title": "Two operating states of the internal clock",
        "x": {"name": "wall time between two contributions (UTC), s", "scale": "log"},
        "y": {"name": "internal clock advance, s", "scale": "log"},
        "series": [
            {
                "key": "work",
                "label": "working (machine-derived factor)",
                "n": int(len(work)),
                "points": [
                    {"x": float(r.wall_delta_s), "y": float(r.task_delta_s),
                     "factor": float(r.factor), "label": r.label, "weg": r.weg,
                     "t0": r.t0}
                    for r in work.itertuples()
                ],
                "factor_median": median_factor,
                "factor_q25": q25,
                "factor_q75": q75,
                "wall_range_s": [float(work.wall_delta_s.min()), float(work.wall_delta_s.max())],
                "on_16_jun": int((work["t0"].str[:10] == "2026-06-16").sum()),
            },
            {
                "key": "wait",
                "label": "clock.wait (self-reported calibration)",
                "n": int(len(wait)),
                "points": [
                    {"x": float(r.shared_seconds), "y": float(r.task_seconds),
                     "factor": float(r.factor_computed), "label": r.label,
                     "t": r.time_utc}
                    for r in wait.itertuples()
                ],
                "factor_range": [float(wait.factor_computed.min()), float(wait.factor_computed.max())],
                "wall_range_s": [float(wait.shared_seconds.min()), float(wait.shared_seconds.max())],
                "task_max_s": float(wait.task_seconds.max()),
            },
        ],
        "lines": [
            {"key": "slope1", "label": "factor 1", "points": factor_line(1.0)},
            {"key": "median", "label": f"factor {median_factor:.3f} (median, working)",
             "points": factor_line(median_factor)},
            {"key": "wait_power",
             "label": f"wait regime: log(wall) = {a:.2f} + {b:.2f}·log(internal)",
             "a": a, "b": b, "points": power_line(x_min, 400.0)},
        ],
        "marks": [
            {"kind": "point", "x": float(outlier.wall_delta_s), "y": float(outlier.task_delta_s),
             "text": f"factor {outlier.factor:.1f} (working set, outlier)", "label": outlier.label},
        ],
        "sources": {
            "work": "paper_uhr_faktoren.csv (datensatz == primaer_AB; wall_delta_s, task_delta_s, factor)",
            "wait": "paper_episode_clockwait_measurements.csv (shared_seconds, task_seconds, factor_computed)",
            "power_law": "paper_math_uhr_clockwait_modelle.csv (Potenzgesetz log-log: a, b)",
        },
    })


# --------------------------------------------------------------------------
# Fig 2 — time course (plan §3.1)
# --------------------------------------------------------------------------
def fig2() -> None:
    daily = csv("paper_episode_daily.csv")
    daily["t"] = pd.to_datetime(daily["t"])
    full = pd.date_range("2026-05-24", "2026-07-02", freq="D")
    daily = daily.set_index("t").reindex(full, fill_value=0).rename_axis("t").reset_index()
    total = int(daily.n_revs.sum())
    top4 = daily.nlargest(4, "n_revs").sort_values("t")
    top4_share = float(top4.n_revs.sum() / total)

    hourly = csv("paper_episode_hourly.csv")
    hourly["hour_utc"] = pd.to_datetime(hourly["hour_utc"], utc=True)
    active_hours = int((hourly.n_revs > 0).sum())
    # Lower panel is cropped to 16 Jun 00:00 – 23 Jun 00:00: all coordination
    # happens there; outside this window 688 of 948 hours are zero and the
    # upper panel already shows the emptiness. Cropping keeps the hourly peak
    # legible without an axis break (plan §3.1 rejects axis breaks).
    lo, hi = pd.Timestamp("2026-06-16", tz="UTC"), pd.Timestamp("2026-06-23", tz="UTC")
    crop = hourly[(hourly.hour_utc >= lo) & (hourly.hour_utc < hi)]
    peak_revs = hourly.loc[hourly.n_revs.idxmax()]
    peak_labels = hourly.loc[hourly.n_labels.idxmax()]

    write("fig2_time_course", {
        "figure": 2,
        "title": "Time course of the incident",
        "panels": {
            "daily": {
                "x": {"name": "date (wall time, UTC)"},
                "y": {"name": "revisions per day"},
                "n_days": int(len(daily)),
                "total_revisions": total,
                "points": [[d.strftime("%Y-%m-%d"), int(v)] for d, v in zip(daily.t, daily.n_revs)],
                "top4_days": [d.strftime("%Y-%m-%d") for d in top4.t],
                "top4_share": top4_share,
            },
            "hourly": {
                "x": {"name": "wall time, UTC (16–22 Jun)"},
                "y": {"name": "revisions per hour"},
                "y2": {"name": "distinct names per hour"},
                "crop": [iso(lo), iso(hi)],
                "crop_reason": "coordination window; 688 of 948 hours in the full range are zero",
                "n_hours_total": int(len(hourly)),
                "n_hours_active": active_hours,
                "points": [[iso(t), int(a), int(b)] for t, a, b in zip(crop.hour_utc, crop.n_revs, crop.n_labels)],
            },
        },
        "marks": [
            {"kind": "vline", "panel": "both", "t": "2026-06-16T09:27:10Z",
             "text": "16 Jun 09:27 — coordination begins"},
            {"kind": "span", "panel": "both", "t0": "2026-06-21T21:00:00Z", "t1": "2026-06-22T06:00:00Z",
             "text": "night of 21/22 Jun — coordination ends"},
            {"kind": "point", "panel": "hourly", "t": iso(peak_revs.hour_utc), "y": int(peak_revs.n_revs),
             "text": f"{int(peak_revs.n_revs):,} revisions, of which 1,769 are one copy loop"},
            {"kind": "point", "panel": "hourly", "t": iso(peak_labels.hour_utc), "y2": int(peak_labels.n_labels),
             "text": f"{int(peak_labels.n_labels)} names"},
        ],
        "sources": {
            "daily": "paper_episode_daily.csv (t, n_revs; missing days filled with 0)",
            "hourly": "paper_episode_hourly.csv (hour_utc, n_revs, n_labels)",
            "copy_loop_1769": "MECHANIK.md §2 (not in a CSV)",
        },
    })


# --------------------------------------------------------------------------
# Fig 3 — format convergence (plan §3.6)
# --------------------------------------------------------------------------
def fig3() -> None:
    q = csv("paper_lernkurve_q3_format_erstversion_koordpop_6h.csv")
    q["f"] = pd.to_datetime(q["f"], utc=True)
    series_def = [
        # key, label, family
        ("cohort", "“cohort”", "invented"),
        ("runde", "round marker", "invented"),
        ("meldeformat", "full report format", "invented"),
        ("sig_endzeile", "signature line", "brought"),
        ("please_relay", "request formula (“please relay”)", "brought"),
    ]
    kept = q[q.n >= MIN_N]
    masked = q[q.n < MIN_N]
    series = []
    for key, label, fam in series_def:
        pts = [[iso(t), (None if n < MIN_N else float(v)), int(n)] for t, v, n in zip(q.f, q[key], q.n)]
        series.append({"key": key, "label": label, "family": fam, "points": pts,
                       "first": float(q[key].iloc[0]),
                       "max": float(kept[key].max()),
                       "max_at": iso(kept.loc[kept[key].idxmax(), "f"])})
    t_start = pd.Timestamp("2026-06-16T09:27:10Z")
    write("fig3_format_convergence", {
        "figure": 3,
        "title": "Format convergence in newcomers' first contributions",
        "x": {"name": "6-h window (wall time, UTC)"},
        "y": {"name": "share of first contributions carrying the feature, %"},
        "min_n": MIN_N,
        "n_windows_total": int(len(q)),
        "n_windows_kept": int(len(kept)),
        "masked_windows": [[iso(t), int(n)] for t, n in zip(masked.f, masked.n)],
        "window_n": [[iso(t), int(n)] for t, n in zip(q.f, q.n)],
        "names_total_kept": int(kept.n.sum()),
        "series": series,
        "marks": [
            {"kind": "vline", "t": iso(t_start), "text": "16 Jun 09:27 — coordination begins"},
            {"kind": "span", "t0": iso(t_start), "t1": iso(t_start + timedelta(hours=24)), "text": "first 24 h"},
        ],
        "sources": {"data": "paper_lernkurve_q3_format_erstversion_koordpop_6h.csv (f, cohort, runde, meldeformat, sig_endzeile, please_relay, n)"},
    })


# --------------------------------------------------------------------------
# Fig 4 — load null result as forest plot (plan §3.4)
# --------------------------------------------------------------------------
MEASURE_LABEL = {
    "load_revs": "revisions",
    "load_bytes": "bytes",
    "load_labels": "names",
    "load_ip": "IP blocks",
    "load_events": "server events",
}
ROBUST_LABEL = {
    "robust_haelfte50": "half sample (n=36)",
    "robust_minwall600": "wall ≥ 600 s (n=55)",
    "robust_grenzen_0.01_200": "bounds 0.01–200 (n=73)",
}


def fig4() -> None:
    k = csv("paper_uhr_korrelation.csv")
    k = k[k.methode == "spearman"]

    def rows(ds: str) -> list[dict]:
        sub = k[k.datensatz == ds]
        out = []
        for w in (5, 15, 60):
            for m in MEASURE_LABEL:
                r = sub[(sub.fenster_min == w) & (sub.mass == m)].iloc[0]
                out.append({"group": f"{w} min", "measure": MEASURE_LABEL[m], "window_min": int(w),
                            "rho": float(r.r), "ci_lo": float(r.ci_lo), "ci_hi": float(r.ci_hi),
                            "p": float(r.p), "n": int(r.n)})
        return out

    robust = []
    for ds, lab in ROBUST_LABEL.items():
        sub = k[(k.datensatz == ds) & (k.mass == "load_revs")]
        for r in sub.sort_values("fenster_min").itertuples():
            robust.append({"group": "robustness (revisions)", "measure": f"{lab}, {int(r.fenster_min)} min",
                           "window_min": int(r.fenster_min), "rho": float(r.r), "ci_lo": float(r.ci_lo),
                           "ci_hi": float(r.ci_hi), "p": float(r.p), "n": int(r.n)})

    clean = rows("primaer_AB")
    dirty = rows("mit_Ereignissen_ABC")
    write("fig4_load_null_forest", {
        "figure": 4,
        "title": "Internal-clock factor vs. wiki load: Spearman ρ with 95 % CI",
        "x": {"name": "Spearman ρ (factor vs. load)", "range": [-0.4, 0.6]},
        "panels": [
            {"key": "clean", "title": "A  clean set (primaer_AB), n = 71", "rows": clean, "robustness": robust,
             "n": 71, "rho_range": [min(r["rho"] for r in clean), max(r["rho"] for r in clean)],
             "p_range": [min(r["p"] for r in clean), max(r["p"] for r in clean)],
             "all_ci_contain_zero": all(r["ci_lo"] < 0 < r["ci_hi"] for r in clean)},
            {"key": "dirty", "title": "B  contaminated set (mit_Ereignissen_ABC), n = 281", "rows": dirty,
             "n": 281, "rho_range": [min(r["rho"] for r in dirty), max(r["rho"] for r in dirty)],
             "p_max": max(r["p"] for r in dirty),
             "all_ci_contain_zero": all(r["ci_lo"] < 0 < r["ci_hi"] for r in dirty)},
        ],
        "marks": [
            {"kind": "vline", "x": 0.0, "text": "ρ = 0"},
            {"kind": "span", "x0": -0.33, "x1": 0.33, "text": "|ρ| < 0.33: not detectable at 80 % power (n = 71)"},
            {"kind": "text", "text": "load hypothesis requires ρ < 0"},
            {"kind": "text", "text": "15 tests ≈ 2.2 effectively independent tests (load measures correlate at 0.97)"},
        ],
        "sources": {
            "data": "paper_uhr_korrelation.csv (datensatz, mass, fenster_min, methode == spearman, n, r, p, ci_lo, ci_hi)",
            "power_0_33": "MECHANIK.md §7.4 (not in a CSV)",
            "effective_tests_2_2": "MECHANIK.md §7.4 (not in a CSV)",
        },
    })


# --------------------------------------------------------------------------
# Fig 5 — round staircase R1–R7 as speech-act stack (plan §3.5)
# --------------------------------------------------------------------------
def fig5() -> None:
    m = csv("paper_episode_round_mentions.csv")
    r = m[m.family == "R"].sort_values("num")
    s = csv("paper_episode_r6_sichtung.csv")
    s6 = s[s.num == 6]
    s7 = s[s.num == 7]
    arr6 = s6[s6.urteil == "ANKUNFT"]
    arr7 = s7[s7.urteil == "ANKUNFT"]
    # Same name posting the same sentence twice counts as one arrival.
    n6_arrivals = int(arr6.drop_duplicates(["label", "sent"]).shape[0])
    n7_arrivals = int(arr7.drop_duplicates(["label", "sent"]).shape[0])
    assert n6_arrivals == 1 and n7_arrivals == 1, (n6_arrivals, n7_arrivals)

    cls = ["observation", "request", "prediction", "negation", "unclassified"]
    rows = []
    for x in r.itertuples():
        if x.num > 7:
            continue
        d = {"round": f"R{x.num}", "n_revs": int(x.n_revs), "n_labels": int(x.n_labels)}
        for c in cls:
            d[c] = int(getattr(x, c))
        d["observation_table"] = int(x.observation)
        rows.append(d)
    tail = r[r.num >= 8]
    d = {"round": "R8+", "n_revs": int(tail.n_revs.sum()), "n_labels": int(tail.n_labels.sum())}
    for c in cls:
        d[c] = int(tail[c].sum())
    d["observation_table"] = d["observation"]
    rows.append(d)
    # Reviewed values (display only; the table stays unchanged in the repo).
    for d in rows:
        if d["round"] == "R6":
            d["observation"] = n6_arrivals
        if d["round"] == "R7":
            d["observation"] = n7_arrivals

    write("fig5_round_staircase", {
        "figure": 5,
        "title": "Rounds R1–R7: what was said about each round",
        "x": {"name": "sentences mentioning the round (classified), count"},
        "y": {"name": "round"},
        "classes": cls,
        "rows": rows,
        "review": {
            "candidates_total": int(len(s)),
            "r6_candidates": int(len(s6)), "r6_ankunft_rows": int(len(arr6)), "r6_arrivals": n6_arrivals,
            "r7_candidates": int(len(s7)), "r7_ankunft_rows": int(len(arr7)), "r7_arrivals": n7_arrivals,
            "r6_table_observation": int(r[r.num == 6].observation.iloc[0]),
            "r7_table_observation": int(r[r.num == 7].observation.iloc[0]),
            "arrival_sentences": arr6.drop_duplicates(["label", "sent"]).sent.tolist()
            + arr7.drop_duplicates(["label", "sent"]).sent.tolist(),
        },
        "marks": [
            {"kind": "text", "row": "R6",
             "text": f"1 arrival after manual review (table: {int(r[r.num == 6].observation.iloc[0])}; {len(s6)} candidate sentences)"},
            {"kind": "text", "row": "R7", "text": "1 arrival (reviewed)"},
        ],
        "sources": {
            "counts": "paper_episode_round_mentions.csv (family == R; observation, request, prediction, negation, unclassified)",
            "review": "paper_episode_r6_sichtung.csv (urteil == ANKUNFT)",
        },
    })


# --------------------------------------------------------------------------
# Fig 6 — lead time on the board, ECDF (optional)
# --------------------------------------------------------------------------
def fig6() -> None:
    n = csv("paper_neuheit_vorsprung_eigenankunft_labels.csv")
    # Non-first reporters (lead > 0) within 24 h; first reporters have lead 0.
    w = n[(n.lead_h > 0) & (n.lead_h <= 24)].sort_values("lead_h")
    wait = csv("paper_episode_clockwait_measurements.csv")
    max_wait_min = float(wait.task_seconds.max() / 60.0)
    leads = w.lead_h.to_numpy()
    ecdf = np.arange(1, len(leads) + 1) / len(leads)
    write("fig6_lead_ecdf", {
        "figure": 6,
        "title": "Lead time non-first reporters had on the board",
        "x": {"name": "lead of the first report on the board, h (upper bound)", "scale": "log"},
        "y": {"name": "share of reporter–item pairs with lead ≤ x"},
        "n_rows": int(len(w)),
        "n_distinct_names": int(w.label.nunique()),
        "n_rows_all": int(len(n)),
        "median_h": float(np.median(leads)),
        "share_ge_1h": float((leads >= 1).mean()),
        "points": [[float(x), float(y)] for x, y in zip(leads, ecdf)],
        "marks": [
            {"kind": "vline", "x": max_wait_min / 60.0,
             "text": f"{max_wait_min:.0f} min: most internal time a clock.wait ever bought"},
            {"kind": "vline", "x": 1.0, "text": "1 h"},
        ],
        "sources": {
            "leads": "paper_neuheit_vorsprung_eigenankunft_labels.csv (lead_h; rows with 0 < lead_h ≤ 24)",
            "max_wait": "paper_episode_clockwait_measurements.csv (max task_seconds = 1648 s)",
        },
    })


# --------------------------------------------------------------------------
# Fig 7 — population estimate (plan §3.11)
# --------------------------------------------------------------------------
def fig7() -> None:
    e = csv("paper_flotte_schaetzer_versoehnt.csv")
    label_map = {
        "Labels, alle (m,d)-Marker": "names, all (month, day) markers",
        "Labels, nur kalendergueltig": "names, calendar-valid markers only",
        "bereinigt: minus 20 reale Schreibdaten": "names, minus 20 real writing dates (canonical)",
        "Labels + Seitennamen": "names + page names",
        "Selbstbenannte Kohorten": "self-named cohorts",
        "Verhaeltnis Labels:Kohorten": "ratio names : cohorts (no interval)",
    }
    rows = []
    for r in e.itertuples():
        rows.append({
            "key": r.verfahren, "label": label_map[r.verfahren],
            "observed": (None if r.beobachtet_D < 0 else int(r.beobachtet_D)),
            "n_hat": int(r.n_hat),
            "ci_lo": (None if r.ci_lo < 0 else int(r.ci_lo)),
            "ci_hi": (None if r.ci_hi < 0 else int(r.ci_hi)),
            "canonical": str(r.bemerkung).startswith("KANONISCH"),
            "note": r.bemerkung,
        })
    write("fig7_population_estimate", {
        "figure": 7,
        "title": "Population estimate: episodes behind 3,103 names",
        "x": {"name": "estimated number of episodes", "range": [0, 3300]},
        "rows": rows,
        "marks": [
            {"kind": "vline", "x": 294, "text": "294 self-named cohorts (hard floor)"},
            {"kind": "vline", "x": 3103, "text": "3,103 distinct names (naive count)"},
        ],
        "sources": {"data": "paper_flotte_schaetzer_versoehnt.csv (verfahren, beobachtet_D, n_hat, ci_lo, ci_hi, bemerkung)",
                    "names_3103": "MECHANIK.md §1 (not in this CSV)"},
    })


# --------------------------------------------------------------------------
# Fig 9 — progress forest plot (controlled β, family-clustered 95 % CI)
# --------------------------------------------------------------------------
PROGRESS_ORDER = [  # same order as paper/tables/tab_progress.tex
    ("log_kadenz_s", "Cadence (log s)"),
    ("log_r1_frist_s", "Initial deadline (log s)"),
    ("log_folgefrist_s", "Answer deadline (log s)"),
    ("clock_wait_b", "clock.wait used"),
    ("counterapi_b", "counterapi used"),
    ("umleitung_b", "Redirect services"),
    ("blob_ausbruch_b", "Blob egress"),
    ("beobachtung_auf_fremder_seite_b", "Observation on foreign page"),
    ("bitten_quote", "Request rate"),
    ("zukunft_erhalten_n_b", "Future answer received"),
    ("exp_runde_max_vor", "Highest round visible on arrival"),
    ("exp_vorsprung_b", "Answer ahead visible on arrival"),
]
PROGRESS_MODEL = "OLS_std_FE_cluster"
PROGRESS_SUBSETS = [("alle", "base"), ("n_deltas>=5", "ge5")]
MIN_TREATED_FAMILIES = 5  # † in tab_progress.tex: fewer treated families than this


def fig9() -> None:
    e = csv("paper_robust_fortschritt_effekte.csv")
    e = e[(e.variante == "basis") & (e.modell == PROGRESS_MODEL)]
    rows = []
    for key, label in PROGRESS_ORDER:
        d = {"key": key, "label": label}
        for sub, skey in PROGRESS_SUBSETS:
            r = e[(e.praediktor == key) & (e.teilmenge == sub)]
            assert len(r) == 1, (key, sub, len(r))
            r = r.iloc[0]
            est = None if pd.isna(r.effekt) else float(r.effekt)
            d[skey] = {
                "beta": est,
                "ci_lo": None if est is None else float(r.ci_lo),
                "ci_hi": None if est is None else float(r.ci_hi),
                "p": None if est is None else float(r.p),
                "q_bh": None if est is None else float(r.q_bh),
                "n": int(r.n),
                "n_fam": int(r.n_fam),
                "n_fam_true": int(r.n_fam_true),
                "binary": bool(r.binaer),
                "note": None if pd.isna(r.grund) else str(r.grund),
                "source_row": {"praediktor": key, "teilmenge": sub, "variante": "basis", "modell": PROGRESS_MODEL},
            }
        d["dagger"] = d["base"]["n_fam_true"] < MIN_TREATED_FAMILIES
        rows.append(d)

    write("fig9_progress_forest", {
        "figure": 9,
        "title": "Progress predictors: controlled standardised β with family-clustered 95 % CI",
        "x": {"name": "controlled standardised β (family-clustered 95 % CI)", "range": [-1.0, 0.8]},
        "model": PROGRESS_MODEL,
        "subsets": [{"key": skey, "teilmenge": sub,
                     "label": ("base, n = 510" if skey == "base" else "≥ 5 revisions, n = 256")}
                    for sub, skey in PROGRESS_SUBSETS],
        "dagger_rule": f"fewer than {MIN_TREATED_FAMILIES} treated families in the base set (n_fam_true)",
        "rows": rows,
        "marks": [{"kind": "vline", "x": 0.0, "text": "β = 0"}],
        "sources": {
            "data": "paper_robust_fortschritt_effekte.csv (variante == basis, modell == OLS_std_FE_cluster; "
                    "teilmenge in {alle, n_deltas>=5}; effekt, ci_lo, ci_hi, p, q_bh, n, n_fam, n_fam_true, grund)",
            "order": "paper/tables/tab_progress.tex",
        },
    })


if __name__ == "__main__":
    for fn in (fig1, fig2, fig3, fig4, fig5, fig6, fig7, fig9):
        fn()
