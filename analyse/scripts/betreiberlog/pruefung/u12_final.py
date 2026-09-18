# -*- coding: utf-8 -*-
"""u12: Schlusspruefungen fuer unbeobachtetes.md (alles UTC)."""
import sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from u00_lib import con
c=con()
FREMD="('raw','export','download','links','backlinks','fullsearch','info','recentchanges','xml','html','printable','revisions','revision','view','source','print','index','preview','setprefs','editpage','context','get','page','new','show','text','display','versions','prefs','history','diff')"
print("== A) fremde Verben: Zahl, Namen, zeitliche Verteilung ==")
print(" gesamt:",c.execute(f"SELECT sum(flotte::int), sum((not flotte)::int), count(distinct name) FILTER (WHERE flotte AND name<>'') FROM rx WHERE lower(action_raw) IN {FREMD}").fetchone())
for r in c.execute(f"""SELECT strftime(to_timestamp(ts_utc),'%Y-%W') w, count(*) n, count(distinct name) FILTER (WHERE name<>'') nm
 FROM rx WHERE flotte AND lower(action_raw) IN {FREMD} GROUP BY 1 ORDER BY 1""").fetchall(): print("  woche %s n=%-5d namen=%d"%r)
print(" Anteil an allen Flottenrequests je Woche (Lernkurve?):")
for r in c.execute(f"""SELECT strftime(to_timestamp(ts_utc),'%Y-%W') w,
  round(1000.0*count(*) FILTER (WHERE lower(action_raw) IN {FREMD})/count(*),2) promille, count(*) gesamt
 FROM rx WHERE flotte GROUP BY 1 ORDER BY 1""").fetchall(): print("  woche %s %s promille (n=%d)"%r)
print("\n== B) Schreibvolumen je Tag UTC, Flotte ==")
for r in c.execute("""SELECT strftime(to_timestamp(ts_utc),'%Y-%m-%d') d, count(*) FILTER (WHERE action_kind='write') w,
  count(distinct page_id) FILTER (WHERE action_kind='write') s, count(distinct name) FILTER (WHERE name<>'') nm
 FROM rx WHERE flotte GROUP BY 1 HAVING count(*) FILTER (WHERE action_kind='write')>0 ORDER BY 1""").fetchall(): print("  %s schreib=%-6d seiten=%-5d namen=%d"%r)
print("\n== C) das Ende, UTC ==")
for r in c.execute("""SELECT strftime(to_timestamp(ts_utc),'%Y-%m-%d') d, count(*) FILTER (WHERE name<>'') b,
 count(distinct name) FILTER (WHERE name<>'') nm, count(*) FILTER (WHERE action_kind='write') w, count(*) n
 FROM rx WHERE ip16 IN (SELECT ip16 FROM fb) AND ts_utc BETWEEN epoch(TIMESTAMP '2026-06-21') AND epoch(TIMESTAMP '2026-07-04')
 GROUP BY 1 ORDER BY 1""").fetchall(): print("  %s benannt=%-6d namen=%-5d schreib=%-5d gesamt=%d"%r)
print(" letzter benannter Request vor der Stille / erster des 2.7.:")
print("  ",c.execute("""SELECT strftime(to_timestamp(max(ts_utc)),'%Y-%m-%d %H:%M:%S') FROM rx WHERE flotte AND name<>'' AND ts_utc<epoch(TIMESTAMP '2026-06-25')""").fetchone(),
      c.execute("""SELECT strftime(to_timestamp(min(ts_utc)),'%Y-%m-%d %H:%M:%S'), strftime(to_timestamp(max(ts_utc)),'%Y-%m-%d %H:%M:%S') FROM rx WHERE flotte AND name<>'' AND ts_utc>epoch(TIMESTAMP '2026-07-02')""").fetchone())
print("  benannte Requests 25.6.-1.7.:", c.execute("SELECT count(*), count(distinct name) FROM rx WHERE flotte AND name<>'' AND ts_utc BETWEEN epoch(TIMESTAMP '2026-06-23') AND epoch(TIMESTAMP '2026-07-02')").fetchone())
print("\n== D) action=archive ==")
print(" ",c.execute("""SELECT count(*), count(distinct name) FILTER (WHERE name<>''), count(distinct page_id),
  count(*) FILTER (WHERE raw_params ILIKE '%cmd=list%') als_liste, count(*) FILTER (WHERE raw_params ILIKE '%version=%') mit_version,
  strftime(to_timestamp(min(ts_utc)),'%Y-%m-%d'), strftime(to_timestamp(max(ts_utc)),'%Y-%m-%d')
  FROM rx WHERE flotte AND lower(action_raw)='archive'""").fetchone())
print("\n== E) Verteilung Requests je Flottenadresse ==")
print(" ",c.execute("""WITH a AS (SELECT ip,count(*) n FROM rx WHERE flotte GROUP BY 1)
 SELECT count(*), min(n), quantile_cont(n,0.05), quantile_cont(n,0.5), quantile_cont(n,0.95), max(n), round(stddev(n)/avg(n),3) vk FROM a""").fetchone())
