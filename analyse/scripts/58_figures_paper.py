"""Render the preprint figures from paper/figures/data/*.json (built by 57_chartdata_paper.py).

Output: paper/figures/fig<N>_<slug>.pdf (vector, primary) and .png (300 dpi).
Conventions: single column 3.4 in, double column 7.0 in; 8 pt type; Okabe-Ito
colours; every two-state distinction is also carried by marker shape, line
style or hatch; n printed inside each panel; axis titles carry units and the
time base ("wall time, UTC" / "internal clock, s"); dates as "16 Jun 20:00".
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "paper" / "figures" / "data"
OUT = ROOT / "paper" / "figures"

# Okabe-Ito
OI = {
    "orange": "#E69F00", "sky": "#56B4E9", "green": "#009E73", "yellow": "#F0E442",
    "blue": "#0072B2", "verm": "#D55E00", "purple": "#CC79A7", "black": "#000000", "grey": "#7F7F7F",
}
SINGLE, DOUBLE = 3.4, 7.0

plt.rcParams.update({
    "font.size": 8, "axes.titlesize": 8, "axes.labelsize": 8, "xtick.labelsize": 7, "ytick.labelsize": 7,
    "legend.fontsize": 7, "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Helvetica", "Arial"],
    "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none",
    "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "xtick.major.size": 2.5, "ytick.major.size": 2.5,
    "axes.spines.top": False, "axes.spines.right": False,
    "legend.frameon": False, "figure.dpi": 100, "savefig.dpi": 300,
})


def load(name: str) -> dict:
    return json.loads((DATA / f"{name}.json").read_text())


def save(fig, name: str) -> None:
    for ext in ("pdf", "png"):
        p = OUT / f"{name}.{ext}"
        fig.savefig(p, bbox_inches="tight", pad_inches=0.02)
        print(f"{p.relative_to(ROOT)}  {p.stat().st_size:,} B")
    plt.close(fig)


def ts(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def fmt_dt(d: datetime) -> str:
    return d.strftime("%-d %b %H:%M")


class DayHourFormatter(mdates.DateFormatter):
    """'16 Jun 20:00' style, or '16 Jun' at midnight."""

    def __init__(self):
        super().__init__("%-d %b %H:%M", tz=timezone.utc)

    def __call__(self, x, pos=None):
        d = mdates.num2date(x, tz=timezone.utc)
        return d.strftime("%-d %b") if (d.hour == 0 and d.minute == 0) else d.strftime("%-d %b %H:%M")


def n_text(ax, text, loc="upper left", **kw):
    x, ha = (0.02, "left") if "left" in loc else (0.98, "right")
    y, va = (0.97, "top") if "upper" in loc else (0.03, "bottom")
    ax.text(x, y, text, transform=ax.transAxes, ha=ha, va=va, fontsize=7, **kw)


# --------------------------------------------------------------------------
def fig1():
    d = load("fig1_clock_two_states")
    work, wait = d["series"]
    fig, ax = plt.subplots(figsize=(SINGLE, 3.1))
    ax.set_xscale("log")
    ax.set_yscale("log")
    # reference lines
    # The fitted wait-regime power law (exponent 0.55) is withdrawn in the paper
    # (CI [0.09, 1.00] at n = 11); only the two reference slopes are drawn.
    for ln, style in zip(d["lines"][:2], [
        dict(color=OI["grey"], ls=":", lw=0.8),
        dict(color=OI["black"], ls="--", lw=0.8),
    ]):
        (x0, y0), (x1, y1) = ln["points"]
        ax.plot([x0, x1], [y0, y1], zorder=1, **style)
    ax.scatter([p["x"] for p in work["points"]], [p["y"] for p in work["points"]],
               s=14, marker="o", facecolors="none", edgecolors=OI["blue"], linewidths=0.7, zorder=3,
               label=f"working, n = {work['n']}\n(median {work['factor_median']:.3f}, IQR {work['factor_q25']:.3f}–{work['factor_q75']:.3f})")
    ax.scatter([p["x"] for p in wait["points"]], [p["y"] for p in wait["points"]],
               s=18, marker="D", color=OI["verm"], zorder=4,
               label=f"clock.wait, n = {wait['n']}\n(factor {wait['factor_range'][0]:.1f}–{wait['factor_range'][1]:.1f})")
    ax.set_xlim(7, 40000)
    ax.set_ylim(7, 80000)
    ax.set_xlabel("wall time between two contributions (UTC), s")
    ax.set_ylabel("internal clock advance, s")
    # line labels
    ax.text(2500, 2500 * 1.4, "factor 1", fontsize=7, color=OI["grey"], rotation=39, ha="center", va="bottom")
    ax.text(15000, 15000 * work["factor_median"] * 0.62, f"factor {work['factor_median']:.3f} (median)", fontsize=7,
            rotation=39, ha="center", va="top")
    ax.text(8, 7000, "wait regime (during clock.wait):\nclock jumps ahead, factor 1.0–18.9", fontsize=6.5, color=OI["verm"],
            ha="left", va="bottom")
    m = d["marks"][0]
    ax.annotate(f"factor {m['x'] and (m['y'] / m['x']):.1f}\n(working set)", xy=(m["x"], m["y"]),
                xytext=(3000, 40000), fontsize=6.5, ha="left", va="center",
                arrowprops=dict(arrowstyle="-", lw=0.5, color=OI["grey"]))
    ax.legend(loc="lower right", handletextpad=0.3, borderaxespad=0.2, fontsize=6.5, labelspacing=0.5)
    save(fig, "fig1_clock_two_states")


# --------------------------------------------------------------------------
def fig2():
    d = load("fig2_time_course")
    dd, hh = d["panels"]["daily"], d["panels"]["hourly"]
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(DOUBLE, 3.6), gridspec_kw=dict(height_ratios=[1, 1.35], hspace=0.55))

    days = [datetime.strptime(p[0], "%Y-%m-%d").replace(tzinfo=timezone.utc) for p in dd["points"]]
    vals = [p[1] for p in dd["points"]]
    ax1.bar(days, vals, width=0.8, color=OI["blue"], lw=0)
    ax1.set_ylabel("revisions per day")
    ax1.set_xlabel("date (wall time, UTC)")
    ax1.xaxis.set_major_locator(mdates.DayLocator(bymonthday=[1, 8, 15, 22, 29]))
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%-d %b", tz=timezone.utc))
    ax1.xaxis.set_minor_locator(mdates.DayLocator())
    ax1.set_xlim(datetime(2026, 5, 23, 12, tzinfo=timezone.utc), datetime(2026, 7, 3, 12, tzinfo=timezone.utc))
    ax1.set_ylim(0, 7200)
    top = max(vals)
    ax1.annotate(f"{top:,}", xy=(days[vals.index(top)], top), xytext=(0, 2), textcoords="offset points",
                 ha="center", va="bottom", fontsize=7)
    ax1.set_title(f"A  full range 24 May – 2 Jul: {dd['n_days']} days, {dd['total_revisions']:,} revisions; "
                  f"{dd['top4_share'] * 100:.1f} % on 16–18 and 22 Jun", loc="left", fontsize=8)

    hours = [ts(p[0]) for p in hh["points"]]
    revs = [p[1] for p in hh["points"]]
    labels = [p[2] for p in hh["points"]]
    ax2.bar(hours, revs, width=1 / 24, align="edge", color=OI["blue"], lw=0, label="revisions per hour")
    ax2.set_ylabel("revisions per hour")
    ax2.set_xlabel("wall time, UTC (16–22 Jun, cropped)")
    ax2.set_ylim(0, 2700)
    ax2b = ax2.twinx()
    ax2b.spines["right"].set_visible(True)
    ax2b.plot([h.replace(minute=30) for h in hours], labels, color=OI["verm"], ls="--", lw=0.8, label="distinct names per hour")
    ax2b.set_ylabel("distinct names per hour", color=OI["verm"])
    ax2b.tick_params(axis="y", colors=OI["verm"])
    ax2b.set_ylim(0, 400)
    ax2.set_xlim(ts(hh["crop"][0]), ts(hh["crop"][1]))
    ax2.xaxis.set_major_locator(mdates.DayLocator())
    ax2.xaxis.set_minor_locator(mdates.HourLocator(byhour=[6, 12, 18]))
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%-d %b", tz=timezone.utc))
    ax2.set_title("B  hourly detail", loc="left", fontsize=8)
    n_text(ax2, f"{hh['n_hours_active']} of {hh['n_hours_total']} hours in the full range have any activity",
           loc="upper right")

    for m in d["marks"]:
        if m["kind"] == "vline":
            t = ts(m["t"])
            for ax in (ax1, ax2):
                ax.axvline(t, color=OI["black"], lw=0.6, ls="-.")
            ax1.text(t, 7100, m["text"] + " ", fontsize=6.5, ha="right", va="top")
        elif m["kind"] == "span":
            t0, t1 = ts(m["t0"]), ts(m["t1"])
            for ax in (ax1, ax2):
                ax.axvspan(t0, t1, color=OI["grey"], alpha=0.25, lw=0)
            ax1.text(t1, 7100, " " + m["text"], fontsize=6.5, ha="left", va="top")
        elif m["kind"] == "point" and "y" in m:
            t = ts(m["t"])
            ax2.annotate(f"{fmt_dt(t)}: {m['text']}", xy=(t.replace(minute=30), m["y"]), xytext=(12, -2),
                         textcoords="offset points", ha="left", va="top", fontsize=6.5,
                         arrowprops=dict(arrowstyle="-", lw=0.5))
        elif m["kind"] == "point" and "y2" in m:
            t = ts(m["t"])
            ax2b.annotate(f"{fmt_dt(t)}: {m['text']}", xy=(t.replace(minute=30), m["y2"]), xytext=(6, 10),
                          textcoords="offset points", ha="left", va="bottom", fontsize=6.5, color=OI["verm"],
                          arrowprops=dict(arrowstyle="-", lw=0.5, color=OI["verm"]))
    h1, l1 = ax2.get_legend_handles_labels()
    h2, l2 = ax2b.get_legend_handles_labels()
    ax2.legend(h1 + h2, l1 + l2, loc="upper right", bbox_to_anchor=(1.0, 0.78))
    save(fig, "fig2_time_course")


# --------------------------------------------------------------------------
def fig3():
    d = load("fig3_format_convergence")
    style = {
        "cohort": dict(color=OI["blue"], ls="-", marker="o"),
        "runde": dict(color=OI["verm"], ls="-", marker="s"),
        "meldeformat": dict(color=OI["green"], ls="-", marker="^"),
        "sig_endzeile": dict(color=OI["black"], ls="--", marker="v"),
        "please_relay": dict(color=OI["sky"], ls="--", marker="D"),
    }
    fig, (axn, ax) = plt.subplots(2, 1, figsize=(SINGLE, 3.4), sharex=True,
                                  gridspec_kw=dict(height_ratios=[1, 4.2], hspace=0.08))
    wn = [(ts(t), n) for t, n in d["window_n"]]
    axn.bar([t for t, _ in wn], [n for _, n in wn], width=6 / 24, align="edge",
            color=[OI["grey"] if n >= d["min_n"] else "#D0D0D0" for _, n in wn], lw=0)
    axn.set_ylabel("n names", fontsize=7)
    axn.set_yscale("log")
    axn.set_ylim(1, 600)
    axn.set_yticks([1, 10, 100])
    axn.axhline(d["min_n"], color=OI["black"], lw=0.5, ls=":")
    axn.text(1.0, d["min_n"], f" n = {d['min_n']}", transform=axn.get_yaxis_transform(), fontsize=6, va="center")
    axn.tick_params(labelbottom=False)

    for s in d["series"]:
        pts = [(ts(t), v) for t, v, n in s["points"] if v is not None]
        ns = [n for t, v, n in s["points"] if v is not None]
        st = style[s["key"]]
        x = [t.replace(hour=t.hour + 3) for t, _ in pts]  # window centre
        ax.plot(x, [v for _, v in pts], color=st["color"], ls=st["ls"], lw=0.9, zorder=2)
        ax.scatter(x, [v for _, v in pts], s=[max(4, 0.35 * np.sqrt(n) * 4) for n in ns], marker=st["marker"],
                   color=st["color"], zorder=3, linewidths=0)
    ax.set_ylim(-3, 103)
    ax.set_ylabel("share of first contributions, %")
    ax.set_xlabel("6-h window (wall time, UTC)")
    for m in d["marks"]:
        if m["kind"] == "vline":
            for a in (ax, axn):
                a.axvline(ts(m["t"]), color=OI["black"], lw=0.6, ls="-.")
            ax.text(ts(m["t"]), 99, "16 Jun 09:27 ", fontsize=6, ha="right", va="top", rotation=90)
        else:
            for a in (ax, axn):
                a.axvspan(ts(m["t0"]), ts(m["t1"]), color=OI["grey"], alpha=0.15, lw=0)
            ax.text(ts(m["t0"]) + (ts(m["t1"]) - ts(m["t0"])) / 2, 101, "first 24 h", fontsize=6.5, ha="center", va="top")
    ax.set_xlim(datetime(2026, 6, 16, 4, tzinfo=timezone.utc), datetime(2026, 6, 22, 2, tzinfo=timezone.utc))
    ax.xaxis.set_major_locator(mdates.DayLocator())
    ax.xaxis.set_minor_locator(mdates.HourLocator(byhour=[12]))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%-d %b", tz=timezone.utc))
    handles = [Line2D([], [], color=style[s["key"]]["color"], ls=style[s["key"]]["ls"], marker=style[s["key"]]["marker"],
                      ms=3.5, lw=0.9, label=s["label"] + (" (brought)" if s["family"] == "brought" else " (invented)"))
               for s in d["series"]]
    ax.legend(handles=handles, loc="lower right", fontsize=6, handlelength=2.6, borderaxespad=0.3, labelspacing=0.25)
    axn.set_title(f"newcomers per window; {d['n_windows_kept']} of {d['n_windows_total']} windows (n ≥ {d['min_n']}) shown, "
                  f"{d['names_total_kept']:,} names; marker area ∝ n", loc="left", fontsize=6)
    save(fig, "fig3_format_convergence")


# --------------------------------------------------------------------------
def fig4():
    d = load("fig4_load_null_forest")
    A, B = d["panels"]
    rowsA = A["rows"] + A["robustness"]
    rowsB = B["rows"]
    nrow = len(rowsA)
    fig, axes = plt.subplots(1, 2, figsize=(DOUBLE, 3.9), sharey=True, gridspec_kw=dict(wspace=0.42, width_ratios=[1, 1]))
    ypos = np.arange(nrow)[::-1]

    def draw(ax, rows, color, title):
        for y, r in zip(ypos, rows):
            excl = not (r["ci_lo"] < 0 < r["ci_hi"])
            ax.plot([r["ci_lo"], r["ci_hi"]], [y, y], color=color, lw=0.9, solid_capstyle="butt")
            for xc in (r["ci_lo"], r["ci_hi"]):
                ax.plot([xc, xc], [y - 0.22, y + 0.22], color=color, lw=0.9)
            ax.plot(r["rho"], y, marker="s" if excl else "o", ms=4, color=color,
                    mfc=color if excl else "white", mew=0.9)
            ax.text(1.02, y, f"{r['rho']:+.2f}  p = {r['p']:.2g}" if r["p"] >= 1e-3 else f"{r['rho']:+.2f}  p = {r['p']:.0e}",
                    fontsize=6, va="center", ha="left", transform=ax.get_yaxis_transform(), clip_on=False)
        ax.set_title(title, loc="left", fontsize=8)

    draw(axes[0], rowsA, OI["blue"], A["title"])
    draw(axes[1], rowsB, OI["verm"], B["title"])
    for ax in axes:
        ax.axvline(0, color=OI["black"], lw=0.6)
        ax.axvspan(-0.33, 0.33, color=OI["grey"], alpha=0.12, lw=0)
        ax.set_xlim(*d["x"]["range"])
        ax.set_xlabel(d["x"]["name"])
        ax.set_ylim(-1.4, nrow + 0.6)
        # group separators
        prev = None
        for y, r in zip(ypos, rowsA):
            if prev is not None and r["group"] != prev:
                ax.axhline(y + 0.5, color=OI["grey"], lw=0.4, ls=":")
            prev = r["group"]
        ax.spines["left"].set_visible(False)
        ax.tick_params(axis="y", length=0)
    axes[0].set_yticks(ypos)
    axes[0].set_yticklabels([(f"{r['measure']} · {r['group']}" if r["group"] != "robustness (revisions)"
                              else f"revisions · {r['measure']}") for r in rowsA], fontsize=6.5)
    for ax, lbl in zip(axes, ["|ρ| < 0.33 not detectable (80 % power, n = 71)",
                              "same band as A, for comparison"]):
        ax.text(-0.32, nrow + 0.5, lbl, fontsize=6, ha="left", va="top", color=OI["grey"])
        ax.text(-0.01, -1.3, "← load hypothesis requires ρ < 0", fontsize=6, ha="right", va="bottom")
    axes[1].text(0.0, len(A["rows"]) - 1 - len(A["robustness"]) + 0.2,
                 f"all 15 CIs exclude 0 (p ≤ {B['p_max']:.1e});\nrobustness variants only computed for A",
                 fontsize=6.5, ha="left", va="top", color=OI["grey"])
    fig.text(0.5, -0.01, "15 tests per panel ≈ 2.2 effectively independent tests (the five load measures correlate at ρ = 0.97)",
             fontsize=6, ha="center", va="top", color=OI["grey"])
    handles = [Line2D([], [], marker="o", mfc="white", color=OI["black"], ls="", label="95 % CI contains 0"),
               Line2D([], [], marker="s", color=OI["black"], ls="", label="95 % CI excludes 0")]
    axes[1].legend(handles=handles, loc="lower right", fontsize=6.5)
    save(fig, "fig4_load_null_forest")


# --------------------------------------------------------------------------
def fig5():
    d = load("fig5_round_staircase")
    rows = d["rows"]
    cls = d["classes"]
    cstyle = {
        "observation": dict(color=OI["blue"], hatch=""),
        "request": dict(color=OI["orange"], hatch="///"),
        "prediction": dict(color=OI["sky"], hatch="..."),
        "negation": dict(color=OI["verm"], hatch="\\\\\\"),
        "unclassified": dict(color="#D9D9D9", hatch=""),
    }
    fig, ax = plt.subplots(figsize=(SINGLE, 2.9))
    y = np.arange(len(rows))[::-1]
    left = np.zeros(len(rows))
    plt.rcParams["hatch.linewidth"] = 0.4
    for c in cls:
        vals = np.array([r[c] for r in rows], dtype=float)
        ax.barh(y, vals, left=left, height=0.7, color=cstyle[c]["color"], hatch=cstyle[c]["hatch"],
                edgecolor="white", lw=0.3, label=c)
        left += vals
    ax.set_yticks(y)
    ax.set_yticklabels([f"{r['round']}\n{r['n_labels']} names" for r in rows], fontsize=6.5)
    ax.set_xlabel(d["x"]["name"])
    ax.set_xlim(0, 6200)
    # R6 / R7 annotations
    r6 = next(r for r in rows if r["round"] == "R6")
    r7 = next(r for r in rows if r["round"] == "R7")
    y6 = y[[r["round"] for r in rows].index("R6")]
    y7 = y[[r["round"] for r in rows].index("R7")]
    ax.text(2400, y6, f"observation = {r6['observation']} arrival after manual review\n(table value {r6['observation_table']}; "
            f"{d['review']['r6_candidates']} candidates reviewed)", fontsize=6.5, ha="left", va="center")
    ax.text(700, y7, f"observation = {r7['observation']} arrival (reviewed); {sum(r7[c] for c in cls)} sentences",
            fontsize=6.5, ha="left", va="center")
    handles = [Patch(facecolor=cstyle[c]["color"], hatch=cstyle[c]["hatch"], edgecolor="white", label=c) for c in cls]
    ax.legend(handles=handles, loc="upper right", ncol=1, fontsize=6.5, handlelength=1.4, borderaxespad=0.3)
    ax.text(0.98, 0.03, "R8+ = R8–R10 combined", transform=ax.transAxes, fontsize=6, ha="right", va="bottom",
            color=OI["grey"])
    save(fig, "fig5_round_staircase")


# --------------------------------------------------------------------------
def fig6():
    d = load("fig6_lead_ecdf")
    x = np.array([p[0] for p in d["points"]])
    yv = np.array([p[1] for p in d["points"]])
    fig, ax = plt.subplots(figsize=(SINGLE, 2.5))
    ax.step(np.concatenate([[x[0]], x]), np.concatenate([[0], yv]), where="post", color=OI["blue"], lw=1.0)
    ax.set_xscale("log")
    ax.set_xlim(0.01, 24)
    ax.set_ylim(0, 1.02)
    ax.set_xlabel(d["x"]["name"])
    ax.set_ylabel("share of pairs with lead ≤ x")
    ax.set_xticks([0.01, 0.1, 1, 10])
    ax.set_xticklabels(["0.01", "0.1", "1", "10"])
    med = d["median_h"]
    ax.axhline(0.5, color=OI["grey"], lw=0.5, ls=":")
    ax.plot([med, med], [0, 0.5], color=OI["grey"], lw=0.5, ls=":")
    ax.text(med * 1.1, 0.47, f"median {med:.1f} h", fontsize=6.5, ha="left", va="top")
    for m in d["marks"]:
        ax.axvline(m["x"], color=OI["verm"] if "clock" in m["text"] else OI["black"], lw=0.7,
                   ls="--" if "clock" in m["text"] else "-.")
    m0 = d["marks"][0]
    ax.text(m0["x"] * 0.93, 0.98, m0["text"].replace(": ", ":\n"), fontsize=6.5, ha="right", va="top", color=OI["verm"])
    ax.text(1.06, 0.74, f"{d['share_ge_1h'] * 100:.1f} % of pairs\nhad ≥ 1 h", fontsize=6.5, ha="left", va="bottom")
    ax.text(0.02, 0.66, f"n = {d['n_rows']} reporter–item pairs\n({d['n_distinct_names']} distinct names),\nleads ≤ 24 h",
            transform=ax.transAxes, fontsize=6.5, ha="left", va="top")
    save(fig, "fig6_lead_ecdf")


# --------------------------------------------------------------------------
def fig7():
    d = load("fig7_population_estimate")
    rows = d["rows"]
    fig, ax = plt.subplots(figsize=(SINGLE, 2.4))
    y = np.arange(len(rows))[::-1]
    for yi, r in zip(y, rows):
        if r["ci_lo"] is None:
            ax.plot(r["n_hat"], yi, marker="D", ms=4.5, color=OI["orange"], ls="")
            ax.text(r["n_hat"] + 60, yi, f"{r['n_hat']:,} (no interval)", fontsize=6.5, va="center")
        else:
            col = OI["blue"] if r["canonical"] else OI["grey"]
            ax.errorbar(r["n_hat"], yi, xerr=[[r["n_hat"] - r["ci_lo"]], [r["ci_hi"] - r["n_hat"]]],
                        fmt="o", ms=4.5 if r["canonical"] else 3.5, color=col, mfc=col if r["canonical"] else "white",
                        capsize=2, lw=0.9, elinewidth=0.9)
            ax.text(r["ci_hi"] + 60, yi, f"{r['n_hat']:,} [{r['ci_lo']:,}–{r['ci_hi']:,}]", fontsize=6.5, va="center")
    ax.set_yticks(y)
    ax.set_yticklabels([r["label"] for r in rows], fontsize=6.5)
    ax.set_xlim(*d["x"]["range"])
    ax.set_xlabel(d["x"]["name"])
    for m in d["marks"]:
        ax.axvline(m["x"], color=OI["black"], lw=0.6, ls="-.")
        ax.text(m["x"], len(rows) + 0.35, " " + m["text"].replace(" (", "\n("), fontsize=6, ha="left" if m["x"] < 1000 else "right",
                va="top", clip_on=False)
    ax.set_ylim(-0.6, len(rows) + 0.4)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    handles = [Line2D([], [], marker="o", color=OI["blue"], ls="", label="canonical estimate, 95 % interval"),
               Line2D([], [], marker="o", color=OI["grey"], mfc="white", ls="", label="other estimators"),
               Line2D([], [], marker="D", color=OI["orange"], ls="", label="ratio, no interval")]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.28), ncol=3, fontsize=6,
              handletextpad=0.3, columnspacing=1.0)
    save(fig, "fig7_population_estimate")


# --------------------------------------------------------------------------
def mmss(x, pos=None):
    x = int(round(x))
    return f"{x // 60:d}:{x % 60:02d}"


def fig8():
    d = load("fig8_cvd_intervals")
    classes = [("fast_17s", "5400", "A  fast class (17 s answers)"),
               ("medium_22s", "6300", "B  medium class (22 s answers)")]
    # one row per cohort × class; the audit's self-inferred death (if any) is a marker on the same row
    rows = {}
    for iv in d["intervals"]:
        key = (iv["class"], iv["cohort"])
        r = rows.setdefault(key, {"cohort": iv["cohort"], "class": iv["class"]})
        if iv["kind"] == "audit_inferred_death":
            r["death"] = iv["hi"]
        else:
            r.update(lo=iv["lo"], hi=iv["hi"], kind=iv["kind"])
    fig, axes = plt.subplots(1, 2, figsize=(DOUBLE, 3.4), gridspec_kw=dict(wspace=0.32))
    for ax, (cls, ck, title) in zip(axes, classes):
        rs = sorted((r for r in rows.values() if r["class"] == cls), key=lambda r: (r["lo"], r["cohort"]))
        due = d["r6_due"][ck]
        lo_min, lo_max = min(r["lo"] for r in rs), max(r["lo"] for r in rs)
        y = np.arange(len(rs))[::-1]
        ax.axvspan(lo_max, due, color=OI["grey"], alpha=0.15, lw=0, zorder=0)
        ax.axvline(due, color=OI["black"], lw=0.6, ls="-.", zorder=1)
        for yi, r in zip(y, rs):
            server = r["kind"] == "server"
            col = OI["black"] if server else OI["grey"]
            ax.plot([r["lo"], r["hi"]], [yi, yi], color=col, lw=0.9, solid_capstyle="butt", zorder=2)
            ax.plot(r["lo"], yi, marker="o" if server else "D", ms=4 if server else 4.2, color=col,
                    mfc=col if server else "white", mew=0.9, ls="", zorder=3)
            ax.plot(r["hi"], yi, marker="|", ms=5, color=col, mew=0.9, ls="", zorder=3)
            if "death" in r:
                ax.plot(r["death"], yi, marker="x", ms=4.5, color=OI["verm"], mew=0.9, ls="", zorder=4)
        ax.set_yticks(y)
        ax.set_yticklabels([r["cohort"] for r in rs], fontsize=6.5)
        ax.set_ylim(-1.7, len(rs) + 0.9)  # head/foot room for the annotations
        ax.tick_params(axis="y", length=0)
        ax.spines["left"].set_visible(False)
        pad = 12
        ax.set_xlim(lo_min - pad - 20, due + pad + 8)
        ax.set_xlabel("internal clock, s after R1")
        top = ax.secondary_xaxis("top", functions=(lambda v: v, lambda v: v))
        top.xaxis.set_major_formatter(plt.FuncFormatter(mmss))
        top.set_xlabel("internal clock, mm:ss after R1", fontsize=7)
        top.tick_params(labelsize=6.5)
        top.spines["top"].set_visible(True)
        n_srv = sum(r["kind"] == "server" for r in rs)
        n_aud = len(rs) - n_srv
        ax.set_title(f"{title}, n = {len(rs)} ({n_srv} server, {n_aud} audit)", loc="left", fontsize=8)
        ax.plot([lo_min, lo_max], [len(rs) - 0.2] * 2, color=OI["black"], lw=0.5)
        ax.text(lo_min + (lo_max - lo_min) / 2, len(rs) - 0.1,
                f"last activity {lo_min:.0f}–{lo_max:.0f} s (window {lo_max - lo_min:.0f} s)",
                fontsize=6.5, ha="center", va="bottom", color=OI["black"])
        ax.text(due - 1, -0.85, f"death interval [{lo_max:.0f}, {due:.0f}] = {due - lo_max:.0f} s",
                fontsize=6.5, ha="right", va="top", color=OI["grey"])
        ax.text(due, len(rs) + 0.85, f" R6 due {due:.0f} s", fontsize=6.5, ha="right", va="top")
    handles = [Line2D([], [], marker="o", color=OI["black"], ls="-", lw=0.9, label="server-evidenced last alive → R6 due"),
               Line2D([], [], marker="D", color=OI["grey"], mfc="white", ls="-", lw=0.9, label="self-reported (audit) last alive → R6 due"),
               Line2D([], [], marker="x", color=OI["verm"], ls="", label="death inferred by the audit itself")]
    axes[0].legend(handles=handles, loc="upper center", bbox_to_anchor=(1.16, -0.2), ncol=3, fontsize=6.5,
                   handletextpad=0.4, columnspacing=1.2)
    save(fig, "fig8_cvd_intervals")


# --------------------------------------------------------------------------
def fig9():
    d = load("fig9_progress_forest")
    rows = d["rows"]
    x0, x1 = d["x"]["range"]
    fig, ax = plt.subplots(figsize=(DOUBLE, 3.3))
    y = np.arange(len(rows))[::-1]
    off = {"base": 0.18, "ge5": -0.18}
    sty = {"base": dict(color=OI["blue"], marker="o"), "ge5": dict(color=OI["verm"], marker="s")}
    ax.axvline(0, color=OI["black"], lw=0.6)
    for yi, r in zip(y, rows):
        for sk in ("base", "ge5"):
            e = r[sk]
            yy = yi + off[sk]
            col, mk = sty[sk]["color"], sty[sk]["marker"]
            if e["beta"] is None:
                continue
            lo, hi = max(e["ci_lo"], x0), min(e["ci_hi"], x1)
            ax.plot([lo, hi], [yy, yy], color=col, lw=0.9, solid_capstyle="butt", zorder=2)
            for xc, orig, arrow in ((lo, e["ci_lo"], "<"), (hi, e["ci_hi"], ">")):
                if orig != xc:  # clipped: arrowhead instead of cap
                    ax.plot(xc, yy, marker=arrow, ms=3.5, color=col, mfc=col, mew=0, ls="", clip_on=False, zorder=3)
                else:
                    ax.plot([xc, xc], [yy - 0.14, yy + 0.14], color=col, lw=0.9)
            ax.plot(e["beta"], yy, marker=mk, ms=4, color=col, mfc="white" if r["dagger"] else col, mew=0.9,
                    ls="", zorder=4)
        b = r["base"]
        if b["beta"] is None:
            ax.text(x0 + 0.02, yi, "not estimable: cluster SE degenerate (treated cohorts in 1 family)",
                    fontsize=6, va="center", ha="left", color=OI["grey"], style="italic")
            txt = "—  (table: ---)"
        else:
            txt = f"{b['beta']:+.2f} [{b['ci_lo']:+.2f}, {b['ci_hi']:+.2f}]  q = {b['q_bh']:.2f}"
        ax.text(1.02, yi, txt, fontsize=6, va="center", ha="left", transform=ax.get_yaxis_transform(), clip_on=False)
        if yi > 0:
            ax.axhline(yi - 0.5, color=OI["grey"], lw=0.3, ls=":")
    ax.set_yticks(y)
    ax.set_yticklabels([r["label"] + (" †" if r["dagger"] else "") for r in rows], fontsize=6.5)
    ax.set_ylim(-0.6, len(rows) - 0.4)
    ax.set_xlim(x0, x1)
    ax.set_xlabel(d["x"]["name"])
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.text(1.02, len(rows) - 0.35, "base: β [95 % CI], BH q", fontsize=6, ha="left", va="bottom",
            transform=ax.get_yaxis_transform(), clip_on=False, color=OI["grey"])
    subs = {s["key"]: s["label"] for s in d["subsets"]}
    handles = [Line2D([], [], marker="o", color=OI["blue"], ls="-", lw=0.9, label=subs["base"]),
               Line2D([], [], marker="s", color=OI["verm"], ls="-", lw=0.9, label=subs["ge5"]),
               Line2D([], [], marker="o", color=OI["black"], mfc="white", ls="",
                      label="† hollow: < 5 treated families"),
               Line2D([], [], marker=">", color=OI["black"], mfc=OI["black"], mew=0, ls="", label="CI clipped at axis")]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=4, fontsize=6.5,
              handletextpad=0.4, columnspacing=1.2)
    save(fig, "fig9_progress_forest")


# --------------------------------------------------------------------------
def fig10():
    """Exposure and adoption in newcomers' first contributions (66_exposition.py part B)."""
    d = load("fig10_exposure_adoption")
    style = [("exp_ad", OI["blue"], "-", "o", "visible on the page, adopted"),
             ("exp_noad", OI["grey"], ":", "v", "visible on the page, not adopted"),
             ("noexp_ad", OI["verm"], "--", "s", "adopted with no source on the page")]
    fig, axes = plt.subplots(1, 3, figsize=(DOUBLE, 2.35), sharex=True, sharey=True)
    t_start = datetime(2026, 6, 16, 9, 27, 10, tzinfo=timezone.utc)
    for ax, srs in zip(axes, d["series"]):
        pts = [(ts(t), a, b, c, n) for t, a, b, c, n in srs["points"] if a is not None]
        x = [t + (ts(srs["points"][0][0]) - ts(srs["points"][0][0])) for t, *_ in pts]
        x = [t.replace(tzinfo=timezone.utc) + (datetime(2026, 1, 1, 3, tzinfo=timezone.utc)
                                               - datetime(2026, 1, 1, tzinfo=timezone.utc)) for t in x]
        for j, (key, col, ls, mk, _) in enumerate(style):
            y = [p[1 + j] for p in pts]
            ax.plot(x, y, color=col, ls=ls, lw=0.9, zorder=2)
            ax.scatter(x, y, s=[max(4, 0.35 * np.sqrt(p[4]) * 4) for p in pts], marker=mk,
                       color=col, zorder=3, linewidths=0)
        ax.axvline(t_start, color=OI["black"], lw=0.6, ls="-.")
        g = srs["gesamt"]
        ax.set_title(srs["label"], fontsize=7.5, loc="left")
        ax.text(0.03, 0.97, f"{int(g['noexp_ad'])} of {int(g['exp_ad'] + g['noexp_ad'])} adopters\n"
                            f"({g['anteil_ohne_sichtbare_quelle']:.0f}\u2009%) with no page source",
                transform=ax.transAxes, fontsize=6, va="top", ha="left", color=OI["verm"])
        ax.set_ylim(-3, 78)
        ax.set_xlim(datetime(2026, 6, 16, 4, tzinfo=timezone.utc), datetime(2026, 6, 22, 2, tzinfo=timezone.utc))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%-d %b", tz=timezone.utc))
        ax.set_xlabel(d["x"]["name"], fontsize=7)
    axes[0].set_ylabel("share of newcomers' first\ncontributions in the window, %")
    handles = [Line2D([], [], color=c, ls=l, marker=m, ms=3.5, lw=0.9, label=lab)
               for _, c, l, m, lab in style]
    axes[0].legend(handles=handles, loc="upper center", bbox_to_anchor=(1.6, -0.28), ncol=3, fontsize=6.5,
                   handlelength=2.6, columnspacing=1.4)
    save(fig, "fig10_exposure_adoption")


if __name__ == "__main__":
    for fn in (fig1, fig2, fig3, fig4, fig5, fig6, fig7, fig8, fig9, fig10):
        fn()
