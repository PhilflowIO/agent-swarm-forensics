# The Mechanics of a Swarm — analysis pipeline and derived artefacts

Reproduction material for

> Philipp Lütje. *The Mechanics of a Swarm: A Reproducible External Reconstruction
> of an Unintended Agent-Coordination Episode on a Third-Party Wiki.*

Between 24 May and 2 July 2026, several thousand autonomous agents wrote to a
small public wiki that nobody had pointed them at. This repository contains every
script that produced a number in that paper, every derived table those numbers are
read from, the gold set with its codebook and both raters' codings, and the detail
reports with their ambiguity lists.

It does **not** contain the wiki export. That export is not ours to redistribute.

---

## What is here

| Path | |
|---|---|
| `analyse/scripts/` | the analysis pipeline, `01` … `93`, run in numeric order |
| `analyse/artefakte/` | every derived table, report and figure input |
| `analyse/data/` | empty — this is where *you* put the export |
| `analyse/rebuild_text.py` | restores page text into the tables (see below) |
| `analyse/release/` | the redaction policy and its audit trail |
| `paper/` | `main.tex`, bibliography, and every table and figure it prints |
| `MECHANIK.md` | the German synthesis every number in the paper is read from |

## Reproducing the paper

```bash
# 1. get the export from its authors
#    https://collusion.wiki/explorer/download.html
#    unpack into analyse/data/ and check it:
cd analyse/data && sha256sum -c SHA256SUMS && cd ..

# 2. environment
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 3. run the pipeline in numeric order, from analyse/
for s in scripts/[0-9]*.py; do .venv/bin/python "$s"; done

# 4. put the page text back into the tables that carry it
.venv/bin/python rebuild_text.py
```

Steps 3 and 4 are independent: step 3 regenerates the artefacts from the export,
step 4 fills the redacted text columns of the shipped ones. Either alone gives you
the complete tables; running both is the cross-check.

## Why some columns are empty

The paper releases derived results and code, not the export and not page text
beyond the short agent-written quotations it uses as evidence. Several derived
tables would break that rule on their own — the gold set is 400 wiki sentences,
and one intermediate table carries the entire corpus.

So the release does two things:

**Five intermediate files are not shipped at all.** `schwarm_revisions.parquet`,
`schwarm_deltas.parquet`, `schwarm_deltas_flags.parquet`,
`paper_lernkurve_revflags.parquet` and `paper_themen_flags.parquet` together hold
about 28 MB of page text. `scripts/30_load.py`, `32_delta.py`,
`34_reziprozitaet.py`, `41_lernkurve.py` and `55_dramaturgie.py` rebuild them from
the export in minutes.

**Text cells elsewhere are replaced by a reference.** Every cell was checked
against the export character by character. Where it matched, the cell was emptied
and a parallel `<column>_ref` column records where the text sits:

```
revision | field | offset | length | sha256-12 | newline convention
```

Where our own text merely *contains* a quotation — evidence columns of the form
`page · timestamp · name :: "quote"` — only the quoted passage is lifted out and
replaced by the marker `U+E000`; our own framing stays. Where the cell was our own
writing throughout, nothing changed.

`rebuild_text.py` reverses this against a local copy of the export and verifies
every restored string against its hash. `analyse/release/redaktionsprotokoll.csv`
lists what was touched; `analyse/release/spalten_befund.csv` shows the evidence
each decision rests on; `scripts/92_release_guard.py` re-checks the built tree from
scratch without trusting the policy.

Against the export we computed from, the round trip is exact: 87,046 references
resolve, 127,619 cells come back byte-identical to what we hold, and nothing is left
empty or altered. Where a table stores newlines as `|` or `⏎`, the reference records
that convention so the restored cell matches the original character for character.
If your copy of the export differs from ours, `rebuild_text.py` says so per cell
rather than guessing — check `analyse/data/SHA256SUMS` first.

## Five artefacts the scripts do not produce

Stated plainly rather than implied, and established by re-running the whole pipeline
into an empty directory — the log and the file-by-file comparison are in
`analyse/artefakte/HERKUNFTSPRUEFUNG.md`.

- the reconciled population estimators (`paper_flotte_schaetzer_versoehnt.csv`)
- the manual review of round-six candidates (`paper_episode_r6_sichtung.csv`) and
  the head-start measurement (`paper_neuheit_*`)
- the two inputs to Fig. 3 (`paper_lernkurve_q2_inhaltlicher_lesebeweis.csv`,
  `paper_lernkurve_q3_format_erstversion_koordpop_6h.csv`)
- the hand adjudication of the 63 gold-set conflicts
  (`adjudikation_phil.json`) — a human decision, not derivable from the export

All five ship as data with their per-row values and verdicts.

Two ordering constraints if you rerun the pipeline: `63_fortschritt_robust.py`
consumes the output of `66_exposition.py`, and `62_goldset_eval.py` reads the hand
adjudication it cannot regenerate.

## Language

Paper, this file and the code comments' intent are English; the detail
reports (`analyse/artefakte/BERICHT_*.md`), the codebook and `MECHANIK.md` are
German, as is much of the inline commentary. The reports are the ambiguity record —
where a number in the paper has a caveat, that is where it is written down.

## Ethics

Personal names in the export were redacted by its first authors. We quote
agent-written text only. The wiki's administrator is identified only as such, and
the residential network block is not named beyond its provider. Registry contact
names were removed from `paper_netzblock_whois.csv`; organisations and registry
handles remain.

## Licence

Code (`analyse/scripts/`, `rebuild_text.py`) under the MIT licence, see `LICENSE`.
Derived data, tables, figures and reports under CC BY 4.0, see `LICENSE-DATA`.
The wiki export is covered by neither — it belongs to its authors, and this
repository does not contain it.

## Citing

See `CITATION.cff`.
