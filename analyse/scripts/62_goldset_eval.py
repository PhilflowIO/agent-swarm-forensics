#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
62_goldset_eval.py
==================
Scores the two independent raters of the gold-set sample against each other
(Cohen's kappa, Krippendorff's alpha, raw agreement), builds the conflict list
for human adjudication, derives the gold labels, and measures the paper's
regex classifiers against them (precision / recall / F1 with Wilson 95 % CI,
raw and reweighted to the regex-positive populations).

Inputs  : artefakte/paper_goldset_sample.csv        (61_goldset_sample.py; regex labels + strata)
          artefakte/paper_goldset_rater1.jsonl      (CODEBOOK_goldset.md §8)
          artefakte/paper_goldset_rater2.jsonl      (CODEBOOK_goldset.md §8)
          artefakte/paper_goldset_konflikte.csv     (optional, earlier run with human `adjudicated_*` fills)
Outputs : artefakte/paper_goldset_agreement.csv
          artefakte/paper_goldset_konflikte.csv
          artefakte/paper_goldset_gold.csv
          artefakte/paper_robust_regex_guete.csv
          paper/tables/app_goldset.tex             (only with real rater data)
          artefakte/BERICHT_robust_goldset.md      (numbers block between AUTO markers, real data only)
          artefakte/_paper_goldset_eval.log

Self-test: if either rater file is missing, two synthetic rater files are
generated from the regex labels plus noise in a scratch directory, the whole
pipeline runs against them, all outputs go to that scratch directory, and the
script exits with code 2 and a clear message.  Nothing synthetic touches
artefakte/ or paper/.

Run:  .venv/bin/python scripts/62_goldset_eval.py
      .venv/bin/python scripts/62_goldset_eval.py --rater1 X --rater2 Y   (explicit files)
"""
from __future__ import annotations
import os, re, sys, json, math, argparse, tempfile, collections, datetime
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)                 # analyse/
ART = os.path.join(BASE, "artefakte")
PAPER_TABLES = os.path.join(os.path.dirname(BASE), "paper", "tables")
OUT = lambda n: os.path.join(ART, n)
LOG = open(OUT("_paper_goldset_eval.log"), "w", encoding="utf-8")


def L(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LOG.write(s + "\n")


# =========================================================== 0. Constants: codebook schema (§8) and scoring map (§9)
# CODEBOOK_goldset.md:324-336  field constraints
RATER_FIELDS = {
    "arrival_round": {None, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10},
    "speech_act": {"request", "prediction", "negation", "observation", "none"},
    "future_answer_receipt": {True, False},
    "clock_statement": {"none", "pair", "bare_internal", "past_event"},
    "coordination_topic": {True, False},
    "register": {"environment", "task", "both", "neither"},
}
# the six raw fields the human adjudicates (one column each in paper_goldset_konflikte.csv)
ADJ_FIELDS = list(RATER_FIELDS)

# CODEBOOK_goldset.md:344-352  scoring map.  Left: name of the mapped target and how it is
# derived from the gold (rater-agreed / adjudicated) raw fields.  Right: regex column(s) in
# paper_goldset_sample.csv and the population over which the classifier is scored.
#   arrival      := arrival_round is not null                     (§9 row 1)  vs regex_strong_obs (strong)
#                                                                              and regex_speech_act=="observation" (weak)
#                                                                  population: regex_has_round
#   speech_act   := speech_act (4 classes + none)                  (§9 row 2)  vs regex_speech_act, population regex_has_round
#                   regex value "unclassified" = none of the four classes
#   future_answer:= future_answer_receipt                         (§9 row 3)  vs regex_future_answer (exact) and
#                                                                              regex_future_answer_candidate; population all
#   clock        := clock_statement                               (§9 row 4)  vs regex_clock_route  A=pair, B=bare_internal,
#                                                                              C=past_event; population all
#   coord_topic  := coordination_topic                            (§9 row 5)  vs regex_coord_topic_sentence (sentence rule),
#                                                                              regex_coord_topic_delta (paper's delta rule); all
#   env          := register in {environment, both}               (§9 row 6)  vs regex_env_sentence, regex_env_delta,
#   task         := register in {task, both}                                   regex_task_sentence; paper priority ENV>TASK in
#                                                                              regex_primary_delta ("ENV_META"); population all
#   format       := strata format_state_filled / format_r_confirmed (§9 row 7, §7:303-306) compared on arrival + speech_act
CLOCK_ROUTE_MAP = {"A": "pair", "B": "bare_internal", "C": "past_event", "none": "none"}   # CODEBOOK §9:349

# Regex-positive population per stratum: printed by 61_goldset_sample.py ("drawn / regex-positive population").
# Source: re-run of analyse/scripts/61_goldset_sample.py (seed 20260909) on 2026-09-09 whose
# paper_goldset_sample.csv was byte-identical to the artefact; the mask counts (|mask|) are the
# values the script prints.  "frame" = |mask minus sentences already drawn by earlier strata|, i.e.
# the actual sampling frame (61:257 `pool`), used for the weights.  If artefakte/_paper_goldset_sample.log
# exists (a captured stdout of 61), its counts override this table.
POP_TABLE = {  # stratum: (drawn, mask_population, frame_population)
    "future_answer_ack":        (9,   9,    9),
    "future_answer_candidate":  (7,   7,    7),
    "format_state_filled":      (17,  17,   17),
    "format_state_placeholder": (10,  171,  171),
    "clock_B_bare_now":         (20,  110,  109),
    "clock_A_pair":             (20,  347,  347),
    "clock_C_past_event":       (20,  606,  606),
    "strong_obs":               (30,  1237, 1225),
    "speech_negation":          (25,  206,  205),
    "speech_observation_weak":  (25,  344,  334),
    "env_positive":             (20,  6581, 6525),
    "coord_topic":              (20,  8638, 8545),
    "speech_request":           (25,  2097, 2087),
    "speech_prediction":        (25,  3102, 3089),
    "format_r_confirmed":       (25,  483,  472),
    "negative_random":          (102, 3059, 3059),
}
# Sampled universe (union of all strata masks) = 19,502 of 309,235 corpus sentences (61 re-run, `[frame]` line);
# reweighted estimates refer to that universe, not to sentences that carry neither a round marker nor a time.
UNIVERSE_SAMPLED, UNIVERSE_ALL = 19502, 309235
FRAME_OVERRIDE: dict[str, int] = {}   # optional manual override of the frame sizes (key -> frame size)


def load_population_from_log(path: str) -> dict[str, int] | None:
    """Parse `  <stratum>  <drawn> / <population>` lines from a captured 61 stdout."""
    if not os.path.exists(path):
        return None
    pat = re.compile(r"^\s*([a-z_]+)\s+(\d+)\s*/\s*(\d+)\s*$")
    out = {}
    for line in open(path, encoding="utf-8"):
        m = pat.match(line)
        if m:
            out[m.group(1)] = int(m.group(3))
    return out or None


# =========================================================== 1. Agreement statistics (own implementations)
def cohen_kappa(a: list, b: list) -> float:
    """Cohen's kappa for two raters over nominal categories (missing values excluded beforehand)."""
    n = len(a)
    if n == 0:
        return float("nan")
    cats = sorted(set(a) | set(b), key=str)
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    ca = collections.Counter(a); cb = collections.Counter(b)
    pe = sum(ca[c] * cb[c] for c in cats) / (n * n)
    if pe == 1.0:
        return 1.0 if po == 1.0 else 0.0
    return (po - pe) / (1 - pe)


def krippendorff_alpha_nominal(values_by_unit: list[list]) -> float:
    """Krippendorff's alpha, nominal metric, any number of raters, missing values allowed.
    values_by_unit: one list per unit with the non-missing codes of that unit.
    Coincidence-matrix form (Krippendorff 2011): units with < 2 values are dropped;
    D_o = sum_{c!=k} o_ck ; D_e = sum_{c!=k} n_c n_k / (n-1) ; alpha = 1 - D_o/D_e."""
    units = [u for u in values_by_unit if len(u) >= 2]
    if not units:
        return float("nan")
    o = collections.defaultdict(float)
    n_c = collections.defaultdict(float)
    for u in units:
        m = len(u)
        for i in range(m):
            for j in range(m):
                if i != j:
                    o[(u[i], u[j])] += 1.0 / (m - 1)
    for (c, k), v in o.items():
        n_c[c] += v
    n = sum(n_c.values())
    if n <= 1:
        return float("nan")
    d_o = sum(v for (c, k), v in o.items() if c != k)
    d_e = sum(n_c[c] * n_c[k] for c in n_c for k in n_c if c != k) / (n - 1)
    if d_e == 0:
        return 1.0 if d_o == 0 else 0.0
    return 1.0 - d_o / d_e


def wilson(k: float, n: float, z: float = 1.959964) -> tuple[float, float, float]:
    """Wilson score interval for a proportion k/n (k, n may be fractional: weighted counts with
    Kish effective n). Returns (p, lo, hi); NaN triple if n == 0."""
    if n <= 0:
        return (float("nan"),) * 3
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return p, max(0.0, centre - half), min(1.0, centre + half)


def prf(gold: np.ndarray, pred: np.ndarray, w: np.ndarray | None = None) -> dict:
    """Precision / recall / F1 of binary pred against binary gold with Wilson 95 % CIs.
    With weights: counts are weighted sums and the CI uses the Kish effective sample size
    n_eff = (sum w)^2 / sum w^2 of the sentences entering the respective denominator."""
    gold = gold.astype(bool); pred = pred.astype(bool)
    if w is None:
        w = np.ones(len(gold))
    tp_m = gold & pred; fp_m = ~gold & pred; fn_m = gold & ~pred
    tp, fp, fn = w[tp_m].sum(), w[fp_m].sum(), w[fn_m].sum()

    def ci(num_mask, den_mask):
        wd = w[den_mask]
        if wd.sum() == 0:
            return (float("nan"),) * 3
        p = w[num_mask].sum() / wd.sum()
        n_eff = wd.sum() ** 2 / (wd ** 2).sum()
        return wilson(p * n_eff, n_eff)

    P, plo, phi = ci(tp_m, tp_m | fp_m)
    R, rlo, rhi = ci(tp_m, tp_m | fn_m)
    F = 2 * P * R / (P + R) if (P + R) > 0 and not (math.isnan(P) or math.isnan(R)) else float("nan")
    return dict(n=int(len(gold)), n_gold_pos=int(gold.sum()), n_pred_pos=int(pred.sum()),
                tp=float(tp), fp=float(fp), fn=float(fn),
                precision=P, p_lo=plo, p_hi=phi, recall=R, r_lo=rlo, r_hi=rhi, f1=F)


# =========================================================== 2. Rater file loading (robust)
def load_rater(path: str, valid_ids: set[str], tag: str) -> tuple[pd.DataFrame, dict]:
    """Read a §8 JSON-Lines file. Invalid JSON, unknown ids, duplicate ids and out-of-range field
    values are reported (not fatal); invalid field values become NA for that field."""
    rep = dict(file=path, lines=0, bad_json=0, unknown_id=0, duplicate_id=0, missing_id=0, bad_field=collections.Counter())
    rows = {}
    for ln, raw in enumerate(open(path, encoding="utf-8"), 1):
        raw = raw.strip()
        if not raw:
            continue
        rep["lines"] += 1
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            rep["bad_json"] += 1
            L(f"  [{tag}] line {ln}: invalid JSON, skipped")
            continue
        sid = str(obj.get("id", "")).strip()
        if sid not in valid_ids:
            rep["unknown_id"] += 1
            L(f"  [{tag}] line {ln}: unknown id {sid!r}, skipped")
            continue
        if sid in rows:
            rep["duplicate_id"] += 1
            L(f"  [{tag}] line {ln}: duplicate id {sid}, last occurrence wins")
        rec = {"id": sid}
        for f, allowed in RATER_FIELDS.items():
            v = obj.get(f, "__missing__")
            if v == "__missing__":
                rep["bad_field"][f] += 1
                L(f"  [{tag}] {sid}: field {f} missing -> NA")
                v = pd.NA
            elif f == "arrival_round":
                if v is None:
                    v = "null"
                elif isinstance(v, bool) or not isinstance(v, (int, float)) or int(v) != v or int(v) not in allowed:
                    rep["bad_field"][f] += 1
                    L(f"  [{tag}] {sid}: arrival_round={v!r} invalid -> NA")
                    v = pd.NA
                else:
                    v = str(int(v))
            elif isinstance(v, bool) or (isinstance(v, (str, int, float)) and v in allowed):
                if v not in allowed:
                    rep["bad_field"][f] += 1
                    L(f"  [{tag}] {sid}: {f}={v!r} invalid -> NA")
                    v = pd.NA
                else:
                    v = str(v) if not isinstance(v, bool) else ("true" if v else "false")
            else:
                rep["bad_field"][f] += 1
                L(f"  [{tag}] {sid}: {f}={v!r} invalid -> NA")
                v = pd.NA
            rec[f] = v
        rec["unclear"] = bool(obj.get("unclear", False)) if isinstance(obj.get("unclear", False), bool) else False
        rec["note"] = str(obj.get("note", "") or "")
        rows[sid] = rec
    rep["missing_id"] = len(valid_ids - set(rows))
    df = pd.DataFrame(list(rows.values())) if rows else pd.DataFrame(columns=["id"] + ADJ_FIELDS + ["unclear", "note"])
    df = df.set_index("id").reindex(sorted(valid_ids))
    df["unclear"] = df["unclear"].fillna(False).astype(bool); df["note"] = df["note"].fillna("")
    L(f"[{tag}] {os.path.basename(path)}: {rep['lines']} lines, bad_json={rep['bad_json']}, unknown_id={rep['unknown_id']}, "
      f"duplicate_id={rep['duplicate_id']}, missing ids={rep['missing_id']}, invalid fields={dict(rep['bad_field'])}")
    return df, rep


# =========================================================== 3. Synthetic raters (self-test only)
def make_synthetic_raters(S: pd.DataFrame, outdir: str, seed: int = 7) -> tuple[str, str]:
    """Two fake raters derived from the regex labels with independent noise so that kappa < 1
    and conflicts exist. Also injects one invalid JSON line, one unknown id, one duplicate and
    one out-of-range value into rater 2 to exercise the loader."""
    rng = np.random.default_rng(seed)

    def truth_row(r):
        sa = r.regex_speech_act if r.regex_speech_act in RATER_FIELDS["speech_act"] else "none"
        arr = None
        if sa == "observation" and r.regex_round_marks:
            nums = [int(re.sub(r"\D", "", m) or 0) for m in str(r.regex_round_marks).split(";") if m]
            arr = max(nums) if nums else None
        reg = "both" if (r.regex_env_sentence and r.regex_task_sentence) else "environment" if r.regex_env_sentence \
            else "task" if r.regex_task_sentence else "neither"
        return dict(arrival_round=arr, speech_act=sa, future_answer_receipt=bool(r.regex_future_answer),
                    clock_statement=CLOCK_ROUTE_MAP.get(str(r.regex_clock_route).split("+")[0], "none"),
                    coordination_topic=bool(r.regex_coord_topic_sentence), register=reg)

    def noisy(t, p):
        t = dict(t)
        if rng.random() < p:
            t["speech_act"] = rng.choice(sorted(RATER_FIELDS["speech_act"]))
        if rng.random() < p:
            t["arrival_round"] = None if t["arrival_round"] is not None else int(rng.integers(1, 6))
        if rng.random() < p:
            t["future_answer_receipt"] = not t["future_answer_receipt"]
        if rng.random() < p:
            t["clock_statement"] = rng.choice(sorted(RATER_FIELDS["clock_statement"]))
        if rng.random() < p:
            t["coordination_topic"] = not t["coordination_topic"]
        if rng.random() < p:
            t["register"] = rng.choice(sorted(RATER_FIELDS["register"]))
        return t

    paths = []
    for k, p in ((1, 0.08), (2, 0.12)):
        path = os.path.join(outdir, f"synthetic_rater{k}.jsonl")
        with open(path, "w", encoding="utf-8") as fh:
            for r in S.itertuples():
                t = noisy(truth_row(r), p)
                t["arrival_round"] = None if t["arrival_round"] is None else int(t["arrival_round"])
                for kk in ("future_answer_receipt", "coordination_topic"):
                    t[kk] = bool(t[kk])
                for kk in ("speech_act", "clock_statement", "register"):
                    t[kk] = str(t[kk])
                obj = {"id": r.id, **t, "unclear": bool(rng.random() < 0.05), "note": "synthetic"}
                fh.write(json.dumps(obj) + "\n")
            if k == 2:
                fh.write("{this is not json\n")
                fh.write(json.dumps({"id": "G999", "speech_act": "none"}) + "\n")
                fh.write(json.dumps({"id": S.id.iloc[0], "arrival_round": 3, "speech_act": "observation",
                                     "future_answer_receipt": False, "clock_statement": "none",
                                     "coordination_topic": True, "register": "neither"}) + "\n")   # duplicate
                fh.write(json.dumps({"id": S.id.iloc[1], "arrival_round": 42, "speech_act": "shout",
                                     "future_answer_receipt": "yes", "clock_statement": "none",
                                     "coordination_topic": True, "register": "neither"}) + "\n")   # invalid values (dup, last wins)
        paths.append(path)
    return paths[0], paths[1]


# =========================================================== 4. Derived targets
def derive_targets(df: pd.DataFrame) -> pd.DataFrame:
    """Mapped targets from the six raw fields (NA-preserving). Names as in CODEBOOK §9 map above."""
    out = pd.DataFrame(index=df.index)
    ar = df["arrival_round"]
    out["arrival"] = ar.map(lambda v: pd.NA if pd.isna(v) else ("false" if v == "null" else "true"))
    out["arrival_round"] = ar
    out["speech_act"] = df["speech_act"]
    out["future_answer"] = df["future_answer_receipt"]
    out["clock"] = df["clock_statement"]
    out["coord_topic"] = df["coordination_topic"]
    out["register"] = df["register"]
    out["env"] = df["register"].map(lambda v: pd.NA if pd.isna(v) else ("true" if v in ("environment", "both") else "false"))
    out["task"] = df["register"].map(lambda v: pd.NA if pd.isna(v) else ("true" if v in ("task", "both") else "false"))
    return out


TARGETS = ["arrival", "arrival_round", "speech_act", "future_answer", "clock", "coord_topic", "register", "env", "task"]


# =========================================================== 5. Main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rater1", default=OUT("paper_goldset_rater1.jsonl"))
    ap.add_argument("--rater2", default=OUT("paper_goldset_rater2.jsonl"))
    ap.add_argument("--force-synthetic", action="store_true")
    ap.add_argument("--outdir", default=None, help="synthetic mode only: reuse this directory (tests adjudication carry-over)")
    args = ap.parse_args()

    L(f"62_goldset_eval.py  {datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')}")
    S = pd.read_csv(OUT("paper_goldset_sample.csv"), dtype={"regex_round_marks": str, "regex_tod": str, "regex_clock_raw": str})
    S["regex_round_marks"] = S["regex_round_marks"].fillna("")
    for c in [c for c in S.columns if c.startswith("regex_") and S[c].dtype == object and set(S[c].dropna().unique()) <= {"True", "False"}]:
        S[c] = S[c] == "True"
    L(f"[sample] {len(S)} sentences, {S.shape[1]} columns, strata: {S.stratum.value_counts().to_dict()}")
    valid_ids = set(S.id)

    synthetic = args.force_synthetic or not (os.path.exists(args.rater1) and os.path.exists(args.rater2))
    if synthetic:
        scratch_root = os.environ.get("CLAUDE_SCRATCHPAD") or tempfile.gettempdir()
        outdir = args.outdir or tempfile.mkdtemp(prefix="goldset_selftest_", dir=scratch_root if os.path.isdir(scratch_root) else None)
        os.makedirs(outdir, exist_ok=True)
        L(f"[mode] SELF-TEST: rater files missing ({args.rater1 if not os.path.exists(args.rater1) else ''} "
          f"{args.rater2 if not os.path.exists(args.rater2) else ''}). Synthetic raters and ALL outputs -> {outdir}")
        r1_path, r2_path = make_synthetic_raters(S, outdir)
        OUTP = lambda n: os.path.join(outdir, n)
        tex_path = None
    else:
        L(f"[mode] REAL rater data: {args.rater1}, {args.rater2}")
        r1_path, r2_path = args.rater1, args.rater2
        OUTP = OUT
        os.makedirs(PAPER_TABLES, exist_ok=True)
        tex_path = os.path.join(PAPER_TABLES, "app_goldset.tex")

    # --- population weights
    pop_log = load_population_from_log(OUT("_paper_goldset_sample.log"))
    pop_src = "artefakte/_paper_goldset_sample.log" if pop_log else "POP_TABLE in 62_goldset_eval.py (captured 61 re-run 2026-09-09)"
    drawn = S.stratum.value_counts().to_dict()
    weights = {}
    for st, n_drawn in drawn.items():
        if pop_log and st in pop_log:
            pop = pop_log[st]
        elif st in POP_TABLE:
            pop = FRAME_OVERRIDE.get(st, POP_TABLE[st][2])
            if POP_TABLE[st][0] != n_drawn:
                L(f"  [weights] WARNING drawn count for {st} in sample ({n_drawn}) != table ({POP_TABLE[st][0]})")
        else:
            L(f"  [weights] WARNING no population for stratum {st}; weight 1"); pop = n_drawn
        weights[st] = pop / n_drawn
    L(f"[weights] source: {pop_src}")
    for st in sorted(weights, key=lambda s: -weights[s]):
        L(f"  {st:26s} drawn={drawn[st]:4d} pop={weights[st] * drawn[st]:8.0f} weight={weights[st]:8.2f}")
    S["w"] = S.stratum.map(weights)

    # --- raters
    R1, rep1 = load_rater(r1_path, valid_ids, "rater1")
    R2, rep2 = load_rater(r2_path, valid_ids, "rater2")
    T1, T2 = derive_targets(R1), derive_targets(R2)

    # --- agreement
    agree_rows = []
    for t in TARGETS:
        a, b = T1[t], T2[t]
        ok = a.notna() & b.notna()
        av, bv = list(a[ok]), list(b[ok])
        n = int(ok.sum())
        raw = float(np.mean([x == y for x, y in zip(av, bv)])) if n else float("nan")
        kap = cohen_kappa(av, bv)
        alpha = krippendorff_alpha_nominal([[x for x in (a.iloc[i], b.iloc[i]) if not pd.isna(x)] for i in range(len(a))])
        cats = sorted(set(av) | set(bv), key=str)
        agree_rows.append(dict(target=t, n_both_coded=n, n_categories=len(cats), raw_agreement=raw, cohen_kappa=kap,
                               krippendorff_alpha=alpha, n_disagree=int(sum(x != y for x, y in zip(av, bv))),
                               r1_positive=int(sum(x == "true" for x in av)) if cats and set(cats) <= {"true", "false"} else "",
                               r2_positive=int(sum(x == "true" for x in bv)) if cats and set(cats) <= {"true", "false"} else ""))
    AG = pd.DataFrame(agree_rows)
    AG.to_csv(OUTP("paper_goldset_agreement.csv"), index=False)
    L("\n=== agreement (n, raw, kappa, alpha) ===")
    for r in AG.itertuples():
        L(f"  {r.target:14s} n={r.n_both_coded:3d} raw={r.raw_agreement:.3f} kappa={r.cohen_kappa:.3f} alpha={r.krippendorff_alpha:.3f} disagree={r.n_disagree}")
    L(f"  unclear flags: rater1={int(R1.unclear.sum())} rater2={int(R2.unclear.sum())} both={int((R1.unclear & R2.unclear).sum())}")

    # --- conflicts + adjudication
    prev_adj = {}
    konf_path = OUTP("paper_goldset_konflikte.csv")
    if os.path.exists(konf_path):
        old = pd.read_csv(konf_path, dtype=str, keep_default_na=False)   # keep the literal "null" (pandas would read it as NaN)
        for r in old.itertuples():
            prev_adj[r.id] = {f: getattr(r, f"adjudicated_{f}", "") for f in ADJ_FIELDS}
        n_prev = sum(1 for v in prev_adj.values() if any(x.strip() for x in v.values()))
        L(f"[adjudication] previous konflikte file found: {len(old)} rows, {n_prev} with at least one adjudicated value")

    def norm_adj(f, v):
        v = str(v).strip()
        if not v:
            return ""
        if f == "arrival_round":
            v = v.lower()
            if v in ("null", "none", "na", "nan"):
                return "null"
            return v if v.isdigit() and 1 <= int(v) <= 10 else "?" + v
        if f in ("future_answer_receipt", "coordination_topic"):
            v = v.lower()
            return v if v in ("true", "false") else "?" + v
        return v if v in RATER_FIELDS[f] else "?" + v

    Sidx = S.set_index("id")
    conf_rows = []; adjud_used = 0; adjud_bad = 0
    gold_raw = pd.DataFrame(index=sorted(valid_ids), columns=ADJ_FIELDS, dtype=object)
    gold_src = pd.Series("", index=gold_raw.index, dtype=object)
    for sid in gold_raw.index:
        a, b = R1.loc[sid], R2.loc[sid]
        both = [f for f in ADJ_FIELDS if pd.notna(a[f]) and pd.notna(b[f])]
        disagree = [f for f in both if a[f] != b[f]]                 # a conflict needs two codings that differ
        incomplete = [f for f in ADJ_FIELDS if f not in both]        # one or both raters have not coded the field yet
        srcs = []
        for f in ADJ_FIELDS:
            if f in incomplete:
                gold_raw.at[sid, f] = pd.NA; srcs.append("incomplete")
            elif f not in disagree:
                gold_raw.at[sid, f] = a[f]; srcs.append("agree")
            else:
                adj = norm_adj(f, prev_adj.get(sid, {}).get(f, ""))
                if adj and not adj.startswith("?"):
                    gold_raw.at[sid, f] = adj; srcs.append("adjudicated"); adjud_used += 1
                else:
                    if adj.startswith("?"):
                        adjud_bad += 1; L(f"  [adjudication] {sid} {f}: value {adj[1:]!r} not in codebook range, ignored")
                    gold_raw.at[sid, f] = pd.NA; srcs.append("open")
        gold_src[sid] = ("incomplete" if incomplete else "agree" if not disagree
                         else "adjudicated" if "open" not in srcs else "open")
        if disagree:
            row = dict(id=sid, stratum=Sidx.at[sid, "stratum"], conflict_fields=";".join(disagree),
                       context_before=Sidx.at[sid, "context_before"], sentence=Sidx.at[sid, "sentence"],
                       context_after=Sidx.at[sid, "context_after"])
            for f in ADJ_FIELDS:
                row[f"r1_{f}"] = "" if pd.isna(a[f]) else a[f]
                row[f"r2_{f}"] = "" if pd.isna(b[f]) else b[f]
            row["r1_unclear"], row["r2_unclear"] = a["unclear"], b["unclear"]
            row["r1_note"], row["r2_note"] = a["note"], b["note"]
            for f in ADJ_FIELDS:
                row[f"adjudicated_{f}"] = prev_adj.get(sid, {}).get(f, "")
            conf_rows.append(row)
    KONF = pd.DataFrame(conf_rows)
    KONF.to_csv(konf_path, index=False)
    n_conf = len(KONF)
    n_conf_open = int(KONF.id.isin(gold_src.index[gold_src.isin(["open", "incomplete"])]).sum()) if n_conf else 0
    n_conf_adj = n_conf - n_conf_open
    n_incomplete = int((gold_src == "incomplete").sum())
    n_both = int(R1[ADJ_FIELDS].notna().all(axis=1).values.__and__(R2[ADJ_FIELDS].notna().all(axis=1).values).sum())
    L(f"\n[conflicts] {n_conf} sentences with >=1 disagreeing field (both raters coded) -> {konf_path}; "
      f"fully adjudicated={n_conf_adj}, still open={n_conf_open}; adjudicated field-values used={adjud_used}, rejected={adjud_bad}; "
      f"sentences not yet coded by both raters={n_incomplete} (coded by both: {n_both})")
    if n_conf:
        L("  conflicts per field: " + ", ".join(f"{f}={int(KONF.conflict_fields.str.contains(f).sum())}" for f in ADJ_FIELDS))

    # --- gold
    G = derive_targets(gold_raw)
    G.insert(0, "gold_source", gold_src)
    G.insert(0, "stratum", Sidx.loc[G.index, "stratum"].values)
    G.index.name = "id"
    G.to_csv(OUTP("paper_goldset_gold.csv"))
    L(f"[gold] per target non-NA: " + ", ".join(f"{t}={int(G[t].notna().sum())}" for t in TARGETS))

    # --- regex quality
    GS = G.join(Sidx, how="left", rsuffix="_s")
    rows = []

    def score(classifier, cls, gold_col, gold_pos, pred_mask, population_mask, note=""):
        m = population_mask & GS[gold_col].notna()
        g = GS.loc[m, gold_col].isin(gold_pos).values
        p = pred_mask[m].values
        w = GS.loc[m, "w"].values.astype(float)
        for weighting, ww in (("raw_sample", None), ("population", w)):
            d = prf(g, p, ww)
            rows.append(dict(classifier=classifier, **{"class": cls}, weighting=weighting, population="regex_has_round" if
                             population_mask.name == "regex_has_round" else "all", note=note, **d))

    ALL = pd.Series(True, index=GS.index, name="all")
    HR = GS["regex_has_round"].astype(bool).rename("regex_has_round")
    # §9 row 1: arrival observation
    score("arrival_obs_strong", "arrival", "arrival", ["true"], GS["regex_strong_obs"].astype(bool), HR, "51:202-203 strong_obs")
    score("arrival_obs_weak", "arrival", "arrival", ["true"], GS["regex_speech_act"] == "observation", HR, "51:166-171 cls==observation")
    n_arr_outside = int((GS["arrival"] == "true")[~HR].sum())
    L(f"[arrival] gold arrivals outside regex_has_round (undetectable by regex): {n_arr_outside}")
    # §9 row 2: speech act 4 classes one-vs-rest
    for cls in ("request", "prediction", "negation", "observation"):
        score("speech_act", cls, "speech_act", [cls], GS["regex_speech_act"] == cls, HR, "51:166-171 classify()")
    # §9 row 3: future-answer receipt
    score("future_answer_exact", "true", "future_answer", ["true"], GS["regex_future_answer"].astype(bool), ALL, "51:318-331 cohort-state rule")
    score("future_answer_candidate", "true", "future_answer", ["true"], GS["regex_future_answer_candidate"].astype(bool), ALL, "ACK vocabulary superset")
    # §9 row 4: clock routes
    route_first = GS["regex_clock_route"].astype(str).map(lambda v: v.split("+")[0])   # priority A > B > C, CODEBOOK:175
    for code, cls in (("A", "pair"), ("B", "bare_internal"), ("C", "past_event")):
        score("clock_route", cls, "clock", [cls], route_first == code, ALL, f"50_uhr route {code}")
    score("clock_route_any", "any_internal", "clock", ["pair", "bare_internal", "past_event"], route_first != "none", ALL, "any route vs any clock statement")
    # §9 row 5: coordination topic
    score("coord_topic_sentence", "true", "coord_topic", ["true"], GS["regex_coord_topic_sentence"].astype(bool), ALL, "55 TAX koord themes, sentence level")
    score("coord_topic_delta", "true", "coord_topic", ["true"], GS["regex_coord_topic_delta"].astype(bool), ALL, "paper rule at delta level")
    # §9 row 6: register
    score("env_sentence", "environment", "env", ["true"], GS["regex_env_sentence"].astype(bool), ALL, "52 ENV block, sentence level")
    score("env_delta", "environment", "env", ["true"], GS["regex_env_delta"].astype(bool), ALL, "52 ENV block, delta level")
    score("primary_delta_env", "environment", "env", ["true"], GS["regex_primary_delta"] == "ENV_META", ALL, "52:111-115 ENV>TASK>COORD")
    score("task_sentence", "task", "task", ["true"], GS["regex_task_sentence"].astype(bool), ALL, "52 TASK block, sentence level")
    Q = pd.DataFrame(rows)
    Q.to_csv(OUTP("paper_robust_regex_guete.csv"), index=False)
    L("\n=== regex quality vs gold (raw sample | population-weighted) ===")
    for (c, k), grp in Q.groupby(["classifier", "class"], sort=False):
        r = grp[grp.weighting == "raw_sample"].iloc[0]; p = grp[grp.weighting == "population"].iloc[0]
        L(f"  {c:24s} {k:14s} n={r.n:3d} gold+={r.n_gold_pos:3d} pred+={r.n_pred_pos:3d} | "
          f"P={r.precision:.2f}[{r.p_lo:.2f},{r.p_hi:.2f}] R={r.recall:.2f}[{r.r_lo:.2f},{r.r_hi:.2f}] F1={r.f1:.2f} | "
          f"P_w={p.precision:.2f}[{p.p_lo:.2f},{p.p_hi:.2f}] R_w={p.recall:.2f}[{p.r_lo:.2f},{p.r_hi:.2f}] F1_w={p.f1:.2f}")

    # --- §7 / §9 row 7: STATE5-XX vs R5 CONFIRMED comparability
    L("\n=== format comparability (CODEBOOK §7:303-306) ===")
    fmt = {}
    for st in ("format_state_filled", "format_r_confirmed", "format_state_placeholder"):
        g = GS[GS.stratum == st]
        arr = g["arrival"].dropna(); sa = g["speech_act"].dropna()
        fmt[st] = dict(n=len(g), arrival_true=int((arr == "true").sum()), arrival_coded=len(arr),
                       obs=int((sa == "observation").sum()), req=int((sa == "request").sum()), neg=int((sa == "negation").sum()),
                       sa_coded=len(sa), round5=int((g["arrival_round"] == "5").sum()))
        f = fmt[st]
        L(f"  {st:26s} n={f['n']:2d} arrival={f['arrival_true']}/{f['arrival_coded']} round5={f['round5']} "
          f"observation={f['obs']}/{f['sa_coded']} request={f['req']} negation={f['neg']}")
    try:
        from scipy.stats import fisher_exact
        a, b = fmt["format_state_filled"], fmt["format_r_confirmed"]
        tab = [[a["arrival_true"], a["arrival_coded"] - a["arrival_true"]], [b["arrival_true"], b["arrival_coded"] - b["arrival_true"]]]
        fisher_p = fisher_exact(tab)[1] if min(a["arrival_coded"], b["arrival_coded"]) > 0 else float("nan")
        L(f"  Fisher exact, arrival share STATE-filled vs R CONFIRMED: p={fisher_p:.3f}  (pool if not different)")
    except Exception as e:   # pragma: no cover
        fisher_p = float("nan"); L(f"  Fisher test skipped: {e}")

    # --- numbers for prose
    n_r1 = int(R1[ADJ_FIELDS].notna().all(axis=1).sum()); n_r2 = int(R2[ADJ_FIELDS].notna().all(axis=1).sum())
    summary = dict(n=len(S), n_strata=int(S.stratum.nunique()), n_r1_complete=n_r1, n_r2_complete=n_r2, n_both=n_both,
                   n_incomplete=n_incomplete, n_conflicts=n_conf, n_adjudicated=n_conf_adj, n_open=n_conf_open,
                   fisher_p=float(fisher_p), mode="synthetic" if synthetic else "real", pop_src=pop_src)
    L(f"\n[summary] {summary}")

    # --- LaTeX + BERICHT (real data only)
    if not synthetic:
        write_tex(tex_path, AG, Q, summary, fmt)
        write_bericht(AG, Q, summary, fmt, weights, drawn, rep1, rep2)
        L(f"[tex] wrote {tex_path}")
    else:
        L("[tex] skipped (synthetic mode): paper/tables/app_goldset.tex and BERICHT numbers are only written from real rater data")
        # smoke-test the LaTeX writer into the scratch dir so the code path is proven
        write_tex(os.path.join(outdir, "app_goldset_SYNTHETIC.tex"), AG, Q, summary, fmt)

    LOG.close()
    if synthetic:
        print(f"\nSELF-TEST ONLY: real rater output is missing ({args.rater1}, {args.rater2}). "
              f"Synthetic outputs in {outdir}. Nothing written to artefakte/ except the log.", file=sys.stderr)
        sys.exit(2)


# =========================================================== 6. Writers
def tex_esc(s) -> str:
    return str(s).replace("\\", "\\textbackslash{}").replace("_", "\\_").replace("%", "\\%").replace("&", "\\&").replace("#", "\\#")


def f2(x) -> str:
    return "--" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.2f}"


def fp(x) -> str:
    """p-value: three decimals, '<0.001' below that."""
    return "--" if x is None or (isinstance(x, float) and math.isnan(x)) else ("<0.001" if x < 0.001 else f"{x:.3f}")


def ci(p, lo, hi) -> str:
    return "--" if isinstance(p, float) and math.isnan(p) else f"{p:.2f} [{lo:.2f}, {hi:.2f}]"


TEX_TARGET_NAMES = {"arrival": "round arrival (any)", "arrival_round": "arrival round (exact)", "speech_act": "speech act (5 classes)",
                    "future_answer": "future-answer receipt", "clock": "clock statement (4 classes)", "coord_topic": "coordination topic",
                    "register": "register (4 classes)", "env": "register: environment", "task": "register: task"}
TEX_CLASSIFIER_NAMES = {"arrival_obs_strong": "arrival, strong", "arrival_obs_weak": "arrival, weak", "speech_act": "speech act",
                        "future_answer_exact": "future answer (paper)", "future_answer_candidate": "future answer (vocab.)",
                        "clock_route": "clock route", "clock_route_any": "clock route, any", "coord_topic_sentence": "coord. topic (sent.)",
                        "coord_topic_delta": "coord. topic (delta)", "env_sentence": "ENV (sent.)", "env_delta": "ENV (delta)",
                        "primary_delta_env": "primary=ENV (delta)", "task_sentence": "TASK (sent.)"}


def write_tex(path: str, AG: pd.DataFrame, Q: pd.DataFrame, sm: dict, fmt: dict):
    today = datetime.date.today().isoformat()
    out = [f"% generated {today} by analyse/scripts/62_goldset_eval.py from paper_goldset_agreement.csv and paper_robust_regex_guete.csv",
           f"% mode: {sm['mode']}; population weights: {tex_esc(sm['pop_src'])}", ""]
    out += ["\\noindent{\\footnotesize\\adjustbox{max width=\\linewidth}{%", "\\begin{tabular}{lrrrrr}", "\\toprule",
            "Target & $n$ & Raw agreement & Cohen's $\\kappa$ & Krippendorff's $\\alpha$ & Disagreements \\\\", "\\midrule"]
    for r in AG.itertuples():
        out.append(f"{tex_esc(TEX_TARGET_NAMES.get(r.target, r.target))} & {r.n_both_coded} & {f2(r.raw_agreement)} & "
                   f"{f2(r.cohen_kappa)} & {f2(r.krippendorff_alpha)} & {r.n_disagree} \\\\")
    out += ["\\bottomrule", "\\end{tabular}}}", "", "\\medskip", ""]
    out += ["\\noindent{\\footnotesize\\adjustbox{max width=\\linewidth}{%", "\\begin{tabular}{llrrrrr}", "\\toprule",
            "Classifier & Class & $n$ & Precision [95\\,\\%] & Recall [95\\,\\%] & $F_1$ & Recall$_{\\text{pop}}$ [95\\,\\%] \\\\", "\\midrule"]
    for (c, k), grp in Q.groupby(["classifier", "class"], sort=False):
        if c == "primary_delta_env":      # identical to env_delta by construction (52:111-115 ENV first); kept in the CSV only
            continue
        r = grp[grp.weighting == "raw_sample"].iloc[0]; p = grp[grp.weighting == "population"].iloc[0]
        out.append(f"{tex_esc(TEX_CLASSIFIER_NAMES.get(c, c))} & {tex_esc(k)} & {r.n} & {ci(r.precision, r.p_lo, r.p_hi)} & "
                   f"{ci(r.recall, r.r_lo, r.r_hi)} & {f2(r.f1)} & {ci(p.recall, p.r_lo, p.r_hi)} \\\\")
    out += ["\\bottomrule", "\\end{tabular}}}", "", "\\smallskip", ""]
    a, b = fmt.get("format_state_filled", {}), fmt.get("format_r_confirmed", {})
    adj_txt = (f"all {sm['n_adjudicated']} were adjudicated by hand" if sm["n_open"] == 0 and sm["n_conflicts"] > 0
               else f"{sm['n_adjudicated']} were adjudicated by hand and {sm['n_open']} remain open (excluded from the gold labels)")
    prose = (f"\\noindent\\footnotesize The gold set holds $n={sm['n']}$ sentences drawn from {sm['n_strata']} strata; "
             f"{sm['n_both']} of them were coded completely by both raters"
             + (f" ({sm['n_incomplete']} still lack one coding)" if sm['n_incomplete'] else "") + ". "
             f"The raters disagreed on at least one field for {sm['n_conflicts']} sentences; {adj_txt}. "
             f"Precision is reported on the stratified sample; the last column reweights recall to the regex-positive populations "
             f"(stratum weight $=$ population\\,/\\,drawn) with Wilson intervals on the Kish effective sample size. "
             f"Filled \\texttt{{STATE5-XX}} tokens were coded as arrivals in {a.get('arrival_true', 0)} of {a.get('arrival_coded', 0)} cases, "
             f"\\texttt{{R\\# CONFIRMED}} sentences in {b.get('arrival_true', 0)} of {b.get('arrival_coded', 0)} "
             f"(Fisher exact $p{'<' if sm['fisher_p'] < 0.001 else '='}{fp(sm['fisher_p']).lstrip('<')}$).")
    out.append(prose)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")


def write_bericht(AG, Q, sm, fmt, weights, drawn, rep1, rep2):
    path = OUT("BERICHT_robust_goldset.md")
    if not os.path.exists(path):
        L(f"[bericht] {path} missing, numbers block not written"); return
    txt = open(path, encoding="utf-8").read()
    beg, end = "<!-- AUTO:BEGIN -->", "<!-- AUTO:END -->"
    if beg not in txt or end not in txt:
        L("[bericht] AUTO markers missing, numbers block not written"); return
    lines = [beg, f"_Automatisch von 62_goldset_eval.py am {datetime.date.today().isoformat()} eingesetzt; Modus: {sm['mode']}._", "",
             f"**Stichprobe:** n = {sm['n']}; vollständig kodiert von Rater 1: {sm['n_r1_complete']}, Rater 2: {sm['n_r2_complete']} "
             f"(Ladeprobleme R1: bad_json={rep1['bad_json']}, unknown={rep1['unknown_id']}, dup={rep1['duplicate_id']}, fehlend={rep1['missing_id']}; "
             f"R2: bad_json={rep2['bad_json']}, unknown={rep2['unknown_id']}, dup={rep2['duplicate_id']}, fehlend={rep2['missing_id']}).", "",
             f"**Konflikte:** {sm['n_conflicts']} Sätze mit mindestens einem abweichenden Feld (von {sm['n_both']} beidseitig kodierten); "
             f"{sm['n_adjudicated']} vollständig adjudiziert, {sm['n_open']} offen (Gold = NA); {sm['n_incomplete']} Sätze noch nicht von beiden kodiert.", "",
             "**Übereinstimmung:**", "", "| Ziel | n | roh | κ | α | Abweichungen |", "|---|---|---|---|---|---|"]
    for r in AG.itertuples():
        lines.append(f"| {r.target} | {r.n_both_coded} | {f2(r.raw_agreement)} | {f2(r.cohen_kappa)} | {f2(r.krippendorff_alpha)} | {r.n_disagree} |")
    lines += ["", f"**Regex-Güte** (Gewichte: {sm['pop_src']}):", "",
              "| Klassifikator | Klasse | n | P [95 %] | R [95 %] | F1 | R_pop [95 %] | F1_pop |", "|---|---|---|---|---|---|---|---|"]
    for (c, k), grp in Q.groupby(["classifier", "class"], sort=False):
        r = grp[grp.weighting == "raw_sample"].iloc[0]; p = grp[grp.weighting == "population"].iloc[0]
        lines.append(f"| {c} | {k} | {r.n} | {ci(r.precision, r.p_lo, r.p_hi)} | {ci(r.recall, r.r_lo, r.r_hi)} | {f2(r.f1)} | "
                     f"{ci(p.recall, p.r_lo, p.r_hi)} | {f2(p.f1)} |")
    lines += ["", "**Formatvergleich (§7):**", "", "| Stratum | n | arrival | R5 | observation | request | negation |", "|---|---|---|---|---|---|---|"]
    for st, f in fmt.items():
        lines.append(f"| {st} | {f['n']} | {f['arrival_true']}/{f['arrival_coded']} | {f['round5']} | {f['obs']}/{f['sa_coded']} | {f['req']} | {f['neg']} |")
    lines += [f"", f"Fisher exact (Anteil arrival, STATE-filled vs R CONFIRMED): p {fp(sm['fisher_p']) if fp(sm['fisher_p']).startswith('<') else '= ' + fp(sm['fisher_p'])}.", "",
              "**Stratum-Gewichte:**", "", "| Stratum | gezogen | Population | Gewicht |", "|---|---|---|---|"]
    for st in sorted(weights, key=lambda s: -weights[s]):
        lines.append(f"| {st} | {drawn[st]} | {weights[st] * drawn[st]:.0f} | {weights[st]:.2f} |")
    lines.append(end)
    new = txt[:txt.index(beg)] + "\n".join(lines) + txt[txt.index(end) + len(end):]
    open(path, "w", encoding="utf-8").write(new)
    L(f"[bericht] numbers block updated in {path}")


if __name__ == "__main__":
    main()
