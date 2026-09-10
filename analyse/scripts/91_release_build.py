#!/usr/bin/env python3
"""
91_release_build.py — baut den veroeffentlichungsfaehigen Abzug des Artefaktbestands.

Regel, die das Paper sich selbst gibt ("Data and code availability"): weitergegeben
werden abgeleitete Ergebnisse und der Code, NICHT der Wiki-Abzug und kein Seitentext
darueber hinaus. Mehrere abgeleitete Tabellen tragen aber Volltext; sie waeren eine
Teil-Weitergabe des Abzugs.

Dieses Skript loest das, ohne Reproduzierbarkeit aufzugeben:

  * Zelle fuer Zelle wird geprueft, ob ihr Inhalt woertlich im Abzug steht.
  * Steht er dort, wird die Zelle geleert und in einer Parallelspalte "<name>_ref"
    ein Verweis abgelegt: revision|feld|versatz|laenge|sha256-12.
  * Steht er nicht dort, ist es unser eigener Text und bleibt unveraendert.
  * Zwischenstufen, die den ganzen Korpus tragen (die Parquet-Dateien), werden gar
    nicht ausgeliefert; die nummerierten Skripte bauen sie aus dem Abzug neu.

Wer den Abzug bei seinen Urhebern herunterlaedt, stellt mit rebuild_text.py den
vollen Bestand wieder her. Wer ihn nicht hat, sieht keinen Seitentext.

Ausgabe: analyse/release/dist/            (der veroeffentlichungsfaehige Baum)
         analyse/release/redaktionsprotokoll.csv
Lauf:    analyse/.venv/bin/python scripts/91_release_build.py
"""
import csv, hashlib, json, shutil, sys, time
from pathlib import Path
import pandas as pd

B    = Path(__file__).resolve().parents[1]          # analyse/
ROOT = B.parent                                      # Projektwurzel
A    = B / "artefakte"
R    = B / "release"
DIST = R / "dist"
csv.field_size_limit(sys.maxsize)

# ---------------------------------------------------------------- Regelwerk
POLICY = json.loads((R / "policy.json").read_text(encoding="utf-8"))
AUSSCHLUSS   = set(POLICY["ausschluss"])
NUR_ORG      = POLICY["nur_organisation"]           # {datei: [spalte, ...]}
NIE_PRUEFEN  = {(d, s) for d, s in POLICY["nie_pruefen"]}

MIN_LEN, MIN_SPACE, FENSTER = 40, 3, 60

def log(*a): print(*a, flush=True)

# ---------------------------------------------------------------- Abzug
log("Abzug laden ...")
rev = pd.read_parquet(A / "schwarm_deltas.parquet",
                      columns=["rev_id", "page_key", "label", "time", "body", "delta"])
rev["body"] = rev["body"].fillna(""); rev["delta"] = rev["delta"].fillna("")
TXT = {r.rev_id: {"delta": r.delta, "body": r.body} for r in rev.itertuples()}

import bisect
def heuhaufen(series):
    parts, offs, ids, pos = [], [], [], 0
    for rid, t in zip(rev["rev_id"], series):
        parts.append(t); offs.append(pos); ids.append(rid); pos += len(t) + 1
    return "\x00".join(parts), offs, ids
HAY = {f: heuhaufen(rev[f]) for f in ("delta", "body")}

def sha12(s): return hashlib.sha256(s.encode("utf-8")).hexdigest()[:12]

def in_revision(rid, wert):
    d = TXT.get(rid)
    if not d: return None
    for feld in ("delta", "body"):
        p = d[feld].find(wert)
        if p >= 0: return feld, rid, p
    return None

def global_suche(wert):
    for feld in ("delta", "body"):
        hay, offs, ids = HAY[feld]
        p = hay.find(wert)
        if p < 0: continue
        i = bisect.bisect_right(offs, p) - 1
        return feld, ids[i], p - offs[i]
    return None

# Manche Tabellen speichern Zeilenumbrueche als Trennzeichen. Der Text steht dann
# im Abzug, aber nicht in dieser Schreibweise. Die angewandte Umformung wird im
# Verweis mitgefuehrt, damit der Rueckbau die Zelle zeichengenau herstellt.
UMFORMUNGEN = (("roh", None), ("sp_cr_sp", " ⏎ "), ("cr", "⏎"), ("sp_pipe_sp", " | "))

def _varianten(v):
    for name, trenn in UMFORMUNGEN:
        if trenn is None:
            yield v, name
        elif trenn in v:
            yield v.replace(trenn, "\n"), name

import re
REV_TOKEN = re.compile(r"[A-Za-z0-9_]+~[^\s·|]+?@\d+")
PAGE_TOKEN = re.compile(r"(?:dse|dorfwiki|[a-z]+)~[A-Za-z0-9_~%\-\.]+")

# Nachschlagewerke, damit eine Zelle ohne rev_id-Spalte trotzdem auf wenige
# Revisionen eingegrenzt werden kann -- dann darf die Suche in ihr erschoepfend
# sein, statt den ganzen Korpus im Raster abzutasten.
NACH_SEITE = {}
for _r in rev.itertuples():
    NACH_SEITE.setdefault(_r.page_key, []).append(_r.rev_id)

def _kandidaten(wert, rid):
    """Revisionen, in denen der Text dieser Zelle plausibel steht."""
    ids = []
    if rid:
        ids.append(rid)
    for t in REV_TOKEN.findall(wert)[:4]:            # "dse~Seite@7" steht oft in der Zelle
        if t in TXT:
            ids.append(t)
    if not ids:
        for t in PAGE_TOKEN.findall(wert)[:2]:       # sonst wenigstens die Seite
            for i in NACH_SEITE.get(t.split("@")[0], [])[:40]:
                ids.append(i)
    out, gesehen = [], set()
    for i in ids:
        if i in gesehen or i not in TXT:
            continue
        gesehen.add(i)
        out.append(i)
    return out[:40]

def _wortgrenzen(v):
    """Startpositionen fuer die Ankersuche: jeder Wortanfang. Damit wird kein
    eingebettetes Zitat mehr verfehlt, wie es ein festes Raster tut."""
    yield 0
    for i in range(1, len(v)):
        if v[i - 1].isspace() and not v[i].isspace():
            yield i

MARKE = "\ue000"   # Platzhalter fuer eine herausgeloeste Passage

def _passt(v, rid, kand=None):
    for k in (kand or ([rid] if rid else [])):
        t = in_revision(k, v)
        if t:
            return t
    return global_suche(v)

def _maximaler_span(v, rid, kand=None):
    """Laengste zusammenhaengende Passage in v, die woertlich im Abzug steht.
    -> (lo, hi, feld, rev_id, versatz) oder None.
    Der Bereich gueltiger Grenzen ist zusammenhaengend (jedes Teilstueck eines
    Treffers ist selbst ein Treffer), deshalb genuegt je Seite eine Halbierung."""
    n = len(v)
    if n < FENSTER:
        t = _passt(v, rid, kand)
        return (0, n, t[0], t[1], t[2]) if t else None
    anker = None
    for i in _wortgrenzen(v):
        if i > n - FENSTER:
            break
        if _passt(v[i:i + FENSTER], rid, kand):
            anker = i
            break
    if anker is None:
        return None
    hi = anker + FENSTER
    lo, a, b = anker, 0, anker          # groesstes Stueck nach links
    while a < b:
        m = (a + b) // 2
        if _passt(v[m:hi], rid, kand): b = m
        else: a = m + 1
    lo = a
    a, b = hi, n                        # groesstes Stueck nach rechts
    while a < b:
        m = (a + b + 1) // 2
        if _passt(v[lo:m], rid, kand): a = m
        else: b = m - 1
    hi = a
    t = _passt(v[lo:hi], rid, kand)
    if not t:
        return None
    return (lo, hi, t[0], t[1], t[2])

def verweis(wert, rid=None):
    """-> (neuer_zellwert, ref, art).

    ganz        der Wert ist selbst Abzugstext  -> Zelle leer, ein Verweis
    teilstueck  der Wert umschliesst Abzugstext -> nur die Passage weicht einer
                Marke, unser eigener Rahmen bleibt stehen
    None        eigener Text                    -> unveraendert
    """
    kand = _kandidaten(wert, rid)
    for v, form in _varianten(wert):
        t = _passt(v, rid, kand)
        if t:
            feld, r, off = t
            return "", f"{r}|{feld}|{off}|{len(v)}|{sha12(v)}|{form}", "ganz"

    rest, refs, marken = wert, [], 0
    while marken < 40:
        sp = _maximaler_span(rest, rid, kand)
        if not sp:
            break
        lo, hi, feld, r, off = sp
        stueck = rest[lo:hi]
        refs.append(f"{r}|{feld}|{off}|{len(stueck)}|{sha12(stueck)}|roh")
        rest = rest[:lo] + MARKE + rest[hi:]
        marken += 1
    # Schlusspruefung. Steht nach allen herausgeloesten Passagen noch Abzugstext im
    # Rest -- weil eine Zelle sehr viele Fundstellen zusammenfasst oder weil das Zitat
    # nur in umgeformter Schreibweise auftaucht --, faellt die ganze Zelle. Lieber ein
    # Verweis ohne Zeichenspanne als ein Rest, den der Waechter findet.
    def _rest_traegt_text(r):
        for v, _ in _varianten(r):
            if _maximaler_span(v, rid, kand):
                return True
        return False

    if _rest_traegt_text(rest):
        return "", f"-|-|-1|{len(wert)}|{sha12(wert)}|roh", "unlokalisiert"
    if refs:
        return rest, ";".join(refs), "teilstueck"
    return None, None, None

ORG_MARKER = ("corporation", "corp", "inc", "llc", "ltd", "limited", "gmbh", "company",
              "co.", "s.a", "b.v", "abuse", "hostmaster", "registry", "network", "noc",
              "tech", "routing", "peering", "dns", "administrator", "operations",
              "support", "team", "communications", "telecom", "hosting", "cloud",
              "services", "university", "institute", "foundation", "association")

def _ist_organisation(t):
    """Registry-Handle (kein Leerzeichen) oder Organisationsname -- alles andere ist
    ein Klarname einer natuerlichen Person und faellt raus."""
    t = t.strip()
    if not t:
        return False
    if " " not in t:
        return True                       # ARIN/RIPE-Handles: BEDAR6-ARIN, MSFT
    return any(m in t.lower() for m in ORG_MARKER)

def nur_organisation(v):
    """Entfernt Klarnamen natuerlicher Personen aus einem RDAP-Eintragsfeld."""
    s = "" if v is None else str(v)
    if not s.strip():
        return s
    return "|".join(t for t in s.split("|") if _ist_organisation(t))

def kandidatenspalte(vals):
    """Kann in dieser Spalte ueberhaupt Abzugstext stehen?

    Frueher entschied der Mittelwert der Wortzahl ueber die ganze Spalte. Das hat
    Spalten uebersehen, in denen nur einzelne Zeilen einen Satz tragen und alle
    uebrigen eine Kennung -- der Waechter hat genau solche Faelle gefunden. Jetzt
    genuegt eine einzige Zelle, die aussieht wie Text; entschieden wird ohnehin je
    Zelle."""
    for x in vals:
        if x is None: continue
        t = str(x)
        if len(t) >= MIN_LEN and t.count(" ") >= MIN_SPACE:
            return True
    return False

# ---------------------------------------------------------------- Bauen
if DIST.exists(): shutil.rmtree(DIST)
(DIST / "artefakte").mkdir(parents=True)

protokoll = []
dateien = sorted(p for p in A.rglob("*") if p.is_file())
t0 = time.time()

for p in dateien:
    relp = str(p.relative_to(A))
    ziel = DIST / "artefakte" / relp
    ziel.parent.mkdir(parents=True, exist_ok=True)

    if relp in AUSSCHLUSS:
        protokoll.append(dict(datei=relp, spalte="*", aktion="ausgeschlossen",
                              grund="Korpus-Zwischenstufe, wird von den Skripten neu gebaut"))
        continue
    if p.suffix not in (".csv", ".parquet"):
        shutil.copy2(p, ziel)                      # Berichte, Logs, Codebook, JSON
        continue

    df = (pd.read_csv(p, dtype=str, keep_default_na=False, engine="python")
          if p.suffix == ".csv" else pd.read_parquet(p))

    hat_rev = "rev_id" in df.columns
    for c in list(df.columns):
        if (relp, str(c)) in NIE_PRUEFEN: continue
        if relp in NUR_ORG and str(c) in NUR_ORG[relp]:
            df[c] = df[c].map(nur_organisation)
            protokoll.append(dict(datei=relp, spalte=str(c), aktion="personennamen entfernt",
                                  zeilen=len(df),
                                  grund="RDAP-Kontaktnamen sind personenbezogen (Ethik-Abschnitt des Papers)"))
            continue
        if not kandidatenspalte(df[c].tolist()): continue

        refs, n_tref, arten = [], 0, {}
        rid_col = df["rev_id"].tolist() if hat_rev else [None]*len(df)
        neue = []
        for v, rid in zip(df[c].tolist(), rid_col):
            s = "" if v is None else str(v)
            if s.strip() in ("", "nan", "None") or len(s) < MIN_LEN or s.count(" ") < 2:
                neue.append(s); refs.append(""); continue
            neu_s, ref, art = verweis(s, rid if isinstance(rid, str) and rid else None)
            if ref:
                neue.append(neu_s); refs.append(ref); n_tref += 1
                arten[art] = arten.get(art, 0) + 1
            else:
                neue.append(s); refs.append("")
        if n_tref:
            df[c] = neue
            df.insert(df.columns.get_loc(c) + 1, f"{c}_ref", refs)
            protokoll.append(dict(datei=relp, spalte=str(c), aktion="ersetzt",
                                  zeilen=len(df), ersetzt=n_tref,
                                  grund=";".join(f"{k}={v}" for k, v in sorted(arten.items()))))
    if p.suffix == ".csv":
        df.to_csv(ziel, index=False)
    else:
        df.to_parquet(ziel, index=False)
    log(f"  {relp}  ({time.time()-t0:.0f}s)")

pd.DataFrame(protokoll).to_csv(R / "redaktionsprotokoll.csv", index=False)
log(f"\nProtokoll: {R/'redaktionsprotokoll.csv'}")
log(f"ersetzt in {sum(1 for r in protokoll if r['aktion']=='ersetzt')} Spalten, "
    f"{sum(r.get('ersetzt',0) or 0 for r in protokoll)} Zellen; "
    f"{len(AUSSCHLUSS)} Dateien ausgeschlossen. {time.time()-t0:.0f}s")
