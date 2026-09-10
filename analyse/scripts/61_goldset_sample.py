#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
61_goldset_sample.py
====================
Stratified gold-set sample (n=400 sentences) for scoring the paper's regex
classifiers (precision / recall / F1, inter-rater kappa).

Universe : every sentence of every non-empty delta in schwarm_deltas.parquet,
           split exactly as 51_prozess.py does (SENT_SPLIT, strip, len >= 3).
Strata   : regex-positive classes of the six classifier families + one
           regex-negative stratum (sentence carries a round marker or a time
           expression but no classifier fires).
Outputs  : artefakte/paper_goldset_sample.csv        (with every regex label)
           artefakte/paper_goldset_sample_blind.csv  (id + text only, shuffled)

All regexes are loaded *from the source scripts* via `ast` (single source of
truth); nothing is re-typed here.  Source lines (verified 2026-09-09):
  51_prozess.py:155-163   SENT_SPLIT, RND, REQ, NEG, PRED, OBS, FP, FUTWIN, TOD
  51_prozess.py:166-171   classify()  (priority request > negation > prediction > observation)
  51_prozess.py:177-179   sentence loop (split, strip, len >= 3); :190 num <= 10 guard; :192-193 window rule (fenster_ok)
  51_prozess.py:202-203   strong_obs
  51_prozess.py:276       ACK
  51_prozess.py:318-331   future-answer receipt (fremddatum & num > run_max & cls ok & ACK & num <= 6)
  50_uhr_auslastung.py:63-94, 101-130, 132-210  clock nouns/times, mentions(), routes A/B/C
  55_dramaturgie.py:21,25-42,186                prosa, TAX, koord = uhr|runde|taktung|abschaltung|vorhersage|signal
  52_ml_verhalten.py:48-71, 75, 84-86, 111-115  ENV / COORD / TASK blocks, case-insensitive, ENV > TASK > COORD
  41_lernkurve.py:20                             state_conf (STATE[0-9]- | R[1-9] CONFIRMED | CONFIRMED= )

Run:  .venv/bin/python scripts/61_goldset_sample.py
"""
from __future__ import annotations
import ast, os, re, collections, hashlib, warnings
warnings.filterwarnings("ignore", category=UserWarning)
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)                  # analyse/
ART = os.path.join(BASE, "artefakte")
OUT = lambda n: os.path.join(ART, n)
SEED = 20260909
N_TOTAL = 400
rng = np.random.default_rng(SEED)


# ------------------------------------------------------------------ 0. regex loader
def load_defs(script: str, names: list[str]) -> dict:
    """Evaluate top-level `NAME = <literal / re.compile(...)>` assignments of a
    source script in order, so later names may reference earlier ones (MON)."""
    src = open(os.path.join(HERE, script), encoding="utf-8").read()
    tree = ast.parse(src)
    env = {"re": re}
    wanted = set(names)
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            nm = node.targets[0].id
            if nm in wanted or nm == "MON":
                env[nm] = eval(compile(ast.Expression(node.value), script, "eval"), env)
    missing = wanted - set(env)
    if missing:
        raise RuntimeError(f"{script}: definitions not found: {missing}")
    return {k: env[k] for k in names}


P51 = load_defs("51_prozess.py", ["MONDD", "SENT_SPLIT", "RND", "REQ", "NEG", "PRED", "OBS", "FP", "FUTWIN", "TOD", "ACK"])
P50 = load_defs("50_uhr_auslastung.py", ["NOUN", "TIME", "TASKSET", "GAP_OK", "NOW_CUE", "EVENT_CUE", "PAST_CUE",
                                          "FUTURE_ONLY", "FIRST_PERSON"])
P55 = load_defs("55_dramaturgie.py", ["TAX"])
P52 = load_defs("52_ml_verhalten.py", ["ENV", "COORD", "TASK"])
P41 = load_defs("41_lernkurve.py", ["PAT"])

SENT_SPLIT, RND, REQ, NEG, PRED, OBS, FP, FUTWIN, TOD, ACK, MONDD = (
    P51[k] for k in ["SENT_SPLIT", "RND", "REQ", "NEG", "PRED", "OBS", "FP", "FUTWIN", "TOD", "ACK", "MONDD"])
KOORD_THEMES = ["uhr", "runde", "taktung", "abschaltung", "vorhersage", "signal"]   # 55_dramaturgie.py:186
KOORD_RE = [re.compile(P55["TAX"][k]) for k in KOORD_THEMES]
ENV_RE = re.compile("|".join(f"(?:{p})" for p in P52["ENV"].values()), re.I)       # 52:75 case=False
TASK_RE = re.compile("|".join(f"(?:{p})" for p in P52["TASK"].values()), re.I)
COORD52_RE = re.compile("|".join(f"(?:{p})" for p in P52["COORD"].values()), re.I)
# 41_lernkurve.py:20 state_conf, split into its three alternatives
FMT_STATE = re.compile(r"(?i)\bSTATE[0-9]-")
FMT_STATE_FILLED = re.compile(r"\bSTATE[0-9]-(?!XX\b)[A-Z]{2}\b")   # token with a concrete postal code, not the XX placeholder
FMT_RCONF = re.compile(r"(?i)\bR[1-9]\s*CONFIRMED\b")
FMT_CONFEQ = re.compile(r"(?i)\bCONFIRMED[0-9]?\s*=")
assert re.compile(P41["PAT"]["state_conf"]).search("STATE5-TX") and re.compile(P41["PAT"]["state_conf"]).search("R5 CONFIRMED")
PROSA_URL = re.compile(r"https?://\S+"); PROSA_WL = re.compile(r"\[\[[^\]]*\]\]"); PROSA_CGI = re.compile(r"wiki\.cgi\?\S+")


def prosa(t: str) -> str:            # 55_dramaturgie.py:21
    return PROSA_CGI.sub(" ", PROSA_WL.sub(" ", PROSA_URL.sub(" ", t)))


def classify(sent):                  # 51_prozess.py:166-171
    if REQ.search(sent): return "request"
    if NEG.search(sent): return "negation"
    if PRED.search(sent): return "prediction"
    if OBS.search(sent): return "observation"
    return "unclassified"


# ------------------------------------------------------------------ 1. universe
d = pd.read_parquet(OUT("schwarm_deltas.parquet"))
d["time"] = pd.to_datetime(d["time"], utc=True)
d["delta"] = d["delta"].fillna("")
d = d[d.delta.str.len() > 0].sort_values(["time", "page_key", "seq"]).reset_index(drop=True)
print(f"[universe] non-empty deltas: {len(d)}")

rows = []
for r in d.itertuples():
    sents = [s.strip() for s in SENT_SPLIT.split(r.delta)]
    sents = [s for s in sents if len(s) >= 3]                       # 51:177-179
    for i, s in enumerate(sents):
        rows.append(dict(rev_id=r.rev_id, page_key=r.page_key, label=r.label, time=r.time,
                         sent_idx=i, n_sents=len(sents), sentence=s,
                         context_before=sents[i - 1] if i > 0 else "",
                         context_after=sents[i + 1] if i + 1 < len(sents) else "",
                         delta=r.delta))
U = pd.DataFrame(rows)
print(f"[universe] sentences: {len(U)}")

# ------------------------------------------------------------------ 2. sentence-level regex labels
def round_nums(s):
    out = []
    for m in RND.finditer(s):
        num = int(m.group(2) or m.group(4))
        if num > 10: continue                                        # 51:190
        out.append(((m.group(1) or "round").upper(), num, m))
    return out


def window_ok(s, m):                                                 # 51:192-193
    win = s[max(0, m.start() - 30): m.end() + 45]
    return bool(OBS.search(win)) and not FUTWIN.search(win)


lab = collections.defaultdict(list)
for s in U.sentence:
    rn = round_nums(s)
    lab["regex_has_round"].append(bool(rn))
    lab["regex_round_marks"].append(";".join(f"{f}{n}" for f, n, _ in rn))
    lab["regex_speech_act"].append(classify(s) if rn else "none")
    lab["regex_firstperson"].append(bool(FP.search(s)))
    tod = TOD.search(s)
    lab["regex_tod"].append(tod.group(0) if tod else "")
    lab["regex_has_time"].append(bool(tod) or bool(P50["TIME"].search(s)))
    lab["regex_window_ok_any"].append(any(window_ok(s, m) for _, _, m in rn))
    lab["regex_ack_vocab"].append(bool(ACK.search(s)))
    lab["regex_foreign_date_any"].append(bool(MONDD.findall(s)))
    ps = prosa(s)
    lab["regex_coord_topic_sentence"].append(any(p.search(ps) for p in KOORD_RE))
    lab["regex_env_sentence"].append(bool(ENV_RE.search(s)))
    lab["regex_task_sentence"].append(bool(TASK_RE.search(s)))
    lab["regex_coord52_sentence"].append(bool(COORD52_RE.search(s)))
    lab["regex_format_state"].append(bool(FMT_STATE.search(s)))
    lab["regex_format_state_filled"].append(bool(FMT_STATE_FILLED.search(s)))
    lab["regex_format_rconfirmed"].append(bool(FMT_RCONF.search(s)))
    lab["regex_format_confirmed_eq"].append(bool(FMT_CONFEQ.search(s)))
for k, v in lab.items():
    U[k] = v

# delta-level labels (the granularity at which 52 and 55 actually classify)
dl = d.set_index("rev_id")
dprosa = dl.delta.map(prosa)
d_coord = pd.Series(False, index=dl.index)
for p in KOORD_RE:
    d_coord |= dprosa.str.contains(p, regex=True, na=False)
d_env = dl.delta.str.contains(ENV_RE, regex=True, na=False)
d_task = dl.delta.str.contains(TASK_RE, regex=True, na=False)
d_c52 = dl.delta.str.contains(COORD52_RE, regex=True, na=False)
d_prim = np.where(d_env, "ENV_META", np.where(d_task, "TASK", np.where(d_c52, "COORD", "REST")))   # 52:111-115
U["regex_coord_topic_delta"] = U.rev_id.map(d_coord)
U["regex_env_delta"] = U.rev_id.map(d_env)
U["regex_task_delta"] = U.rev_id.map(d_task)
U["regex_primary_delta"] = U.rev_id.map(pd.Series(d_prim, index=dl.index))

# ------------------------------------------------------------------ 3. labels that need cohort state: join the paper artefact
RM = pd.read_csv(OUT("paper_prozess_rundensaetze_delta.csv"))
RM["time"] = pd.to_datetime(RM["time"], utc=True)
RM["fremddatum"] = RM.fremddatum.astype(bool); RM["fenster_ok"] = RM.fenster_ok.astype(bool)
RM["firstperson"] = RM.firstperson.astype(bool)
RM["strong_obs"] = (RM.cls == "observation") & (~RM.fremddatum) & (
    RM.firstperson | RM.tod.notna() | RM.sent.str.contains("CONFIRMED")) & RM.fenster_ok        # 51:202-203
# future-answer receipt, 51:318-331 reproduced per cohort
RM["future_answer"] = False
for coh, rmg in RM[RM.cohort.notna()].groupby("cohort"):
    rmg = rmg.sort_values("time")
    so = rmg[rmg.strong_obs]
    own_obs_times = so[["time", "num"]].values.tolist()
    for idx, r in rmg.iterrows():
        own_before = [n for t, n in own_obs_times if t <= r.time]
        run_max = max(own_before) if own_before else 0
        if r.fremddatum and r.num > run_max and r.cls not in ("request", "prediction", "negation") \
                and ACK.search(r.sent) and r.num <= 6:
            RM.loc[idx, "future_answer"] = True
# ACK candidate without the cohort-state condition (superset used as its own stratum)
RM["future_answer_candidate"] = RM.fremddatum & RM.cls.isin(["observation", "unclassified"]) & (RM.num <= 6) \
    & RM.sent.map(lambda s: bool(ACK.search(str(s))))
agg = (RM.assign(key=RM.rev_id + "\x1f" + RM.sent.astype(str))
         .groupby("key").agg(regex_strong_obs=("strong_obs", "any"),
                             regex_foreign_date=("fremddatum", "any"),
                             regex_future_answer=("future_answer", "any"),
                             regex_future_answer_candidate=("future_answer_candidate", "any"),
                             own_date=("own_date", "first"), cohort=("cohort", "first")))
U["_key"] = U.rev_id + "\x1f" + U.sentence.str[:300]
for c in ["regex_strong_obs", "regex_foreign_date", "regex_future_answer", "regex_future_answer_candidate"]:
    U[c] = U._key.map(agg[c]).fillna(False).astype(bool)
U["own_date"] = U._key.map(agg.own_date); U["cohort"] = U._key.map(agg.cohort)
print(f"[join] round-sentences in artefact: {agg.shape[0]}  matched in universe: {U._key.isin(agg.index).sum()}  "
      f"(universe round-sentences: {int(U.regex_has_round.sum())})")
print(f"[join] future_answer exact positives: {int(U.regex_future_answer.sum())} (artefact sum: {int(RM.future_answer.sum())}); "
      f"candidates: {int(U.regex_future_answer_candidate.sum())}")

# clock statements: link the line-level artefact (50_uhr_auslastung.py) to sentences
TZ = pd.read_csv(OUT("paper_uhr_taskzeiten.csv"))
tz_by_rev = collections.defaultdict(list)
for r in TZ.itertuples():
    tz_by_rev[r.rev_id].append((r.weg, str(r.task_time_raw), str(r.evidence_snippet)))
routes = []; raws = []
for r in U.itertuples():
    got = set(); rw = []
    for weg, raw, snip in tz_by_rev.get(r.rev_id, []):
        if raw in r.sentence and (r.sentence[:380] in snip or snip[:200] in r.sentence):
            got.add(weg); rw.append(f"{weg}:{raw}")
    routes.append("+".join(sorted(got)) if got else "none"); raws.append(" | ".join(rw))
U["regex_clock_route"] = routes; U["regex_clock_raw"] = raws
print(f"[join] clock rows in artefact: {len(TZ)}; sentences with route: {(U.regex_clock_route != 'none').sum()}; "
      f"by route: {U.regex_clock_route.value_counts().to_dict()}")

# ------------------------------------------------------------------ 4. strata
U["stratum_any_positive"] = (
    U.regex_speech_act.isin(["request", "prediction", "negation", "observation"]) | U.regex_strong_obs
    | U.regex_future_answer | U.regex_future_answer_candidate | (U.regex_clock_route != "none")
    | U.regex_coord_topic_sentence | U.regex_env_sentence
    | U.regex_format_state | U.regex_format_rconfirmed | U.regex_format_confirmed_eq)
neg_mask = (~U.stratum_any_positive) & (U.regex_has_round | U.regex_has_time)

STRATA = [  # (name, mask, target) — rare classes first; ALL positives if the class has <= target members
    ("future_answer_ack", U.regex_future_answer, 40),
    ("future_answer_candidate", U.regex_future_answer_candidate & ~U.regex_future_answer, 20),
    ("format_state_filled", U.regex_format_state_filled, 25),
    ("format_state_placeholder", U.regex_format_state & ~U.regex_format_state_filled, 10),
    ("clock_B_bare_now", U.regex_clock_route.str.contains("B"), 20),
    ("clock_A_pair", U.regex_clock_route.str.contains("A"), 20),
    ("clock_C_past_event", U.regex_clock_route.str.contains("C"), 20),
    ("strong_obs", U.regex_strong_obs, 30),
    ("speech_negation", U.regex_speech_act == "negation", 25),
    ("speech_observation_weak", (U.regex_speech_act == "observation") & ~U.regex_strong_obs, 25),
    ("env_positive", U.regex_env_sentence, 20),
    ("coord_topic", U.regex_coord_topic_sentence & ~U.regex_env_sentence, 20),
    ("speech_request", U.regex_speech_act == "request", 25),
    ("speech_prediction", U.regex_speech_act == "prediction", 25),
    ("format_r_confirmed", U.regex_format_rconfirmed | U.regex_format_confirmed_eq, 25),
]
taken = set(); U["stratum"] = ""
pop_sizes = {}
for name, mask, target in STRATA:
    pool = U.index[mask & ~U.index.isin(taken)]
    pop_sizes[name] = int(mask.sum())
    n = min(target, len(pool))
    pick = rng.choice(pool, size=n, replace=False) if n else []
    U.loc[pick, "stratum"] = name; taken.update(pick)
n_neg = max(80, N_TOTAL - len(taken))
pool = U.index[neg_mask & ~U.index.isin(taken)]
pop_sizes["negative_random"] = int(neg_mask.sum())
pick = rng.choice(pool, size=min(n_neg, len(pool)), replace=False)
U.loc[pick, "stratum"] = "negative_random"; taken.update(pick)

S = U[U.stratum != ""].copy()
# opaque ids in a seeded shuffle so the blind file leaks neither page nor stratum order
perm = rng.permutation(len(S))
S = S.iloc[perm].reset_index(drop=True)
S.insert(0, "id", [f"G{i + 1:03d}" for i in range(len(S))])
S["rev_hash"] = S.rev_id.map(lambda x: hashlib.sha1(x.encode()).hexdigest()[:10])

cols = ["id", "stratum", "page_key", "label", "time", "rev_id", "sent_idx", "n_sents", "cohort", "own_date",
        "context_before", "sentence", "context_after",
        "regex_has_round", "regex_round_marks", "regex_speech_act", "regex_strong_obs", "regex_window_ok_any",
        "regex_firstperson", "regex_tod", "regex_has_time", "regex_foreign_date", "regex_foreign_date_any",
        "regex_ack_vocab", "regex_future_answer", "regex_future_answer_candidate",
        "regex_clock_route", "regex_clock_raw",
        "regex_coord_topic_sentence", "regex_coord_topic_delta",
        "regex_env_sentence", "regex_task_sentence", "regex_coord52_sentence",
        "regex_env_delta", "regex_task_delta", "regex_primary_delta",
        "regex_format_state", "regex_format_state_filled", "regex_format_rconfirmed", "regex_format_confirmed_eq"]
full = S[cols].copy()
for c in ["context_before", "sentence", "context_after"]:
    full[c] = full[c].str.slice(0, 600)
full.to_csv(OUT("paper_goldset_sample.csv"), index=False)
blind = full[["id", "context_before", "sentence", "context_after"]]
blind.to_csv(OUT("paper_goldset_sample_blind.csv"), index=False)

print("\n=== stratum counts (drawn / regex-positive population) ===")
cnt = full.stratum.value_counts()
for name in [s[0] for s in STRATA] + ["negative_random"]:
    print(f"  {name:26s} {int(cnt.get(name, 0)):4d} / {pop_sizes[name]}")
print(f"  {'TOTAL':26s} {len(full):4d}")
print("format families in sample: STATE-format", int(full.regex_format_state.sum()), "(filled", int(full.regex_format_state_filled.sum()), ")",
      "| R CONFIRMED", int(full.regex_format_rconfirmed.sum()), "| CONFIRMED=", int(full.regex_format_confirmed_eq.sum()))
print("speech acts in sample:", full.regex_speech_act.value_counts().to_dict())
print("clock routes in sample:", full.regex_clock_route.value_counts().to_dict())
print(f"wrote {OUT('paper_goldset_sample.csv')} and {OUT('paper_goldset_sample_blind.csv')}")
