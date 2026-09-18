import sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from u00_lib import con
c=con()
print("== KILLED je /16, top 20 ==")
for r in c.execute("""SELECT ip16, sum(killed::int) k, count(*) n, count(distinct name) nm,
  min(strftime(to_timestamp(ts_utc),'%Y-%m-%d')) FILTER (WHERE killed) d0,
  max(strftime(to_timestamp(ts_utc),'%Y-%m-%d')) FILTER (WHERE killed) d1
 FROM rx GROUP BY 1 HAVING sum(killed::int)>0 ORDER BY k DESC LIMIT 20""").fetchall():
    print("%-10s killed=%-8d req=%-9d namen=%-5d %s..%s"%r)
print("\n== KILLED je Monat/Tag, gesamt ==")
for r in c.execute("""SELECT strftime(to_timestamp(ts_utc),'%Y-%m-%d') d, sum(killed::int) k, count(*) n
 FROM rx GROUP BY 1 HAVING sum(killed::int)>1000 ORDER BY 1""").fetchall(): print("%s k=%-8d n=%d"%r)
print("\n== tragen die KILLED-Zeilen Agenten-Seitennamen? ==")
print(c.execute("""SELECT count(*) FILTER (WHERE page_id ILIKE 'Agent%') agentseiten,
 count(*) FILTER (WHERE name<>'') mit_name, count(*) k FROM rx WHERE killed""").fetchone())
print("\n== beispiele KILLED ==")
for r in c.execute("""SELECT src_file,rec_no,ip16,name,action_kind,raw_params FROM rx WHERE killed USING SAMPLE 12 ROWS""").fetchall(): print(r)
