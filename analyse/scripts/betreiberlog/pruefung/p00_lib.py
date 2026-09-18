#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
p00_lib.py — gemeinsame Bausteine der Gegenpruefung der Lesemessung.

Rekonstruiert die Definitionen aus 71_lesespalte.py exakt (READ_CONTENT,
BIT-Maske, meldeformat(), mask_at(), wilson(), rd_ci()) und macht sie
parametrisierbar: Leseklassen-Menge, Vorlauf-Fenster, Seiten-Scope.

Nichts hier veraendert bestehende Artefakte. Nur Lesen.
"""
from __future__ import annotations
import os, glob, math
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))   # analyse/
ART = os.path.join(BASE, "artefakte")
OUT = os.path.join(ART, "betreiberlog")
PRUEF = os.path.join(OUT, "pruefung")
DATA = os.path.join(BASE, "data")
os.makedirs(PRUEF, exist_ok=True)

# --- 71_lesespalte.py:52-55 wortgleich ---------------------------------------
READ_CONTENT = {"browse", "raw", "editform", "bare", "archive_page"}
READ_STRICT = {"browse", "raw"}
FEEDKINDS = {"rc", "other:rss", "other:recentchanges"}
FEEDPAGES = {"RecentChanges", "AktuelleAenderungen"}

# --- 71_lesespalte.py:159-169 wortgleich -------------------------------------
BASIS = ["sig_endzeile", "please_relay", "cohort", "runde", "state_conf", "uhrenpaar", "zeitstempel"]
BIT = {k: 1 << i for i, k in enumerate(BASIS)}
MERKMALE = ["runde", "cohort", "meldeformat", "sig_endzeile", "please_relay"]
HERKUNFT = {"runde": "erfunden", "cohort": "erfunden", "meldeformat": "erfunden",
            "sig_endzeile": "mitgebracht", "please_relay": "mitgebracht"}


def meldeformat(mask):
    return bool(mask & BIT["sig_endzeile"]) and bool(mask & (BIT["uhrenpaar"] | BIT["zeitstempel"])) \
        and bool(mask & (BIT["runde"] | BIT["state_conf"] | BIT["cohort"]))


def hasm(mask, m):
    return meldeformat(mask) if m == "meldeformat" else bool(mask & BIT[m])


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"),) * 3
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p * 100, (c - h) * 100, (c + h) * 100


def rd_ci(k1, n1, k0, n0, z=1.96):
    if n1 == 0 or n0 == 0:
        return (float("nan"),) * 3
    p1, p0 = k1 / n1, k0 / n0
    se = math.sqrt(p1 * (1 - p1) / n1 + p0 * (1 - p0) / n0)
    return (p1 - p0) * 100, (p1 - p0 - z * se) * 100, (p1 - p0 + z * se) * 100


# =============================================================== Laden
def lade():
    req = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(os.path.join(OUT, "req_*.parquet")))],
                    ignore_index=True)
    for c in ("name", "kind", "page", "wiki", "script", "query", "ip", "ip16"):
        req[c] = req[c].astype(str)
    ix = pd.read_parquet(os.path.join(ART, "paper_exposition_index.parquet"))
    ix["time"] = pd.to_datetime(ix["time"], utc=True)
    coord = pd.read_csv(os.path.join(OUT, "kernmessung_namen.csv"))
    return req, ix, coord


def seitenzustand(ix):
    """PSTATE wie 71_lesespalte.py:172-177."""
    ixd = ix[ix.page_key.str.startswith("dse~")].sort_values(["page_key", "time"], kind="mergesort")
    ps = {}
    for pk, g in ixd.groupby("page_key", sort=False):
        ps[pk[4:]] = (g.time.values.astype("datetime64[s]").astype(np.int64),
                      g.mask_body.values.astype(np.int64))
    return ps


def mask_at_factory(PSTATE):
    def mask_at(page, ts):
        e = PSTATE.get(page)
        if e is None:
            return -1
        times, masks = e
        j = np.searchsorted(times, ts, side="right") - 1
        return int(masks[j]) if j >= 0 else 0
    return mask_at


def vier_felder(coord, gelesen_col, ad_col):
    g = coord[gelesen_col].values.astype(bool)
    a = coord[ad_col].values.astype(bool)
    n11, n10 = int((g & a).sum()), int((g & ~a).sum())
    n01, n00 = int((~g & a).sum()), int((~g & ~a).sum())
    r, lo, hi = rd_ci(n11, n11 + n10, n01, n01 + n00)
    return dict(n_gelesen=n11 + n10, p_ad_gelesen=(n11 / (n11 + n10) * 100) if n11 + n10 else float("nan"),
                n_nicht=n01 + n00, p_ad_nicht=(n01 / (n01 + n00) * 100) if n01 + n00 else float("nan"),
                rd=r, rd_lo=lo, rd_hi=hi)
