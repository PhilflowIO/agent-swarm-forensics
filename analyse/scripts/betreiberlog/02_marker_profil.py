#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""02_marker_profil.py -- Kandidaten-Marker fuer 'flottenartig' ueber ganze Monatslogs pruefen.
Zaehlt je Marker die Requests pro Tag (UTC) und je vhost, und liefert die ERSTE Zeile je Marker.
Aufruf: python3 02_marker_profil.py 2604 2605 [2606 2607]
Ausgabe: CSV nach stdout + Erst-Treffer nach stderr.
"""
import sys, re, collections
from lib_log import iter_log, utc

Z_RX = re.compile(r"[?&]z=0\.\d{6,}")          # Cache-Buster z=<float>
X_RX = re.compile(r"[?&]_x=")
MARKERS = {
    "vhost_www_wsat": lambda r: r["vhost"] == "www.wikiservice.at",
    "vhost_wsat": lambda r: r["vhost"] == "wikiservice.at",
    "vhost_prowiki": lambda r: r["vhost"] == "prowiki.org",
    "vhost_wscom": lambda r: r["vhost"] == "wikiservice.com",
    "z_buster": lambda r: bool(Z_RX.search(r["action"])),
    "x_buster": lambda r: bool(X_RX.search(r["action"])),
    "z_and_www": lambda r: bool(Z_RX.search(r["action"])) and r["vhost"] == "www.wikiservice.at",
    "z_not_www": lambda r: bool(Z_RX.search(r["action"])) and r["vhost"] != "www.wikiservice.at",
    "form_edit": lambda r: "form_edit=1" in r["action"],
    "form_edit_www": lambda r: "form_edit=1" in r["action"] and r["vhost"] == "www.wikiservice.at",
}

cnt = collections.defaultdict(collections.Counter)
first = {}
tot = collections.Counter()
for mon in sys.argv[1:]:
    for ln, r in iter_log(mon):
        day = utc(r["ts"])[:10]
        tot[day] += 1
        for k, f in MARKERS.items():
            if f(r):
                cnt[k][day] += 1
                if k not in first:
                    first[k] = (mon, ln, utc(r["ts"]), r["ip"], r["action"][:200])

days = sorted(tot)
print("day,total," + ",".join(sorted(MARKERS)))
for d in days:
    print(d + "," + str(tot[d]) + "," + ",".join(str(cnt[k][d]) for k in sorted(MARKERS)))
for k in sorted(first):
    m, ln, t, ip, a = first[k]
    print("FIRST %-16s log_%s:%d  %s  %s  %s" % (k, m, ln, t, ip, a), file=sys.stderr)
