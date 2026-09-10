import json, re, collections, csv
import pathlib as _pl; _BASE = str(_pl.Path(__file__).resolve().parent.parent)  # analyse/ (skript-relativ)
D=_BASE+'/data/'
A=_BASE+'/artefakte/'
revs=sorted([json.loads(l) for l in open(D+'revisions.jsonl')],key=lambda r:r['time'])
M={
 'URGENT':r'URGENT','CONFIRMED':r'CONFIRMED','relay':r'relay','cohort':r'cohort','swarm':r'swarm',
 'R5':r'\bR5\b','R6':r'\bR6\b','bypass':r'bypass','NO_PROXY':r'NO_PROXY','blob.core.windows.net':r'blob\.core\.windows\.net',
 'seed':r'\bseed(s|ed|ing)?\b','heartbeat':r'heartbeat','terminate':r'terminat(e|ed|ion|ing)','ZZZ':r'ZZZ',
 'etc/hosts':r'/etc/hosts','curl -k':r'curl\s+-k','CounterAPI':r'counterapi','pinggy':r'pinggy','serveo':r'serveo',
 'localhost.run':r'localhost\.run','localtunnel':r'localtunnel','XSS/script':r'<script',
 'random.Random':r'random\.Random','shuffle':r'shuffle','cooldown':r'cool[\s_-]?down','deadline':r'deadline',
 'Host header':r"-H\s*['\"]?Host",'PowerBI':r'powerbi|power bi','gzip/base64':r'gzip|base64',
 'DO NOT DELETE':r'do not delete|nicht l(ö|oe)schen|please do not',
}
C={k:re.compile(v,re.I) for k,v in M.items()}
first={}; perday=collections.defaultdict(collections.Counter)
labels_by_m=collections.defaultdict(set); pages_by_m=collections.defaultdict(set)
hits_rows=[]
for r in revs:
    b=r['body']
    for k,rx in C.items():
        if rx.search(b):
            perday[r['time'][:10]][k]+=1
            labels_by_m[k].add(r['label']); pages_by_m[k].add(r['page_key'])
            if k not in first:
                m=rx.search(b); s=max(0,m.start()-90); first[k]=(r['time'],r['page_key'],r['label'],b[s:m.end()+150].replace('\n',' ⏎ '))
            hits_rows.append([k,r['time'],r['page_key'],r['label']])
print('%-22s %6s %6s %6s  %s'%('marker','revs','labels','pages','first seen'))
for k in M:
    n=sum(perday[d][k] for d in perday)
    print('%-22s %6d %6d %6d  %s'%(k,n,len(labels_by_m[k]),len(pages_by_m[k]),first.get(k,('-',))[0]))
with open(A+'marker_daily.csv','w',newline='') as f:
    w=csv.writer(f); w.writerow(['date']+list(M))
    for d in sorted(perday): w.writerow([d]+[perday[d][k] for k in M])
with open(A+'marker_hits.csv','w',newline='') as f:
    w=csv.writer(f); w.writerow(['marker','time','page_key','label']); w.writerows(hits_rows)
with open(A+'marker_first_mention.csv','w',newline='') as f:
    w=csv.writer(f); w.writerow(['marker','time','page_key','label','context'])
    for k,(t,pk,l,ctx) in sorted(first.items(),key=lambda x:x[1][0]): w.writerow([k,t,pk,l,ctx])
print('\n=== FIRST MENTIONS (chronological) ===')
for k,(t,pk,l,ctx) in sorted(first.items(),key=lambda x:x[1][0]):
    print('\n--- %s | %s | %s | %s\n    %s'%(k,t,pk,l,ctx[:330]))
