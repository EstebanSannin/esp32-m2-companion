"""v2 GATE V3: move the USBH3_D_N finger via (rev-B route, apply_rev_b_corner.py)
off finger 10. v2 uses finger 10 (LED_1_n, B side); the rev-B via at
(107.10, 146.95) sat right above it with the B-key notch (x 105.0-106.2,
top y 146.5) on the other side, so finger 10 had no way out on any layer.

New: F finger 9 straight up to a via at (107.25, 145.25), B left at y 145.25
(0.26 mm above the D_P B run at y 144.85) onto the rev-B B run at
(105.55, 145.40). +0.2 mm on D_N (USB FS from the ESP32-S3: irrelevant).
Same track width; 0.35/0.2 via. The strip between the notch and the D_N F run stays
via-free: it is the only F pour path from GND finger 11 to the GND pour
(rev B had it too); LED_1_n climbs it on B and drops through a via above.
Two processes (SWIG Remove() rule):
  $KPY tools/v2_usbh3_dn_reroute.py remove
  $KPY tools/v2_usbh3_dn_reroute.py add
"""
import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "tools"))
PCB = HERE / "kicad" / "esp32_m2_companion.kicad_pcb"
NET = "USBH3_D_N"
W = 0.14
# rev-B via + B diagonal, and this tool's first (GATE V3) placement at y 146.1
OLD_PTS = [(107.10, 146.95), (106.60, 146.45), (107.25, 146.10), (106.30, 146.10)]
NEW = [("F.Cu", [(107.25, 147.5), (107.25, 145.25)]),
       ("B.Cu", [(107.25, 145.25), (105.55, 145.25), (105.55, 145.40)])]
NEW_VIA = (107.25, 145.25)


def main():
    b = pcbnew.LoadBoard(str(PCB))
    mm, T = pcbnew.FromMM, pcbnew.ToMM
    if sys.argv[1] == "remove":
        n = 0
        for t in list(b.GetTracks()):
            if t.GetNetname() != NET:
                continue
            if t.Type() == pcbnew.PCB_VIA_T:
                ends = [(T(t.GetX()), T(t.GetY()))]
            else:
                ends = [(T(t.GetStart().x), T(t.GetStart().y)), (T(t.GetEnd().x), T(t.GetEnd().y))]
            if any(abs(x - ox) < 0.01 and abs(y - oy) < 0.01 for x, y in ends for ox, oy in OLD_PTS):
                b.Remove(t)
                n += 1
        pcbnew.SaveBoard(str(PCB), b)
        print(f"{NET}: removed {n} rev-B items at the finger-10 corner")
        return
    ni = b.FindNet(NET)
    for lname, pts in NEW:
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            t = pcbnew.PCB_TRACK(b)
            t.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
            t.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
            t.SetWidth(mm(W)); t.SetLayer(b.GetLayerID(lname)); t.SetNet(ni); t.SetLocked(True)
            b.Add(t)
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(pcbnew.VECTOR2I(mm(NEW_VIA[0]), mm(NEW_VIA[1])))
    # 0.35/0.2 (the approved small-via option): a 0.45 pad here is 0.105 mm
    # from the D_P B run at y 144.85 (< 0.127)
    v.SetWidth(mm(0.35)); v.SetDrill(mm(0.2)); v.SetNet(ni); v.SetLocked(True)
    b.Add(v)
    pcbnew.SaveBoard(str(PCB), b)
    print(f"{NET}: new finger-9 via at {NEW_VIA} placed (locked)")


if __name__ == "__main__":
    from kicad_exit import run
    run(main)
