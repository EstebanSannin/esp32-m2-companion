"""Hand-finish helper: stitch isolated fragments of an outer GND pour to the
In1 GND plane. KiCad keeps a pour fragment that touches a GND pad but not
the rest of the pour, and reports it 'unconnected'. For every filled
fragment of the given zones without a GND via/PTH inside, place one via at
the first point (0.1 mm scan) that is >= 0.3 mm inside the fragment and
clear of every foreign item on every copper layer (clearance + hole rules).
  $KPY tools/v2_stitch_islands.py [ZONE_NAME ...]   (default GND_top GND_bot)
"""
import math
import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "tools"))
PCB = HERE / "kicad" / "esp32_m2_companion.kicad_pcb"
VD, VDR = 0.45, 0.2
CLR, HOLE_CLR, HOLE_HOLE, EDGE = 0.127, 0.2, 0.25, 0.3


def main():
    names = sys.argv[1:] or ["GND_top", "GND_bot"]
    b = pcbnew.LoadBoard(str(PCB))
    T, mm = pcbnew.ToMM, pcbnew.FromMM
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    gnd = b.FindNet("GND")
    cu = list(b.GetEnabledLayers().CuStack())
    gvias = [(T(t.GetX()), T(t.GetY())) for t in b.GetTracks()
             if t.Type() == pcbnew.PCB_VIA_T and t.GetNetname() == "GND"]
    gvias += [(T(p.GetX()), T(p.GetY())) for fp in b.GetFootprints() for p in fp.Pads()
              if p.GetNetname() == "GND" and p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH]
    outline = pcbnew.SHAPE_POLY_SET()
    b.GetBoardPolygonOutlines(outline)

    def legal(x, y):
        c = pcbnew.VECTOR2I(mm(x), mm(y))
        if not outline.Outline(0).PointInside(c):
            return False
        probe = pcbnew.SHAPE_CIRCLE(c, mm(VD / 2))
        hole = pcbnew.SHAPE_CIRCLE(c, mm(VDR / 2))
        # board edge
        ed = outline.Outline(0)
        if ed.SquaredDistance(c, True) < mm(EDGE + VD / 2) ** 2:   # outline only (inside -> 0 otherwise)
            return False
        for t in b.GetTracks():
            if t.GetNetCode() == gnd.GetNetCode():
                if t.Type() == pcbnew.PCB_VIA_T and math.hypot(T(t.GetX()) - x, T(t.GetY()) - y) < VDR + HOLE_HOLE:
                    return False
                continue
            for l in cu:
                if not t.IsOnLayer(l):
                    continue
                sh = t.GetEffectiveShape(l)
                if sh.Collide(probe, mm(CLR)) or sh.Collide(hole, mm(HOLE_CLR)):
                    return False
        for fp in b.GetFootprints():
            for p in fp.Pads():
                if p.GetNetCode() == gnd.GetNetCode() and p.GetNetCode() != 0:
                    continue
                for l in cu:
                    if not p.IsOnLayer(l):
                        continue
                    sh = p.GetEffectiveShape(l)
                    if sh.Collide(probe, mm(CLR)) or sh.Collide(hole, mm(HOLE_CLR)):
                        return False
        for z in list(b.Zones()) + [z for fp in b.GetFootprints() for z in fp.Zones()]:
            if z.GetIsRuleArea() and z.GetDoNotAllowVias() and z.Outline().Collide(c, mm(VD / 2)):
                return False
        return True

    placed = []
    for z in b.Zones():
        if z.GetZoneName() not in names:
            continue
        layer = z.GetLayer()
        polys = z.GetFilledPolysList(layer)
        for k in range(polys.OutlineCount()):
            ol = polys.Outline(k)
            if any(ol.PointInside(pcbnew.VECTOR2I(mm(x), mm(y))) for x, y in gvias):
                continue
            bb = ol.BBox()
            x0, y0, x1, y1 = T(bb.GetLeft()), T(bb.GetTop()), T(bb.GetRight()), T(bb.GetBottom())
            found = None
            ys = [y0 + 0.1 * i for i in range(int((y1 - y0) / 0.1) + 1)]
            xs = [x0 + 0.1 * i for i in range(int((x1 - x0) / 0.1) + 1)]
            for y in ys:
                for x in xs:
                    c = pcbnew.VECTOR2I(mm(x), mm(y))
                    if not ol.PointInside(c) or ol.SquaredDistance(c, True) < mm(0.3) ** 2:
                        continue
                    if legal(x, y):
                        found = (round(x, 2), round(y, 2))
                        break
                if found:
                    break
            if found:
                v = pcbnew.PCB_VIA(b)
                v.SetPosition(pcbnew.VECTOR2I(mm(found[0]), mm(found[1])))
                v.SetWidth(mm(VD)); v.SetDrill(mm(VDR)); v.SetNet(gnd)
                b.Add(v)
                gvias.append(found)
                placed.append((z.GetZoneName(), found))
            else:
                placed.append((z.GetZoneName(), f"NO SPOT in fragment bbox {x0:.2f},{y0:.2f}-{x1:.2f},{y1:.2f}"))
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(str(PCB), b)
    for p in placed:
        print(p)


if __name__ == "__main__":
    from kicad_exit import run
    run(main)
