#!/usr/bin/env python3
"""Reproduce aggregate corrections for the reviewed v4 manuscript.

Run from any directory with analyse/.venv/bin/python. Requires the local
normalised logs and the existing read-analysis artefacts (71 and pruefung/p10).
Writes aggregates only; no names, addresses or source-record locators.
Intervals are unadjusted Wald intervals assuming independent names, not causal
or cluster-adjusted intervals. The historical-page state assignments are reused,
not independently reconstructed here.
"""
from pathlib import Path
import json
import math
import sys

import duckdb
import pandas as pd
from scipy.stats import fisher_exact

HERE = Path(__file__).resolve().parent
ANALYSE = HERE.parents[1]
OUT = ANALYSE / "artefakte" / "betreiberlog"
sys.path.insert(0, str(HERE / "pruefung"))
from u00_lib import con  # read-only view; same fleet classifier and time window


def comparison(coord, requests, definition):
    hit = set(requests.loc[requests.c_runde, "name"])
    adopted = coord.ad_runde.astype(bool)
    requested = coord.label.isin(hit)
    k1, n1 = int((adopted & requested).sum()), int(adopted.sum())
    k0, n0 = int((~adopted & requested).sum()), int((~adopted).sum())
    p1, p0 = k1 / n1, k0 / n0
    se = math.sqrt(p1 * (1 - p1) / n1 + p0 * (1 - p0) / n0)
    return {
        "definition": definition,
        "adopters_requested": k1, "adopters": n1,
        "nonadopters_requested": k0, "nonadopters": n0,
        "request_prevalence_difference_pp": 100 * (p1 - p0),
        "independent_names_wald_ci95_pp": [
            100 * (p1 - p0 - 1.96 * se), 100 * (p1 - p0 + 1.96 * se)
        ],
        "fisher_two_sided_p": float(fisher_exact(
            [[k1, n1 - k1], [k0, n0 - k0]], alternative="two-sided"
        ).pvalue),
        "expected_if_equal_request_prevalence": n1 * p0,
    }


def main():
    coord = pd.read_csv(OUT / "kernmessung_namen.csv")
    coord = coord[coord.coordpop.astype(bool)].copy()
    pages = dict(zip(coord.label, coord.seite_rev.str.removeprefix("dse~")))
    requests = pd.read_parquet(OUT / "pruefung" / "lesezugriffe_coordpop.parquet")
    requests = requests[(requests.lead > 0) & (requests["mask"] > 0)]
    eligible = coord[~coord.exp_runde.astype(bool)]
    foreign_first = requests[requests.page != requests.name.map(pages)]
    comparisons = [
        comparison(eligible, foreign_first, "exclude_first_written_page"),
        comparison(eligible, requests[~requests.eigene], "exclude_every_ever_written_page"),
    ]
    c = con()
    parser_pattern = str(OUT / "req_*.parquet")
    names = c.execute("""
        WITH n AS (
          SELECT name, bool_or(kind='write') w, bool_or(kind='editform') e
          FROM read_parquet(?) WHERE name<>'' GROUP BY name
        ) SELECT count(*), sum((NOT w)::INT), sum((NOT w AND NOT e)::INT) FROM n
    """, [parser_pattern]).fetchone()
    rejected = c.execute("""
        SELECT count(*) FILTER (WHERE killed),
          count(*) FILTER (WHERE killed AND ts_utc BETWEEN 1779602131 AND 1783036799),
          count(*) FILTER (WHERE flotte), count(*) FILTER (WHERE flotte AND killed)
        FROM rx
    """).fetchone()
    minute = c.execute("""
        WITH m AS (
          SELECT ip, floor(ts_utc/60) minute_bucket, count(*) n
          FROM rx WHERE flotte GROUP BY 1,2
        ) SELECT avg(n), max(n) FROM m
    """).fetchone()
    permutation = pd.read_csv(OUT / "pruefung" / "n_permutation.csv")
    marker = permutation[permutation.merkmal.eq("runde")].iloc[0]
    result = {
        "comparisons": comparisons,
        "named_population_read_parser": {
            "all": names[0], "never_save": names[1],
            "neither_save_nor_edit_form": names[2],
        },
        "request_counts_release_normalizer": {
            "rejected_four_months": rejected[0], "rejected_incident_window": rejected[1],
            "classified_fleet": rejected[2], "classified_fleet_rejected": rejected[3],
        },
        "classified_fleet_occupied_minute_bins": {"mean": minute[0], "maximum": minute[1]},
        "round_marker_permutation": {
            "observed_rd_pp": float(marker.beobachtet_rd),
            "null_mean_rd_pp": float(marker.null_rd_mittel),
            "null_p975_rd_pp": float(marker.null_rd_p97_5),
            "draws": 200, "zero_exceedances_plus_one_p": 1 / 201,
        },
        "limits": [
            "Exploratory comparison; independent-name intervals; no causal identification.",
            "Ever-written-page sensitivity conditions on later activity.",
            "Reuse of historical-state assignments does not verify returned content.",
            "Fleet classification uses provider prefixes and an incident window.",
        ],
    }
    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    (OUT / "cross_review_summary.json").write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
