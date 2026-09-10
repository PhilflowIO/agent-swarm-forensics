#!/usr/bin/env python3
"""Volltext-Grep ueber revisions.jsonl mit Beleg-Metadaten.
Usage: 20_grep.py <regex> [--ctx N] [--max M] [--count-only] [--sort]
Ausgabe: page_key | time | label | snippet
"""
import json, re, sys, os
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REV = os.path.join(BASE, "data", "revisions.jsonl")

def load():
    with open(REV, encoding="utf-8") as f:
        for line in f:
            yield json.loads(line)

def main():
    pat = sys.argv[1]
    ctx = 160; mx = 60; count_only = "--count-only" in sys.argv
    if "--ctx" in sys.argv: ctx = int(sys.argv[sys.argv.index("--ctx")+1])
    if "--max" in sys.argv: mx = int(sys.argv[sys.argv.index("--max")+1])
    rx = re.compile(pat, re.I if "--cs" not in sys.argv else 0)
    hits = []
    for r in load():
        b = r.get("body") or ""
        for m in rx.finditer(b):
            hits.append((r["page_key"], r["time"], r["label"],
                         b[max(0,m.start()-ctx):m.end()+ctx].replace("\n"," ")))
            break
    hits.sort(key=lambda h: h[1])
    print(f"# HITS(revisions)={len(hits)} labels={len({h[2] for h in hits})} pages={len({h[0] for h in hits})}", file=sys.stderr)
    if count_only: return
    for h in hits[:mx]:
        print(f"{h[0]} | {h[1]} | {h[2]} | ...{h[3]}...")

if __name__ == "__main__":
    main()
