# -*- coding: utf-8 -*-
"""u03: was ist action=archive / die fremden Verben?"""
import sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from u00_lib import con
c=con()
print("== beispiele action_raw=archive (flotte) ==")
for r in c.execute("""SELECT ts_utc,name,page_id,raw_params FROM rx WHERE flotte AND lower(action_raw)='archive' LIMIT 8""").fetchall():
    print(r)
print("\n== zeitspanne + wer ==")
print(c.execute("""SELECT min(ts_utc),max(ts_utc),count(distinct name),count(distinct ip),count(distinct page_id) FROM rx WHERE flotte AND lower(action_raw)='archive'""").fetchall())
FREMD=('raw','export','download','links','backlinks','fullsearch','info','recentchanges','wordindex','xml','html','printable','revisions','revision','view','source','print','index','login','random','preview','setprefs','editpage','context','get','page','new','show','text','display','versions','help','top','prefs','preferences','version')
q="','".join(FREMD)
print("\n== fremde Verben: Flotte vs Rest, Zeitraum, Traeger ==")
for r in c.execute(f"""SELECT lower(action_raw) a, sum(flotte::int) f, sum((not flotte)::int) nf,
   min(ts_utc) FILTER (WHERE flotte) t0, max(ts_utc) FILTER (WHERE flotte) t1,
   count(distinct name) FILTER (WHERE flotte) nm
   FROM rx WHERE lower(action_raw) IN ('{q}') GROUP BY 1 ORDER BY f DESC""").fetchall():
    print("%-16s f=%-6d rest=%-6d %s..%s namen=%s" % r)
print("\n== Beispielzeilen einiger fremder Verben ==")
for a in ('raw','export','download','links','backlinks','fullsearch','info','xml','login'):
    rows=c.execute(f"""SELECT src_file,rec_no,ts_utc,name,raw_params FROM rx WHERE flotte AND lower(action_raw)='{a}' LIMIT 2""").fetchall()
    for r in rows: print(a,"|",r)
