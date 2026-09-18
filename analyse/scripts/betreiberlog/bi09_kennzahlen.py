#!/usr/bin/env python3
"""bi09 — Restliche Kennzahlen des Berichts, alle streamend.

Aufruf: analyse/.venv/bin/python analyse/scripts/betreiberlog/bi09_kennzahlen.py
Ausgabe: analyse/artefakte/betreiberlog_identitaet/bi09_kennzahlen.json
"""
import csv, collections, datetime as dt, gzip, json, os

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NORM = os.path.join(BASE, "data", "betreiberlogs", "normalisiert")
ART  = os.path.join(BASE, "artefakte", "betreiberlog_identitaet")

flotte16 = {r["ip16"] for r in csv.DictReader(open(os.path.join(ART, "bi07_netzklassen.csv"), encoding="utf-8"))
            if r["klasse"] == "flotte"}
res = {"flotte_bloecke": len(flotte16)}

for m in ["2605", "2606"]:
    kinds_f = collections.Counter(); benannt_f = 0; unbenannt_f = 0
    paare = set(); n_named = 0
    with gzip.open(os.path.join(NORM, f"bi_{m}.tsv.gz"), "rt", encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE):
            b = ".".join(r["ip"].split(".")[:2])
            if b in flotte16:
                kinds_f[r["kind"]] += 1
                if r["name"]: benannt_f += 1
                else: unbenannt_f += 1
            if r["name"] and r["namensquelle"] == "name":
                n_named += 1; paare.add((r["name"], r["ip"]))
    lesen = kinds_f["browse"] + kinds_f["raw"] + kinds_f["search"] + kinds_f["diff"] + kinds_f["rc"]
    res[m] = dict(flotte_requests=sum(kinds_f.values()), flotte_benannt=benannt_f,
                  flotte_unbenannt=unbenannt_f, flotte_lesen=lesen,
                  flotte_save=kinds_f["save"], flotte_editform=kinds_f["editform"],
                  flotte_other=kinds_f["other"],
                  lesen_je_save=round(lesen / max(kinds_f["save"], 1), 1),
                  benannte_requests=n_named, name_ip_paare=len(paare),
                  requests_je_name_ip_paar=round(n_named / max(len(paare), 1), 3))
    print(m, res[m], flush=True)

for k in ["2605", "2606"]:
    pass
json.dump(res, open(os.path.join(ART, "bi09_kennzahlen.json"), "w"), indent=1)
print(dt.datetime.fromtimestamp(1781646147, dt.UTC).isoformat(), "= Spitzenfenster Juni (bi06)")
print(dt.datetime.fromtimestamp(1779812769, dt.UTC).isoformat(), "= Spitzenfenster Mai (bi06)")
