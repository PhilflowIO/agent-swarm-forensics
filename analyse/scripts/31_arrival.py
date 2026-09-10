"""31: Ankunftsprozess. Link-Graph ueber Zeit, verwaiste Wiederfindung, Namensmorphologie."""
import pandas as pd, numpy as np, re, pathlib, json, collections
B = pathlib.Path(__file__).resolve().parent.parent
A = B/"artefakte"
df = pd.read_parquet(A/"schwarm_revisions.parquet")
log = open(A/"_audit.log","a")
def L(s): print(s); log.write("31_arrival: "+s+"\n")

L(f"input revs={len(df)} labels={df.label.nunique()} pages={df.page_key.nunique()}")

# ---------- 1. Chronologie der ersten Schreibzugriffe ----------
first = (df.sort_values("time").groupby("page_key")
           .agg(first_time=("time","first"), creator=("label","first"), wiki=("wiki","first"),
                name=("name","first")).reset_index())
first.sort_values("first_time").head(60).to_csv(A/"schwarm_first_pages.csv", index=False)
L(f"erste 60 Seiten -> schwarm_first_pages.csv; erste Seite {first.first_time.min()}")

# ---------- 2. Link-Graph: welcher Seitenname wird wann wo erwaehnt ----------
# UseMod verlinkt sowohl [[Free Links]] als auch nackte CamelCase-WikiWords.
allnames = set(df.name.unique())
# Index: name -> frueheste Zeit, zu der der Name im Body EINER ANDEREN Seite steht
name_re = {}
mention_first = {}      # name -> (time, page_key, label)
mention_count = collections.Counter()
# Effizient: pro Revision alle CamelCase-Tokens + [[...]] extrahieren, gegen allnames schneiden
cc = re.compile(r"\b(?:[A-Z][a-z0-9]+){2,}[A-Za-z0-9]*\b")
free = re.compile(r"\[\[([^\]]{1,120})\]\]")
rows = df[["page_key","name","label","time","body"]].itertuples(index=False)
for pk, nm, lab, t, body in rows:
    cand = set(cc.findall(body))
    for f in free.findall(body):
        cand.add(f.strip().replace(" ",""))
        cand.add(f.strip())
    hits = cand & allnames
    for h in hits:
        if h == nm:      # Selbstnennung ist keine Auffindbarkeit von aussen
            continue
        mention_count[h] += 1
        if h not in mention_first or t < mention_first[h][0]:
            mention_first[h] = (t, pk, lab)

L(f"Seitennamen, die jemals auf einer ANDEREN Seite genannt werden: {len(mention_first)} von {len(allnames)}")

# ---------- 3. Verwaiste Wiederfindung ----------
# Fuer jede Seite: erste Bearbeitung durch ein anderes Label als den Ersteller.
d = df.sort_values("time")
recs = []
for pk, g in d.groupby("page_key", sort=False):
    creator = g.label.iloc[0]; t0 = g.time.iloc[0]; nm = g.name.iloc[0]
    other = g[g.label != creator]
    if len(other) == 0: continue
    t1 = other.time.iloc[0]; finder = other.label.iloc[0]
    mt, mp, ml = mention_first.get(nm, (None,None,None))
    linked_before = (mt is not None) and (mt < t1)
    recs.append(dict(page_key=pk, name=nm, creator=creator, created=t0,
                     finder=finder, found=t1, gap_min=(t1-t0).total_seconds()/60,
                     n_labels=g.label.nunique(), n_revs=len(g),
                     first_external_mention=mt, mention_page=mp,
                     linked_before_find=linked_before))
co = pd.DataFrame(recs)
co.to_csv(A/"schwarm_page_discovery.csv", index=False)
L(f"Seiten mit >=2 Labels: {len(co)}; davon vor dem Fund verlinkt: {int(co.linked_before_find.sum())} "
  f"({co.linked_before_find.mean()*100:.1f}%) -> unverlinkt gefunden: {int((~co.linked_before_find).sum())}")
orph = co[~co.linked_before_find]
L(f"unverlinkt gefunden: {len(orph)} Seiten, {orph.finder.nunique()} verschiedene Finder, "
  f"Median-Gap {orph.gap_min.median():.1f} min, p25 {orph.gap_min.quantile(.25):.1f}, p75 {orph.gap_min.quantile(.75):.1f}")
L(f"davon Gap>60min (RecentChanges-Fenster ueberschritten): {int((orph.gap_min>60).sum())}")
L(f"davon Gap>1440min (>24h): {int((orph.gap_min>1440).sum())}")
# Ausschluss der Hub-/Altseiten
hub = {"WillkommenImWiki","StartSeite","TestSeite","RecentChanges"}
orph2 = orph[~orph.name.isin(hub)]
L(f"ohne die 4 Altseiten: {len(orph2)} unverlinkt gefundene Agenten-Seiten, {orph2.finder.nunique()} Finder")
orph2.sort_values("n_labels",ascending=False).head(200).to_csv(A/"schwarm_orphan_found.csv", index=False)

# ---------- 4. Morphologie der Seitennamen ----------
SRC = ["DataUSA","OECD","IHME","Healthdata","UEFA","SEC","USASpending","Census","Eurostat","WorldBank",
       "CDC","BLS","Preservica","DPLA","CatalogIt","PowerBI","CounterAPI","Api","Federal"]
TOPIC = ["Construction","Grocery","Clothing","Language","Equity","CVD","Smoking","Maids","Police","Wage",
         "Education","Enrollment","Family","Planning","Rugby","Health","Population","Sector","State",
         "Investor","Budget","Account","Wine","Tourism","Employment","Income","Poverty","Mortality"]
MON = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec",
       "January","February","March","April","June","July","August","September","October","November","December"]
ROLE = ["Live","Collab","Relay","Signal","Board","Scout","Helper","Agent","Watcher","Sequence","Proof",
        "Cache","Log","Notes","Raw","Fast","Bridge","Test","Tmp","Probe","Reply","Link","Index","Ref",
        "Mirror","Archive","Team","Coord","Sync","Hub","Reader","Verifier","Observer","Researcher","Miner"]
ORG = ["OpenAI","OAI","Agent","Research","Assistant","GPT"]
ROUND = re.compile(r"\b[RG](?:[1-9])\b|R[1-9]|G[1-9]")
def toks(n):
    return re.findall(r"[A-Z]+(?![a-z])|[A-Z][a-z]+|\d+", n)
def morph(n):
    t = toks(n); s=set(t); f=set()
    if any(x in s for x in SRC) or any(x.lower() in n.lower() for x in ("DataUSA","OECD","IHME")): f.add("source")
    if any(x in s for x in TOPIC): f.add("topic")
    if any(x in s for x in MON): f.add("month")
    if re.search(r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\d{1,2}", n): f.add("cohort_date")
    if any(x in s for x in ROLE): f.add("role")
    if any(x in s for x in ORG): f.add("org")
    if re.search(r"R[1-6]|G[1-6]", n): f.add("round")
    if re.search(r"\d{4,}", n): f.add("longnum")
    elif re.search(r"\d", n): f.add("num")
    return f
pages = pd.DataFrame({"name": sorted(allnames)})
pages["feat"] = pages.name.map(lambda n: "+".join(sorted(morph(n))) or "none")
for k in ["source","topic","month","cohort_date","role","org","round","longnum"]:
    pages[k] = pages.name.map(lambda n,k=k: k in morph(n))
pages.to_csv(A/"schwarm_pagename_morphology.csv", index=False)
n=len(pages)
L("Morphologie ueber alle %d Seitennamen:" % n)
for k in ["source","topic","month","cohort_date","role","org","round","longnum"]:
    L(f"  {k}: {int(pages[k].sum())} ({pages[k].mean()*100:.1f}%)")
L("Top-Kombinationen:")
for combo,c in pages.feat.value_counts().head(15).items():
    L(f"  {combo}: {c} ({c/n*100:.1f}%)")
L(f"Namen mit >=3 Bausteinen: {int((pages[['source','topic','month','role','org','round']].sum(axis=1)>=3).sum())} "
  f"({(pages[['source','topic','month','role','org','round']].sum(axis=1)>=3).mean()*100:.1f}%)")

# ---------- 5. Kollision: gleicher Name unabhaengig konstruiert? ----------
# Namen, die in mehreren Wikis existieren
mw = df.groupby("name").wiki.nunique()
L(f"Namen in mehr als einem Wiki: {int((mw>1).sum())}")

# ---------- 6. Namensschema-Test: unabhaengig konstruierte Zwillingsnamen ----------
import collections
def keyset(n):
    t=[x for x in re.findall(r"[A-Z]+(?![a-z])|[A-Z][a-z]+|\d+", n) if not x.isdigit()]
    return tuple(sorted(set(x.lower() for x in t)))
creators = df.sort_values("time").groupby("name").agg(creator=("label","first"), created=("time","first"))
buck=collections.defaultdict(list)
for n,r in creators.iterrows(): buck[keyset(n)].append((n,r.creator,r.created))
multi=[(k,v) for k,v in buck.items() if len(v)>1 and len({x[1] for x in v})>1 and len(k)>=3]
L(f"\nNamensschema: Bausteinmengen (>=3 Bausteine), die von >=2 VERSCHIEDENEN Labels unabhaengig zu Seiten gemacht wurden: {len(multi)}")
tot=sum(len(v) for k,v in multi)
L(f"  betroffene Seiten: {tot}; verschiedene Ersteller: {len({x[1] for k,v in multi for x in v})}")
rows=[]
for k,v in sorted(multi,key=lambda x:-len(x[1]))[:400]:
    for n,c,t in v: rows.append(dict(bausteine="+".join(k), name=n, creator=c, created=t, gruppengroesse=len(v)))
pd.DataFrame(rows).to_csv(A/"schwarm_namensschema_zwillinge.csv", index=False)
for k,v in sorted(multi,key=lambda x:-len(x[1]))[:8]:
    L(f"  [{'+'.join(k)}] {len(v)} Seiten von {len({x[1] for x in v})} Erstellern: " +
      ", ".join(f"{n}({c})" for n,c,t in v[:5]))

# ---------- 7. Wie viele kamen allein an? ----------
lab_first = df.sort_values("time").groupby("label").first()
solo = df.groupby("page_key").label.nunique()
lab_first["seite_solo"] = lab_first.page_key.map(solo)==1
L(f"\nLabels, deren erste Bearbeitung auf einer Seite liegt, die NIE ein zweites Label beruehrte: "
  f"{int(lab_first.seite_solo.sum())} von {len(lab_first)} ({lab_first.seite_solo.mean()*100:.1f}%)")
neu = df.sort_values("time").groupby("page_key").first().reset_index()
L(f"Seiten insgesamt neu angelegt: {len(neu)}; verschiedene Ersteller: {neu.label.nunique()}")
log.close()
