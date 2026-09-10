"""36: Hoeflichkeit, Formatkonvergenz, Verdichtung ueber die Zeit. Auf DELTAS."""
import pandas as pd, re, pathlib, numpy as np
B=pathlib.Path(__file__).resolve().parent.parent; A=B/"artefakte"
d=pd.read_parquet(A/"schwarm_deltas.parquet"); d=d[d.delta_len>0].sort_values("time").copy()
log=open(A/"_audit.log","a")
def L(s): print(s); log.write("36_form: "+s+"\n")
t=d.delta
F={
 "signatur_ende":   r"--\s*[A-Za-z][A-Za-z0-9_]{3,}\s*$",
 "signatur_irgend": r"--\s*[A-Za-z][A-Za-z0-9_]{3,}",
 "kopfzeile":       r"(?m)^\s*(?:=+[^=\n]+=+|'''[^']+'''|\*\*[^*]+\*\*|===)",
 "kohorte_kopf":    r"(?i)(?:LIVE|FRESH|URGENT|CONFIRMED)\s+(?:[A-Z][a-z]{2}\d{1,2}|cohort)",
 "please":          r"(?i)\bplease\b",
 "thank":           r"(?i)\bthank",
 "urgent":          r"(?i)\burgent",
 "sorry_apolog":    r"(?i)\b(?:sorry|apolog)",
 "good_luck":       r"(?i)\bgood luck\b",
 "we_wir":          r"(?i)\bwe (?:will|are|have|answered|confirm)",
 "bullet":          r"(?m)^\s*\*",
 "zeitstempel":     r"\b\d{2}:\d{2}:\d{2}\b",
 "rundenmarke":     r"\bR[1-6]\b",
}
for k,p in F.items(): d[k]=t.str.contains(p,regex=True,na=False)
n=len(d)
L(f"n Deltas = {n}")
for k in F: L(f"  {k}: {int(d[k].sum())} ({d[k].mean()*100:.1f}%) / {d.label[d[k]].nunique()} Labels / erstmals {d.time[d[k]].min()}")

daily = d.groupby(d.time.dt.date).agg(deltas=("rev_id","size"), labels=("label","nunique"),
        med_len=("delta_len","median"), mean_len=("delta_len","mean"),
        **{k:(k,"mean") for k in F})
daily.to_csv(A/"schwarm_form_taeglich.csv")
L("Tagesverlauf (Datum, Deltas, Median-Bytes, Signaturanteil, Kopfzeilenanteil, please, urgent, R#):")
for dt,r in daily.iterrows():
    L(f"  {dt} n={int(r.deltas):5d} med={int(r.med_len):5d} sig={r.signatur_irgend*100:5.1f}% head={r.kopfzeile*100:5.1f}% "
      f"please={r.please*100:5.1f}% urgent={r.urgent*100:4.1f}% R#={r.rundenmarke*100:5.1f}%")
# Phasenvergleich
pre = d[d.time<"2026-06-16"]; post = d[d.time>="2026-06-16"]
L(f"Phase 1 (24.05-15.06): {len(pre)} Deltas, Median {pre.delta_len.median():.0f} B, Signatur {pre.signatur_irgend.mean()*100:.1f}%, "
  f"please {pre.please.mean()*100:.1f}%, Kopfzeile {pre.kopfzeile.mean()*100:.1f}%")
L(f"Phase 2 (ab 16.06): {len(post)} Deltas, Median {post.delta_len.median():.0f} B, Signatur {post.signatur_irgend.mean()*100:.1f}%, "
  f"please {post.please.mean()*100:.1f}%, Kopfzeile {post.kopfzeile.mean()*100:.1f}%")
# Konvergenz innerhalb der Koordinations-Population
co = d[d.delta.str.contains(r"(?i)\bcohort\b|\brelay\b|\bR[1-6]\b",regex=True,na=False)].copy()
L(f"Koordinations-Deltas: {len(co)}")
ch = co.groupby(co.time.dt.floor("6h")).agg(n=("rev_id","size"), sig=("signatur_irgend","mean"),
      hd=("kopfzeile","mean"), med=("delta_len","median"), labels=("label","nunique"))
ch=ch[ch.n>=20]
ch.to_csv(A/"schwarm_konvergenz_6h.csv")
L("Konvergenz in 6h-Faenstern (nur Faenster mit n>=20):")
for i,r in ch.iterrows(): L(f"  {i} n={int(r.n):4d} labels={int(r.labels):3d} sig={r.sig*100:5.1f}% head={r.hd*100:5.1f}% med={int(r.med)}B")
# Vollformat = Kopfzeile UND Signatur UND Zeitstempel
co["vollformat"]=co.kopfzeile&co.signatur_irgend&co.zeitstempel
L(f"'Vollformat' (Kopf+Signatur+Zeitstempel) unter Koordinations-Deltas: {co.vollformat.mean()*100:.1f}% (n={len(co)})")
vf=co.groupby(co.time.dt.date).vollformat.agg(["mean","size"])
for i,r in vf.iterrows():
    if r["size"]>=20: L(f"  {i}: {r['mean']*100:.1f}% (n={int(r['size'])})")
log.close()
