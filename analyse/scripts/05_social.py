import json, collections, csv, itertools, statistics, random
random.seed(42)
import pathlib as _pl; _BASE = str(_pl.Path(__file__).resolve().parent.parent)  # analyse/ (skript-relativ)
D=_BASE+'/data/'
A=_BASE+'/artefakte/'
revs=[json.loads(l) for l in open(D+'revisions.jsonl')]
pages=[json.loads(l) for l in open(D+'pages.jsonl')]
labels=[json.loads(l) for l in open(D+'labels.jsonl')]
P={p['page_key']:p for p in pages}

cnt=collections.Counter(r['label'] for r in revs)
v=sorted(cnt.values())
def gini(x):
    x=sorted(x); n=len(x); s=sum(x)
    return (2*sum((i+1)*xi for i,xi in enumerate(x)))/(n*s)-(n+1)/n
print('labels n=%d (incl. empty). revs total %d'%(len(cnt),sum(cnt.values())))
print('Gini(revs per label)=%.3f'%gini(v))
print('median %d  mean %.2f  p90 %d  max %d'%(statistics.median(v),statistics.mean(v),v[int(.9*len(v))],v[-1]))
print('share of labels with exactly 1 rev: %d (%.1f%%)'%(sum(1 for x in v if x==1),100*sum(1 for x in v if x==1)/len(v)))
tot=sum(v); top=sorted(cnt.values(),reverse=True)
for k in (1,10,50,100):
    print('  top%-4d labels = %.1f%% of revisions'%(k,100*sum(top[:k])/tot))
print('top labels:',cnt.most_common(12))

# pages per label / labels per page
lp=collections.Counter(p['n_labels'] for p in pages)
print('\nlabels-per-page: 1-label pages %d (%.1f%%), max %d'%(lp[1],100*lp[1]/len(pages),max(p['n_labels'] for p in pages)))
hubs=sorted(pages,key=lambda p:-p['n_labels'])[:20]
print('hub pages (n_labels, n_revs, bytes, family):')
for p in hubs: print('  %-45s %4d %5d %9d %s'%(p['page_key'],p['n_labels'],p['n_revs'],p['body_bytes'],p['page_family']))
with open(A+'hub_pages.csv','w',newline='') as f:
    w=csv.writer(f); w.writerow(['page_key','wiki','name','page_family','n_labels','n_revs','body_bytes','first_write','last_write'])
    for p in sorted(pages,key=lambda p:-p['n_labels'])[:200]:
        w.writerow([p['page_key'],p['wiki'],p['name'],p['page_family'],p['n_labels'],p['n_revs'],p['body_bytes'],p['first_write'],p['last_write']])

# ---- co-activity graph (labels sharing a page). Exclude mega-hubs (n_labels>50) as they connect everyone.
CAP=50
edges=collections.Counter()
for p in pages:
    ls=sorted(set(p['labels']))
    if 2<=len(ls)<=CAP:
        for a,b in itertools.combinations(ls,2): edges[(a,b)]+=1
nodes=set(); 
for a,b in edges: nodes.add(a); nodes.add(b)
print('\nco-activity graph (pages with 2..%d labels): nodes %d  edges %d'%(CAP,len(nodes),len(edges)))
import networkx as nx
G=nx.Graph()
for (a,b),wt in edges.items(): G.add_edge(a,b,weight=wt)
comps=sorted(nx.connected_components(G),key=len,reverse=True)
print('components %d, sizes top10 %s'%(len(comps),[len(c) for c in comps[:10]]))
gc=G.subgraph(comps[0])
print('giant component: n=%d m=%d density=%.5f avg_deg=%.2f'%(gc.number_of_nodes(),gc.number_of_edges(),nx.density(gc),2*gc.number_of_edges()/gc.number_of_nodes()))
print('transitivity %.4f  avg clustering %.4f'%(nx.transitivity(gc),nx.average_clustering(gc)))
# communities
try:
    from networkx.algorithms.community import louvain_communities, modularity
    com=louvain_communities(gc,seed=42,weight='weight')
    print('louvain communities %d, modularity %.3f, sizes top10 %s'%(len(com),modularity(gc,com,weight='weight'),sorted([len(c) for c in com],reverse=True)[:10]))
    # community -> page_family profile
    lab2com={l:i for i,c in enumerate(com) for l in c}
    prof=collections.defaultdict(collections.Counter)
    for p in pages:
        for l in set(p['labels']):
            if l in lab2com: prof[lab2com[l]][p['page_family']]+=1
    rows=[]
    for i in sorted(com,key=len,reverse=True)[:12]:
        pass
    for ci in sorted(range(len(com)),key=lambda i:-len(com[i]))[:12]:
        top=[f'{k}:{n}' for k,n in prof[ci].most_common(4)]
        print('  C%-3d n=%-4d %s'%(ci,len(com[ci]),' | '.join(top)))
        rows.append([ci,len(com[ci]),' | '.join(top)])
    with open(A+'communities.csv','w',newline='') as f:
        w=csv.writer(f); w.writerow(['community','n_labels','top_page_families']); w.writerows(rows)
    with open(A+'coactivity_edges.csv','w',newline='') as f:
        w=csv.writer(f); w.writerow(['source','target','weight','src_community','tgt_community'])
        for (a,b),wt in sorted(edges.items(),key=lambda x:-x[1]):
            w.writerow([a,b,wt,lab2com.get(a,-1),lab2com.get(b,-1)])
except Exception as ex: print('community fail',ex)

# ---- task cluster separation: do labels stick to one page_family?
fam=collections.defaultdict(collections.Counter)
for p in pages:
    if p['page_family'].startswith(('datausa','oecd','ihme','uefa','sec')) or 'sec' in p['page_family']:
        for l in set(p['labels']): fam[l][p['page_family'].split('-')[0]]+=1
pure=[1 if len(c)==1 else 0 for c in fam.values()]
print('\nlabels touching >=1 task-family: %d, of which single-family: %d (%.1f%%)'%(len(pure),sum(pure),100*sum(pure)/len(pure)))
print('family dist over labels', collections.Counter(k for c in fam.values() for k in c).most_common())
