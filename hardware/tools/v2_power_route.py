"""v2 GATE V3: hand-route (scripted, explicit geometry, locked) the +3V3_M2
input trunk: fingers 70/72/74 (B) -> C14.1 (input cap) -> U6.5 (eFuse IN),
0.35 mm (~1 A, = eFuse limit), plus the stubs + via of the right-side 3.3 V
fingers 2/4. The 2/4 link to the trunk and the sense branches (R31 OVLO
divider, R33 EN pull-up) are thin and left to the router (`--thin`).

Why by hand: routed by the grid router, the trunk ran sideways along the
finger tops on B and walled in EXP_5..EXP_11 (fingers 59-65), and it put
thin tracks between the gold fingers (contact area). Here every finger is
entered only from its top edge (y 147.5).
  $KPY tools/v2_power_route.py
"""
import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "tools"))
PCB = HERE / "kicad" / "esp32_m2_companion.kicad_pcb"
NET = "+3V3_M2"
W = 0.35
VD, VDR = 0.45, 0.3

# U6.5 is a 0.3 mm strip x 91.70-92.00, y 140.70-143.10, entered from below
# between the U6.6 OUT strip (x <= 91.50) and the U6.4 corner (x >= 92.20):
# 0.35 mm at x 91.85 keeps 0.175 mm to both. C14.1: x 91.925-92.825,
# y 143.825-144.775. Fingers 70/72/74 (B): x 92.0 / 91.5 / 91.0, top y 147.5.
ROUTES = [
    ("B.Cu", [(92.0, 147.6), (92.0, 146.6)]),
    ("B.Cu", [(91.5, 147.6), (91.5, 146.6)]),
    ("B.Cu", [(91.0, 147.6), (91.0, 146.6), (92.0, 146.6)]),
    ("B.Cu", [(92.0, 146.6), (92.375, 146.225), (92.375, 144.3)]),
    ("B.Cu", [(92.375, 144.3), (91.85, 143.775), (91.85, 142.9)]),
    # right-side 3.3 V fingers 2 / 4 (B): x 109.0 / 108.5 -> via above them;
    # 0.2 mm (link current only) and angled away from the locked USBH3_D_P
    # via at (108.1, 146.95)
]
THIN = 0.2
THIN_ROUTES = [
    ("B.Cu", [(108.6, 147.6), (108.75, 147.3), (108.75, 146.65)]),
    ("B.Cu", [(108.95, 147.6), (108.75, 147.3)]),
]
VIAS = [(108.75, 146.65)]


def main():
    b = pcbnew.LoadBoard(str(PCB))
    mm = pcbnew.FromMM
    ni = b.FindNet(NET)
    for routes, w in ((ROUTES, W), (THIN_ROUTES, THIN)):
        for lname, pts in routes:
            layer = b.GetLayerID(lname)
            for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
                t = pcbnew.PCB_TRACK(b)
                t.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
                t.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
                t.SetWidth(mm(w)); t.SetLayer(layer); t.SetNet(ni); t.SetLocked(True)
                b.Add(t)
    for x, y in VIAS:
        v = pcbnew.PCB_VIA(b)
        v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
        v.SetWidth(mm(VD)); v.SetDrill(mm(VDR)); v.SetNet(ni); v.SetLocked(True)
        b.Add(v)
    pcbnew.SaveBoard(str(PCB), b)
    print(f"{NET}: trunk + finger 2/4 stubs placed (locked)")


if __name__ == "__main__":
    from kicad_exit import run
    run(main)
