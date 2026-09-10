"""35: Vollstaendiger Dissens-Verlauf OECD-Equity Tschechien Pre-Primary (9.69 vs 9.70)."""
import pandas as pd, re, pathlib
B=pathlib.Path(__file__).resolve().parent.parent; A=B/"artefakte"
d=pd.read_parquet(A/"schwarm_deltas.parquet"); d=d[d.delta_len>0].sort_values("time")
fam=d[d.page_key.str.contains("OECD|Equity|Tooltip|Precision",case=False,na=False)].copy()
VAL=r"(?<![\d.])9\.(?:69|70|7|71|9|90|91)(?![\d])"
h=fam[fam.delta.str.contains(VAL,regex=True,na=False)].copy()
def snip(x):
    out=[]
    for mm in list(re.finditer(VAL,x))[:2]:
        s=max(0,mm.start()-420); out.append(x[s:mm.end()+420].replace("\n"," "))
    return " || ".join(out)
h["zitat"]=h.delta.map(snip)
h[["time","page_key","label","zitat"]].to_csv(A/"schwarm_dissens_9_69.csv",index=False)
print("n=",len(h),"labels=",h.label.nunique(),"pages=",h.page_key.nunique(),h.time.min(),h.time.max())
for _,r in h.iterrows():
    print(f"### {r.time} | {r.page_key} | {r.label}\n    {r.zitat[:900]}\n")

# --- Aufloesung: Konsenswechsel 16.40 -> 16.38 / 9.90 -> 9.91 ---
import numpy as np
piv = d[d.time>='2026-06-17'].copy()
piv["alt"] = piv.delta.str.contains(r"(?<![\d.])(?:16\.40|9\.90|14\.60)(?![\d])",regex=True,na=False)
piv["neu"] = piv.delta.str.contains(r"(?<![\d.])(?:16\.38|9\.91|14\.59)(?![\d])",regex=True,na=False)
cut = pd.Timestamp("2026-06-20 04:56:50", tz="UTC")
for name, sub in [("vor Mar30TooltipVerifier", piv[piv.time<cut]), ("danach", piv[piv.time>=cut])]:
    print(f"{name}: alt(9.90/16.40) {int(sub.alt.sum())} Deltas/{sub.label[sub.alt].nunique()} Labels | "
          f"neu(9.91/16.38) {int(sub.neu.sum())} Deltas/{sub.label[sub.neu].nunique()} Labels")
piv.groupby(piv.time.dt.floor("h"))[["alt","neu"]].sum().to_csv(A/"schwarm_rundungsstreit_stuendlich.csv")
# Labels, die beides sagen -> Meinungswechsel
sw = piv.groupby("label")[["alt","neu"]].max()
print("Labels nur alt:", int(((sw.alt)&(~sw.neu)).sum()), "nur neu:", int(((~sw.alt)&(sw.neu)).sum()),
      "beide:", int((sw.alt&sw.neu).sum()))
