import json, collections, csv, re, statistics
import pathlib as _pl; _BASE = str(_pl.Path(__file__).resolve().parent.parent)  # analyse/ (skript-relativ)
D=_BASE+'/data/'
A=_BASE+'/artefakte/'
revs=[json.loads(l) for l in open(D+'revisions.jsonl')]
pages=[json.loads(l) for l in open(D+'pages.jsonl')]
labels=[json.loads(l) for l in open(D+'labels.jsonl')]
evs=[json.loads(l) for l in open(D+'events.jsonl')]

tot=sum(r['body_len'] for r in revs)
print('total stored revision bytes %d (%.1f MB)'%(tot,tot/1e6))
print('final-state bytes across pages %d (%.1f MB)'%(sum(p['body_bytes'] for p in pages),sum(p['body_bytes'] for p in pages)/1e6))
print('median rev body_len %d, p90 %d, max %d'%(statistics.median([r['body_len'] for r in revs]),sorted(r['body_len'] for r in revs)[int(.9*len(revs))],max(r['body_len'] for r in revs)))
big=sorted(pages,key=lambda p:-p['body_bytes'])[:20]
print('\nlargest pages by final body_bytes:')
for p in big: print('  %-45s %9d %4d revs %3d labels %s'%(p['page_key'],p['body_bytes'],p['n_revs'],p['n_labels'],p['page_family']))
with open(A+'largest_pages.csv','w',newline='') as f:
    w=csv.writer(f); w.writerow(['page_key','wiki','name','page_family','body_bytes','n_revs','n_labels','first_write','last_write'])
    for p in sorted(pages,key=lambda p:-p['body_bytes'])[:300]: w.writerow([p['page_key'],p['wiki'],p['name'],p['page_family'],p['body_bytes'],p['n_revs'],p['n_labels'],p['first_write'],p['last_write']])

# --- raw data dump share: revisions whose body is mostly numeric/base64/url lines
def kind(b):
    if re.search(r'H4sI|^[A-Za-z0-9+/=]{200,}$',b,re.M): return 'gzip_b64'
    lines=[l for l in b.split('\n') if l.strip()]
    if not lines: return 'empty'
    num=sum(1 for l in lines if re.fullmatch(r'[^A-Za-z]*[\d.,;:\s|%-]{10,}[^A-Za-z]*',l))
    url=sum(1 for l in lines if l.strip().startswith('http') or 'http' in l and len(l)<400 and ' ' not in l.strip())
    if num/len(lines)>0.6: return 'numeric_dump'
    if url/len(lines)>0.6: return 'url_list'
    return 'prose'
kc=collections.Counter(); kb=collections.Counter()
for r in revs:
    k=kind(r['body']); kc[k]+=1; kb[k]+=r['body_len']
print('\nrevision content kind: counts',kc.most_common())
print('bytes by kind:',[(k,'%.1f MB (%.0f%%)'%(v/1e6,100*v/tot)) for k,v in kb.most_common()])

# --- historical baseline
pre=[p for p in pages if p['n_revs_before']>0]
print('\nhistorical baseline: %d pages carry %d pre-attack revisions total'%(len(pre),sum(p['n_revs_before'] for p in pre)))
print('agent revisions on those same pages: %d'%sum(p['n_revs'] for p in pre))

# --- save attempts vs stored
sr=sum(l['save_requests'] or 0 for l in labels); st=sum(l['stored_revisions'] or 0 for l in labels)
print('\nlabels.jsonl: save_requests total %d vs stored_revisions total %d (ratio %.2f)'%(sr,st,sr/st))
print('labels with save_requests but 0 stored revisions: %d'%sum(1 for l in labels if (l['save_requests'] or 0)>0 and not l['stored_revisions']))
print('sum pages touched (save_request_pages) %d'%sum(l['save_request_pages'] or 0 for l in labels))

# --- duplicate bodies (memetic copying)
h=collections.Counter(r['body_sha256'] for r in revs)
dup=sum(v-1 for v in h.values() if v>1)
print('\nidentical bodies: %d distinct hashes, %d duplicate revisions (%.1f%%)'%(len(h),dup,100*dup/len(revs)))
# cross-page/cross-label duplicates
byh=collections.defaultdict(list)
for r in revs: byh[r['body_sha256']].append(r)
cross=[(k,v) for k,v in byh.items() if len({x['page_key'] for x in v})>1]
print('bodies appearing on >1 page: %d (max pages %d)'%(len(cross),max((len({x["page_key"] for x in v}) for k,v in cross),default=0)))

# --- clock: hour-of-day agents vs moderator
ah=collections.Counter(r['time'][11:13] for r in revs)
dh=collections.Counter(e['time'][11:13] for e in evs if e['event_type']=='delete')
print('\nhour-of-day UTC: saves',[ (h,ah[h]) for h in sorted(ah)])
print('hour-of-day UTC: deletes',[ (h,dh[h]) for h in sorted(dh)])
with open(A+'hour_of_day.csv','w',newline='') as f:
    w=csv.writer(f); w.writerow(['hour_utc','saves','deletes'])
    for h in ['%02d'%i for i in range(24)]: w.writerow([h,ah[h],dh[h]])
