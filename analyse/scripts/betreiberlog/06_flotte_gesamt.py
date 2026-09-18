#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""06_flotte_gesamt.py -- Flotten-Detektor ueber alle vier Monatslogs.

Detektor FLEET(r), disjunktiv, jede Klausel einzeln gezaehlt:
  z      : Cache-Buster  z=0.<>=6 Nachkommastellen
  x      : Cache-Buster  _x=<zahl>
  user   : p_username=   (Wiki-Benutzernamen setzen)
  write  : form_edit=1 | form_editprefs=1 | action=saveprefs | action=form_edit
  page   : id=/keywords=/oldid= trifft einen im Export belegten Schwarm-Seitennamen
           (pages.jsonl.name) oder einen Schwarm-Label-Namen (labels.jsonl.label)
Ausgabe:
  A) Erst-Treffer je Klausel und je vhost
  B) Tagescounts je vhost (nur Flotten-Requests)
  C) Stundencounts 23.-26.05. je vhost
  D) die ersten N Flotten-Requests ueberhaupt, chronologisch
Aufruf: python3 06_flotte_gesamt.py [N]
"""
import re, json, os, sys, collections
from lib_log import iter_log, utc, site

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.normpath(os.path.join(HERE, "..", "..", "data"))
N_FIRST = int(sys.argv[1]) if len(sys.argv) > 1 else 80

# Vokabular NUR aus Seiten, die der Schwarm selbst angelegt hat:
# n_revs_before == 0 (keine Vorgeschichte im Wiki) UND first_write >= 2026-05-24.
# Damit faellt jeder deutsche Altbestand (WillkommenImWiki etc.) heraus.
vocab = set()
with open(os.path.join(DATA, "pages.jsonl"), encoding="utf-8") as fh:
    for line in fh:
        o = json.loads(line)
        if o.get("n_revs_before", 0) == 0 and (o.get("first_write") or "") >= "2026-05-24" \
           and o.get("name") and len(o["name"]) >= 10:
            vocab.add(o["name"])
# Gegenprobe: alles, was im April-Log schon als id/keywords/oldid/search/mp vorkam,
# ist KEIN Schwarm-Name (Altbestand oder Allerweltswort) und fliegt raus.
APRIL_RX = re.compile(r"[?&](?:id|keywords|oldid|mp|search)=([^&]*)")
seen_april = set()
for _ln, _r in iter_log("2604"):
    for _v in APRIL_RX.findall(_r["action"]):
        if _v in vocab:
            seen_april.add(_v)
vocab -= seen_april
sys.stderr.write("Schwarm-Seitenvokabular nach April-Gegenprobe: %d (entfernt: %d)\n"
                 % (len(vocab), len(seen_april)))

Z = re.compile(r"[?&]z=0\.\d{6,}")
X = re.compile(r"[?&]_x=\d")
IDV = re.compile(r"[?&](?:id|keywords|oldid|mp|search)=([^&]*)")
WRITE = re.compile(r"(form_edit=1|form_editprefs=1|action=saveprefs|action=form_edit)")


def clauses(r):
    a = r["action"]; out = []
    if Z.search(a): out.append("z")
    if X.search(a): out.append("x")
    if "p_username=" in a: out.append("user")
    if WRITE.search(a): out.append("write")
    # 'page' bewusst NICHT im Aggregat-Detektor: das Seitenvokabular ist nicht
    # trennscharf (Altbestand wie TestSeite/202605 steckt in pages.jsonl).
    # Seitennamen werden in 07_hostreihenfolge.py separat und eng gefasst geprueft.
    return out


first_cl = {}; first_vh = {}
day = collections.defaultdict(collections.Counter)      # day -> vhost -> n
hour = collections.defaultdict(collections.Counter)
cl_tot = collections.Counter()
firsts = []
for mon in ("2604", "2605", "2606", "2607"):
    for ln, r in iter_log(mon):
        cs = clauses(r)
        if not cs:
            continue
        s = site(r["vhost"]); t = utc(r["ts"])
        for c in cs:
            cl_tot[c] += 1
            first_cl.setdefault(c, (mon, ln, t, s, r["ip"], r["action"][:170]))
        first_vh.setdefault(s, (mon, ln, t, r["ip"], "+".join(cs), r["action"][:170]))
        day[t[:10]][s] += 1
        if "2026-05-23" <= t[:10] <= "2026-05-27":
            hour[t[:13]][s] += 1
        if len(firsts) < N_FIRST:
            firsts.append((mon, ln, t, r["ip"], s, "+".join(cs), r["action"][:190]))

print("# A1 Erst-Treffer je Detektor-Klausel (gesamter 4-Monats-Log)")
for c in sorted(first_cl):
    m, ln, t, s, ip, a = first_cl[c]
    print("  %-6s n=%-7d log_%s:%-8d %s  %-18s %-16s %s" % (c, cl_tot[c], m, ln, t, s, ip, a))
print("# A2 Erst-Treffer je Farm-Host")
for s in sorted(first_vh, key=lambda k: first_vh[k][2]):
    m, ln, t, ip, cs, a = first_vh[s]
    print("  %-22s log_%s:%-8d %s  %-16s [%s] %s" % (s, m, ln, t, ip, cs, a))
print("# B Flotten-Requests je Tag und Farm-Host")
hosts = sorted({h for d in day.values() for h in d})
print("  day," + ",".join(hosts))
for d in sorted(day):
    print("  %s,%s" % (d, ",".join(str(day[d][h]) for h in hosts)))
print("# C Flotten-Requests je Stunde 23.-27.05.")
for h in sorted(hour):
    print("  %s  %s" % (h, dict(hour[h])))
print("# D Die ersten %d Flotten-Requests chronologisch" % N_FIRST)
for m, ln, t, ip, s, cs, a in firsts:
    print("  log_%s:%-8d %s %-16s %-18s [%-12s] %s" % (m, ln, t, ip, s, cs, a))
