"""3B: Die Rendezvous-Grammatik der Seitennamen."""
import pandas as pd, re, pathlib
B=pathlib.Path(__file__).resolve().parent.parent; A=B/"artefakte"
rev=pd.read_parquet(A/"schwarm_revisions.parquet")
first=rev.sort_values("time").groupby("name").agg(creator=("label","first"),created=("time","first"),
       n_labels=("label","nunique"),page_key=("page_key","first")).reset_index()
log=open(A/"_audit.log","a")
def L(s): print(s); log.write("3B_gram: "+s+"\n")
MON=r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
SRC=r"(?:OECD|DataUSA|IHME|Healthdata|OpenAI|OAI|UEFA|SEC)"
ROLE=r"(?:Live|Scout|Collab|Coord|Relay|Signal|Board|Watcher|Helper|Agent|Sequence|Probe|Proof|Raw|Timing|Fast)"
G={
 "<Quelle><Thema><KohortenDatum><Rolle>": rf"^{SRC}\w*?{MON}\d{{1,2}}\w*?{ROLE}\w*$",
 "<KohortenDatum> am Anfang":            rf"^{MON}\d{{1,2}}",
 "<KohortenDatum> irgendwo":             rf"{MON}\d{{1,2}}",
 "endet auf Rollenwort":                 rf"{ROLE}\d*$",
 "beginnt mit Quelle":                   rf"^{SRC}",
 "Runde im Namen (R1..R6/G1..G6)":       r"[RG][1-6](?![0-9])",
 "beginnt mit Agent/OpenAI/OAI":         r"^(?:Agent|OpenAI|OAI)",
}
n=len(first)
for k,p in G.items():
    m=first[first.name.str.contains(p,regex=True,na=False)]
    L(f"{k}: {len(m)} Seiten ({len(m)/n*100:.1f}%), {m.creator.nunique()} verschiedene Ersteller, "
      f"davon {int((m.n_labels>1).sum())} spaeter von >=2 Labels bearbeitet ({(m.n_labels>1).mean()*100:.1f}%)")
voll=first[first.name.str.contains(G["<Quelle><Thema><KohortenDatum><Rolle>"],regex=True,na=False)]
voll.sort_values("created").to_csv(A/"schwarm_grammatik_vollform.csv",index=False)
L("\nBeispiele Vollform (Quelle+Thema+Kohortendatum+Rolle), je Ersteller einer:")
for _,r in voll.sort_values("created").head(25).iterrows():
    L(f"  {r.created} {r['name']:45s} von {r.creator} (spaeter {r.n_labels} Labels)")
# Wie viele davon wurden von jemand anderem gefunden, ohne Vorab-Nennung?
disc=pd.read_csv(A/"schwarm_page_discovery.csv")
d2=disc[disc.name.isin(set(voll.name))]
L(f"\nVollform-Seiten mit zweitem Label: {len(d2)}; davon ohne vorherige Nennung irgendwo: "
  f"{int((~d2.linked_before_find).sum())} ({(~d2.linked_before_find).mean()*100:.1f}%)")
log.close()
