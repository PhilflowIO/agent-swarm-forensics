import json, collections, os, sys
import pathlib as _pl; _BASE = str(_pl.Path(__file__).resolve().parent.parent)  # analyse/ (skript-relativ)
D=_BASE+'/data/'
A=_BASE+'/artefakte/'
os.makedirs(A, exist_ok=True)
log=open(_BASE+'/artefakte/_audit.log','a')
def L(*a): s=' '.join(map(str,a)); print(s); log.write(s+'\n')

revs=[json.loads(l) for l in open(D+'revisions.jsonl')]
evs=[json.loads(l) for l in open(D+'events.jsonl')]
pages=[json.loads(l) for l in open(D+'pages.jsonl')]
labels=[json.loads(l) for l in open(D+'labels.jsonl')]
L('raw rows: revisions',len(revs),'events',len(evs),'pages',len(pages),'labels',len(labels))

# time span
ts=sorted(r['time'] for r in revs if r.get('time'))
L('revision time span', ts[0], '->', ts[-1], 'null times', sum(1 for r in revs if not r.get('time')))
ets=sorted(e['time'] for e in evs if e.get('time'))
L('event time span', ets[0],'->',ets[-1], 'null', sum(1 for e in evs if not e.get('time')))

L('wiki dist revisions', collections.Counter(r['wiki'] for r in revs))
L('wiki dist events', collections.Counter((e.get('wiki'),e['event_type']) for e in evs))
L('unique labels in revisions', len({r['label'] for r in revs}))
L('empty-label revisions', sum(1 for r in revs if not r['label']))
L('unique pages in revisions', len({r['page_key'] for r in revs}))
L('total body bytes', sum(r['body_len'] for r in revs))
L('time_grade dist', collections.Counter(r['time_grade'] for r in revs))
L('uncertainty seconds dist', collections.Counter(r['uncertainty_seconds'] for r in revs).most_common(10))
L('body_encoding', collections.Counter(r['body_encoding'] for r in revs))

# labels file
L('labels: is_human_handle', collections.Counter(l['is_human_handle'] for l in labels))
L('labels: empty name rows', sum(1 for l in labels if not l['label']))
L('pages: deleted_live', collections.Counter(p['deleted_live'] for p in pages))
L('pages: n_revs_before>0', sum(1 for p in pages if p['n_revs_before']>0))
L('sum n_revs_before', sum(p['n_revs_before'] for p in pages))
L('sum n_deletions', sum(p['n_deletions'] for p in pages), 'sum n_recreations', sum(p['n_recreations'] for p in pages))
log.close()
