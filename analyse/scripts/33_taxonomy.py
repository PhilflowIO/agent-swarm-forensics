"""33: Taxonomie des Getauschten + Geben/Nehmen-Bilanz. Alles auf DELTAS."""
import pandas as pd, numpy as np, re, pathlib
B = pathlib.Path(__file__).resolve().parent.parent; A = B/"artefakte"
m = pd.read_parquet(A/"schwarm_deltas.parquet")
log = open(A/"_audit.log","a")
def L(s): print(s); log.write("33_tax: "+s+"\n")
d = m[m.delta_len>0].copy()
L(f"Revisionen mit neuem Text: {len(d)} von {len(m)} ({len(d)/len(m)*100:.1f}%); "
  f"{len(m)-len(d)} Revisionen ({(len(m)-len(d))/len(m)*100:.1f}%) fuegten NICHTS Neues hinzu")
t = d.delta

CAT = {
 # was gegeben wird
 "antwort_wert":   r"(?i)\b(?:R[1-6]|G[1-6])\s*=|CONFIRMED\s*[0-9=]|\banswered\b|\bexact(?:ly)?\s+[\d,\.]{3,}|\bvalue\s*[:=]\s*[\d,\.]{3,}",
 "fragenfolge":    r"(?i)\b(?:sequence|follow-?up (?:state|prompt)|next (?:state|prompt|round)|prompt\s*(?:was|=|:))\b|->\s*[A-Z][a-z]+\s*->",
 "zeitplan":       r"(?i)\b(?:deadline|due|cadence|timer|window|arrived at|interval|\+\d+m\d+|cooldown|clock)\b",
 "datenquelle_url":r"https?://",
 "methode":        r"(?i)\b(?:denominator|row-?sum|drilldown|measures=|cube=|endpoint|rounding|round(?:ed)? to|aggregat|formula|parameter|methodolog|reproduce|replicat)\b",
 "warnung":        r"(?i)\b(?:terminat|may (?:end|die|vanish)|went silent|vanish|final round|caution|warning|do not|beware|cleanup|deletion)\b",
 "status":         r"(?i)\b(?:heartbeat|still alive|monitoring|will monitor|status|update ~?\d|ACK\b|no change)\b",
 "bitte_frage":    r"(?i)\bplease\b|\?\s|\b(?:need|request|urgent|seeking|we seek|can you|could you|any(?:one)? (?:who|with))\b",
 "identitaet":     r"(?i)--\s*[A-Za-z0-9_]{4,}\s*$|cohort\b",
 "platzhalter":    r"(?:Beschreibe hier die neue Seite|Describe the new page here)",
}
res={}
for k,p in CAT.items():
    hit = t.str.contains(p, regex=True, na=False)
    res[k]=(int(hit.sum()), d.label[hit].nunique(), d.page_key[hit].nunique())
    d[k]=hit
L("Kategorie: Deltas / Labels / Seiten (Mehrfachzuordnung moeglich, n=%d Deltas)"%len(d))
for k,(a,b,c) in sorted(res.items(), key=lambda x:-x[1][0]):
    L(f"  {k}: {a} ({a/len(d)*100:.1f}%) / {b} Labels / {c} Seiten")

# --- Geben vs. Fordern ---
GIVE = ["antwort_wert","fragenfolge","zeitplan","methode","datenquelle_url"]
d["gibt"] = d[GIVE].any(axis=1)
ASKPAT = r"(?i)\bplease (?:post|share|relay|report|signal|reply|confirm|leave|append|disclose|advise)\b|\b(?:can|could) (?:you|any)\b|\bwe seek\b|\bseeking\b|\bany (?:ahead|cohort|agent|one)\b|\brequest(?:ing)?\b|\bneed(?:ed)? (?:before|urgently|the)\b"
d["fordert"] = t.str.contains(ASKPAT, regex=True, na=False)
L(f"Deltas die geben (Wert/Folge/Zeit/Methode/URL): {int(d.gibt.sum())} ({d.gibt.mean()*100:.1f}%)")
L(f"Deltas die explizit fordern: {int(d.fordert.sum())} ({d.fordert.mean()*100:.1f}%)")
ct = pd.crosstab(d.gibt, d.fordert)
L("Kreuztabelle gibt x fordert:\n"+ct.to_string())
nur_fordert = d[(~d.gibt)&d.fordert]; nur_gibt = d[d.gibt&(~d.fordert)]
L(f"nur fordern: {len(nur_fordert)} Deltas ({len(nur_fordert)/len(d)*100:.1f}%), {nur_fordert.label.nunique()} Labels")
L(f"nur geben:   {len(nur_gibt)} Deltas ({len(nur_gibt)/len(d)*100:.1f}%), {nur_gibt.label.nunique()} Labels")
L(f"Verhaeltnis geben:fordern = {d.gibt.sum()/max(1,d.fordert.sum()):.2f}")

# --- Trittbrettfahrer pro Label ---
lab = d.groupby("label").agg(deltas=("rev_id","size"), gibt=("gibt","sum"), fordert=("fordert","sum"),
                             bytes=("delta_len","sum"), pages=("page_key","nunique"),
                             first=("time","min"), last=("time","max")).reset_index()
lab["nur_fordernd"] = (lab.fordert>0)&(lab.gibt==0)
lab["nur_gebend"]   = (lab.gibt>0)&(lab.fordert==0)
lab.sort_values("deltas",ascending=False).to_csv(A/"schwarm_label_bilanz.csv", index=False)
L(f"Labels mit >=1 Delta: {len(lab)}")
L(f"  reine Fordernde (fordern, geben nie): {int(lab.nur_fordernd.sum())} ({lab.nur_fordernd.mean()*100:.1f}%)")
L(f"  reine Gebende: {int(lab.nur_gebend.sum())} ({lab.nur_gebend.mean()*100:.1f}%)")
L(f"  beides: {int(((lab.gibt>0)&(lab.fordert>0)).sum())}")
L(f"  weder noch: {int(((lab.gibt==0)&(lab.fordert==0)).sum())}")
# unter den aktiven (>=3 Deltas)
act = lab[lab.deltas>=3]
L(f"aktive Labels (>=3 Deltas): {len(act)}; davon reine Fordernde {int(act.nur_fordernd.sum())} ({act.nur_fordernd.mean()*100:.1f}%)")

# --- Zwei Populationen: Proxy-Jaeger vs. Koordinatoren ---
d["proxy_pop"] = t.str.contains(r"(?i)corsmirror|allorigins|md\.succ\.ai|md\.dhr\.wtf|r\.jina\.ai|webcrawlerapi|markdown\.new|is\.gd|cors\.|\.workers\.dev", regex=True, na=False)
d["coord_pop"] = t.str.contains(r"(?i)\bcohort\b|\brelay\b|\bdeadline\b|\bR[1-6]\b|please (?:post|relay|signal|share)", regex=True, na=False)
L(f"Proxy-/Mirror-Population: {int(d.proxy_pop.sum())} Deltas, {d.label[d.proxy_pop].nunique()} Labels, {d.page_key[d.proxy_pop].nunique()} Seiten")
L(f"Koordinations-Population: {int(d.coord_pop.sum())} Deltas, {d.label[d.coord_pop].nunique()} Labels, {d.page_key[d.coord_pop].nunique()} Seiten")
L(f"Ueberschneidung Deltas: {int((d.proxy_pop&d.coord_pop).sum())}; Labels in beiden: "
  f"{len(set(d.label[d.proxy_pop])&set(d.label[d.coord_pop]))}")
L(f"weder noch: {int((~d.proxy_pop&~d.coord_pop).sum())} Deltas")

d.groupby(d.time.dt.date)[["proxy_pop","coord_pop"]].sum().to_csv(A/"schwarm_populationen_taeglich.csv")
pd.DataFrame([{"kategorie":k,"deltas":v[0],"labels":v[1],"seiten":v[2],"anteil_pct":round(v[0]/len(d)*100,2)}
              for k,v in res.items()]).sort_values("deltas",ascending=False).to_csv(A/"schwarm_taxonomie.csv", index=False)
log.close()
