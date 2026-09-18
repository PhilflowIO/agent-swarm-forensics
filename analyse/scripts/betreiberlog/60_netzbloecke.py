#!/usr/bin/env python3
"""
60_netzbloecke.py -- Netzblock-Aggregation (Datenschutz-Vorlauf).
Gibt NUR /8- und /16-Aggregate aus, nie Einzel-IPs.
Aufruf: analyse/.venv/bin/python analyse/scripts/betreiberlog/60_netzbloecke.py
"""
from pathlib import Path
import duckdb
BASE = Path(__file__).resolve().parents[3]
N = BASE / "analyse" / "data" / "betreiberlogs" / "normalisiert"
con = duckdb.connect(); con.execute("SET TimeZone='UTC'")
con.execute(f"CREATE VIEW r AS SELECT *, split_part(ip,'.',1)||'.'||split_part(ip,'.',2) AS ip16 "
            f"FROM read_parquet('{N}/requests_26*.parquet')")
def show(t, sql):
    rows = con.execute(sql).fetchall(); cols = [d[0] for d in con.description]
    print(f"\n### {t}\n| " + " | ".join(cols) + " |")
    print("|" + "|".join("---" for _ in cols) + "|")
    for x in rows: print("| " + " | ".join("" if v is None else str(v) for v in x) + " |")
show("Top-/16-Bloecke mit Wiki-Namen (Flotte)", """
 SELECT ip16, count(*) n, count(DISTINCT ip) ips, count(DISTINCT name) FILTER (WHERE name<>'') namen,
        count(*) FILTER (WHERE action_kind='write') writes
 FROM r WHERE name<>'' GROUP BY 1 ORDER BY n DESC LIMIT 20""")
show("Top-/16-Bloecke gesamt", """
 SELECT ip16, count(*) n, count(DISTINCT ip) ips FROM r GROUP BY 1 ORDER BY n DESC LIMIT 20""")
show("Loeschungen je /16 (Administrator)", """
 SELECT ip16, count(*) n, count(DISTINCT ip) ips, count(DISTINCT name) FILTER (WHERE name<>'') namen
 FROM r WHERE action_kind='delete' GROUP BY 1 ORDER BY n DESC LIMIT 10""")
show("Schreibvorgaenge je /16", """
 SELECT ip16, count(*) n, count(DISTINCT ip) ips FROM r WHERE action_kind='write'
 GROUP BY 1 ORDER BY n DESC LIMIT 15""")
