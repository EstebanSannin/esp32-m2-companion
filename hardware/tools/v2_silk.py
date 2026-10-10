"""v2 GATE V3: silkscreen cleanup (DRC silk_overlap / silk_over_copper /
text_height).

1. Board texts: revision line -> v2.0 Rev A; the rev-B test-point labels of
   the removed TP3-TP6 (TX/RX/3V3/GND) are deleted; EN / BOOT move next to
   TP1 / TP2 (which also moved at GATE V3).
2. Reference designators: all 0.8 mm (DRC min_text_height), 0.15 stroke.
   Each label is kept where it is if legal, else placed at the first legal
   spot of a ring of candidates around its part (4 sides x 2 rotations, then
   corners, then a wider ring), else the nearest legal point of a 0.2 mm grid
   within 2.5 mm of the part. Legal = text box clear of every pad / NPTH
   opening on that side (copper exposed through the mask), of every other
   silkscreen item on that side, and >= 0.3 mm inside the board outline.
   A label with no legal spot is hidden (the assembly drawing still shows
   every reference) and listed.
  $KPY tools/v2_silk.py [--dry]
"""
import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "tools"))
PCB = HERE / "kicad" / "esp32_m2_companion.kicad_pcb"
DRY = "--dry" in sys.argv
H, TH = 0.8, 0.15
M_PAD, M_SILK, M_EDGE = 0.1, 0.05, 0.3
REV_OLD, REV_NEW = "v1.0 Rev B 2026-10", "v2.0 Rev A 2026-10"
DROP = {"TX", "RX", "3V3", "GND"}
MOVE = {"EN": "TP1", "BOOT": "TP2"}


def main():
    b = pcbnew.LoadBoard(str(PCB))
    T, mm = pcbnew.ToMM, pcbnew.FromMM
    V = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))

    def box(bb, m=0.0):
        return (T(bb.GetLeft()) - m, T(bb.GetTop()) - m, T(bb.GetRight()) + m, T(bb.GetBottom()) + m)

    def hit(a, c):
        return not (a[2] <= c[0] or c[2] <= a[0] or a[3] <= c[1] or c[3] <= a[1])

    outline = pcbnew.SHAPE_POLY_SET()
    b.GetBoardPolygonOutlines(outline)
    ol = outline.Outline(0)

    def inside(bx):
        for x, y in ((bx[0], bx[1]), (bx[2], bx[1]), (bx[0], bx[3]), (bx[2], bx[3])):
            c = V(x, y)
            if not ol.PointInside(c) or ol.SquaredDistance(c, True) < mm(M_EDGE) ** 2:
                return False
        return True

    log = []
    # ---- 1. board texts ---------------------------------------------------
    texts = [d for d in b.GetDrawings() if isinstance(d, pcbnew.PCB_TEXT)]
    doomed = []
    for t in texts:
        s = t.GetText()
        if s == REV_OLD:
            t.SetText(REV_NEW); log.append(f"text '{REV_OLD}' -> '{REV_NEW}'")
        elif s in DROP and t.GetLayer() == pcbnew.B_SilkS:
            doomed.append(t); log.append(f"text '{s}' deleted (TP removed in v2)")
    side_layers = {pcbnew.B_SilkS: pcbnew.B_Cu, pcbnew.F_SilkS: pcbnew.F_Cu}

    # obstacle sets per silk layer
    def pad_boxes(cu):
        out = []
        for fp in b.GetFootprints():
            for p in fp.Pads():
                if p.IsOnLayer(cu) or p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                    out.append(box(p.GetBoundingBox(), M_PAD))
        return out
    pads = {sl: pad_boxes(cu) for sl, cu in side_layers.items()}
    silk = {sl: [] for sl in side_layers}         # (owner, box)
    for fp in b.GetFootprints():
        for g in fp.GraphicalItems():
            if g.GetLayer() in silk and not isinstance(g, pcbnew.PCB_TEXT):
                silk[g.GetLayer()].append((fp.GetReference() + ":g", box(g.GetBoundingBox(), M_SILK)))
    for t in texts:
        if t not in doomed and t.GetLayer() in silk and t.GetText() not in MOVE:
            silk[t.GetLayer()].append(("text:" + t.GetText(), box(t.GetBoundingBox(), M_SILK)))

    def legal(item, sl, own):
        bx = box(item.GetBoundingBox())
        if not inside(bx):
            return False
        if any(hit(bx, p) for p in pads[sl]):
            return False
        return not any(hit(bx, s) for o, s in silk[sl] if o != own)

    def place(item, sl, own, cx, cy, crt):
        """try current spot, then rings around crt (x0,y0,x1,y1)."""
        cur = item.GetPosition()
        cands = [(T(cur.x), T(cur.y), item.GetTextAngleDegrees())]
        for gap in (0.55, 0.9, 1.3):
            for ang in (0, 90):
                w = len(item.GetShownText(False)) * H * 0.75 if ang == 0 else H
                cands += [(cx, crt[1] - gap, ang), (cx, crt[3] + gap, ang),
                          (crt[0] - gap - w / 2 + 0.4, cy, ang), (crt[2] + gap + w / 2 - 0.4, cy, ang)]
                cands += [(crt[0] - w / 2, crt[1] - gap, ang), (crt[2] + w / 2, crt[1] - gap, ang),
                          (crt[0] - w / 2, crt[3] + gap, ang), (crt[2] + w / 2, crt[3] + gap, ang)]
        # fallback: 0.2 mm grid within 2.5 mm of the part centre, nearest first
        grid = [(cx + i * 0.2, cy + j * 0.2, ang) for i in range(-12, 13) for j in range(-12, 13)
                for ang in (0, 90) if (i * i + j * j) * 0.04 <= 2.5 ** 2]
        grid.sort(key=lambda c: (c[0] - cx) ** 2 + (c[1] - cy) ** 2)
        for x, y, ang in cands + grid:
            item.SetPosition(V(x, y)); item.SetTextAngleDegrees(ang)
            if legal(item, sl, own):
                return True
        item.SetPosition(cur)
        return False

    # EN / BOOT labels beside their test points
    for t in texts:
        if t.GetText() in MOVE and t not in doomed:
            fp = b.FindFootprintByReference(MOVE[t.GetText()])
            t.SetTextSize(V(H, H)); t.SetTextThickness(mm(TH))
            crt = box(fp.GetBoundingBox(False, False))
            ok = place(t, t.GetLayer(), "text:" + t.GetText(), T(fp.GetX()), T(fp.GetY()), crt)
            silk[t.GetLayer()].append(("text:" + t.GetText(), box(t.GetBoundingBox(), M_SILK)))
            log.append(f"text '{t.GetText()}' next to {MOVE[t.GetText()]}: {'ok' if ok else 'NO SPOT'}")

    # ---- 2. reference designators -----------------------------------------
    fps = sorted(b.GetFootprints(), key=lambda f: (f.GetReference()[0], f.GetReference()))
    for fp in fps:
        r = fp.Reference()
        if not r.IsVisible() or r.GetLayer() not in silk:
            continue
        r.SetTextSize(V(H, H)); r.SetTextThickness(mm(TH))
        silk[r.GetLayer()].append((fp.GetReference(), box(r.GetBoundingBox(), M_SILK)))
    hidden = []
    for fp in fps:
        r = fp.Reference()
        if not r.IsVisible() or r.GetLayer() not in silk:
            continue
        sl = r.GetLayer()
        ref = fp.GetReference()
        silk[sl] = [(o, s) for o, s in silk[sl] if o != ref]
        sh = fp.GetCourtyard(pcbnew.B_CrtYd if fp.IsFlipped() else pcbnew.F_CrtYd)
        crt = box(sh.BBox()) if sh.OutlineCount() else box(fp.GetBoundingBox(False, False))
        if place(r, sl, ref, T(fp.GetX()), T(fp.GetY()), crt):
            silk[sl].append((ref, box(r.GetBoundingBox(), M_SILK)))
        else:
            r.SetVisible(False)
            hidden.append(ref)
    log.append(f"hidden references ({len(hidden)}): {', '.join(hidden)}")
    print("\n".join(log))
    if not DRY:
        for t in doomed:
            b.Remove(t)
        pcbnew.SaveBoard(str(PCB), b)


if __name__ == "__main__":
    from kicad_exit import run
    run(main)
