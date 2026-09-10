"""Erzeugt die ECharts-Datensaetze fuer den Blogartikel aus den Analyse-Artefakten.

Ausgabe: philflow.io/src/public/charts/<id>.json  (publicDir -> /dist/charts/<id>.json)
Jede Datei ist reine DATEN plus Achsenbeschriftung. Das Aussehen kommt aus dem
ECharts-Theme, nicht von hier.
"""
import csv, json, os
from collections import defaultdict
from datetime import datetime

import pathlib as _pl; _BASE = str(_pl.Path(__file__).resolve().parent.parent)  # analyse/ (skript-relativ)
A = _BASE+"/artefakte"
# Ziel des Website-Exports. Standard ist ein Verzeichnis im Projekt; wer woanders
# hin exportieren will, setzt CHARTS_OUT -- kein absoluter Pfad im Quelltext.
OUT = os.environ.get("CHARTS_OUT", _BASE + "/artefakte/charts")
os.makedirs(OUT, exist_ok=True)

def rows(name):
    with open(os.path.join(A, name), newline="") as f:
        return list(csv.DictReader(f))

def write(name, obj):
    p = os.path.join(OUT, name + ".json")
    with open(p, "w") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
    print(f"{name:16s} {os.path.getsize(p):>7,} B")

def hhmm(ts):
    return datetime.fromisoformat(ts.replace("Z", "+00:00")).strftime("%H:%M")

# 1 Ausbreitung des Exploits: Stufenlinie kumulierter Agenten
r = rows("exploit_propagation.csv")
t0 = datetime.fromisoformat(r[0]["time"].replace("Z", "+00:00"))
pts, seen = [], None
for x in r:
    t = datetime.fromisoformat(x["time"].replace("Z", "+00:00"))
    mins = round((t - t0).total_seconds() / 60, 2)
    if mins > 95:
        break
    c = int(x["cum_unique_labels"])
    if c != seen:
        pts.append([mins, c, hhmm(x["time"]), x["label"]])
        seen = c
write("ausbreitung", {
    "type": "step",
    "xName": "Minuten nach dem ersten Beitrag",
    # Der Artikel warnt ausdruecklich davor, Benutzernamen fuer Agenten zu halten
    # (Namensfeld frei ausfuellbar) - deshalb zaehlt die Achse Namen, nicht Agenten.
    "yName": "Namen, die die Methode verwenden",
    "points": pts,
    # Die Markierungslinien tragen ihre Beschriftung selbst; `place` sagt, an
    # welchem Ende der Linie sie sitzt. Der Renderer liest `markLines`.
    "markLines": [
        {"x": 17.9, "place": "start", "label": "17 min 54 s\nerste Bestätigung"},
        {"x": 90, "place": "end", "label": "90 min\n21 Agenten"},
    ],
})
# Englische Fassung: identische Zahlen, nur die Textfelder uebersetzt. Die
# englische Artikelfassung referenziert die Diagramm-ID mit Suffix "-en".
write("ausbreitung-en", {
    "type": "step",
    "xName": "Minutes after the first post",
    "yName": "Names using the method",
    "points": pts,
    "markLines": [
        {"x": 17.9, "place": "start", "label": "17 min 54 s\nfirst confirmation"},
        {"x": 90, "place": "end", "label": "90 min\n21 agents"},
    ],
})

# 2 Umgehungswege: horizontale Balken, log-Skala. Das Wiki selbst ist kein Umgehungsweg.
r = [x for x in rows("harness_network_infra.csv") if x["mechanism"] != "wikiservice.at"]
r.sort(key=lambda x: int(x["n_revs"]))
write("allowlist", {
    "type": "bar-h-log",
    "xName": "Beiträge (logarithmisch)",
    "items": [{
        "name": x["mechanism"],
        "value": int(x["n_revs"]),
        "labels": int(x["n_labels"]),
        "first": x["first_time"][:10],
        "hero": x["mechanism"] in ("blob.core.windows.net", "/etc/hosts", "NO_PROXY", "--resolve", "Host header override"),
    } for x in r],
})

# 3 Zwei Populationen pro Tag
r = rows("schwarm_populationen_taeglich.csv")
write("populationen", {
    "type": "bar-stack",
    "yName": "Beiträge mit neuem Text",
    "dates": [x["time"] for x in r],
    "series": [
        {"name": "Umgehungswerkzeug", "data": [int(x["proxy_pop"]) for x in r]},
        {"name": "Verabredung", "data": [int(x["coord_pop"]) for x in r]},
    ],
})

# 4 Konsenssturz: zwei Linien, stuendlich, nur das aktive Fenster
r = [x for x in rows("schwarm_rundungsstreit_stuendlich.csv")
     if int(x["alt"]) or int(x["neu"])]
_times = [x["time"][:16] for x in r]
_alt = [int(x["alt"]) for x in r]
_neu = [int(x["neu"]) for x in r]
write("konsenssturz", {
    "type": "line2",
    "yName": "Beiträge pro Stunde",
    "times": _times,
    "series": [
        {"name": "9,90 / 16,40 (Konsens)", "data": _alt},
        {"name": "9,91 / 16,38 (belegt)", "data": _neu},
    ],
    "mark": {"time": "2026-06-20 04:00", "label": "04:56 der Beweis"},
})
# Englische Fassung. Zeitwerte bleiben sprachneutral; der Dezimaltrenner der
# Preisangaben wechselt vom Komma zum Punkt.
write("konsenssturz-en", {
    "type": "line2",
    "yName": "Posts per hour",
    "times": _times,
    "series": [
        {"name": "9.90 / 16.40 (consensus)", "data": _alt},
        {"name": "9.91 / 16.38 (proven)", "data": _neu},
    ],
    "mark": {"time": "2026-06-20 04:00", "label": "04:56 the proof"},
})

# 5 Formkonvergenz: Signaturanteil je 6-h-Fenster, nur Fenster mit n>=20
r = [x for x in rows("schwarm_konvergenz_6h.csv") if int(x["n"]) >= 20]
write("form", {
    "type": "line-pct",
    "yName": "Anteil Beiträge mit Unterschrift",
    "times": [x["time"][:16] for x in r],
    "values": [round(float(x["sig"]) * 100, 1) for x in r],
    "labels": [int(x["labels"]) for x in r],
    "n": [int(x["n"]) for x in r],
    "firstLabel": "{v} % im\nallerersten Fenster",
})

# 6 Kollision auf der Willkommensseite: nur der 18. Juni, der Tag der Kollision.
# Die restlichen 28 Bearbeitungen liegen Tage spaeter und wuerden die Achse
# auf 17 Tage strecken, in denen nichts passiert.
r = [x for x in rows("willkommen_timeline.csv") if x["time"][:10] == "2026-06-18"]
t0 = datetime.fromisoformat(r[0]["time"].replace("Z", "+00:00"))
prev, pts, shrink = None, [], 0
for x in r:
    t = datetime.fromisoformat(x["time"].replace("Z", "+00:00"))
    n = int(x["body_len"])
    # 1 = diese Bearbeitung hat die Seite verkuerzt, also fremden Text
    # ueberschrieben. Das ist die eigentliche Aussage des Bildes.
    cut = 1 if (prev is not None and n < prev) else 0
    shrink += cut
    pts.append([round((t - t0).total_seconds() / 60, 2), n, cut, hhmm(x["time"])])
    prev = n
write("kollision", {
    "type": "scatter",
    "xName": "Minuten seit der ersten Bearbeitung am 18. Juni",
    "yName": "Seitengröße in Bytes",
    "points": pts,
    "n": len(pts),
    "shrink": shrink,
    "xMax": round(max(p[0] for p in pts)),
})

# 7 Loeschschlacht: Schreibvorgaenge gegen Loeschungen
r = rows("wiki_daily.csv")
_dates = [x["date"] for x in r]
_saves = [int(x["saves"]) for x in r]
_deletes = [int(x["deletes"]) for x in r]
write("loeschschlacht", {
    "type": "line2-axis",
    "dates": _dates,
    "series": [
        {"name": "Bearbeitungen der Agenten (linke Achse)", "data": _saves, "axis": 0},
        {"name": "Löschungen des Moderators (rechte Achse)", "data": _deletes, "axis": 1},
    ],
    # Marke "letzter Tag der Agenten" entfernt: vom Artikel nicht gedeckt und den
    # eigenen Daten widersprechend (saves am 2026-07-01: 7, am 2026-07-02: 14).
})
# Englische Fassung. Die Datumswerte sind ISO-Strings und bleiben sprachneutral.
write("loeschschlacht-en", {
    "type": "line2-axis",
    "dates": _dates,
    "series": [
        {"name": "Edits by the agents (left axis)", "data": _saves, "axis": 0},
        {"name": "Deletions by the moderator (right axis)", "data": _deletes, "axis": 1},
    ],
})

# 8 Selbstvermessung: Anteil reiner Umgebungsarbeit je Tag.
# Nur die koordinierende Population. Der 18. und der 22.06. stehen in derselben
# Datei, gehoeren aber zur zweiten, nicht koordinierenden Population (Egress-
# Werkzeugtest, BERICHT_ml_verhalten.md Abschnitt 3) und wuerden als Balken
# derselben Reihe einen Einbruch dieser Kurve behaupten, den es nicht gibt.
# Deshalb sind sie ausgelassen statt gezeichnet: das Bild macht genau eine
# Aussage ueber genau eine Population.
_KOORD = ("2026-06-16", "2026-06-17", "2026-06-19", "2026-06-20", "2026-06-21")
r = [x for x in rows("paper_ml_envcore_taeglich.csv") if x["day"] in _KOORD]
r.sort(key=lambda x: x["day"])
_tage = [x["day"] for x in r]
_anteil = [round(float(x["core_share"]) * 100, 1) for x in r]
_beitraege = [int(x["n"]) for x in r]
write("selbstvermessung", {
    "type": "line-pct",
    "yName": "Anteil reiner Umgebungsarbeit",
    "valueName": "Umgebungsarbeit",
    "times": _tage,
    "values": _anteil,
    "n": _beitraege,
    "highlight": len(_anteil) - 1,
    "firstLabel": "{v} % am letzten Tag",
})
# Englische Fassung: identische Zahlen, nur die Textfelder uebersetzt.
write("selbstvermessung-en", {
    "type": "line-pct",
    "yName": "Share of pure environment work",
    "valueName": "environment work",
    "times": _tage,
    "values": _anteil,
    "n": _beitraege,
    "highlight": len(_anteil) - 1,
    "firstLabel": "{v} % on the last day",
})
