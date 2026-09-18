#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""08_kandidaten.py -- Einzelne IPs / /24-Netze ueber alle vier Monate vollstaendig auflisten.
Aufruf: python3 08_kandidaten.py <ip-oder-/24> [...]
"""
import sys, collections
from lib_log import iter_log, utc

targets = sys.argv[1:]
rows = collections.defaultdict(list)
for mon in ("2604", "2605", "2606", "2607"):
    for ln, r in iter_log(mon):
        ip = r["ip"]; p = ip.split(".")
        for t in targets:
            if ip == t or ".".join(p[:3]) == t or ".".join(p[:2]) == t:
                rows[t].append((mon, ln, utc(r["ts"]), ip, r["action"][:190]))
for t in targets:
    v = rows[t]
    print("## %s  n=%d  erster %s  letzter %s" % (t, len(v), v[0][2] if v else "-", v[-1][2] if v else "-"))
    for m, ln, ts, ip, a in (v if len(v) <= 60 else v[:30] + [("...",) * 5] + v[-30:]):
        print("   log_%s:%-8s %s %-16s %s" % (m, ln, ts, ip, a))
