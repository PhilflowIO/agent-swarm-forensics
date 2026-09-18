import sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from u00_lib import con, flotte_bloecke
c=con()
print("== 3. Juli: KILLED je /16 ==")
for r in c.execute("""SELECT ip16, sum(killed::int) k, count(*) n, count(distinct name) nm,
  (ip16 IN (SELECT ip16 FROM fb)) flottenblock
 FROM rx WHERE strftime(to_timestamp(ts_utc),'%Y-%m-%d')='2026-07-03'
 GROUP BY 1 ORDER BY k DESC LIMIT 15""").fetchall(): print(r)
print("\n== Flottenbloecke: Verkehr und KILLED je Tag, 28.6.-10.7. (ohne Fensterfilter) ==")
for r in c.execute("""SELECT strftime(to_timestamp(ts_utc),'%Y-%m-%d') d, count(*) n, sum(killed::int) k,
  count(distinct name) FILTER (WHERE name<>'') nm, count(*) FILTER (WHERE page_id ILIKE 'Agent%') ag
 FROM rx WHERE ip16 IN (SELECT ip16 FROM fb)
   AND ts_utc BETWEEN epoch(TIMESTAMP '2026-06-28 00:00:00') AND epoch(TIMESTAMP '2026-07-10 23:59:59')
 GROUP BY 1 ORDER BY 1""").fetchall(): print("%s n=%-8d killed=%-6d namen=%-5d agentseiten=%d"%r)
print("\n== Flottenbloecke nach dem Vorfall: Monatssummen ==")
for r in c.execute("""SELECT src_file, count(*) n, sum(killed::int) k, count(distinct name) FILTER (WHERE name<>'') nm
 FROM rx WHERE ip16 IN (SELECT ip16 FROM fb) GROUP BY 1 ORDER BY 1""").fetchall(): print(r)
print("\n== 3. Juli, was wurde gekillt (Muster) ==")
for r in c.execute("""SELECT action_kind, count(*) n, sum(killed::int) k FROM rx
 WHERE strftime(to_timestamp(ts_utc),'%Y-%m-%d')='2026-07-03' GROUP BY 1 ORDER BY k DESC""").fetchall(): print(r)
