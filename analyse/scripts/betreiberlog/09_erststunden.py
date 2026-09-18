#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""09_erststunden.py -- Was hat die Flotte in den ersten Stunden angefragt?

Definition 'saubere Flotten-/24': ein /24, das (a) irgendwann im 4-Monats-Log einen harten
Marker (z=/_x=/p_username=/write) traegt UND (b) VOR 2026-05-24T05:55:00Z kein einziges Mal
im Log vorkommt. (b) entfernt Dauerkrabbler und Tor-Exits, die (a) zufaellig ausloesen.

Ausgabe:
  A) Zahl der sauberen /24 + wie viele davon ihren ersten Request am 24.05. haben
  B) alle Requests sauberer /24 am 24.05., chronologisch (erste K)
  C) Haeufigkeit der angefragten Werte (id/keywords/search/oldid) am 24.05.
  D) Haeufigkeit der action=-Werte am 24.05.
  E) Requests/IP-Verhaeltnis am 24.05. (Rotationsmass)
Aufruf: python3 09_erststunden.py [K]
"""
import re, sys, collections
from lib_log import iter_log, utc, to_ts, site

K = int(sys.argv[1]) if len(sys.argv) > 1 else 120
Z = re.compile(r"[?&]z=0\.\d{6,}")
X = re.compile(r"[?&]_x=\d")
WRITE = re.compile(r"(form_edit=1|form_editprefs=1|action=saveprefs|action=form_edit)")
VAL = re.compile(r"[?&](id|keywords|search|oldid)=([^&]*)")
ACT = re.compile(r"[?&]action=([^&]*)")
PRE = to_ts("2026-05-24T05:55:00Z")
D0, D1 = to_ts("2026-05-24T00:00:00Z"), to_ts("2026-05-25T00:00:00Z")


def marker(a):
    return bool(Z.search(a) or X.search(a) or ("p_username=" in a) or WRITE.search(a))


mark24 = set(); pre24 = set()
for mon in ("2604", "2605", "2606", "2607"):
    for ln, r in iter_log(mon):
        k = ".".join(r["ip"].split(".")[:3])
        if r["ts"] < PRE:
            pre24.add(k)
        if marker(r["action"]):
            mark24.add(k)
clean = mark24 - pre24
print("# A  /24 mit Marker: %d ; davon ohne jeden Request vor 2026-05-24T05:55:00Z: %d"
      % (len(mark24), len(clean)))

rows = []; vals = collections.Counter(); acts = collections.Counter()
ips = collections.Counter(); hosts = collections.Counter(); hourly = collections.Counter()
for ln, r in iter_log("2605"):
    if not (D0 <= r["ts"] < D1):
        continue
    if ".".join(r["ip"].split(".")[:3]) not in clean:
        continue
    rows.append((ln, utc(r["ts"]), r["ip"], site(r["vhost"]), r["action"]))
    ips[r["ip"]] += 1; hosts[site(r["vhost"])] += 1; hourly[utc(r["ts"])[11:13]] += 1
    for _k, v in VAL.findall(r["action"]):
        vals[v] += 1
    m = ACT.search(r["action"])
    acts[m.group(1) if m else "<kein action=>"] += 1

print("# B  Requests sauberer /24 am 24.05.: %d ; erste %d chronologisch" % (len(rows), K))
for ln, t, ip, s, a in rows[:K]:
    print("   log_2605:%-8d %s %-16s %-16s %s" % (ln, t, ip, s, a[:210]))
print("# C  angefragte Werte (id/keywords/search/oldid), Top 60 von %d distinkt" % len(vals))
for v, c in vals.most_common(60):
    print("   %5d  %s" % (c, v))
print("# D  action=-Werte")
for a, c in acts.most_common(30):
    print("   %5d  %s" % (c, a))
print("# E  Rotation: %d Requests von %d distinkten IPs (= %.2f Requests/IP); Hosts: %s"
      % (len(rows), len(ips), len(rows) / max(1, len(ips)), dict(hosts)))
print("# F  Requests je UTC-Stunde am 24.05.: %s" % dict(sorted(hourly.items())))
