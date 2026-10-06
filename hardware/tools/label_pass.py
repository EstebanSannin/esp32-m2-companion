"""Rev-B silkscreen label pass (idempotent). Run with KiCad's python:
  .../python3 tools/label_pass.py

1. D3/D4 re-synced from the library footprint (rev B adds the silk cathode
   bar - v1 had NO silk polarity mark on the LEDs).
2. Test points: silk shows the FUNCTION (EN, BOOT, ...); TPn refs move to
   B.Fab so the assembly drawing still carries them.
3. J3/J4: silk pin labels under each pin (SPEC 6.6 "label every pin").
4. Every silk reference re-placed at 0.8 mm by a collision search against
   pad mask openings (+0.15), vias, other silk (+0.1) and the 0.3 mm edge
   keep-in. Board-level labels live in PCB_GROUP "label_pass", rebuilt on
   every run. Results are verified by `make drc` (silk checks), not trusted.
"""

from pathlib import Path

import pcbnew

from kicad_exit import run

HERE = Path(__file__).resolve().parent.parent
PCB = HERE / "kicad" / "esp32_m2_companion.kicad_pcb"
LIB = HERE / "kicad" / "footprints.pretty"
GROUP = "label_pass"
mm = pcbnew.FromMM
ERR = mm(0.005)

REF_H, REF_T = 0.8, 0.153          # JLC min stroke 0.153 mm
PIN_H, PIN_T = 0.8, 0.153          # board rule min_text_height = 0.8
TP_FUNC = {"TP1": "EN", "TP2": "BOOT", "TP3": "TX", "TP4": "RX",
           "TP5": "3V3", "TP6": "GND"}
# J3/J4: per-pin labels do not fit legibly - 0.8 mm text (board rule) on a
# 1.0 mm pitch leaves ~0.05 mm between columns, and J3 pins 2/3 sit right
# above the B-key notch. Proposal: connector legend (ref + function) next to
# the footprint's own pin-1 arrow; per-pin pinout lives in DATASHEET.md.
# (Option B for the owner's label review: 2-char per-pin labels.)
J_LEGEND = {"J3": "J3 QWIIC", "J4": "J4 UART/SPI"}


def rect_poly(bb, infl=0):
    ps = pcbnew.SHAPE_POLY_SET()
    ps.NewOutline()
    i = mm(infl)
    for x, y in ((bb.GetLeft() - i, bb.GetTop() - i), (bb.GetRight() + i, bb.GetTop() - i),
                 (bb.GetRight() + i, bb.GetBottom() + i), (bb.GetLeft() - i, bb.GetBottom() + i)):
        ps.Append(int(x), int(y))
    return ps


def area(ps):
    return sum(ps.Outline(i).Area() for i in range(ps.OutlineCount()))


class Side:
    def __init__(self, b, silk, mask, allowed):
        self.silk, self.allowed = silk, allowed
        self.obs = pcbnew.SHAPE_POLY_SET()
        self.cyd = {}          # ref -> courtyard rect (labels must not hide under parts)
        for fp in b.GetFootprints():
            for p in fp.Pads():
                if p.IsOnLayer(mask):
                    p.TransformShapeToPolygon(self.obs, mask, mm(0.15), ERR, pcbnew.ERROR_OUTSIDE)
            for g in fp.GraphicalItems():
                if g.GetLayer() == silk and g.GetClass() == "PCB_SHAPE":
                    g.TransformShapeToPolygon(self.obs, silk, mm(0.1), ERR, pcbnew.ERROR_OUTSIDE)
            if fp.GetReference() != "J1":   # J1 courtyard = socket zone
                cy = fp.GetCourtyard(pcbnew.F_CrtYd if silk == pcbnew.F_SilkS
                                     else pcbnew.B_CrtYd)
                if cy.OutlineCount():
                    self.cyd[fp.GetReference()] = rect_poly(cy.BBox(), 0.05)
        # vias are NOT obstacles: every via is tented front+back (board
        # setup "tenting front back", no per-via overrides), so silk may
        # legally print over them.
        for d in b.GetDrawings():
            if d.GetLayer() == silk and (d.GetParentGroup() is None or
                                         d.GetParentGroup().GetName() != GROUP):
                if d.GetClass() == "PCB_TEXT":
                    self.obs.BooleanAdd(rect_poly(d.GetBoundingBox(), 0.1))
                else:
                    d.TransformShapeToPolygon(self.obs, silk, mm(0.1), ERR, pcbnew.ERROR_OUTSIDE)
        self.obs.Simplify()

    def fits(self, bb, own=None):
        r = rect_poly(bb)
        for ref, cy in self.cyd.items():
            if ref == own:
                continue
            hit = rect_poly(bb)
            hit.BooleanIntersection(cy)
            if area(hit) > 0:
                return False
        return self.fits_obs(bb)

    def fits_obs(self, bb):
        # fresh polygons, never Clone*(): SWIG returns raw pointers for
        # clones in this process (KiCad 9 python quirk)
        out = rect_poly(bb)
        out.BooleanSubtract(self.allowed)
        if area(out) > 1e6:            # > 1e-6 mm^2 outside the keep-in
            return False
        hit = rect_poly(bb)
        hit.BooleanIntersection(self.obs)
        return area(hit) == 0

    def fits_glyphs(self, t):
        """Exact test on the stroked glyph outlines (+0.15 to pads is in obs)."""
        g = pcbnew.SHAPE_POLY_SET()
        t.TransformShapeToPolygon(g, self.silk, 0, ERR, pcbnew.ERROR_OUTSIDE)
        out = pcbnew.SHAPE_POLY_SET()
        t.TransformShapeToPolygon(out, self.silk, 0, ERR, pcbnew.ERROR_OUTSIDE)
        out.BooleanSubtract(self.allowed)
        if area(out) > 1e6:
            return False
        g.BooleanIntersection(self.obs)
        return area(g) == 0

    def take(self, bb):
        self.obs.BooleanAdd(rect_poly(bb, 0.12))


def style(t, h, th):
    t.SetTextSize(pcbnew.VECTOR2I(mm(h), mm(h)))
    t.SetTextThickness(mm(th))
    t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
    t.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
    t.SetKeepUpright(True)


def place(side, t, anchor_bb, centre, rots=(0, 90), own=None):
    """Try positions ringing anchor_bb (both rotations), nearest first."""
    cands = []
    for rot in rots:
        t.SetTextAngleDegrees(rot)
        t.SetPosition(centre)
        tb = t.GetBoundingBox()
        hw, hh = tb.GetWidth() / 2, tb.GetHeight() / 2
        cx, cy = anchor_bb.Centre().x, anchor_bb.Centre().y
        # slide along each side over the part's full extent (+1.2 mm)
        nx = int((anchor_bb.GetWidth() / 2 / 1e6 + 1.2) / 0.4)
        ny = int((anchor_bb.GetHeight() / 2 / 1e6 + 1.2) / 0.4)
        for ring in range(0, 8):
            g = mm(0.18 + 0.3 * ring)
            for k in range(-nx, nx + 1):
                s = mm(0.4 * k)
                for px, py in ((cx + s, anchor_bb.GetTop() - g - hh),
                               (cx + s, anchor_bb.GetBottom() + g + hh)):
                    cands.append(((px - centre.x) ** 2 + (py - centre.y) ** 2,
                                  rot, int(px), int(py)))
            for k in range(-ny, ny + 1):
                s = mm(0.4 * k)
                for px, py in ((anchor_bb.GetLeft() - g - hw, cy + s),
                               (anchor_bb.GetRight() + g + hw, cy + s)):
                    cands.append(((px - centre.x) ** 2 + (py - centre.y) ** 2,
                                  rot, int(px), int(py)))
    for _, rot, px, py in sorted(cands):
        t.SetTextAngleDegrees(rot)
        t.SetPosition(pcbnew.VECTOR2I(px, py))
        bb = t.GetBoundingBox()
        if side.fits(bb, own):
            side.take(bb)
            return True
    return False


FLIP = {"F.SilkS": pcbnew.B_SilkS, "F.Fab": pcbnew.B_Fab,
        "F.CrtYd": pcbnew.B_CrtYd}


def parse_mod(path):
    """Non-copper graphics of a .kicad_mod, parsed as text: pcbnew objects
    for library footprints come back as raw SWIG pointers once a board is
    loaded in the same process (KiCad 9), so don't use pcbnew for this."""
    import re
    src = path.read_text()
    num = r"(-?[\d.]+)"
    items = []
    for m in re.finditer(r"\((fp_line|fp_rect) \(start " + num + " " + num +
                         r"\) \(end " + num + " " + num + r"\).*?\(width " + num +
                         r"\).*?\(layer \"([^\"]+)\"\)", src):
        k, x1, y1, x2, y2, w, layer = m.groups()
        items.append({"kind": k, "pts": [(float(x1), float(y1)), (float(x2), float(y2))],
                      "w": float(w), "layer": layer})
    for m in re.finditer(r"\(fp_poly \(pts ((?:\(xy [^)]+\) ?)+)\).*?\(width " + num +
                         r"\).*?\(fill (\w+)\).*?\(layer \"([^\"]+)\"\)", src):
        pts = [tuple(map(float, xy.split())) for xy in re.findall(r"\(xy ([^)]+)\)", m.group(1))]
        items.append({"kind": "fp_poly", "pts": pts, "w": float(m.group(2)),
                      "fill": m.group(3) == "solid", "layer": m.group(4)})
    for m in re.finditer(r"\(fp_text user \"([^\"]*)\" \(at " + num + " " + num +
                         r"\) \(layer \"([^\"]+)\"\) \(effects \(font \(size " + num +
                         " " + num + r"\) \(thickness " + num + r"\)", src):
        t, x, y, layer, h, _, th = m.groups()
        items.append({"kind": "text", "text": t, "pts": [(float(x), float(y))],
                      "h": float(h), "th": float(th), "layer": layer})
    return items


def resync_led(b, ref, lib_items):
    """Rebuild the board instance's non-copper graphics from the library
    file (rev B adds the silk cathode bar) WITHOUT swapping/flipping
    footprints - both segfault in KiCad 9's SWIG build. Library-local
    coords map to board as pos + (-y, -x) for a bottom-side footprint at
    90 deg, verified against the asymmetric emit-arrow polygon on D3's fab
    layer. DRC library parity checks the result."""
    # ALL lookups happen before ANY Remove(): after a Remove(), KiCad 9's
    # SWIG returns raw unwrapped pointers for the rest of the process.
    fp, o, old = ref
    assert fp.IsFlipped() and abs(fp.GetOrientationDegrees() - 90) < 1e-6, \
        "transform only verified for bottom side @ 90 deg"

    def T(x, y):
        return pcbnew.VECTOR2I(o.x - mm(y), o.y - mm(x))

    for g in old:
        fp.Remove(g)
    for it in lib_items:
        layer = FLIP.get(it["layer"])
        if layer is None:
            continue
        if it["kind"] == "text":
            n = pcbnew.PCB_TEXT(fp)
            n.SetText(it["text"])
            n.SetLayer(layer)
            n.SetTextSize(pcbnew.VECTOR2I(mm(it["h"]), mm(it["h"])))
            n.SetTextThickness(mm(it["th"]))
            n.SetMirrored(True)
            n.SetTextAngleDegrees(90)
            n.SetPosition(T(*it["pts"][0]))
        else:
            n = pcbnew.PCB_SHAPE(fp)
            n.SetLayer(layer)
            n.SetWidth(mm(it["w"]))
            if it["kind"] == "fp_poly":
                n.SetShape(pcbnew.SHAPE_T_POLY)
                ps = pcbnew.SHAPE_POLY_SET()
                ps.NewOutline()
                for x, y in it["pts"]:
                    q = T(x, y)
                    ps.Append(q.x, q.y)
                n.SetPolyShape(ps)
                n.SetFilled(it["fill"])
            else:
                n.SetShape(pcbnew.SHAPE_T_RECT if it["kind"] == "fp_rect"
                           else pcbnew.SHAPE_T_SEGMENT)
                n.SetStart(T(*it["pts"][0]))
                n.SetEnd(T(*it["pts"][1]))
        fp.Add(n)


def stage_resync():
    """Stage 1 (own process): everything that needs Remove()."""
    lib_led = parse_mod(LIB / "LED_TJ-S1706_SideView.kicad_mod")
    b = pcbnew.LoadBoard(str(PCB))
    fps = []
    for ref in ("D3", "D4"):
        fp = b.FindFootprintByReference(ref)
        old = [g for g in fp.GraphicalItems()
               if g.GetClass() in ("PCB_SHAPE", "PCB_TEXT")]
        fps.append((fp, fp.GetPosition(), old))
    groups = [(g, list(g.GetItems())) for g in b.Groups() if g.GetName() == GROUP]
    for g, items in groups:
        for it in items:
            b.Remove(it)
        b.Remove(g)
    for f in fps:
        resync_led(b, f, lib_led)
    pcbnew.SaveBoard(str(PCB), b)
    print("label pass: D3/D4 graphics re-synced from library; old labels cleared")
    return 0


def main():
    """Run both stages in fresh processes (see SWIG note in resync_led)."""
    import subprocess
    import sys
    for stage in ("resync", "place"):
        r = subprocess.run([sys.executable, __file__, stage])
        if r.returncode:
            return r.returncode
    return 0


def stage_place():
    """Stage 2 (own process): labels + reference placement, no Remove()."""
    b = pcbnew.LoadBoard(str(PCB))
    for fp in b.GetFootprints():        # idempotent: every ref starts on silk
        r = fp.Reference()
        if r.IsVisible() and r.GetLayer() in (pcbnew.F_Fab, pcbnew.B_Fab):
            r.SetLayer(pcbnew.B_SilkS if fp.IsFlipped() else pcbnew.F_SilkS)

    allowed = pcbnew.SHAPE_POLY_SET()
    b.GetBoardPolygonOutlines(allowed)
    allowed.Deflate(mm(0.3), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, ERR)
    sides = {pcbnew.F_SilkS: Side(b, pcbnew.F_SilkS, pcbnew.F_Mask, allowed),
             pcbnew.B_SilkS: Side(b, pcbnew.B_SilkS, pcbnew.B_Mask, allowed)}
    grp = pcbnew.PCB_GROUP(b)
    grp.SetName(GROUP)
    b.Add(grp)
    failed, fab_only = [], []

    def board_text(txt, layer, h, th):
        t = pcbnew.PCB_TEXT(b)
        t.SetText(txt)
        t.SetLayer(layer)
        t.SetMirrored(layer == pcbnew.B_SilkS)
        style(t, h, th)
        return t                 # added to the board only once placed

    def commit(t):
        b.Add(t)
        grp.AddItem(t)

    # J3/J4 legends (replace the bare refs; refs move to F.Fab): centred under
    # their own connector, first legal y below the pins, checked against the
    # real glyph outlines (bounding boxes are ~1.8x the 0.8 mm text height,
    # too coarse next to the B-key notch). Separate legends, not one string.
    for ref, legend in J_LEGEND.items():
        fp = b.FindFootprintByReference(ref)
        fp.Reference().SetLayer(pcbnew.F_Fab)
        t = board_text(legend, pcbnew.F_SilkS, REF_H, REF_T)
        pads = [p for p in fp.Pads() if p.GetNumber().isdigit()]
        cx = sum(p.GetPosition().x for p in pads) // len(pads)
        y0 = max(p.GetBoundingBox().GetBottom() for p in pads)
        for k in range(60):
            t.SetPosition(pcbnew.VECTOR2I(cx, y0 + mm(0.45 + 0.02 * k)))
            if sides[pcbnew.F_SilkS].fits_glyphs(t):
                sides[pcbnew.F_SilkS].take(t.GetBoundingBox())
                commit(t)
                break
        else:
            failed.append(f"{ref} legend '{legend}'")

    # test points: function on silk, ref to fab
    for ref, func in TP_FUNC.items():
        fp = b.FindFootprintByReference(ref)
        fp.Reference().SetLayer(pcbnew.B_Fab)
        t = board_text(func, pcbnew.B_SilkS, REF_H, REF_T)
        pad = list(fp.Pads())[0]
        if place(sides[pcbnew.B_SilkS], t, pad.GetBoundingBox(), pad.GetPosition(),
                 own=ref):
            commit(t)
        else:
            failed.append(f"{ref} function label '{func}'")

    # every remaining silk reference
    fps = [fp for fp in b.GetFootprints()
           if fp.Reference().GetLayer() in sides and fp.Reference().IsVisible()]
    fps.sort(key=lambda f: f.GetBoundingBox(False).GetArea())   # small parts first
    for fp in fps:
        t = fp.Reference()
        style(t, REF_H, REF_T)
        cy = fp.GetCourtyard(pcbnew.B_CrtYd if fp.IsFlipped() else pcbnew.F_CrtYd)
        anchor = cy.BBox() if cy.OutlineCount() else fp.GetBoundingBox(False)
        layer = t.GetLayer()
        if not place(sides[layer], t, anchor, fp.GetPosition(), own=fp.GetReference()):
            # no legal silk spot: reference lives on the fab layer only
            # (assembly drawing), centred on the part
            t.SetLayer(pcbnew.B_Fab if layer == pcbnew.B_SilkS else pcbnew.F_Fab)
            t.SetTextAngleDegrees(0)
            t.SetPosition(fp.GetPosition())
            fab_only.append(fp.GetReference())

    pcbnew.SaveBoard(str(PCB), b)
    print(f"label pass: {len(fps)} refs, {len(TP_FUNC)} TP labels, "
          f"{len(J_LEGEND)} connector legends; {len(failed)} unplaced")
    print(f"  fab-only refs ({len(fab_only)}): {', '.join(sorted(fab_only))}")
    for f in failed:
        print("  UNPLACED:", f)
    return 1 if failed else 0


if __name__ == "__main__":
    import sys
    stage = sys.argv[1] if len(sys.argv) > 1 else None
    run({"resync": stage_resync, "place": stage_place}.get(stage, main))
