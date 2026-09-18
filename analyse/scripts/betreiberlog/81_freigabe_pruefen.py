#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
81_freigabe_pruefen.py -- zweiter Durchlauf ueber den Flottenausschnitt, der
der Bauregel nicht glaubt.

`80_freigabe_flotte.py` behauptet: keine Volladresse, kein Seitentext, nur
Flottenbloecke, nur das Vorfallsfenster. Dieses Skript prueft jede dieser
Behauptungen noch einmal an den gebauten Dateien selbst -- ohne den Filter des
Bauskripts zu benutzen, mit eigenen Mustern und eigenen Grenzen. Es entspricht
dem zweiten Schwaerzungsdurchlauf, den das Paper fuer die Tabellen faehrt
(`paper/main.tex` §Data and code availability: "a second pass re-scans the built
tree without trusting the policy").

Aufruf:
    analyse/.venv/bin/python analyse/scripts/betreiberlog/81_freigabe_pruefen.py

Rueckgabe: 0 wenn alle Proben aufgehen, sonst 1.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import pyarrow.parquet as pq

BASE = Path(__file__).resolve().parents[3]
FREI = BASE / "analyse" / "data" / "betreiberlogs" / "freigabe"
NETZ = BASE / "analyse" / "artefakte" / "betreiberlog_identitaet" / "bi07_netzklassen.csv"

# Eigene Muster, absichtlich weiter gefasst als die des Bauskripts.
IPV4 = re.compile(r"(?<![0-9.])\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?![0-9.])")
TEXTP = re.compile(r"(?:^|&)text=([^&]*)")
REF = re.compile(r"^log_260[4-7]\|\d+\|\d+\|[0-9a-f]{12}$")

LO = int(datetime(2026, 5, 24, 5, 55, 31, tzinfo=timezone.utc).timestamp())
HI = int(datetime(2026, 7, 2, 23, 59, 59, tzinfo=timezone.utc).timestamp())

TEXTSPALTEN = ["ip16", "host", "host_raw", "script", "wiki", "name",
               "action_kind", "action_raw", "action_detail", "page_id", "raw_params"]


def main():
    bloecke = {r["ip16"] for r in csv.DictReader(NETZ.open(encoding="utf-8"))
               if r["klasse"] == "flotte"}
    befund = {
        "zeilen": 0,
        "volladresse_irgendwo": 0,
        "seitentext_nicht_NN": 0,
        "block_nicht_flotte": 0,
        "zeit_ausserhalb_fenster": 0,
        "verweis_unlesbar": 0,
        "spalte_ip_vorhanden": 0,
        "spalte_client_host_vorhanden": 0,
        "adr_ids": 0,
        "fremde_bloecke": [],
    }
    fremd = set()
    ids = set()

    for p in sorted(FREI.glob("flotte_requests_26*.parquet")):
        pf = pq.ParquetFile(p)
        felder = set(pf.schema_arrow.names)
        befund["spalte_ip_vorhanden"] += int("ip" in felder)
        befund["spalte_client_host_vorhanden"] += int("client_host" in felder)
        for b in pf.iter_batches(batch_size=100_000):
            d = b.to_pydict()
            befund["zeilen"] += len(d["ts_utc"])
            for ts in d["ts_utc"]:
                if not (LO <= ts <= HI):
                    befund["zeit_ausserhalb_fenster"] += 1
            for pre in d["ip16"]:
                if pre not in bloecke:
                    befund["block_nicht_flotte"] += 1
                    fremd.add(pre)
            ids.update(d["adr_id"])
            for ref in d["rec_ref"]:
                if not REF.match(ref or ""):
                    befund["verweis_unlesbar"] += 1
            for q in d["raw_params"]:
                for v in TEXTP.findall((q or "").replace("&amp;", "&")):
                    if v != "(NN)":
                        befund["seitentext_nicht_NN"] += 1
            for sp in TEXTSPALTEN:
                for wert in d[sp]:
                    if wert and IPV4.search(wert):
                        befund["volladresse_irgendwo"] += 1

    befund["adr_ids"] = len(ids)
    befund["fremde_bloecke"] = sorted(fremd)[:20]

    schlecht = [k for k in ("volladresse_irgendwo", "seitentext_nicht_NN",
                            "block_nicht_flotte", "zeit_ausserhalb_fenster",
                            "verweis_unlesbar", "spalte_ip_vorhanden",
                            "spalte_client_host_vorhanden") if befund[k]]
    befund["urteil"] = "bestanden" if not schlecht else "durchgefallen: " + ", ".join(schlecht)
    (FREI / "freigabe_pruefung.json").write_text(
        json.dumps(befund, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(befund, indent=1, ensure_ascii=False))
    return 0 if not schlecht else 1


if __name__ == "__main__":
    sys.exit(main())
