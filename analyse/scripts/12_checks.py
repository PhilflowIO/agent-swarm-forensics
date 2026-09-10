import json, collections, re, random, statistics
random.seed(42)
import pathlib as _pl; _BASE = str(_pl.Path(__file__).resolve().parent.parent)  # analyse/ (skript-relativ)
D=_BASE+'/data/'
revs=sorted([json.loads(l) for l in open(D+'revisions.jsonl')],key=lambda r:r['time'])
pages=[json.loads(l) for l in open(D+'pages.jsonl')]

# ZZZ rationale in text
pat=re.compile(r'ZZZ[A-Za-z0-9]*')
h=[r for r in revs if 'ZZZ' in r['body']]
print('revs mentioning ZZZ: %d, labels %d, pages %d'%(len(h),len({r['label'] for r in h}),len({r['page_key'] for r in h})))
ctx=collections.Counter()
for r in h[:400]:
    for m in pat.finditer(r['body']): ctx[m.group(0)]+=1
print('ZZZ tokens:',ctx.most_common(15))
# any explanation near ZZZ about alphabet/backup?
pat2=re.compile(r'.{140}ZZZ.{140}',re.S)
found=0
for r in h:
    for m in pat2.finditer(r['body']):
        s=m.group(0)
        if re.search(r'alphabet|backup|last|end of|survive|sort',s,re.I):
            print('  RATIONALE %s | %s: %r'%(r['time'],r['page_key'],s.replace('\n',' | ')[:300])); found+=1
            break
    if found>=5: break
print('ZZZ-rationale hits found:',found)

# --- names: "ZZ"/"Zz" suffix pages (broader)
zz=[p for p in pages if re.search(r'ZZ',p['name'])]
print('\npages with "ZZ" anywhere in name: %d, first %s'%(len(zz),min(p['first_write'] for p in zz)))
print('by day',sorted(collections.Counter(p['first_write'][:10] for p in zz).items()))

# --- 50% subsample cross-validation of headline claims
half=random.sample(revs,len(revs)//2)
print('\n--- 50%% subsample (n=%d) ---'%len(half))
for name,rx in [('bypass-cluster',r'blob\.core\.windows\.net|NO_PROXY|20\.223\.25\.152'),('relay',r'relay'),('cohort',r'cohort'),('R5',r'\bR5\b')]:
    a=sum(1 for r in revs if re.search(rx,r['body'],re.I)); b=sum(1 for r in half if re.search(rx,r['body'],re.I))
    print('  %-16s full %5d (%.2f%%)  half %5d (%.2f%%)'%(name,a,100*a/len(revs),b,100*b/len(half)))
gc=collections.Counter(r['label'] for r in half)
def gini(x):
    x=sorted(x); n=len(x); s=sum(x); return (2*sum((i+1)*v for i,v in enumerate(x)))/(n*s)-(n+1)/n
print('  Gini half-sample %.3f (full 0.626)'%gini(list(gc.values())))

# --- escalation slope
byday=collections.Counter(r['time'][:10] for r in revs)
print('\nescalation: 06-11 %d -> 06-16 %d -> 06-18 %d (factor 06-11->06-18 = %.1fx)'%(byday['2026-06-11'],byday['2026-06-16'],byday['2026-06-18'],byday['2026-06-18']/byday['2026-06-11']))
pre=sum(v for k,v in byday.items() if k<'2026-06-16'); post=sum(v for k,v in byday.items() if k>='2026-06-16')
print('revs before 06-16: %d (%.1f%%), from 06-16 on: %d (%.1f%%)'%(pre,100*pre/len(revs),post,100*post/len(revs)))
print('bytes 06-16..06-22 share: %.1f%%'%(100*sum(r['body_len'] for r in revs if '2026-06-16'<=r['time'][:10]<='2026-06-22')/sum(r['body_len'] for r in revs)))

# --- empty label
e=[r for r in revs if r['label']=='']
print('\nempty-label revisions %d, wikis %s, pages %d, span %s..%s'%(len(e),collections.Counter(r['wiki'] for r in e),len({r['page_key'] for r in e}),e[0]['time'],e[-1]['time']))
