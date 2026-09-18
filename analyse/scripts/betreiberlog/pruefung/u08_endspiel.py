import sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from u00_lib import con
c=con()
print("== Flottenbloecke: benannte Requests je Tag, 20.6.-05.7. ==")
for r in c.execute("""SELECT strftime(to_timestamp(ts_utc),'%Y-%m-%d') d,
  count(*) FILTER (WHERE name<>'') benannt, count(distinct name) FILTER (WHERE name<>'') namen,
  count(*) FILTER (WHERE action_kind='write') schreib, count(*) gesamt
 FROM rx WHERE ip16 IN (SELECT ip16 FROM fb)
  AND ts_utc BETWEEN epoch(TIMESTAMP '2026-06-20 00:00:00') AND epoch(TIMESTAMP '2026-07-05 23:59:59')
 GROUP BY 1 ORDER BY 1""").fetchall(): print("%s benannt=%-7d namen=%-5d schreib=%-5d gesamt=%d"%r)
print("\n== die Luecke exakt ==")
print("letzter benannter Request vor der Luecke / erster danach:")
for q in ["SELECT max(ts_utc) FROM rx WHERE ip16 IN (SELECT ip16 FROM fb) AND name<>'' AND ts_utc < epoch(TIMESTAMP '2026-07-01 00:00:00')",
          "SELECT min(ts_utc) FROM rx WHERE ip16 IN (SELECT ip16 FROM fb) AND name<>'' AND ts_utc > epoch(TIMESTAMP '2026-06-25 00:00:00')"]:
    t=c.execute(q).fetchone()[0]
    print(" ",t, c.execute(f"SELECT strftime(to_timestamp({t}),'%Y-%m-%d %H:%M:%S')").fetchone()[0])
print("\n== Schreibrequests der Flotte NACH 2026-07-02T17:51:22Z ==")
for r in c.execute("""SELECT strftime(to_timestamp(ts_utc),'%H:%M:%S') t, ip16, name, page_id, action_kind
 FROM rx WHERE ip16 IN (SELECT ip16 FROM fb) AND ts_utc > 1783014682
   AND action_kind IN ('write','delete') ORDER BY ts_utc""").fetchall(): print("  ",r)
print("\n== alle benannten Requests am 2.7. je Stunde ==")
for r in c.execute("""SELECT strftime(to_timestamp(ts_utc),'%H') h, count(*) n, count(distinct name) nm,
  count(*) FILTER (WHERE action_kind='write') w
 FROM rx WHERE ip16 IN (SELECT ip16 FROM fb) AND name<>''
  AND strftime(to_timestamp(ts_utc),'%Y-%m-%d')='2026-07-02' GROUP BY 1 ORDER BY 1""").fetchall(): print("  h%s n=%-4d namen=%-3d schreib=%d"%r)
print("\n== Namen des 2.7. ==")
print(c.execute("""SELECT list(distinct name) FROM rx WHERE ip16 IN (SELECT ip16 FROM fb) AND name<>''
 AND strftime(to_timestamp(ts_utc),'%Y-%m-%d')='2026-07-02'""").fetchone()[0])
