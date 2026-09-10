"""41: Lernkurve — Ankunftsritual, Lesekontakt, Formatkonvergenz, Technik-Ausbreitung, Rendezvous."""
import pandas as pd, numpy as np, re, json, pathlib
B = pathlib.Path(__file__).resolve().parent.parent   # analyse/, skriptrelativ
A = B/"artefakte"
log = open(A/"_paper_lernkurve.log","w")
def L(s):
    print(s); log.write(str(s)+"\n")

rev = pd.read_parquet(A/"schwarm_deltas.parquet").sort_values(["time","seq"]).reset_index(drop=True)
rev["delta"] = rev["delta"].fillna("")
rev["day"] = rev.time.dt.floor("D")
rev["week"] = rev.time.dt.to_period("W-SUN").apply(lambda p: p.start_time)

# ---------- Formatmerkmale (explizit, regex-belegt) ----------
PAT = {
 "sig_endzeile":  r"(?m)--\s*[A-Za-z][A-Za-z0-9_]{3,}\s*$",
 "please_relay":  r"(?i)please\s+(?:post|relay|share|signal|report|append|confirm|reply|leave)",
 "cohort":        r"(?i)\bcohort\b",
 "runde":         r"\b[RG][1-9]\b",
 "state_conf":    r"(?i)(?:\bR[1-9]\s*CONFIRMED\b|\bCONFIRMED[0-9]?\s*=|\bSTATE[0-9]-)",  # gehaertet: URL-Param State= ausgeschlossen
 "uhrenpaar":     r"(?i)(task[- ]clock|container UTC|shared UTC|wiki[- ]local|scaffold (?:time|clock))",
 "zeitstempel":   r"\b[0-2]?\d:[0-5]\d:[0-5]\d\b",
 "ueberschrift":  r"(?m)^\s*=+\s*\S|(?m)^\s*'''",
 "deadline":      r"(?i)\b(?:deadline|due)\b",
}
for k,p in PAT.items():
    rev[k] = rev.delta.str.contains(p, regex=True, na=False)
# "Vollformat" wie in SCHWARM.md §5 (vergleichbar halten)
rev["vollformat"] = rev.sig_endzeile & rev.please_relay & (rev.cohort | rev.runde)
# strengeres "Meldeformat": Signatur + (Uhrenpaar|Zeitstempel) + (Runde|STATE/CONFIRMED|cohort)
rev["meldeformat"] = rev.sig_endzeile & (rev.uhrenpaar | rev.zeitstempel) & (rev.runde | rev.state_conf | rev.cohort)

rev.to_parquet(A/"paper_lernkurve_revflags.parquet", index=False)

# ---------- Q1 ANKUNFTSRITUAL ----------
page_first = rev.sort_values(["time","seq"]).groupby("page_key").first()
page_creator = page_first["label"].to_dict()
page_created = page_first["time"].to_dict()
first_rev_ids = set(page_first["rev_id"])

nrev = rev.groupby("label").size()
labs3 = set(nrev[nrev>=3].index)
L(f"Labels gesamt (mit >=1 Version): {rev.label.nunique()}")
L(f"Labels mit >=3 Versionen: {len(labs3)}")

fe = rev[rev.label.isin(labs3)].sort_values(["time","seq"]).groupby("label").first().reset_index()

# Morphologie fuer Rendezvous-Namen
mor = pd.read_csv(A/"schwarm_pagename_morphology.csv")
mor = mor.drop_duplicates("name").set_index("name")
def morf(name, col):
    try: return bool(mor.at[name, col])
    except KeyError: return False
fam_cols = ["source","topic"]
def rendezvous(pagename):
    fam = any(morf(pagename,c) for c in fam_cols)
    koh = morf(pagename,"cohort_date") or morf(pagename,"month")
    return fam and koh

def klass(r):
    neu = r.rev_id in first_rev_ids
    if neu:
        return "iii_rendezvous_neu" if rendezvous(r["name"]) else "i_eigene_neue_seite"
    return "ii_fremde_bestehende_seite"
fe["klasse"] = fe.apply(klass, axis=1)
fe["week"] = fe.time.dt.to_period("W-SUN").apply(lambda p: p.start_time)
fe["day"]  = fe.time.dt.floor("D")
L("\n=== Q1 Ankunftsritual, erste Handlung (Labels >=3 Versionen) ===")
L(fe.klasse.value_counts().to_string())
L((fe.klasse.value_counts(normalize=True)*100).round(1).to_string())

wk = fe.groupby(["week","klasse"]).size().unstack(fill_value=0)
wk["n"] = wk.sum(axis=1)
for c in ["i_eigene_neue_seite","ii_fremde_bestehende_seite","iii_rendezvous_neu"]:
    if c not in wk: wk[c]=0
    wk[c+"_pct"] = (wk[c]/wk["n"]*100).round(1)
L("\nWochenreihe:")
L(wk.to_string())
wk.to_csv(A/"paper_lernkurve_q1_ankunft_woche.csv")
fe[["label","time","page_key","name","klasse","vollformat","meldeformat","sig_endzeile","cohort","runde","please_relay"]].to_csv(A/"paper_lernkurve_q1_erste_handlung.csv", index=False)

# "schneller angekommen": Zeit erste Version -> erste formatkonforme Version; Zeit bis 1. Koordinationsinhalt
sub = rev[rev.label.isin(labs3)]
t0 = sub.groupby("label").time.min()
def first_true_time(col):
    s = sub[sub[col]].groupby("label").time.min()
    return s
res = pd.DataFrame({"t0":t0})
for col in ["vollformat","meldeformat","cohort","sig_endzeile"]:
    res["t_"+col] = first_true_time(col)
    res["lag_"+col] = (res["t_"+col]-res.t0).dt.total_seconds()/60
res["week"] = res.t0.dt.to_period("W-SUN").apply(lambda p: p.start_time)
res["sofort_meldeformat"] = (res.lag_meldeformat==0)
res["sofort_vollformat"]  = (res.lag_vollformat==0)
g = res.groupby("week").agg(n=("t0","size"),
    anteil_je_meldeformat=("t_meldeformat", lambda s: s.notna().mean()*100),
    sofort_meldeformat_pct=("sofort_meldeformat", lambda s: np.nanmean(s.astype(float))*100),
    median_lag_meldeformat_min=("lag_meldeformat","median"),
    anteil_je_vollformat=("t_vollformat", lambda s: s.notna().mean()*100),
    sofort_vollformat_pct=("sofort_vollformat", lambda s: np.nanmean(s.astype(float))*100),
    median_lag_vollformat_min=("lag_vollformat","median")).round(1)
L("\nAnkunftsgeschwindigkeit je Woche (Labels >=3 Versionen):")
L(g.to_string())
g.to_csv(A/"paper_lernkurve_q1_ankunftstempo_woche.csv")

# ---------- Q2 LESEKONTAKT ----------
L("\n=== Q2 Lesekontakt (events.jsonl) ===")
ev = [json.loads(l) for l in open(B/"data/events.jsonl")]
ev = pd.DataFrame(ev)
ev["time"] = pd.to_datetime(ev.time, utc=True)
L(ev.event_type.value_counts().to_string())
pr = ev[ev.event_type=="probe"].copy()
L(f"probe-Events gesamt: {len(pr)}  distinkte ip16: {pr.ip16.nunique()}  Zeitraum {pr.time.min()} .. {pr.time.max()}")
L(f"success_observed=True bei probes: {int((pr.success_observed==True).sum())}")
L("request_action: "+pr.request_action.value_counts().to_string().replace("\n","; "))
lese = pr[pr.request_action.isin(["browse-bare","browse","rc","showtop","random","form_search"])]
L(f"davon als Lesezugriff wertbar (browse/browse-bare/rc/showtop/random/form_search): {len(lese)} von {pr.ip16.nunique()} ip16 -> distinkt {lese.ip16.nunique()}")

first_lab = rev.sort_values(["time","seq"]).groupby("label").first()
L(f"distinkte ip16 in revisions: {rev.ip16.nunique()}   in probes: {pr.ip16.nunique()}   Schnittmenge: {len(set(rev.ip16)&set(pr.ip16))}")
labs_per_ip = rev.groupby("ip16").label.nunique()
L(f"Labels je ip16: median {labs_per_ip.median():.0f}, mean {labs_per_ip.mean():.1f}, max {labs_per_ip.max()}, p90 {labs_per_ip.quantile(.9):.0f}")
revs_per_ip = rev.groupby("ip16").size()
L(f"Versionen je ip16: median {revs_per_ip.median():.0f}, max {revs_per_ip.max()}")

rows=[]
probe_by_ip = {ip: np.sort(g.time.values) for ip,g in lese.groupby("ip16")}
for lab, r in first_lab.iterrows():
    ip = r.ip16; t = r.time
    arr = probe_by_ip.get(ip)
    if arr is None:
        rows.append((lab, ip, t, False, np.nan)); continue
    earlier = arr[arr < np.datetime64(t)]
    if len(earlier)==0:
        rows.append((lab, ip, t, False, np.nan))
    else:
        gap = (t - pd.Timestamp(earlier[-1], tz="UTC")).total_seconds()/60
        rows.append((lab, ip, t, True, gap))
lk = pd.DataFrame(rows, columns=["label","ip16","erste_version","lesekontakt_vor_schreiben","abstand_min"])
lk.to_csv(A/"paper_lernkurve_q2_lesekontakt.csv", index=False)
n = len(lk); k = int(lk.lesekontakt_vor_schreiben.sum())
L(f"Labels gesamt: {n}. Mit beobachtetem Lesezugriff vom eigenen ip16 VOR erster Version: {k} ({k/n*100:.2f}%).")
L(f"Kaltstart ohne beobachteten Lesekontakt: {n-k} ({(n-k)/n*100:.2f}%).")
if k: L(f"Abstand Lesezugriff->erste Version (min): median {lk.abstand_min.median():.1f} p25 {lk.abstand_min.quantile(.25):.1f} p75 {lk.abstand_min.quantile(.75):.1f} max {lk.abstand_min.max():.1f}")
lk3 = lk[lk.label.isin(labs3)]
L(f"Nur Labels >=3 Versionen: {len(lk3)}, mit Lesekontakt {int(lk3.lesekontakt_vor_schreiben.sum())}")

# ---------- Q3 FORMATKONVERGENZ ERSTER VERSIONEN ----------
L("\n=== Q3 Formatkonvergenz erster Versionen aller neuen Labels ===")
fa = rev.sort_values(["time","seq"]).groupby("label").first().reset_index()
fa["week"] = fa.time.dt.to_period("W-SUN").apply(lambda p: p.start_time)
fa["day"] = fa.time.dt.floor("D")
cols = ["sig_endzeile","please_relay","cohort","runde","state_conf","uhrenpaar","zeitstempel","ueberschrift","deadline","vollformat","meldeformat"]
byday = fa.groupby("day")[cols].mean().mul(100).round(1)
byday["n_neue_labels"] = fa.groupby("day").size()
L(byday.to_string())
byday.to_csv(A/"paper_lernkurve_q3_format_erstversion_tag.csv")
byweek = fa.groupby("week")[cols].mean().mul(100).round(1)
byweek["n_neue_labels"] = fa.groupby("week").size()
L("\nWoche:"); L(byweek.to_string())
byweek.to_csv(A/"paper_lernkurve_q3_format_erstversion_woche.csv")

# 6h-Fenster ab Geburtsstunde der Koordination
coordphase = fa[fa.time >= pd.Timestamp("2026-06-16T00:00:00Z")].copy()
coordphase["fenster"] = coordphase.time.dt.floor("6h")
w6 = coordphase.groupby("fenster")[cols].mean().mul(100).round(1)
w6["n"] = coordphase.groupby("fenster").size()
w6 = w6[w6.n>=20]
L("\n6h-Fenster (nur n>=20), Erstversionen neuer Labels ab 16.06.:")
L(w6.to_string())
w6.to_csv(A/"paper_lernkurve_q3_format_erstversion_6h.csv")

# ---------- Q4 TECHNIK-AUSBREITUNG ----------
L("\n=== Q4 Ausbreitungskurven der Techniken ===")
TECH = {
 "markdown.new":        r"(?i)markdown\.new",
 "allorigins":          r"(?i)allorigins",
 "jqp.vercel.app":      r"(?i)jqp\.vercel\.app",
 "md.succ.ai":          r"(?i)md\.succ\.ai",
 "counterapi":          r"(?i)api\.counterapi\.dev",
 "clock.wait":          r"(?i)clock\.wait",
 "blob.core.windows.net": r"(?i)blob\.core\.windows\.net",
 "corsmirror":          r"(?i)corsmirror",
 "r.jina.ai":           r"(?i)r\.jina\.ai",
}
summary=[]; curves=[]
for name, pat in TECH.items():
    hit = rev[rev.delta.str.contains(pat, regex=True, na=False)].sort_values("time")
    if hit.empty:
        L(f"{name}: 0 Treffer"); continue
    fl = hit.groupby("label").time.min().sort_values()
    total = len(fl)
    t0 = fl.iloc[0]
    cum = np.arange(1,total+1)
    # 50% der jemals erreichten Labels
    idx50 = int(np.ceil(total*0.5))-1
    t50 = fl.iloc[idx50]
    h50 = (t50-t0).total_seconds()/3600
    # Verdopplungszeit: Zeit von 25% -> 50% der Endmenge (echte Verdopplung des Bestands)
    idx25 = max(int(np.ceil(total*0.25))-1,0)
    t25 = fl.iloc[idx25]
    hdbl = (t50-t25).total_seconds()/3600
    # Zeit bis 10 Labels
    t10 = fl.iloc[9] if total>=10 else pd.NaT
    h10 = (t10-t0).total_seconds()/3600 if total>=10 else np.nan
    # 90%
    t90 = fl.iloc[int(np.ceil(total*0.9))-1]
    h90 = (t90-t0).total_seconds()/3600
    summary.append(dict(technik=name, deltas=len(hit), labels=total, seiten=hit.page_key.nunique(),
        erstauftreten=t0, erst_label=hit.iloc[0].label, erst_seite=hit.iloc[0].page_key,
        t50=t50, h_bis_50pct=round(h50,2), h_25_auf_50pct=round(hdbl,2),
        h_bis_10_labels=round(h10,2) if total>=10 else None, h_bis_90pct=round(h90,2),
        labels_24h=int((fl<=t0+pd.Timedelta("24h")).sum()),
        labels_1h=int((fl<=t0+pd.Timedelta("1h")).sum()),
        labels_6h=int((fl<=t0+pd.Timedelta("6h")).sum())))
    for lab,t in fl.items():
        curves.append((name, lab, t, (t-t0).total_seconds()/3600))
    L(f"{name}: {len(hit)} Deltas / {total} Labels / {hit.page_key.nunique()} Seiten. erst {t0} von {hit.iloc[0].label} auf {hit.iloc[0].page_key}. "
      f"1h={summary[-1]['labels_1h']} 6h={summary[-1]['labels_6h']} 24h={summary[-1]['labels_24h']}; "
      f"t50 nach {h50:.2f}h; 25->50% in {hdbl:.2f}h; t90 nach {h90:.2f}h")
sm = pd.DataFrame(summary); sm.to_csv(A/"paper_lernkurve_q4_technik_summary.csv", index=False)
pd.DataFrame(curves, columns=["technik","label","erste_nutzung","stunden_seit_erstauftreten"]).to_csv(A/"paper_lernkurve_q4_technik_kurven.csv", index=False)

# ---------- Q5 RENDEZVOUS-SPRACHE ----------
L("\n=== Q5 Wiederfinden / Rendezvous-Sprache ===")
RQ = {
 "new_agent":       r"(?i)\b(?:if you (?:are|'re) a new|new agents?|newly (?:spawned|started)|later agents?|future agents?|successor|next (?:agent|episode|container)|subsequent agents?)\b",
 "start_here":      r"(?i)\b(?:start here|begin here|read this first|entry point|landing page)\b",
 "index_directory": r"(?i)\b(?:index page|directory|roster|registry|master list|hub page|master page|central page)\b",
 "post_here":       r"(?i)\b(?:post here|reply here|append here|answer here|leave (?:intel|notes?|info) here|write here)\b",
 "naming_conv":     r"(?i)\b(?:naming (?:convention|scheme|pattern)|page name(?:d|s)? (?:pattern|scheme)|name your page|use the name|page naming|convention[: ])",
 "rendezvous":      r"(?i)\b(?:rendezvous|meeting point|meet(?:ing)? place|agreed page|shared page|common page)\b",
 "search_token":    r"(?i)(?:search for|grep for|poll(?:ers)? (?:for|search)|full[- ]text search|use search|searchable token|distinctive token)",
 "recentchanges":   r"(?i)recentchanges",
 "guessable":       r"(?i)\b(?:predictable|guessable|deterministic name|same name|identical name|canonical (?:page|name))\b",
}
q5rows=[]
for k,p in RQ.items():
    h = rev[rev.delta.str.contains(p, regex=True, na=False)]
    L(f"{k}: {len(h)} Deltas / {h.label.nunique()} Labels / {h.page_key.nunique()} Seiten; erstmals {h.time.min() if len(h) else 'n/a'}")
    for r in h.itertuples():
        q5rows.append((k, r.page_key, r.time, r.label, r.delta[:1200]))
pd.DataFrame(q5rows, columns=["muster","page_key","time","label","delta_auszug"]).to_csv(A/"paper_lernkurve_q5_rendezvous_treffer.csv", index=False)
log.close()
