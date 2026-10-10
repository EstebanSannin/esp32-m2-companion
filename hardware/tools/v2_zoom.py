"""Debug aid: render a window of the board (pads, tracks, vias of one layer
+ all vias) as an SVG with net-name labels, to see why a net is blocked.

  $KPY tools/v2_zoom.py X0 Y0 X1 Y1 LAYER OUT.svg [HIGHLIGHT_NET ...]
"""
import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "tools"))
PCB = HERE / "kicad" / "esp32_m2_companion.kicad_pcb"
T = pcbnew.ToMM


def main():
    x0, y0, x1, y1 = map(float, sys.argv[1:5])
    lname, out = sys.argv[5], sys.argv[6]
    hl = set(sys.argv[7:])
    b = pcbnew.LoadBoard(str(PCB))
    layer = b.GetLayerID(lname)
    S = 60.0  # px per mm
    W, H = (x1 - x0) * S, (y1 - y0) * S
    el = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}" height="{H:.0f}" '
          f'style="background:#fff" font-family="monospace">']

    def X(v): return (v - x0) * S
    def Y(v): return (v - y0) * S

    def col(net):
        return "#d62728" if net in hl else ("#888" if net in ("GND", "+3V3") else "#1f77b4")
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if not p.IsOnLayer(layer):
                continue
            bb = p.GetBoundingBox()
            l, t, r, bt = T(bb.GetLeft()), T(bb.GetTop()), T(bb.GetRight()), T(bb.GetBottom())
            if r < x0 or l > x1 or bt < y0 or t > y1:
                continue
            n = p.GetNetname()
            el.append(f'<rect x="{X(l):.1f}" y="{Y(t):.1f}" width="{(r-l)*S:.1f}" height="{(bt-t)*S:.1f}" '
                      f'fill="{col(n)}" fill-opacity="0.45" stroke="#000" stroke-width="0.5"/>')
            el.append(f'<text x="{X((l+r)/2):.1f}" y="{Y((t+bt)/2):.1f}" font-size="7" '
                      f'text-anchor="middle">{fp.GetReference()}.{p.GetNumber()} {n}</text>')
    for t in b.GetTracks():
        n = t.GetNetname()
        if t.Type() == pcbnew.PCB_VIA_T:
            x, y = T(t.GetX()), T(t.GetY())
            if x0 <= x <= x1 and y0 <= y <= y1:
                el.append(f'<circle cx="{X(x):.1f}" cy="{Y(y):.1f}" r="{0.225*S:.1f}" fill="none" '
                          f'stroke="{col(n)}" stroke-width="2"/>')
        elif t.GetLayer() == layer:
            a, c = t.GetStart(), t.GetEnd()
            el.append(f'<line x1="{X(T(a.x)):.1f}" y1="{Y(T(a.y)):.1f}" x2="{X(T(c.x)):.1f}" '
                      f'y2="{Y(T(c.y)):.1f}" stroke="{col(n)}" stroke-width="{T(t.GetWidth())*S:.1f}" '
                      f'stroke-opacity="0.7" stroke-linecap="round"/>')
    el.append("</svg>")
    Path(out).write_text("\n".join(el))
    print("wrote", out)


if __name__ == "__main__":
    from kicad_exit import run
    run(main)
