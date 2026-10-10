"""v2 GATE V3: hand-route (scripted, explicit geometry, locked) the finger
fan-in of the EXP nets the grid router could not escape: EXP_10
(finger 64, B), EXP_7 (finger 61, F) and LED_1_n (finger 10, B). Fingers
59-65 sit at 0.25 mm alternating F/B pitch; a via at one finger's x blocks
both neighbours, so these are fixed first and the rest of EXP_5..EXP_11 route around them.

  EXP_10  B: finger top -> up-left stub to (93.3, 146.6), clear of the F
          stubs of 63 / 65; the route continues on B from there (the via
          first planned at its end was never used - dropped)
  (EXP_9 had a hand run up the J4.2/J4.3 gap; once EXP_7/EXP_10 were fixed
  the router found a shorter finger entry and the hand run was a dead
  branch - dropped.)
  EXP_7   F: finger 61 straight up -> 0.35/0.2 via (94.25, 145.2), centred
          between the F runs of EXP_9 (x 93.8) and EXP_5 (x ~94.75), 0.43 mm
          below J4.3 (the router had parked three B-net vias above finger 61)
  LED_1_n B: finger 10 sits between the B-key notch (x <= 106.2) and the
          USBH3_D_N finger-9 run; after v2_usbh3_dn_reroute.py moved that via
          to (107.25, 145.25): straight up on B through the notch/D_N strip
          (kept via-free: GND finger 11's F pour path, rule areas
          GND11_STRIP / GND11_BAND) to a 0.35/0.2 via (106.85, 145.65),
          0.155 mm to the D_N F and B runs; other end
          Q2.6 (D1) escapes straight up to a 0.35/0.2 via (103.05, 125.8)
  $KPY tools/v2_fanin_route.py [NET1,NET2]   (default: all)
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
    "EXP_7": [("F.Cu", [(94.25, 147.6), (94.25, 145.2)])],
    "LED_1_n": [("B.Cu", [(106.95, 147.6), (106.95, 147.45), (106.85, 147.35), (106.85, 145.65)]),
                ("B.Cu", [(103.05, 126.45), (103.05, 125.8)])],
}
VIAS = {"EXP_10": [], "EXP_7": [(94.25, 145.2)],
        "LED_1_n": [(106.85, 145.65), (103.05, 125.8)]}


def main():
    b = pcbnew.LoadBoard(str(PCB))
    mm = pcbnew.FromMM
    only = set(sys.argv[1].split(",")) if len(sys.argv) > 1 else None
    for net, polys in ROUTES.items():
        if only and net not in only:
            continue
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
    print(f"finger fan-in placed (locked): {sorted(only or ROUTES)}")


if __name__ == "__main__":
    from kicad_exit import run
    run(main)
