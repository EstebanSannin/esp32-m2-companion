"""v2 GATE V3: place the parked v2 footprints onto the bottom side.

Each part goes to the nearest LEGAL spot to its target (spiral search,
two rotations). Legal means:
- inside the bottom-side region;
- courtyard clear of every other bottom-side courtyard;
- pads clear (0.2 mm) of foreign copper on B.Cu, every via and PTH pad, and
  rule areas.
Targets are routing-aware (docs: v2 GATE V3 plan): switches above their
finger clusters, arrays next to the module pads, eFuse at the power entry.
The rev-B parts are NOT moved.

  $KPY tools/v2_place.py            # place + save
  $KPY tools/v2_place.py --dry      # report only
"""
import math
import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "tools"))
PCB = HERE / "kicad" / "esp32_m2_companion.kicad_pcb"
DRY = "--dry" in sys.argv
T = pcbnew.ToMM

# ref: (x, y, rot) target, board coords (card: x 89..111, y 108..150;
# fingers at y >= 147.3). Order = placement priority.
TARGETS = [
    # power entry (lower left, VCC fingers 70/72/74 at x ~91-92)
    ("U6", 91.6, 143.6, 0), ("C14", 89.9, 143.6, 90), ("R31", 93.6, 142.2, 90),
    ("R32", 93.6, 144.0, 90), ("R34", 93.6, 145.6, 90), ("R33", 89.9, 141.6, 90),
    ("FB1", 94.9, 142.6, 90),
    # switches in the freed test-point strip, above their fingers
    ("U4", 93.6, 136.0, 0), ("U5", 96.4, 136.0, 0), ("U3", 101.0, 136.0, 0),
    ("C11", 95.0, 134.2, 0), ("C12", 97.8, 134.2, 0), ("C10", 102.4, 134.2, 0),
    # resistor arrays next to the module pads
    ("RN2", 95.4, 125.0, 0), ("RN3", 95.4, 128.4, 0), ("RN1", 106.4, 122.6, 0),
    ("R20", 105.0, 120.2, 90), ("R21", 106.0, 120.2, 90),
    # carrier detect cluster
    ("Q1", 102.0, 121.0, 0), ("R22", 99.6, 119.8, 90), ("R23", 100.6, 119.8, 90),
    ("R24", 99.6, 122.0, 90), ("R25", 100.6, 122.0, 90), ("R26", 103.6, 123.6, 90),
    ("C13", 102.2, 123.6, 90),
    # host-facing cells (pads 33/35 right, fingers 10/23/26)
    ("Q2", 104.0, 127.0, 0), ("Q3", 104.0, 129.4, 0), ("R27", 102.0, 126.6, 90),
    ("R28", 102.0, 128.4, 90), ("R29", 106.0, 129.6, 90), ("R30", 106.0, 127.4, 90),
    # recovery test points (EN / BOOT), 1.0 mm
    ("TP1", 107.4, 136.2, 0), ("TP2", 105.6, 136.2, 0),
]
REGION = (89.6, 118.9, 110.4, 147.0)
CLR = 0.2


def bbox_mm(b):
    return (T(b.GetLeft()), T(b.GetTop()), T(b.GetRight()), T(b.GetBottom()))


def overlap(a, b, m=0.0):
    return not (a[2] + m <= b[0] or b[2] + m <= a[0] or a[3] + m <= b[1] or b[3] + m <= a[1])


def dseg(px, py, a, b):
    (x1, y1), (x2, y2) = a, b
    dx, dy = x2 - x1, y2 - y1
    L = dx * dx + dy * dy
    u = 0 if L == 0 else max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / L))
    return math.hypot(px - (x1 + u * dx), py - (y1 + u * dy))


def main():
    b = pcbnew.LoadBoard(str(PCB))
    fps = {fp.GetReference(): fp for fp in b.GetFootprints()}
    targets = {r for r, *_ in TARGETS}

    def crt(fp):
        sh = fp.GetCourtyard(pcbnew.B_CrtYd if fp.IsFlipped() else pcbnew.F_CrtYd)
        return bbox_mm(sh.BBox()) if sh.OutlineCount() else bbox_mm(fp.GetBoundingBox(False, False))

    crt_obs, pad_obs = [], []
    for r, fp in fps.items():
        if r in targets:
            continue
        if fp.IsFlipped():
            crt_obs.append(crt(fp))
        for p in fp.Pads():
            if p.IsOnLayer(pcbnew.B_Cu):
                pad_obs.append((bbox_mm(p.GetBoundingBox()), p.GetNetname()))
    cu_obs = []
    for t in b.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T:
            q = (T(t.GetX()), T(t.GetY()))
            cu_obs.append((q, q, T(t.GetWidth(pcbnew.F_Cu)) / 2, t.GetNetname()))
        elif t.GetLayer() == pcbnew.B_Cu:
            cu_obs.append(((T(t.GetStart().x), T(t.GetStart().y)),
                           (T(t.GetEnd().x), T(t.GetEnd().y)), T(t.GetWidth()) / 2,
                           t.GetNetname()))
    rule_obs = [bbox_mm(z.GetBoundingBox()) for z in b.Zones()
                if z.GetIsRuleArea() and z.GetDoNotAllowTracks()]

    def legal(fp):
        c = crt(fp)
        if c[0] < REGION[0] or c[1] < REGION[1] or c[2] > REGION[2] or c[3] > REGION[3]:
            return False
        if any(overlap(c, o) for o in crt_obs):
            return False
        for p in fp.Pads():
            if not p.IsOnLayer(pcbnew.B_Cu):
                continue
            pb, n = bbox_mm(p.GetBoundingBox()), p.GetNetname()
            cx, cy = (pb[0] + pb[2]) / 2, (pb[1] + pb[3]) / 2
            r = math.hypot(pb[2] - pb[0], pb[3] - pb[1]) / 2
            if any(overlap(pb, ro, 0.1) for ro in rule_obs):
                return False
            for a, bb, w, on in cu_obs:
                if (not n or on != n) and dseg(cx, cy, a, bb) < r + w + CLR:
                    return False
            for ob, on in pad_obs:
                if (not n or on != n) and overlap(pb, ob, CLR):
                    return False
        return True

    report = []
    for ref, x, y, rot in TARGETS:
        fp = fps[ref]
        if not fp.IsFlipped():
            fp.Flip(fp.GetPosition(), False)
        found = None
        for rr10 in range(0, 120):
            r = rr10 * 0.1
            n = max(1, int(2 * math.pi * r / 0.1))
            for k in range(n):
                a = 2 * math.pi * k / n
                for rot_try in (rot, rot + 90):
                    fp.SetOrientationDegrees(180 - rot_try)   # flipped side
                    fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x + r * math.cos(a)),
                                                   pcbnew.FromMM(y + r * math.sin(a))))
                    if legal(fp):
                        found = (round(x + r * math.cos(a), 2), round(y + r * math.sin(a), 2),
                                 rot_try, round(r, 1))
                        break
                if found:
                    break
            if found:
                break
        if not found:
            report.append(f"{ref}: NO LEGAL SPOT near ({x},{y})")
            fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(118), pcbnew.FromMM(y)))
            continue
        report.append(f"{ref}: ({found[0]},{found[1]}) rot {found[2]}  [moved {found[3]} mm from target]")
        crt_obs.append(crt(fp))
        for p in fp.Pads():
            if p.IsOnLayer(pcbnew.B_Cu):
                pad_obs.append((bbox_mm(p.GetBoundingBox()), p.GetNetname()))
    print("\n".join(report))
    if not DRY:
        pcbnew.SaveBoard(str(PCB), b)
        print("saved", PCB)


if __name__ == "__main__":
    from kicad_exit import run
    run(main)
