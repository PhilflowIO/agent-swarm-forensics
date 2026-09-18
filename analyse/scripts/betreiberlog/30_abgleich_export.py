#!/usr/bin/env python3
"""
30_abgleich_export.py -- Abgleich Betreiber-Requestlog <-> publizierter Export.

Aufruf: analyse/.venv/bin/python analyse/scripts/betreiberlog/30_abgleich_export.py
Eingabe: normalisiert/requests_26*.parquet, data/{revisions,events,labels,pages}.jsonl
Ausgabe: stdout (Markdown) + normalisiert/abgleich.json
         normalisiert/rev_unmatched.csv  (nicht zuordenbare Revisionen)
         normalisiert/deleted_no_archive.csv (geloeschte Seiten ohne Archiv)

MATCH-REGELN Revision -> Schreibrequest:
  Kandidaten sind alle Requests mit action_kind='write' (Regel R1 aus
  10_normalisieren.py) und page_id = revision.name.
  T1 exact  : |dt| = 0 s UND ip16(request) = revision.ip16
  T2 ip2s   : |dt| <= 2 s UND ip16 gleich
  T3 t60    : |dt| <= 60 s (ip egal)
  T4 page   : nur Seitenname trifft, beliebige Zeit
  T0 none   : kein Schreibrequest auf diesen Seitennamen im Log
  ip16 = die ersten zwei Oktette; der Export publiziert IPs nur so.
"""
import json, csv, collections, datetime as dt
from pathlib import Path
import duckdb

BASE = Path(__file__).resolve().parents[3]
D = BASE / "analyse" / "data"
N = D / "betreiberlogs" / "normalisiert"
con = duckdb.connect(); con.execute("SET TimeZone='UTC'")
con.execute(f"CREATE VIEW r AS SELECT * FROM read_parquet('{N}/requests_26*.parquet')")
OUT = []

def sec(t):
    print("\n## " + t)

def show(title, rows, cols):
    print(f"\n### {title}\n")
    print("| " + " | ".join(cols) + " |")
    print("|" + "|".join("---" for _ in cols) + "|")
    for x in rows:
        print("| " + " | ".join("" if v is None else str(v) for v in x) + " |")
    OUT.append({"title": title, "cols": cols, "rows": [list(map(str, x)) for x in rows]})

def iso(s):
    return int(dt.datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc).timestamp())

# ---------- Schreibrequests aus dem Log ----------
writes = con.execute("""
  SELECT ts_utc, ip, page_id, name,
         regexp_extract(raw_params,'(?:^|&)username=([^&]*)',1) AS uname
  FROM r WHERE action_kind='write' AND page_id<>''
""").fetchall()
w_by_page = collections.defaultdict(list)
for ts, ip, pid, nm, un in writes:
    w_by_page[pid].append((ts, ".".join(ip.split(".")[:2]), nm, un))
n_writes_total = con.execute("SELECT count(*) FROM r WHERE action_kind='write'").fetchone()[0]

sec("A) Zuordnung der archivierten Revisionen")
tiers = collections.Counter(); tier_by_wiki = collections.defaultdict(collections.Counter)
unmatched = []
revs = 0
for line in open(D / "revisions.jsonl"):
    d = json.loads(line); revs += 1
    ts = iso(d["time"]); cand = w_by_page.get(d["name"], [])
    tier = "T0_none"
    if cand:
        best = None
        for c_ts, c_ip16, c_nm, c_un in cand:
            dtv = abs(c_ts - ts)
            ipok = (d.get("ip16") or "") == c_ip16
            if dtv == 0 and ipok: t = "T1_exact"
            elif dtv <= 2 and ipok: t = "T2_ip2s"
            elif dtv <= 60: t = "T3_t60"
            else: t = "T4_page"
            rank = ["T1_exact", "T2_ip2s", "T3_t60", "T4_page"].index(t)
            if best is None or rank < best[0]: best = (rank, t, dtv)
        tier = best[1]
    tiers[tier] += 1; tier_by_wiki[d["wiki"]][tier] += 1
    if tier in ("T4_page", "T0_none"):
        unmatched.append([d["wiki"], d["name"], d["time"], d.get("label"), d.get("ip16"), tier])
order = ["T1_exact", "T2_ip2s", "T3_t60", "T4_page", "T0_none"]
show("Revisionen (n=%d) nach Match-Guete" % revs,
     [[t, tiers[t], f"{100*tiers[t]/revs:.1f}%"] for t in order], ["tier", "n", "anteil"])
show("Match-Guete je Wiki",
     [[w] + [tier_by_wiki[w][t] for t in order] + [sum(tier_by_wiki[w].values())]
      for w in sorted(tier_by_wiki)], ["wiki"] + order + ["summe"])
with open(N / "rev_unmatched.csv", "w", newline="") as f:
    cw = csv.writer(f); cw.writerow(["wiki", "name", "time", "label", "ip16", "tier"]); cw.writerows(unmatched)

sec("B) Speicherversuche gegen archivierte Fassungen")
lab = [json.loads(l) for l in open(D / "labels.jsonl")]
sum_sr = sum(x.get("save_requests") or 0 for x in lab)
human = sum(x.get("save_requests") or 0 for x in lab if x.get("is_human_handle"))
fleet = sum_sr - human
dse_only = sum(x.get("save_requests") or 0 for x in lab if x.get("wikis") == ["dse"])
show("Speicherversuche: Export vs Log", [
    ["labels.jsonl sum(save_requests)", sum_sr, "Paper: 39456"],
    ["davon is_human_handle=true", human, ""],
    ["davon Flotte (nicht human)", fleet, "Paper: 35555"],
    ["Log: action_kind='write' (form_edit)", n_writes_total, "alle Hosts, nur /dse/"],
    ["Log: write mit page_id", len(writes), ""],
    ["archivierte Revisionen (Export)", revs, "Paper: 14591"],
    ["fehlgeschlagen = Flotte - archiviert(dse+..)", fleet - revs, ""],
], ["groesse", "wert", "anmerkung"])

# Schreibrequests je Seite ohne jede archivierte Revision
rev_pages = set()
for line in open(D / "revisions.jsonl"):
    d = json.loads(line); rev_pages.add(d["name"])
noarch = {p: v for p, v in w_by_page.items() if p not in rev_pages}
show("Schreibrequests im Log auf Seiten OHNE jede archivierte Revision",
     [["Seiten", len(noarch)], ["Requests", sum(len(v) for v in noarch.values())]], ["groesse", "wert"])
# Wiederholungen: Requests auf Seiten MIT Archiv, minus Zahl der Revisionen dieser Seite
rev_per_page = collections.Counter()
for line in open(D / "revisions.jsonl"):
    rev_per_page[json.loads(line)["name"]] += 1
surplus = sum(max(0, len(v) - rev_per_page[p]) for p, v in w_by_page.items() if p in rev_pages)
show("Ueberzaehlige Schreibrequests auf archivierten Seiten (Retry-Schleifen)",
     [["ueberzaehlig", surplus]], ["groesse", "wert"])

sec("C) Geloeschte Seiten ohne archivierten Inhalt")
ev = [json.loads(l) for l in open(D / "events.jsonl")]
dels = [e for e in ev if e["event_type"] == "delete"]
held = {}
for e in dels:
    held.setdefault(e["page_key"], e.get("page_held"))
no_arch_pages = sorted(k for k, v in held.items() if v is False)
show("Loeschereignisse", [
    ["delete-Events", len(dels)],
    ["verschiedene Seiten", len(held)],
    ["Seiten mit page_held=false (ohne Archiv)", len(no_arch_pages), ],
], ["groesse", "wert"])
names = [k.split("~", 1)[1].replace("~2f", "/") for k in no_arch_pages]  # ~2f = Export-Escape fuer "/" (Unterseiten)
con.execute("CREATE TABLE gp(name VARCHAR)")
con.executemany("INSERT INTO gp VALUES (?)", [(x,) for x in names])
res = con.execute("""
 SELECT g.name,
        count(q.ts_utc) AS requests,
        count(q.ts_utc) FILTER (WHERE q.action_kind='write') AS writes,
        count(q.ts_utc) FILTER (WHERE q.action_kind='read') AS reads,
        count(q.ts_utc) FILTER (WHERE q.action_kind='delete') AS deletes,
        count(DISTINCT q.ip) AS ips,
        count(DISTINCT q.name) FILTER (WHERE q.name<>'') AS namen,
        min(q.ts_utc) AS t0, max(q.ts_utc) AS t1
 FROM gp g LEFT JOIN r q ON q.page_id=g.name GROUP BY 1
""").fetchall()
vis = [x for x in res if x[1] > 0]
withw = [x for x in res if x[2] > 0]
show("Sichtbarkeit der %d Seiten ohne Archiv im Requestlog" % len(names), [
    ["im Log ueberhaupt sichtbar", len(vis), f"{100*len(vis)/max(1,len(names)):.1f}%"],
    ["mit mindestens einem Schreibrequest", len(withw), f"{100*len(withw)/max(1,len(names)):.1f}%"],
    ["gar nicht im Log", len(names) - len(vis), ""],
    ["Requests auf diese Seiten gesamt", sum(x[1] for x in res), ""],
], ["groesse", "wert", "anteil"])
with open(N / "deleted_no_archive.csv", "w", newline="") as f:
    cw = csv.writer(f)
    cw.writerow(["name", "requests", "writes", "reads", "deletes", "ips", "namen", "first_utc", "last_utc"])
    for x in sorted(res, key=lambda y: -y[1]):
        cw.writerow(list(x[:7]) + [dt.datetime.fromtimestamp(x[7], dt.timezone.utc).isoformat() if x[7] else "",
                                   dt.datetime.fromtimestamp(x[8], dt.timezone.utc).isoformat() if x[8] else ""])
show("Zehn meistbesuchte dieser Seiten (Namen sind Agentenseiten, keine Personendaten)",
     [[x[0], x[1], x[2], x[3], x[5],
       dt.datetime.fromtimestamp(x[7], dt.timezone.utc).strftime("%Y-%m-%d") if x[7] else "",
       dt.datetime.fromtimestamp(x[8], dt.timezone.utc).strftime("%Y-%m-%d") if x[8] else ""]
      for x in sorted(res, key=lambda y: -y[1])[:10]],
     ["seite", "requests", "writes", "reads", "ips", "erst", "letzt"])

sec("D) Die 101 probe-Events")
pr = [e for e in ev if e["event_type"] == "probe"]
src = collections.Counter(s.split(":")[0].split("/")[-1] for e in pr for s in e["source_refs"])
show("Quellen der probe-Events", [[k, v] for k, v in src.items()], ["quelle", "n"])
show("probe: request_action / param_family",
     list(collections.Counter((e["request_action"], e["param_family"]) for e in pr).items()),
     ["(action,family)", "n"])
# Zuordnung ts+ip16
byts = collections.defaultdict(set)
for ts, ip in con.execute("SELECT ts_utc, ip FROM r").fetchall():
    byts[ts].add(".".join(ip.split(".")[:2]))
hit = sum(1 for e in pr if ".".join((e["ip16"] or "").split(".")[:2]) in byts.get(iso(e["time"]), set()))
show("Zuordnung der probe-Events ins Betreiberlog (Sekunde + ip16)",
     [["probe-Events", len(pr)], ["im Log wiedergefunden", hit],
      ["Zeitfenster", f"{min(e['time'] for e in pr)} .. {max(e['time'] for e in pr)}"]],
     ["groesse", "wert"])
(N / "abgleich.json").write_text(json.dumps(OUT, indent=1, default=str))
