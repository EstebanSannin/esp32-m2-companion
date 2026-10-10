"""Hand-finish helper: remove dangling tracks/vias (KiCad DRC 'track_dangling'
/ 'via_dangling'), e.g. fan-out copper left behind when a part was moved.
Never touches the USB nets. Iterates: removing a dangling via can make its
stub dangle. Separate process per pass (SWIG Remove() rule).
  $KPY tools/v2_drop_dangling.py DRC.json [--planes-only] [--skip N1,N2]
"""
import json
import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "tools"))
PCB = HERE / "kicad" / "esp32_m2_companion.kicad_pcb"
PROTECTED = {"USBH3_D_P", "USBH3_D_N", "USB_D_P", "USB_D_N"}
# --planes-only: remove only orphaned GND/+3V3 fan-out (safe, never unravels a signal net)
PLANES_ONLY = "--planes-only" in sys.argv
# --skip N1,N2: leave these nets alone (unfinished nets keep their partial
# copper for hand-finishing; only COMPLETE nets lose dead escape branches)
SKIP = set(sys.argv[sys.argv.index("--skip") + 1].split(",")) if "--skip" in sys.argv else set()


def main():
    drc = json.load(open(sys.argv[1]))
    pts = []
    for v in drc["violations"]:
        if v["type"] in ("track_dangling", "via_dangling"):
            for it in v["items"]:
                if PLANES_ONLY and not ("[GND]" in it["description"] or "[+3V3]" in it["description"]):
                    continue
                if not any(n in it["description"] for n in PROTECTED):
                    pts.append((it["pos"]["x"], it["pos"]["y"], it["description"].split()[0]))
    b = pcbnew.LoadBoard(str(PCB))
    n = 0
    for t in list(b.GetTracks()):
        if t.GetNetname() in PROTECTED or t.GetNetname() in SKIP:
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
