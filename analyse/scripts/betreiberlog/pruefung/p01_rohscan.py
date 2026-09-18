#!/usr/bin/env python3
"""p01_rohscan.py -- Annahmen-Audit, Durchlauf 1: Rohstruktur der Betreiberlogs.

Read-only. Schreibt NUR nach
analyse/betreiberlogs-befunde/rohdaten-pruefung/p01_rohscan.json

Geprueft werden (je Monatsdatei):
  A  Satzstruktur: physische Zeilen, Datensaetze, mehrzeilige Datensaetze,
     Datensaetze mit einem zweiten '#DONE2|' im Inneren (Spleiss-Test fuer
     nicht-gesperrtes Anhaengen, wiki.pl:4988 FileAppStr ohne flock).
  B  TS-Semantik: TS gegen STAMP (Wiener Lokalzeit), Sekundenabweichung.
  C  Reihenfolge: TS gegen Dateireihenfolge (Rueckwaertsspruenge = Differenz
     zwischen Prozessstart $^T und Zeitpunkt des Anhaengens).
  D  Luecken in der Zeitachse (Abstaende aufeinanderfolgender Sekunden).
  E  Dubletten: exakt identische Datensaetze.
  F  ' KILLED': Anzahl, Aufteilung nach Aktionsart (grob ueber die Query),
     Namensbesetzung, Zeitverteilung.
  G  IP-Feld mit '#CookieID' (wiki.pl:18661) und USER-Feld-Besetzung.
  H  UT/ST-Verteilung.
  I  Monatszugehoerigkeit: min/max TS je Datei.
"""
import io, json, os, re, sys, hashlib, datetime as dt
from collections import Counter, defaultdict
from zoneinfo import ZoneInfo

BASE = "/home/philflow/Dokumente/coding/research/agent-swarm-forensics"
DATA = os.path.join(BASE, "analyse", "data", "betreiberlogs")
OUT = os.path.join(BASE, "analyse", "betreiberlogs-befunde", "rohdaten-pruefung")
os.makedirs(OUT, exist_ok=True)

REC = re.compile(
    r"^#DONE2\|(?P<v>[^|]*)\|UT\|(?P<ut>[^|]*)\|ST\|(?P<st>[^|]*)\|STAMP\|(?P<stamp>[^|]*)"
    r"\|IP\|(?P<ip>[^|]*)\|HOST\|(?P<host>[^|]*)\|USER\|(?P<user>[^|]*)\|NAME\|(?P<name>[^|]*)"
    r"\|ACTION\|(?P<action>.*)\|TS\|(?P<ts>\d+)$", re.S)
TAIL = re.compile(r"\|TS\|\d+$")
VIENNA = ZoneInfo("Europe/Vienna")
MON = {"Januar": 1, "Februar": 2, "M\xe4rz": 3, "April": 4, "Mai": 5, "Juni": 6,
       "Juli": 7, "August": 8, "September": 9, "Oktober": 10, "November": 11, "Dezember": 12}
STAMP_RX = re.compile(r"^(\d{1,2})\.\s*([A-Za-z\xe4\xf6\xfc]+)\s+(\d{4})\s+(\d{1,2}):(\d{2})$")


def stamp_to_utc(s):
    m = STAMP_RX.match(s.strip())
    if not m:
        return None
    d, mon, y, hh, mm = m.groups()
    if mon not in MON:
        return None
    try:
        local = dt.datetime(int(y), MON[mon], int(d), int(hh), int(mm), tzinfo=VIENNA)
    except ValueError:
        return None
    return int(local.timestamp())


def scan(fn):
    path = os.path.join(DATA, fn)
    st = dict(physical_lines=0, records=0, multiline=0, spliced=0, unparsed=0)
    stamp_mismatch = Counter()
    stamp_examples = []
    back_jumps = Counter()
    back_max = (0, None)
    gaps = []
    dup_hash = {}
    dups = 0
    dup_examples = []
    killed = 0
    killed_kind = Counter()
    killed_named = 0
    killed_by_day = Counter()
    kind_all = Counter()
    ip_hash = 0
    user_set = 0
    v_field = Counter()
    ut = Counter()
    stt = Counter()
    ts_min, ts_max = None, None
    prev_ts = None
    same_ts_ip = Counter()
    ml_examples = []
    seen = set()

    buf = []
    with open(path, "rb") as fh:
        for raw in fh:
            st["physical_lines"] += 1
            line = raw.decode("iso-8859-1").rstrip("\r\n")
            if line.startswith("#DONE2|") and buf:
                st["unparsed"] += 1
                buf = []
            if line.startswith("#DONE2|") or buf:
                buf.append(line)
            else:
                st["unparsed"] += 1
                continue
            if not TAIL.search(line):
                continue
            rec = "\n".join(buf)
            nbuf = len(buf)
            buf = []
            m = REC.match(rec)
            if not m:
                st["unparsed"] += 1
                continue
            st["records"] += 1
            if nbuf > 1:
                st["multiline"] += 1
                if len(ml_examples) < 12:
                    ml_examples.append({"rec_no": st["records"], "lines": nbuf,
                                        "len": len(rec), "text": rec[:400]})
            if "#DONE2|" in rec[1:]:
                st["spliced"] += 1

            ts = int(m.group("ts"))
            ts_min = ts if ts_min is None else min(ts_min, ts)
            ts_max = ts if ts_max is None else max(ts_max, ts)

            # B  STAMP
            su = stamp_to_utc(m.group("stamp"))
            if su is None:
                stamp_mismatch["unparsebar"] += 1
            else:
                d = ts - su
                if not (0 <= d < 60):
                    stamp_mismatch["abweichend"] += 1
                    if len(stamp_examples) < 10:
                        stamp_examples.append({"stamp": m.group("stamp"), "ts": ts, "delta": d})
                else:
                    stamp_mismatch["passt"] += 1

            # C  Reihenfolge
            if prev_ts is not None:
                d = ts - prev_ts
                if d < 0:
                    b = -d
                    back_jumps[min(b, 3600) if b < 3600 else 3600] += 1
                    if b > back_max[0]:
                        back_max = (b, {"rec_no": st["records"], "ts": ts, "prev_ts": prev_ts})
                elif d > 60:
                    gaps.append((prev_ts, ts, d))
            prev_ts = ts

            # E  Dubletten
            h = hashlib.blake2b(rec.encode("iso-8859-1"), digest_size=8).digest()
            if h in seen:
                dups += 1
                if len(dup_examples) < 5:
                    dup_examples.append(rec[:300])
            else:
                seen.add(h)

            # F  KILLED
            ch = m.group("host")
            act = m.group("action")
            q = act.split("?", 1)[1] if "?" in act else ""
            ql = q.replace("&amp;", "&")
            if "form_edit" in ql or "action=form_edit" in ql or "action=save" in ql:
                kind = "write"
            elif "action=delete" in ql:
                kind = "delete"
            elif "action=browse" in ql or "action=raw" in ql or "action=" not in ql:
                kind = "read"
            elif "action=search" in ql or "keywords=" in ql or "search=" in ql:
                kind = "search"
            else:
                kind = "other"
            kind_all[kind] += 1
            if " KILLED" in ch:
                killed += 1
                killed_kind[kind] += 1
                if m.group("name").strip():
                    killed_named += 1
                killed_by_day[dt.datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d")] += 1

            # G
            if "#" in m.group("ip"):
                ip_hash += 1
            if m.group("user").strip():
                user_set += 1
            v_field[m.group("v")] += 1

            # H
            ut[m.group("ut")] += 1
            stt[m.group("st")] += 1

            # I  gleicher TS + gleiche IP (Prozessstart-Quantisierung)
            same_ts_ip[(ts, m.group("ip"))] += 1

    multi = sum(1 for v in same_ts_ip.values() if v > 1)
    gaps.sort(key=lambda t: -t[2])
    return {
        "datei": fn,
        "A_struktur": st,
        "A_mehrzeilig_beispiele": ml_examples,
        "B_stamp": dict(stamp_mismatch), "B_stamp_beispiele": stamp_examples,
        "C_rueckwaerts": {"anzahl": sum(back_jumps.values()),
                          "max_sek": back_max[0], "max_kontext": back_max[1],
                          "histogramm_sek": dict(sorted(back_jumps.items())[:40])},
        "D_luecken_top20": [{"von_utc": dt.datetime.utcfromtimestamp(a).isoformat() + "Z",
                             "bis_utc": dt.datetime.utcfromtimestamp(b).isoformat() + "Z",
                             "sekunden": c} for a, b, c in gaps[:20]],
        "D_luecken_gesamt_ueber_60s": len(gaps),
        "E_dubletten": {"anzahl": dups, "beispiele": dup_examples},
        "F_killed": {"anzahl": killed, "nach_art": dict(killed_kind),
                     "mit_namen": killed_named,
                     "top_tage": killed_by_day.most_common(10)},
        "F_alle_arten": dict(kind_all),
        "G_ip_mit_raute": ip_hash, "G_user_gesetzt": user_set,
        "G_v_feld": dict(v_field.most_common(10)),
        "H_ut_top": ut.most_common(8), "H_st_top": stt.most_common(8),
        "I_ts": {"min": dt.datetime.utcfromtimestamp(ts_min).isoformat() + "Z",
                 "max": dt.datetime.utcfromtimestamp(ts_max).isoformat() + "Z"},
        "I_ts_ip_mehrfach": multi,
    }


if __name__ == "__main__":
    res = {}
    for fn in ["log_2604", "log_2605", "log_2606", "log_2607"]:
        res[fn] = scan(fn)
        print(fn, "fertig", res[fn]["A_struktur"], flush=True)
    with open(os.path.join(OUT, "p01_rohscan.json"), "w") as fh:
        json.dump(res, fh, indent=1, ensure_ascii=False)
    print("geschrieben:", os.path.join(OUT, "p01_rohscan.json"))
