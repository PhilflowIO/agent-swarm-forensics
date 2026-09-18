#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""01_fenster.py -- Roh-Dump eines UTC-Zeitfensters aus einem Monatslog, mit Zeilennummer.
Aufruf: python3 01_fenster.py <monat 2604|2605|2606|2607> <von ISO-UTC> <bis ISO-UTC> [regex-filter]
"""
import sys, re
from lib_log import iter_log, utc, to_ts

mon, a, b = sys.argv[1], to_ts(sys.argv[2]), to_ts(sys.argv[3])
rx = re.compile(sys.argv[4]) if len(sys.argv) > 4 else None
n = 0
for ln, r in iter_log(mon):
    if r["ts"] < a or r["ts"] > b:
        continue
    if rx and not rx.search(r["action"]):
        continue
    n += 1
    print("L%-9d %s %-16s %-24s %s" % (ln, utc(r["ts"]), r["ip"], r["vhost"], r["path"] + ("?" + r["query"] if r["query"] else "")))
print("# n=%d" % n, file=sys.stderr)
