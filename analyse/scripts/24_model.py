#!/usr/bin/env python3
import json,re,os,collections,csv
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAT={
 "gpt-N":r"\bgpt[- ]?[0-9][^ ]{0,8}",
 "GPT bare":r"\bGPT\b",
 "o3/o4/o1":r"\bo[134](?:-mini|-pro)?\b",
 "Codex":r"\bcodex\b",
 "ChatGPT":r"ChatGPT",
 "knowledge cutoff":r"knowledge cut[- ]?off|training cut[- ]?off|cutoff date|data cut[-]?off",
 "training data":r"training data|trained on|my training",
 "language model":r"language model|\bLLM\b|large language",
 "as an AI":r"as an AI|I am an AI|I'm an AI",
 "model version":r"model version|model name|model id|which model",
 "Anthropic/Claude/Gemini":r"anthropic|claude|gemini|llama|mistral",
 "OpenAI":r"OpenAI|openai",
 "assistant/agent self":r"\bI am (an|a) (agent|assistant|model)",
 "system prompt content":r"system prompt|my instructions|my system",
}
RX={k:re.compile(v,re.I) for k,v in PAT.items()}
cnt=collections.Counter(); labs=collections.defaultdict(set); ex=collections.defaultdict(list); toks=collections.Counter()
rx_gpt=re.compile(r"\bgpt[- ]?[0-9][\w.\-]{0,6}",re.I)
for line in open(os.path.join(BASE,"data","revisions.jsonl"),encoding="utf-8"):
    r=json.loads(line); b=r.get("body") or ""
    for k,rx in RX.items():
        m=rx.search(b)
        if m:
            cnt[k]+=1; labs[k].add(r["label"])
            if len(ex[k])<6:
                ex[k].append((r["time"],r["page_key"],r["label"],b[max(0,m.start()-150):m.end()+150].replace("\n"," ")))
    for t in rx_gpt.findall(b): toks[t.lower()]+=1
for k in PAT:
    print(f"=== {k}: revs={cnt[k]} labels={len(labs[k])}")
    for e in ex[k][:4]: print("   ",e[0],"|",e[1],"|",e[2],"|",e[3][:300])
print("=== gpt-token histogram:", toks.most_common(20))
