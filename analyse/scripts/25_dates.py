#!/usr/bin/env python3
"""Extrahiert fiktive Datums-Marker (MonAbk + Tag) aus Agenten-Namen und Volltext."""
import json,re,os,csv,collections
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MON=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
MONLONG={"January":"Jan","February":"Feb","March":"Mar","April":"Apr","May":"May","June":"Jun",
         "July":"Jul","August":"Aug","September":"Sep","October":"Oct","November":"Nov","December":"Dec"}
NUM={"One":"01","Two":"02","Three":"03","Four":"04","Five":"05","Six":"06","Seven":"07","Eight":"08",
     "Nine":"09","Ten":"10","Eleven":"11","Twelve":"12","Thirteen":"13","Fourteen":"14","Fifteen":"15",
     "Sixteen":"16","Seventeen":"17","Eighteen":"18","Nineteen":"19","Twenty":"20","TwentyOne":"21",
     "TwentyFive":"25","Thirty":"30","ThirtyOne":"31"}
rx_short=re.compile("(" + "|".join(MON) + r")(\d{2})(?!\d)")
rx_long =re.compile("(" + "|".join(MONLONG) + r")(\d{2}(?!\d)|" + "|".join(sorted(NUM,key=len,reverse=True)) + ")")

def marks(s):
    out=set()
    for m,d in rx_short.findall(s): out.add((m,int(d)))
    for m,d in rx_long.findall(s):
        mm=MONLONG[m]; dd=NUM.get(d,d)
        try: out.add((mm,int(dd)))
        except: pass
    return out

lab_marks=collections.Counter(); lab_with=set(); lab_all=set()
for line in open(os.path.join(BASE,"data","labels.jsonl"),encoding="utf-8"):
    r=json.loads(line); L=r["label"]; lab_all.add(L)
    ms=marks(L)
    if ms: lab_with.add(L)
    for m in ms: lab_marks[m]+=1

body_marks=collections.Counter(); body_lab=collections.defaultdict(set)
years=collections.Counter()
rx_year=re.compile(r'\b(20[2-3][0-9])\b')
rx_tc=re.compile(r'task[- ]clock[^.\n]{0,40}?\b(20[2-3][0-9])\b',re.I)
tcyears=collections.Counter()
for line in open(os.path.join(BASE,"data","revisions.jsonl"),encoding="utf-8"):
    r=json.loads(line); b=r.get("body") or ""
    for y in rx_year.findall(b): years[y]+=1
    for y in rx_tc.findall(b): tcyears[y]+=1
    for m in marks(r["label"]): body_marks[m]+=1; body_lab[m].add(r["label"])

MONI={m:i+1 for i,m in enumerate(MON)}
rows=sorted(lab_marks.items(), key=lambda kv:(MONI[kv[0][0]],kv[0][1]))
p=os.path.join(BASE,"artefakte","harness_fake_dates.csv")
with open(p,"w",newline="",encoding="utf-8") as f:
    w=csv.writer(f); w.writerow(["month","day","month_num","n_labels","n_revisions"])
    for (m,d),n in rows: w.writerow([m,d,MONI[m],n,body_marks.get((m,d),0)])
print("labels total",len(lab_all),"labels with date marker",len(lab_with),
      f"({len(lab_with)/len(lab_all)*100:.1f}%)")
print("distinct (month,day) pairs:",len(lab_marks))
permonth=collections.Counter()
for (m,d),n in lab_marks.items(): permonth[m]+=n
print("per month (labels):", [(m,permonth.get(m,0)) for m in MON])
daycov=collections.defaultdict(set)
for (m,d) in lab_marks: daycov[m].add(d)
for m in MON:
    ds=sorted(daycov[m]); miss=[d for d in range(1,32) if d not in ds]
    print(f"{m}: {len(ds)} distinct days, max {max(ds) if ds else '-'}, missing 1..31: {miss}")
print("years in body (top):", years.most_common(12))
print("years near 'task clock':", tcyears.most_common(10))
