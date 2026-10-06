"""Assembly + fab drawings for review gates (`make drawings`).

Output: docs/review/rev_b_drawings.pdf (also hardware/build/drawings/)
  sheet 1  assembly: top + bottom-as-seen-from-below at 4:1, pads, refs,
           pad numbers on polarized parts, LED '+'/'K', DNP crossed
  sheet 2  fab: outline + dimensions, hole table (PTH/NPTH), fab notes
Drawn from the board by tools/asm_view.py (kicad-cli's PDF plot has no
scale option - a 22x42 mm card is a speck on A4). Needs rsvg-convert
(Homebrew librsvg). Refuses to plot if board DNP != netlist DNP.
"""

import datetime
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
ROOT = HERE.parent
APP = Path.home() / "Applications/KiCad/KiCad.app/Contents"
KPY = APP / "Frameworks/Python.framework/Versions/3.9/bin/python3"
OUT = HERE / "build" / "drawings"
DOCS = ROOT / "docs" / "review"


def main():
    subprocess.run([str(KPY), str(HERE / "tools" / "sync_dnp.py"), "--check"],
                   check=True)
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    rev = subprocess.run(["git", "describe", "--tags", "--always", "--dirty"],
                         cwd=ROOT, capture_output=True, text=True).stdout.strip()
    rev = f"v1.0 Rev B · {rev}"
    date = datetime.date.today().isoformat()
    subprocess.run([str(KPY), str(HERE / "tools" / "asm_view.py"), str(OUT),
                    "ESP32-M2-COMPANION", rev, date], check=True)
    pdf = OUT / "drawings.pdf"
    subprocess.run(["rsvg-convert", "-f", "pdf", "-o", str(pdf),
                    str(OUT / "assembly.svg"), str(OUT / "fab.svg")], check=True)
    DOCS.mkdir(parents=True, exist_ok=True)
    shutil.copy(pdf, DOCS / "rev_b_drawings.pdf")
    print("wrote", DOCS / "rev_b_drawings.pdf")


if __name__ == "__main__":
    main()
