#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""10_hosts_und_ausnahmen.py

Teil 1 (Host-Reihenfolge): erster Request einer 'sauberen Flotten-/24' je Farm-Host,
        plus Tagesverteilung je Host.
Teil 2 (Ausnahmen-Audit): die /24-Netze, die einen Marker tragen ABER schon vor dem
        24.05. 05:55 im Log stehen -- je Netz: Anzahl vor dem Schnitt, erster und letzter
        Request vor dem Schnitt, erster Marker-Request, und ein Verhaltensprofil
        (haeufigste action=-Werte vor dem Schnitt). Damit wird gepr., ob ein echter
        Vorlaeufer darunter ist oder nur Dauerkrabbler.
Aufruf: python3 10_hosts_und_ausnahmen.py
"""
import re, collections
from lib_log import iter_log, utc, to_ts, site

Z = re.compile(r"[?&]z=0\.\d{6,}")
X = re.compile(r"[?&]_x=\d")
WRITE = re.compile(r"(form_edit=1|form_editprefs=1|action=saveprefs|action=form_edit)")
ACT = re.compile(r"[?&]action=([^&]*)")
PRE = to_ts("2026-05-24T05:55:00Z")


def marker(a):
    return bool(Z.search(a) or X.search(a) or ("p_username=" in a) or WRITE.search(a))


mark = set(); pre = collections.Counter(); first_mark = {}
for mon in ("2604", "2605", "2606", "2607"):
    for ln, r in iter_log(mon):
        k = ".".join(r["ip"].split(".")[:3])
        if r["ts"] < PRE:
            pre[k] += 1
        if marker(r["action"]):
            mark.add(k)
            first_mark.setdefault(k, (mon, ln, utc(r["ts"]), r["ip"], r["action"][:150]))
clean = mark - set(pre)
dirty = sorted(mark & set(pre), key=lambda k: -pre[k])
print("# Teil1: saubere Flotten-/24 = %d, Marker-/24 mit Vorgeschichte = %d" % (len(clean), len(dirty)))

first_host = {}; day_host = collections.defaultdict(collections.Counter)
for mon in ("2605", "2606", "2607"):
    for ln, r in iter_log(mon):
        if ".".join(r["ip"].split(".")[:3]) not in clean:
            continue
        s = site(r["vhost"]); t = utc(r["ts"])
        first_host.setdefault(s, (mon, ln, t, r["ip"], r["action"][:170]))
        day_host[t[:10]][s] += 1
print("# Erster Request einer sauberen Flotten-/24 je Farm-Host")
for s in sorted(first_host, key=lambda k: first_host[k][2]):
    m, ln, t, ip, a = first_host[s]
    print("  %-22s %s  log_%s:%-8d %-16s %s" % (s, t, m, ln, ip, a))
print("# Flotten-Requests je Tag und Host (saubere /24)")
hs = sorted({h for d in day_host.values() for h in d})
print("  day," + ",".join(hs))
for d in sorted(day_host):
    print("  %s,%s" % (d, ",".join(str(day_host[d][h]) for h in hs)))

print("# Teil2: Marker-/24 MIT Vorgeschichte vor 2026-05-24T05:55:00Z")
prof = collections.defaultdict(collections.Counter)
firstpre = {}; lastpre = {}
for mon in ("2604", "2605"):
    for ln, r in iter_log(mon):
        if r["ts"] >= PRE:
            continue
        k = ".".join(r["ip"].split(".")[:3])
        if k not in mark:
            continue
        m_ = ACT.search(r["action"])
        prof[k][m_.group(1) if m_ else "<kein action=>"] += 1
        firstpre.setdefault(k, (mon, ln, utc(r["ts"]), r["ip"], r["action"][:120]))
        lastpre[k] = (mon, ln, utc(r["ts"]), r["ip"], r["action"][:120])
for k in dirty:
    fm, fl, ft, fi, fa = firstpre[k]
    lm, ll, lt, li, la = lastpre[k]
    mm, ml, mt, mi, ma = first_mark[k]
    print("  /24 %-14s vor_Schnitt=%-5d  erster %s  letzter %s" % (k, pre[k], ft, lt))
    print("       erster  log_%s:%-8d %-16s %s" % (fm, fl, fi, fa))
    print("       letzter log_%s:%-8d %-16s %s" % (lm, ll, li, la))
    print("       Marker  log_%s:%-8d %s %-16s %s" % (mm, ml, mt, mi, ma))
    print("       Profil  %s" % dict(prof[k].most_common(6)))
