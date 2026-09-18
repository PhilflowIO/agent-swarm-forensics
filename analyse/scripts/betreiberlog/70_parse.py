#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
70_parse.py — Pass 1 ueber die Betreiber-Requestlogs (log_2604..log_2607).

Zeilenformat (ISO-8859-1, eine Zeile je HTTP-Request):
  #DONE2|1|UT|<usertime>|ST|<systime>|STAMP|<Wiener Lokalzeit>|IP|<ip>|HOST|<host>
  |USER|<user>|NAME|<Wiki-Name>|ACTION|<rekonstruierte URL>|TS|<unix-utc>

Erzeugt je Monat ein Parquet in artefakte/betreiberlog/req_<monat>.parquet mit
Spalten: ts, ip, ip16, user, name, script, kind, page, query, diff, raw_action.

Klassifikation (kind):
  write     form_edit=1 oder action=form_edit            -> Schreibversuch
  editform  action=edit                                  -> Editformular (liefert Seitentext!)
  browse    action=browse                                -> Lesen
  raw       action=raw                                   -> Lesen (Rohtext)
  bare      ?PageName oder ?PageName=                    -> Lesen (ProWiki-Kurzform)
  archive_page  action=archive&cmd=page&version=X          -> Lesen einer Altversion
  archive_list  action=archive&cmd=list                    -> Versionsliste (Metadaten)
  rc        action=rc                                     -> Aenderungsstrom (Feed)
  search    keywords= / search=                          -> Suche
  prefs     action=editprefs
  other     alles uebrige

Lauf:  .venv/bin/python scripts/betreiberlog/70_parse.py
"""
from __future__ import annotations
import os, re, sys, collections
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(os.path.dirname(HERE))          # analyse/
LOGDIR = os.path.join(BASE, "data", "betreiberlogs")
OUTDIR = os.path.join(BASE, "artefakte", "betreiberlog")
os.makedirs(OUTDIR, exist_ok=True)

MONTHS = ["2604", "2605", "2606", "2607"]
PATHRE = re.compile(r"^https?://[^/]+/(?:htdocs/)?(?:wikise/)?([A-Za-z0-9_]+)/(wiki2?)\.cgi(.*)$", re.S)


def unq(s: str) -> str:
    # minimal, defensiv: %XX und + nur wo noetig; wir brauchen vor allem Seitennamen
    if "%" in s:
        try:
            from urllib.parse import unquote
            s = unquote(s, encoding="iso-8859-1", errors="replace")
        except Exception:
            pass
    return s


def parse_line(line: str):
    """-> dict oder None"""
    if not line.startswith("#DONE2|"):
        return None
    head, _, tail = line.rpartition("|TS|")
    if not tail:
        return None
    try:
        ts = int(tail.strip())
    except ValueError:
        return None
    pre, _, action = head.partition("|ACTION|")
    f = pre.split("|")
    # f: 0 #DONE2, 1 1, 2 UT, 3 ut, 4 ST, 5 st, 6 STAMP, 7 stamp, 8 IP, 9 ip,
    #    10 HOST, 11 host, 12 USER, 13 user, 14 NAME, 15 name
    if len(f) < 16:
        return None
    ip, user, name = f[9], f[13], f[15]
    m = PATHRE.match(action)
    if not m:
        return dict(ts=ts, ip=ip, user=user, name=name, wiki="", script="",
                    kind="unparsed", page="", query="", diff=False)
    wiki, script, rest = m.group(1), m.group(2), m.group(3)
    q = rest[1:] if rest.startswith("?") else ""
    q = q.replace("&amp;", "&")
    params = {}
    bare = []
    for part in q.split("&"):
        if not part:
            continue
        k, eq, v = part.partition("=")
        if eq and v:
            params.setdefault(k, v)
        else:
            bare.append(k)
            if eq:
                params.setdefault(k, "")
    act = params.get("action", "")
    page = unq(params.get("id", ""))
    diff = "diff" in params
    query = ""
    if params.get("form_edit") == "1" or act == "form_edit":
        kind = "write"
        page = unq(params.get("id", "") or params.get("incoming", ""))
    elif act == "edit":
        kind = "editform"
    elif act == "browse":
        kind = "browse"
    elif act == "raw":
        kind = "raw"
    elif act == "archive":
        cmd = params.get("cmd", "")
        kind = "archive_page" if cmd == "page" else ("archive_list" if cmd == "list" else "archive_other")
    elif act == "rc":
        kind = "rc"
    elif act == "editprefs":
        kind = "prefs"
    elif "keywords" in params or "search" in params:
        kind = "search"
        query = unq(params.get("keywords", "") or params.get("search", ""))
    elif act:
        kind = "other:" + act[:20]
    elif bare:
        cand = [b for b in bare if b and not b.islower()]
        if cand:
            kind = "bare"
            page = unq(cand[0])
        else:
            kind = "other"
    else:
        kind = "other"
    if not page and "id" in params:
        page = unq(params["id"])
    return dict(ts=ts, ip=ip, user=user, name=name, wiki=wiki, script=script,
                kind=kind, page=page, query=query, diff=diff)


def main():
    tot = collections.Counter()
    for mon in MONTHS:
        path = os.path.join(LOGDIR, "log_" + mon)
        if not os.path.exists(path):
            print("fehlt:", path); continue
        rows = []
        bad = 0
        with open(path, "r", encoding="iso-8859-1", errors="replace") as fh:
            for line in fh:
                r = parse_line(line)
                if r is None:
                    bad += 1
                    continue
                rows.append(r)
        df = pd.DataFrame(rows)
        for c in ("ip", "user", "name", "wiki", "script", "kind", "page", "query"):
            df[c] = df[c].fillna("")
        df["ip16"] = df.ip.str.split(".").str[:2].str.join(".")
        df["ts"] = df.ts.astype("int64")
        for c in ("user", "name", "wiki", "script", "kind"):
            df[c] = df[c].astype("category")
        out = os.path.join(OUTDIR, f"req_{mon}.parquet")
        df.to_parquet(out, index=False)
        print(f"{mon}: {len(df):,} Zeilen, {bad} unlesbar -> {out}")
        print("   kind:", dict(df.kind.value_counts().head(12)))
        print("   wiki:", dict(df.wiki.value_counts().head(5)))
        print("   NAME gesetzt:", int((df.name.astype(str) != '').sum()),
              f"({(df.name.astype(str)!='').mean()*100:.1f} %)")
        tot.update(df.kind.astype(str).value_counts().to_dict())
    print("\nGESAMT kind:", dict(tot.most_common()))


if __name__ == "__main__":
    main()
