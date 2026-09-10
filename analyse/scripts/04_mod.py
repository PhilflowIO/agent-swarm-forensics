import json, collections, csv
import pathlib as _pl; _BASE = str(_pl.Path(__file__).resolve().parent.parent)  # analyse/ (skript-relativ)
D=_BASE+'/data/'
A=_BASE+'/artefakte/'
evs=[json.loads(l) for l in open(D+'events.jsonl')]
pages=[json.loads(l) for l in open(D+'pages.jsonl')]
P={p['page_key']:p for p in pages}
dels=sorted([e for e in evs if e['event_type']=='delete'],key=lambda e:e['time'])
# is deletion alphabetical within a session?
import re
def nm(e): return e['page_key'].split('~',1)[1] if '~' in e['page_key'] else e['page_key']
# per day: measure monotonic-increasing fraction of consecutive names
byday=collections.defaultdict(list)
for e in dels: byday[e['time'][:10]].append(nm(e))
print('day  n  frac_alpha_ascending  first  last')
for d in sorted(byday):
    L=byday[d]
    if len(L)<2: continue
    asc=sum(1 for a,b in zip(L,L[1:]) if b.upper()>=a.upper())/(len(L)-1)
    print('%s %5d %.2f  %-30s %-30s'%(d,len(L),asc,L[0][:30],L[-1][:30]))
# Z-bucket survival: do Z pages get deleted later?
import statistics
from datetime import datetime
def T(s): return datetime.fromisoformat(s.replace('Z','+00:00'))
fd={}
for e in dels: fd.setdefault(e['page_key'],e['time'])
byb=collections.defaultdict(list)
for pk,p in P.items():
    if pk in fd: byb[p['bucket']].append((T(fd[pk])-T(p['first_write'])).total_seconds()/3600)
print('\nbucket median lifetime h (n):')
for b in sorted(byb,key=lambda b:-statistics.median(byb[b])):
    if len(byb[b])>=5: print('  %-6s n=%-5d median=%.0f'%(b,len(byb[b]),statistics.median(byb[b])))
# reverts + probes
print('\nreverts:')
for e in evs:
    if e['event_type']=='revert': print(' ',e['time'],e.get('page_key'),e.get('actor_label'),e.get('change_summary'))
print('\nprobes (101) request_action counter:',collections.Counter(e['request_action'] for e in evs if e['event_type']=='probe').most_common())
print('probe days',collections.Counter(e['time'][:10] for e in evs if e['event_type']=='probe').most_common())
print('probe ip16',collections.Counter(e['ip16'] for e in evs if e['event_type']=='probe').most_common(8))
