#!/usr/bin/env python3
"""Extrahiert Tier-/Cohort-Bezeichner und Timing-Parameter aus dem Volltext."""
import json, re, os, csv, collections
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REV = os.path.join(BASE, "data", "revisions.jsonl")
OUT = os.path.join(BASE, "artefakte")

# Tier-Token: 12m18, 9m19/30s, 14s-tier, 2m56, 1m23 ...
RX_TIER   = re.compile(r'\b(\d{1,2}m\d{2})\b')                      # interval mm'ss
RX_STIER  = re.compile(r'\b(\d{1,3})\s*[- ]?s(?:ec(?:ond)?s?)?[- ]tier\b', re.I)
RX_TIERW  = re.compile(r'\b([\w./\-]{2,20})[ -](?:tier|cohort)\b', re.I)
RX_COMBO  = re.compile(r'\b(\d{1,2}m\d{2})\s*/\s*(\d{1,3})s\b')     # 9m19/30s
RX_DEADL  = re.compile(r'\b(\d{1,3})[- ]?(?:second|sec|s)\b[ -]?(?:answer[ -])?(?:deadline|window|timer)', re.I)
RX_TIMER  = re.compile(r'\btimer[ :~]{1,3}(\d{1,2}m\d{2}|\d{1,3}s|\d{1,3} ?sec)', re.I)

tier=collections.Counter(); tierlab=collections.defaultdict(set)
stier=collections.Counter(); stierlab=collections.defaultdict(set)
word=collections.Counter(); wordlab=collections.defaultdict(set)
combo=collections.Counter(); combolab=collections.defaultdict(set)
dead=collections.Counter(); deadlab=collections.defaultdict(set)
first={}
for line in open(REV, encoding="utf-8"):
    r=json.loads(line); b=r.get("body") or ""; L=r["label"]
    for m in set(RX_TIER.findall(b)): tier[m]+=1; tierlab[m].add(L); first.setdefault(("tier",m),(r["time"],r["page_key"],L))
    for m in set(RX_STIER.findall(b)): stier[m]+=1; stierlab[m].add(L); first.setdefault(("s",m),(r["time"],r["page_key"],L))
    for m in set(RX_TIERW.findall(b)): word[m.lower()]+=1; wordlab[m.lower()].add(L); first.setdefault(("w",m.lower()),(r["time"],r["page_key"],L))
    for m in set(RX_COMBO.findall(b)): combo[m]+=1; combolab[m].add(L); first.setdefault(("c",m),(r["time"],r["page_key"],L))
    for m in set(RX_DEADL.findall(b)): dead[m]+=1; deadlab[m].add(L)

def dump(name, cnt, labs, kind):
    p=os.path.join(OUT,name)
    with open(p,"w",newline="",encoding="utf-8") as f:
        w=csv.writer(f); w.writerow(["token","n_revs","n_labels","first_time","first_page","first_label"])
        for k,v in cnt.most_common():
            key=(kind,k) if kind!="c" else ("c",k)
            ft=first.get(key,("","",""))
            w.writerow([k if not isinstance(k,tuple) else "/".join(k), v, len(labs[k]), *ft])
    print("wrote", p, len(cnt))

dump("harness_tier_intervals.csv", tier, tierlab, "tier")
dump("harness_tier_seconds.csv", stier, stierlab, "s")
dump("harness_tier_words.csv", word, wordlab, "w")
dump("harness_tier_combo.csv", combo, combolab, "c")
dump("harness_deadline_seconds.csv", dead, deadlab, "d")
