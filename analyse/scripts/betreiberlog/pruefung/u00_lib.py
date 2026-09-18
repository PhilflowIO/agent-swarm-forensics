# -*- coding: utf-8 -*-
"""u00_lib.py -- duckdb-Sicht fuer die hypothesenfreie Nachlese (unbeobachtetes.md).
Flottendefinition uebernommen aus bi07_netze.py:31 / 80_freigabe_flotte.py:105-106.
Nur Lesen; veraendert keine bestehenden Artefakte.
"""
from __future__ import annotations
import os, csv, duckdb

BASE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
PQ = os.path.join(BASE, "data", "betreiberlogs", "normalisiert", "requests_26*.parquet")
NETZ = os.path.join(BASE, "artefakte", "betreiberlog_identitaet", "bi07_netzklassen.csv")
T0, T1 = 1779602131, 1783036799  # 2026-05-24T05:55:31Z .. 2026-07-02T23:59:59Z

def flotte_bloecke():
    out = []
    with open(NETZ, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if int(r["namen_2606"] or 0) >= 50 and int(r["req_2606"] or 0) > 0:
                out.append(r["ip16"])
    return out

def con():
    c = duckdb.connect()
    c.execute("SET TimeZone='UTC'")
    c.execute(f"CREATE VIEW r AS SELECT * FROM read_parquet('{PQ}')")
    c.execute("CREATE TABLE fb(ip16 VARCHAR)")
    c.executemany("INSERT INTO fb VALUES (?)", [(b,) for b in flotte_bloecke()])
    c.execute(f"""CREATE VIEW rx AS SELECT r.*,
        concat(str_split(r.ip,'.')[1],'.',str_split(r.ip,'.')[2]) AS ip16,
        (concat(str_split(r.ip,'.')[1],'.',str_split(r.ip,'.')[2]) IN (SELECT ip16 FROM fb)
         AND r.ts_utc BETWEEN {T0} AND {T1}) AS flotte
        FROM r""")
    return c

if __name__ == "__main__":
    c = con()
    print("bloecke", len(flotte_bloecke()))
    print(c.execute("SELECT flotte, count(*) FROM rx GROUP BY 1 ORDER BY 1").fetchall())
