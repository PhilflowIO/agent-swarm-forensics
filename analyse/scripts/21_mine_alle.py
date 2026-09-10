#!/usr/bin/env python3
"""
21_mine_alle.py — erzeugt die 15 harness_*-Tabellen aus einem festgehaltenen Suchmuster.

Hintergrund: 21_mine.py ist ein argumentgetriebenes Werkzeug; die Muster des
Erstlaufs standen nirgends im Repository (Herkunftspruefung, Befund P2). Sie
stehen jetzt in scripts/21_muster.json. Dieses Skript ist der Erzeuger, den die
Lauftabelle bisher vermisste.

Lauf:
    analyse/.venv/bin/python scripts/21_mine_alle.py --pruefen    # baut neu, vergleicht, schreibt nichts
    analyse/.venv/bin/python scripts/21_mine_alle.py --schreiben  # baut neu und ersetzt artefakte/

--pruefen endet mit Rueckgabewert 1, sobald eine Datei nicht bitgleich ist.
Eintraege mit status="naeherung" werden uebersprungen: fuer sie ist kein Muster
bekannt, das die Datei reproduziert (derzeit nur harness_r1.csv).
"""
import json, subprocess, sys, tempfile, shutil, filecmp
from pathlib import Path

B      = Path(__file__).resolve().parents[1]        # analyse/
MINE   = B / "scripts" / "21_mine.py"
MUSTER = B / "scripts" / "21_muster.json"
ART    = B / "artefakte"

def bauen(basis: Path) -> dict:
    """Laesst 21_mine.py je Muster laufen. basis ist die Ersatz-Wurzel (basis/scripts,
    basis/data, basis/artefakte); 21_mine.py schreibt nach basis/artefakte."""
    muster = json.loads(MUSTER.read_text(encoding="utf-8"))["muster"]
    gebaut = {}
    for name, eintrag in sorted(muster.items()):
        if eintrag["status"] != "abgenommen":
            print(f"uebersprungen {name} -- Muster nur Naeherung, siehe 21_muster.json")
            continue
        regex = eintrag["regex"]
        # 21_mine.py schreibt fest nach <basis>/artefakte/<name>; wir geben ihm
        # eine eigene Basis, damit der Bestand unangetastet bleibt.
        r = subprocess.run([sys.executable, str(basis / "scripts" / MINE.name),
                            regex, "--max", "0", "--csv", name],
                           capture_output=True, text=True)
        if r.returncode != 0:
            sys.exit(f"{name}: 21_mine.py brach ab\n{r.stderr}")
        gebaut[name] = basis / "artefakte" / name
    return gebaut

def main():
    modus = sys.argv[1] if len(sys.argv) > 1 else "--pruefen"
    if modus not in ("--pruefen", "--schreiben"):
        sys.exit(__doc__)

    with tempfile.TemporaryDirectory() as tmp:
        arbeit = Path(tmp)
        # Arbeitskopie der Struktur, die 21_mine.py erwartet: <basis>/data, <basis>/artefakte
        (arbeit / "scripts").mkdir()
        (arbeit / "artefakte").mkdir()
        (arbeit / "data").symlink_to(B / "data")
        shutil.copy2(MINE, arbeit / "scripts" / MINE.name)
        gebaut = bauen(arbeit)

        abweichung = 0
        for name, neu in sorted(gebaut.items()):
            alt = ART / name
            if modus == "--schreiben":
                shutil.copy2(neu, alt)
                print(f"geschrieben  {name}")
                continue
            if not alt.exists():
                print(f"FEHLT        {name}"); abweichung += 1
            elif filecmp.cmp(alt, neu, shallow=False):
                print(f"bitgleich    {name}")
            else:
                print(f"ABWEICHUNG   {name}"); abweichung += 1

        if modus == "--pruefen":
            print(f"\n{len(gebaut)} Tabellen geprueft, {abweichung} Abweichungen")
            sys.exit(1 if abweichung else 0)

if __name__ == "__main__":
    main()
