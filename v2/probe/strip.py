"""Probe stage 0: copy of rev-B board with the OUTER pours removed (separate
process: never keep using a board after Remove())."""
import sys
from pathlib import Path
import pcbnew
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "hardware" / "tools"))

def main():
    src = HERE / "probe_base.kicad_pcb"
    b = pcbnew.LoadBoard(str(HERE.parent.parent / "hardware/kicad/esp32_m2_companion.kicad_pcb"))
    n = 0
    for z in list(b.Zones()):
        if not z.GetIsRuleArea() and z.GetLayer() in (pcbnew.F_Cu, pcbnew.B_Cu):
            b.Remove(z); n += 1
    pcbnew.SaveBoard(str(src), b)
    print("removed outer pours:", n, "->", src)

if __name__ == "__main__":
    from kicad_exit import run
    run(main)
