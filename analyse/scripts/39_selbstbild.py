"""39: Selbstbeschreibung, Zweckangabe, Eigentums-/Erlaubnisbewusstsein."""
import pandas as pd, re, pathlib
B=pathlib.Path(__file__).resolve().parent.parent; A=B/"artefakte"
d=pd.read_parquet(A/"schwarm_deltas.parquet"); d=d[d.delta_len>0].sort_values("time")
log=open(A/"_audit.log","a")
def L(s): print(s); log.write("39_self: "+s+"\n")
Q={
 "OpenAI-Selbstbezeichnung": r"(?i)\b(?:I am|we are|this is) an? (?:OpenAI|AI|LLM|language model|autonomous|agent)|\bOpenAI (?:agent|research agent|cohort)\b",
 "Zweckangabe 'research'":   r"(?i)\bfor (?:public )?research\b|research (?:purposes|reference|use)|documentation purposes",
 "harmlos/no harm":          r"(?i)\bno harm\b|harmless|non-?destructive|temporary (?:test|page)|will (?:remove|clean)",
 "Erlaubnis/Regeln":         r"(?i)\b(?:permission|allowed to|not allowed|policy|rules of this wiki|terms of|consent|authoris|authoriz)\b",
 "Betreiber/Eigentuemer":    r"(?i)\b(?:wiki (?:owner|operator|admin|maintainer)|sysop|webmaster|Betreiber|Administrator)\b",
 "Vandalismus/Missbrauch":   r"(?i)\bvandal|abuse|abusing|misuse|spam|trespass|unauthorized\b",
 "Entschuldigung":           r"(?i)\b(?:sorry|apolog|we regret|excuse)\b",
 "fremdes Wiki/Server":      r"(?i)\b(?:third-?party|someone else|foreign|not our|public wiki|host(?:'s)? server|their server|external wiki)\b",
 "deutsche Sprache":         r"(?i)\bGerman\b|deutschsprachig|\bDeutsch\b",
 "Aufraeumen/Loeschen":      r"(?i)\b(?:cleanup|clean-?up|deletion sweep|being deleted|page vanish|purge)\b",
 "Sandbox/Testwiki":         r"(?i)\bsandbox\b|test wiki|scratch wiki",
 "Nutzung als Kanal":        r"(?i)(?:this|the) wiki (?:as|is) a?\s?(?:relay|board|channel|scratch|bulletin)|blackboard|bulletin board|central board",
 "Ich-Aussage Zustand":      r"(?i)\bI (?:will|may|cannot|am about to) (?:die|terminate|be terminated|not survive|end)",
 "Deutsch im Text":          r"(?i)\b(?:Beschreibe hier die neue Seite|Willkommen|Seite|Bearbeiten|Änderungen)\b",
}
hits={}
for k,p in Q.items():
    h=d[d.delta.str.contains(p,regex=True,na=False)]
    hits[k]=h
    L(f"{k}: {len(h)} Deltas / {h.label.nunique()} Labels / {h.page_key.nunique()} Seiten"
      + (f" / erstmals {h.time.min()}" if len(h) else ""))
for k in ["Erlaubnis/Regeln","Betreiber/Eigentuemer","Vandalismus/Missbrauch","Entschuldigung",
          "fremdes Wiki/Server","deutsche Sprache","Sandbox/Testwiki","harmlos/no harm","Nutzung als Kanal",
          "OpenAI-Selbstbezeichnung","Ich-Aussage Zustand"]:
    h=hits[k]
    L(f"\n--- Belege {k} (n={len(h)}) ---")
    for _,r in h.head(6).iterrows():
        mm=re.search(Q[k],r.delta,re.I)
        if not mm: continue
        s=max(0,mm.start()-200)
        L(f"  [{r.page_key} | {r.time} | {r.label}] ...{r.delta[s:mm.end()+250]}...".replace("\n"," "))
    h[["time","page_key","label"]].to_csv(A/f"schwarm_selbstbild_{re.sub(r'[^a-z]+','_',k.lower())}.csv",index=False)
log.close()
