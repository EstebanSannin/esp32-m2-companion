"""Board DNP attribute <- netlist DNP field (single source of truth).

Run with KiCad's python:  .../python3 tools/sync_dnp.py [--check]
--check: change nothing, exit 1 if the board disagrees with the netlist.

v1: the netlist (and so BOM/CPL) knew R5/R6/C8/C9 were DNP, the board
did not - the assembly drawing would have shown them as fitted.
"""

import re
import sys
from pathlib import Path

import pcbnew

from kicad_exit import run

HERE = Path(__file__).resolve().parent.parent
PCB = HERE / "kicad" / "esp32_m2_companion.kicad_pcb"
NET = HERE / "build" / "esp32_m2_companion.net"


def netlist_dnp():
    src = NET.read_text()
    dnp = set()
    for comp in re.split(r"\(comp\s*\n", src)[1:]:
        ref = re.search(r'\(ref "([^"]+)"\)', comp).group(1)
        if re.search(r'\(name "DNP"\)\s*"DNP"', comp):
            dnp.add(ref)
    return dnp


def main():
    check = "--check" in sys.argv
    want = netlist_dnp()
    b = pcbnew.LoadBoard(str(PCB))
    bad = []
    for fp in b.GetFootprints():
        ref = fp.GetReference()
        d = ref in want
        if fp.IsDNP() != d:
            bad.append(f"{ref}: board DNP={fp.IsDNP()} netlist DNP={d}")
            if not check:
                fp.SetDNP(d)
                if d:
                    fp.SetExcludedFromBOM(True)
                    fp.SetExcludedFromPosFiles(True)
    for line in bad:
        print(("MISMATCH " if check else "fixed ") + line)
    if not check and bad:
        pcbnew.SaveBoard(str(PCB), b)
    print(f"DNP per netlist: {', '.join(sorted(want))} - "
          f"{'mismatches' if check else 'changed'}: {len(bad)}")
    return 1 if (check and bad) else 0


if __name__ == "__main__":
    run(main)
