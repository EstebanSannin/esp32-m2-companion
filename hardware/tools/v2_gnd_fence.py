"""RC1 (review layout-4): GND stitching of the outer pours to the In1 plane.

1. Finger tops: every GND finger gets a GND via within FINGER_R of
   (finger x, 146.8), above the finger rule areas (vias are forbidden in
   y 147.3-150.2).
2. USB transitions: every via of a USB net gets a GND via within USB_R
   (Espressif HDG: ground return via at each layer change).
3. Fence: greedy - take the outer-pour point (GND_top / GND_bot fill, 0.25 mm
   grid) farthest from any GND via; if it is farther than R, put a via at the
   legal spot nearest to it inside the same fill; repeat.
Legal = same rules as v2_stitch_islands.py (clearance 0.127, hole-to-copper
0.2, hole-to-hole 0.25, 0.3 mm to the edge, no via-forbidding rule area).
Vias 0.45/0.3 (0.35/0.2 for steps 1-2 when 0.45 does not fit).
  $KPY tools/v2_gnd_fence.py [--dry] [--r 2.5]
"""
import math
import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "tools"))
PCB = HERE / "kicad" / "esp32_m2_companion.kicad_pcb"
DRY = "--dry" in sys.argv
R = float(sys.argv[sys.argv.index("--r") + 1]) if "--r" in sys.argv else 2.5
CLR, HOLE_CLR, HOLE_HOLE, EDGE = 0.127, 0.2, 0.25, 0.3
FINGER_R, USB_R = 1.0, 1.0
FINGER_Y = 146.8
USB_NETS = {"USBH3_D_P", "USBH3_D_N", "USB_D_P", "USB_D_N", "USB_D_P_ESD", "USB_D_N_ESD"}
G = 0.25
T, mm = pcbnew.ToMM, pcbnew.FromMM


class Board:
    def __init__(self, b):
        self.b = b
        self.gnd = b.FindNet("GND")
        self.cu = list(b.GetEnabledLayers().CuStack())
        self.outline = pcbnew.SHAPE_POLY_SET()
        b.GetBoardPolygonOutlines(self.outline)
        self.gvias = [(T(t.GetX()), T(t.GetY()), T(t.GetDrillValue())) for t in b.GetTracks()
                      if t.Type() == pcbnew.PCB_VIA_T and t.GetNetname() == "GND"]
        self.gvias += [(T(p.GetX()), T(p.GetY()), 0.3) for fp in b.GetFootprints() for p in fp.Pads()
                       if p.GetNetname() == "GND" and p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH]
        # foreign copper, bucketed by 1 mm cells (bbox + 0.7 mm)
        self.cells = {}
        items = [t for t in b.GetTracks() if t.GetNetCode() != self.gnd.GetNetCode()]
        items += [p for fp in b.GetFootprints() for p in fp.Pads()
                  if p.GetNetCode() != self.gnd.GetNetCode() or p.GetNetCode() == 0]
        for it in items:
            bb = it.GetBoundingBox()
            for cx in range(int(T(bb.GetLeft()) - 0.7), int(T(bb.GetRight()) + 0.7) + 1):
                for cy in range(int(T(bb.GetTop()) - 0.7), int(T(bb.GetBottom()) + 0.7) + 1):
                    self.cells.setdefault((cx, cy), []).append(it)
        self.keep = [z for z in list(b.Zones()) + [z for fp in b.GetFootprints() for z in fp.Zones()]
                     if z.GetIsRuleArea() and z.GetDoNotAllowVias()]

    def legal(self, x, y, vd, vdr):
        c = pcbnew.VECTOR2I(mm(x), mm(y))
        ed = self.outline.Outline(0)
        if not ed.PointInside(c) or ed.SquaredDistance(c, True) < mm(EDGE + vd / 2) ** 2:
            return False
        for gx, gy, gd in self.gvias:
            if math.hypot(gx - x, gy - y) < (vdr + gd) / 2 + HOLE_HOLE:
                return False
        probe = pcbnew.SHAPE_CIRCLE(c, mm(vd / 2))
        hole = pcbnew.SHAPE_CIRCLE(c, mm(vdr / 2))
        for it in self.cells.get((int(x), int(y)), []):
            for l in self.cu:
                if not it.IsOnLayer(l):
                    continue
                sh = it.GetEffectiveShape(l)
                if sh.Collide(probe, mm(CLR)) or sh.Collide(hole, mm(HOLE_CLR)):
                    return False
        for z in self.keep:
            if z.Outline().Collide(c, mm(vd / 2)):
                return False
        return True

    def add(self, x, y, vd, vdr, why):
        v = pcbnew.PCB_VIA(self.b)
        v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
        v.SetWidth(mm(vd)); v.SetDrill(mm(vdr)); v.SetNet(self.gnd)
        self.b.Add(v)
        self.gvias.append((x, y, vdr))
        print(f"  via {vd}/{vdr} at ({x:.2f},{y:.2f})  {why}")

    def near_gnd(self, x, y, r):
        return any(math.hypot(gx - x, gy - y) <= r for gx, gy, _ in self.gvias)

    def spot(self, x, y, rmax, inside=None, sizes=((0.45, 0.3), (0.35, 0.2)), step=0.05):
        """nearest legal spot to (x, y) within rmax (step-mm grid)."""
        cands = []
        n = int(rmax / step)
        for i in range(-n, n + 1):
            for j in range(-n, n + 1):
                d = math.hypot(i, j) * step
                if d <= rmax:
                    cands.append((d, round(x + i * step, 3), round(y + j * step, 3)))
        cands.sort()
        for vd, vdr in sizes:
            for _, cx, cy in cands:
                if inside and not inside(cx, cy):
                    continue
                if self.legal(cx, cy, vd, vdr):
                    return cx, cy, vd, vdr
        return None


def main():
    b = pcbnew.LoadBoard(str(PCB))
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    B = Board(b)
    fills = [(z.GetFilledPolysList(z.GetLayer()), z.GetZoneName()) for z in b.Zones()
             if z.GetZoneName() in ("GND_top", "GND_bot")]

    def in_fill(x, y, margin=0.25):
        c = pcbnew.VECTOR2I(mm(x), mm(y))
        for f, _ in fills:
            for k in range(f.OutlineCount()):
                ol = f.Outline(k)
                if ol.PointInside(c) and ol.SquaredDistance(c, True) >= mm(margin) ** 2:
                    return True
        return False

    added = 0
    print("1. finger tops")
    j1 = b.FindFootprintByReference("J1")
    for p in sorted(j1.Pads(), key=lambda p: p.GetX()):
        if p.GetNetname() != "GND":
            continue
        x = T(p.GetX())
        if B.near_gnd(x, FINGER_Y, FINGER_R):
            continue
        s = B.spot(x, FINGER_Y, FINGER_R, inside=in_fill)
        if s:
            B.add(*s, f"finger {p.GetNumber()}"); added += 1
        else:
            print(f"  finger {p.GetNumber()}: NO SPOT within {FINGER_R} mm")
    print("2. USB transitions")
    for t in list(b.GetTracks()):
        if t.Type() != pcbnew.PCB_VIA_T or t.GetNetname() not in USB_NETS:
            continue
        x, y = T(t.GetX()), T(t.GetY())
        if B.near_gnd(x, y, USB_R):
            continue
        s = B.spot(x, y, USB_R)
        if s:
            B.add(*s, f"USB {t.GetNetname()} via ({x:.2f},{y:.2f})"); added += 1
        else:
            print(f"  {t.GetNetname()} via ({x:.2f},{y:.2f}): NO SPOT within {USB_R} mm")
    print(f"3. fence, every outer-pour point within {R} mm of a GND via")
    pts = []
    bb = B.outline.BBox()
    for i in range(int((T(bb.GetRight()) - T(bb.GetLeft())) / G) + 1):
        for k in range(int((T(bb.GetBottom()) - T(bb.GetTop())) / G) + 1):
            x, y = T(bb.GetLeft()) + i * G, T(bb.GetTop()) + k * G
            if y >= 147.3:   # finger band: fed by step 1
                continue
            if in_fill(x, y, 0.0):
                pts.append((x, y))
    skip = set()
    while True:
        far = max(((min(math.hypot(gx - x, gy - y) for gx, gy, _ in B.gvias), x, y)
                   for x, y in pts if (x, y) not in skip), default=None)
        if not far or far[0] <= R:
            break
        d, x, y = far
        s = B.spot(x, y, R * 0.8, inside=in_fill, sizes=((0.45, 0.3),), step=0.1)
        if s:
            B.add(*s, f"fence (point ({x:.2f},{y:.2f}) was {d:.1f} mm away)"); added += 1
        else:
            skip.add((x, y))
    if skip:
        print(f"  {len(skip)} pour points left > {R} mm (no legal spot near them)")
    print(f"added {added} GND vias")
    if not DRY:
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
        pcbnew.SaveBoard(str(PCB), b)


if __name__ == "__main__":
    from kicad_exit import run
    run(main)
