#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""11_pfade_takt.py -- (a) Welche Pfade enthaelt der Betreiberlog ueberhaupt? (Reichweiten-Test:
kann er einen Zugriff auf / oder /robots.txt zeigen?)  (b) Takt der Flotte im Erstkontakt-Fenster.
Aufruf: python3 11_pfade_takt.py
"""
import re, collections
from lib_log import iter_log, utc, to_ts

paths = collections.Counter()
for ln, r in iter_log("2605"):
    paths[r["path"]] += 1
print("# Pfade in log_2605, Top 25 von %d distinkt" % len(paths))
for p, c in paths.most_common(25):
    print("   %8d  %s" % (c, p))
nonwiki = sum(c for p, c in paths.items() if "wiki" not in p and "cgi" not in p)
print("# Requests auf Pfade ohne 'wiki'/'cgi': %d" % nonwiki)

A, B = to_ts("2026-05-24T05:55:00Z"), to_ts("2026-05-24T06:20:00Z")
ts = []
for ln, r in iter_log("2605"):
    if A <= r["ts"] <= B and re.search(r"[?&]z=0\.\d{6,}|p_username=|form_edit", r["action"]):
        ts.append(r["ts"])
gaps = [b - a for a, b in zip(ts, ts[1:])]
print("# Erstkontakt-Takt: %d markierte Requests, Abstaende (s): %s" % (len(ts), gaps))
