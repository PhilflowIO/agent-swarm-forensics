#!/usr/bin/env python3
"""bi05 — Sammelbild-Schaetzer (Occupancy) auf der NAMENSMENGE DES BETREIBERLOGS.

Wiederholt exakt das Verfahren aus paper/main.tex:149-158 (N=365 Kalendertoepfe,
E[D]=N(1-(1-1/N)^n), Inversion an beobachtetem D, Intervall per Monte Carlo),
aber mit der groesseren Namensmenge des Requestlogs statt der 3103 Export-Labels.
Markerdefinition und Namenszerlegung uebernommen aus scripts/51_prozess.py:50-52,:115.

Aufruf:
  analyse/.venv/bin/python analyse/scripts/betreiberlog/bi05_population.py
Ausgabe: analyse/artefakte/betreiberlog_identitaet/bi05_population.csv / .json
"""
import csv, collections, datetime as dt, gzip, json, math, os, re
import numpy as np

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NORM = os.path.join(BASE, "data", "betreiberlogs", "normalisiert")
ART  = os.path.join(BASE, "artefakte", "betreiberlog_identitaet")
MON = "(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
MONDD_NAME = re.compile(rf"({MON})(\d{{2}})(?!\d)")
TAGE = {"Jan": 31, "Feb": 29, "Mar": 31, "Apr": 30, "May": 31, "Jun": 30,
        "Jul": 31, "Aug": 31, "Sep": 30, "Oct": 31, "Nov": 30, "Dec": 31}
KUERZEL = {v: k for k, v in enumerate(["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                                       "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)}
N = 365
RNG = np.random.default_rng(20260917)


def marken(name):
    out = []
    for m in MONDD_NAME.finditer(name or ""):
        mo, d = m.group(1), int(m.group(2))
        if 1 <= d <= TAGE[mo]:
            out.append(mo + m.group(2))
    return out


def invert(D):
    if D >= N:
        return float("inf")
    lo, hi = 1.0, 1e6
    for _ in range(200):
        mid = (lo + hi) / 2
        if N * (1 - (1 - 1 / N) ** mid) < D: lo = mid
        else: hi = mid
    return (lo + hi) / 2


def mc_interval(D, reps=4000):
    """Akzeptanzbereich-Inversion: welche n erzeugen D mit 95 % Wahrscheinlichkeit?"""
    nhat = invert(D)
    if not math.isfinite(nhat): return (float("nan"), float("nan"))
    kand = np.unique(np.clip(np.linspace(nhat * 0.4, nhat * 3.0, 260).astype(int), 1, None))
    lo = hi = None
    for n in kand:
        draws = RNG.integers(0, N, size=(reps, int(n)))
        Ds = np.array([len(np.unique(row)) for row in draws])
        q = np.percentile(Ds, [2.5, 97.5])
        if q[0] <= D <= q[1]:
            if lo is None: lo = int(n)
            hi = int(n)
    return (lo, hi)


# --- Namensmengen einsammeln -------------------------------------------------
klasse = {}          # name -> 'nur_leser' | 'schreiber'
erst_ts = {}
for m in ["2604", "2605", "2606", "2607"]:
    p = os.path.join(NORM, f"bi_{m}.tsv.gz")
    if not os.path.exists(p): continue
    with gzip.open(p, "rt", encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE):
            n = r["name"]
            if not n or r["namensquelle"] != "name": continue
            ts = int(r["ts"])
            if n not in erst_ts or ts < erst_ts[n]: erst_ts[n] = ts
            if r["kind"] in ("save", "editform"): klasse[n] = "schreiber"
            else: klasse.setdefault(n, "nur_leser")

export = set()
for line in open(os.path.join(BASE, "data", "labels.jsonl"), encoding="utf-8"):
    export.add(json.loads(line)["label"])

mengen = {
    "Export-Labels (Paper)":            export,
    "Betreiberlog, alle Namen":         set(klasse),
    "Betreiberlog, nur Schreiber":      {n for n, k in klasse.items() if k == "schreiber"},
    "Betreiberlog, nur reine Leser":    {n for n, k in klasse.items() if k == "nur_leser"},
    "Vereinigung Log + Export":         set(klasse) | export,
}

rows = []
for titel, menge in mengen.items():
    ein = {n: marken(n)[0] for n in menge if len(set(marken(n))) == 1}
    # Regel main.tex:152 — Namen, deren Marke ihr REALES Erstauftrittsdatum ist, raus
    echt = 0
    ein2 = {}
    for n, mk in ein.items():
        ts = erst_ts.get(n)
        if ts is not None:
            d = dt.datetime.fromtimestamp(ts, dt.UTC)
            if KUERZEL[mk[:3]] == d.month and int(mk[3:]) == d.day:
                echt += 1
                continue
        ein2[n] = mk
    D = len(set(ein2.values()))
    est = invert(D)
    lo, hi = mc_interval(D)
    rows.append(dict(menge=titel, n_namen=len(menge), namen_mit_genau_1_marke=len(ein),
                     reale_daten_entfernt=echt, D=D, schaetzer=round(est, 1),
                     ci_lo=lo, ci_hi=hi))
    print(rows[-1], flush=True)

with open(os.path.join(ART, "bi05_population.csv"), "w", newline="", encoding="utf-8") as o:
    w = csv.DictWriter(o, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
json.dump(rows, open(os.path.join(ART, "bi05_population.json"), "w"), indent=1)
