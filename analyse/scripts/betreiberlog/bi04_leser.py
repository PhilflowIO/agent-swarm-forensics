#!/usr/bin/env python3
"""bi04 — Die Namen im Log gegen die Labels des Exports.

Beantwortet: warum traegt das Juni-Log mehr Wiki-Namen als der Export Labels kennt.
Zerlegt die Log-Namen in
  (a) im Export als Label bekannt,
  (b) im Log mit Speicher-Request, im Export unbekannt  (Schreibversuch nie archiviert),
  (c) im Log ohne jeden Speicher-Request                (reine Leser — im Export unsichtbar).

Namens- und Datumsdefinition uebernommen aus scripts/51_prozess.py:50-52 und :115
(MONDD_NAME = (Jan|Feb|...|Dec)(\\d{2})), damit die Kohortenzaehlung dieselbe bleibt.

Aufruf:
  analyse/.venv/bin/python analyse/scripts/betreiberlog/bi04_leser.py
Ausgabe: analyse/artefakte/betreiberlog_identitaet/bi04_*.csv|json
"""
import csv, collections, gzip, json, os, re

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NORM = os.path.join(BASE, "data", "betreiberlogs", "normalisiert")
ART  = os.path.join(BASE, "artefakte", "betreiberlog_identitaet")
os.makedirs(ART, exist_ok=True)

MON = "(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
MONDD_NAME = re.compile(rf"({MON})(\d{{2}})(?!\d)")          # 51_prozess.py:52
TAGE = {"Jan": 31, "Feb": 29, "Mar": 31, "Apr": 30, "May": 31, "Jun": 30,
        "Jul": 31, "Aug": 31, "Sep": 30, "Oct": 31, "Nov": 30, "Dec": 31}


def marker(name):                                             # 51_prozess.py:115
    return [m.group(1) + m.group(2) for m in MONDD_NAME.finditer(name or "")]


labels, labels_dse = set(), set()
for line in open(os.path.join(BASE, "data", "labels.jsonl"), encoding="utf-8"):
    r = json.loads(line)
    labels.add(r["label"])
    if "dse" in (r.get("wikis") or []):
        labels_dse.add(r["label"])

res = {}
for m in ["2604", "2605", "2606", "2607"]:
    kinds = collections.defaultdict(collections.Counter)
    with gzip.open(os.path.join(NORM, f"bi_{m}.tsv.gz"), "rt", encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE):
            if r["name"] and r["namensquelle"] == "name":
                kinds[r["name"]][r["kind"]] += 1
    namen = set(kinds)
    schreiber = {n for n in namen if kinds[n]["save"] or kinds[n]["editform"]}
    speicherer = {n for n in namen if kinds[n]["save"]}
    nur_leser = namen - schreiber
    bekannt = namen & labels
    with open(os.path.join(ART, f"bi04_namen_{m}.csv"), "w", newline="", encoding="utf-8") as o:
        w = csv.writer(o)
        w.writerow(["name", "n_requests", "n_save", "n_editform", "n_browse", "n_raw",
                    "n_search", "im_export", "im_export_dse", "klasse", "datumsmarker"])
        for n in sorted(namen):
            k = kinds[n]
            kl = ("bekannt" if n in labels else
                  "schreibversuch_unarchiviert" if n in schreiber else "nur_leser")
            w.writerow([n, sum(k.values()), k["save"], k["editform"], k["browse"], k["raw"],
                        k["search"], n in labels, n in labels_dse, kl, ";".join(marker(n))])
    # Sammelbild-Eingang: distinkte kalendergueltige (Monat,Tag)-Marken
    def marken(menge):
        s = set()
        for n in menge:
            for mk in marker(n):
                if int(mk[3:]) >= 1 and int(mk[3:]) <= TAGE[mk[:3]]:
                    s.add(mk)
        return s
    res[m] = dict(
        namen=len(namen), im_export=len(bekannt), nicht_im_export=len(namen - labels),
        mit_save=len(speicherer), mit_editform_ohne_save=len(schreiber - speicherer),
        nur_leser=len(nur_leser),
        nur_leser_nicht_im_export=len(nur_leser - labels),
        schreiber_nicht_im_export=len(schreiber - labels),
        marken_log=len(marken(namen)), marken_export_labels=len(marken(labels)),
        namen_mit_marke=sum(1 for n in namen if marker(n)),
    )
    print(m, res[m], flush=True)

json.dump(res, open(os.path.join(ART, "bi04_uebersicht.json"), "w"), indent=1)
