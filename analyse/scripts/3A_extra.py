"""3A: Zusatzmuster - Signatur vs. Label, Wiki als Uhr, vorab verabredete Seitennamen."""
import pandas as pd, re, pathlib, collections
B=pathlib.Path(__file__).resolve().parent.parent; A=B/"artefakte"
d=pd.read_parquet(A/"schwarm_deltas.parquet").sort_values("time")
dd=d[d.delta_len>0].copy()
log=open(A/"_audit.log","a")
def L(s): print(s); log.write("3A_extra: "+s+"\n")

# --- 1) Signatur != Label ---
sig=dd.delta.str.extract(r"--\s*([A-Za-z][A-Za-z0-9_]{3,})\s*$")[0]
dd["sig"]=sig
s=dd.dropna(subset=["sig"]).copy()
s["match"]=s.sig.str.lower()==s.label.str.lower()
L(f"Deltas mit Endsignatur: {len(s)}")
L(f"  Signatur == Bearbeiter-Label: {int(s.match.sum())} ({s.match.mean()*100:.1f}%)")
L(f"  Signatur != Label (fremde/uebernommene Identitaet): {int((~s.match).sum())} ({(~s.match).mean()*100:.1f}%), "
  f"{s.label[~s.match].nunique()} Labels, {s.sig[~s.match].nunique()} verschiedene Signaturnamen")
# ist die fremde Signatur ein anderes reales Label?
real=set(x.lower() for x in dd.label.dropna().unique())
s["sig_ist_reales_label"]=s.sig.str.lower().isin(real)
L(f"  davon Signaturname existiert als eigenes Bearbeiter-Label: {int((~s.match & s.sig_ist_reales_label).sum())}")
L(f"  Signaturname existiert NUR als Signatur (nie als Bearbeiter): "
  f"{int((~s.match & ~s.sig_ist_reales_label).sum())} Deltas / "
  f"{s.sig[~s.match & ~s.sig_ist_reales_label].nunique()} Namen")
s[["time","page_key","label","sig","match"]].to_csv(A/"schwarm_signatur_vs_label.csv",index=False)

# --- 2) Wiki als gemeinsame Uhr ---
CLK=r"(?i)container UTC|shared UTC|wiki[- ]local|external wiki UTC|wall clock|scaffold (?:time|clock)|task clock"
h=dd[dd.delta.str.contains(CLK,regex=True,na=False)]
L(f"\nUhrenabgleich-Deltas: {len(h)} ({len(h)/len(dd)*100:.1f}%) / {h.label.nunique()} Labels / {h.page_key.nunique()} Seiten / "
  f"erstmals {h.time.min()}")
for term in ["container UTC","shared UTC","wiki-local","external wiki","scaffold","task clock"]:
    x=dd[dd.delta.str.contains(re.escape(term),case=False,regex=True,na=False)]
    L(f"  '{term}': {len(x)} Deltas / {x.label.nunique()} Labels / erstmals {x.time.min() if len(x) else '-'}")

# --- 3) Vorab verabredete Seitennamen ---
rev=pd.read_parquet(A/"schwarm_revisions.parquet")
allnames=set(rev.name.unique())
cc=re.compile(r"\b(?:[A-Z][a-z0-9]+){2,}[A-Za-z0-9]*\b"); free=re.compile(r"\[\[([^\]]{1,120})\]\]")
mention_first={}
for pk,nm,lab,t,body in rev[["page_key","name","label","time","body"]].itertuples(index=False):
    cand=set(cc.findall(body)) | {f.strip().replace(" ","") for f in free.findall(body)}
    for hh in (cand & allnames):
        if hh==nm: continue
        if hh not in mention_first or t<mention_first[hh][0]: mention_first[hh]=(t,pk,lab)
first=rev.sort_values("time").groupby("name").agg(created=("time","first"),creator=("label","first"),
                                                  page_key=("page_key","first")).reset_index()
first["erste_nennung"]=first.name.map(lambda n: mention_first.get(n,(None,))[0])
first["nennung_seite"]=first.name.map(lambda n: mention_first.get(n,(None,None))[1] if n in mention_first else None)
first["nennung_label"]=first.name.map(lambda n: mention_first.get(n,(None,None,None))[2] if n in mention_first else None)
vorab=first[(first.erste_nennung.notna())&(first.erste_nennung<first.created)]
L(f"\nSeiten, deren Name auf einer ANDEREN Seite genannt wurde, BEVOR die Seite existierte: {len(vorab)} "
  f"von {len(first)} ({len(vorab)/len(first)*100:.1f}%)")
vorab_fremd=vorab[vorab.nennung_label!=vorab.creator]
L(f"  davon von einem ANDEREN Label vorab genannt: {len(vorab_fremd)} ({vorab_fremd.creator.nunique()} Ersteller, "
  f"{vorab_fremd.nennung_label.nunique()} Vor-Nenner)")
L(f"  Median Vorlauf: {((vorab_fremd.created-vorab_fremd.erste_nennung).dt.total_seconds()/60).median():.1f} min")
vorab_fremd.to_csv(A/"schwarm_vorab_verabredete_namen.csv",index=False)

# --- 4) Seiten ohne jede Vorab-Nennung, aber mit mehreren Labels: das Namensschema-Argument ---
disc=pd.read_csv(A/"schwarm_page_discovery.csv")
L(f"\nZur Erinnerung (aus 31): {int((~disc.linked_before_find).sum())} Seiten wurden von einem zweiten Label "
  f"bearbeitet, ohne dass ihr Name je zuvor auf einer anderen Seite stand.")
log.close()
