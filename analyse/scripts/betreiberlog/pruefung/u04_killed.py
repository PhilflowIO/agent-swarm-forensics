# -*- coding: utf-8 -*-
"""u04: die KILLED-Markierung -- wen trifft sie, wogegen, und was tut der Agent danach?"""
import sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from u00_lib import con
c=con()
print("gesamt killed:", c.execute("SELECT sum(killed::int), count(*) FROM rx").fetchone())
print("killed flotte/rest:", c.execute("SELECT flotte, sum(killed::int) k, count(*) n FROM rx GROUP BY 1 ORDER BY 1").fetchall())
print("\n== killed je action_kind (flotte) ==")
for r in c.execute("""SELECT action_kind, sum(killed::int) k, count(*) n, round(100.0*sum(killed::int)/count(*),2) p
 FROM rx WHERE flotte GROUP BY 1 ORDER BY k DESC""").fetchall(): print("%-12s k=%-8d n=%-9d %.2f%%"%r)
print("\n== killed je action_kind (rest) ==")
for r in c.execute("""SELECT action_kind, sum(killed::int) k, count(*) n, round(100.0*sum(killed::int)/count(*),2) p
 FROM rx WHERE not flotte GROUP BY 1 ORDER BY k DESC""").fetchall(): print("%-12s k=%-8d n=%-9d %.2f%%"%r)
print("\n== killed je Tag (flotte), Anteil ==")
for r in c.execute("""SELECT strftime(to_timestamp(ts_utc),'%Y-%m-%d') d, sum(killed::int) k, count(*) n,
 round(100.0*sum(killed::int)/count(*),2) p FROM rx WHERE flotte GROUP BY 1 ORDER BY 1""").fetchall():
    print("%s k=%-8d n=%-8d %.2f%%"%r)
print("\n== killed je action_detail (flotte), top ==")
for r in c.execute("""SELECT action_detail, sum(killed::int) k, count(*) n, round(100.0*sum(killed::int)/count(*),2) p
 FROM rx WHERE flotte GROUP BY 1 HAVING sum(killed::int)>50 ORDER BY k DESC LIMIT 25""").fetchall(): print("%-18s k=%-8d n=%-8d %.2f%%"%r)
