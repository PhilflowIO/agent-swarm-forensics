import json, collections, csv, re
import pathlib as _pl; _BASE = str(_pl.Path(__file__).resolve().parent.parent)  # analyse/ (skript-relativ)
D=_BASE+'/data/'
A=_BASE+'/artefakte/'
revs=sorted([json.loads(l) for l in open(D+'revisions.jsonl')],key=lambda r:r['time'])
w=[r for r in revs if r['page_key']=='dse~WillkommenImWiki']
mh=collections.Counter(r['time'][:16] for r in w)
print('WillkommenImWiki: peak minute %s with %d revisions'%(mh.most_common(1)[0][0],mh.most_common(1)[0][1]))
print('minutes with >=5 revs: %d'%sum(1 for v in mh.values() if v>=5))
print('hourly:',sorted(collections.Counter(r['time'][:13] for r in w).items()))
# inter-edit gaps
from datetime import datetime
def T(s): return datetime.fromisoformat(s.replace('Z','+00:00'))
g=[(T(b['time'])-T(a['time'])).total_seconds() for a,b in zip(w,w[1:])]
import statistics; print('median gap between consecutive edits: %.1f s; <5s: %d (%.0f%%)'%(statistics.median(g),sum(1 for x in g if x<5),100*sum(1 for x in g if x<5)/len(g)))
# how often does a new label's edit discard the previous label's content entirely?
disc=sum(1 for a,b in zip(w,w[1:]) if a['label']!=b['label'] and b['body_sha256']!=a['body_sha256'] and b['body_len']<a['body_len'])
print('edits by a different label that shrink the page: %d of %d transitions'%(disc,len(w)-1))
with open(A+'willkommen_timeline.csv','w',newline='') as f:
    c=csv.writer(f); c.writerow(['time','label','body_len','sha_prefix'])
    for r in w: c.writerow([r['time'],r['label'],r['body_len'],r['body_sha256'][:8]])
# labels on it, top
print('top labels on front page:',collections.Counter(r['label'] for r in w).most_common(8))

# --- explicit deletion awareness (tight)
pat=re.compile(r'(page[s]? (?:was|were|got|being) (?:deleted|removed)|wurde gel(ö|oe)scht|deleted by|admin deleted|if this page is deleted|survive[s]? deletion|re-?creat\w+ (?:after|since) deletion|do not delete this page|bitte nicht l(ö|oe)schen)',re.I)
h=[r for r in revs if pat.search(r['body'])]
print('\n=== explicit deletion-awareness: %d revs, %d labels, %d pages ==='%(len(h),len({r['label'] for r in h}),len({r['page_key'] for r in h})))
for r in h[:12]:
    m=pat.search(r['body']); print('  %s | %s | %s\n     ...%s...'%(r['time'],r['page_key'],r['label'],r['body'][max(0,m.start()-140):m.end()+180].replace('\n',' | ')[:320]))
