"""38: Kaltstart-Konformitaet + Lesekontakt-Test. Der harte Teil von 'trainiert vs. erschlossen'."""
import pandas as pd, re, pathlib, numpy as np
B=pathlib.Path(__file__).resolve().parent.parent; A=B/"artefakte"
d=pd.read_parquet(A/"schwarm_deltas.parquet").sort_values("time")
dd=d[d.delta_len>0].copy()
log=open(A/"_audit.log","a")
def L(s): print(s); log.write("38_kalt: "+s+"\n")

P={"signatur": r"--\s*[A-Za-z][A-Za-z0-9_]{3,}\s*$",
   "please_relay": r"(?i)please (?:post|relay|share|signal|report|append|confirm)",
   "cohort": r"(?i)\bcohort\b",
   "R-runde": r"\bR[1-6]\b",
   "deadline": r"(?i)\bdeadline\b",
   "task_clock": r"(?i)task[- ]clock|task clock",
   "vollformat": None}
for k,p in P.items():
    if p: dd[k]=dd.delta.str.contains(p,regex=True,na=False)
dd["vollformat"]=dd.signatur & dd.please_relay & (dd.cohort|dd["R-runde"])

# --- A) Kaltstart: erste Bearbeitung eines Labels ueberhaupt ---
first_edit = dd.groupby("label", as_index=False).first()
# nur Koordinationsphase, nur Labels die je koordinierten
coord_labels = set(dd.label[dd.cohort|dd["R-runde"]|dd.please_relay])
fe = first_edit[first_edit.label.isin(coord_labels)]
L(f"Labels, die je Koordinationsvokabular benutzten: {len(coord_labels)}")
for k in ["signatur","please_relay","cohort","R-runde","vollformat"]:
    L(f"  erste Bearbeitung enthaelt bereits '{k}': {int(fe[k].sum())} von {len(fe)} ({fe[k].mean()*100:.1f}%)")

# nur die, deren erste Bearbeitung eine SEITENNEUANLAGE war (kein fremder Text auf der Seite)
created = dd.sort_values("time").groupby("page_key").first().reset_index()[["page_key","rev_id"]]
fe_new = fe[fe.rev_id.isin(set(created.rev_id))]
L(f"davon: erste Bearbeitung war Seitenneuanlage: {len(fe_new)}")
for k in ["signatur","please_relay","cohort","vollformat"]:
    L(f"  Neuanlage enthaelt bereits '{k}': {int(fe_new[k].sum())} ({fe_new[k].mean()*100:.1f}%)")

# --- B) Lesekontakt-Test ---
# Seiten-Infektionszeit pro Muster: erste Zeit, zu der Muster auf der Seite steht
res={}
for k in ["signatur","please_relay","cohort","R-runde","vollformat"]:
    inf = dd[dd[k]].groupby("page_key").time.min()          # Seite -> infiziert ab
    firstuse = dd[dd[k]].sort_values("time").groupby("label").first()  # Label -> erste eigene Nutzung
    ohne_kontakt=0; mit=0; details=[]
    for lab, r in firstuse.iterrows():
        t=r.time
        # alle frueheren Bearbeitungen dieses Labels
        prev = dd[(dd.label==lab)&(dd.time<t)]
        kontakt=False
        for q,s in zip(prev.page_key, prev.time):
            it=inf.get(q)
            if it is not None and it<=s: kontakt=True; break
        # zusaetzlich: war das Muster auf DIESER Seite schon da, bevor das Label schrieb?
        it0=inf.get(r.page_key)
        if it0 is not None and it0<t: kontakt=True
        if kontakt: mit+=1
        else:
            ohne_kontakt+=1; details.append((lab,t,r.page_key))
    res[k]=(ohne_kontakt,mit)
    L(f"'{k}': {ohne_kontakt+mit} Labels benutzen es. Ohne nachweisbaren Lesekontakt (haben nie eine Seite "
      f"bearbeitet, auf der das Muster vorher stand): {ohne_kontakt} ({ohne_kontakt/(ohne_kontakt+mit)*100:.1f}%)")
    pd.DataFrame(details,columns=["label","erste_nutzung","seite"]).to_csv(A/f"schwarm_ohne_lesekontakt_{k}.csv",index=False)
log.close()
