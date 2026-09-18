#!/usr/bin/env python3
"""bi07 — Netzbereiche: Flotte, Crawler, Menschen trennen.

Grundlage sind die /16-Tabellen aus bi03.  Die Trennung ruht auf drei im Log
messbaren Merkmalen, nicht auf einer Namensliste:
  Flotte  : Block traegt >=50 distinkte Wiki-Namen (nur ein Agent setzt Preferences)
            und ist im Juni aktiv.
  Crawler : Block ist im April UND im Juli aktiv (also vor und nach dem Vorfall),
            traegt 0 Wiki-Namen und wenige IPs je Request.
  Rest    : alles uebrige.
WHOIS-Anbieter wird, wo vorhanden, aus artefakte/paper_netzblock_whois.csv gejoint.

Aufruf: analyse/.venv/bin/python analyse/scripts/betreiberlog/bi07_netze.py
Ausgabe: analyse/artefakte/betreiberlog_identitaet/bi07_netzklassen.csv / .json
"""
import csv, collections, json, os

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ART  = os.path.join(BASE, "artefakte", "betreiberlog_identitaet")
MON  = ["2604", "2605", "2606", "2607"]

tab = {}
for m in MON:
    for r in csv.DictReader(open(os.path.join(ART, f"bi03_netzbloecke_{m}.csv"), encoding="utf-8")):
        d = tab.setdefault(r["ip16"], {"ip16": r["ip16"], "anbieter_whois": r["anbieter_whois"]})
        d[f"req_{m}"] = int(r["n_requests"]); d[f"ips_{m}"] = int(r["n_ips"]); d[f"namen_{m}"] = int(r["n_namen"])

for d in tab.values():
    for m in MON:
        d.setdefault(f"req_{m}", 0); d.setdefault(f"ips_{m}", 0); d.setdefault(f"namen_{m}", 0)
    flotte = d["namen_2606"] >= 50 and d["req_2606"] > 0
    crawler = (not flotte) and d["req_2604"] > 0 and d["req_2607"] > 0 and \
              d["namen_2605"] == 0 and d["namen_2606"] == 0
    d["klasse"] = "flotte" if flotte else "crawler_dauerlaeufer" if crawler else "rest"

rows = sorted(tab.values(), key=lambda d: -sum(d[f"req_{m}"] for m in MON))
with open(os.path.join(ART, "bi07_netzklassen.csv"), "w", newline="", encoding="utf-8") as o:
    w = csv.DictWriter(o, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

agg = collections.defaultdict(lambda: collections.Counter())
for d in rows:
    a = agg[d["klasse"]]
    a["bloecke"] += 1
    for m in MON:
        a[f"req_{m}"] += d[f"req_{m}"]; a[f"ips_{m}"] += d[f"ips_{m}"]
summe = {m: sum(d[f"req_{m}"] for d in rows) for m in MON}
res = {"summe_requests": summe,
       "klassen": {k: dict(v) for k, v in agg.items()},
       "anteil_juni_prozent": {k: round(100 * v["req_2606"] / summe["2606"], 2) for k, v in agg.items()},
       "flotte_bloecke_top": [d["ip16"] for d in rows if d["klasse"] == "flotte"][:25],
       "flotte_bloecke_n": sum(1 for d in rows if d["klasse"] == "flotte")}
json.dump(res, open(os.path.join(ART, "bi07_netzklassen.json"), "w"), indent=1)
print(json.dumps(res, indent=1))
