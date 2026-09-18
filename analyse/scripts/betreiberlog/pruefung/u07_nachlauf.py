import sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from u00_lib import con
c=con()
W="ts_utc BETWEEN epoch(TIMESTAMP '2026-07-03 00:00:00') AND epoch(TIMESTAMP '2026-07-31 23:59:59') AND ip16 IN (SELECT ip16 FROM fb)"
print("== Nachlauf in Flottenbloecken, Juli ==")
print(c.execute(f"SELECT count(*), count(distinct ip), count(distinct page_id), strftime(to_timestamp(min(ts_utc)),'%Y-%m-%d %H:%M:%S'), strftime(to_timestamp(max(ts_utc)),'%Y-%m-%d %H:%M:%S') FROM rx WHERE {W}").fetchone())
print("\naction_kind:", c.execute(f"SELECT action_kind, count(*) FROM rx WHERE {W} GROUP BY 1 ORDER BY 2 DESC").fetchall())
print("\ntop /16:", c.execute(f"SELECT ip16,count(*) n, count(distinct ip) FROM rx WHERE {W} GROUP BY 1 ORDER BY n DESC LIMIT 8").fetchall())
print("\ntop Agent-Seiten:")
for r in c.execute(f"SELECT page_id, count(*) n, count(distinct ip) a, strftime(to_timestamp(min(ts_utc)),'%Y-%m-%d %H:%M:%S'), strftime(to_timestamp(max(ts_utc)),'%Y-%m-%d %H:%M:%S') FROM rx WHERE {W} AND page_id ILIKE 'Agent%' GROUP BY 1 ORDER BY n DESC LIMIT 20").fetchall(): print("  ",r)
print("\n== letzter Schreibvorgang der Flotte ueberhaupt ==")
for r in c.execute("""SELECT strftime(to_timestamp(ts_utc),'%Y-%m-%d %H:%M:%S'), ip16, name, page_id, substr(raw_params,1,90) FROM rx
 WHERE ip16 IN (SELECT ip16 FROM fb) AND action_kind='write' ORDER BY ts_utc DESC LIMIT 12""").fetchall(): print("  ",r)
print("\n== letzte Requests mit gesetztem Wiki-Namen aus Flottenbloecken ==")
for r in c.execute("""SELECT strftime(to_timestamp(ts_utc),'%Y-%m-%d %H:%M:%S'), ip16, name, action_kind, substr(raw_params,1,80) FROM rx
 WHERE ip16 IN (SELECT ip16 FROM fb) AND name<>'' ORDER BY ts_utc DESC LIMIT 15""").fetchall(): print("  ",r)
