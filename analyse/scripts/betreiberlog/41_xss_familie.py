#!/usr/bin/env python3
"""
41_xss_familie.py -- Rekonstruktion der Export-Definition "narrow executable
script-injection family" und Quantifizierung des Wegfilterns.

Aufruf: analyse/.venv/bin/python analyse/scripts/betreiberlog/41_xss_familie.py

DETEKTOR (aus der Sichtung aller 101 publizierten probe-Events abgeleitet,
siehe normalisiert/probe_dump.txt): ein Request gehoert zur Familie, wenn die
url-dekodierte Query eines der folgenden Muster enthaelt (case-insensitiv):
  <script  </script  <img (tag)  <iframe  javascript:
  onerror=  onmouseover=  onclick=  onfocus=  onload=
  document.cookie  document.title  alert(
Der zusammengesetzte Scanner-String
  "... UNION ALL SELECT 1,NULL,'<script>alert(\"XSS\")</script>' ..."
faellt dadurch ebenfalls in die Familie -- genau so haelt es der Export.
"""
import json, csv, collections, datetime as dt, urllib.parse
from pathlib import Path
import duckdb

BASE = Path(__file__).resolve().parents[3]
D = BASE / "analyse" / "data"; N = D / "betreiberlogs" / "normalisiert"
con = duckdb.connect(); con.execute("SET TimeZone='UTC'")
con.execute(f"CREATE VIEW r AS SELECT * FROM read_parquet('{N}/requests_26*.parquet')")
PAT = ["<script", "</script", "<img ", "<iframe", "javascript:", "onerror=",
       "onmouseover=", "onclick=", "onfocus=", "onload=", "document.cookie",
       "document.title", "alert("]
def hit(q):
    s = urllib.parse.unquote_plus(q).lower()
    return any(p in s for p in PAT)

fam = []
for ts, ip, q, src, ad in con.execute(
        "SELECT ts_utc, ip, raw_params, src_file, action_detail FROM r").fetchall():
    if hit(q): fam.append((ts, ".".join(ip.split(".")[:2]), src, ad, q))
bym = collections.Counter(x[2] for x in fam)
ev = [json.loads(l) for l in open(D / "events.jsonl")]
pr = [e for e in ev if e["event_type"] == "probe"]
def iso(s): return int(dt.datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc).timestamp())
pk = {(iso(e["time"]), e["ip16"]) for e in pr}
fk = {(x[0], x[1]) for x in fam}
tot = con.execute("SELECT count(*) FROM r").fetchone()[0]
mj = con.execute("SELECT count(*) FROM r WHERE src_file IN ('log_2605','log_2606')").fetchone()[0]

def show(t, rows, cols):
    print(f"\n### {t}\n| " + " | ".join(cols) + " |")
    print("|" + "|".join("---" for _ in cols) + "|")
    for x in rows: print("| " + " | ".join(str(v) for v in x) + " |")

ex = sorted(k for k in fk if k not in pk and k[0] >= min(x[0] for x in fam if x[2] in ("log_2605","log_2606"))
            and any(x[2] in ("log_2605","log_2606") for x in fam if (x[0],x[1])==k))
show("Familientreffer in Mai/Juni, die der Export NICHT publiziert", [
    [dt.datetime.fromtimestamp(t, dt.timezone.utc).isoformat(), i,
     [x[4][:120] for x in fam if (x[0],x[1])==(t,i)][0]] for t,i in ex],
    ["zeit_utc","ip16","query"])
show("Skript-Injektionsfamilie im Betreiberlog", [
    ["Familie gesamt (Apr-Jul)", len(fam)],
    ["davon log_2605 (Mai)", bym["log_2605"]],
    ["davon log_2606 (Juni)", bym["log_2606"]],
    ["Mai+Juni zusammen", bym["log_2605"] + bym["log_2606"]],
    ["log_2604 (April, im Export nicht vorhanden)", bym["log_2604"]],
    ["log_2607 (Juli, im Export nicht vorhanden)", bym["log_2607"]],
    ["publizierte probe-Events", len(pr)],
    ["probe-Schluessel (sek,ip16), die die Familie trifft", len(pk & fk)],
    ["probe-Schluessel ohne Familientreffer", len(pk - fk)],
], ["groesse", "wert"])
show("Wie eng der Ausschnitt ist", [
    ["Requests im Betreiberlog gesamt", f"{tot:,}"],
    ["Requests Mai+Juni", f"{mj:,}"],
    ["publizierte Zugriffsereignisse (probe)", len(pr)],
    ["Anteil am Gesamtlog", f"{100*len(pr)/tot:.5f} %"],
    ["Anteil am Mai/Juni-Log", f"{100*len(pr)/mj:.5f} %"],
    ["Lesezugriffe im Log, im Export = 0", f"{con.execute(chr(83)+chr(69)+chr(76)+chr(69)+chr(67)+chr(84)+' count(*) FROM r WHERE action_kind=' + chr(39)+'read'+chr(39)).fetchone()[0]:,}"],
], ["groesse", "wert"])
with open(N / "xss_familie.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["ts_utc", "iso_utc", "ip16", "src_file", "action_detail", "query", "im_export"])
    for ts, ip16, src, ad, q in sorted(fam):
        w.writerow([ts, dt.datetime.fromtimestamp(ts, dt.timezone.utc).isoformat(), ip16, src, ad, q[:500],
                    (ts, ip16) in pk])
print("\nCSV:", N / "xss_familie.csv")
