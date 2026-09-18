#!/usr/bin/env python3
"""
93_release_repo.py — stellt aus dem geprueften Bestand das oeffentliche Repository zusammen.

Reihenfolge:
    scripts/90_release_index.py     Spaltenbefund (welche Spalte traegt Abzugstext)
    scripts/91_release_build.py     Redaktion    (Abzugstext -> Verweis)
    scripts/92_release_guard.py     Gegenprobe   (bricht ab, wenn noch Text drin ist)
    scripts/93_release_repo.py      dieses Skript

Ergebnis: analyse/release/repo/ -- ein vollstaendiges, hochladbares Verzeichnis.
Es enthaelt NICHT analyse/data/ (den Abzug) und nicht die fuenf Zwischenstufen,
die den vollen Seitentext tragen; beides bauen die nummerierten Skripte neu.

Lauf: analyse/.venv/bin/python scripts/93_release_repo.py
"""
import shutil, sys
from pathlib import Path

B      = Path(__file__).resolve().parents[1]        # analyse/
ROOT   = B.parent                                    # Projektwurzel
R      = B / "release"
DIST   = R / "dist" / "artefakte"
REPO   = R / "repo"

if not DIST.exists():
    sys.exit(f"{DIST} fehlt -- erst scripts/91_release_build.py laufen lassen.")
if (R / "guard_verstoesse.csv").exists():
    sys.exit("release/guard_verstoesse.csv existiert -- 92_release_guard.py hat Text gefunden. "
             "Erst beheben, dann die Datei loeschen.")

# Neu aufbauen, aber die Git-Historie behalten: repo/ ist der Arbeitsbaum des
# veroeffentlichten Repositories, sein .git traegt die Tags, auf die Zenodo verweist.
REPO.mkdir(parents=True, exist_ok=True)
for p in REPO.iterdir():
    if p.name == ".git":
        continue
    shutil.rmtree(p) if p.is_dir() else p.unlink()

def kopiere_baum(quelle: Path, ziel: Path, ohne=()):
    ziel.mkdir(parents=True, exist_ok=True)
    for p in sorted(quelle.rglob("*")):
        if any(teil in ohne for teil in p.parts):
            continue
        z = ziel / p.relative_to(quelle)
        if p.is_dir():
            z.mkdir(parents=True, exist_ok=True)
        else:
            z.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, z)

OHNE = ("__pycache__", ".venv", ".pytest_cache")

# 1. Analysepipeline
kopiere_baum(B / "scripts", REPO / "analyse" / "scripts", OHNE)
shutil.copy2(B / "requirements.txt", REPO / "analyse" / "requirements.txt")

# 2. Geprueft redigierte Artefakte
kopiere_baum(DIST, REPO / "analyse" / "artefakte", OHNE)

# 3. Belege der Redaktion selbst -- ohne sie waere sie nicht nachpruefbar
(REPO / "analyse" / "release").mkdir(parents=True, exist_ok=True)
for n in ("policy.json", "spalten_befund.csv", "redaktionsprotokoll.csv",
          "rebuild_text.py", "BERICHT_veroeffentlichung.md"):
    if (R / n).exists():
        shutil.copy2(R / n, REPO / "analyse" / "release" / n)
shutil.copy2(R / "rebuild_text.py", REPO / "analyse" / "rebuild_text.py")

# 4. Was das Paper druckt
kopiere_baum(ROOT / "paper" / "tables",  REPO / "paper" / "tables",  OHNE)
kopiere_baum(ROOT / "paper" / "figures", REPO / "paper" / "figures", OHNE)
for n in ("main.tex", "references.bib", "limitations_raw.md"):
    if (ROOT / "paper" / n).exists():
        shutil.copy2(ROOT / "paper" / n, REPO / "paper" / n)
if (ROOT / "paper" / "main.pdf").exists():
    shutil.copy2(ROOT / "paper" / "main.pdf", REPO / "paper" / "main.pdf")

# 5. Deutsche Synthese, aus der jede Zahl des Papers stammt
for n in ("MECHANIK.md", "README.md"):
    if (ROOT / n).exists():
        shutil.copy2(ROOT / n, REPO / ("MECHANIK.md" if n == "MECHANIK.md" else "README_analyse_de.md"))

# 6. Der Kopf des Repositories (handgeschrieben, liegt unter release/vorlagen/)
V = R / "vorlagen"
for n in ("README.md", "LICENSE", "LICENSE-DATA", "CITATION.cff", ".gitignore"):
    if (V / n).exists():
        shutil.copy2(V / n, REPO / n)

# 7. Leeres data/ mit Wegweiser statt des Abzugs
(REPO / "analyse" / "data").mkdir(parents=True, exist_ok=True)
if (B / "data" / "SHA256SUMS").exists():
    shutil.copy2(B / "data" / "SHA256SUMS", REPO / "analyse" / "data" / "SHA256SUMS")
# Betreiberlog: nur Herkunft und Pruefsummen (das Paper verweist darauf), nie das Log
# selbst und nie den vorbereiteten Ausschnitt unter freigabe/.
(REPO / "analyse" / "data" / "betreiberlogs").mkdir(parents=True, exist_ok=True)
for n in ("HERKUNFT.md", "SHA256SUMS"):
    shutil.copy2(B / "data" / "betreiberlogs" / n, REPO / "analyse" / "data" / "betreiberlogs" / n)
(REPO / "analyse" / "data" / "README.md").write_text(
    "# The export does not live here\n\n"
    "This directory is intentionally empty. The wiki export is not ours to redistribute.\n"
    "Download it from its authors at <https://collusion.wiki/explorer/download.html> and\n"
    "unpack it here, then verify it against `SHA256SUMS` (the sums of the copy every number\n"
    "in the paper was computed from).\n\n"
    "Expected files: `revisions.jsonl`, `pages.jsonl`, `events.jsonl`, `labels.jsonl`,\n"
    "`manifest.json`.\n", encoding="utf-8")

dateien = sum(1 for p in REPO.rglob("*") if p.is_file())
groesse = sum(p.stat().st_size for p in REPO.rglob("*") if p.is_file())
print(f"{REPO}\n  {dateien} Dateien, {groesse/1e6:.1f} MB")
for d in sorted(x for x in REPO.rglob("*") if x.is_dir()):
    n = sum(1 for p in d.rglob("*") if p.is_file())
    if n:
        print(f"  {str(d.relative_to(REPO)):32} {n:>5} Dateien "
              f"{sum(p.stat().st_size for p in d.rglob('*') if p.is_file())/1e6:>7.1f} MB")
