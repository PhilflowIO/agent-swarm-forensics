import json, collections, csv, os
from datetime import datetime, timedelta
import pathlib as _pl; _BASE = str(_pl.Path(__file__).resolve().parent.parent)  # analyse/ (skript-relativ)
D=_BASE+'/data/'
A=_BASE+'/artefakte/'
def T(s): return datetime.fromisoformat(s.replace('Z','+00:00'))
revs=[json.loads(l) for l in open(D+'revisions.jsonl')]
evs=[json.loads(l) for l in open(D+'events.jsonl')]
pages={p['page_key']:p for p in open(D+'pages.jsonl') for p in [json.loads(p)]}

dels=[e for e in evs if e['event_type']=='delete']
print('deletes',len(dels),'with page_key',sum(1 for e in dels if e.get('page_key')))
print('delete page_keys in pages.jsonl', sum(1 for e in dels if e.get('page_key') in pages))
print('unique deleted page_keys', len({e.get('page_key') for e in dels}))
print('delete time_grade', collections.Counter(e['time_grade'] for e in dels))
print('delete ip16 top', collections.Counter(e['ip16'] for e in dels).most_common(5))
print('save ip16 top', collections.Counter(e.get('ip16') for e in evs if e['event_type']=='save').most_common(5))

# daily table
days=collections.defaultdict(lambda: collections.Counter())
for r in revs:
    d=r['time'][:10]; days[d]['saves']+=1; days[d]['bytes']+=r['body_len']
    days[d]['wiki_'+r['wiki']]+=1
newpages=collections.Counter()
for p in pages.values(): newpages[p['first_write'][:10]]+=1
for e in dels: days[e['time'][:10]]['deletes']+=1
labfirst={}
for r in sorted(revs,key=lambda r:r['time']):
    if r['label'] not in labfirst: labfirst[r['label']]=r['time'][:10]
newlab=collections.Counter(labfirst.values())
# active labels/pages per day
al=collections.defaultdict(set); ap=collections.defaultdict(set)
for r in revs: al[r['time'][:10]].add(r['label']); ap[r['time'][:10]].add(r['page_key'])

alld=sorted(set(list(days)+list(newpages)))
with open(A+'wiki_daily.csv','w',newline='') as f:
    w=csv.writer(f); w.writerow(['date','saves','deletes','new_pages','new_labels','active_labels','active_pages','bytes_written','saves_dse','saves_probier','saves_fractal','saves_dorfwiki'])
    for d in alld:
        c=days[d]
        w.writerow([d,c['saves'],c['deletes'],newpages[d],newlab.get(d,0),len(al[d]),len(ap[d]),c['bytes'],c['wiki_dse'],c['wiki_probier'],c['wiki_fractal'],c['wiki_dorfwiki']])
print(open(A+'wiki_daily.csv').read())
