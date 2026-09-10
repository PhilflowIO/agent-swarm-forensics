import json, collections, csv, statistics
from datetime import datetime
import pathlib as _pl; _BASE = str(_pl.Path(__file__).resolve().parent.parent)  # analyse/ (skript-relativ)
D=_BASE+'/data/'
A=_BASE+'/artefakte/'
def T(s): return datetime.fromisoformat(s.replace('Z','+00:00'))
revs=[json.loads(l) for l in open(D+'revisions.jsonl')]
evs=[json.loads(l) for l in open(D+'events.jsonl')]
pages=[json.loads(l) for l in open(D+'pages.jsonl')]
P={p['page_key']:p for p in pages}
dels=[e for e in evs if e['event_type']=='delete']

# ---- hourly escalation 06-15..06-23
h=collections.Counter(); hl=collections.defaultdict(set)
for r in revs:
    h[r['time'][:13]]+=1; hl[r['time'][:13]].add(r['label'])
hd=collections.Counter(e['time'][:13] for e in dels)
with open(A+'hourly.csv','w',newline='') as f:
    w=csv.writer(f); w.writerow(['hour','saves','deletes','active_labels'])
    for k in sorted(set(list(h)+list(hd))): w.writerow([k,h[k],hd[k],len(hl[k])])
peak=h.most_common(8); print('peak hours saves',peak)
print('max hourly deletes',hd.most_common(5))

# ---- page lifetime: first_write -> first delete
firstdel={}
for e in sorted(dels,key=lambda e:e['time']):
    firstdel.setdefault(e['page_key'],e['time'])
life=[]
for pk,p in P.items():
    if pk in firstdel:
        life.append(((T(firstdel[pk])-T(p['first_write'])).total_seconds()/3600.0, pk))
life.sort()
vals=[x[0] for x in life]
print('pages with known lifetime n=',len(vals))
print('lifetime hours: p10 %.1f p25 %.1f median %.1f p75 %.1f p90 %.1f mean %.1f'%(
 vals[int(.1*len(vals))],vals[int(.25*len(vals))],statistics.median(vals),vals[int(.75*len(vals))],vals[int(.9*len(vals))],statistics.mean(vals)))
print('shortest 5',life[:5]); print('longest 3',life[-3:])
print('deleted page_keys NOT in pages.jsonl:', len({e["page_key"] for e in dels}-set(P)))

# ---- ZZZ pages
zzz=[p for p in pages if p['name'].upper().startswith('ZZZ')]
print('ZZZ pages',len(zzz),'first_write min',min(p['first_write'] for p in zzz) if zzz else None)
zc=collections.Counter(p['first_write'][:10] for p in zzz)
print('ZZZ by day',sorted(zc.items()))
print('ZZZ revs', sum(p['n_revs'] for p in zzz),'bytes',sum(p['body_bytes'] for p in zzz))
print('ZZZ labels', len({l for p in zzz for l in p['labels']}))
print('ZZZ sample names', [p['name'] for p in zzz[:15]])
# bucket distribution of all pages (alphabetical deletion order relevance)
print('bucket dist', collections.Counter(p['bucket'] for p in pages).most_common())
with open(A+'zzz_pages.csv','w',newline='') as f:
    w=csv.writer(f); w.writerow(['page_key','name','wiki','first_write','last_write','n_revs','body_bytes','labels'])
    for p in sorted(zzz,key=lambda p:p['first_write']): w.writerow([p['page_key'],p['name'],p['wiki'],p['first_write'],p['last_write'],p['n_revs'],p['body_bytes'],'|'.join(p['labels'])])

# ---- start pages / pre-existing pages
pre=[p for p in pages if p['n_revs_before']>0]
print('\npre-existing pages (n_revs_before>0):')
for p in sorted(pre,key=lambda p:-p['n_revs_before']):
    print('  %-40s before=%-5d agent_revs=%-4d labels=%d first=%s'%(p['name'],p['n_revs_before'],p['n_revs'],p['n_labels'],p['first_write']))
# recreations
rec=[p for p in pages if p['n_recreations']>0]
print('pages with recreations',len(rec),'total',sum(p['n_recreations'] for p in rec))
for p in sorted(rec,key=lambda p:-p['n_recreations'])[:15]:
    print('  rec=%d del=%d %s'%(p['n_recreations'],p['n_deletions'],p['page_key']))
