# -*- coding: utf-8 -*-
"""u02: Suchanfragen der Flotte -- was stand im Suchfeld?"""
import sys, os, re, urllib.parse, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from u00_lib import con
c = con()
rows = c.execute("""SELECT ts_utc, name, action_detail, raw_params FROM rx
  WHERE flotte AND action_kind='search'""").fetchall()
print("flotten-suchrequests:", len(rows))
def term(p):
    q = urllib.parse.parse_qs(p, keep_blank_values=True)
    for k in ("search", "keywords", "q", "text", "query"):
        if k in q and q[k][0].strip():
            return k, q[k][0]
    return None, None
cnt = collections.Counter(); keyc = collections.Counter(); first = {}
uniq = set()
for ts, nm, ad, p in rows:
    k, t = term(p)
    if t is None:
        continue
    keyc[k] += 1
    t = t.strip()
    cnt[t] += 1; uniq.add(t)
    if t not in first or ts < first[t]:
        first[t] = ts
print("parameter:", keyc.most_common())
print("verschiedene suchbegriffe:", len(uniq))
print("\n== top 80 ==")
for t, n in cnt.most_common(80):
    print("%-6d %s" % (n, t[:120]))
import json
# Suchbegriffe aller Besucher -- Log-Inhalt, gehoert zu den (gesperrten) Artefakten, nicht zum Code.
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "artefakte",
                   "betreiberlog", "pruefung", "u02_begriffe.tsv")
with open(out, "w", encoding="utf-8") as fh:
    for t, n in cnt.most_common():
        fh.write("%d\t%d\t%s\n" % (n, first[t], t.replace("\t", " ")))
print("\ngeschrieben:", out)
