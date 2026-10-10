"""Hand-finish helper: remove dangling tracks/vias (KiCad DRC 'track_dangling'
/ 'via_dangling'), e.g. fan-out copper left behind when a part was moved.
Never touches the USB nets. Iterates: removing a dangling via can make its
stub dangle. Separate process per pass (SWIG Remove() rule).
  $KPY tools/v2_drop_dangling.py DRC.json
"""
import json
import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "tools"))
PCB = HERE / "kicad" / "esp32_m2_companion.kicad_pcb"
PROTECTED = {"USBH3_D_P", "USBH3_D_N", "USB_D_P", "USB_D_N"}


def main():
    drc = json.load(open(sys.argv[1]))
    pts = []
    for v in drc["violations"]:
        if v["type"] in ("track_dangling", "via_dangling"):
            for it in v["items"]:
                if not any(n in it["description"] for n in PROTECTED):
                    pts.append((it["pos"]["x"], it["pos"]["y"], it["description"].split()[0]))
    b = pcbnew.LoadBoard(str(PCB))
    n = 0
    for t in list(b.GetTracks()):
        if t.GetNetname() in PROTECTED:
            continue
        for x, y, kind in pts:
            if kind == "Via" and t.Type() != pcbnew.PCB_VIA_T:
                continue
            if kind == "Track" and t.Type() == pcbnew.PCB_VIA_T:
                continue
            if t.HitTest(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)), pcbnew.FromMM(0.02)):
                b.Remove(t)
                n += 1
                break
    pcbnew.SaveBoard(str(PCB), b)
    print(f"removed {n} dangling items")


if __name__ == "__main__":
    from kicad_exit import run
    run(main)
