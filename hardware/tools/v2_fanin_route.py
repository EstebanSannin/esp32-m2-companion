"""v2 GATE V3: hand-route (scripted, explicit geometry, locked) the finger
fan-in of the EXP nets the grid router could not escape: EXP_10
(finger 64, B), EXP_9 (finger 63, F), EXP_7 (finger 61, F). Fingers 59-65 sit
at 0.25 mm
alternating F/B pitch; a via at one finger's x blocks both neighbours, so
these are fixed first and the rest of EXP_5..EXP_11 route around them.

  EXP_10  B: finger top -> up-left -> 0.35/0.2 via (93.3, 146.6)  (row clear
          of the F stubs of 63 (x 93.75) / 65 (x 93.25, bends left))
  EXP_9   F: straight up through the 0.4 mm gap between J4 pads 2/3
          (x 93.6-94.0) -> 0.35/0.2 via (93.8, 141.9), above J4 and 0.19 mm
          clear of R32.2 (y >= 142.27)
  EXP_7   F: finger 61 straight up -> 0.35/0.2 via (94.25, 145.2), centred
          between the F runs of EXP_9 (x 93.8) and EXP_5 (x ~94.75), 0.43 mm
          below J4.3 (the router had parked three B-net vias above finger 61)
  $KPY tools/v2_fanin_route.py
"""
import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "tools"))
PCB = HERE / "kicad" / "esp32_m2_companion.kicad_pcb"
W = 0.127
VD, VDR = 0.35, 0.2

ROUTES = {
    "EXP_10": [("B.Cu", [(93.5, 147.6), (93.5, 147.2), (93.3, 147.0), (93.3, 146.6)])],
    "EXP_9": [("F.Cu", [(93.75, 147.6), (93.8, 147.55), (93.8, 141.9)])],
    "EXP_7": [("F.Cu", [(94.25, 147.6), (94.25, 145.2)])],
}
VIAS = {"EXP_10": [(93.3, 146.6)], "EXP_9": [(93.8, 141.9)], "EXP_7": [(94.25, 145.2)]}


def main():
    b = pcbnew.LoadBoard(str(PCB))
    mm = pcbnew.FromMM
    for net, polys in ROUTES.items():
        ni = b.FindNet(net)
        for lname, pts in polys:
            layer = b.GetLayerID(lname)
            for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
                t = pcbnew.PCB_TRACK(b)
                t.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
                t.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
                t.SetWidth(mm(W)); t.SetLayer(layer); t.SetNet(ni); t.SetLocked(True)
                b.Add(t)
        for x, y in VIAS[net]:
            v = pcbnew.PCB_VIA(b)
            v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
            v.SetWidth(mm(VD)); v.SetDrill(mm(VDR)); v.SetNet(ni); v.SetLocked(True)
            b.Add(v)
    pcbnew.SaveBoard(str(PCB), b)
    print("EXP_7 / EXP_9 / EXP_10 finger fan-in placed (locked)")


if __name__ == "__main__":
    from kicad_exit import run
    run(main)
