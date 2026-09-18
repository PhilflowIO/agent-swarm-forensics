# -*- coding: utf-8 -*-
"""u01: vollstaendiger Verb-Vorrat, Flotte vs. Rest."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from u00_lib import con
c = con()
print("== action_kind ==")
for row in c.execute("""SELECT action_kind, sum(flotte::int) f, sum((not flotte)::int) nf
  FROM rx GROUP BY 1 ORDER BY f DESC""").fetchall():
    print("%-16s f=%-10d rest=%d" % row)
print("\n== action_raw (roh, was der Client wirklich schrieb) ==")
for row in c.execute("""SELECT lower(action_raw) a, sum(flotte::int) f, sum((not flotte)::int) nf
  FROM rx WHERE action_raw<>'' GROUP BY 1 ORDER BY f DESC LIMIT 60""").fetchall():
    print("%-24s f=%-10d rest=%d" % row)
print("\n== action_detail ==")
for row in c.execute("""SELECT action_detail, sum(flotte::int) f, sum((not flotte)::int) nf
  FROM rx WHERE action_detail<>'' GROUP BY 1 ORDER BY f DESC LIMIT 60""").fetchall():
    print("%-28s f=%-10d rest=%d" % row)
print("\n== script ==")
for row in c.execute("""SELECT script, sum(flotte::int) f, sum((not flotte)::int) nf
  FROM rx GROUP BY 1 ORDER BY f+nf DESC""").fetchall():
    print("%-14s f=%-10d rest=%d" % row)
