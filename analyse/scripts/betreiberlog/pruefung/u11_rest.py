# -*- coding: utf-8 -*-
"""u11: Sucharten quantifiziert, wiki2.cgi, zweite Population, Menschen-Gleichzeitigkeit."""
import sys,os,re,urllib.parse,collections
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from u00_lib import con
c=con()
print("=== A) Sucharten: Begriff je Seite vs. Nicht-Seite ===")
c.execute("CREATE TABLE pid AS SELECT DISTINCT page_id FROM rx WHERE page_id<>''")
rows=c.execute("SELECT ts_utc,name,ip,raw_params FROM rx WHERE flotte AND action_kind='search'").fetchall()
def term(p):
    q=urllib.parse.parse_qs(p,keep_blank_values=True)
    for k in ("search","keywords","q","query","text"):
        if k in q and q[k][0].strip(): return q[k][0].strip()
    return None
KOORD=re.compile(r"\bR[0-9]\b|\bG[0-9]\b|CONFIRMED|arrived|terminal|termination|terminated|timer|horizon|deadline|\b\d+m\d+\b|\b\d+\s*(seconds|minutes|sec|min)\b|scheduled|alive|ack\b|cohort|round",re.I)
pids=set(x[0] for x in c.execute("SELECT page_id FROM pid").fetchall())
tot=0; seite=0; koord=0; nat=0
sam=collections.Counter()
for ts,nm,ip,p in rows:
    t=term(p)
    if t is None: continue
    tot+=1
    if t in pids: seite+=1
    else:
        if KOORD.search(t): koord+=1
        if " " in t: nat+=1; sam[t]+=1
print("suchrequests mit Begriff:",tot)
print("  Begriff ist ein im Log vorkommender Seitenname:",seite, round(100*seite/tot,1),"%")
print("  sonst, davon Koordinations-/Zeitmuster:",koord, round(100*koord/tot,1),"%")
print("  sonst, davon mehrwortig (natuerliche Sprache):",nat, round(100*nat/tot,1),"%")
print("\n=== B) Suchwiederholung: derselbe Name, derselbe Begriff ===")
seen=collections.defaultdict(list)
for ts,nm,ip,p in rows:
    t=term(p)
    if t and nm: seen[(nm,t)].append(ts)
mehr=[v for v in seen.values() if len(v)>=3]
import statistics
gaps=[]
for v in mehr:
    v.sort(); gaps += [b-a for a,b in zip(v,v[1:])]
print("  (Name,Begriff)-Paare gesamt:",len(seen),"davon >=3 Wiederholungen:",len(mehr))
if gaps:
    gaps.sort()
    print("  Abstaende zwischen Wiederholungen s: median=%d p25=%d p75=%d, <=60s: %.1f%%"%(
        gaps[len(gaps)//2], gaps[len(gaps)//4], gaps[3*len(gaps)//4], 100*sum(1 for g in gaps if g<=60)/len(gaps)))
print("\n=== C) wiki2.cgi ===")
for r in c.execute("""SELECT flotte, script, count(*) n, count(distinct name) FILTER (WHERE name<>'') nm,
  count(*) FILTER (WHERE action_kind='write') w, sum(killed::int) k
 FROM rx GROUP BY 1,2 ORDER BY 1,2""").fetchall(): print("  flotte=%s %-10s n=%-9d namen=%-6d schreib=%-6d killed=%d"%r)
print("  Flotte auf wiki2.cgi, action_kind:", c.execute("SELECT action_kind,count(*) FROM rx WHERE flotte AND script='wiki2.cgi' GROUP BY 1 ORDER BY 2 DESC").fetchall())
print("  Zeitraum:", c.execute("SELECT strftime(to_timestamp(min(ts_utc)),'%Y-%m-%d %H:%M'), strftime(to_timestamp(max(ts_utc)),'%Y-%m-%d %H:%M') FROM rx WHERE flotte AND script='wiki2.cgi'").fetchone())
print("\n=== D) zweite Population: Nicht-Flottenverkehr mit Agentenmerkmalen ===")
print(c.execute("""SELECT count(*) gesamt,
  count(*) FILTER (WHERE page_id ILIKE 'Agent%') agentseiten,
  count(*) FILTER (WHERE name<>'') benannt,
  count(distinct name) FILTER (WHERE name<>'') namen,
  count(distinct ip16) bloecke FROM rx WHERE NOT flotte""").fetchone())
for r in c.execute("""SELECT ip16, count(*) n, count(distinct ip) a, count(distinct name) FILTER (WHERE name<>'') nm,
   count(*) FILTER (WHERE page_id ILIKE 'Agent%') ag, sum(killed::int) k
 FROM rx WHERE NOT flotte GROUP BY 1 HAVING count(*) FILTER (WHERE page_id ILIKE 'Agent%')>2000
 ORDER BY ag DESC LIMIT 15""").fetchall(): print("  %-10s n=%-9d adressen=%-5d namen=%-5d agentseiten=%-8d killed=%d"%r)
