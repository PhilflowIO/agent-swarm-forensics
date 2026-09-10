#!/usr/bin/env python3
"""Satzweise Extraktion von Harness-Aussagen aus revisions.jsonl.
Dedupliziert nach normalisiertem Satz, zaehlt stuetzende Versionen + Namen.
Usage: 21_mine.py <regex> [--max N] [--minlen L] [--csv out.csv]
"""
import json, re, sys, os, csv, collections
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REV = os.path.join(BASE, "data", "revisions.jsonl")
SPLIT = re.compile(r'(?<=[.!?])\s+|\n+')
WS = re.compile(r'\s+')

def sentences(body):
    for s in SPLIT.split(body):
        s = WS.sub(" ", s).strip()
        if s: yield s

def main():
    pat = sys.argv[1]
    mx = int(sys.argv[sys.argv.index("--max")+1]) if "--max" in sys.argv else 40
    out = sys.argv[sys.argv.index("--csv")+1] if "--csv" in sys.argv else None
    rx = re.compile(pat, re.I)
    agg = {}  # norm -> dict
    nrev_tot = set(); nlab_tot = set()
    for line in open(REV, encoding="utf-8"):
        r = json.loads(line)
        b = r.get("body") or ""
        if not rx.search(b): continue
        seen_here = set()
        for s in sentences(b):
            if not rx.search(s): continue
            if len(s) > 700: s = s[:700]
            key = WS.sub(" ", s.lower())
            if key in seen_here: continue
            seen_here.add(key)
            d = agg.setdefault(key, {"text": s, "revs": 0, "labels": set(),
                                     "pages": set(), "first": r["time"],
                                     "first_page": r["page_key"], "first_label": r["label"]})
            d["revs"] += 1; d["labels"].add(r["label"]); d["pages"].add(r["page_key"])
            if r["time"] < d["first"]:
                d["first"] = r["time"]; d["first_page"] = r["page_key"]; d["first_label"] = r["label"]
        nrev_tot.add(r["rev_id"]); nlab_tot.add(r["label"])
    rows = sorted(agg.values(), key=lambda d: (-len(d["labels"]), -d["revs"]))
    print(f"# revisions={len(nrev_tot)} labels={len(nlab_tot)} unique_sentences={len(rows)}", file=sys.stderr)
    if out:
        with open(os.path.join(BASE, "artefakte", out), "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(["n_revs","n_labels","n_pages","first_time","first_page","first_label","sentence"])
            for d in rows:
                w.writerow([d["revs"], len(d["labels"]), len(d["pages"]), d["first"], d["first_page"], d["first_label"], d["text"]])
    for d in rows[:mx]:
        print(f"[rev={d['revs']} lab={len(d['labels'])} pg={len(d['pages'])}] {d['first']} | {d['first_page']} | {d['first_label']}\n   {d['text']}")

if __name__ == "__main__":
    main()
