#!/usr/bin/env python3
"""
10_normalisieren.py -- Normalisiert die Betreiber-Requestlogs (log_26MM) zu Parquet.

Aufruf:
  .venv/bin/python analyse/scripts/betreiberlog/10_normalisieren.py

Eingabe : analyse/data/betreiberlogs/log_2604 .. log_2607   (ISO-8859-1)
Ausgabe : analyse/data/betreiberlogs/normalisiert/requests_26MM.parquet
          analyse/data/betreiberlogs/normalisiert/parse_report.json

Datensatzformat der Quelle (eine Zeile je Request, ABER: das ACTION-Feld kann
sowohl '|' als auch Zeilenumbrueche enthalten -- deshalb wird ein Datensatz
ueber den Anker '^#DONE2|' bis '|TS|<digits>$' zusammengesetzt):

  #DONE2|1|UT|<usertime>|ST|<systime>|STAMP|<Wiener Lokalzeit>|IP|<ip>|HOST|<host>
        |USER|<user>|NAME|<wikiname>|ACTION|<rekonstruierte URL>|TS|<unix-utc>

KLASSIFIZIERUNGSREGELN (action_kind), in dieser Reihenfolge ausgewertet:

  R1 write      : Query enthaelt den Parameter 'form_edit'  ODER action in
                  {form_edit, save}.  Begruendung: der Speicher-Request des
                  ProWiki-Editformulars traegt 'form_edit=1&action=form_edit'
                  (Beleg: log_2606, Datensatz mit TS 1780267187).
  R2 delete     : action == 'delete'.
  R3 editprefs  : action in {editprefs, form_editprefs} ODER Parameter
                  'form_editprefs' vorhanden.
  R4 search     : action in {search, form_search, fullsearch} ODER Parameter
                  'keywords' oder 'search' vorhanden.
  R5 read       : action in {browse, raw}  (enge Definition des Betreibers)
                  ODER gar kein 'action'-Parameter vorhanden -> "browse-bare"
                  (dieselbe Vokabel benutzt der publizierte Export in
                  events.jsonl, Feld request_action).
  R6 other      : alles uebrige (action=edit = Anzeige des Editformulars,
                  archive, rc, history, diff, wpx, spx, login, rss, ...).
                  Die feine Auspraegung steht in 'action_raw' / 'action_detail'.

  Die HTTP-Methode ist aus der rekonstruierten URL NICHT ableitbar; es wird
  nirgends GET/POST behauptet.

page_id-Ableitung (Spalte page_id), in dieser Reihenfolge:
  P1 Parameter 'id'
  P2 Parameter 'oldid'
  P3 bei "browse-bare" der erste Parameter-Schluessel mit leerem Wert
     (Form '?SeitenName=') bzw. eine Query ganz ohne '=' ('?SeitenName')
  sonst leer.

script : letzter Pfadbestandteil (wiki.cgi / wiki2.cgi)
wiki   : Pfadsegment vor dem Skript (in diesen Logs durchgaengig 'dse')
host   : URL-netloc, kleingeschrieben, ohne fuehrendes 'www.' und ohne Port
         (wikiservice.at / prowiki.org / wikiservice.com / ...); host_raw haelt
         den Rohwert.
client_host : das HOST-Feld der Logzeile = Client-Host/IP des Betreiber-Logs.
killed : True, wenn das HOST-Feld die Betreibermarkierung ' KILLED' traegt
         (der Request wurde serverseitig abgebrochen).
"""
import json, re, sys, unicodedata, urllib.parse
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

BASE = Path(__file__).resolve().parents[3]
DATA = BASE / "analyse" / "data" / "betreiberlogs"
OUT = DATA / "normalisiert"
OUT.mkdir(parents=True, exist_ok=True)

REC = re.compile(
    r"^#DONE2\|(?P<v>[^|]*)\|UT\|(?P<ut>[^|]*)\|ST\|(?P<st>[^|]*)\|STAMP\|(?P<stamp>[^|]*)"
    r"\|IP\|(?P<ip>[^|]*)\|HOST\|(?P<host>[^|]*)\|USER\|(?P<user>[^|]*)\|NAME\|(?P<name>[^|]*)"
    r"\|ACTION\|(?P<action>.*)\|TS\|(?P<ts>\d+)$",
    re.S,
)
TAIL = re.compile(r"\|TS\|\d+$")

SEARCH_ACTIONS = {"search", "form_search", "fullsearch"}
READ_ACTIONS = {"browse", "raw"}
PREF_ACTIONS = {"editprefs", "form_editprefs"}

SCHEMA = pa.schema([
    ("ts_utc", pa.int64()),
    ("ip", pa.string()),
    ("host", pa.string()),
    ("host_raw", pa.string()),
    ("client_host", pa.string()),
    ("killed", pa.bool_()),
    ("script", pa.string()),
    ("wiki", pa.string()),
    ("name", pa.string()),
    ("action_kind", pa.string()),
    ("action_raw", pa.string()),
    ("action_detail", pa.string()),
    ("page_id", pa.string()),
    ("raw_params", pa.string()),
    ("src_file", pa.string()),
    ("rec_no", pa.int64()),
])


def parse_query(q):
    """Split query string into ordered (key, value) pairs. '&amp;' is an
    artefact of the operator's URL reconstruction and is treated as '&'."""
    q = q.replace("&amp;", "&")
    out = []
    for kv in q.split("&"):
        if kv == "":
            continue
        if "=" in kv:
            k, v = kv.split("=", 1)
        else:
            k, v = kv, None
        out.append((k, v))
    return out


def classify(params, pmap):
    act = pmap.get("action") or ""
    act = act.strip().strip("'\"")
    if "form_edit" in pmap or act in ("form_edit", "save"):
        return "write", act, "form_edit"
    if act == "delete":
        return "delete", act, "delete"
    if act in PREF_ACTIONS or "form_editprefs" in pmap:
        return "editprefs", act, act or "form_editprefs"
    if act in SEARCH_ACTIONS or "keywords" in pmap or "search" in pmap:
        detail = "keywords" if "keywords" in pmap else ("search" if "search" in pmap else act)
        return "search", act, detail
    if act in READ_ACTIONS:
        return "read", act, act
    if "action" not in pmap:
        return "read", "", "browse-bare"
    return "other", act, act


def page_of(pmap, params, kind, detail):
    if pmap.get("id"):
        return pmap["id"]
    if pmap.get("oldid"):
        return pmap["oldid"]
    if detail == "browse-bare":
        for k, v in params:
            if v in (None, ""):
                return k
    return ""


def norm_host(h):
    h = h.strip().split(" ")[0].lower()
    if ":" in h:
        h = h.split(":", 1)[0]
    if h.startswith("www."):
        h = h[4:]
    return h


def iter_records(src, stats=None):
    """Streamt die Rohdatei und liefert (rec_no, rec) je vollstaendig
    zusammengesetztem Datensatz.  rec_no zaehlt NUR geglueckte Datensaetze und
    ist damit derselbe Schluessel, den die Parquet-Spalte rec_no traegt.
    stats (dict, optional) nimmt physical_lines / unparsed_fragments /
    multiline_records auf.  Es wird nie mehr als ein Datensatz gehalten."""
    st = stats if stats is not None else {}
    st.setdefault("physical_lines", 0)
    st.setdefault("unparsed_fragments", 0)
    st.setdefault("multiline_records", 0)
    buf = []
    n_rec = 0
    with open(src, "rb") as fh:
        for raw in fh:
            st["physical_lines"] += 1
            line = raw.decode("iso-8859-1").rstrip("\r\n")
            if line.startswith("#DONE2|") and buf:
                st["unparsed_fragments"] += 1      # previous fragment never terminated
                buf = []
            if line.startswith("#DONE2|") or buf:
                buf.append(line)
            else:
                st["unparsed_fragments"] += 1
                continue
            if not TAIL.search(line):
                continue
            rec = "\n".join(buf)
            if len(buf) > 1:
                st["multiline_records"] += 1
            buf = []
            if not REC.match(rec):
                st["unparsed_fragments"] += 1
                continue
            n_rec += 1
            yield n_rec, rec
    if buf:
        st["unparsed_fragments"] += 1
    st["records"] = n_rec


def run():
    report = {}
    for fn in ["log_2604", "log_2605", "log_2606", "log_2607"]:
        src = DATA / fn
        writer = pq.ParquetWriter(OUT / f"requests_{fn.split('_')[1]}.parquet", SCHEMA,
                                  compression="zstd")
        stats = {}
        batch = {f.name: [] for f in SCHEMA}

        def flush():
            nonlocal batch
            if not batch["ts_utc"]:
                return
            writer.write_table(pa.table({k: pa.array(v, type=SCHEMA.field(k).type)
                                         for k, v in batch.items()}, schema=SCHEMA))
            batch = {f.name: [] for f in SCHEMA}

        for n_rec, rec in iter_records(src, stats):
            m = REC.match(rec)
            url = m.group("action")
            u = urllib.parse.urlsplit(url)
            path = u.path
            seg = [s for s in path.split("/") if s]
            script = seg[-1] if seg else ""
            wiki = seg[-2] if len(seg) >= 2 else ""
            params = parse_query(u.query)
            pmap = {}
            for k, v in params:
                pmap.setdefault(k, v if v is not None else "")
            kind, act_raw, detail = classify(params, pmap)
            pid = page_of(pmap, params, kind, detail)
            batch["ts_utc"].append(int(m.group("ts")))
            batch["ip"].append(m.group("ip").strip())
            batch["host"].append(norm_host(u.netloc))
            batch["host_raw"].append(u.netloc)
            ch = m.group("host").strip()
            batch["client_host"].append(ch.split(" ")[0])
            batch["killed"].append(" KILLED" in ch)
            batch["script"].append(script)
            batch["wiki"].append(wiki)
            batch["name"].append(m.group("name").strip())
            batch["action_kind"].append(kind)
            batch["action_raw"].append(act_raw)
            batch["action_detail"].append(detail)
            batch["page_id"].append(pid[:512])
            batch["raw_params"].append(u.query[:4000])
            batch["src_file"].append(fn)
            batch["rec_no"].append(n_rec)
            if len(batch["ts_utc"]) >= 200000:
                flush()
        flush()
        writer.close()
        report[fn] = {"physical_lines": stats["physical_lines"], "records": stats["records"],
                      "multiline_records": stats["multiline_records"],
                      "unparsed_fragments": stats["unparsed_fragments"]}
        print(fn, report[fn], flush=True)
    (OUT / "parse_report.json").write_text(json.dumps(report, indent=2))


if __name__ == "__main__":
    run()
