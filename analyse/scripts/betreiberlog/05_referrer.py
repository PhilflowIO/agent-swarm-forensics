#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""05_referrer.py -- Alle vier refer_*-Dateien auswerten.
Format: <unix-ts>|<pfad>|<referrer>
Fragen: (a) Gesamtverteilung der Referrer-Domains je Monat,
        (b) Referrer, die auf eine Flotten-Seite zeigen oder von Suchmaschinen/extern kommen,
        (c) alles im Erstkontakt-Fenster.
Aufruf: python3 05_referrer.py
"""
import io, os, re, sys, collections, datetime as dt
from lib_log import DATA, REFS, utc, to_ts

SE = re.compile(r"(google|bing|duckduckgo|yandex|baidu|ecosia|startpage|search\.|qwant|brave|perplexity|openai|chatgpt|claude|anthropic)", re.I)
FLEET = re.compile(r"(Federal|DataUSA|Agent|Sector|Cohort|OpenAI|Relay|Sequence|Test[A-Z])")

dom_rx = re.compile(r"^[a-z]+://([^/]+)", re.I)
tot = collections.Counter()
by_month_dom = collections.defaultdict(collections.Counter)
se_rows = []
fleet_rows = []
window_rows = []
A, B = to_ts("2026-05-17T00:00:00Z"), to_ts("2026-05-25T00:00:00Z")
first_ts = {}
for mon, fn in sorted(REFS.items()):
    p = os.path.join(DATA, fn)
    with io.open(p, "r", encoding="iso-8859-1", errors="replace") as fh:
        for ln, line in enumerate(fh, 1):
            line = line.rstrip("\n")
            parts = line.split("|", 2)
            if len(parts) != 3 or not parts[0].strip().isdigit():
                continue
            ts = int(parts[0]); path, ref = parts[1], parts[2]
            tot[mon] += 1
            m = dom_rx.match(ref)
            dom = (m.group(1).lower() if m else ("<" + ref[:20] + ">"))
            by_month_dom[mon][dom] += 1
            first_ts.setdefault(mon, ts)
            if SE.search(ref):
                se_rows.append((fn, ln, ts, path, ref))
            if FLEET.search(path) or FLEET.search(ref):
                fleet_rows.append((fn, ln, ts, path, ref))
            if A <= ts <= B:
                window_rows.append((fn, ln, ts, path, ref))

print("# Zeilen je Referrer-Datei:", dict(tot))
for mon in sorted(by_month_dom):
    print("## refer_%s Top-Referrer-Domains" % mon)
    for d, c in by_month_dom[mon].most_common(12):
        print("   %6d  %s" % (c, d))
print("# Suchmaschinen-/LLM-Referrer gesamt: %d" % len(se_rows))
for r in se_rows[:40]:
    print("   %s:%d %s %s <- %s" % (r[0], r[1], utc(r[2]), r[3][:70], r[4][:110]))
print("# Referrer-Zeilen mit Flotten-Grammatik in Pfad oder Referrer: %d" % len(fleet_rows))
for r in fleet_rows[:60]:
    print("   %s:%d %s %s <- %s" % (r[0], r[1], utc(r[2]), r[3][:80], r[4][:110]))
print("# Referrer-Zeilen im Fenster 17.-24.05.: %d" % len(window_rows))
for r in window_rows:
    print("   %s:%d %s %s <- %s" % (r[0], r[1], utc(r[2]), r[3][:80], r[4][:110]))
