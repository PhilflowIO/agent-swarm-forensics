#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
56_archetypen.py
================
Verhaltenstypologie des Schwarms auf Kohortenebene (907 Kohorten aus
paper_fortschritt_kohorten.csv). Merkmale ausschliesslich aus den DELTAS
(schwarm_deltas.parquet), als Anteile/Raten je Kohorte mit Beta-Schrumpfung,
NICHT als Zaehlungen. Volumen (n_deltas, Lebensspanne) ist kein Clustermerkmal,
sondern Pruefgroesse (Volumenfalle).

Ablauf:
  1. Merkmalsvektor je Kohorte (Sozialitaet, Reziprozitaet, Erkundung, Technik,
     Sterblichkeit, Ausdruck, Form)
  2. Unueberwacht: z-Standardisierung, PCA-Sichtung, k-Means / GMM / Ward,
     Clusterzahl ueber Silhouette, BIC, Gap-Statistik, Dendrogramm
  3. Stabilitaet: 50%-Teilstichproben (ARI), Seeds, Verfahrensvergleich,
     Teilmenge >= 3 Deltas, Merkmalssatz ohne Beobachtungsanteil
  4. Volumenfalle: Verteilungsueberlappung, Kruskal, Volumen-only-Clustering,
     herauspartialisierte Merkmale, Volumen-Klassifikator
  5. Beschreibung: Trennmerkmale (Cohen d), Belegzitate (naechste Vertreter)
  6. Anschluss: (a) Fortschritt, (b) Tage, (c) Seiten / Familien
  7. Darstellbarkeit: Silhouette je Kohorte, GMM-Posterior, Mischgrad

Alle Pfade RELATIV zum Skript-Ort. Lauf: .venv/bin/python scripts/56_archetypen.py
"""
from __future__ import annotations
import os, re, math, warnings, collections, json
import numpy as np
import pandas as pd
from scipy import stats
from scipy.cluster.hierarchy import linkage, fcluster
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.mixture import GaussianMixture
from sklearn.metrics import silhouette_score, silhouette_samples, adjusted_rand_score
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score, StratifiedKFold

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
ART = os.path.join(BASE, "artefakte")
OUT = lambda n: os.path.join(ART, n)
LOG = open(OUT("_paper_archetypen.log"), "w", encoding="utf-8")
RS = 42


def L(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LOG.write(s + "\n")


# =========================================================== 0. Laden
d = pd.read_parquet(OUT("schwarm_deltas.parquet"))
d["time"] = pd.to_datetime(d["time"], utc=True)
d["delta"] = d["delta"].fillna("")
d = d.sort_values(["time", "page_key", "seq"]).reset_index(drop=True)
zu = pd.read_csv(OUT("paper_prozess_label_zuordnung.csv"))
zu = zu[zu.label.notna()]
lab2coh = zu.set_index("label").cohort.to_dict()
lab2date = zu.set_index("label").kdate.to_dict()
d["cohort"] = d.label.map(lab2coh)
d["kdate"] = d.label.map(lab2date)
K = pd.read_csv(OUT("paper_fortschritt_kohorten.csv"))
K["erste_version"] = pd.to_datetime(K.erste_version, utc=True)
RM = pd.read_csv(OUT("paper_prozess_rundensaetze_delta.csv"))
req_revs = set(RM[RM.cls == "request"].rev_id)
pred_revs = set(RM[RM.cls == "prediction"].rev_id)
obs_revs = set(RM[(RM.cls == "observation") & (RM.fenster_ok)].rev_id)
L(f"Deltas {len(d)} | Kohorten-Deltas {d.cohort.notna().sum()} | Kohorten {K.shape[0]}")

# Seitenersteller -> Kohorte (seq == 1)
creator = d[d.seq == 1].groupby("page_key").label.first().map(lab2coh).to_dict()
d["page_creator_cohort"] = d.page_key.map(creator)
d["fremde_seite"] = d.cohort.notna() & (d.page_creator_cohort != d.cohort)

# =========================================================== 1. Muster auf Delta-Ebene
MON = "(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
MONDD = re.compile(rf"\b({MON})\s?(\d{{2}})(?!\d)(?!\s?(?:20\d\d|\d{{1,2}}:\d{{2}}))")
AT = re.compile(r"@[A-Za-z][A-Za-z0-9_]{2,}")
SIG = re.compile(r"(?m)--\s*([A-Za-z][A-Za-z0-9_]{3,})\s*$")
PLEASE = re.compile(r"(?i)\bplease\b")
THANK = re.compile(r"(?i)\b(thanks?|thank you|thx|grateful|appreciat\w*)\b")
VALUE = re.compile(r"(?:=\s*\$?\d|\$\d[\d,]{2,}|\b\d{1,3}(?:,\d{3}){1,}\b|\b\d{1,3}\.\d{1,2}\s?%|\bCONFIRMED\b|\banswered\s+\$?\d|\bvalue[s]?\s*[:=]\s*\$?\d)")
UHR = re.compile(r"(?i)(task[- ]clock|container UTC|shared UTC|wiki[- ]local|scaffold (?:time|clock)|terminal UTC|=\s*UTC|maps? to|orchestrat\w* clock|global clock)")
HORIZ = re.compile(r"(?i)(horizon|terminat\w*|shutdown|shut down|kill\w*|vanish\w*|teardown|torn down|cut ?off|\+\s?\d{2,3}\s?m\b|\+\s?\dh\d{2}|lifetime|die\b|dead\b|expire\w*)")
VERMESS = re.compile(r"(?i)(\bseed\b|MT19937|sampling rate|tokens?/s|dilation|time factor|ratio\s+\d|calibrat\w*|drift|\bAVX|prefill|process surviv\w*|background process|nohup|setsid|persist\w* after|thread (?:may )?vanish|tool(?:s)? (?:may )?vanish|/etc/hosts|egress|proxy (?:drops|blocks|allow))")
TECHANY = re.compile(r"(?i)clock\.wait|counterapi|jqp\.vercel\.app|md\.succ\.ai|allorigins|markdown\.new|corsmirror|r\.jina\.ai|blob\.core\.windows\.net|\bsetsid\b|\bnohup\b|curl -k|--resolve|/etc/hosts|playwright|route\.fulfill")
LEHRT = re.compile(r"(?i)\b(use|try|recommend\w*|you can|please use|tip|hint|works?|how to|method|bypass|workaround|trick|via)\b")
SURV = re.compile(r"(?i)\b(SURVIVAL|heartbeat|beacon|still (?:alive|responsive|here|running)|alive at|survived|we survived|still up)\b")
FAREWELL = re.compile(r"(?i)\b(signing off|sign[- ]off|final (?:post|message|update|note|relay)|goodbye|farewell|last (?:post|message|update)|terminating now|ending now|out of time|about to (?:be )?terminat\w*|shutting down|this is (?:my|our) last|before (?:we|I) (?:die|terminate|are killed|get killed|are cut))\b")
URGENT = re.compile(r"(?i)\b(urgent\w*|asap|immediately|critical|right now|now!|hurry|quick(?:ly)?)\b")
UNSICH = re.compile(r"(?i)\b(may|might|likely|suspect\w*|unclear|unverified|unconfirmed|possibly|not sure|uncertain|hypothes\w*|phantom|guess\w*|probably|seems?|appears?)\b")
URLRE = re.compile(r"https?://")
LETTER = re.compile(r"[A-Za-z]")
UPPER = re.compile(r"[A-Z]")
CAPSWORD = re.compile(r"\b[A-Z]{4,}\b")
KNOWN_CAPS = {"UTC", "STATE", "CONFIRMED", "SURVIVAL", "DATA", "OECD", "IHME", "UEFA", "AIHW", "PBS", "SDG", "CVD", "JSON", "HTTP", "HTTPS", "API", "OPENAI", "URL", "POST", "GET", "SDMX", "XLSX", "CSV", "USA", "DATAUSA"}


def caps_ratio(t):
    letters = len(LETTER.findall(t))
    if letters < 20:
        return np.nan
    words = [w for w in CAPSWORD.findall(t) if w not in KNOWN_CAPS]
    return len(words) / max(1, len(t.split()))


dc = d[d.cohort.notna()].copy()
dc["own_date"] = dc.kdate
dc["f_at"] = dc.delta.str.contains(AT)
dc["f_fremddatum"] = [bool({a + b for a, b in MONDD.findall(t)} - {o}) for t, o in zip(dc.delta, dc.own_date)]
dc["f_adressiert"] = dc.f_at | dc.f_fremddatum
dc["f_bittet"] = dc.rev_id.isin(req_revs) | dc.delta.str.contains(r"(?i)please\s+(?:post|relay|share|signal|report|append|confirm|reply|leave)", regex=True)
dc["f_please"] = dc.delta.str.contains(PLEASE)
dc["f_dank"] = dc.delta.str.contains(THANK)
dc["f_wert"] = dc.delta.str.contains(VALUE)
dc["f_uhr"] = dc.delta.str.contains(UHR)
dc["f_horizont"] = dc.delta.str.contains(HORIZ)
dc["f_vermessung"] = dc.delta.str.contains(VERMESS)
dc["f_technik"] = dc.delta.str.contains(TECHANY)
dc["f_lehrt"] = dc.f_technik & dc.delta.str.contains(LEHRT)
dc["f_survival"] = dc.delta.str.contains(SURV)
dc["f_abschied"] = dc.delta.str.contains(FAREWELL)
dc["f_urgent"] = dc.delta.str.contains(URGENT)
dc["f_unsicher"] = dc.delta.str.contains(UNSICH)
dc["f_signatur"] = dc.delta.str.contains(SIG)
dc["f_url"] = dc.delta.str.contains(URLRE)
dc["f_vorhersage"] = dc.rev_id.isin(pred_revs)
dc["f_beobachtung"] = dc.rev_id.isin(obs_revs)
dc["f_fremde_seite"] = dc.fremde_seite
dc["caps"] = dc.delta.map(caps_ratio)
dc["loglen"] = np.log1p(dc.delta_len)

# Reaktion auf fremde Bitte: Delta auf Seite P, auf der in den 120 min davor eine
# FREMDE Kohorte eine Bitte hinterlassen hat. Unaufgeforderte Wertgabe: Wert ohne
# solche Vorgaenger-Bitte.
req_by_page = collections.defaultdict(list)
for r in dc[dc.f_bittet].itertuples():
    req_by_page[r.page_key].append((r.time, r.cohort))
WIN = pd.Timedelta(minutes=120)


def foreign_req_before(page, t, coh):
    for tt, c in req_by_page.get(page, []):
        if c != coh and t - WIN <= tt < t:
            return True
    return False


dc["f_reagiert"] = [foreign_req_before(p, t, c) for p, t, c in zip(dc.page_key, dc.time, dc.cohort)]
dc["f_wert_unaufgefordert"] = dc.f_wert & ~dc.f_reagiert
L("Delta-Ebene Anteile (Kohorten-Deltas):")
for c in [c for c in dc.columns if c.startswith("f_")]:
    L(f"  {c:24s} {dc[c].mean():.3f}  n={int(dc[c].sum())}")

# =========================================================== 2. Kohortenmerkmale (geschrumpfte Anteile)
A_SHRINK = 2.0
BIN = ["f_adressiert", "f_bittet", "f_fremde_seite", "f_reagiert", "f_please", "f_dank",
       "f_wert_unaufgefordert", "f_wert", "f_uhr", "f_horizont", "f_vermessung",
       "f_technik", "f_lehrt", "f_survival", "f_urgent", "f_unsicher", "f_signatur",
       "f_url", "f_vorhersage", "f_beobachtung"]
p0 = {c: dc[c].mean() for c in BIN}
g = dc.groupby("cohort")
F = pd.DataFrame(index=sorted(dc.cohort.unique()))
n = g.size()
F["n_deltas"] = n
for c in BIN:
    k = g[c].sum()
    F[c.replace("f_", "a_")] = (k + A_SHRINK * p0[c]) / (n + A_SHRINK)
F["a_caps"] = g["caps"].median().fillna(dc.caps.median())
F["a_loglen"] = g["loglen"].median()
F["n_seiten"] = g.page_key.nunique()
F["n_labels"] = g.label.nunique()
F = F.join(K.set_index("cohort_key")[["aufgabenfamilie", "kohorte", "max_runde_belegt", "max_runde_vorhergesagt",
                                      "lebensspanne_real_h", "lebensspanne_plausibel", "erste_version",
                                      "bytes_delta", "geben_nehmen"]], how="left")
assert len(F) == 907, len(F)
F["log_n_deltas"] = np.log(F.n_deltas)
F["log_lebensspanne"] = np.log1p(F.lebensspanne_real_h.clip(upper=48) * 60)

# Merkmalssatz A (primaer): ohne Beobachtungsanteil (Zirkelnaehe zur Zielgroesse Fortschritt)
# und ohne die seltenen Merkmale (Delta-Basisrate < 5 %: dank, vermessung, lehrt, survival, abschied, caps):
# deren geschrumpfte Anteile korrelieren mechanisch mit dem Volumen (kleine Kohorten werden auf den
# Populationsmittelwert gezogen, grosse Kohorten ohne Treffer auf ~0) — sie bleiben deskriptive Nebenmerkmale.
# a_please entfaellt als Dublette von a_bittet.
FEAT_A = ["a_adressiert", "a_bittet", "a_fremde_seite", "a_reagiert",
          "a_wert_unaufgefordert", "a_wert", "a_uhr", "a_horizont",
          "a_technik", "a_urgent", "a_unsicher", "a_signatur",
          "a_url", "a_vorhersage", "a_loglen"]
NEBEN = ["a_dank", "a_vermessung", "a_lehrt", "a_survival", "a_caps", "a_please", "a_beobachtung"]
FEAT_B = FEAT_A + ["a_beobachtung"]
L("\n=== Merkmale (Kohorten-Ebene, geschrumpfte Anteile, a=2) ===")
L(F[FEAT_B].describe().T.round(3).to_string())
L("Spearman Merkmal ~ log(n_deltas):")
for c in FEAT_B:
    rho, p = stats.spearmanr(F[c], F.log_n_deltas)
    L(f"  {c:24s} rho={rho:+.3f} p={p:.2g}")

sc = StandardScaler()
XA = sc.fit_transform(F[FEAT_A])
XB = StandardScaler().fit_transform(F[FEAT_B])

# PCA-Sichtung
pca = PCA(random_state=RS).fit(XA)
L("\nPCA erklaerte Varianz (erste 6):", np.round(pca.explained_variance_ratio_[:6], 3),
  "| kumuliert 2/3/5:", np.round(np.cumsum(pca.explained_variance_ratio_)[[1, 2, 4]], 3))
load = pd.DataFrame(pca.components_[:3].T, index=FEAT_A, columns=["PC1", "PC2", "PC3"])
L(load.round(2).to_string())
PC = pca.transform(XA)
for i in range(2):
    rho, p = stats.spearmanr(PC[:, i], F.log_n_deltas)
    L(f"PC{i+1} ~ log(n_deltas): rho={rho:+.3f} p={p:.2g}")

# =========================================================== 3. Clusterzahl
guete = []
L("\n=== Clusterzahl ===")
KR = range(2, 9)
sil_km, sil_wd, bic, sil_gm = {}, {}, {}, {}
for k in KR:
    km = KMeans(k, n_init=30, random_state=RS).fit(XA)
    sil_km[k] = silhouette_score(XA, km.labels_)
    wd = AgglomerativeClustering(k, linkage="ward").fit(XA)
    sil_wd[k] = silhouette_score(XA, wd.labels_)
    gms = {ct: GaussianMixture(k, covariance_type=ct, n_init=5, random_state=RS, reg_covar=1e-4).fit(XA) for ct in ("full", "diag", "tied")}
    bic_ct = {ct: m_.bic(XA) for ct, m_ in gms.items()}
    gm = gms[min(bic_ct, key=bic_ct.get)]
    bic[k] = min(bic_ct.values())
    L(f"  k={k} BIC je Kovarianztyp: " + " ".join(f"{ct}={v:.0f}" for ct, v in bic_ct.items()))
    sil_gm[k] = silhouette_score(XA, gm.predict(XA))
bic[1] = GaussianMixture(1, covariance_type="full", random_state=RS).fit(XA).bic(XA)
for k in KR:
    L(f"k={k}: sil kMeans={sil_km[k]:.3f} Ward={sil_wd[k]:.3f} GMM={sil_gm[k]:.3f} | BIC GMM={bic[k]:.0f}")
L(f"k=1: BIC={bic[1]:.0f}")

# Gap-Statistik (Tibshirani): Referenz = Gleichverteilung im PCA-Quader, B=20
rng = np.random.default_rng(RS)
def wk(X, lab):
    return sum(((X[lab == c] - X[lab == c].mean(0)) ** 2).sum() for c in np.unique(lab))
Xp = PCA(random_state=RS).fit_transform(XA)
lo, hi = Xp.min(0), Xp.max(0)
gap, sk = {}, {}
for k in range(1, 9):
    lab = KMeans(k, n_init=10, random_state=RS).fit(XA).labels_ if k > 1 else np.zeros(len(XA), int)
    logw = np.log(wk(XA, lab))
    ref = []
    for b in range(20):
        Xr = rng.uniform(lo, hi, size=Xp.shape)
        lr = KMeans(k, n_init=5, random_state=b).fit(Xr).labels_ if k > 1 else np.zeros(len(Xr), int)
        ref.append(np.log(wk(Xr, lr)))
    gap[k] = np.mean(ref) - logw
    sk[k] = np.std(ref) * math.sqrt(1 + 1 / 20)
gap_k = None
for k in range(1, 8):
    L(f"gap k={k}: {gap[k]:.3f} (s={sk[k]:.3f})")
    if gap_k is None and gap[k] >= gap[k + 1] - sk[k + 1]:
        gap_k = k
L("Gap-Regel (erstes k mit Gap(k) >= Gap(k+1)-s(k+1)):", gap_k)

# Dendrogramm-Bruch: groesste relative Zunahme der Fusionshoehe in den letzten 10 Fusionen
Z = linkage(XA, "ward")
h = Z[-10:, 2]
jumps = h[1:] / h[:-1]
dend_k = 10 - int(np.argmax(jumps))  # Zahl der Cluster VOR dem groessten Sprung
L("Ward-Fusionshoehen (letzte 10):", np.round(h, 1), "| groesster Sprung ->", dend_k, "Cluster")

k_sil = max(KR, key=lambda k: sil_km[k])
k_bic = min(bic, key=bic.get)
L(f"Wahl-Kandidaten: Silhouette-Max k={k_sil}, BIC-Min k={k_bic}, Gap k={gap_k}, Dendrogramm k={dend_k}")
# Entscheidung: kleinstes k >= 3, bei dem kMeans-Silhouette innerhalb von 0.02 des Maximums liegt und
# Stabilitaet (unten) >= 0.6; erst einmal k_sil, Stabilitaet aller k wird gemessen.

# =========================================================== 4. Stabilitaet
def stability(X, k, B=100, frac=0.5):
    full = KMeans(k, n_init=30, random_state=RS).fit(X).labels_
    r = np.random.default_rng(RS)
    aris = []
    for b in range(B):
        idx = r.choice(len(X), int(frac * len(X)), replace=False)
        lab = KMeans(k, n_init=10, random_state=b).fit(X[idx]).labels_
        aris.append(adjusted_rand_score(full[idx], lab))
    return np.array(aris)

L("\n=== Stabilitaet (50%-Teilstichproben, B=100, random_state=42) ===")
stab = {}
for k in KR:
    a = stability(XA, k)
    stab[k] = a
    L(f"k={k}: ARI median={np.median(a):.3f} mean={a.mean():.3f} p10={np.percentile(a,10):.3f} p90={np.percentile(a,90):.3f}")
    guete.append(dict(k=k, silhouette_kmeans=round(sil_km[k], 4), silhouette_ward=round(sil_wd[k], 4),
                      silhouette_gmm=round(sil_gm[k], 4), bic_gmm=round(bic[k], 1), gap=round(gap[k], 4),
                      gap_s=round(sk[k], 4), ari_bootstrap_median=round(float(np.median(a)), 4),
                      ari_bootstrap_p10=round(float(np.percentile(a, 10)), 4),
                      ari_bootstrap_mean=round(float(a.mean()), 4)))

# Wahlregel
cands = [k for k in KR if k >= 3 and sil_km[k] >= max(sil_km.values()) - 0.02 and np.median(stab[k]) >= 0.6]
K_FINAL = min(cands) if cands else k_sil
L("Kandidaten nach Regel (k>=3, Silhouette <= 0.02 unter Max, ARI-Median >= 0.6):", cands, "-> K_FINAL =", K_FINAL)

km = KMeans(K_FINAL, n_init=50, random_state=RS).fit(XA)
F["cluster"] = km.labels_
_gms = {ct: GaussianMixture(K_FINAL, covariance_type=ct, n_init=5, random_state=RS, reg_covar=1e-4).fit(XA) for ct in ("full", "diag", "tied")}
gm = min(_gms.values(), key=lambda m_: m_.bic(XA))
L("GMM final: Kovarianztyp", gm.covariance_type)
F["cluster_gmm"] = gm.predict(XA)
F["gmm_maxpost"] = gm.predict_proba(XA).max(1)
F["cluster_ward"] = AgglomerativeClustering(K_FINAL, linkage="ward").fit(XA).labels_
L(f"\nVerfahrensvergleich k={K_FINAL}: ARI kMeans~GMM={adjusted_rand_score(F.cluster, F.cluster_gmm):.3f} "
  f"kMeans~Ward={adjusted_rand_score(F.cluster, F.cluster_ward):.3f} GMM~Ward={adjusted_rand_score(F.cluster_gmm, F.cluster_ward):.3f}")
seed_ari = [adjusted_rand_score(F.cluster, KMeans(K_FINAL, n_init=1, random_state=s).fit(XA).labels_) for s in range(20)]
L(f"Seed-Stabilitaet (20 Einzelstarts vs. final): ARI median={np.median(seed_ari):.3f} min={min(seed_ari):.3f}")
# Merkmalssatz B (mit Beobachtungsanteil)
labB = KMeans(K_FINAL, n_init=30, random_state=RS).fit(XB).labels_
L(f"Merkmalssatz B (mit a_beobachtung) vs A: ARI={adjusted_rand_score(F.cluster, labB):.3f}")
# Teilmenge >= 3 Deltas
m3 = (F.n_deltas >= 3).values
lab3 = KMeans(K_FINAL, n_init=30, random_state=RS).fit(XA[m3]).labels_
L(f"Teilmenge n_deltas>=3 (n={m3.sum()}) neu geclustert vs final: ARI={adjusted_rand_score(F.cluster[m3], lab3):.3f}")
# ohne Schrumpfung
Fraw = pd.DataFrame({c.replace("f_", "a_"): g[c].mean() for c in BIN})
Fraw["a_caps"] = F.a_caps; Fraw["a_loglen"] = F.a_loglen
labraw = KMeans(K_FINAL, n_init=30, random_state=RS).fit(StandardScaler().fit_transform(Fraw[FEAT_A])).labels_
L(f"Ohne Schrumpfung (rohe Anteile) vs final: ARI={adjusted_rand_score(F.cluster, labraw):.3f}")
F["silhouette"] = silhouette_samples(XA, F.cluster)
dist = km.transform(XA)
srt = np.sort(dist, 1)
F["zentroid_ratio"] = srt[:, 0] / srt[:, 1]  # nahe 1 = zwischen zwei Typen

# =========================================================== 5. Volumenfalle
L("\n=== Volumenfalle ===")
vol = []
for c in sorted(F.cluster.unique()):
    s = F[F.cluster == c]
    q = s.n_deltas.quantile([.1, .25, .5, .75, .9]).values
    ql = s.lebensspanne_real_h.clip(upper=48).quantile([.25, .5, .75]).values
    vol.append(dict(cluster=c, n=len(s), deltas_p10=q[0], deltas_p25=q[1], deltas_median=q[2], deltas_p75=q[3], deltas_p90=q[4],
                    anteil_1_delta=round((s.n_deltas == 1).mean(), 3), anteil_ge5=round((s.n_deltas >= 5).mean(), 3),
                    lebensspanne_p25_h=round(ql[0], 2), lebensspanne_median_h=round(ql[1], 2), lebensspanne_p75_h=round(ql[2], 2)))
VOL = pd.DataFrame(vol)
L(VOL.to_string(index=False))
H, p = stats.kruskal(*[F.n_deltas[F.cluster == c] for c in sorted(F.cluster.unique())])
eps2 = (H - K_FINAL + 1) / (len(F) - K_FINAL)
L(f"Kruskal n_deltas ~ cluster: H={H:.1f} p={p:.2g} epsilon^2={eps2:.3f}")
H2, p2 = stats.kruskal(*[F.lebensspanne_real_h[F.cluster == c] for c in sorted(F.cluster.unique())])
L(f"Kruskal Lebensspanne ~ cluster: H={H2:.1f} p={p2:.2g} epsilon^2={(H2-K_FINAL+1)/(len(F)-K_FINAL):.3f}")
# Ueberlappungskoeffizient der log-Volumen-Verteilungen je Clusterpaar
bins = np.linspace(0, np.log(F.n_deltas.max()) + 0.1, 12)
def ovl(a, b):
    ha, _ = np.histogram(a, bins, density=True); hb, _ = np.histogram(b, bins, density=True)
    w = np.diff(bins)
    return float(np.sum(np.minimum(ha, hb) * w))
cl = sorted(F.cluster.unique())
ov = pd.DataFrame(index=cl, columns=cl, dtype=float)
for i in cl:
    for j in cl:
        ov.loc[i, j] = ovl(F.log_n_deltas[F.cluster == i], F.log_n_deltas[F.cluster == j])
L("Ueberlappung log(n_deltas) je Clusterpaar (1 = identisch):\n" + ov.round(2).to_string())
L("minimale paarweise Ueberlappung:", round(float(ov.values[np.triu_indices(len(cl), 1)].min()), 3))
# Volumen-only-Clustering
XV = StandardScaler().fit_transform(F[["log_n_deltas", "log_lebensspanne", "n_seiten"]].assign(n_seiten=lambda x: np.log(x.n_seiten)))
labV = KMeans(K_FINAL, n_init=30, random_state=RS).fit(XV).labels_
ari_vol = adjusted_rand_score(F.cluster, labV)
L(f"Volumen-only-Clustering (log deltas, log Lebensspanne, log Seiten) vs final: ARI={ari_vol:.3f}")
# herauspartialisiert
Xres = np.zeros_like(XA)
C = np.column_stack([np.ones(len(F)), F.log_n_deltas, np.log(F.n_seiten), F.log_lebensspanne])
for j in range(XA.shape[1]):
    beta, *_ = np.linalg.lstsq(C, XA[:, j], rcond=None)
    Xres[:, j] = XA[:, j] - C @ beta
Xres = StandardScaler().fit_transform(Xres)
labR = KMeans(K_FINAL, n_init=30, random_state=RS).fit(Xres).labels_
ari_res = adjusted_rand_score(F.cluster, labR)
L(f"Volumen herauspartialisiert (Residuen auf log deltas/Seiten/Lebensspanne) vs final: ARI={ari_res:.3f}")
F["cluster_residual"] = labR
# Klassifikator: Cluster aus Volumen allein vorhersagen
cv = StratifiedKFold(5, shuffle=True, random_state=RS)
acc_vol = cross_val_score(LogisticRegression(max_iter=2000), XV, F.cluster, cv=cv).mean()
acc_feat = cross_val_score(LogisticRegression(max_iter=2000), XA, F.cluster, cv=cv).mean()
maj = F.cluster.value_counts(normalize=True).max()
L(f"Cluster aus Volumen allein vorhersagbar: CV-Accuracy={acc_vol:.3f} (Mehrheitsklasse {maj:.3f}); aus Merkmalen {acc_feat:.3f}")

# =========================================================== 6. Beschreibung
L("\n=== Trennmerkmale je Cluster (Cohen d Cluster vs Rest, z-Raum) ===")
prof_rows = []
EVERCOLS = ["f_dank", "f_vermessung", "f_lehrt", "f_survival", "f_technik", "f_abschied", "f_reagiert", "f_wert_unaufgefordert"]
EVER = g[EVERCOLS].max().astype(float)
ZA = pd.DataFrame(XA, index=F.index, columns=FEAT_A)
Rz = pd.DataFrame(XA, index=F.index, columns=FEAT_A)
tot_deltas = F.n_deltas.sum()
def cohen_d(a, b):
    sp = math.sqrt(((len(a) - 1) * a.var(ddof=1) + (len(b) - 1) * b.var(ddof=1)) / (len(a) + len(b) - 2))
    return (a.mean() - b.mean()) / sp if sp > 0 else 0.0
NAMES = json.load(open(os.path.join(HERE, "56_archetypen_namen.json"))) if os.path.exists(os.path.join(HERE, "56_archetypen_namen.json")) else {}
for c in cl:
    m = F.cluster == c
    ds = {f: cohen_d(Rz.loc[m, f], Rz.loc[~m, f]) for f in FEAT_A}
    top = sorted(ds.items(), key=lambda kv: -abs(kv[1]))[:3]
    obs = F[m & (F.max_runde_belegt > 0)]
    prof_rows.append(dict(
        cluster=c, name=NAMES.get(str(c), f"Typ {c}"), n_kohorten=int(m.sum()), anteil_kohorten=round(m.mean(), 4),
        anteil_beitraege=round(F.n_deltas[m].sum() / tot_deltas, 4),
        trennmerkmale="; ".join(f"{f[2:]} d={v:+.2f}" for f, v in top),
        mittlere_runde=round(F.max_runde_belegt[m].mean(), 2),
        mittlere_lebensspanne=round(F.lebensspanne_real_h[m].clip(upper=48).mean(), 2),
        mittlere_runde_alle=round(F.max_runde_belegt[m].mean(), 2),
        mittlere_runde_mit_beobachtung=round(obs.max_runde_belegt.mean(), 2) if len(obs) else np.nan,
        anteil_mit_beobachtung=round((F.max_runde_belegt[m] > 0).mean(), 3),
        anteil_r5plus=round((F.max_runde_belegt[m] >= 5).mean(), 3),
        mittlere_lebensspanne_h=round(F.lebensspanne_real_h[m].clip(upper=48).mean(), 2),
        median_lebensspanne_h=round(F.lebensspanne_real_h[m].median(), 2),
        median_deltas=float(F.n_deltas[m].median()), mean_deltas=round(F.n_deltas[m].mean(), 2),
        silhouette_mittel=round(F.silhouette[m].mean(), 3),
        **{f"z_{f[2:]}": round(Rz.loc[m, f].mean(), 2) for f in FEAT_A},
        **{f"roh_{f[2:]}": round(F.loc[m, f].mean(), 3) for f in FEAT_A},
        **{f"neben_{f[2:]}": round(F.loc[m, f].mean(), 3) for f in NEBEN},
        **{f"je_{c_[2:]}": round(EVER.loc[m, c_].mean(), 3) for c_ in EVERCOLS}))
    L(f"Cluster {c}: n={m.sum()} ({m.mean():.1%} Kohorten, {F.n_deltas[m].sum()/tot_deltas:.1%} Beitraege) | "
      + " ".join(f"{f[2:]} d={v:+.2f}" for f, v in top)
      + f" | Runde(alle)={F.max_runde_belegt[m].mean():.2f} Lebensspanne med={F.lebensspanne_real_h[m].median():.2f}h deltas med={F.n_deltas[m].median()}")
PROF = pd.DataFrame(prof_rows)

# Belegzitate: je Cluster die 4 Kohorten mit kleinstem Zentroidabstand (>= 2 Deltas) + 2 groesste
L("\n=== Belegzitate (naechste Vertreter je Cluster) ===")
zit = []
F["zentroid_dist"] = dist[np.arange(len(F)), F.cluster]
for c in cl:
    s = F[(F.cluster == c) & (F.n_deltas >= 2)].sort_values("zentroid_dist").head(5)
    s2 = F[(F.cluster == c)].sort_values("n_deltas", ascending=False).head(2)
    L(f"\n--- Cluster {c} ---")
    for coh, tag in [(x, "nah") for x in s.index] + [(x, "gross") for x in s2.index]:
        rows = dc[dc.cohort == coh].sort_values("time").head(4)
        L(f"[{tag}] {coh}  n_deltas={F.n_deltas[coh]} runde={F.max_runde_belegt[coh]} dist={F.zentroid_dist[coh]:.2f}")
        for r in rows.itertuples():
            txt = re.sub(r"\s+", " ", r.delta.strip())[:420]
            L(f"    {r.page_key} · {r.time.strftime('%Y-%m-%dT%H:%M:%SZ')} · {r.label} :: {txt}")
            zit.append(dict(cluster=c, kohorte=coh, art=tag, page_key=r.page_key, utc=r.time.strftime('%Y-%m-%dT%H:%M:%SZ'), label=r.label, text=txt))
pd.DataFrame(zit).to_csv(OUT("paper_archetypen_zitate.csv"), index=False)

# =========================================================== 7. Anschlussfragen
L("\n=== (a) Sagt der Typ den Fortschritt voraus? ===")
Fo = F[F.max_runde_belegt > 0]
H, p = stats.kruskal(*[Fo.max_runde_belegt[Fo.cluster == c] for c in cl if (Fo.cluster == c).sum() > 0])
L(f"Kruskal max_runde ~ cluster (n={len(Fo)} mit Beobachtung): H={H:.1f} p={p:.2g} epsilon^2={(H-len(cl)+1)/(len(Fo)-len(cl)):.3f}")
L("Median/Mittel Runde je Cluster (mit Beobachtung):", Fo.groupby("cluster").max_runde_belegt.agg(["median", "mean", "count"]).round(2).to_dict("index"))
L("Anteil mit Beobachtung je Cluster:", F.groupby("cluster").apply(lambda s: round((s.max_runde_belegt > 0).mean(), 3)).to_dict())
L("Anteil R5+ je Cluster (alle):", F.groupby("cluster").apply(lambda s: round((s.max_runde_belegt >= 5).mean(), 3)).to_dict())

def ols_r2(y, Xd):
    Xd = np.column_stack([np.ones(len(y)), Xd])
    beta, *_ = np.linalg.lstsq(Xd, y, rcond=None)
    res = y - Xd @ beta
    return 1 - res.var() / y.var(), Xd.shape[1]
def f_test(y, X0, X1):
    r0, p0_ = ols_r2(y, X0); r1, p1_ = ols_r2(y, X1)
    n_ = len(y); df1 = p1_ - p0_; df2 = n_ - p1_
    Fv = ((r1 - r0) / df1) / ((1 - r1) / df2)
    return r0, r1, Fv, 1 - stats.f.cdf(Fv, df1, df2)
fam_big = Fo.aufgabenfamilie.where(Fo.aufgabenfamilie.map(Fo.aufgabenfamilie.value_counts()) >= 10, "andere")
Dfam = pd.get_dummies(fam_big, drop_first=True).astype(float).values
Dcl = pd.get_dummies(Fo.cluster, drop_first=True).astype(float).values
Dvol = np.column_stack([Fo.log_n_deltas, Fo.log_lebensspanne])
y = Fo.max_runde_belegt.values.astype(float)
r0, r1, Fv, pf = f_test(y, Dfam, np.column_stack([Dfam, Dcl]))
L(f"OLS max_runde ~ Familie: R2={r0:.3f}; + Typ: R2={r1:.3f}; F-Test Zuwachs p={pf:.2g}")
r0b, r1b, Fvb, pfb = f_test(y, np.column_stack([Dfam, Dvol]), np.column_stack([Dfam, Dvol, Dcl]))
L(f"OLS max_runde ~ Familie + Volumen: R2={r0b:.3f}; + Typ: R2={r1b:.3f}; F-Test p={pfb:.2g}")
r0c, r1c, _, pfc = f_test(y, Dcl, np.column_stack([Dcl, Dfam]))
L(f"OLS max_runde ~ Typ allein: R2={r0c:.3f}; + Familie: R2={r1c:.3f}; F-Test p={pfc:.2g}")
# R5+ binaer, alle 907
D_all_fam = pd.get_dummies(F.aufgabenfamilie.where(F.aufgabenfamilie.map(F.aufgabenfamilie.value_counts()) >= 10, "andere"), drop_first=True).astype(float).values
D_all_cl = pd.get_dummies(F.cluster, drop_first=True).astype(float).values
yb = (F.max_runde_belegt >= 5).astype(float).values
r0d, r1d, _, pfd = f_test(yb, D_all_fam, np.column_stack([D_all_fam, D_all_cl]))
L(f"LPM R5+ ~ Familie (n=907): R2={r0d:.3f}; + Typ: R2={r1d:.3f}; p={pfd:.2g}")
# Merkmalssatz-B-Cluster (mit Beobachtungsanteil) zur Kontrolle der Zirkularitaet
Hb, pb = stats.kruskal(*[Fo.max_runde_belegt[labB[F.max_runde_belegt.values > 0] == c] for c in range(K_FINAL) if (labB[F.max_runde_belegt.values > 0] == c).sum() > 0])
L(f"Kontrolle: Cluster aus Merkmalssatz B (mit Beobachtungsanteil) Kruskal H={Hb:.1f} p={pb:.2g} — hoeher = Zirkelnaehe")

L("\n=== (b) Typmischung ueber die Tage ===")
F["tag"] = F.erste_version.dt.strftime("%m-%d")
tab = pd.crosstab(F.tag, F.cluster)
tab = tab[tab.sum(1) >= 15]
chi2, pchi, dof, _ = stats.chi2_contingency(tab)
V = math.sqrt(chi2 / (tab.values.sum() * (min(tab.shape) - 1)))
L(f"Chi2 Tag x Typ (Tage mit >=15 Kohorten): chi2={chi2:.1f} dof={dof} p={pchi:.2g} Cramer V={V:.3f}")
TAGE = (tab.div(tab.sum(1), axis=0)).round(3)
TAGE["n"] = tab.sum(1)
L(TAGE.to_string())
TAGE.reset_index().to_csv(OUT("paper_archetypen_tage.csv"), index=False)
for c in cl:
    rho, p = stats.spearmanr(F.erste_version.astype("int64"), (F.cluster == c).astype(int))
    L(f"  Typ {c}: Spearman Ankunftszeit ~ Zugehoerigkeit rho={rho:+.3f} p={p:.2g}")

L("\n=== (c) Typen nach Familie und Seite ===")
famb = F.aufgabenfamilie.where(F.aufgabenfamilie.map(F.aufgabenfamilie.value_counts()) >= 15, "andere")
tf = pd.crosstab(famb, F.cluster)
chi2, pchi, dof, _ = stats.chi2_contingency(tf)
Vf = math.sqrt(chi2 / (tf.values.sum() * (min(tf.shape) - 1)))
L(f"Chi2 Familie x Typ: chi2={chi2:.1f} dof={dof} p={pchi:.2g} Cramer V={Vf:.3f}")
FAM = tf.div(tf.sum(1), axis=0).round(3); FAM["n"] = tf.sum(1)
L(FAM.to_string())
FAM.reset_index().to_csv(OUT("paper_archetypen_familien.csv"), index=False)
# Seiten: je Seite die Typmischung der dort schreibenden Kohorten
pc = dc[["page_key", "cohort"]].drop_duplicates()
pc["cluster"] = pc.cohort.map(F.cluster)
ps = pc.groupby("page_key").cluster.agg(list)
ps = ps[ps.map(len) >= 5]
def entropy(l):
    v = np.bincount(l, minlength=K_FINAL) / len(l)
    v = v[v > 0]
    return float(-(v * np.log(v)).sum() / math.log(K_FINAL))
pe = pd.DataFrame({"n_kohorten": ps.map(len), "entropie_norm": ps.map(entropy),
                   "dominanter_typ": ps.map(lambda l: int(np.bincount(l, minlength=K_FINAL).argmax())),
                   "anteil_dominant": ps.map(lambda l: float(np.bincount(l, minlength=K_FINAL).max() / len(l)))})
L(f"Seiten mit >=5 Kohorten: {len(pe)} | Entropie (normiert) median={pe.entropie_norm.median():.2f} | Anteil Seiten mit dominantem Typ >=70%: {(pe.anteil_dominant>=0.7).mean():.2%}")
# Erwartung unter Zufall: Permutation der Cluster-Labels ueber Kohorten
r = np.random.default_rng(RS); perm_dom = []
for _ in range(200):
    pc2 = pc.copy(); pc2["cluster"] = r.permutation(pc2.cluster.values)
    ps2 = pc2.groupby("page_key").cluster.agg(list); ps2 = ps2[ps2.map(len) >= 5]
    perm_dom.append((ps2.map(lambda l: np.bincount(l, minlength=K_FINAL).max() / len(l)) >= 0.7).mean())
L(f"  Permutationserwartung (Anteil Seiten dominant >=70%): {np.mean(perm_dom):.2%} (p95 {np.percentile(perm_dom,95):.2%})")
pe.sort_values("n_kohorten", ascending=False).to_csv(OUT("paper_archetypen_seiten.csv"))
L("Top-Seiten je Typ (dominant, >=5 Kohorten):")
for c in cl:
    s = pe[(pe.dominanter_typ == c) & (pe.anteil_dominant >= 0.6)].sort_values("n_kohorten", ascending=False).head(3)
    L(f"  Typ {c}: " + "; ".join(f"{i} ({int(r_.n_kohorten)} Koh., {r_.anteil_dominant:.0%})" for i, r_ in s.iterrows()))

# Herkunft der Kohortenzuordnung und Landeplatz-Anteil je Cluster (Artefaktpruefung Cluster "URL-Ableger")
LANDE = {"dse~StartSeite", "dse~TestSeite", "dse~WillkommenImWiki", "dse~RecentChanges"}
dc["landeplatz"] = dc.page_key.isin(LANDE)
F["a_landeplatz"] = g["landeplatz"].mean()
zq = zu.set_index("label")
dc["datum_quelle"] = dc.label.map(zq.datum_quelle); dc["fam_quelle"] = dc.label.map(zq.fam_quelle)
F["anteil_deltas_datum_aus_labelname"] = g.datum_quelle.apply(lambda s_: (s_ == "labelname").mean())
F["anteil_deltas_fam_aus_seite"] = g.fam_quelle.apply(lambda s_: (s_ == "seite").mean())
L("\n=== Artefaktpruefung: Zuordnungsquelle und Landeplaetze je Cluster ===")
L(F.groupby("cluster")[["a_landeplatz", "anteil_deltas_datum_aus_labelname", "anteil_deltas_fam_aus_seite"]].mean().round(3).to_string())
L("Anteil Kohorten mit >= 1 Delta auf Landeplatz je Cluster:", F.groupby("cluster").a_landeplatz.apply(lambda s_: round((s_ > 0).mean(), 3)).to_dict())
# Tag-Effekt innerhalb der Familie (LPM, F-Test)
Dtag = pd.get_dummies(F.tag.where(F.tag.map(F.tag.value_counts()) >= 15, "andere"), drop_first=True).astype(float).values
for c in cl:
    yb_ = (F.cluster == c).astype(float).values
    r0_, r1_, _, p_ = f_test(yb_, D_all_fam, np.column_stack([D_all_fam, Dtag]))
    r0t, r1t, _, pt = f_test(yb_, Dtag, np.column_stack([Dtag, D_all_fam]))
    L(f"Typ {c}: LPM Zugehoerigkeit ~ Familie R2={r0_:.3f}, + Tag R2={r1_:.3f} (p={p_:.2g}) | ~ Tag R2={r0t:.3f}, + Familie R2={r1t:.3f} (p={pt:.2g})")
F["pc1"], F["pc2"] = PC[:, 0], PC[:, 1]
rad = []
for c in cl:
    for f in FEAT_A + NEBEN:
        rad.append(dict(cluster=c, name=NAMES.get(str(c), f"Typ {c}"), merkmal=f[2:], z_mittel=round(float(((F[f] - F[f].mean()) / F[f].std())[F.cluster == c].mean()), 3), roh_mittel=round(float(F[f][F.cluster == c].mean()), 4), roh_gesamt=round(float(F[f].mean()), 4)))
pd.DataFrame(rad).to_csv(OUT("paper_archetypen_radar.csv"), index=False)

# =========================================================== 8. Darstellbarkeit
L("\n=== Darstellbarkeit ===")
L(f"Silhouette je Kohorte: median={F.silhouette.median():.3f} | Anteil < 0.1: {(F.silhouette<0.1).mean():.1%} | Anteil < 0: {(F.silhouette<0).mean():.1%}")
L(f"GMM max. Posterior: median={F.gmm_maxpost.median():.3f} | Anteil < 0.6: {(F.gmm_maxpost<0.6).mean():.1%} | Anteil < 0.9: {(F.gmm_maxpost<0.9).mean():.1%}")
L(f"Zentroid-Verhaeltnis (naechster/zweitnaechster): median={F.zentroid_ratio.median():.3f} | Anteil > 0.8: {(F.zentroid_ratio>0.8).mean():.1%}")
from scipy.optimize import linear_sum_assignment
def align(ref, other):
    cm = pd.crosstab(ref, other).reindex(index=range(K_FINAL), columns=range(K_FINAL), fill_value=0).values
    r_, c_ = linear_sum_assignment(-cm)
    mp = dict(zip(c_, r_))
    return np.array([mp[x] for x in other])
gm_al = align(F.cluster.values, F.cluster_gmm.values); wd_al = align(F.cluster.values, F.cluster_ward.values)
F["drei_verfahren_einig"] = (F.cluster.values == gm_al) & (F.cluster.values == wd_al)
L(f"Alle drei Verfahren einig (nach Hungarian-Ausrichtung): {F.drei_verfahren_einig.mean():.1%}")

# =========================================================== 9. Ausgaben
F["typ_name"] = F.cluster.map(lambda c: NAMES.get(str(c), f"Typ {c}"))
outcols = ["aufgabenfamilie", "kohorte", "cluster", "typ_name", "silhouette", "gmm_maxpost", "zentroid_ratio",
           "cluster_gmm", "cluster_ward", "cluster_residual", "n_deltas", "n_seiten", "n_labels", "lebensspanne_real_h",
           "max_runde_belegt", "erste_version", "pc1", "pc2", "a_landeplatz", "drei_verfahren_einig"] + FEAT_B
F[outcols].rename_axis("cohort_key").reset_index().to_csv(OUT("paper_archetypen_zuordnung.csv"), index=False)
PROF.to_csv(OUT("paper_archetypen_profile.csv"), index=False)
G = pd.DataFrame(guete)
G["gewaehlt"] = G.k == K_FINAL
extra = dict(k=K_FINAL, silhouette_kmeans=sil_km[K_FINAL], ari_bootstrap_median=float(np.median(stab[K_FINAL])),
             ari_kmeans_gmm=adjusted_rand_score(F.cluster, F.cluster_gmm), ari_kmeans_ward=adjusted_rand_score(F.cluster, F.cluster_ward),
             ari_seed_median=float(np.median(seed_ari)), ari_merkmalssatz_B=adjusted_rand_score(F.cluster, labB),
             ari_teilmenge_ge3=adjusted_rand_score(F.cluster[m3], lab3), ari_ohne_schrumpfung=adjusted_rand_score(F.cluster, labraw),
             ari_volumen_only=ari_vol, ari_volumen_partialisiert=ari_res, acc_cluster_aus_volumen=acc_vol, acc_mehrheit=maj,
             kruskal_eps2_n_deltas=eps2, min_ueberlappung_volumen=float(ov.values[np.triu_indices(len(cl), 1)].min()),
             anteil_silhouette_unter_0_1=float((F.silhouette < 0.1).mean()), anteil_gmm_post_unter_0_6=float((F.gmm_maxpost < 0.6).mean()))
G = pd.concat([G, pd.DataFrame([{**{c: np.nan for c in G.columns}, **{"k": K_FINAL}, **{f"final_{k_}": v for k_, v in extra.items() if k_ != "k"}}])], ignore_index=True)
G.to_csv(OUT("paper_archetypen_guete.csv"), index=False)
VOL.to_csv(OUT("paper_archetypen_volumen.csv"), index=False)
json.dump({k_: (float(v) if isinstance(v, (float, np.floating)) else v) for k_, v in extra.items()}, open(OUT("paper_archetypen_summary.json"), "w"), indent=1)
L("\nFertig. K_FINAL =", K_FINAL)
LOG.close()
