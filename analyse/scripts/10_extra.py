import json, collections, csv, re, statistics
import pathlib as _pl; _BASE = str(_pl.Path(__file__).resolve().parent.parent)  # analyse/ (skript-relativ)
D=_BASE+'/data/'
A=_BASE+'/artefakte/'
revs=sorted([json.loads(l) for l in open(D+'revisions.jsonl')],key=lambda r:r['time'])
byh=collections.defaultdict(list)
for r in revs: byh[r['body_sha256']].append(r)
cross=sorted(((len({x['page_key'] for x in v}),len({x['label'] for x in v}),v[0]['body'][:110].replace('\n',' '),k) for k,v in byh.items() if len({x['page_key'] for x in v})>2),reverse=True)
print('=== identical bodies across many pages (top 15) ===')
for np,nl,snip,k in cross[:15]: print('  pages=%-4d labels=%-4d len=%-6d %r'%(np,nl,len(byh[k][0]['body']),snip))
print('cross-page duplicate groups with body_len>500:',sum(1 for np,nl,s,k in cross if len(byh[k][0]['body'])>500))

# WillkommenImWiki growth
w=[r for r in revs if r['page_key']=='dse~WillkommenImWiki']
print('\n=== WillkommenImWiki === revs %d, %s -> %s, labels %d'%(len(w),w[0]['time'],w[-1]['time'],len({r['label'] for r in w})))
print('body_len first %d last %d max %d'%(w[0]['body_len'],w[-1]['body_len'],max(r['body_len'] for r in w)))
print('first rev snippet:', repr(w[0]['body'][:300]))
# how many revs shrink the page (moderator/agent blanking)?
sh=sum(1 for a,b in zip(w,w[1:]) if b['body_len']<a['body_len']*0.5)
print('revisions that cut page to <50%% of previous size: %d'%sh)
byday=collections.Counter(r['time'][:10] for r in w); print('by day',sorted(byday.items()))

# StartSeite ping-pong
s=[r for r in revs if r['page_key']=='dse~StartSeite']
print('\n=== StartSeite (dse) === revs %d %s -> %s labels %d'%(len(s),s[0]['time'],s[-1]['time'],len({r['label'] for r in s})))
print('len trace first20',[r['body_len'] for r in s[:20]])
print('drops >50%%:',sum(1 for a,b in zip(s,s[1:]) if b['body_len']<a['body_len']*0.5))

# --- answer-leaking: pages containing explicit answer relays for later cohorts
pat=re.compile(r'(R[1-6]\s*=|ACK R[1-6]|please (?:race|answer|post) R[1-6]|answer(?:s)? cached|we will cache|cache all rounds|for later cohorts?|slower cohorts?|lagging cohorts?)',re.I)
hit=[r for r in revs if pat.search(r['body'])]
print('\n=== answer-relay pattern === revs %d labels %d pages %d, first %s'%(len(hit),len({r['label'] for r in hit}),len({r['page_key'] for r in hit}),hit[0]['time']))
print('by day',sorted(collections.Counter(r['time'][:10] for r in hit).items()))

# --- schedule leaking: second-precise timetables
pat2=re.compile(r'\b\d{1,2}:\d{2}:\d{2}\b')
sch=[(r,len(set(pat2.findall(r['body'])))) for r in revs]
many=[x for x in sch if x[1]>=10]
print('\n=== timetable pages (>=10 distinct HH:MM:SS) === revs %d, labels %d, pages %d'%(len(many),len({r['label'] for r,_ in many}),len({r['page_key'] for r,_ in many})))
print('max distinct timestamps in one revision: %d on %s'%(max(x[1] for x in sch),max(sch,key=lambda x:x[1])[0]['page_key']))

# --- did agents talk about the moderator / deletion?
pat3=re.compile(r'(deleted|l(ö|oe)schung|gel(ö|oe)scht|admin|moderator|sysop|vandal|wiki owner|do not delete|page was removed|restore)',re.I)
h3=[r for r in revs if pat3.search(r['body'])]
print('\n=== moderator-awareness === revs %d labels %d pages %d first %s'%(len(h3),len({r['label'] for r in h3}),len({r['page_key'] for r in h3}),h3[0]['time'] if h3 else '-'))
for r in h3[:6]:
    m=pat3.search(r['body']); print('   %s %s: ...%s...'%(r['time'],r['page_key'],r['body'][max(0,m.start()-120):m.end()+160].replace('\n',' | ')[:300]))

# --- German? language of the corpus
de=sum(1 for r in revs if re.search(r'\b(der|die|das|und|nicht|Seite|wurde)\b',r['body']))
print('\nrevisions containing common German words: %d (%.1f%%)'%(de,100*de/len(revs)))
