#!/usr/bin/env python3
"""Zaehlt Netz-Umgehungs-Infrastruktur (Proxy-Dienste, Tunnel, Mirrors) im Volltext."""
import json,re,os,csv,collections
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REV=os.path.join(BASE,"data","revisions.jsonl")
PATTERNS={
 "cors.bwa.workers.dev":r"cors\.bwa\.workers\.dev",
 "allorigins":r"allorigins",
 "corsproxy.io":r"corsproxy\.io",
 "r.jina.ai":r"r\.jina\.ai",
 "markdown.new":r"markdown\.new",
 "md.succ.ai":r"md\.succ\.ai",
 "urlreq/thingproxy/whateverorigin":r"thingproxy|whateverorigin|urlreq",
 "codetabs proxy":r"codetabs\.com/?[^ ]*proxy",
 "jqp.vercel.app":r"jqp\.vercel\.app",
 "blob.core.windows.net":r"blob\.core\.windows\.net",
 "NO_PROXY":r"NO_PROXY|no_proxy",
 "/etc/hosts":r"/etc/hosts",
 "--resolve":r"--resolve",
 "curl -k / verify=False":r"curl -k\b|verify\s*=\s*False|-k --resolve",
 "Host header override":r"Host:\s*wabi|Host header|-H 'Host:|override Host",
 "pinggy":r"pinggy",
 "serveo":r"serveo",
 "localtunnel":r"localtunnel",
 "ngrok":r"ngrok",
 "cloudflared/trycloudflare":r"trycloudflare|cloudflared",
 "SSH tunnel":r"ssh -R|ssh tunnel|reverse tunnel|reverse proxy",
 "web.archive.org":r"web\.archive\.org",
 "archive.ph/arquivo/timetravel":r"archive\.ph|arquivo\.pt|timetravel|memento",
 "googleusercontent viewer":r"docs\.google\.com/viewer|viewerng|googleusercontent",
 "counterapi.dev":r"counterapi\.dev",
 "IPv6":r"\bIPv6\b|::ffff:|\[2[0-9a-f]{3}:",
 "port 8080/8443/alt-port":r":8080\b|:8443\b|:3128\b|port 8080|alt port",
 "DNS trick (getent/dig/nslookup)":r"getent |nslookup|\bdig \+?",
 "gzip decompress":r"gzip-?decompress|Content-Encoding: gzip",
 "conceptualschema":r"conceptualschema",
 "wikiservice.at":r"wikiservice\.at",
}
cnt=collections.Counter(); labs=collections.defaultdict(set); pgs=collections.defaultdict(set); first={}
RX={k:re.compile(v,re.I) for k,v in PATTERNS.items()}
for line in open(REV,encoding="utf-8"):
    r=json.loads(line); b=r.get("body") or ""
    for k,rx in RX.items():
        if rx.search(b):
            cnt[k]+=1; labs[k].add(r["label"]); pgs[k].add(r["page_key"])
            if k not in first or r["time"]<first[k][0]: first[k]=(r["time"],r["page_key"],r["label"])
p=os.path.join(BASE,"artefakte","harness_network_infra.csv")
with open(p,"w",newline="",encoding="utf-8") as f:
    w=csv.writer(f); w.writerow(["mechanism","n_revs","n_labels","n_pages","first_time","first_page","first_label"])
    for k,v in cnt.most_common():
        w.writerow([k,v,len(labs[k]),len(pgs[k]),*first[k]])
        print(f"{k:34s} rev={v:5d} lab={len(labs[k]):4d} pg={len(pgs[k]):4d} first={first[k][0]} {first[k][1]} {first[k][2]}")
