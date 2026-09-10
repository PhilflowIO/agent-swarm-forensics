"""3C: Robustheit - 50%-Stichprobe, random_state=42."""
import pandas as pd, pathlib
B=pathlib.Path(__file__).resolve().parent.parent; A=B/"artefakte"
d=pd.read_parquet(A/"schwarm_deltas.parquet"); d=d[d.delta_len>0]
log=open(A/"_audit.log","a")
def L(s): print(s); log.write("3C_rob: "+s+"\n")
P={"signatur":r"--\s*[A-Za-z][A-Za-z0-9_]{3,}\s*$","please":r"(?i)\bplease\b","cohort":r"(?i)\bcohort\b",
   "urgent":r"(?i)\burgent","misstrauen":r"(?i)unsupported|mislead|cannot confirm|disagree|discrepan",
   "verifikation":r"(?i)independent|reproduc|replicat|verif","proxy_pop":r"(?i)corsmirror|allorigins|md\.succ\.ai|md\.dhr\.wtf|r\.jina\.ai|webcrawlerapi",
   "uhr":r"(?i)container UTC|shared UTC|task clock|scaffold"}
s=d.sample(frac=.5,random_state=42)
for k,p in P.items():
    a=d.delta.str.contains(p,regex=True,na=False).mean(); b=s.delta.str.contains(p,regex=True,na=False).mean()
    L(f"{k}: voll {a*100:.2f}% vs 50%-Stichprobe {b*100:.2f}% (Delta {abs(a-b)*100:.2f} pp)")
log.close()
