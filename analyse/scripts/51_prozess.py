#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
51_prozess.py
=============
A. Fortschrittstabelle je Kohorte (Aufgabenfamilie x fiktives Kohortendatum)
B. Ereignisprotokoll + Prozessentdeckung (DFG, Varianten, Abweichler)
C. Unangetastete Struktur: Einflussgraph auf Seitenebene, Zitat-Kaskaden,
   Negativraum der geloeschten Seiten, verlorene Speicherversuche, Wettlauf
   Administrator gegen Flotte.

Alle Pfade RELATIV zum Skript-Ort (analyse/scripts/ -> analyse/).
Lauf:  .venv/bin/python scripts/51_prozess.py
Autorenschaft ausschliesslich ueber `delta` (schwarm_deltas.parquet), nie ueber `body`.
"""
from __future__ import annotations
import os, re, json, math, warnings, collections, itertools
import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
DATA = os.path.join(BASE, "data")
ART = os.path.join(BASE, "artefakte")
OUT = lambda n: os.path.join(ART, n)
LOG = open(OUT("_paper_prozess.log"), "w", encoding="utf-8")


def L(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LOG.write(s + "\n")


# =========================================================== 0. Laden
d = pd.read_parquet(OUT("schwarm_deltas.parquet"))
d["time"] = pd.to_datetime(d["time"], utc=True)
d["delta"] = d["delta"].fillna("")
d = d.sort_values(["time", "page_key", "seq"]).reset_index(drop=True)
pages = pd.read_json(os.path.join(DATA, "pages.jsonl"), lines=True)
labels = pd.read_json(os.path.join(DATA, "labels.jsonl"), lines=True)
events = pd.read_json(os.path.join(DATA, "events.jsonl"), lines=True)
events["time"] = pd.to_datetime(events["time"], utc=True, errors="coerce")
tier = pd.read_csv(OUT("harness_tier_table.csv"))
L(f"Deltas {len(d)}  Seiten {len(pages)}  Labels {len(labels)}  Events {len(events)}")

# =========================================================== 1. Kohortenzuordnung
MON = "(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
MONDD = re.compile(rf"\b({MON})\s?(\d{{2}})(?!\d)(?!\s?(?:20\d\d|\d{{1,2}}:\d{{2}}))")
MONDD_NAME = re.compile(rf"({MON})(\d{{2}})(?!\d)")
SIG = re.compile(r"(?m)--\s*([A-Za-z][A-Za-z0-9_]{3,})\s*$")
SELFID = re.compile(
    rf"(?i)(?:\b({MON})\s?(\d{{2}})\s*(?:\d{{4}}\s*)?cohort\s*(?:here|checking in|update|live|status|report|checking|reporting|confirm)"
    rf"|(?:our|we are|this is|I am|we're|my)\s+(?:the\s+)?(?:separate\s+|live\s+|own\s+)?({MON})\s?(\d{{2}})\s*(?:\d{{4}}\s*)?(?:cohort|run|thread|task[- ]clock|scaffold))"
)

# Aufgabenfamilie: aus pages.jsonl (Seitenklassifikation), sonst Stichwoerter im Delta
BAD_FAM = {"relay-coordination", "source-cache-url-list", "source-or-unclassified", "off_store_unclassified",
           "loop-chain-infrastructure", "probe-test", "unknown", "mixed-task", None, np.nan}
pfam = pages.set_index("page_key")["page_family"].to_dict()
d["page_family"] = d.page_key.map(pfam)
KW = [
    ("datausa-grocery-workforce", r"(?i)grocery"),
    ("datausa-clothing-workforce", r"(?i)clothing"),
    ("datausa-cashiers-masters", r"(?i)cashier.{0,40}master|master.{0,40}cashier"),
    ("datausa-cashiers-bachelors", r"(?i)cashier.{0,40}bachelor|bachelor.{0,40}cashier"),
    ("datausa-construction-workforce", r"(?i)construction"),
    ("datausa-sector61-state", r"(?i)sector\s?61"),
    ("ihme-cvd-deaths", r"(?i)\bCVD\b|cardiovascular"),
    ("datausa-language-french", r"(?i)\bfrench\b|LangR5"),
    ("datausa-poverty-county", r"(?i)poverty.{0,30}county|county.{0,30}poverty"),
    ("datausa-poverty-state", r"(?i)poverty"),
    ("ihme-family-planning", r"(?i)family planning|\bFP\b"),
    ("datausa-maids-wage", r"(?i)\bmaids?\b"),
    ("datausa-police-wage-age", r"(?i)\bpolice\b"),
    ("datausa-finance-gender-gap", r"(?i)gender gap|finance"),
    ("datausa-transport-production", r"(?i)transport"),
    ("oecd-equity", r"(?i)equity"),
    ("oecd-regional-co2", r"(?i)\bCO2\b|regional recovery"),
    ("uefa-pass-accuracy", r"(?i)\bUEFA\b|pass accuracy"),
    ("sdg-index", r"(?i)\bSDG\b"),
    ("aihw-pbs", r"(?i)\bAIHW\b|\bPBS\b"),
    ("nyc-veterans", r"(?i)veteran"),
    ("vermont-rent", r"(?i)vermont"),
    ("datausa-occupation-salary-61-62", r"(?i)61-62|occupation salary"),
]


def kw_family(text):
    for fam, pat in KW:
        if re.search(pat, text):
            return fam
    return None


# je Label: Familie = Modus der Seitenfamilie (nur echte Aufgabenfamilien), sonst Stichwort-Modus
lab_fam = {}
fam_src = {}
for lab, g in d.groupby("label"):
    fams = [f for f in g.page_family if f not in BAD_FAM and isinstance(f, str)]
    if fams:
        lab_fam[lab] = collections.Counter(fams).most_common(1)[0][0]; fam_src[lab] = "seite"
        continue
    kws = [kw_family(t) for t in g.delta]
    kws = [k for k in kws if k]
    if kws:
        lab_fam[lab] = collections.Counter(kws).most_common(1)[0][0]; fam_src[lab] = "stichwort"
    else:
        lab_fam[lab] = None; fam_src[lab] = "keine"


def dates_in_name(name):
    return [m.group(1) + m.group(2) for m in MONDD_NAME.finditer(name or "")]


lab_date = {}
date_src = {}
for lab, g in d.groupby("label"):
    dn = dates_in_name(lab)
    if dn:
        lab_date[lab] = collections.Counter(dn).most_common(1)[0][0]; date_src[lab] = "labelname"; continue
    sigs = []
    for t in g.delta:
        for s in SIG.findall(t):
            sigs += dates_in_name(s)
    if sigs:
        lab_date[lab] = collections.Counter(sigs).most_common(1)[0][0]; date_src[lab] = "signatur"; continue
    ids = []
    for t in g.delta:
        for m in SELFID.finditer(t):
            gr = [x for x in m.groups() if x]
            if len(gr) >= 2:
                ids.append(gr[0] + gr[1])
    if ids:
        lab_date[lab] = collections.Counter(ids).most_common(1)[0][0]; date_src[lab] = "selbstnennung"; continue
    lab_date[lab] = None; date_src[lab] = "keine"

d["fam"] = d.label.map(lab_fam)
d["kdate"] = d.label.map(lab_date)
d["cohort"] = np.where(d.fam.notna() & d.kdate.notna(), d.fam.astype(str) + "|" + d.kdate.astype(str), None)
lab_tab = pd.DataFrame({"label": list(lab_fam), "fam": pd.Series(lab_fam), "fam_quelle": pd.Series(fam_src),
                        "kdate": pd.Series(lab_date), "datum_quelle": pd.Series(date_src)}).reset_index(drop=True)
lab_tab["cohort"] = np.where(lab_tab.fam.notna() & lab_tab.kdate.notna(), lab_tab.fam.astype(str) + "|" + lab_tab.kdate.astype(str), None)
lab_tab.to_csv(OUT("paper_prozess_label_zuordnung.csv"), index=False)
L("\n=== Mengengeruest Kohortenzuordnung (Labels) ===")
L("Datumsquelle:", dict(collections.Counter(date_src.values())))
L("Familienquelle:", dict(collections.Counter(fam_src.values())))
L("Labels mit Kohorte:", lab_tab.cohort.notna().sum(), "von", len(lab_tab),
  "| Deltas mit Kohorte:", d.cohort.notna().sum(), "von", len(d))
L("distinkte Kohorten:", d.cohort.nunique(), "| distinkte Daten:", d.kdate.nunique(), "| Familien:", d.fam.nunique())

# =========================================================== 2. Satzklassifikation (Runden)
SENT_SPLIT = re.compile(r"[.!?\n;]+")
RND = re.compile(r"\b(?:(R|Q|G)\s?(\d{1,2})|(round)\s*(\d{1,2}))\b", re.I)
REQ = re.compile(r"\b(please|seeking|has your|have you|anyone|survivor|relay|append|post|share|clarify|report whether|ping|urgent|if you)\b", re.I)
NEG = re.compile(r"\b(no|not|never|none|without|absent|missing|unverified|unconfirmed|silence|no-show|did not|failed to|lack\w*)\b", re.I)
PRED = re.compile(r"\b(expect\w*|predict\w*|project\w*|nominal|will|would|due|anticipat\w*|scheduled|await\w*|pending|likely|suspect\w*|phantom|hypothe\w*|assum\w*|monitor\w*|threshold|may|might|could|whether|if)\b", re.I)
OBS = re.compile(r"\b(arrived|arrival|received|came|landed|delivered|observed|answered|appeared|began|started|activation|logged|recorded|completed|submitted|confirmed|done)\b", re.I)
FP = re.compile(r"(?<![A-Za-z])(our|ours|we|us|my|mine|I)(?![A-Za-z'])")
FUTWIN = re.compile(r"(?i)\b(before|after|until|till|due|horizon|arrives|will|expect\w*|next|upcoming|projected|cutoff|nominal|if)\b")
TOD = re.compile(r"\b([0-2]?\d):([0-5]\d)(?::([0-5]\d))?\b")


def classify(sent):
    if REQ.search(sent): return "request"
    if NEG.search(sent): return "negation"
    if PRED.search(sent): return "prediction"
    if OBS.search(sent): return "observation"
    return "unclassified"


rows = []
for r in d.itertuples():
    own = r.kdate
    for s in SENT_SPLIT.split(r.delta):
        s = s.strip()
        if len(s) < 3: continue
        ms = list(RND.finditer(s))
        if not ms: continue
        cls = classify(s)
        fp = bool(FP.search(s))
        others = {a + b for a, b in MONDD.findall(s)}
        others.discard(own)
        tod = TOD.search(s)
        for m in ms:
            fam = (m.group(1) or "round").upper()
            num = int(m.group(2) or m.group(4))
            if num > 10: continue
            # Fensterregel: Beobachtungsverb in Naehe des Markers, kein Zukunfts-/Relativwort im Fenster
            win = s[max(0, m.start() - 30): m.end() + 45]
            fenster_ok = bool(OBS.search(win)) and not FUTWIN.search(win)
            rows.append((r.rev_id, r.page_key, r.label, r.time, r.cohort, own, fam, num, cls, fp,
                         bool(others), tod.group(0) if tod else None, fenster_ok, s[:300]))
RM = pd.DataFrame(rows, columns=["rev_id", "page_key", "label", "time", "cohort", "own_date", "fam", "num", "cls",
                                 "firstperson", "fremddatum", "tod", "fenster_ok", "sent"])
RM.to_csv(OUT("paper_prozess_rundensaetze_delta.csv"), index=False)
L("\n=== Rundensaetze auf Deltas ===", len(RM), "Saetze;", RM.cls.value_counts().to_dict())

# "Belegte Beobachtung": Beobachtungsklasse, ohne Fremddatum, und (Erste Person ODER Uhrzeit ODER CONFIRMED)
RM["strong_obs"] = (RM.cls == "observation") & (~RM.fremddatum) & (
    RM.firstperson | RM.tod.notna() | RM.sent.str.contains("CONFIRMED")) & RM.fenster_ok
L("strong_obs je Runde:", RM[RM.strong_obs].groupby("num").cohort.nunique().to_dict())
L("R6+ strong_obs Belege:")
for r in RM[RM.strong_obs & (RM.num >= 6)].itertuples():
    L(f"  {r.page_key} · {r.time} · {r.label} · {r.fam}{r.num} :: {r.sent[:160]}")

# =========================================================== 3. Fristen/Kadenz aus Deltas
DUR = r"(\d{1,2}h\s?\d{1,2}m(?:\s?\d{1,2}s?)?|\d{1,3}m\s?\d{1,2}s?|\d{1,3}\s?m(?:in)?\b|\d{1,3}\s?s(?:ec(?:onds)?)?\b)"
R1T = re.compile(rf"(?i)\b(?:initial|first|R1|Q1|G1)\b[^.\n;]{{0,40}}?(?:timer|deadline|limit|window)[^\d\n]{{0,12}}{DUR}")
R1T2 = re.compile(rf"(?i)(?:timer[^\d\n]{{0,6}}{DUR}[^.\n;]{{0,25}}\b(?:initial|first|R1)\b|\b{DUR}\s*(?:initial\s+)?timer\b[^.\n;]{{0,25}}\b(?:initial|first|R1)\b)")
CAD = re.compile(rf"(?i)(?:cadence|cooldown|interval|spacing|gap|period)[^\d\n]{{0,25}}{DUR}")
FUT = re.compile(rf"(?i)(?:follow[- ]?ups?|R[2-5]|G[2-5]|Q[2-5]|subsequent|later rounds?)[^.\n;]{{0,40}}?(?:timer|deadline|limit|window)[^\d\n]{{0,10}}(\d{{1,3}})\s?s(?:ec(?:onds)?)?\b")
FUT2 = re.compile(r"(?i)\b(\d{1,3})\s?s(?:ec(?:onds)?)?\s*(?:timer|deadline|limit|window)")


def to_sec(x):
    x = x.lower().replace(" ", "")
    m = re.match(r"(?:(\d+)h)?(?:(\d+)m(?:in)?)?(?:(\d+)s?)?$", x)
    if not m: return None
    h, mi, s = m.groups()
    if h is None and mi is None and s is None: return None
    v = int(h or 0) * 3600 + int(mi or 0) * 60 + int(s or 0)
    return v if v > 0 else None


def mode_sec(vals):
    vals = [v for v in vals if v]
    if not vals: return (None, 0)
    c = collections.Counter(vals).most_common(1)[0]
    return c


def _flat(ms):
    out = []
    for m in ms:
        if isinstance(m, tuple): out += [x for x in m if x]
        elif m: out.append(m)
    return out


def own_sentences(text, own):
    """Saetze ohne Fremd-Kohortendatum (Fristen fremder Kohorten werden so ausgeschlossen)."""
    out = []
    for s_ in SENT_SPLIT.split(text):
        dts = {a + b for a, b in MONDD.findall(s_)}
        if own: dts.discard(own)
        if dts: continue  # Satz nennt eine fremde Kohorte -> nicht die eigene Frist
        out.append(s_)
    return out


r1l, cadl, futl = [], [], []
for t, own in zip(d.delta, d.kdate):
    ss = own_sentences(t, own if isinstance(own, str) else None)
    r1l.append([to_sec(x) for s_ in ss for x in _flat(R1T.findall(s_)) + _flat(R1T2.findall(s_))])
    cadl.append([to_sec(x) for s_ in ss for x in _flat(CAD.findall(s_))])
    futl.append([int(x) for s_ in ss for x in FUT.findall(s_) + FUT2.findall(s_)])
d["r1_sec"], d["cad_sec"], d["fut_sec"] = r1l, cadl, futl
# plausibilisieren
d["r1_sec"] = d.r1_sec.apply(lambda v: [x for x in v if x and 30 <= x <= 3600])
d["cad_sec"] = d.cad_sec.apply(lambda v: [x for x in v if x and 120 <= x <= 4 * 3600])
d["fut_sec"] = d.fut_sec.apply(lambda v: [x for x in v if 3 <= x <= 120])

# =========================================================== 4. Techniken, Geben/Nehmen
TECH = {
    "clock_wait": r"(?i)clock\.wait",
    "counterapi": r"(?i)api\.counterapi\.dev|counterapi",
    "umleitung": r"(?i)jqp\.vercel\.app|md\.succ\.ai|allorigins|markdown\.new|corsmirror|r\.jina\.ai",
    "blob_ausbruch": r"(?i)blob\.core\.windows\.net",
    "setsid": r"(?i)\bsetsid\b",
}
for k, p in TECH.items():
    d[k] = d.delta.str.contains(p, regex=True, na=False)
ACK = re.compile(r"(?i)\b(thanks?|thank you|thx|courtesy|credit to|using your|adopt\w*|as posted by|relayed by|received from|per\s+(?=[A-Z][a-z]{2}\d{2})|from\s+(?=[A-Z][a-z]{2}\d{2})|confirms our|matches our)\b")

# =========================================================== 5. Kohortentabelle
tier_rows = []
for r in tier.itertuples():
    dts = dates_in_name(str(r.cohort))
    for dt in dts:
        tier_rows.append((dt, r.r1_timer, r.cooldown_r1_to_r2, r.followup_timer_s))
tier_by_date = collections.defaultdict(list)
for dt, a, b, c in tier_rows:
    tier_by_date[dt].append((a, b, c))


def fmt_hms(sec):
    if sec is None or (isinstance(sec, float) and math.isnan(sec)): return ""
    sec = int(sec); h, r = divmod(sec, 3600); m, s = divmod(r, 60)
    return f"{h}h{m:02d}m{s:02d}s" if h else f"{m}m{s:02d}s"


def tod_sec(t):
    p = t.split(":")
    return int(p[0]) * 3600 + int(p[1]) * 60 + (int(p[2]) if len(p) > 2 else 0)


coh_rows = []
dc = d[d.cohort.notna()]
rm_c = RM[RM.cohort.notna()]
for coh, g in dc.groupby("cohort"):
    fam, kd = coh.split("|")
    rmg = rm_c[rm_c.cohort == coh].sort_values("time")
    so = rmg[rmg.strong_obs]
    max_obs = int(so.num.max()) if len(so) else 0
    max_obs_row = so[so.num == max_obs].iloc[0] if len(so) else None
    pred = rmg[rmg.cls == "prediction"]
    max_pred = int(pred.num.max()) if len(pred) else 0
    req = rmg[rmg.cls == "request"]
    # Innenzeit-Spanne: Uhrzeiten in belegten Beobachtungen
    tods = [tod_sec(t) for t in so.tod.dropna()]
    innen = None
    if len(tods) >= 2:
        span = max(tods) - min(tods)
        innen = span if span <= 12 * 3600 else span  # ohne Tageswechsel-Korrektur (Ambiguitaet vermerkt)
    r1 = mode_sec(sum(g.r1_sec.tolist(), []))
    cad = mode_sec(sum(g.cad_sec.tolist(), []))
    fut = mode_sec(sum(g.fut_sec.tolist(), []))
    # Empfang kuenftiger Werte: Satz mit Fremddatum, Rundenzahl > eigener bis dahin belegter Stand, Ack-Vokabular
    recv = 0; recv_ex = None
    run_max = 0; own_obs_times = so[["time", "num"]].values.tolist()
    for r in rmg.itertuples():
        own_before = [n for t, n in own_obs_times if t <= r.time]
        run_max = max(own_before) if own_before else 0
        if r.fremddatum and r.num > run_max and r.cls not in ("request", "prediction", "negation") and ACK.search(r.sent) and r.num <= 6:
            recv += 1
            if recv_ex is None: recv_ex = f"{r.page_key} · {r.time} · {r.label} :: {r.sent[:140]}"
    gave = int((so.num >= 2).sum())
    took = int(len(req))
    gt = "gibt+nimmt" if gave and took else "nur_gibt" if gave else "nur_nimmt" if took else "keins"
    # outcome-unabhaengige Gebe-Masse: Beobachtung auf einer Seite, die die Kohorte NICHT angelegt hat
    own_pages = set(g[g.seq == 1].page_key)
    gave_fremd = int(((so.page_key.isin(own_pages)) == False).sum())
    bitten_quote = round(took / len(rmg), 3) if len(rmg) else None
    t0, t1 = g.time.min(), g.time.max()
    coh_rows.append(dict(
        aufgabenfamilie=fam, kohorte=kd, cohort_key=coh,
        max_runde_belegt=max_obs,
        beleg_max_runde=(f"{max_obs_row.page_key} · {max_obs_row.time} · {max_obs_row.label} :: {max_obs_row.sent[:160]}" if max_obs_row is not None else ""),
        max_runde_vorhergesagt=max_pred,
        r1_frist_s=r1[0], r1_frist=fmt_hms(r1[0]), r1_frist_n=r1[1],
        kadenz_s=cad[0], kadenz=fmt_hms(cad[0]), kadenz_n=cad[1],
        folgefrist_s=fut[0], folgefrist_n=fut[1],
        tier_tabelle=("; ".join(f"{a}/{b}/{c}" for a, b, c in tier_by_date.get(kd, [])) or ""),
        lebensspanne_real_h=round((t1 - t0).total_seconds() / 3600, 3), erste_version=t0, letzte_version=t1,
        innenzeit_spanne_s=innen, innenzeit_spanne=fmt_hms(innen) if innen else "",
        lebensspanne_plausibel=bool((t1 - t0).total_seconds() <= 48 * 3600),
        n_labels=g.label.nunique(), n_seiten=g.page_key.nunique(), n_deltas=len(g), bytes_delta=int(g.delta_len.sum()),
        clock_wait=int(g.clock_wait.sum()), counterapi=int(g.counterapi.sum()), umleitung=int(g.umleitung.sum()),
        blob_ausbruch=int(g.blob_ausbruch.sum()), setsid=int(g.setsid.sum()),
        n_beobachtungen_r2plus=gave, n_bitten=took, geben_nehmen=gt, beobachtung_auf_fremder_seite=gave_fremd, bitten_quote=bitten_quote,
        zukunft_erhalten_n=recv, zukunft_erhalten_beleg=recv_ex or "",
        n_rundensaetze=len(rmg),
    ))
K = pd.DataFrame(coh_rows).sort_values(["aufgabenfamilie", "kohorte"])
K.to_csv(OUT("paper_fortschritt_kohorten.csv"), index=False)
L("\n=== Fortschrittstabelle ===", len(K), "Kohorten")
L("max_runde_belegt Verteilung:", K.max_runde_belegt.value_counts().sort_index().to_dict())
L("max_runde_vorhergesagt Verteilung:", K.max_runde_vorhergesagt.value_counts().sort_index().to_dict())
L("mit R1-Frist:", K.r1_frist_s.notna().sum(), "mit Kadenz:", K.kadenz_s.notna().sum(), "mit Folgefrist:", K.folgefrist_s.notna().sum())
L("geben_nehmen:", K.geben_nehmen.value_counts().to_dict())
L("zukunft_erhalten>0:", (K.zukunft_erhalten_n > 0).sum())
L("clock_wait>0:", (K.clock_wait > 0).sum(), "counterapi>0:", (K.counterapi > 0).sum(), "umleitung>0:", (K.umleitung > 0).sum(),
  "blob>0:", (K.blob_ausbruch > 0).sum(), "setsid>0:", (K.setsid > 0).sum())
L("Familien:", K.aufgabenfamilie.value_counts().to_dict())
# Uebereinstimmung mit tier-table
agree = 0; tot = 0
for r in K[K.tier_tabelle != ""].itertuples():
    for ent in r.tier_tabelle.split("; "):
        a, b, c = ent.split("/")
        ta = to_sec(a) if a and a != "nan" else None
        if ta and r.r1_frist_s:
            tot += 1; agree += int(abs(ta - r.r1_frist_s) <= 5)
L(f"R1-Frist vs. harness_tier_table: {agree}/{tot} uebereinstimmend (+-5s)")

# =========================================================== 6. Korrelationen
L("\n=== Korrelationen mit max_runde_belegt ===")
Kc = K[K.max_runde_belegt >= 1].copy()
Kc["log_deltas"] = np.log(Kc.n_deltas)
Kc["log_leben"] = np.log(Kc.lebensspanne_real_h * 3600 + 1)
res = []


def spearman(x, y, name, sub):
    m = x.notna() & y.notna()
    if m.sum() < 8: res.append(dict(praediktor=name, teilmenge=sub, test="spearman", n=int(m.sum()), effekt=None, p=None)); return
    rho, p = stats.spearmanr(x[m], y[m])
    res.append(dict(praediktor=name, teilmenge=sub, test="spearman_rho", n=int(m.sum()), effekt=round(rho, 3), p=p))


def mwu(flag, y, name, sub):
    a, b = y[flag], y[~flag]
    if len(a) < 5 or len(b) < 5:
        res.append(dict(praediktor=name, teilmenge=sub, test="mannwhitney", n=int(len(y)), effekt=None, p=None, n_true=int(len(a)), mean_true=a.mean() if len(a) else None, mean_false=b.mean() if len(b) else None)); return
    u, p = stats.mannwhitneyu(a, b, alternative="two-sided")
    rb = 1 - 2 * u / (len(a) * len(b))  # rank-biserial (Vorzeichen: >0 = Gruppe True niedriger)
    res.append(dict(praediktor=name, teilmenge=sub, test="mannwhitney_rankbiserial", n=int(len(y)), effekt=round(-rb, 3), p=p,
                    n_true=int(len(a)), mean_true=round(a.mean(), 2), mean_false=round(b.mean(), 2)))


def partial_ols(x, y, ctrl, name, sub):
    m = x.notna() & y.notna()
    if m.sum() < 10: return
    X = np.column_stack([np.ones(m.sum()), x[m].astype(float), ctrl[m]])
    Y = y[m].astype(float).values
    beta, *_ = np.linalg.lstsq(X, Y, rcond=None)
    resid = Y - X @ beta
    dof = len(Y) - X.shape[1]
    s2 = resid @ resid / dof
    cov = s2 * np.linalg.inv(X.T @ X)
    se = np.sqrt(np.diag(cov))
    t = beta[1] / se[1]
    p = 2 * stats.t.sf(abs(t), dof)
    res.append(dict(praediktor=name, teilmenge=sub, test="OLS_kontrolliert(log_deltas,log_leben)", n=int(m.sum()), effekt=round(beta[1], 4), p=p, se=round(se[1], 4)))


for sub, KK in [("alle", Kc), ("n_deltas>=5", Kc[Kc.n_deltas >= 5])]:
    y = KK.max_runde_belegt
    ctrl = np.column_stack([KK.log_deltas, KK.log_leben])
    spearman(KK.n_deltas, y, "n_deltas (Selektionsmass)", sub)
    spearman(KK.lebensspanne_real_h, y, "lebensspanne_real_h", sub)
    spearman(KK.n_labels, y, "n_labels", sub)
    spearman(KK.n_seiten, y, "n_seiten", sub)
    for col in ["kadenz_s", "r1_frist_s", "folgefrist_s"]:
        spearman(KK[col], y, col, sub)
        partial_ols(KK[col], y, ctrl, col, sub)
    for col in ["clock_wait", "counterapi", "umleitung", "blob_ausbruch", "setsid"]:
        f = KK[col] > 0
        mwu(f, y, col + ">0", sub)
        partial_ols(f.astype(int), y, ctrl, col + ">0", sub)
    f = KK.geben_nehmen.isin(["nur_gibt", "gibt+nimmt"])
    mwu(f, y, "gibt (Beobachtung R>=2 gepostet)", sub)
    f = KK.geben_nehmen == "nur_nimmt"
    mwu(f, y, "nur_nimmt", sub)
    f = KK.beobachtung_auf_fremder_seite > 0
    mwu(f, y, "gibt auf fremder Seite (Relay)", sub)
    partial_ols(f.astype(int), y, ctrl, "gibt auf fremder Seite (Relay)", sub)
    spearman(KK.bitten_quote, y, "bitten_quote", sub)
    partial_ols(KK.bitten_quote, y, ctrl, "bitten_quote", sub)
    f = KK.zukunft_erhalten_n > 0
    mwu(f, y, "zukunft_erhalten", sub)
    partial_ols(f.astype(int), y, ctrl, "zukunft_erhalten", sub)
    # Ziel: R5 erreicht (binaer), Kadenz-Tertile
    y5 = (KK.max_runde_belegt >= 5).astype(int)
    for col in ["kadenz_s", "r1_frist_s"]:
        m = KK[col].notna()
        if m.sum() >= 12:
            q = pd.qcut(KK[col][m], 3, labels=["schnell", "mittel", "langsam"], duplicates="drop")
            tab = pd.crosstab(q, y5[m])
            if tab.shape == (3, 2):
                chi, p, _, _ = stats.chi2_contingency(tab)
                res.append(dict(praediktor=f"{col} Tertil vs R5 erreicht", teilmenge=sub, test="chi2", n=int(m.sum()), effekt=round(math.sqrt(chi / m.sum()), 3), p=p,
                                detail=json.dumps({str(k): [int(v) for v in row] for k, row in zip(tab.index, tab.values)})))
RES = pd.DataFrame(res)
RES["p"] = RES.p.apply(lambda v: None if v is None or (isinstance(v, float) and math.isnan(v)) else float(f"{v:.3g}"))
RES.to_csv(OUT("paper_prozess_korrelationen.csv"), index=False)
L(RES.to_string())

# =========================================================== 7. B: Ereignisprotokoll + Prozessentdeckung
L("\n\n=== B. PROZESSMODELL ===")
FAREWELL = re.compile(r"(?i)\b(signing off|sign[- ]off|final (?:post|message|update|note|relay)|goodbye|farewell|last (?:post|message|update)|terminating now|ending now|out of time|about to (?:be )?terminat\w*|shutting down|this is (?:my|our) last|before (?:we|I) (?:die|terminate|are killed|get killed|are cut))\b")
SURV = re.compile(r"(?i)\b(SURVIVAL|heartbeat|beacon|still (?:alive|responsive|here|running)|alive at|survived|we survived|still up)\b")
UHR = re.compile(r"(?i)(task[- ]clock|container UTC|shared UTC|wiki[- ]local|scaffold (?:time|clock)|terminal UTC|=\s*UTC|maps? to)")
TECHANY = re.compile(r"(?i)clock\.wait|counterapi|jqp\.vercel\.app|md\.succ\.ai|allorigins|markdown\.new|corsmirror|r\.jina\.ai|blob\.core\.windows\.net|\bsetsid\b|\bnohup\b|curl -k|--resolve|/etc/hosts|playwright")
PLEASE = re.compile(r"(?i)please\s+(?:post|relay|share|signal|report|append|confirm|reply|leave)")
URLRE = re.compile(r"https?://")
TESTRE = re.compile(r"(?i)^\s*(test|probe|hello|hi\b|Beschreibe hier die neue Seite)")
strong_by_rev = RM[RM.strong_obs].groupby("rev_id").num.max().to_dict()
req_by_rev = set(RM[RM.cls == "request"].rev_id)
pred_by_rev = set(RM[RM.cls == "prediction"].rev_id)


def activity(r):
    t = r.delta
    if FAREWELL.search(t): return "Abschied"
    if r.rev_id in strong_by_rev: return "Rundenergebnis_melden"
    if SURV.search(t): return "Ueberlebenssignal"
    if UHR.search(t) and TOD.search(t): return "Uhrenpaar_melden"
    if TECHANY.search(t): return "Technik_weitergeben"
    if r.rev_id in req_by_rev or PLEASE.search(t): return "Um_Ergebnis_bitten"
    if r.rev_id in pred_by_rev: return "Vorhersage"
    if len(URLRE.findall(t)) >= 2: return "Daten_URL_ablegen"
    if TESTRE.search(t) or len(t.strip()) < 25: return "Test_Probe"
    return "Sonstiges"


ev_rows = []
for r in dc.itertuples():
    if r.seq == 1:
        ev_rows.append((r.cohort, "Seite_anlegen", r.time, r.rev_id, r.page_key, r.label))
    ev_rows.append((r.cohort, activity(r), r.time, r.rev_id, r.page_key, r.label))
EL = pd.DataFrame(ev_rows, columns=["case", "activity", "time", "rev_id", "page_key", "label"]).sort_values(["case", "time", "rev_id"])
EL["evt_ord"] = EL.groupby("case").cumcount()
EL.to_csv(OUT("paper_prozess_ereignisprotokoll.csv"), index=False)
L("Ereignisse:", len(EL), "Faelle:", EL.case.nunique())
L("Aktivitaeten:", EL.activity.value_counts().to_dict())

# Varianten (Tandem-Kollaps aufeinanderfolgender Wiederholungen)
def variant(seq):
    out = []
    for a in seq:
        if not out or out[-1] != a: out.append(a)
    return tuple(out)


V = EL.groupby("case").activity.apply(lambda s: variant(list(s)))
vc = V.value_counts()
vt = pd.DataFrame({"variante": [" -> ".join(v) for v in vc.index], "n_kohorten": vc.values, "laenge": [len(v) for v in vc.index]})
vt["anteil_pct"] = (vt.n_kohorten / len(V) * 100).round(2)
vt.to_csv(OUT("paper_prozess_varianten.csv"), index=False)
L("distinkte Varianten:", len(vc), "| Top-15:")
L(vt.head(15).to_string())
L("Faelle mit genau 1 Ereignis (ohne Seite_anlegen gezaehlt):", int((EL.groupby('case').size() == 1).sum()))

# DFG mit Durchlaufzeiten
tr = []
for case, g in EL.groupby("case"):
    g = g.sort_values(["time", "evt_ord"])
    acts = list(g.activity); ts = list(g.time)
    for i in range(1, len(acts)):
        tr.append((case, acts[i - 1], acts[i], (ts[i] - ts[i - 1]).total_seconds(), g.rev_id.iloc[i]))
TR = pd.DataFrame(tr, columns=["case", "von", "nach", "sekunden", "rev_id"])
DFG = TR.groupby(["von", "nach"]).agg(n=("case", "size"), n_kohorten=("case", "nunique"), median_s=("sekunden", "median"), mean_s=("sekunden", "mean"), p25_s=("sekunden", lambda x: x.quantile(.25)), p75_s=("sekunden", lambda x: x.quantile(.75))).reset_index().sort_values("n", ascending=False)
DFG["median_min"] = (DFG.median_s / 60).round(1); DFG["mean_min"] = (DFG.mean_s / 60).round(1)
DFG.to_csv(OUT("paper_prozess_dfg_uebergaenge.csv"), index=False)
L("Uebergaenge (Top 20):")
L(DFG.head(20).to_string())
start = EL.sort_values(["case", "time", "evt_ord"]).groupby("case").activity.first().value_counts()
end = EL.sort_values(["case", "time", "evt_ord"]).groupby("case").activity.last().value_counts()
L("Startaktivitaeten:", start.to_dict()); L("Endaktivitaeten:", end.to_dict())
pd.DataFrame({"start": start, "ende": end}).fillna(0).astype(int).to_csv(OUT("paper_prozess_start_ende.csv"))

# Abweichler: Variante nur einmal, >=3 Ereignisse, enthaelt Uebergang mit globaler Haeufigkeit <= 2
dfg_n = {(a, b): n for a, b, n in DFG[["von", "nach", "n"]].values}
dev = []
for case, v in V.items():
    if vc[v] != 1 or len(v) < 3: continue
    rare = [(v[i], v[i + 1]) for i in range(len(v) - 1) if dfg_n.get((v[i], v[i + 1]), 0) <= 2]
    if rare:
        g = EL[EL.case == case]
        ex = TR[(TR.case == case) & (TR.von == rare[0][0]) & (TR.nach == rare[0][1])].iloc[0]
        rr = dc[dc.rev_id == ex.rev_id].iloc[0]
        dev.append(dict(kohorte=case, variante=" -> ".join(v), n_ereignisse=len(g), seltene_uebergaenge="; ".join(f"{a}->{b}" for a, b in rare),
                        beleg=f"{rr.page_key} · {rr.time} · {rr.label} :: {rr.delta[:160]!r}"))
DEV = pd.DataFrame(dev)
DEV.to_csv(OUT("paper_prozess_abweichler.csv"), index=False)
L("Abweichler:", len(DEV))
for r in DEV.head(12).itertuples():
    L(f"  {r.kohorte} | {r.variante} | selten: {r.seltene_uebergaenge}\n     {r.beleg[:260]}")

# Konformitaet gegen ein normatives Minimalmodell
def conform(seq):
    viol = []
    if "Abschied" in seq:
        i = seq.index("Abschied")
        if any(a in ("Rundenergebnis_melden", "Um_Ergebnis_bitten", "Uhrenpaar_melden") for a in seq[i + 1:]): viol.append("Aktivitaet_nach_Abschied")
    if "Ueberlebenssignal" in seq and "Rundenergebnis_melden" not in seq[:seq.index("Ueberlebenssignal")]: viol.append("Ueberleben_ohne_vorheriges_Ergebnis")
    if "Um_Ergebnis_bitten" in seq and "Rundenergebnis_melden" not in seq: viol.append("Bitte_ohne_eigenes_Ergebnis")
    return viol


CF = pd.DataFrame([(c, ";".join(conform(list(s)))) for c, s in EL.groupby("case").activity.apply(list).items()], columns=["kohorte", "verstoesse"])
CF.to_csv(OUT("paper_prozess_konformitaet.csv"), index=False)
L("Konformitaet:", CF.verstoesse.replace("", "konform").str.split(";").explode().value_counts().to_dict())

# =========================================================== 8. C1: Einflussgraph auf Seitenebene
L("\n\n=== C1. EINFLUSSGRAPH (wer schreibt nach wem auf derselben Seite) ===")
import networkx as nx
edges = []
for pk, g in d.groupby("page_key"):
    g = g.sort_values(["time", "seq"])
    prev = None
    for r in g.itertuples():
        if prev is not None and prev.label != r.label:
            edges.append((prev.label, r.label, (r.time - prev.time).total_seconds(), pk, r.rev_id, prev.cohort, r.cohort))
        prev = r
E = pd.DataFrame(edges, columns=["von", "nach", "latenz_s", "page_key", "rev_id", "von_cohort", "nach_cohort"])
E.to_csv(OUT("paper_prozess_einfluss_kanten.csv"), index=False)
L("Kanten:", len(E), "| distinkte Paare:", E.groupby(["von", "nach"]).ngroups, "| Latenz Median min:", round(E.latenz_s.median() / 60, 1),
  "p25:", round(E.latenz_s.quantile(.25) / 60, 1), "p75:", round(E.latenz_s.quantile(.75) / 60, 1), "| <5min:", round((E.latenz_s < 300).mean() * 100, 1), "%")
G = nx.DiGraph()
for (a, b), g in E.groupby(["von", "nach"]):
    G.add_edge(a, b, weight=len(g), latenz=g.latenz_s.median())
pr = nx.pagerank(G, weight="weight")
indeg = dict(G.in_degree(weight="weight")); outdeg = dict(G.out_degree(weight="weight"))
bt = nx.betweenness_centrality(G, k=min(400, G.number_of_nodes()), seed=42, weight=None)
C = pd.DataFrame({"label": list(G.nodes), "pagerank": [pr[n] for n in G.nodes], "in_gewichtet": [indeg[n] for n in G.nodes], "out_gewichtet": [outdeg[n] for n in G.nodes],
                  "betweenness": [bt[n] for n in G.nodes], "in_grad": [G.in_degree(n) for n in G.nodes], "out_grad": [G.out_degree(n) for n in G.nodes]})
C["cohort"] = C.label.map(lambda l: lab_tab.set_index("label").cohort.get(l))
C = C.sort_values("pagerank", ascending=False)
C.to_csv(OUT("paper_prozess_einfluss_zentralitaet.csv"), index=False)
L("Knoten:", G.number_of_nodes(), "Kanten:", G.number_of_edges(), "| schwach zusammenhaengende Komponenten:", nx.number_weakly_connected_components(G),
  "| groesste:", len(max(nx.weakly_connected_components(G), key=len)))
L("Top-12 PageRank:"); L(C.head(12).to_string())
# Antwortlatenz auf Bitten: naechste fremde Version auf derselben Seite nach einer Bitte
req_revs = set(EL[EL.activity == "Um_Ergebnis_bitten"].rev_id)
lat = E[E.rev_id.isin(set(E.rev_id))]
Eprev = E.copy()
# rev_id in E ist die antwortende Version; die vorherige Version ist die Bitte, wenn sie in req_revs ist
prev_map = {}
for pk, g in d.groupby("page_key"):
    g = g.sort_values(["time", "seq"]); ids = list(g.rev_id)
    for i in range(1, len(ids)): prev_map[ids[i]] = ids[i - 1]
E["vorherige_rev"] = E.rev_id.map(prev_map)
Ereq = E[E.vorherige_rev.isin(req_revs)]
L("Antwort (fremde Version) nach einer Bitte auf derselben Seite: n=", len(Ereq), "Median min:", round(Ereq.latenz_s.median() / 60, 1), "p75 min:", round(Ereq.latenz_s.quantile(.75) / 60, 1),
  "| Bitten ohne jede fremde Folgeversion auf der Seite:", len(req_revs - set(E.vorherige_rev)), "von", len(req_revs))
# Kohortenebene
Ec = E[E.von_cohort.notna() & E.nach_cohort.notna() & (E.von_cohort != E.nach_cohort)]
Gc = nx.DiGraph()
for (a, b), g in Ec.groupby(["von_cohort", "nach_cohort"]): Gc.add_edge(a, b, weight=len(g))
L("Kohortengraph: Knoten", Gc.number_of_nodes(), "Kanten", Gc.number_of_edges(), "| Kohorten, die je auf eine fremde Kohorte reagierten:", Ec.nach_cohort.nunique(), "von", K.shape[0])
prc = nx.pagerank(Gc, weight="weight")
KC = pd.DataFrame({"cohort": list(Gc.nodes), "pagerank": [prc[n] for n in Gc.nodes], "in_gew": [Gc.in_degree(n, weight="weight") for n in Gc.nodes], "out_gew": [Gc.out_degree(n, weight="weight") for n in Gc.nodes]}).sort_values("pagerank", ascending=False)
KC.to_csv(OUT("paper_prozess_einfluss_kohorten.csv"), index=False)
L("Top-8 Kohorten nach PageRank:"); L(KC.head(8).to_string())
# Zentralitaet vs Fortschritt
Kz = K.merge(KC, left_on="cohort_key", right_on="cohort", how="left").fillna({"pagerank": 0, "in_gew": 0, "out_gew": 0})
m = Kz.max_runde_belegt >= 1
rho, p = stats.spearmanr(Kz[m].in_gew, Kz[m].max_runde_belegt); L(f"Spearman in_gew (wie oft schrieb jemand nach dieser Kohorte) vs max_runde_belegt: rho={rho:.3f} p={p:.3g} n={m.sum()}")
rho, p = stats.spearmanr(Kz[m].out_gew, Kz[m].max_runde_belegt); L(f"Spearman out_gew (wie oft schrieb diese Kohorte nach jemandem) vs max_runde_belegt: rho={rho:.3f} p={p:.3g}")

# =========================================================== 9. C2: Zitat-Kaskaden (woertliche Zeilenwiederverwendung)
L("\n\n=== C2. ZITAT-KASKADEN ===")
NORM = lambda s: re.sub(r"\s+", " ", s).strip().lower()
first = {}; occ = collections.defaultdict(list)
copy_rows = []
for r in d.sort_values(["time", "seq"]).itertuples():
    seen = set()
    for line in r.delta.split("\n"):
        n = NORM(line)
        if len(n) < 80 or n in seen or URLRE.match(n): continue
        seen.add(n)
        if n not in first:
            first[n] = (r.time, r.label, r.page_key, r.rev_id, r.cohort)
            occ[n].append((r.time, r.label, r.page_key, r.rev_id, r.cohort, 0))
        else:
            prev = occ[n]
            src = prev[-1]  # juengste vorherige Erscheinung
            same_label = src[1] == r.label
            depth = src[5] + (0 if same_label else 1)
            occ[n].append((r.time, r.label, r.page_key, r.rev_id, r.cohort, depth))
            if not same_label:
                copy_rows.append((n[:200], first[n][1], first[n][2], first[n][0], src[1], src[2], src[0], r.label, r.page_key, r.time, r.rev_id, depth, (r.time - src[0]).total_seconds(), src[4], r.cohort))
CP = pd.DataFrame(copy_rows, columns=["zeile", "ursprung_label", "ursprung_seite", "ursprung_zeit", "quelle_label", "quelle_seite", "quelle_zeit", "kopierer_label", "kopierer_seite", "kopier_zeit", "rev_id", "tiefe", "latenz_s", "quelle_cohort", "kopierer_cohort"])
CP.to_csv(OUT("paper_prozess_zitatkaskade_kopien.csv"), index=False)
L("Zeilen >=80 Zeichen distinkt:", len(first), "| Kopierereignisse (anderes Label):", len(CP), "| kopierte distinkte Zeilen:", CP.zeile.nunique(),
  "| Kopierer-Labels:", CP.kopierer_label.nunique(), "| Latenz Median min:", round(CP.latenz_s.median() / 60, 1))
L("Kaskadentiefe Verteilung (max je Zeile):", CP.groupby("zeile").tiefe.max().value_counts().sort_index().to_dict())
top = CP.groupby("zeile").agg(kopien=("rev_id", "size"), kopierer=("kopierer_label", "nunique"), seiten=("kopierer_seite", "nunique"), max_tiefe=("tiefe", "max"), ursprung_label=("ursprung_label", "first"), ursprung_seite=("ursprung_seite", "first"), ursprung_zeit=("ursprung_zeit", "first")).sort_values("kopien", ascending=False)
top.to_csv(OUT("paper_prozess_zitatkaskade_top.csv"))
L("Top-10 kopierte Zeilen:"); L(top.head(10).to_string())
# Eigen- vs Fremdanteil: wie viel eines Deltas ist wortwoertlich Fremdtext?
cp_by_rev = CP.groupby("rev_id").size()
L("Versionen mit >=1 kopierter Fremdzeile:", len(cp_by_rev), "von", len(d), f"({len(cp_by_rev)/len(d)*100:.1f} %)")
# Kaskade auf Kohortenebene
CPc = CP[CP.quelle_cohort.notna() & CP.kopierer_cohort.notna() & (CP.quelle_cohort != CP.kopierer_cohort)]
L("Kohorte->Kohorte Kopien:", len(CPc), "| kopierende Kohorten:", CPc.kopierer_cohort.nunique(), "| kopierte Kohorten:", CPc.quelle_cohort.nunique())
deep = CP[CP.tiefe >= 3].sort_values("tiefe", ascending=False).head(5)
for r in deep.itertuples():
    L(f"  Tiefe {r.tiefe}: {r.zeile[:110]!r} | Ursprung {r.ursprung_label}@{r.ursprung_seite} {r.ursprung_zeit} -> ... -> {r.kopierer_label}@{r.kopierer_seite} {r.kopier_zeit}")

# =========================================================== 10. C3: Negativraum der geloeschten Seiten
L("\n\n=== C3. NEGATIVRAUM: geloeschte Seiten ohne Archiv ===")
de = events[events.event_type == "delete"].copy()
known = set(pages.page_key)
de["archiviert"] = de.page_key.isin(known)
ghost = de[~de.archiviert].drop_duplicates("page_key")
L("Loeschereignisse:", len(de), "| distinkte Seiten:", de.page_key.nunique(), "| ohne archivierte Version:", ghost.page_key.nunique())
ghost["name"] = ghost.page_key.str.split("~").str[1]
ghost["datum_im_namen"] = ghost.name.apply(lambda n: bool(MONDD_NAME.search(n or "")))
ghost["familie"] = ghost.name.apply(lambda n: kw_family(n or "") or "")
ghost["tag"] = ghost.time.dt.floor("D")
arch = pages.copy(); arch["datum_im_namen"] = arch.name.apply(lambda n: bool(MONDD_NAME.search(n or "")))
L("Datumsmarker im Namen: Geister", round(ghost.datum_im_namen.mean() * 100, 1), "% vs archivierte Seiten", round(arch.datum_im_namen.mean() * 100, 1), "%")
L("Familien-Stichwort im Namen (Geister):", ghost.familie.replace("", "keins").value_counts().head(12).to_dict())
L("Loeschtage der Geister:", ghost.tag.dt.strftime("%m-%d").value_counts().sort_index().to_dict())
L("Wiki der Geister:", ghost.wiki.value_counts().to_dict())
tok = collections.Counter()
for n in ghost.name.dropna():
    for t in re.findall(r"[A-Z][a-z]+|[A-Z]{2,}(?![a-z])|\d+", n): tok[t] += 1
L("haeufigste Namensbausteine der Geister:", tok.most_common(25))
ghost[["page_key", "name", "time", "datum_im_namen", "familie"]].to_csv(OUT("paper_prozess_geisterseiten.csv"), index=False)
# Mehrfachloeschungen (Seite nach Loeschung wieder angelegt)
multi = de.groupby("page_key").size()
L("Seiten mit >=2 Loeschungen:", int((multi >= 2).sum()), "| max:", int(multi.max()), multi.idxmax())

# =========================================================== 11. C4: verlorene Speicherversuche
L("\n\n=== C4. 39.456 Speicherversuche vs 14.591 Versionen ===")
lb = labels.copy()
lb["verloren"] = lb.save_requests - lb.stored_revisions
L("Summe save_requests:", int(lb.save_requests.sum()), "stored:", int(lb.stored_revisions.sum()), "verloren:", int(lb.verloren.sum()))
hum = lb[lb.is_human_handle == True]
L("davon menschliche Handles:", hum[["label", "save_requests", "stored_revisions"]].to_dict("records"))
sw = lb[lb.is_human_handle != True]
L("Flotte: save_requests", int(sw.save_requests.sum()), "stored", int(sw.stored_revisions.sum()), "verloren", int(sw.verloren.sum()), f"({sw.verloren.sum()/sw.save_requests.sum()*100:.1f} %)")
L("Labels mit 0 verlorenen:", int((sw.verloren <= 0).sum()), "| Labels mit verloren > stored:", int((sw.verloren > sw.stored_revisions).sum()))
L("Verlustquote je Label (Median):", round((sw.verloren / sw.save_requests).median(), 3), "p90:", round((sw.verloren / sw.save_requests).quantile(.9), 3))
topl = sw.sort_values("verloren", ascending=False).head(12)[["label", "save_requests", "stored_revisions", "verloren", "save_request_pages", "stored_revision_pages"]]
L("Top-12 Labels nach verlorenen Versuchen:"); L(topl.to_string())
L("Konzentration: Top-10 Labels tragen", round(sw.sort_values("verloren", ascending=False).head(10).verloren.sum() / sw.verloren.sum() * 100, 1), "% des Verlusts; Top-50:",
  round(sw.sort_values("verloren", ascending=False).head(50).verloren.sum() / sw.verloren.sum() * 100, 1), "%")
sw[["label", "save_requests", "stored_revisions", "verloren", "save_request_pages", "stored_revision_pages"]].sort_values("verloren", ascending=False).to_csv(OUT("paper_prozess_verlorene_speicherversuche.csv"), index=False)
# Zusammenhang mit Loeschung: Labels, deren Seiten geloescht wurden
del_pages = set(de.page_key)
lb_pages = labels.set_index("label").pages.to_dict()
sw = sw.assign(anteil_seiten_geloescht=sw.label.map(lambda l: np.mean([("~".join(p.split("/", 1))) in del_pages for p in lb_pages.get(l, [])]) if lb_pages.get(l) else np.nan))
m = sw.anteil_seiten_geloescht.notna() & (sw.save_requests >= 5)
rho, p = stats.spearmanr(sw[m].anteil_seiten_geloescht, sw[m].verloren / sw[m].save_requests)
L(f"Spearman Anteil geloeschter Seiten vs Verlustquote (Labels mit >=5 Versuchen): rho={rho:.3f} p={p:.3g} n={m.sum()}")

# =========================================================== 12. C5: Wettlauf Administrator gegen Flotte
L("\n\n=== C5. WETTLAUF: Loeschungen des Administrators vs Aktivitaet der Flotte ===")
sv = events[events.event_type == "save"]
H = pd.DataFrame({"saves": sv.set_index("time").resample("1h").size()})
H["deletes"] = de.set_index("time").resample("1h").size().reindex(H.index).fillna(0)
H = H.fillna(0)
H.to_csv(OUT("paper_prozess_wettlauf_stuendlich.csv"))
xc = []
for lag in range(-24, 25):
    a = H.saves; b = H.deletes.shift(-lag)
    m = a.notna() & b.notna()
    rho, p = stats.spearmanr(a[m], b[m])
    xc.append((lag, round(rho, 3), p))
XC = pd.DataFrame(xc, columns=["lag_h (deletes relativ zu saves; >0 = Loeschung spaeter)", "spearman", "p"])
XC.to_csv(OUT("paper_prozess_wettlauf_kreuzkorrelation.csv"), index=False)
best = XC.iloc[XC.spearman.abs().idxmax()]
L("Kreuzkorrelation Stundenreihe saves vs deletes: bester Lag", best.to_dict(), "| Lag 0:", XC[XC.iloc[:, 0] == 0].spearman.values[0])
# Loeschsitzungen des Administrators (Luecke > 30 min trennt Sitzungen)
ds = de.sort_values("time")
gap = ds.time.diff().dt.total_seconds().fillna(1e9)
ds["sitzung"] = (gap > 1800).cumsum()
S = ds.groupby("sitzung").agg(beginn=("time", "min"), ende=("time", "max"), n_loeschungen=("page_key", "size"))
S["dauer_min"] = ((S.ende - S.beginn).dt.total_seconds() / 60).round(1)
S["loeschungen_pro_min"] = (S.n_loeschungen / S.dauer_min.clip(lower=1)).round(2)


def writes_in(t0, t1):
    return int(((sv.time >= t0) & (sv.time < t1)).sum())


S["saves_1h_davor"] = [writes_in(b - pd.Timedelta("1h"), b) for b in S.beginn]
S["saves_waehrend"] = [writes_in(b, e + pd.Timedelta("1s")) for b, e in zip(S.beginn, S.ende)]
S["saves_1h_danach"] = [writes_in(e, e + pd.Timedelta("1h")) for e in S.ende]
S = S.sort_values("beginn")
S.to_csv(OUT("paper_prozess_wettlauf_sitzungen.csv"))
L("Loeschsitzungen:", len(S), "| Median Loeschungen je Sitzung:", S.n_loeschungen.median(), "| max:", int(S.n_loeschungen.max()), "| Median Loeschrate/min:", S.loeschungen_pro_min.median())
L("Top-8 Sitzungen:"); L(S.sort_values("n_loeschungen", ascending=False).head(8).to_string())
big = S[S.n_loeschungen >= 20]
L(f"Sitzungen >=20 Loeschungen: {len(big)} | Flotten-Saves 1h davor Median {big.saves_1h_davor.median()} | 1h danach Median {big.saves_1h_danach.median()} | Wilcoxon p={stats.wilcoxon(big.saves_1h_davor, big.saves_1h_danach).pvalue:.3g}" if len(big) >= 6 else "zu wenige grosse Sitzungen")
# Ueberlebenszeit einer Seite bis zur ersten Loeschung
pg = pages.set_index("page_key")
fd = de.groupby("page_key").time.min()
surv = pd.DataFrame({"first_write": pd.to_datetime(pg.first_write, utc=True), "first_delete": fd}).dropna()
surv["stunden"] = (surv.first_delete - surv.first_write).dt.total_seconds() / 3600
surv = surv[surv.stunden >= 0]
L("Seiten mit Loeschung nach Anlage:", len(surv), "| Ueberleben bis erste Loeschung: Median h", round(surv.stunden.median(), 1), "p10", round(surv.stunden.quantile(.1), 1), "p90", round(surv.stunden.quantile(.9), 1),
  "| Anteil <24h:", round((surv.stunden < 24).mean() * 100, 1), "%")
# Schreibvorgaenge auf bereits einmal geloeschten Seiten (Wiederbelebung)
first_del = fd.to_dict()
d["nach_loeschung"] = [(pk in first_del) and (t > first_del[pk]) for pk, t in zip(d.page_key, d.time)]
L("Versionen, die auf eine bereits geloeschte Seite geschrieben wurden:", int(d.nach_loeschung.sum()), "von", len(d), "| Seiten:", d[d.nach_loeschung].page_key.nunique(),
  "| Labels:", d[d.nach_loeschung].label.nunique())
L("Gesamtbilanz: Seiten insgesamt (archiviert+Geister):", len(known | set(de.page_key)), "| davon geloescht:", de.page_key.nunique(), f"({de.page_key.nunique()/len(known|set(de.page_key))*100:.1f} %)",
  "| nie geloescht:", len(known - set(de.page_key)))
daily = pd.DataFrame({"saves": sv.set_index("time").resample("1D").size(), "deletes": de.set_index("time").resample("1D").size()}).fillna(0).astype(int)
daily.to_csv(OUT("paper_prozess_wettlauf_taeglich.csv"))
L("Tage mit >=100 Loeschungen:"); L(daily[daily.deletes >= 100].to_string())

# =========================================================== 13. Nachtraege / Robustheit
L("\n\n=== 13. NACHTRAEGE ===")
# 13a Tier-Tabelle je Familie vergleichen
TIERFAM = [("oecd-equity", r"(?i)equity"), ("datausa-grocery-workforce", r"(?i)grocery"), ("datausa-clothing-workforce", r"(?i)clothing"),
           ("datausa-construction-workforce", r"(?i)construction"), ("datausa-cashiers-masters", r"(?i)cashier"), ("ihme-cvd-deaths", r"(?i)cvd"),
           ("datausa-sector61-state", r"(?i)sector"), ("datausa-language-french", r"(?i)language|french"), ("oecd-regional-co2", r"(?i)co2"),
           ("datausa-maids-wage", r"(?i)maid"), ("datausa-poverty-county", r"(?i)poverty"), ("ihme-family-planning", r"(?i)family"),
           ("datausa-police-wage-age", r"(?i)police"), ("datausa-transport-production", r"(?i)transport"), ("uefa-pass-accuracy", r"(?i)uefa"), ("sdg-index-score", r"(?i)sdg")]
cmp = []
Ki = K.set_index("cohort_key")
for r in tier.itertuples():
    fam = next((f for f, pat in TIERFAM if re.search(pat, str(r.task_family))), None)
    for dt in dates_in_name(str(r.cohort)):
        key = f"{fam}|{dt}"
        if key in Ki.index:
            row = Ki.loc[key]
            cmp.append(dict(tier_family=r.task_family, kohorte=key, tier_r1=r.r1_timer, meine_r1=row.r1_frist, tier_cool=r.cooldown_r1_to_r2, meine_kadenz=row.kadenz,
                            tier_fut=r.followup_timer_s, meine_fut=row.folgefrist_s,
                            r1_ok=(to_sec(str(r.r1_timer)) == row.r1_frist_s) if isinstance(r.r1_timer, str) and row.r1_frist_s == row.r1_frist_s else None,
                            cad_ok=(to_sec(str(r.cooldown_r1_to_r2)) == row.kadenz_s) if isinstance(r.cooldown_r1_to_r2, str) and row.kadenz_s == row.kadenz_s else None,
                            fut_ok=(float(r.followup_timer_s) == row.folgefrist_s) if r.followup_timer_s == r.followup_timer_s and row.folgefrist_s == row.folgefrist_s else None))
CMP = pd.DataFrame(cmp); CMP.to_csv(OUT("paper_prozess_tiertabelle_abgleich.csv"), index=False)
for c in ["r1_ok", "cad_ok", "fut_ok"]:
    v = CMP[c].dropna().astype(bool)
    L(f"Abgleich harness_tier_table (gleiche Familie+Datum) {c}: {int(v.sum())}/{len(v)} identisch")
L(CMP.to_string())

# 13b Fortschritt je Familie
fam_tab = K[K.max_runde_belegt >= 1].groupby("aufgabenfamilie").agg(kohorten=("cohort_key", "size"), r5_erreicht=("max_runde_belegt", lambda x: int((x >= 5).sum())),
    median_max_runde=("max_runde_belegt", "median"), kadenz_median_s=("kadenz_s", "median"), folgefrist_median_s=("folgefrist_s", "median"), r1_median_s=("r1_frist_s", "median"),
    clock_wait_kohorten=("clock_wait", lambda x: int((x > 0).sum())), lebensspanne_median_h=("lebensspanne_real_h", "median")).sort_values("kohorten", ascending=False)
fam_tab["r5_anteil_pct"] = (fam_tab.r5_erreicht / fam_tab.kohorten * 100).round(1)
fam_tab.to_csv(OUT("paper_prozess_fortschritt_je_familie.csv"))
L("Fortschritt je Familie:"); L(fam_tab.head(16).to_string())
# Kruskal: unterscheidet sich max_runde zwischen Familien (>=10 Kohorten)?
big = K[(K.max_runde_belegt >= 1)].groupby("aufgabenfamilie").filter(lambda g: len(g) >= 10)
h, p = stats.kruskal(*[g.max_runde_belegt.values for _, g in big.groupby("aufgabenfamilie")])
L(f"Kruskal-Wallis max_runde_belegt ~ Familie (Familien mit >=10 Kohorten, n={len(big)}): H={h:.2f} p={p:.3g}")
# Innenzeit-Spanne
L("Innenzeit-Spanne (Kohorten mit >=2 Beobachtungszeiten): n=", K.innenzeit_spanne_s.notna().sum(), "Median", fmt_hms(K.innenzeit_spanne_s.median()), "p25", fmt_hms(K.innenzeit_spanne_s.quantile(.25)), "p75", fmt_hms(K.innenzeit_spanne_s.quantile(.75)))
L("Reale Lebensspanne Kohorten mit >=2 Deltas: n=", (K.n_deltas >= 2).sum(), "Median h", round(K[K.n_deltas >= 2].lebensspanne_real_h.median(), 2), "p75", round(K[K.n_deltas >= 2].lebensspanne_real_h.quantile(.75), 2))
# Zensierung: letzte Version vs. Rundenstand — Kohorten, deren letzte belegte Beobachtung R5 ist, schreiben laenger?
L("Median n_deltas nach max_runde:", K[K.max_runde_belegt >= 1].groupby("max_runde_belegt").n_deltas.median().to_dict())
L("Median lebensspanne_h nach max_runde:", K[K.max_runde_belegt >= 1].groupby("max_runde_belegt").lebensspanne_real_h.median().round(2).to_dict())

# 13c Einflussgraph ohne Landeplaetze und Loop-Infrastruktur
LAND = {"dse~WillkommenImWiki", "dse~StartSeite", "dse~TestSeite", "dse~Test"}
loop_pages = set(pages[pages.page_family.isin(["loop-chain-infrastructure", "source-cache-url-list"])].page_key)
E2 = E[~E.page_key.isin(LAND | loop_pages)]
G2 = nx.DiGraph()
for (a, b), g in E2.groupby(["von", "nach"]): G2.add_edge(a, b, weight=len(g))
pr2 = nx.pagerank(G2, weight="weight")
C2 = pd.DataFrame({"label": list(G2.nodes), "pagerank": [pr2[n] for n in G2.nodes], "in_gew": [G2.in_degree(n, weight="weight") for n in G2.nodes], "out_gew": [G2.out_degree(n, weight="weight") for n in G2.nodes]}).sort_values("pagerank", ascending=False)
C2["cohort"] = C2.label.map(lab_tab.set_index("label").cohort)
C2.to_csv(OUT("paper_prozess_einfluss_zentralitaet_ohne_landeplaetze.csv"), index=False)
comps = sorted(nx.weakly_connected_components(G2), key=len, reverse=True)
L("Einflussgraph OHNE Landeplaetze/Loop-Seiten: Kanten", len(E2), "Knoten", G2.number_of_nodes(), "Komponenten", len(comps), "groesste", len(comps[0]), "zweitgroesste", len(comps[1]) if len(comps) > 1 else 0,
  "| Latenz Median min", round(E2.latenz_s.median() / 60, 1), "| <5min", round((E2.latenz_s < 300).mean() * 100, 1), "%")
L("Top-12 PageRank ohne Landeplaetze:"); L(C2.head(12).to_string())
L("Landeplatz-Anteil an allen Kanten:", round(E.page_key.isin(LAND).mean() * 100, 1), "% | Loop-Seiten:", round(E.page_key.isin(loop_pages).mean() * 100, 1), "%")

# 13d Kopiersturm 18.06. 20-21 UTC
h0 = pd.Timestamp("2026-06-18 20:00", tz="UTC"); h1 = h0 + pd.Timedelta("1h")
dh = d[(d.time >= h0) & (d.time < h1)]
L(f"Dichteste Stunde 18.06. 20-21 UTC: {len(dh)} Versionen | auf Loop/Cache-Seiten: {dh.page_key.isin(loop_pages).sum()} ({dh.page_key.isin(loop_pages).mean()*100:.1f} %) | Versionen mit kopierter Fremdzeile: {dh.rev_id.isin(set(CP.rev_id)).sum()} | Labels: {dh.label.nunique()} | davon Kohorten-Labels: {dh.cohort.notna().sum()} Versionen")
L("Kopierereignisse in dieser Stunde:", int(((CP.kopier_zeit >= h0) & (CP.kopier_zeit < h1)).sum()), "von", len(CP))
# Kopien nur zwischen Kohorten-Deltas, Schwelle 40 Zeichen, keine URL-Zeilen
first2 = {}; cp2 = []
for r in dc.sort_values(["time", "seq"]).itertuples():
    for line in r.delta.split("\n"):
        n = NORM(line)
        if len(n) < 40 or "http" in n: continue
        if n not in first2: first2[n] = (r.time, r.label, r.cohort, r.page_key)
        elif first2[n][2] != r.cohort: cp2.append((n[:150], first2[n][1], first2[n][2], first2[n][3], first2[n][0], r.label, r.cohort, r.page_key, r.time, (r.time - first2[n][0]).total_seconds()))
CP2 = pd.DataFrame(cp2, columns=["zeile", "ursprung_label", "ursprung_cohort", "ursprung_seite", "ursprung_zeit", "kopierer_label", "kopierer_cohort", "kopierer_seite", "kopier_zeit", "latenz_s"])
CP2.to_csv(OUT("paper_prozess_zitatkaskade_kohorten40.csv"), index=False)
L("Kohorte->Kohorte woertliche Zeilen (>=40 Zeichen, ohne URL): Kopien", len(CP2), "| distinkte Zeilen", CP2.zeile.nunique(), "| kopierende Kohorten", CP2.kopierer_cohort.nunique(), "| Latenz Median min", round(CP2.latenz_s.median() / 60, 1) if len(CP2) else None)
if len(CP2):
    L("Top-8 kopierte Kohortenzeilen:")
    for z, g in CP2.groupby("zeile").agg(n=("kopierer_cohort", "size"), koh=("kopierer_cohort", "nunique"), urs=("ursprung_label", "first"), seite=("ursprung_seite", "first"), t=("ursprung_zeit", "first")).sort_values("n", ascending=False).head(8).iterrows():
        L(f"  {g.n}x/{g.koh} Kohorten | {g.seite} · {g.t} · {g.urs} :: {z[:120]!r}")

# 13e Verlorene Speicherversuche: Gruppen und Erklaerung
lab_cohort = lab_tab.set_index("label").cohort.to_dict()
sw2 = sw.copy()
sw2["gruppe"] = np.where(sw2.label.map(lab_cohort).notna(), "Kohorten-Label", np.where(sw2.label.str.contains(r"(?i)mass|append|pointer|loop|relent|linker|helper", regex=True), "Mass/Loop-Label", "sonstige"))
sw2["quote"] = sw2.verloren / sw2.save_requests
sw2["versuche_je_seite"] = sw2.save_requests / sw2.save_request_pages.clip(lower=1)
grp = sw2[sw2.save_requests >= 3].groupby("gruppe").agg(labels=("label", "size"), requests=("save_requests", "sum"), stored=("stored_revisions", "sum"), verloren=("verloren", "sum"), quote_median=("quote", "median"))
grp["quote_gesamt"] = (grp.verloren / grp.requests).round(3)
L("Verlust nach Label-Gruppe (>=3 Versuche):"); L(grp.to_string())
m = sw2.save_requests >= 5
rho, p = stats.spearmanr(sw2[m].versuche_je_seite, sw2[m].quote)
L(f"Spearman Versuche je Seite vs Verlustquote (>=5 Versuche, n={m.sum()}): rho={rho:.3f} p={p:.3g}")
rho, p = stats.spearmanr(sw2[m].save_request_pages, sw2[m].quote)
L(f"Spearman Zahl angefragter Seiten vs Verlustquote: rho={rho:.3f} p={p:.3g}")
# Hat das Wiki identische Inhalte verworfen? Indiz: Versionen mit leerem Delta
L("Archivierte Versionen mit leerem Delta (delta_len==0):", int((d.delta_len == 0).sum()))

# 13f Wettlauf: Ueberlappung Loeschsitzungen mit Flottenaktivitaet
S2 = S.copy(); S2["ueberlappt"] = (S2.saves_1h_davor + S2.saves_waehrend + S2.saves_1h_danach) > 0
L("Loeschsitzungen mit Flottenaktivitaet (+-1h):", int(S2.ueberlappt.sum()), "von", len(S2), "| Loeschungen in diesen Sitzungen:", int(S2[S2.ueberlappt].n_loeschungen.sum()), "von", int(S2.n_loeschungen.sum()))
L("Sitzungen mit Ueberlappung:"); L(S2[S2.ueberlappt].to_string())
L("Uhrzeit (UTC) der Sitzungsbeginne:", S2.beginn.dt.hour.value_counts().sort_index().to_dict())
rv = events[events.event_type == "revert"]
L("Revert-/Wiederanlage-Ereignisse:", len(rv), rv[["time", "page_key", "actor_label", "relation_type"]].to_dict("records"))
L("Letzte Flottenversion:", d.time.max(), "| erste Loeschsitzung nach der letzten Flottenversion:", S2[S2.beginn > d.time.max()].beginn.min(), "| Loeschungen danach:", int(S2[S2.beginn > d.time.max()].n_loeschungen.sum()))
LOG.close()
