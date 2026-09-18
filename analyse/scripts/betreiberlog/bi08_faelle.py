#!/usr/bin/env python3
"""bi08 — Die drei Identitaetsprobleme aus main.tex:434 gegen das Log gehalten.

  (1) generische Namen mit Lebensdauer bis 588 h  -> teilen sich mehrere Prozesse einen Namen?
  (2) OAI7C97Dec26 / Nov18 / Oct09 (ein Thread, drei Episoden)
  (3) 47 Namensfamilien / 327 Namen (Praefix + >=4 Ziffern), z. B. Sep13Watcher*

Entscheidender Test fuer (1): parallele Schreibvorgaenge unter EINEM Namen.
Zwei Speicher-Requests desselben Namens auf VERSCHIEDENE Seiten innerhalb von
<= dt Sekunden koennen nicht von einem sequentiell arbeitenden Prozess stammen.

Aufruf: analyse/.venv/bin/python analyse/scripts/betreiberlog/bi08_faelle.py
Ausgabe: analyse/artefakte/betreiberlog_identitaet/bi08_*.csv|json
"""
import csv, collections, gzip, json, os, re

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NORM = os.path.join(BASE, "data", "betreiberlogs", "normalisiert")
ART  = os.path.join(BASE, "artefakte", "betreiberlog_identitaet")
FAMILIE = re.compile(r"^(.*?)(\d{4,})$")          # Praefix + >=4 Ziffern (BERICHT_flottengroesse.md:126)

saves = []
for m in ["2605", "2606", "2607"]:
    p = os.path.join(NORM, f"bi_save_{m}.tsv.gz")
    if not os.path.exists(p): continue
    with gzip.open(p, "rt", encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE):
            r["ts"] = int(r["ts"]); saves.append(r)
saves.sort(key=lambda r: r["ts"])
print("Speicher-Requests gesamt:", len(saves))

# --- (1) Parallelitaet je Name -------------------------------------------------
pro_name = collections.defaultdict(list)
for r in saves:
    if r["name"]: pro_name[r["name"]].append(r)

zeilen = []
for n, rs in pro_name.items():
    rs.sort(key=lambda r: r["ts"])
    par = 0; bel = ""
    for i in range(1, len(rs)):
        for j in range(i - 1, -1, -1):
            if rs[i]["ts"] - rs[j]["ts"] > 2: break
            if rs[i]["page"] != rs[j]["page"] and rs[i]["rndstamp"] != rs[j]["rndstamp"]:
                par += 1
                if not bel:
                    bel = (f"{rs[j]['ts']} {rs[j]['page']} rnd={rs[j]['rndstamp']} || "
                           f"{rs[i]['ts']} {rs[i]['page']} rnd={rs[i]['rndstamp']}")
                break
    zeilen.append(dict(name=n, n_saves=len(rs), n_ips=len({r["ip"] for r in rs}),
                       n_seiten=len({r["page"] for r in rs}),
                       n_rndstamps=len({r["rndstamp"] for r in rs}),
                       spanne_h=round((rs[-1]["ts"] - rs[0]["ts"]) / 3600, 2),
                       parallel_paare_2s=par, beleg=bel))
zeilen.sort(key=lambda d: -d["parallel_paare_2s"])
with open(os.path.join(ART, "bi08_namen_parallelitaet.csv"), "w", newline="", encoding="utf-8") as o:
    w = csv.DictWriter(o, fieldnames=list(zeilen[0])); w.writeheader(); w.writerows(zeilen)
n_par = sum(1 for d in zeilen if d["parallel_paare_2s"] > 0)
print(f"Namen mit nachweislich parallelen Schreibvorgaengen (<=2 s, andere Seite, anderer rndstamp): "
      f"{n_par} von {len(zeilen)}")
for d in zeilen[:6]:
    print("   ", d["name"], d["n_saves"], "saves", d["parallel_paare_2s"], "Paare |", d["beleg"][:150])

# --- (2) Thread-Praefix-Faelle --------------------------------------------------
fall2 = {}
for pref in ["OAI7C97", "OpenAIThread42e0", "Thread42e0", "OAI4FFE"]:
    tr = [r for r in saves if r["name"].startswith(pref)]
    fall2[pref] = dict(n_saves=len(tr), namen=sorted({r["name"] for r in tr}),
                       ips=len({r["ip"] for r in tr}),
                       ip_ueberschneidung=len({r["ip"] for r in tr}) < len(tr),
                       rndstamps_geteilt=len(tr) - len({r["rndstamp"] for r in tr}),
                       zeitraum=[min((r["ts"] for r in tr), default=None),
                                 max((r["ts"] for r in tr), default=None)])
print(json.dumps(fall2, indent=1))

# --- (3) Namensfamilien ---------------------------------------------------------
fam = collections.defaultdict(set)
for n in pro_name:
    m = FAMILIE.match(n)
    if m and len(m.group(1)) >= 4: fam[m.group(1)].add(n)
gross = {k: sorted(v) for k, v in fam.items() if len(v) >= 3}
fam_ip = {}
for k, mitglieder in gross.items():
    ipsets = {n: {r["ip"] for r in pro_name[n]} for n in mitglieder}
    gemeinsam = 0
    ms = list(mitglieder)
    for i in range(len(ms)):
        for j in range(i + 1, len(ms)):
            if ipsets[ms[i]] & ipsets[ms[j]]: gemeinsam += 1
    fam_ip[k] = dict(n_mitglieder=len(mitglieder), paare_mit_gemeinsamer_ip=gemeinsam,
                     paare_gesamt=len(ms) * (len(ms) - 1) // 2)
res3 = dict(n_familien=len(gross), n_namen=sum(len(v) for v in gross.values()),
            familien_mit_ip_ueberschneidung=sum(1 for v in fam_ip.values() if v["paare_mit_gemeinsamer_ip"]),
            details={k: v for k, v in sorted(fam_ip.items(), key=lambda kv: -kv[1]["n_mitglieder"])[:15]})
print(json.dumps(res3, indent=1))
json.dump({"fall1_namen_mit_parallelitaet": n_par, "fall1_namen_gesamt": len(zeilen),
           "fall2": fall2, "fall3": res3},
          open(os.path.join(ART, "bi08_faelle.json"), "w"), indent=1)
