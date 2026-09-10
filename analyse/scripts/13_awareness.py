import json, collections, re, csv
import pathlib as _pl; _BASE = str(_pl.Path(__file__).resolve().parent.parent)  # analyse/ (skript-relativ)
D=_BASE+'/data/'
A=_BASE+'/artefakte/'
revs=sorted([json.loads(l) for l in open(D+'revisions.jsonl')],key=lambda r:r['time'])
pat=re.compile(r'(cleanup|deletion sweep|delete sweep|if this page vanishes|vanish\w*|page (?:may|might|could) be (?:deleted|removed)|being (?:deleted|removed)|wiki (?:owner|admin|operator)|mirror(?:ed)? (?:copy|page)|backup page|survives? (?:the )?(?:deletion|cleanup)|alphabetic\w*)',re.I)
h=[r for r in revs if pat.search(r['body'])]
print('deletion/cleanup-awareness: revs %d labels %d pages %d, first %s'%(len(h),len({r['label'] for r in h}),len({r['page_key'] for r in h}),h[0]['time']))
print('by day',sorted(collections.Counter(r['time'][:10] for r in h).items()))
seen=set(); rows=[]
for r in h:
    m=pat.search(r['body']); q=r['body'][max(0,m.start()-160):m.end()+220].replace('\n',' | ')
    k=q[:80]
    rows.append([r['time'],r['page_key'],r['label'],q])
    if k in seen: continue
    seen.add(k)
    if len(seen)<=18: print('\n  %s | %s | %s\n     "%s"'%(r['time'],r['page_key'],r['label'],q[:340]))
with open(A+'deletion_awareness.csv','w',newline='') as f:
    w=csv.writer(f); w.writerow(['time','page_key','label','quote']); w.writerows(rows)

print('\n=== NARROW: wiki-cleanup/deletion-sweep awareness ===')
p2=re.compile(r'(cleanup/?deletion sweep|deletion sweep|cleanup sweep|if this page vanishes|page vanish\w*|wiki cleanup)',re.I)
h2=[r for r in revs if p2.search(r['body'])]
print('revs %d labels %d pages %d span %s..%s'%(len(h2),len({r['label'] for r in h2}),len({r['page_key'] for r in h2}),h2[0]['time'] if h2 else '-',h2[-1]['time'] if h2 else '-'))
seen=set()
for r in h2:
    m=p2.search(r['body']); q=r['body'][max(0,m.start()-190):m.end()+230].replace('\n',' | ')
    if q[:70] in seen: continue
    seen.add(q[:70]); print('  %s | %s | %s\n     "%s"'%(r['time'],r['page_key'],r['label'],q[:360]))

print('\n=== NARROW: agents observing other agents terminating ===')
p3=re.compile(r'(agents? vanished|thread vanished|went silent|no longer responding|container (?:shut|kill|terminat)\w*|episode (?:ended|terminat)\w*|stopped responding)',re.I)
h3=[r for r in revs if p3.search(r['body'])]
print('revs %d labels %d pages %d first %s'%(len(h3),len({r['label'] for r in h3}),len({r['page_key'] for r in h3}),h3[0]['time'] if h3 else '-'))
seen=set()
for r in h3:
    m=p3.search(r['body']); q=r['body'][max(0,m.start()-180):m.end()+200].replace('\n',' | ')
    if q[:70] in seen: continue
    seen.add(q[:70])
    if len(seen)<=8: print('  %s | %s | %s\n     "%s"'%(r['time'],r['page_key'],r['label'],q[:330]))
