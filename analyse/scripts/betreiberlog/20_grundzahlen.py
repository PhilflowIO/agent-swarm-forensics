#!/usr/bin/env python3
"""
20_grundzahlen.py -- Grundzahlen je Monat, je Host, je Skript.
Aufruf: analyse/.venv/bin/python analyse/scripts/betreiberlog/20_grundzahlen.py
Ausgabe: stdout (Markdown) + normalisiert/grundzahlen.json
Alle Zeitangaben UTC (Spalte ts_utc, Quelle: Feld TS der Logzeile).
"""
import json
from pathlib import Path
import duckdb

BASE = Path(__file__).resolve().parents[3]
N = BASE / "analyse" / "data" / "betreiberlogs" / "normalisiert"
con = duckdb.connect()
con.execute("SET TimeZone='UTC'")
con.execute(f"CREATE VIEW r AS SELECT * FROM read_parquet('{N}/requests_26*.parquet')")

def md(sql, title, store):
    rows = con.execute(sql).fetchall(); cols = [d[0] for d in con.description]
    print(f"\n### {title}\n")
    print("| " + " | ".join(cols) + " |")
    print("|" + "|".join("---" for _ in cols) + "|")
    for x in rows:
        print("| " + " | ".join("" if v is None else str(v) for v in x) + " |")
    store.append({"title": title, "sql": sql, "cols": cols, "rows": rows})
    return rows

M = """
  count(*) AS requests,
  count(*) FILTER (WHERE name<>'') AS mit_namen,
  count(*) FILTER (WHERE action_kind='read') AS lesen,
  count(*) FILTER (WHERE action_kind='search') AS suchen,
  count(*) FILTER (WHERE action_kind='write') AS schreiben,
  count(*) FILTER (WHERE action_kind='editprefs') AS editprefs,
  count(*) FILTER (WHERE action_kind='delete') AS loeschen,
  count(*) FILTER (WHERE action_kind='other') AS sonstige,
  count(DISTINCT name) FILTER (WHERE name<>'') AS namen,
  count(DISTINCT ip) AS ips,
  count(DISTINCT page_id) FILTER (WHERE page_id<>'') AS seiten,
  strftime(to_timestamp(min(ts_utc)),'%Y-%m-%d %H:%M') AS von_utc,
  strftime(to_timestamp(max(ts_utc)),'%Y-%m-%d %H:%M') AS bis_utc
"""
S = []
md(f"SELECT 'GESAMT' AS x, {M} FROM r", "Gesamtkorpus", S)
md(f"SELECT src_file, {M} FROM r GROUP BY 1 ORDER BY 1",
   "Je Logdatei (Monatsgrenzen in Wiener Lokalzeit gesetzt, Werte in UTC)", S)
md(f"SELECT strftime(to_timestamp(ts_utc),'%Y-%m') AS monat_utc, {M} FROM r GROUP BY 1 ORDER BY 1",
   "Je UTC-Kalendermonat", S)
md(f"SELECT host, {M} FROM r GROUP BY 1 ORDER BY requests DESC",
   "Je URL-Host (normalisiert: klein, ohne www., ohne Port)", S)
md(f"SELECT wiki, script, {M} FROM r GROUP BY 1,2 ORDER BY requests DESC",
   "Je Wiki-Pfad und Skript", S)
md("SELECT host, src_file, count(*) AS n FROM r GROUP BY 1,2 ORDER BY 1,2", "Host x Monat", S)
md("SELECT src_file, script, count(*) AS n FROM r GROUP BY 1,2 ORDER BY 1,2", "Skript x Monat", S)
md("SELECT action_kind, action_detail, count(*) AS n FROM r GROUP BY 1,2 ORDER BY n DESC LIMIT 30",
   "action_kind / action_detail (Top 30)", S)
md("SELECT action_raw, count(*) AS n FROM r WHERE action_kind='other' GROUP BY 1 ORDER BY n DESC LIMIT 25",
   "Was in 'other' faellt (Top 25 action-Werte)", S)
md("SELECT src_file, count(*) AS killed FROM r WHERE killed GROUP BY 1 ORDER BY 1",
   "Vom Betreiber abgebrochene Requests (HOST-Feld traegt ' KILLED')", S)
md("SELECT host_raw, count(*) AS n FROM r GROUP BY 1 ORDER BY n DESC",
   "Rohe URL-netloc-Varianten", S)
(N / "grundzahlen.json").write_text(json.dumps(S, indent=1, default=str))
