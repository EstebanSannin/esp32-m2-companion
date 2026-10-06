"""Assembly + fab drawing pages (SVG) drawn from the board, for gate review.

Run with KiCad's python (gen_drawings.py calls it):
  .../python3 tools/asm_view.py OUT_DIR TITLE REV DATE
Writes OUT_DIR/assembly.svg and OUT_DIR/fab.svg (A4 landscape, mm units).

Page 1: top view + bottom view AS SEEN FROM BELOW (= JLC's bottom preview),
4:1. Fab outlines, pads, refs, DNP crossed. Every polarized part and
connector shows its pad numbers; LEDs get explicit '+' (anode) / 'K'.
Page 2: outline with key dimensions, hole table (PTH / NPTH), fab notes.
"""

import sys
from html import escape
from pathlib import Path

import pcbnew

from kicad_exit import run

HERE = Path(__file__).resolve().parent.parent
PCB = HERE / "kicad" / "esp32_m2_companion.kicad_pcb"
ERR = pcbnew.FromMM(0.005)
SCALE = 3.2
POLAR = {"D1", "D2", "D3", "D4", "U1", "U2", "J3", "J4"}


def mm(v):
    return v / 1e6


class View:
    def __init__(self, b, bottom, ox, oy):
        self.b, self.bottom, self.ox, self.oy = b, bottom, ox, oy
        ol = pcbnew.SHAPE_POLY_SET()
        b.GetBoardPolygonOutlines(ol)
        bb = ol.BBox()                  # true outline (no edge stroke width)
        self.x0, self.x1 = mm(bb.GetLeft()), mm(bb.GetRight())
        self.y0 = mm(bb.GetTop())
        self.out = []

    def P(self, x, y):
        """board mm -> page mm (bottom side mirrored left-right)"""
        if self.bottom:
            x = self.x0 + self.x1 - x
        return self.ox + (x - self.x0) * SCALE, self.oy + (y - self.y0) * SCALE

    def poly(self, ps, **attr):
        d = []
        for i in range(ps.OutlineCount()):
            o = ps.Outline(i)
            pts = [self.P(mm(o.CPoint(k).x), mm(o.CPoint(k).y)) for k in range(o.PointCount())]
            d.append("M" + " L".join(f"{x:.2f},{y:.2f}" for x, y in pts) + " Z")
        a = " ".join(f'{k.replace("_", "-")}="{v}"' for k, v in attr.items())
        self.out.append(f'<path d="{" ".join(d)}" {a}/>')

    def text(self, x, y, s, size, **attr):
        px, py = self.P(x, y)
        a = " ".join(f'{k.replace("_", "-")}="{v}"' for k, v in attr.items())
        self.out.append(f'<text x="{px:.2f}" y="{py:.2f}" font-size="{size}" '
                        f'text-anchor="middle" dominant-baseline="central" {a}>{escape(s)}</text>')

    def draw(self):
        b = self.b
        side_cu = pcbnew.B_Cu if self.bottom else pcbnew.F_Cu
        fab = pcbnew.B_Fab if self.bottom else pcbnew.F_Fab
        outline = pcbnew.SHAPE_POLY_SET()
        b.GetBoardPolygonOutlines(outline)
        self.poly(outline, fill="#fbfaf6", stroke="#111", stroke_width="0.35")
        for fp in b.GetFootprints():
            on_side = fp.IsFlipped() == self.bottom
            if fp.GetReference() == "J1":
                continue
            # pads of this side's parts
            if on_side:
                ps = pcbnew.SHAPE_POLY_SET()
                for p in fp.Pads():
                    if p.IsOnLayer(side_cu):
                        p.TransformShapeToPolygon(ps, side_cu, 0, ERR, pcbnew.ERROR_INSIDE)
                self.poly(ps, fill="#c9c4b8", stroke="none")
            if not on_side:
                continue
            # fab-layer outline
            for g in fp.GraphicalItems():
                if g.GetLayer() == fab and g.GetClass() == "PCB_SHAPE":
                    ps = pcbnew.SHAPE_POLY_SET()
                    g.TransformShapeToPolygon(ps, fab, 0, ERR, pcbnew.ERROR_INSIDE)
                    self.poly(ps, fill="#333" if g.IsFilled() else "none",
                              stroke="#333", stroke_width="0.25")
            ref = fp.GetReference()
            c = fp.GetPosition()
            bbox = fp.GetBoundingBox(False)
            size = max(1.6, min(3.2, mm(min(bbox.GetWidth(), bbox.GetHeight())) * SCALE * 0.38))
            if fp.IsDNP():
                x0, y0 = self.P(mm(bbox.GetLeft()), mm(bbox.GetTop()))
                x1, y1 = self.P(mm(bbox.GetRight()), mm(bbox.GetBottom()))
                for a, bb2 in (((x0, y0), (x1, y1)), ((x0, y1), (x1, y0))):
                    self.out.append(f'<line x1="{a[0]:.2f}" y1="{a[1]:.2f}" x2="{bb2[0]:.2f}" '
                                    f'y2="{bb2[1]:.2f}" stroke="#c0392b" stroke-width="0.4"/>')
                self.text(mm(c.x), mm(bbox.GetBottom()) + 0.4, "DNP", "1.6",
                          fill="#c0392b", font_family="sans-serif")
            self.text(mm(c.x), mm(c.y), ref, f"{size:.2f}",
                      fill="#555" if fp.IsDNP() else "#0b3d91",
                      font_weight="bold", font_family="sans-serif",
                      stroke="#fbfaf6", stroke_width="0.5", paint_order="stroke")
            if "LED" in fp.GetFPIDAsString():
                pads = {p.GetNumber(): p.GetPosition() for p in fp.Pads()}
                a, k = pads["2"], pads["1"]
                ux, uy = mm(a.x - k.x), mm(a.y - k.y)
                n = (ux * ux + uy * uy) ** 0.5
                ux, uy = ux / n, uy / n
                # beside each pad, outside the left card edge (LEDs sit flush
                # with it); D3/D4 are end to end, so never along the axis
                ex = self.x0 - 1.0
                for q, lab in ((a, "+"), (k, "K")):
                    self.text(ex, mm(q.y), lab, "2.8", fill="#c0392b",
                              font_weight="bold", font_family="sans-serif")
                    x1, y1 = self.P(ex + 0.45, mm(q.y))
                    x2, y2 = self.P(mm(q.x) - 0.3, mm(q.y))
                    self.out.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" '
                                    f'y2="{y2:.2f}" stroke="#c0392b" stroke-width="0.25"/>')
                self.text(ex - 1.3, mm((a.y + k.y) / 2), ref, "2.2", fill="#c0392b",
                          font_family="sans-serif")
                continue
            if ref in POLAR:
                for p in fp.Pads():
                    n = p.GetNumber()
                    if not n or not n.isdigit():
                        continue
                    if ref == "U2" and n not in ("1",):
                        continue
                    q = p.GetPosition()
                    label = n
                    self.text(mm(q.x), mm(q.y), label, "1.6",
                              fill="#c0392b", font_weight="bold", font_family="sans-serif")
        return "\n".join(self.out)


def page(title, rev, date, body, sheet, notes):
    W, H = 297, 210
    tb = (f'<g font-family="sans-serif">'
          f'<rect x="10" y="10" width="{W-20}" height="{H-20}" fill="none" stroke="#111" stroke-width="0.5"/>'
          f'<rect x="{W-110}" y="{H-38}" width="100" height="28" fill="#fff" stroke="#111" stroke-width="0.4"/>'
          f'<text x="{W-107}" y="{H-31}" font-size="4.2" font-weight="bold">{escape(title)}</text>'
          f'<text x="{W-107}" y="{H-25}" font-size="3">{escape(sheet)}</text>'
          f'<text x="{W-107}" y="{H-19.5}" font-size="2.6">Rev {escape(rev)}</text>'
          f'<text x="{W-107}" y="{H-14.5}" font-size="2.6">{escape(date)} · CERN-OHL-P v2 · Stefano Viola</text>'
          + "".join(f'<text x="{W-107}" y="{20 + 4.2*i}" font-size="2.6" '
                    f'xml:space="preserve">{escape(n)}</text>'
                    for i, n in enumerate(notes)) + "</g>")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" '
            f'viewBox="0 0 {W} {H}"><rect width="{W}" height="{H}" fill="#fff"/>{body}{tb}</svg>')


def main():
    out, title, rev, date = Path(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4]
    b = pcbnew.LoadBoard(str(PCB))
    top = View(b, False, 18, 18).draw()
    bot = View(b, True, 18 + 22 * SCALE + 14, 18).draw()
    lab = ('<g font-family="sans-serif" font-size="4" font-weight="bold">'
           f'<text x="18" y="15">TOP</text>'
           f'<text x="{18 + 22*SCALE + 14}" y="15">BOTTOM — seen from below</text></g>')
    notes = ["Scale 3.2:1. Grey = copper pads; bold = refdes.",
             "Red numbers = pad numbers (polarized parts, connectors).",
             "LEDs: '+' = anode (pad 2, wired to R3/R4),",
             "      'K' = cathode (pad 1) = SILK BAR end.",
             "D1/D2 BAT54A: pin 3 = common anode (card side).",
             "U1 USBLC6: pin 1 = I/O1 (D+ in), silk triangle.",
             "J3 pin 1 = GND (Qwiic); J4 pin 1 = TXD0.",
             "DNP (red X): R5 R6 (I2C pull-ups), C8 C9 (USB SI).",
             "TP1-6: bare pads, not placed (silk: function).",
             "Bottom view mirrored like JLC's bottom preview:",
             "N/S (screw / fingers) is invariant, E/W swap.",
             "Verify every polarized part against the JLC",
             "preview with fab/polarity_checklist.md."]
    (out / "assembly.svg").write_text(page(
        "ESP32-M2-COMPANION — assembly", rev, date, top + bot + lab,
        "Sheet 1/2 · assembly drawing", notes))

    # fab page: outline + dims + hole table
    v = View(b, False, 30, 22)
    outline = pcbnew.SHAPE_POLY_SET()
    b.GetBoardPolygonOutlines(outline)
    v.poly(outline, fill="#fbfaf6", stroke="#111", stroke_width="0.35")
    holes = {}
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if p.GetDrillSize().x > 0:
                kind = "NPTH" if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH else "PTH"
                key = (kind, round(mm(p.GetDrillSize().x), 2))
                holes[key] = holes.get(key, 0) + 1
                if kind == "NPTH":
                    q = p.GetPosition()
                    x, y = v.P(mm(q.x), mm(q.y))
                    r = mm(p.GetDrillSize().x) / 2 * SCALE
                    v.out.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r:.2f}" fill="none" '
                                 f'stroke="#c0392b" stroke-width="0.5" stroke-dasharray="1.5 1"/>')
                    v.out.append(f'<text x="{x + r + 2:.2f}" y="{y - 2:.2f}" font-size="3" '
                                 f'fill="#c0392b" font-family="sans-serif">Ø{mm(p.GetDrillSize().x):.1f} '
                                 f'NPTH — NOT plated, no copper</text>')
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA":
            key = ("PTH via", round(mm(t.GetDrillValue()), 2))
            holes[key] = holes.get(key, 0) + 1
    bb = outline.BBox()
    (x0, y0), (x1, y1) = v.P(mm(bb.GetLeft()), mm(bb.GetTop())), v.P(mm(bb.GetRight()), mm(bb.GetBottom()))
    dims = (f'<g font-family="sans-serif" font-size="3.2" stroke="#111" stroke-width="0.25">'
            f'<line x1="{x0}" y1="{y1+6}" x2="{x1}" y2="{y1+6}"/><text x="{(x0+x1)/2}" y="{y1+11}" '
            f'text-anchor="middle" stroke="none">{mm(bb.GetWidth()):.2f} mm</text>'
            f'<line x1="{x1+6}" y1="{y0}" x2="{x1+6}" y2="{y1}"/><text x="{x1+8}" y="{(y0+y1)/2}" '
            f'stroke="none">{mm(bb.GetHeight()):.2f} mm</text></g>')
    table = ['<g font-family="sans-serif" font-size="3"><text x="150" y="30" font-size="4" '
             'font-weight="bold">Hole table</text>']
    for i, ((kind, d), n) in enumerate(sorted(holes.items())):
        table.append(f'<text x="150" y="{37 + 5*i}">{kind:8} Ø{d:.2f} mm × {n}</text>')
    table.append("</g>")
    fab_notes = ["4 layers SIG/GND/PWR/SIG, 0.80 mm, stackup JLC04081H-3313",
                 "ENIG; hard-gold fingers; NO bevel (board < 50 mm):",
                 "  hand-chamfer the leading edge before first insertion",
                 "Mounting notch: NPTH (separate -NPTH.drl) - do NOT",
                 "  select castellated holes",
                 "Min track/space 0.127 mm (5 mil), min drill 0.30 mm",
                 "Vias tented both sides",
                 "Assembly: both sides; 22 placed parts; DNP R5 R6 C8 C9",
                 "CPL: D3/D4 +180° vs KiCad (JLC_ROT) - VERIFY PREVIEW"]
    (out / "fab.svg").write_text(page(
        "ESP32-M2-COMPANION — fabrication", rev, date,
        "\n".join(v.out) + dims + "".join(table), "Sheet 2/2 · fab drawing", fab_notes))
    print("wrote", out / "assembly.svg", out / "fab.svg")


if __name__ == "__main__":
    run(main)
