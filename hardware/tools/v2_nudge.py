"""Hand-finish helper: rotate / move a placed footprint.
  $KPY tools/v2_nudge.py REF [rot+DEG] [dx DX] [dy DY]
e.g.  v2_nudge.py C14 rot+180      v2_nudge.py R34 dx -1.2 dy 0.5
Prints the new pad positions. Run DRC after.
"""
import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "tools"))
PCB = HERE / "kicad" / "esp32_m2_companion.kicad_pcb"


def main():
    ref = sys.argv[1]
    args = sys.argv[2:]
    b = pcbnew.LoadBoard(str(PCB))
    fp = b.FindFootprintByReference(ref)
    k = 0
    while k < len(args):
        a = args[k]
        if a.startswith("rot+"):
            fp.SetOrientationDegrees(fp.GetOrientationDegrees() + float(a[4:]))
            k += 1
        elif a in ("dx", "dy"):
            d = pcbnew.FromMM(float(args[k + 1]))
            pos = fp.GetPosition()
            fp.SetPosition(pcbnew.VECTOR2I(pos.x + (d if a == "dx" else 0),
                                           pos.y + (d if a == "dy" else 0)))
            k += 2
        else:
            raise SystemExit(f"bad arg {a}")
    for p in fp.Pads():
        print(f"{ref}.{p.GetNumber()} {p.GetNetname():14s} "
              f"({pcbnew.ToMM(p.GetX()):.2f}, {pcbnew.ToMM(p.GetY()):.2f})")
    pcbnew.SaveBoard(str(PCB), b)


if __name__ == "__main__":
    from kicad_exit import run
    run(main)
