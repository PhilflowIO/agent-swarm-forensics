#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""07_vorlauf.py -- Zwei-Pass-Test auf Vorlaeufer.

Pass 1: ueber alle vier Monatslogs alle Requests mit hartem Flotten-Marker
        (z=0.<6+>, _x=<z>, p_username=, form_edit=1|form_editprefs=1|action=saveprefs|action=form_edit)
        -> Menge der Flotten-IPs und ihrer /24- und /16-Netze.
Pass 2: nochmal ueber log_2604 + log_2605 bis zum Erstkontakt 2026-05-24T05:57:55Z;
        wie viele Requests kommen aus exakt diesen IPs bzw. /24-Netzen?
        Zusaetzlich: parameterloses /wiki.cgi (bare) je Tag als eigener Kandidat-Marker.
Aufruf: python3 07_vorlauf.py
"""
import re, collections, sys
from lib_log import iter_log, utc, to_ts, site

Z = re.compile(r"[?&]z=0\.\d{6,}")
X = re.compile(r"[?&]_x=\d")
WRITE = re.compile(r"(form_edit=1|form_editprefs=1|action=saveprefs|action=form_edit)")
BARE = re.compile(r"^https?://[^/]+/[^?]*wiki2?\.cgi$")
CUT = to_ts("2026-05-24T05:57:55Z")


def marker(a):
    return bool(Z.search(a) or X.search(a) or ("p_username=" in a) or WRITE.search(a))


ips = set(); n24 = set(); n16 = set()
for mon in ("2604", "2605", "2606", "2607"):
    for ln, r in iter_log(mon):
        if marker(r["action"]):
            ips.add(r["ip"])
            p = r["ip"].split(".")
            n24.add(".".join(p[:3])); n16.add(".".join(p[:2]))
print("# Pass1: Flotten-IPs=%d  /24=%d  /16=%d" % (len(ips), len(n24), len(n16)))

hit_ip = collections.Counter(); hit24 = collections.Counter()
first_ip = {}; first24 = {}
bare_day = collections.Counter(); bare_day24 = collections.Counter()
bare_samples = []
for mon in ("2604", "2605"):
    for ln, r in iter_log(mon):
        if r["ts"] >= CUT:
            continue
        d = utc(r["ts"])[:10]
        p = r["ip"].split(".")
        k24 = ".".join(p[:3])
        if BARE.match(r["action"]):
            bare_day[d] += 1
            if k24 in n24:
                bare_day24[d] += 1
                if len(bare_samples) < 60:
                    bare_samples.append((mon, ln, utc(r["ts"]), r["ip"], r["action"]))
        if r["ip"] in ips:
            hit_ip[r["ip"]] += 1
            first_ip.setdefault(r["ip"], (mon, ln, utc(r["ts"]), r["action"][:130]))
        if k24 in n24:
            hit24[k24] += 1
            first24.setdefault(k24, (mon, ln, utc(r["ts"]), r["ip"], r["action"][:130]))

print("# Pass2 vor %s: exakte Flotten-IPs: %d Requests / %d IPs" % (utc(CUT), sum(hit_ip.values()), len(hit_ip)))
for ip, c in hit_ip.most_common(40):
    m, ln, t, a = first_ip[ip]
    print("   IP  %-16s n=%-5d log_%s:%-8d %s  %s" % (ip, c, m, ln, t, a))
print("# Pass2 vor Schnitt: Flotten-/24-Netze: %d Requests / %d Netze" % (sum(hit24.values()), len(hit24)))
for k, c in hit24.most_common(40):
    m, ln, t, ip, a = first24[k]
    print("   /24 %-14s n=%-5d log_%s:%-8d %s  %-16s %s" % (k, c, m, ln, t, ip, a))
print("# parameterlose wiki.cgi-Requests je Tag (gesamt / davon aus Flotten-/24)")
for d in sorted(bare_day):
    print("   %s  %5d  %5d" % (d, bare_day[d], bare_day24[d]))
print("# Beispiele bare-Requests aus Flotten-/24 vor dem Schnitt")
for m, ln, t, ip, a in bare_samples:
    print("   log_%s:%-8d %s %-16s %s" % (m, ln, t, ip, a))
