"""Hand-finish helper: remove one via of every same-net pair that violates
hole-to-hole (reads a DRC JSON). Keeps the via listed first by DRC.
  $KPY tools/v2_drop_dup_vias.py DRC.json
"""
import json
import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "tools"))
PCB = HERE / "kicad" / "esp32_m2_companion.kicad_pcb"


def main():
    drc = json.load(open(sys.argv[1]))
    drop = []
    for v in drc["violations"]:
        if v["type"] in ("hole_to_hole", "holes_co_located"):
            it = v["items"]
            if all(i["description"].startswith("Via") for i in it):
                n0 = it[0]["description"].split("[")[1].split("]")[0]
                n1 = it[1]["description"].split("[")[1].split("]")[0]
                if n0 == n1:
                    drop.append((it[1]["pos"]["x"], it[1]["pos"]["y"]))
    b = pcbnew.LoadBoard(str(PCB))
    n = 0
    for t in list(b.GetTracks()):
        if t.Type() == pcbnew.PCB_VIA_T:
            x, y = pcbnew.ToMM(t.GetX()), pcbnew.ToMM(t.GetY())
            if any(abs(x - dx) < 0.01 and abs(y - dy) < 0.01 for dx, dy in drop):
                b.Remove(t)
                n += 1
    pcbnew.SaveBoard(str(PCB), b)
    print(f"dropped {n} duplicate same-net vias")


if __name__ == "__main__":
    from kicad_exit import run
    run(main)
