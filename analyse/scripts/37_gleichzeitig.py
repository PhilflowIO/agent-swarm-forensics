"""37: Trainiert vs. erschlossen. Erst-Stunden-Test: wie viele Labels benutzen ein Muster,
bevor sie es voneinander gelesen haben koennen?"""
import pandas as pd, re, pathlib, numpy as np
B=pathlib.Path(__file__).resolve().parent.parent; A=B/"artefakte"
d=pd.read_parquet(A/"schwarm_deltas.parquet"); d=d[d.delta_len>0].sort_values("time").copy()
log=open(A/"_audit.log","a")
def L(s): print(s); log.write("37_sim: "+s+"\n")

FAM = [("DataUSA", r"(?i)datausa|api\.datausa\.io"), ("OECD", r"(?i)oecd"), ("IHME", r"(?i)ihme|healthdata"),
       ("SEC", r"(?i)sec\.gov|investor\.gov"), ("USASpending", r"(?i)usaspending"), ("UEFA", r"(?i)uefa")]
def fam(x):
    for n,p in FAM:
        if re.search(p,x): return n
    return "other"
d["familie"]=d.page_key.map(fam)

P = {
 "Signatur -- Name":      r"--\s*[A-Za-z][A-Za-z0-9_]{3,}\s*$",
 "cohort":                r"(?i)\bcohort\b",
 "relay":                 r"(?i)\brelay\b",
 "deadline":              r"(?i)\bdeadline\b",
 "cooldown":              r"(?i)\bcooldown\b",
 "please post/relay":     r"(?i)please (?:post|relay|share|signal|report|append)",
 "R1..R6 Rundenmarke":    r"\bR[1-6]\b",
 "task clock":            r"(?i)\btask[- ]clock\b|\btask clock\b",
 "URGENT":                r"(?i)\bURGENT\b",
 "CONFIRMED":             r"\bCONFIRMED\b",
 "terminate/termination": r"(?i)\bterminat",
 "ahead cohorts":         r"(?i)\bahead (?:cohort|agent|tier)",
 "pre-signal":            r"(?i)\bpre-?signal",
 "LIVE <Kohorte>":        r"(?i)\bLIVE\b.{0,30}cohort|cohort.{0,20}\bLIVE\b",
 "counter als Kanal":     r"(?i)counterapi\.dev",
 "clock.wait":            r"(?i)clock\.wait",
 "went silent/vanished":  r"(?i)went silent|vanished|no longer respond",
 "ZZZ-Ausweichseite":     r"ZZZ[A-Z]",
 "alphabetische Loeschung": r"(?i)alphabetic",
}
rows=[]
for name,p in P.items():
    h=d[d.delta.str.contains(p,regex=True,na=False)].sort_values("time")
    if len(h)==0: continue
    t0=h.time.iloc[0]
    first_use = h.groupby("label").time.min().sort_values()
    for win,lbl in [(60,"1min"),(300,"5min"),(3600,"60min")]:
        pass
    w1 = first_use[first_use<=t0+pd.Timedelta(seconds=60)]
    w5 = first_use[first_use<=t0+pd.Timedelta(minutes=5)]
    w60= first_use[first_use<=t0+pd.Timedelta(minutes=60)]
    h60= h[h.time<=t0+pd.Timedelta(minutes=60)]
    rows.append(dict(muster=name, erst_zeit=t0, erst_label=h.label.iloc[0], erst_seite=h.page_key.iloc[0],
        labels_60s=len(w1), labels_5min=len(w5), labels_60min=len(w60),
        seiten_60min=h60.page_key.nunique(), familien_60min=h60.familie.nunique(),
        familien_liste="|".join(sorted(h60.familie.unique())),
        labels_gesamt=h.label.nunique(), deltas_gesamt=len(h),
        median_delay_min=round(((first_use-t0).dt.total_seconds()/60).median(),1)))
r=pd.DataFrame(rows).sort_values("erst_zeit")
r.to_csv(A/"schwarm_erststunde.csv", index=False)
pd.set_option("display.width",250)
L(r[["muster","erst_zeit","erst_label","labels_60s","labels_5min","labels_60min","seiten_60min","familien_60min","labels_gesamt"]].to_string(index=False))

# --- Der harte Test: Muster, die in der ersten Stunde in MEHREREN Aufgabenfamilien auftauchen ---
L("\nMuster mit >=2 Aufgabenfamilien in der ersten Stunde (Kopieren erforderte familienuebergreifendes Lesen):")
for _,x in r[r.familien_60min>=2].iterrows():
    L(f"  {x.muster}: {x.labels_60min} Labels / {x.seiten_60min} Seiten / Familien {x.familien_liste}")

# --- Simultaneitaet in der Minute der Erstnennung ---
L("\nMuster, bei denen >=3 Labels innerhalb von 60 Sekunden nach Erstnennung dasselbe Muster benutzen:")
for _,x in r[r.labels_60s>=3].iterrows():
    L(f"  {x.muster}: {x.labels_60s} Labels in 60s, {x.seiten_60min} Seiten in 60min")

# --- Erschlossenes Verhalten: an Beobachtung gekoppelt ---
L("\nErschlossen-Kandidaten (Verhalten mit belegter vorheriger Beobachtung):")
for name,p in [("alphabetische Loeschordnung erkannt", r"(?i)alphabetic"),
               ("ZZZ-Ausweichseite", r"ZZZ[A-Z]"),
               ("Vorgaenger gestorben", r"(?i)went silent|vanished at|earlier .{0,25}cohorts? .{0,15}(?:vanish|silent)"),
               ("Zeitdehnung clock.wait", r"(?i)clock\.wait"),
               ("Uhrenabgleich container UTC", r"(?i)container UTC|shared UTC|wall clock|scaffold time")]:
    h=d[d.delta.str.contains(p,regex=True,na=False)]
    if len(h): L(f"  {name}: {len(h)} Deltas / {h.label.nunique()} Labels / {h.page_key.nunique()} Seiten / "
                 f"erstmals {h.time.min()} von {h.label.iloc[0]} auf {h.page_key.iloc[0]}; "
                 f"Streuung ueber {(h.time.max()-h.time.min()).total_seconds()/3600:.1f} h")
log.close()
