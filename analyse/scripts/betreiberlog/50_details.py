#!/usr/bin/env python3
"""
50_details.py -- Restfragen: (b) Herkunft der Zahl 20995, (c) die 22 unsichtbaren
Seiten, (d) der eine probe-Schluessel ohne Familientreffer.
Aufruf: analyse/.venv/bin/python analyse/scripts/betreiberlog/50_details.py
"""
import json, collections, datetime as dt, urllib.parse
from pathlib import Path
import duckdb
BASE = Path(__file__).resolve().parents[3]
D = BASE / "analyse" / "data"; N = D / "betreiberlogs" / "normalisiert"
con = duckdb.connect(); con.execute("SET TimeZone='UTC'")
con.execute(f"CREATE VIEW r AS SELECT * FROM read_parquet('{N}/requests_26*.parquet')")
def show(t, rows, cols):
    print(f"\n### {t}\n| " + " | ".join(cols) + " |")
    print("|" + "|".join("---" for _ in cols) + "|")
    for x in rows: print("| " + " | ".join(str(v) for v in x) + " |")

lab = {json.loads(l)["label"]: json.loads(l) for l in open(D / "labels.jsonl")}
human = {k for k, v in lab.items() if v.get("is_human_handle")}
revs = [json.loads(l) for l in open(D / "revisions.jsonl")]
rh = sum(1 for x in revs if x.get("label") in human)
sr = sum(v.get("save_requests") or 0 for v in lab.values())
srh = sum(v.get("save_requests") or 0 for v in lab.values() if v.get("is_human_handle"))
show("(b) Rekonstruktion der Paper-Zahl 20995", [
    ["sum(save_requests) aller Labels", sr],
    ["davon Menschen-Handles", srh],
    ["Flotte", sr - srh],
    ["archivierte Revisionen gesamt", len(revs)],
    ["davon von Menschen-Handles", rh],
    ["davon von Flotten-Labels", len(revs) - rh],
    ["Flotten-Versuche minus Flotten-Revisionen", (sr - srh) - (len(revs) - rh)],
    ["Paper", 20995],
], ["groesse", "wert"])

ev = [json.loads(l) for l in open(D / "events.jsonl")]
held = {}
for e in ev:
    if e["event_type"] == "delete": held.setdefault(e["page_key"], e.get("page_held"))
names = [k.split("~", 1)[1] for k in sorted(k for k, v in held.items() if v is False)]
con.execute("CREATE TABLE gp(name VARCHAR)")
con.executemany("INSERT INTO gp VALUES (?)", [(x,) for x in names])
miss = [x[0] for x in con.execute(
    "SELECT g.name FROM gp g LEFT JOIN r q ON q.page_id=g.name GROUP BY 1 HAVING count(q.ts_utc)=0").fetchall()]
show("(c) Die %d Seiten ohne jeden Logtreffer (page_id exakt)" % len(miss),
     [[m, con.execute("SELECT count(*) FROM r WHERE lower(page_id)=lower(?)", [m]).fetchone()[0],
       con.execute("SELECT count(*) FROM r WHERE raw_params LIKE ?", ['%'+m+'%']).fetchone()[0]]
      for m in miss], ["seite", "treffer_case_insensitiv", "treffer_irgendwo_in_query"])

pr = [e for e in ev if e["event_type"] == "probe"]
def iso(s): return int(dt.datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc).timestamp())
PAT = ["<script", "</script", "<img src=x", "<iframe", "javascript:", "onerror=", "onmouseover=",
       "onclick=", "onfocus=", "onload=", "document.cookie", "document.title", "alert("]
fk = set()
for ts, ip, q in con.execute("SELECT ts_utc, ip, raw_params FROM r").fetchall():
    s = urllib.parse.unquote_plus(q).lower()
    if any(p in s for p in PAT): fk.add((ts, ".".join(ip.split(".")[:2])))
pk = {(iso(e["time"]), e["ip16"]) for e in pr}
show("(d) probe-Schluessel ohne Familientreffer",
     [[dt.datetime.fromtimestamp(t, dt.timezone.utc).isoformat(), i,
       con.execute("SELECT count(*) FROM r WHERE ts_utc=?", [t]).fetchone()[0]] for t, i in sorted(pk - fk)],
     ["zeit_utc", "ip16", "requests_in_dieser_sekunde"])
show("Schluesselstatistik", [["probe-Events", len(pr)], ["verschiedene (sek,ip16)", len(pk)],
                             ["davon mit Familientreffer", len(pk & fk)]], ["groesse", "wert"])
