import json, difflib, os, re, sys
from collections import defaultdict
D = "/home/philflow/Dokumente/coding/research/agent-swarm-forensics/analyse/data/"
def load(fn):
    out=[]
    with open(D+fn) as f:
        for i,l in enumerate(f,1):
            o=json.loads(l); o["_line"]=i; out.append(o)
    return out
_revs=None
def revs():
    global _revs
    if _revs is None: _revs=load("revisions.jsonl")
    return _revs
def bypage():
    d=defaultdict(list)
    for r in revs(): d[r["page_key"]].append(r)
    for k in d: d[k].sort(key=lambda r:r["seq"])
    return d
def added(prev, cur):
    """lines added in cur relative to prev (both body strings)"""
    a=(prev or "").splitlines()
    b=(cur or "").splitlines()
    sm=difflib.SequenceMatcher(None,a,b,autojunk=False)
    out=[]
    for tag,i1,i2,j1,j2 in sm.get_opcodes():
        if tag in ("insert","replace"):
            out.extend(b[j1:j2])
    return out
def page_deltas(pk, bp=None):
    bp = bp or bypage()
    rs = bp[pk]
    res=[]
    prev=""
    for r in rs:
        res.append((r, added(prev, r["body"])))
        prev=r["body"]
    return res
