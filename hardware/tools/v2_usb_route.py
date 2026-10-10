"""v2 GATE V3: hand-route (scripted, explicit geometry) the USB nets between
U1 (USBLC6, ESD side) and the module, replacing the rev-B route that ran
through the new switch strip. All items locked.

  ESD side  U1.4 N / U1.6 P (B) -> vias right of U1 -> In2 (L3, directly on
            the L2 GND plane) up the right edge, left along y 131.4/130.9
            [6-layer JLC vias are epoxy-filled + capped: via-in-pad OK]
  MCU side  In2 down the module's left pad column -> via-in-pad on module
            pads 13 (N, y 135.23) / 14 (P, y 136.5).
Widths 0.15 mm (USB_DIFF class). FS USB (12 Mbit/s): the pair is
GND-referenced and length-matched within the budget printed below; tight
coupling is not required at these lengths (edges ~4 ns >> ~0.2 ns flight).
  $KPY tools/v2_usb_route.py
"""
import math
import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "tools"))
PCB = HERE / "kicad" / "esp32_m2_companion.kicad_pcb"
W = 0.15
VD, VDR = 0.45, 0.3

# net: list of (layer, [points]) polylines ; vias: net -> [(x, y)]
ROUTES = {
    # U1 MCU-side pins (B) -> vias right of U1 -> In2 (on the L2 GND plane)
    # up the right edge, left above the switch strip, down the module's left
    # pad column (x 90.45 / 89.95, under the F pads) -> via-in-pad on module
    # pads 13 (N) / 14 (P). No F/B run under the switches: the old F.Cu leg
    # at y 135.2/136.5 crossed U4/U5 and blocked every escape via (GATE V3).
    "USB_D_N": [
        ("B.Cu", [(108.838, 142.35), (109.90, 142.35)]),
        ("In2.Cu", [(109.90, 142.35), (109.90, 131.4), (90.45, 131.4),
                    (90.45, 135.23), (91.25, 135.23)]),
    ],
    "USB_D_P": [
        ("B.Cu", [(108.838, 144.25), (110.40, 144.25)]),
        ("In2.Cu", [(110.40, 144.25), (110.40, 130.9), (89.95, 130.9),
                    (89.95, 136.5), (91.25, 136.5)]),
    ],
}
VIAS = {
    "USB_D_N": [(109.90, 142.35), (91.25, 135.23)],
    "USB_D_P": [(110.40, 144.25), (91.25, 136.5)],
}


def main():
    only = set(sys.argv[1].split(",")) if len(sys.argv) > 1 else None
    b = pcbnew.LoadBoard(str(PCB))
    mm = pcbnew.FromMM
    lengths = {}
    for net, polys in ROUTES.items():
        if only and net not in only:
            continue
        ni = b.FindNet(net)
        assert ni is not None, net
        L = 0.0
        for lname, pts in polys:
            layer = b.GetLayerID(lname)
            for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
                t = pcbnew.PCB_TRACK(b)
                t.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
                t.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
                t.SetWidth(mm(W)); t.SetLayer(layer); t.SetNet(ni); t.SetLocked(True)
                b.Add(t)
                L += math.hypot(x2 - x1, y2 - y1)
        for (x, y) in VIAS.get(net, []):
            v = pcbnew.PCB_VIA(b)
            v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
            v.SetWidth(mm(VD)); v.SetDrill(mm(VDR)); v.SetNet(ni); v.SetLocked(True)
            b.Add(v)
        lengths[net] = L
    pcbnew.SaveBoard(str(PCB), b)
    for k, v in lengths.items():
        print(f"{k:12s} {v:6.2f} mm")
    if "USB_D_P" in lengths and "USB_D_N" in lengths:
        print("pair skew U1 -> module: %.2f mm" % abs(lengths["USB_D_P"] - lengths["USB_D_N"]))


if __name__ == "__main__":
    from kicad_exit import run
    run(main)
