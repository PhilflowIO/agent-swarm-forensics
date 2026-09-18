#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""03_flotten_ips.py -- Sichere Flotten-Requests im Fenster bestimmen, deren IPs/Netze sammeln,
und dann das GESAMTE April+Mai-Log nach genau diesen IPs und /24-Netzen rueckwaerts absuchen.

Sicherer Flotten-Request (Konjunktion, konservativ):
  vhost in {www.wikiservice.at, wikiservice.at} UND (z=<float> ODER p_username= ODER form_edit=1
  ODER id/keywords = eine im Export belegte Schwarm-Seite)
Aufruf: python3 03_flotten_ips.py
"""
import re, json, os, collections, sys
from lib_log import iter_log, utc, to_ts

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.normpath(os.path.join(HERE, "..", "..", "data"))

# Schwarm-Seitennamen aus dem Export (pages.jsonl)
swarm_pages = set()
with open(os.path.join(DATA, "pages.jsonl"), encoding="utf-8") as fh:
    for line in fh:
        o = json.loads(line)
        k = o.get("key") or o.get("page") or ""
        if "~" in k:
            k = k.split("~", 1)[1]
        if k:
            swarm_pages.add(k)
sys.stderr.write("swarm_pages=%d\n" % len(swarm_pages))

Z_RX = re.compile(r"[?&]z=0\.\d{6,}")
ID_RX = re.compile(r"[?&](?:id|keywords|oldid)=([^&]*)")
WS = ("www.wikiservice.at", "wikiservice.at")


def sure_fleet(r):
    if r["vhost"] not in WS:
        return None
    a = r["action"]
    if Z_RX.search(a):
        return "z"
    if "p_username=" in a:
        return "p_username"
    if "form_edit=1" in a:
        return "form_edit"
    for v in ID_RX.findall(a):
        if v in swarm_pages:
            return "swarmpage"
    return None


ips = collections.Counter()
nets24 = collections.Counter()
kinds = collections.Counter()
first_by_ip = {}
LO, HI = to_ts("2026-05-24T00:00:00Z"), to_ts("2026-05-25T00:00:00Z")
for ln, r in iter_log("2605"):
    if not (LO <= r["ts"] < HI):
        continue
    k = sure_fleet(r)
    if k:
        kinds[k] += 1
        ips[r["ip"]] += 1
        p = r["ip"].split(".")
        nets24[".".join(p[:3])] += 1
        first_by_ip.setdefault(r["ip"], (ln, utc(r["ts"]), r["action"][:120]))

sys.stderr.write("sichere Flotten-Requests am 24.05.: %d, distinkte IPs: %d, /24: %d, Arten: %s\n"
                 % (sum(ips.values()), len(ips), len(nets24), dict(kinds)))
json.dump({"ips": sorted(ips), "nets24": sorted(nets24)},
          open(os.path.join(HERE, "..", "..", "artefakte", "betreiberlog", "flotte_ips_2405.json"), "w"), indent=0)
print("ip,count,first_line,first_utc")
for ip, c in ips.most_common():
    ln, t, a = first_by_ip[ip]
    print("%s,%d,%d,%s" % (ip, c, ln, t))
