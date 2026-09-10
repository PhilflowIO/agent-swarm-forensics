#!/usr/bin/env python3
"""Baut eine Tabelle beobachteter Episoden-Konfigurationen (R1-Timer / Cooldown / Folge-Timer)."""
import json,re,os,csv,collections
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPLIT=re.compile(r'(?<=[.!?])\s+|\n+'); WS=re.compile(r'\s+')
def mmss(t):
    if 'm' in t:
        a,b=t.split('m'); return int(a)*60+int(b or 0)
    return int(t)
RX_R1=re.compile(r'(?:initial|R1|Q1|first)[- ](?:timer|deadline|window)\s*(?:was|of|:|=)?\s*~?\*{0,2}(\d{1,3}m\d{2}|\d{1,3}m\b|\d{1,3})\s*(s|sec|seconds)?',re.I)
RX_CD=re.compile(r'(?:cooldown|next query|next prompt|follow-?up)[^.\n]{0,60}?(?:\+|after deadline|in|of|exactly)\s*~?\*{0,2}(\d{1,2}h\d{1,2}m\d{2}|\d{1,3}m\d{2})',re.I)
RX_FT=re.compile(r'(?:timer|deadline|window)\s*(?:of\s*)?~?(\d{1,3})\s*(?:s|sec|seconds)\b',re.I)
RX_TIERD=re.compile(r'(\d{1,2}m\d{2})\s*(?:/\s*(\d{1,3})\s*s)?\s*[- ]?(?:tier|cohort)',re.I)

conf=collections.Counter(); labs=collections.defaultdict(set); first={}
rows=[]
for line in open(os.path.join(BASE,"data","revisions.jsonl"),encoding="utf-8"):
    r=json.loads(line); b=r.get("body") or ""
    for s in re.split(r'\n\s*\n', b):
        s=WS.sub(" ",s).strip()
        m1=RX_R1.search(s); m2=RX_CD.search(s); m3=RX_FT.search(s)
        if m1 and (m2 or m3):
            t1=m1.group(1)
            if 'm' not in t1 and not m1.group(2): continue
            cd=m2.group(1) if m2 else ""
            ft=m3.group(1) if m3 else ""
            key=(t1,cd,ft)
            conf[key]+=1; labs[key].add(r["label"])
            if key not in first or r["time"]<first[key][0]: first[key]=(r["time"],r["page_key"],r["label"],s[:280])
p=os.path.join(BASE,"artefakte","harness_episode_configs.csv")
with open(p,"w",newline="",encoding="utf-8") as f:
    w=csv.writer(f); w.writerow(["r1_timer","cooldown","followup_timer_s","n_revs","n_labels","first_time","first_page","first_label","evidence"])
    for k,v in sorted(conf.items(),key=lambda kv:(-len(labs[kv[0]]),-kv[1])):
        w.writerow([k[0],k[1],k[2],v,len(labs[k]),*first[k]])
print("konfigurationen:",len(conf))
for k,v in sorted(conf.items(),key=lambda kv:-len(labs[kv[0]]))[:30]:
    print(f"R1={k[0]:8s} cd={k[1]:10s} ft={k[2]:4s} rev={v:4d} lab={len(labs[k]):3d} | {first[k][0]} {first[k][2]}")
    print("     ",first[k][3][:200])
