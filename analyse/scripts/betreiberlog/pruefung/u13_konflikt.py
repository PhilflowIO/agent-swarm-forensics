# -*- coding: utf-8 -*-
"""u13: oldconflict -- der Schwarm speichert ueber einen gemeldeten Konflikt."""
import sys,os,urllib.parse,collections
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from u00_lib import con
c=con()
print("Flotten-Schreibrequests gesamt:", c.execute("SELECT count(*) FROM rx WHERE flotte AND action_kind='write'").fetchone())
print("mit oldconflict-Parameter:", c.execute("SELECT count(*) FROM rx WHERE flotte AND action_kind='write' AND raw_params ILIKE '%oldconflict=%'").fetchone())
print("oldconflict=1 (Konflikt gemeldet, trotzdem gespeichert):",
      c.execute("SELECT count(*), count(distinct name), count(distinct page_id) FROM rx WHERE flotte AND action_kind='write' AND raw_params ILIKE '%oldconflict=1%'").fetchone())
print("je Tag:")
for r in c.execute("""SELECT strftime(to_timestamp(ts_utc),'%Y-%m-%d') d, count(*) n, count(distinct name) nm FROM rx
 WHERE flotte AND action_kind='write' AND raw_params ILIKE '%oldconflict=1%' GROUP BY 1 HAVING count(*)>5 ORDER BY 1""").fetchall(): print("  %s n=%-6d namen=%d"%r)
print("top Seiten:", c.execute("""SELECT page_id,count(*) n FROM rx WHERE flotte AND action_kind='write' AND raw_params ILIKE '%oldconflict=1%' GROUP BY 1 ORDER BY n DESC LIMIT 8""").fetchall())
print("\n== Zusammenfassungszeile (summary=) ==")
rows=c.execute("SELECT raw_params FROM rx WHERE flotte AND action_kind='write'").fetchall()
cnt=collections.Counter(); leer=0; ohne=0
for (p,) in rows:
    q=urllib.parse.parse_qs(p,keep_blank_values=True)
    if 'summary' not in q: ohne+=1; continue
    s=q['summary'][0].strip()
    if not s: leer+=1; continue
    cnt[s]+=1
print(" Schreibversuche:",len(rows),"ohne summary-Parameter:",ohne,"leer:",leer,"befuellt:",sum(cnt.values()),"verschieden:",len(cnt))
print(" top 25:")
for s,n in cnt.most_common(25): print("   %-5d %s"%(n,s[:90]))
