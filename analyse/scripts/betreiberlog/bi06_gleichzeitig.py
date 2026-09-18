#!/usr/bin/env python3
"""bi06 — Wie viele Container liefen gleichzeitig? Drei unabhaengige Wege.

Weg A  Namensgleichzeitigkeit: distinkte Namen mit >=1 Request in einem Fenster.
Weg B  Sitzungsrekonstruktion je Name (Lueckenschwelle g); ueberlappende Sitzungen zaehlen.
Weg C  Little'sches Gesetz auf Requestrate: Flottenrate R(t) geteilt durch die
       gemessene Requestrate eines einzelnen aktiven Namens r.

Aufruf:
  analyse/.venv/bin/python analyse/scripts/betreiberlog/bi06_gleichzeitig.py 2606
Ausgabe: analyse/artefakte/betreiberlog_identitaet/bi06_*.csv|json
"""
import csv, collections, gzip, json, os, sys
import numpy as np

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NORM = os.path.join(BASE, "data", "betreiberlogs", "normalisiert")
ART  = os.path.join(BASE, "artefakte", "betreiberlog_identitaet")
FLOTTE_16 = None   # wird aus bi07 geladen, falls vorhanden


def lade(m, nur_benannt=True):
    ev = collections.defaultdict(list)     # name -> [ts]
    alle = []
    with gzip.open(os.path.join(NORM, f"bi_{m}.tsv.gz"), "rt", encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE):
            ts = int(r["ts"])
            alle.append(ts)
            if r["name"] and r["namensquelle"] == "name":
                ev[r["name"]].append(ts)
    for k in ev: ev[k].sort()
    alle.sort()
    return ev, np.array(alle, dtype=np.int64)


def weg_a(ev, W):
    """max. Zahl distinkter Namen in einem Fenster der Breite W Sekunden."""
    punkte = []
    for n, ts in ev.items():
        # jeder Name traegt Intervalle [t, t+W] bei; Sweep ueber Namenspraesenz
        letzte = -10**12
        for t in ts:
            if t - letzte > W:
                punkte.append((t, +1)); punkte.append((t + W, -1))
                letzte = t
            else:
                # verlaengert das laufende Intervall
                punkte[-1] = (t + W, -1)
                letzte = t
    punkte.sort()
    cur = best = 0; bt = None
    for t, d in punkte:
        cur += d
        if cur > best: best, bt = cur, t
    return best, bt


def weg_b(ev, g):
    """Sitzungen je Name bei Lueckenschwelle g; max. Ueberlappung."""
    sess = []
    for n, ts in ev.items():
        s = ts[0]; p = ts[0]
        for t in ts[1:]:
            if t - p > g:
                sess.append((s, p, n)); s = t
            p = t
        sess.append((s, p, n))
    punkte = sorted([(a, 1) for a, b, n in sess] + [(b, -1) for a, b, n in sess])
    cur = best = 0; bt = None
    for t, d in punkte:
        cur += d
        if cur > best: best, bt = cur, t
    return len(sess), best, bt


def weg_c(ev, alle, fenster=300):
    """Little: Flottenrate / Einzelrate."""
    # Einzelrate: fuer jede Namens-Sitzung (Lueecke<=120 s, >=5 Requests) Requests/s
    raten = []
    for n, ts in ev.items():
        s = ts[0]; p = ts[0]; k = 1
        for t in ts[1:]:
            if t - p > 120:
                if k >= 5 and p > s: raten.append(k / (p - s))
                s = t; k = 1
            else: k += 1
            p = t
        if k >= 5 and p > s: raten.append(k / (p - s))
    r = float(np.median(raten)) if raten else float("nan")
    # Flottenrate: benannte Requests je Fenster
    bts = np.sort(np.concatenate([np.array(v) for v in ev.values()])) if ev else np.array([])
    if len(bts) == 0: return r, 0, 0, None
    b0, b1 = bts[0], bts[-1]
    bins = np.arange(b0, b1 + fenster, fenster)
    h, _ = np.histogram(bts, bins=bins)
    i = int(h.argmax())
    R = h[i] / fenster
    return r, len(raten), R / r if r else float("nan"), int(bins[i])


if __name__ == "__main__":
    out = {}
    for m in (sys.argv[1:] or ["2605", "2606"]):
        ev, alle = lade(m)
        o = {"monat": m, "namen": len(ev), "benannte_requests": sum(len(v) for v in ev.values())}
        for W in (60, 300, 3600):
            b, t = weg_a(ev, W)
            o[f"A_max_namen_fenster{W}s"] = b
            o[f"A_zeitpunkt{W}s"] = t
        for g in (300, 900, 3600):
            ns, b, t = weg_b(ev, g)
            o[f"B_sitzungen_g{g}s"] = ns
            o[f"B_max_ueberlappend_g{g}s"] = b
            o[f"B_zeitpunkt_g{g}s"] = t
        r, nr, conc, tw = weg_c(ev, alle)
        o.update(C_einzelrate_req_pro_s=round(r, 4), C_n_sitzungen_gemessen=nr,
                 C_gleichzeitig=round(conc, 1), C_fenster_start=tw)
        out[m] = o
        print(json.dumps(o, indent=1), flush=True)
    json.dump(out, open(os.path.join(ART, "bi06_gleichzeitig.json"), "w"), indent=1)
