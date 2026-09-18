#!/usr/bin/env python3
"""
40_probes_filter.py -- Was der Export bei den 101 'probe'-Events weggefiltert hat.

Aufruf: analyse/.venv/bin/python analyse/scripts/betreiberlog/40_probes_filter.py
Ausgabe: stdout (Markdown) + normalisiert/probes.json, normalisiert/probe_matches.csv

DETEKTOR-FAMILIEN (auf der roh-URL-dekodierten Query, case-insensitiv):
  script  : '<script', 'javascript:', 'onerror=', 'onload=', 'onmouseover=',
            'alert(', '<svg', '<img', 'document.cookie', 'eval('
            -> "executable script injection" im Sinne der Export-Definition
  sqli    : 'union select', ' and 1=1', ' or 1=1', 'chr(', 'sleep(', 'benchmark(',
            'information_schema', 'waitfor delay', 'pg_sleep', '--' am Ende
  traversal: '../', '..%2f', '/etc/passwd', 'c:\\'
  tmpl    : '{{', '${', '<%='
  cmd     : ';cat ', '|cat ', '`id`', '$(', 'wget ', 'curl '
Ein Request kann mehreren Familien angehoeren.
"""
import json, csv, collections, datetime as dt, urllib.parse, re
from pathlib import Path
import duckdb

BASE = Path(__file__).resolve().parents[3]
D = BASE / "analyse" / "data"; N = D / "betreiberlogs" / "normalisiert"
con = duckdb.connect(); con.execute("SET TimeZone='UTC'")
con.execute(f"CREATE VIEW r AS SELECT * FROM read_parquet('{N}/requests_26*.parquet')")
OUT = []
def show(t, rows, cols):
    print(f"\n### {t}\n| " + " | ".join(cols) + " |")
    print("|" + "|".join("---" for _ in cols) + "|")
    for x in rows: print("| " + " | ".join("" if v is None else str(v) for v in x) + " |")
    OUT.append({"title": t, "cols": cols, "rows": [list(map(str, x)) for x in rows]})

SCRIPT = ["<script", "javascript:", "onerror=", "onload=", "onmouseover=", "alert(",
          "<svg", "<img", "document.cookie", "eval("]
SQLI = ["union select", " and 1=1", " or 1=1", "chr(", "sleep(", "benchmark(",
        "information_schema", "waitfor delay", "pg_sleep"]
TRAV = ["../", "..%2f", "/etc/passwd"]
TMPL = ["{{", "${", "<%="]
CMD = [";cat ", "|cat ", "`id`", "$(", "wget ", "curl "]
FAM = [("script", SCRIPT), ("sqli", SQLI), ("traversal", TRAV), ("tmpl", TMPL), ("cmd", CMD)]

def fams(q):
    s = urllib.parse.unquote_plus(q).lower()
    return [n for n, pats in FAM if any(p in s for p in pats)]

cnt = collections.Counter(); per_month = collections.defaultdict(collections.Counter)
script_rows = []
for ts, ip, q, src, act in con.execute(
        "SELECT ts_utc, ip, raw_params, src_file, action_detail FROM r").fetchall():
    f = fams(q)
    if not f: continue
    for n in f:
        cnt[n] += 1; per_month[src][n] += 1
    if "script" in f:
        script_rows.append((ts, ".".join(ip.split(".")[:2]), src, act, q[:300]))
show("Angriffsartige Requests im Gesamtlog (5.157.202 Requests)",
     [[k, v] for k, v in cnt.most_common()], ["familie", "requests"])
show("Je Logdatei", [[s] + [per_month[s][k] for k, _ in FAM] for s in sorted(per_month)],
     ["logdatei"] + [k for k, _ in FAM])

ev = [json.loads(l) for l in open(D / "events.jsonl")]
pr = [e for e in ev if e["event_type"] == "probe"]
def iso(s): return int(dt.datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc).timestamp())
pset = {(iso(e["time"]), e["ip16"]) for e in pr}
sidx = collections.defaultdict(list)
for ts, ip16, src, act, q in script_rows: sidx[(ts, ip16)].append((src, act, q))
matched = [k for k in pset if k in sidx]
show("Deckung: die 101 probe-Events gegen den Skript-Injektions-Detektor", [
    ["probe-Events (Export)", len(pr)],
    ["davon (Sekunde,ip16) traegt im Log ein Skript-Injektions-Muster", len(matched)],
    ["Skript-Injektions-Requests im Gesamtlog", cnt["script"]],
    ["davon im Exportfenster Mai+Juni (log_2605+log_2606)", per_month["log_2605"]["script"] + per_month["log_2606"]["script"]],
    ["nicht publiziert (Mai+Juni, Skriptfamilie)", per_month["log_2605"]["script"] + per_month["log_2606"]["script"] - len(pr)],
    ["April + Juli ueberhaupt nicht im Export", per_month["log_2604"]["script"] + per_month["log_2607"]["script"]],
    ["alle Angriffsfamilien gesamt (Union unterschaetzt, Familien ueberlappen)", sum(cnt.values())],
], ["groesse", "wert"])
with open(N / "probe_matches.csv", "w", newline="") as f:
    cw = csv.writer(f); cw.writerow(["ts_utc", "iso", "ip16", "src_file", "action_detail", "query"])
    for ts, ip16, src, act, q in sorted(script_rows):
        cw.writerow([ts, dt.datetime.fromtimestamp(ts, dt.timezone.utc).isoformat(), ip16, src, act, q])
show("Fuenf Beispiele aus der Skriptfamilie (Query gekuerzt, ip nur /16)",
     [[dt.datetime.fromtimestamp(t, dt.timezone.utc).isoformat(), i, s, a, q[:110]]
      for t, i, s, a, q in sorted(script_rows)[:5]],
     ["zeit_utc", "ip16", "logdatei", "aktion", "query"])
(N / "probes.json").write_text(json.dumps(OUT, indent=1, default=str))
