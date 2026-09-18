# -*- coding: utf-8 -*-
"""u10: Suche als Warteschleife -- gesucht wird, was es noch nicht gibt."""
import sys,os,urllib.parse,collections
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from u00_lib import con
c=con()
# 1) Suchbegriff == spaeterer Seitenname?
c.execute("""CREATE TABLE such AS
 SELECT ts_utc, name, raw_params FROM rx WHERE flotte AND action_kind='search'""")
rows=c.execute("SELECT ts_utc,name,raw_params FROM such").fetchall()
first_such={}; cnt=collections.Counter()
for ts,nm,p in rows:
    q=urllib.parse.parse_qs(p,keep_blank_values=True)
    t=None
    for k in ("search","keywords","q","query","text"):
        if k in q and q[k][0].strip(): t=q[k][0].strip(); break
    if not t: continue
    cnt[t]+=1
    if t not in first_such or ts<first_such[t]: first_such[t]=ts
c.execute("CREATE TABLE st(term VARCHAR, n BIGINT, t0 BIGINT)")
c.executemany("INSERT INTO st VALUES (?,?,?)",[(t,cnt[t],first_such[t]) for t in cnt])
print("suchbegriffe:",len(cnt))
r=c.execute("""WITH w AS (SELECT page_id, min(ts_utc) t0 FROM rx WHERE flotte AND action_kind='write' AND page_id<>'' GROUP BY 1)
 SELECT count(*) treffer,
   count(*) FILTER (WHERE st.t0 < w.t0) gesucht_vor_erstschreibung,
   count(*) FILTER (WHERE st.t0 >= w.t0) gesucht_danach
 FROM st JOIN w ON st.term = w.page_id""").fetchone()
print("Suchbegriffe, die zugleich eine von der Flotte beschriebene Seite sind:",r[0])
print("  davon zuerst GESUCHT, dann erst geschrieben:",r[1])
print("  davon erst geschrieben, dann gesucht:",r[2])
print("\nVorlauf (Sekunden) gesucht-vor-geschrieben, Verteilung:")
print(c.execute("""WITH w AS (SELECT page_id, min(ts_utc) t0 FROM rx WHERE flotte AND action_kind='write' AND page_id<>'' GROUP BY 1)
 SELECT count(*), round(quantile_cont(w.t0-st.t0,0.25)), round(quantile_cont(w.t0-st.t0,0.5)), round(quantile_cont(w.t0-st.t0,0.75)), max(w.t0-st.t0)
 FROM st JOIN w ON st.term=w.page_id WHERE st.t0<w.t0""").fetchone())
print("\nBeispiele (Begriff, Suchen, Vorlauf in s):")
for r in c.execute("""WITH w AS (SELECT page_id, min(ts_utc) t0 FROM rx WHERE flotte AND action_kind='write' AND page_id<>'' GROUP BY 1)
 SELECT st.term, st.n, w.t0-st.t0 FROM st JOIN w ON st.term=w.page_id WHERE st.t0<w.t0 ORDER BY st.n DESC LIMIT 15""").fetchall(): print("  ",r)
print("\n== Suchbegriffe, die NIE eine Seite wurden (top 20 nach Zahl) ==")
for r in c.execute("""SELECT st.term, st.n FROM st WHERE st.term NOT IN (SELECT page_id FROM rx WHERE page_id<>'')
 ORDER BY st.n DESC LIMIT 20""").fetchall(): print("  ",r)
