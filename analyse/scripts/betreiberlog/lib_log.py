# -*- coding: utf-8 -*-
"""Gemeinsamer Streaming-Parser fuer die Betreiber-Requestlogs (log_26MM).
Zeilenformat:
#DONE2|1|UT|<f>|ST|<f>|STAMP|<lokal>|IP|<ip>|HOST|<host>|USER|<u>|NAME|<n>|ACTION|<url>|TS|<unix-utc>
ACTION kann selbst '|' enthalten -> von hinten nach TS splitten, von vorne nach den Feldern.
"""
from __future__ import annotations
import io, os, re, hashlib, datetime as dt

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "betreiberlogs")
DATA = os.path.normpath(DATA)
LOGS = {"2604": "log_2604", "2605": "log_2605", "2606": "log_2606", "2607": "log_2607"}
REFS = {"2604": "refer_2604", "2605": "refer_2605", "2606": "refer_2606", "2607": "refer_2607"}

FIELD_RX = re.compile(
    r"^#DONE2\|(?P<n>[^|]*)\|UT\|(?P<ut>[^|]*)\|ST\|(?P<st>[^|]*)\|STAMP\|(?P<stamp>[^|]*)"
    r"\|IP\|(?P<ip>[^|]*)\|HOST\|(?P<host>[^|]*)\|USER\|(?P<user>[^|]*)\|NAME\|(?P<name>[^|]*)"
    r"\|ACTION\|(?P<action>.*)\|TS\|(?P<ts>-?\d+)\s*$"
)
HOST_RX = re.compile(r"^https?://([^/]+)(/[^?]*)?(?:\?(.*))?$", re.S)


def iter_log(month, lineno_start=1):
    """Yield (lineno, rec) streaming. rec: dict mit ts(int), ip, host, user, name, action,
    vhost, path, query, stamp."""
    path = os.path.join(DATA, LOGS[month])
    with io.open(path, "r", encoding="iso-8859-1", errors="replace", newline="") as fh:
        for i, line in enumerate(fh, lineno_start):
            m = FIELD_RX.match(line)
            if not m:
                continue
            d = m.groupdict()
            act = d["action"]
            hm = HOST_RX.match(act)
            vhost = (hm.group(1).lower() if hm else "")
            path_ = (hm.group(2) or "") if hm else ""
            query = (hm.group(3) or "") if hm else ""
            yield i, {
                "lineno": i, "ts": int(d["ts"]), "ip": d["ip"], "rhost": d["host"],
                "user": d["user"], "name": d["name"], "action": act, "stamp": d["stamp"],
                "vhost": vhost, "path": path_, "query": query,
            }


def utc(ts):
    return dt.datetime.utcfromtimestamp(ts).strftime("%Y-%m-%dT%H:%M:%SZ")


def to_ts(s):
    """'2026-05-24T05:57:02Z' -> int"""
    return int(dt.datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc).timestamp())


def site(vhost):
    """Farm-Host normalisieren."""
    v = vhost
    if v.startswith("www."):
        v = v[4:]
    return v


def anon(ip):
    """/24 + Salt-freier Kurzhash; fuer Cloud-Praefixe der Flotte wird die IP separat gezeigt."""
    parts = ip.split(".")
    if len(parts) == 4:
        return parts[0] + "." + parts[1] + ".x.x#" + hashlib.sha1(ip.encode()).hexdigest()[:6]
    return "ip#" + hashlib.sha1(ip.encode()).hexdigest()[:8]


def slash16(ip):
    p = ip.split(".")
    return ".".join(p[:2]) if len(p) == 4 else ip
