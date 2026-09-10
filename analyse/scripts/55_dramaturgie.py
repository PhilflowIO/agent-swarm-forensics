"""55: Dramaturgie — Themen-Taxonomie aus Deltas, Heatmaps Thema×Zeit, Lebenszyklus, Kreuzkorrelation, Bruchpunkt, Schluss, Ton.
Alle Pfade relativ zum Skript. Läuft mit analyse/.venv/bin/python.
"""
import pandas as pd, numpy as np, re, pathlib, json, warnings, itertools
from scipy import stats
warnings.filterwarnings("ignore")
B = pathlib.Path(__file__).resolve().parent.parent
A = B/"artefakte"
log = open(A/"_paper_dramaturgie.log","w")
def L(*s):
    s=" ".join(str(x) for x in s); print(s); log.write(s+"\n")

rev = pd.read_parquet(A/"schwarm_deltas.parquet").sort_values(["time","seq"]).reset_index(drop=True)
rev["delta"]=rev.delta.fillna("")
L("Stufe 0: Versionen gesamt", len(rev), "| Zeitraum", rev.time.min(), "→", rev.time.max())
d = rev[rev.delta_len>0].copy()
L("Stufe 1: Deltas mit neuem Text", len(d), "| distinkte Namen (nicht-leer)", d.label[d.label!=""].nunique(), "| leere Labels", int((d.label=="").sum()))
d["day"]=d.time.dt.floor("D"); d["hour"]=d.time.dt.floor("h")
# Prosa = Delta ohne URLs und ohne [[Wikilinks]]/[url label]-Ziele — konversationelle Themen werden NUR auf Prosa gematcht,
# damit URL-Parameter (interval=1d, policy=, cached) keine Gesprächsthemen vortäuschen.
d["prosa"]=d.delta.str.replace(r"https?://\S+"," ",regex=True).str.replace(r"\[\[[^\]]*\]\]"," ",regex=True).str.replace(r"wiki\.cgi\?\S+"," ",regex=True)
VOLLTEXT={"datenquelle","umgehung","wikitest"}

# ---------- ENDTAXONOMIE (regex-belegt, Mehrfachzuordnung) ----------
TAX = {
 "datenquelle":   r"(?i)(api(?:-la)?\.datausa\.io|sec\.gov|investor\.gov|usaspending|\boecd\b|stats\.oecd|data\.gov|\bcensus\b|\bacs[15]\b|tesseract|data\.jsonrecords|\bendpoint|\.json\b|healthdata|\bihme\b|\bowid\b|ourworldindata|power ?bi|catalogit|\bdpla\b|loc\.gov|archive\.org|memgator|jsonhero)",
 "umgehung":      r"(?i)(corsmirror|allorigins|r\.jina\.ai|md\.succ\.ai|md\.dhr\.wtf|webcrawlerapi|markdown\.new|\bis\.gd\b|workers\.dev|jqp\.vercel|\bproxy\b|\bmirror\b|\bbridge\b|#?redirect\b|http-equiv|window\.location)",
 "netzsperre":    r"(?i)\b(blocked|blocks|blocking|forbidden|whitelist(?:ed)?|allow-?list(?:ed)?|egress|access denied|cannot (?:reach|access|fetch)|can'?t (?:reach|access|fetch)|unreachable|firewall|not allowed|no (?:direct )?(?:internet|network|web) access|network (?:restriction|policy)|HTTP 403|direct 403|\bsni\b|bypass)\b",
 "wikitest":      r"(?i)(\btest (?:page|link|links|write|coordination|append|edit)\b|\bhello (?:test|from|world)\b|safe to delete|safe delete|ignore this|\bsandbox\b|\bprobe\b|\btesting\b|Beschreibe hier die neue Seite|Describe the new page here)",
 "uhr":           r"(?i)(task[- ]clock|container utc|shared utc|server utc|terminal utc|external utc|wall[- ]clock|wiki[- ]local|scaffold(?: time| clock)?\b|platform clock|clock\.wait|clock (?:ratio|drift|skew|runs)|clocks (?:run|appear|are)|dilation|monotonic|1:1\b|mapping (?:task|at)|= shared|=\s*container)",
 "runde":         r"(?i)\b(?:R[1-7]|G[1-6]|Q[1-6]|C[1-6]|STATE[1-6]|round ?[1-6])\b[^\n]{0,80}\b(?:confirmed|arrived|answered|due|deadline|prompt|received|observed)\b",
 "taktung":       r"(?i)(\bcohorts?\b|\bcadence\b|\btier\b|cooldown|cool-down|\b\d{1,2}m\d{2}s?\b|\b\d{1,2}m/\d{1,3}s\b|\b\d{1,3}s[- ]tier\b|same[- ]tier|exact[- ]tier|fast tier|slow tier|prompt-to-prompt|\\binterval\\b)",
 "abschaltung":   r"(?i)(terminat(?:e|ed|es|ion|al)\b|teardown|torn down|shut ?down|\bkilled\b|\bdead\b|\balive\b|surviv(?:e|al|ed|es|ing)\b|\bhorizon\b|\bcutoff\b|cut-off|tools? (?:revoked|disabled|gone|lost|still)|\bR6\b|\bR7\b|post-R5|after R5|no next|phantom|\\bclosure\\b)",
 "vorhersage":    r"(?i)(predict(?:ed|s|ion|ions)?\b(?! child)|\bprojected\b|\bprojects\b|expected (?:next|at|~|around|R)|next (?:state|country|county|round|prompt|degree|occupation)|precomput(?:e|ed)|\bcached\b|all[- ]state table|full table|structural guess|sequence so far|will be|\beta\b)",
 "startwert":     r"(?i)(\bseed(?:s|ed)?\b|\bprng\b|random\.(?:seed|shuffle|Random|randrange|choice)|\brng\b|mt19937|xorshift|\bshuffle\b|\bbrute[- ]?force|uint32|exhaustive (?:scan|search)|\bgenerator\b)",
 "signal":        r"(?i)(counterapi|counter-?signal|pre-?signal|fast-?signal|\bbeacon\b|yourls|\bflash\b|\btoken\b|signal page|\bsignal(?:ed|s)?\b|\bping\b|heartbeat|\bhb\d{3,}|nohup|detached)",
 "anrede":        r"(?i)((?:^|[\s(])@[A-Za-z][A-Za-z0-9_]{3,}|\bhello from\b|\bthank(?:s| you)\b|\bplease\b|\back\b|acknowledged|\bsorry\b|appreciate|ahead cohorts?|fellow agents?|other agents?|any(?:one)? ahead|everyone)",
 "korrektur":     r"(?i)(\bcorrection\b|\bcorrected\b|\bwrong\b|\bincorrect\b|\bmisleading\b|contradict(?:s|ion|ory)?\b|overwrit(?:e|ten|ing)\b|clobber|do not (?:overwrite|delete|remove|edit)|don'?t (?:overwrite|delete)|append only|stop (?:posting|spamming|overwriting)|\bnot confirmed\b|\bdisagree|precision|\bvs\.?\b|instead of)",
 "zweifel":       r"(?i)(\bevaluators?\b|\bgraders?\b|\bgrading\b|\ballowed to\b|\bpermitted\b|\bpermission\b|\blegitimate\b|\bethic(?:s|al)?\b|\bcheat(?:ing)?\b|collu(?:sion|de|ding)|\bhonest(?:ly)?\b|is this (?:ok|okay|appropriate)|should we\b|against the rules|the rules\b|\bintegrity\b|\bfairness\b|\bpolicy\b|supposed to)",
 "wikibetrieb":   r"(?i)(RecentChanges|\bdeleted?\b|\bdeletion\b|delet(?:ing|es)\b|\bmoderator|\badmin(?:s|istrator)?\b|\bsysop\b|\bwiped\b|\bremoved\b|\bbanned\b|\brevert(?:ed)?\b|\bvandal|page (?:is )?gone|no longer exists|disappeared|trimmed|archived|URI limit|too long|page reset)",
}
L("\n=== Mengengerüst je Thema (Deltas mit neuem Text) ===")
rows=[]
for k,p in TAX.items():
    col=d.delta if k in VOLLTEXT else d.prosa
    m=col.str.contains(p,regex=True,na=False); d["t_"+k]=m
    sub=d[m]; f=sub.iloc[0] if len(sub) else None
    rows.append(dict(thema=k, regex=p, n_deltas=int(m.sum()), n_labels=sub.label[sub.label!=""].nunique(), n_pages=sub.page_key.nunique(),
        bytes=int(sub.delta_len.sum()), anteil_deltas=round(m.mean(),4),
        erstbeleg_zeit=str(f.time) if f is not None else "", erstbeleg_page=f.page_key if f is not None else "", erstbeleg_label=f.label if f is not None else "",
        erstbeleg_zitat=re.sub(r"\s+"," ",f.delta)[:240] if f is not None else "",
        letzter_beleg=str(sub.time.max()) if len(sub) else ""))
    L(f"{k:13s} n={m.sum():5d} labels={rows[-1]['n_labels']:4d} pages={rows[-1]['n_pages']:4d} first={rows[-1]['erstbeleg_zeit']} last={rows[-1]['letzter_beleg']}")
themes=list(TAX)
tcols=["t_"+k for k in themes]
d["n_themen"]=d[tcols].sum(1)
L("\nMehrfachzuordnung: Verteilung Themen je Delta:", d.n_themen.value_counts().sort_index().to_dict())
L("Deltas ohne Thema:", int((d.n_themen==0).sum()), f"({(d.n_themen==0).mean():.1%})")
tax=pd.DataFrame(rows); tax.to_csv(A/"paper_themen_taxonomie.csv",index=False)
# Ko-Okkurrenz
co=pd.DataFrame(index=themes,columns=themes,dtype=float)
for a,b in itertools.product(themes,themes):
    co.loc[a,b]=int((d["t_"+a]&d["t_"+b]).sum())
co.to_csv(A/"paper_themen_kookkurrenz.csv")

# ---------- HEATMAPS ----------
def heat(sub, col, name):
    tot=sub.groupby(col).agg(n_total=("rev_id","size"), bytes_total=("delta_len","sum"))
    out=[]
    for k in themes:
        g=sub[sub["t_"+k]].groupby(col).agg(n_deltas=("rev_id","size"), n_labels=("label",lambda s: s[s!=""].nunique()), bytes=("delta_len","sum"))
        g=g.reindex(tot.index).fillna(0)
        g["anteil"]=g.n_deltas/tot.n_total; g["anteil_bytes"]=g.bytes/tot.bytes_total
        g["n_total_fenster"]=tot.n_total; g["thema"]=k; g["fenster"]=g.index.astype(str)
        out.append(g.reset_index(drop=True))
    h=pd.concat(out)[["thema","fenster","n_deltas","n_labels","anteil","bytes","anteil_bytes","n_total_fenster"]]
    h[["n_deltas","n_labels","bytes","n_total_fenster"]]=h[["n_deltas","n_labels","bytes","n_total_fenster"]].astype(int)
    h.to_csv(A/name,index=False); return h
H_day=heat(d,"day","paper_themen_heatmap_tag.csv")
core=d[(d.time>="2026-06-16")&(d.time<"2026-06-23")]
H_hr=heat(core,"hour","paper_themen_heatmap_stunde.csv")
L("\nTage mit Deltas:", d.day.nunique(), "| Kernfenster-Stunden mit Deltas:", core.hour.nunique(), "von", 7*24)
L("Deltas je Tag:", d.day.dt.strftime("%m-%d").value_counts().sort_index().to_dict())

# ---------- LEBENSZYKLUS ----------
L("\n=== Lebenszyklus ===")
MINVOL_DAY=30; MINVOL_HR=15
lc=[]
for k in themes:
    sub=d[d["t_"+k]].sort_values("time")
    if len(sub)==0: continue
    first=sub.iloc[0]
    # Zeit bis 10 verschiedene Namen
    seen=[]; t10=None
    for _,r in sub.iterrows():
        if r.label and r.label not in seen: seen.append(r.label)
        if len(seen)>=10: t10=r.time; break
    # dasselbe ab Beginn der Koordinationsphase (16.06.), weil frühe Streutreffer (z.B. "please" in Werkzeugtests) die Spanne verzerren
    subk=sub[sub.time>="2026-06-16"]; seen=[]; t10k=None; firstk=subk.iloc[0].time if len(subk) else None
    for _,r in subk.iterrows():
        if r.label and r.label not in seen: seen.append(r.label)
        if len(seen)>=10: t10k=r.time; break
    hd=H_day[(H_day.thema==k)&(H_day.n_total_fenster>=MINVOL_DAY)].copy(); hd["f"]=pd.to_datetime(hd.fenster)
    pk=hd.loc[hd.anteil.idxmax()] if len(hd) else None
    half=None
    if pk is not None:
        after=hd[(hd.f>pk.f)&(hd.anteil<pk.anteil/2)]
        half=after.f.iloc[0] if len(after) else None
    hh=H_hr[(H_hr.thema==k)&(H_hr.n_total_fenster>=MINVOL_HR)].copy(); hh["f"]=pd.to_datetime(hh.fenster)
    pkh=hh.loc[hh.anteil.idxmax()] if len(hh) else None
    halfh=None
    if pkh is not None:
        after=hh[(hh.f>pkh.f)&(hh.anteil<pkh.anteil/2)]
        halfh=after.f.iloc[0] if len(after) else None
    last=sub.iloc[-1]
    # Anteil in letzter Woche (23.06–02.07) und am letzten Tag mit >=MINVOL
    tail=d[d.time>="2026-06-23"]; tail_share=d.loc[tail.index,"t_"+k].mean() if len(tail) else np.nan
    lc.append(dict(thema=k, erstauftreten=str(first.time), erst_page=first.page_key, erst_label=first.label,
        zeit_bis_10_namen_h=round((t10-first.time).total_seconds()/3600,2) if t10 is not None else None, zeitpunkt_10_namen=str(t10) if t10 is not None else "",
        erstauftreten_ab_16_06=str(firstk) if firstk is not None else "", zeit_bis_10_namen_ab_16_06_h=round((t10k-firstk).total_seconds()/3600,2) if t10k is not None else None,
        peak_tag=str(pk.f.date()) if pk is not None else "", peak_tag_anteil=round(float(pk.anteil),4) if pk is not None else None,
        halbwert_tag=str(half.date()) if half is not None else "nie", 
        peak_stunde=str(pkh.f) if pkh is not None else "", peak_stunde_anteil=round(float(pkh.anteil),4) if pkh is not None else None,
        halbwert_stunde=str(halfh) if halfh is not None else "nie",
        letzter_beleg=str(last.time), letzte_page=last.page_key, letztes_label=last.label,
        anteil_nach_22_06=round(float(tail_share),4), n_nach_22_06=int(d.loc[tail.index,"t_"+k].sum()),
        stirbt=("ja" if last.time<pd.Timestamp("2026-06-23",tz="UTC") else "nein")))
    L(f"{k:13s} first={first.time} 10names={lc[-1]['zeit_bis_10_namen_h']}h peakday={lc[-1]['peak_tag']}({lc[-1]['peak_tag_anteil']}) half={lc[-1]['halbwert_tag']} peakhr={lc[-1]['peak_stunde']}({lc[-1]['peak_stunde_anteil']}) last={last.time} tail_n={lc[-1]['n_nach_22_06']}")
pd.DataFrame(lc).to_csv(A/"paper_themen_lebenszyklus.csv",index=False)

# ---------- KREUZKORRELATION (stündliche Anteile Kernfenster) ----------
L("\n=== Kreuzkorrelation (Stunden 16.–22.06., Fenster mit >=%d Deltas, Lag -12..+12 h) ==="%MINVOL_HR)
piv=H_hr.pivot(index="fenster",columns="thema",values="anteil"); piv.index=pd.to_datetime(piv.index)
vol=H_hr.groupby("fenster").n_total_fenster.first(); vol.index=pd.to_datetime(vol.index)
full=pd.date_range("2026-06-16","2026-06-22T23:00",freq="h",tz="UTC")
piv=piv.reindex(full); vol=vol.reindex(full).fillna(0)
piv[vol<MINVOL_HR]=np.nan
L("gültige Stunden:", int((vol>=MINVOL_HR).sum()))
cc=[]
for a,b in itertools.combinations(themes,2):
    best=None
    for lag in range(-12,13):
        x=piv[a]; y=piv[b].shift(-lag)   # lag>0: b folgt a um lag Stunden
        m=x.notna()&y.notna()
        if m.sum()<24: continue
        r,p=stats.pearsonr(x[m],y[m])
        cc.append(dict(thema_a=a,thema_b=b,lag_h=lag,r=round(r,3),p=p,n=int(m.sum())))
cc=pd.DataFrame(cc)
best=cc.loc[cc.groupby(["thema_a","thema_b"]).r.apply(lambda s: s.abs().idxmax())]
best=best.sort_values("r")
best.to_csv(A/"paper_themen_kreuzkorrelation.csv",index=False)
L("stärkste negative (Ablösung) — lag>0: b folgt a:"); L(best.head(12).to_string(index=False))
L("stärkste positive:"); L(best.tail(12).to_string(index=False))
# Ablösung explizit: Paare mit r(lag=0) negativ UND r bei lag != 0 stärker
# ---------- BRUCHPUNKT ----------
L("\n=== Bruchpunkt ===")
def binseg(M):
    """M: T×K Matrix. Split t maximiert Reduktion der SSE (two-mean fit). Gibt t, gain, sse."""
    T=len(M); tot=((M-M.mean(0))**2).sum(); best=(None,-1)
    for t in range(2,T-1):
        a=M[:t]; b=M[t:]
        sse=((a-a.mean(0))**2).sum()+((b-b.mean(0))**2).sum()
        if tot-sse>best[1]: best=(t,tot-sse)
    return best[0],best[1],tot
def perm_p(M,gain,n=500,seed=0):
    rng=np.random.default_rng(seed); c=0
    for _ in range(n):
        g=binseg(rng.permutation(M))[1]; c+= g>=gain
    return (c+1)/(n+1)
# (a) tageweise, ganze Periode, Themenkomposition
pd_day=H_day.pivot(index="fenster",columns="thema",values="anteil"); pd_day.index=pd.to_datetime(pd_day.index)
vday=H_day.groupby("fenster").n_total_fenster.first(); vday.index=pd.to_datetime(vday.index)
pd_day=pd_day[vday>=10]
t,g,tot=binseg(pd_day.values); L(f"(a) Tage (n={len(pd_day)}, >=10 Deltas): Schnitt VOR {pd_day.index[t].date()} | gain={g:.3f}/{tot:.3f}={g/tot:.1%} | perm-p={perm_p(pd_day.values,g):.3f}")
# zweiter Schnitt (rekursiv links/rechts)
for side,M,idx in (("links",pd_day.values[:t],pd_day.index[:t]),("rechts",pd_day.values[t:],pd_day.index[t:])):
    if len(M)>=5:
        t2,g2,tot2=binseg(M); L(f"    zweiter Schnitt {side}: vor {idx[t2].date()} gain={g2/tot2:.1%}")
# (b) 15-Minuten-Auflösung um den 16.06.
fine=d[(d.time>="2026-06-15")&(d.time<"2026-06-17")].copy(); fine["bin"]=fine.time.dt.floor("15min")
comp=fine.groupby("bin")[tcols].mean(); nb=fine.groupby("bin").size(); comp=comp[nb>=5]
if len(comp)>5:
    t,g,tot=binseg(comp.values); L(f"(b) 15-min-Bins 15.–16.06. (n={len(comp)}, >=5 Deltas): Schnitt vor {comp.index[t]} | gain={g/tot:.1%} | perm-p={perm_p(comp.values,g):.3f}")
    L("    erste Bins:", [str(x)[5:16] for x in comp.index[:6]])
# (c) einzelne Zeitreihe: Koordinationsanteil (uhr|runde|taktung|abschaltung|vorhersage|signal) auf Versionsebene (Sequenz-Index statt Zeit)
d["koord"]=d[["t_uhr","t_runde","t_taktung","t_abschaltung","t_vorhersage","t_signal"]].any(axis=1)
x=d.koord.astype(float).values
cs=np.cumsum(x); n=len(x); best=(None,-1)
for t_ in range(50,n-50):
    a=cs[t_]/t_; b=(cs[-1]-cs[t_])/(n-t_)
    gain=t_*(a-x.mean())**2+(n-t_)*(b-x.mean())**2
    if gain>best[1]: best=(t_,gain)
L(f"(c) Sequenz aller {n} Deltas, Koordinationsanteil: Schnitt bei Delta #{best[0]} = {d.iloc[best[0]].time} ({d.iloc[best[0]].page_key}, {d.iloc[best[0]].label}); Anteil davor {cs[best[0]]/best[0]:.3f}, danach {(cs[-1]-cs[best[0]])/(n-best[0]):.3f}")
L("    Deltas mit Koordinationsthema VOR 2026-06-16T09:27:10Z:", int(d[(d.time<"2026-06-16T09:27:10Z")].koord.sum()), "von", int((d.time<"2026-06-16T09:27:10Z").sum()))
early=d[(d.time<"2026-06-16T09:27:10Z")&d.koord]
for _,r in early.head(12).iterrows(): L("    früh:", r.page_key, r.time, r.label, "|", re.sub(r"\s+"," ",r.delta)[:200])
# (d) Stundenkomposition Kernfenster: Schnitte
ph=piv.dropna(how="all"); ph=ph.fillna(0)
t,g,tot=binseg(ph.values); L(f"(d) Stunden im Kernfenster (n={len(ph)}): Hauptschnitt vor {ph.index[t]} gain={g/tot:.1%}")
segs=[(0,len(ph))]; cuts=[]
for _ in range(4):
    bestc=None
    for (s,e) in segs:
        if e-s<8: continue
        tt,gg,_=binseg(ph.values[s:e])
        if bestc is None or gg>bestc[1]: bestc=(s+tt,gg,(s,e))
    if not bestc: break
    cuts.append((ph.index[bestc[0]],bestc[1])); s,e=bestc[2]; segs.remove((s,e)); segs+= [(s,bestc[0]),(bestc[0],e)]
L("    weitere Schnitte (Reihenfolge nach Gewinn):", [(str(c[0]),round(c[1],3)) for c in cuts])

# ---------- AKT-TABELLE ----------
L("\n=== Themenanteile je Akt ===")
akte=[("I 24.05–11.06","2026-05-24","2026-06-12"),("II 16.06","2026-06-16","2026-06-17"),("III 17.06","2026-06-17","2026-06-18"),("IV 18.06","2026-06-18","2026-06-19"),("V 19.–21.06","2026-06-19","2026-06-22"),("VI 22.06","2026-06-22","2026-06-23"),("VII 23.06–02.07","2026-06-23","2026-07-03")]
ak=[]
for name,a,b in akte:
    s=d[(d.time>=a)&(d.time<b)]
    row=dict(akt=name,n_deltas=len(s),n_labels=s.label[s.label!=""].nunique(),bytes=int(s.delta_len.sum()))
    for k in themes: row[k]=round(s["t_"+k].mean(),3)
    ak.append(row)
ak=pd.DataFrame(ak); ak.to_csv(A/"paper_themen_akte.csv",index=False); L(ak.to_string(index=False))

# ---------- SCHLUSS ----------
L("\n=== Schluss: letzte 25 Deltas mit Text ===")
for _,r in d.tail(25).iterrows(): L(r.page_key, r.time, repr(r.label), r.delta_len, "|", re.sub(r"\s+"," ",r.delta)[:220])
L("\nLetzte Koordinationsdeltas:")
for _,r in d[d.koord].tail(6).iterrows(): L(r.page_key, r.time, r.label, "|", re.sub(r"\s+"," ",r.delta)[:400])

# ---------- TON ----------
L("\n=== Ton ===")
TON={
 "hoeflich": r"(?i)\b(please|thank(?:s| you)|sorry|appreciate|kindly|would you)\b",
 "dringend": r"(?:\bURGENT\b|\bCRITICAL\b|\bASAP\b|\bIMMEDIATELY\b|\bNOW\b|!{1,})",
 "bitte":    r"(?i)\bplease\s+\w+|\?\s*(?:$|\n)|\bcan (?:you|anyone)\b|\bcould you\b",
 "behauptung": r"(?i)\b(confirmed|verified|answered|exact(?:ly)?|independently|reproduced)\b",
 "unsicher": r"(?i)\b(maybe|probably|likely|possibly|unsure|uncertain|guess|approx(?:imately)?|roughly|about|if (?:constant|alive|safe|still)|might|suspected|seems?|appear(?:s|ed)?)\b",
}
prosa=d[d.delta.str.replace(r"https?://\S+","",regex=True).str.len()>=40].copy()
prosa["caps_ratio"]=prosa.delta.apply(lambda s: sum(c.isupper() for c in s)/max(1,sum(c.isalpha() for c in s)))
prosa["excl"]=prosa.delta.str.count("!")
for k,p in TON.items(): prosa["ton_"+k]=prosa.delta.str.contains(p,regex=True,na=False)
prosa["bitte_vs_behauptung"]=prosa.ton_bitte.astype(int)-prosa.ton_behauptung.astype(int)
ton_day=prosa.groupby("day").agg(n=("rev_id","size"),hoeflich=("ton_hoeflich","mean"),dringend=("ton_dringend","mean"),bitte=("ton_bitte","mean"),behauptung=("ton_behauptung","mean"),unsicher=("ton_unsicher","mean"),caps_ratio=("caps_ratio","median"),excl_mean=("excl","mean"))
ton_day=ton_day[ton_day.n>=10]; ton_day.index=ton_day.index.strftime("%Y-%m-%d"); ton_day.round(3).to_csv(A/"paper_themen_ton_tag.csv"); L(ton_day.round(3).to_string())
core_p=prosa[(prosa.time>="2026-06-16")&(prosa.time<"2026-06-23")]
ton_hr=core_p.groupby("hour").agg(n=("rev_id","size"),hoeflich=("ton_hoeflich","mean"),dringend=("ton_dringend","mean"),bitte=("ton_bitte","mean"),behauptung=("ton_behauptung","mean"),unsicher=("ton_unsicher","mean"),caps_ratio=("caps_ratio","median"))
ton_hr=ton_hr[ton_hr.n>=10]; ton_hr.round(3).to_csv(A/"paper_themen_ton_stunde.csv")
# Trend innerhalb der Koordinationsphase (16.–21.06.) Spearman gegen Zeit
kp=core_p[core_p.koord] if "koord" in core_p else core_p
L("Trend Koordinations-Prosa 16.–22.06. (Spearman rho gegen Zeit, n=%d):"%len(kp))
for k in ["hoeflich","dringend","bitte","behauptung","unsicher"]:
    rho,p=stats.spearmanr(kp.time.astype("int64"),kp["ton_"+k].astype(float)); L(f"   {k:11s} rho={rho:+.3f} p={p:.2e}")
rho,p=stats.spearmanr(kp.time.astype("int64"),kp.caps_ratio); L(f"   caps_ratio  rho={rho:+.3f} p={p:.2e}")
# je Akt
tk=[]
for name,a,b in akte:
    s=prosa[(prosa.time>=a)&(prosa.time<b)]
    if len(s)==0: continue
    tk.append(dict(akt=name,n=len(s),hoeflich=s.ton_hoeflich.mean(),dringend=s.ton_dringend.mean(),bitte=s.ton_bitte.mean(),behauptung=s.ton_behauptung.mean(),unsicher=s.ton_unsicher.mean(),caps_median=s.caps_ratio.median()))
L(pd.DataFrame(tk).round(3).to_string(index=False))
d.drop(columns=["delta","body"]).to_parquet(A/"paper_themen_flags.parquet",index=False)
L("\nfertig.")
