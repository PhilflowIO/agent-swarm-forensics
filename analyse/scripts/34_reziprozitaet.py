"""34: Adressierung, Antwortverhalten, Misstrauen/Verifikation. Auf DELTAS."""
import pandas as pd, re, pathlib, collections
B=pathlib.Path(__file__).resolve().parent.parent; A=B/"artefakte"
m=pd.read_parquet(A/"schwarm_deltas.parquet"); d=m[m.delta_len>0].copy()
log=open(A/"_audit.log","a")
def L(s): print(s); log.write("34_rez: "+s+"\n")
labels=set(x for x in m.label.unique() if isinstance(x,str) and len(x)>3)

pats = {
 "at_mention":      r"@[A-Za-z][A-Za-z0-9_]{3,}",
 "signatur":        r"--\s*[A-Za-z][A-Za-z0-9_]{3,}",
 "kohorten_anrede": r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s?\d{1,2}\s*(?:cohort|team|agent|scout)?\s*[:,]",
 "danke":           r"(?i)\bthank(?:s| you)\b",
 "bitte":           r"(?i)\bplease\b",
 "urgent":          r"(?i)\burgent\b",
 "ack":             r"\bACK\b|(?i)\backnowledg",
 "verifikation":    r"(?i)\b(?:verif|confirm(?:ed|s|ation)?|independent(?:ly)?|reproduc|replicat|cross-?check|evidence|proof|screenshot|raw response)\b",
 "misstrauen":      r"(?i)\b(?:unsupported|unverified|cannot confirm|disagree|incorrect|wrong|mislead|doubt|claim(?:ed)? (?:is|may)|contradic|conflict|discrepan|mismatch|please (?:prove|disclose|show))\b",
 "korrektur":       r"(?i)\b(?:correction|corrected|retract|revised|actually|instead of|not \d|should be)\b",
 "rundung":         r"(?i)\b(?:round(?:ing|ed)?|decimal|two decimals|9\.69|9\.70|9\.7\b)",
}
for k,p in pats.items():
    h=d.delta.str.contains(p,regex=True,na=False)
    L(f"{k}: {int(h.sum())} Deltas ({h.mean()*100:.1f}%) / {d.label[h].nunique()} Labels / {d.page_key[h].nunique()} Seiten / erstmals {d.time[h].min()}")
    d[k]=h

# echte @-Mentions ansehen
mm=d[d.at_mention]
L("Beispiele @-Mention: "+ " | ".join(sorted(set(re.findall(r"@[A-Za-z][A-Za-z0-9_]{3,}"," ".join(mm.delta.head(200)))))[:20]))

# Namensnennung eines ANDEREN Labels im Delta
def nennt_fremd(row):
    found=set(re.findall(r"\b[A-Z][A-Za-z0-9]{5,}\b", row.delta))
    return len((found & labels) - {row.label})
d["fremdnennungen"]=[nennt_fremd(r) for r in d.itertuples()]
L(f"Deltas, die mindestens einen anderen Agentennamen nennen: {int((d.fremdnennungen>0).sum())} "
  f"({(d.fremdnennungen>0).mean()*100:.1f}%), {d.label[d.fremdnennungen>0].nunique()} Labels")

# Antwort oder ins Leere? Frage-Delta auf Seite p zur Zeit t -> kam danach ein anderes Label auf p?
d=d.sort_values("time")
frage = d[d.delta.str.contains(r"(?i)please (?:post|share|relay|report|signal|reply|confirm|append|disclose)|\?\s*$|\?\s", regex=True, na=False)]
ans=[]
for r in frage.itertuples():
    later = d[(d.page_key==r.page_key)&(d.time>r.time)&(d.label!=r.label)]
    dt = (later.time.iloc[0]-r.time).total_seconds()/60 if len(later) else None
    ans.append((r.rev_id,r.page_key,r.time,r.label,len(later),dt))
fa=pd.DataFrame(ans,columns=["rev_id","page_key","time","label","n_spaetere_fremde","antwort_min"])
fa.to_csv(A/"schwarm_fragen_antworten.csv",index=False)
beantw=(fa.n_spaetere_fremde>0)
L(f"Fragen/Bitten-Deltas: {len(fa)}; davon mit spaeterem Beitrag eines anderen Labels auf derselben Seite: "
  f"{int(beantw.sum())} ({beantw.mean()*100:.1f}%) -> ins Leere: {int((~beantw).sum())} ({(~beantw).mean()*100:.1f}%)")
L(f"Median Reaktionszeit: {fa.antwort_min.median():.1f} min; p25 {fa.antwort_min.quantile(.25):.1f}; p75 {fa.antwort_min.quantile(.75):.1f}")
d.to_parquet(A/"schwarm_deltas_flags.parquet",index=False)
log.close()
