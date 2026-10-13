"""Side-by-side copper view of a board region (tracks/vias/pads + outline,
no pours) for review. Run with KiCad's python:
  .../python3 tools/corner_view.py OUT.svg X0 Y0 X1 Y1 LABEL=board.kicad_pcb ...
"""

import sys

import pcbnew

from kicad_exit import run

COL = {pcbnew.F_Cu: "#d23c3c", pcbnew.In1_Cu: "#2e9e44",
       pcbnew.In2_Cu: "#d98a1c", pcbnew.B_Cu: "#3c6ed2"}
NAME = {pcbnew.F_Cu: "F.Cu", pcbnew.In1_Cu: "In1.Cu (GND plane)",
        pcbnew.In2_Cu: "In2.Cu (PWR plane)", pcbnew.B_Cu: "B.Cu"}
# via label offsets (mm) per net, so labels sit beside their own via
KEY = {"USBH3_D_P": (0.1, 1.6), "USBH3_D_N": (-2.9, 1.6),
       "W_DISABLE1_n": (-3.6, -0.75), "GND": (0.35, -0.3),
       "+3V3_M2": (0.35, -0.3)}


def mm(v):
    return v / 1e6


def poly_path(ps, ox, oy):
    d = []
    for i in range(ps.OutlineCount()):
        o = ps.Outline(i)
        pts = [o.CPoint(k) for k in range(o.PointCount())]
        d.append("M" + " L".join(f"{mm(p.x)-ox:.3f},{mm(p.y)-oy:.3f}"
                                 for p in pts) + " Z")
    return " ".join(d)


def panel(path, x0, y0, x1, y1):
    b = pcbnew.LoadBoard(path)
    g = []
    outline = pcbnew.SHAPE_POLY_SET()
    b.GetBoardPolygonOutlines(outline)
    keep = outline.CloneDropTriangulation()
    keep.Deflate(pcbnew.FromMM(0.3), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,
                 pcbnew.FromMM(0.005))
    g.append(f'<path d="{poly_path(outline, x0, y0)}" fill="#f4f1e8" '
             f'stroke="#222" stroke-width="0.04"/>')
    g.append(f'<path d="{poly_path(keep, x0, y0)}" fill="none" stroke="#888" '
             f'stroke-width="0.025" stroke-dasharray="0.12 0.08"/>')
    for layer in (pcbnew.In2_Cu, pcbnew.In1_Cu, pcbnew.B_Cu, pcbnew.F_Cu):
        ps = pcbnew.SHAPE_POLY_SET()
        for fp in b.GetFootprints():
            for p in fp.Pads():
                if p.IsOnLayer(layer):
                    p.TransformShapeToPolygon(ps, layer, 0, pcbnew.FromMM(0.005),
                                              pcbnew.ERROR_INSIDE)
        for t in b.GetTracks():
            if t.IsOnLayer(layer) and t.GetClass() != "PCB_VIA":
                t.TransformShapeToPolygon(ps, layer, 0, pcbnew.FromMM(0.005),
                                          pcbnew.ERROR_INSIDE)
        g.append(f'<path d="{poly_path(ps, x0, y0)}" fill="{COL[layer]}" '
                 f'fill-opacity="0.55" fill-rule="nonzero"/>')
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA":
            p = t.GetPosition()
            if not (x0 - 1 < mm(p.x) < x1 + 1 and y0 - 1 < mm(p.y) < y1 + 1):
                continue
            cx, cy = mm(p.x) - x0, mm(p.y) - y0
            g.append(f'<circle cx="{cx:.3f}" cy="{cy:.3f}" '
                     f'r="{mm(t.GetWidth(pcbnew.F_Cu))/2:.3f}" fill="#777" '
                     f'stroke="#222" stroke-width="0.02"/>')
            g.append(f'<circle cx="{cx:.3f}" cy="{cy:.3f}" '
                     f'r="{mm(t.GetDrillValue())/2:.3f}" fill="#fff"/>')
            if t.GetNetname() in KEY:
                dx, dy = KEY[t.GetNetname()]
                tw = 0.17 * len(t.GetNetname())          # approx text width
                ax = cx + dx + (tw if dx < 0 else 0)      # leader end at text
                g.append(f'<line x1="{cx:.2f}" y1="{cy:.2f}" x2="{ax:.2f}" '
                         f'y2="{cy+dy-0.09:.2f}" stroke="#111" '
                         f'stroke-width="0.025"/>')
                g.append(f'<text x="{cx+dx:.2f}" y="{cy+dy:.2f}" font-size="0.28" '
                         f'fill="#111" stroke="#fff" stroke-width="0.08" '
                         f'paint-order="stroke">{t.GetNetname()}</text>')
    return "\n".join(g)


def main():
    out = sys.argv[1]
    x0, y0, x1, y1 = map(float, sys.argv[2:6])
    boards = [a.split("=", 1) for a in sys.argv[6:]]
    w, h = x1 - x0, y1 - y0
    gap = 0.6
    W = len(boards) * w + (len(boards) - 1) * gap
    H = h + 2.1
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -1.0 {W:.2f} {H:.2f}" '
         f'width="{W*60:.0f}" height="{H*60:.0f}" font-family="sans-serif">',
         f'<rect x="0" y="-1.0" width="{W:.2f}" height="{H:.2f}" fill="#fff"/>']
    for i, (label, path) in enumerate(boards):
        ox = i * (w + gap)
        s.append(f'<text x="{ox:.2f}" y="-0.4" font-size="0.5" '
                 f'font-weight="bold">{label}</text>')
        s.append(f'<svg x="{ox:.2f}" y="0" width="{w}" height="{h}" '
                 f'viewBox="0 0 {w} {h}" overflow="hidden">')
        s.append(panel(path, x0, y0, x1, y1))
        s.append("</svg>")
    lx = 0.0
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu):
        s.append(f'<rect x="{lx:.2f}" y="{h+0.2:.2f}" width="0.3" height="0.3" '
                 f'fill="{COL[layer]}" fill-opacity="0.55"/>'
                 f'<text x="{lx+0.4:.2f}" y="{h+0.47:.2f}" font-size="0.3">'
                 f'{NAME[layer]}</text>')
        lx += 3.0
    s.append(f'<text x="0" y="{h+0.95:.2f}" font-size="0.3" fill="#666">'
             f'dashed = 0.3 mm copper-to-edge keep-in · pours hidden · '
             f'grey rings = vias</text>')
    s.append("</svg>")
    open(out, "w").write("\n".join(s))
    print("wrote", out)


if __name__ == "__main__":
    run(main)
