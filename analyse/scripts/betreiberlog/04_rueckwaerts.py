#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""04_rueckwaerts.py -- Treffen die IPs / /24-Netze der am 24.05. sicher belegten Flotte
schon frueher auf die Farm? Voller Scan ueber log_2604 + log_2605 bis 24.05. 05:57:02Z.
Aufruf: python3 04_rueckwaerts.py
"""
import json, os, collections, sys
from lib_log import iter_log, utc, to_ts

HERE = os.path.dirname(os.path.abspath(__file__))
S = json.load(open(os.path.join(HERE, "..", "..", "artefakte", "betreiberlog", "flotte_ips_2405.json")))
IPS, N24 = set(S["ips"]), set(S["nets24"])
N16 = set(".".join(n.split(".")[:2]) for n in N24)
CUT = to_ts("2026-05-24T05:57:02Z")

hit_ip = collections.Counter(); hit24 = collections.Counter(); hit16 = collections.Counter()
first_ip = {}; first24 = {}
n16_day = collections.Counter()
for mon in ("2604", "2605"):
    for ln, r in iter_log(mon):
        if r["ts"] >= CUT:
            continue
        ip = r["ip"]; p = ip.split(".")
        n24 = ".".join(p[:3]); n16 = ".".join(p[:2])
        if ip in IPS:
            hit_ip[ip] += 1; first_ip.setdefault(ip, (mon, ln, utc(r["ts"]), r["vhost"] + r["path"] + "?" + r["query"]))
        if n24 in N24:
            hit24[n24] += 1; first24.setdefault(n24, (mon, ln, utc(r["ts"]), ip, r["vhost"] + r["path"] + "?" + r["query"]))
        if n16 in N16:
            hit16[n16] += 1; n16_day[utc(r["ts"])[:10]] += 1

print("# exakte Flotten-IPs vor 24.05. 05:57:02Z: %d Requests auf %d IPs" % (sum(hit_ip.values()), len(hit_ip)))
for ip, c in hit_ip.most_common(30):
    m, ln, t, a = first_ip[ip]
    print("  IP %-16s n=%-4d erster: log_%s:%d %s %s" % (ip, c, m, ln, t, a[:110]))
print("# /24-Netze der Flotte vor dem Schnitt: %d Requests auf %d Netzen" % (sum(hit24.values()), len(hit24)))
for n, c in hit24.most_common(20):
    m, ln, t, ip, a = first24[n]
    print("  /24 %-14s n=%-4d erster: log_%s:%d %s %s %s" % (n, c, m, ln, t, ip, a[:100]))
print("# /16-Netze der Flotte, Requests je Tag (vor dem Schnitt):")
for d in sorted(n16_day):
    print("  %s %d" % (d, n16_day[d]))
