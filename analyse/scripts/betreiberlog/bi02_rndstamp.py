#!/usr/bin/env python3
"""bi02 — Formular-Token (rndstamp) als Container-Kennung.

ProWiki rendert das Bearbeitungsformular mit zwei versteckten Feldern:
  oldtime=<Zeitstempel der Vorversion der Seite>   (seitenspezifisch)
  rndstamp=<Zufallszahl, bei jedem Formular-Render neu> (formularspezifisch)
Beide kommen beim Speichern wieder mit.  Mehrere Speicher-Requests mit demselben
rndstamp stammen daher aus EINEM Formular-Abruf, also aus EINEM Prozess —
unabhaengig davon, von welcher IP und unter welchem Namen sie eintreffen.

Aufruf:
  analyse/.venv/bin/python analyse/scripts/betreiberlog/bi02_rndstamp.py

Ausgabe: analyse/data/betreiberlogs/normalisiert/bi_save_<monat>.tsv.gz
Spalten : ts ip name page rndstamp oldtime summary_len script
"""
import gzip, os, re, sys, urllib.parse

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC  = os.path.join(BASE, "data", "betreiberlogs")
DST  = os.path.join(SRC, "normalisiert")
MONATE = ["log_2604", "log_2605", "log_2606", "log_2607"]
SAFE = re.compile(r"[\t\r\n]")


def lauf(fn):
    src = os.path.join(SRC, fn)
    dst = os.path.join(DST, "bi_save_" + fn.replace("log_", "") + ".tsv.gz")
    n = 0
    with open(src, "rb") as f, gzip.open(dst, "wt", encoding="utf-8", compresslevel=6) as out:
        out.write("ts\tip\tname\tpage\trndstamp\toldtime\tsummary\tscript\n")
        for raw in f:
            if b"form_edit" not in raw:
                continue
            s = raw.decode("iso-8859-1").rstrip("\n")
            if not s.startswith("#DONE2|"):
                continue
            p = s.split("|")
            d = dict(zip(p[2::2], p[3::2]))
            if not d.get("TS", "").isdigit():
                continue
            a = d.get("ACTION", "")
            q = a.split("?", 1)[1] if "?" in a else ""
            qd = {}
            for kv in q.split("&"):
                if "=" in kv:
                    k, v = kv.split("=", 1)
                    if k not in qd:
                        qd[k] = urllib.parse.unquote_plus(v)
            if "form_edit" not in qd and qd.get("action") != "form_edit":
                continue
            name = d.get("NAME", "") or qd.get("username", "")
            out.write("\t".join(SAFE.sub(" ", x)[:200] for x in (
                d["TS"], d.get("IP", ""), name, qd.get("id", ""),
                qd.get("rndstamp", ""), qd.get("oldtime", ""),
                qd.get("summary", ""), "wiki2" if "wiki2.cgi" in a else "wiki")) + "\n")
            n += 1
    print(f"{fn}: {n} Speicher-Requests -> {dst}", flush=True)


if __name__ == "__main__":
    for fn in (sys.argv[1:] or MONATE):
        lauf(fn)
