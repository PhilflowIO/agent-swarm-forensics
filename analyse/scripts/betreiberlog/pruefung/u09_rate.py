# -*- coding: utf-8 -*-
"""u09: Warum die Flotte nie gekillt wurde -- Requestrate je Adresse/Block."""
import sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from u00_lib import con
c=con()
print("== Spitzenlast je Einzeladresse und Stunde ==")
for lab,w in [("Flotte (im Fenster)","flotte"),("gekillte Bloecke","ip16 IN ('74.7','216.73','35.240','195.201','65.108','95.217')")]:
    r=c.execute(f"""WITH h AS (SELECT ip, date_trunc('hour', to_timestamp(ts_utc)) hh, count(*) n
      FROM rx WHERE {w} GROUP BY 1,2)
      SELECT count(*), round(avg(n),1), quantile_cont(n,0.5), quantile_cont(n,0.95), max(n) FROM h""").fetchone()
    print("%-22s adressstunden=%-8d mittel=%-8s median=%-6s p95=%-7s max=%s"%((lab,)+r))
print("\n== Spitzenlast je Einzeladresse und Minute ==")
for lab,w in [("Flotte","flotte"),("gekillte Bloecke","ip16 IN ('74.7','216.73','35.240','195.201','65.108','95.217')")]:
    r=c.execute(f"""WITH m AS (SELECT ip, floor(ts_utc/60) mm, count(*) n FROM rx WHERE {w} GROUP BY 1,2)
      SELECT round(avg(n),2), quantile_cont(n,0.95), max(n) FROM m""").fetchone()
    print("%-22s mittel=%-7s p95=%-6s max=%s"%((lab,)+r))
print("\n== Gesamtlast je Adresse ueber den Vorfall (Flotte) ==")
print(c.execute("""WITH a AS (SELECT ip, count(*) n FROM rx WHERE flotte GROUP BY 1)
 SELECT count(*) adressen, round(avg(n),1) mittel, quantile_cont(n,0.5) median, quantile_cont(n,0.99) p99, max(n) FROM a""").fetchone())
print("\n== zum Vergleich: der groesste gekillte Einzelblock 74.7 ==")
print(c.execute("""WITH a AS (SELECT ip, count(*) n FROM rx WHERE ip16='74.7' GROUP BY 1)
 SELECT count(*) adressen, round(avg(n),1), max(n) FROM a""").fetchone())
print("\n== Spitzenstunde der Flotte insgesamt gegen Adressen ==")
for r in c.execute("""SELECT strftime(date_trunc('hour',to_timestamp(ts_utc)),'%Y-%m-%d %H') h, count(*) n,
  count(distinct ip) a, round(count(*)*1.0/count(distinct ip),1) je_adresse
 FROM rx WHERE flotte GROUP BY 1 ORDER BY n DESC LIMIT 6""").fetchall(): print("  %s n=%-7d adressen=%-5d je_adresse=%s"%r)
