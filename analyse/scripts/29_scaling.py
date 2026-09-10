#!/usr/bin/env python3
"""Automatische, unkuratierte Extraktion von (R1-Timer, Folge-Timer)-Paaren; Skalierungstest."""
import json,re,os,csv,collections,statistics
from scipy import stats
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RX1=re.compile(r'(?:initial|R1|Q1|first)[ -]?(?:round )?(?:timer|deadline|window)[^0-9\n]{0,25}(\d{1,3})m(\d{2})\b',re.I)
RX2=re.compile(r'(?:(\d{1,3})[ -]?(?:s|sec|second)s?[- ](?:timer|deadline|window)|(?:timer|deadline|window)[^0-9\n]{0,18}(\d{1,3})\s*(?:s\b|sec))',re.I)
pairs={}
for line in open(os.path.join(BASE,"data","revisions.jsonl"),encoding="utf-8"):
    r=json.loads(line); b=r.get("body") or ""
    for para in re.split(r'\n\s*\n',b):
        m1=RX1.search(para); m2=RX2.search(para)
        if not (m1 and m2): continue
        t1=int(m1.group(1))*60+int(m1.group(2)); t2=int(m2.group(1) or m2.group(2))
        if not (30<=t1<=7200 and 1<=t2<=600): continue
        key=(t1,t2)
        d=pairs.setdefault(key,{"revs":0,"labels":set(),"first":(r["time"],r["page_key"],r["label"],para[:200])})
        d["revs"]+=1; d["labels"].add(r["label"])
        if r["time"]<d["first"][0]: d["first"]=(r["time"],r["page_key"],r["label"],para[:200])
p=os.path.join(BASE,"artefakte","harness_scaling_pairs.csv")
with open(p,"w",newline="",encoding="utf-8") as f:
    w=csv.writer(f); w.writerow(["r1_timer_s","followup_timer_s","ratio","n_revs","n_labels","first_time","first_page","first_label","evidence"])
    for (t1,t2),d in sorted(pairs.items()):
        w.writerow([t1,t2,round(t1/t2,2),d["revs"],len(d["labels"]),*d["first"]])
X=[t1 for (t1,t2) in pairs]; Y=[t2 for (t1,t2) in pairs]
print("unkuratierte distinkte Paare:",len(pairs),"| stuetzende Versionen:",sum(d['revs'] for d in pairs.values()),
      "| Namen:",len(set().union(*[d['labels'] for d in pairs.values()])))
r,pv=stats.pearsonr(X,Y); rs,ps=stats.spearmanr(X,Y)
print("Pearson r=%.3f p=%.5f | Spearman rho=%.3f p=%.5f"%(r,pv,rs,ps))
ra=[t1/t2 for t1,t2 in pairs]
print("Verhaeltnis R1/Folge: median %.1f  IQR %.1f-%.1f  min %.1f max %.1f"%(
    statistics.median(ra),statistics.quantiles(ra,n=4)[0],statistics.quantiles(ra,n=4)[2],min(ra),max(ra)))
# 50%-Subsample
import random; random.seed(42)
k=sorted(pairs); sub=random.sample(k,len(k)//2)
r2,p2=stats.pearsonr([a for a,b in sub],[b for a,b in sub])
print("50%%-Subsample (n=%d): Pearson r=%.3f p=%.5f"%(len(sub),r2,p2))
