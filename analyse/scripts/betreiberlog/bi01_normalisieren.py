#!/usr/bin/env python3
"""bi01 — Streaming-Normalisierung der Betreiber-Requestlogs (ISO-8859-1, eine Zeile je HTTP-Request).

Erzeugt je Monat eine gzip-TSV mit genau den Feldern, die die Identitaets- und
Containerfrage braucht.  Nie wird eine ganze Datei in den Speicher gelesen.

Aufruf:
  analyse/.venv/bin/python analyse/scripts/betreiberlog/bi01_normalisieren.py

Ausgabe: analyse/data/betreiberlogs/normalisiert/bi_<monat>.tsv.gz
Spalten : ts  ip  name  namensquelle  kind  page  script
  ts           Unix-UTC (Feld TS der Rohzeile)
  ip           volle Quell-IP (Feld IP)
  name         Wiki-Name; Feld NAME, sonst Formularfeld username=
  namensquelle name | username | ''
  kind         save | editform | browse | raw | diff | search | rc | other
  page         Seitenname aus id= / oldid= / nacktem ?Seitenname
  script       wiki | wiki2 (ProWiki hat zwei CGI-Endpunkte)
"""
import gzip, os, re, sys, urllib.parse

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC  = os.path.join(BASE, "data", "betreiberlogs")
DST  = os.path.join(SRC, "normalisiert")
os.makedirs(DST, exist_ok=True)

MONATE = ["log_2604", "log_2605", "log_2606", "log_2607"]
PATH_RX = re.compile(r"^https?://[^/]+(/\S*?)(?:\?|$)")
SAFE    = re.compile(r"[\t\r\n]")


def kind_und_seite(query_keys, qd, path):
    action = (qd.get("action") or "").lower()
    page = qd.get("id") or qd.get("oldid") or ""
    if "form_edit" in qd or action == "form_edit":
        k = "save"
    elif action == "edit":
        k = "editform"
    elif action in ("browse", ""):
        k = "browse"
    elif action == "raw":
        k = "raw"
    elif "diff" in qd or action == "diff":
        k = "diff"
    elif action in ("rc", "recentchanges"):
        k = "rc"
    else:
        k = "other"
    if not page and ("keywords" in qd or "search" in qd):
        k = "search"
        page = qd.get("keywords") or qd.get("search") or ""
    if not page and len(query_keys) == 1 and query_keys[0] and "=" not in query_keys[0]:
        page = query_keys[0]          # nackte Form ?SeitenName
        k = "browse" if k == "other" else k
    return k, page


def lauf(fn):
    src = os.path.join(SRC, fn)
    dst = os.path.join(DST, "bi_" + fn.replace("log_", "") + ".tsv.gz")
    n = ok = bad = 0
    with open(src, "rb") as f, gzip.open(dst, "wt", encoding="utf-8", compresslevel=6) as out:
        out.write("ts\tip\tname\tnamensquelle\tkind\tpage\tscript\n")
        for raw in f:
            n += 1
            s = raw.decode("iso-8859-1").rstrip("\n")
            if not s.startswith("#DONE2|"):
                bad += 1
                continue
            p = s.split("|")
            d = dict(zip(p[2::2], p[3::2]))
            ts = d.get("TS", "")
            if not ts.isdigit():
                bad += 1
                continue
            a = d.get("ACTION", "")
            m = PATH_RX.match(a)
            path = m.group(1) if m else ""
            script = "wiki2" if "wiki2.cgi" in path else "wiki" if "wiki.cgi" in path else "andere"
            q = a.split("?", 1)[1] if "?" in a else ""
            keys = [kv for kv in q.split("&") if kv]
            qd = {}
            for kv in keys:
                if "=" in kv:
                    k, v = kv.split("=", 1)
                    if k not in qd:
                        qd[k] = urllib.parse.unquote_plus(v)
            kind, page = kind_und_seite(keys, qd, path)
            name = d.get("NAME", "")
            quelle = "name" if name else ""
            if not name:
                name = qd.get("username", "")
                quelle = "username" if name else ""
            out.write("\t".join(SAFE.sub(" ", x)[:200] for x in
                                (ts, d.get("IP", ""), name, quelle, kind, page, script)) + "\n")
            ok += 1
    print(f"{fn}: {n} Zeilen, {ok} normalisiert, {bad} verworfen -> {dst}", flush=True)


if __name__ == "__main__":
    for fn in (sys.argv[1:] or MONATE):
        lauf(fn)
