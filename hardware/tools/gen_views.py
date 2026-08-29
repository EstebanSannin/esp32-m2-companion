"""Generate datasheet figures from the board: labeled top/bottom component
views (Mallow-datasheet style: line drawing + callouts) and a dimensioned
mechanical drawing. Run with KiCad's bundled python (needs pcbnew):

  ~/Applications/.../python3 tools/gen_views.py

Outputs docs/img/view_top.(svg|png), view_bottom.(svg|png), mechanical.(svg|png).
"""

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
ROOT = HERE.parent
IMG = ROOT / "docs" / "img"

sys.path.insert(0, str(Path(__file__).parent))
import pcbnew  # noqa: E402

ORIGIN = (100.0, 150.0)  # must match gen_pcb.py

from view_defs import TOP_CALLOUTS, BOT_CALLOUTS  # noqa: E402

S = 10.0  # svg px per mm


def card_xy(fp):
    p = fp.GetPosition()
    return (pcbnew.ToMM(p.x) - ORIGIN[0], pcbnew.ToMM(p.y) - ORIGIN[1] + 42.0)
    # returns x in [-11,11], y in [0(top of card)..42(edge)]


def outline_path():
    """Card outline as SVG path, y=0 at card TOP (screw end), 42 = edge."""
    # verified geometry: 22x42, key notch x 5..6.2 depth 3.5 (full R end),
    # screw semicircle r1.75 at top centre, corner radii ~0.5/0.3
    def pt(x, y):
        return f"{(x + 11) * S:.1f},{y * S:.1f}"
    p = f"M {pt(-10.5, 0)} L {pt(10.5, 0)} Q {pt(11, 0)} {pt(11, 0.5)} "
    p += f"L {pt(11, 37.8)} L {pt(10.8, 38)} L {pt(10.45, 38)} L {pt(9.95, 38.5)} "
    p += f"L {pt(9.95, 41.8)} Q {pt(9.95, 42)} {pt(9.75, 42)} "
    p += f"L {pt(6.2, 42)} L {pt(6.2, 39.1)} A {0.6*S:.1f} {0.6*S:.1f} 0 0 0 {pt(5.0, 39.1)} "
    p += f"L {pt(5.0, 42)} L {pt(-9.75, 42)} Q {pt(-9.95, 42)} {pt(-9.95, 41.8)} "
    p += f"L {pt(-9.95, 38.5)} L {pt(-10.45, 38)} L {pt(-10.8, 38)} L {pt(-11, 37.8)} "
    p += f"L {pt(-11, 0.5)} Q {pt(-11, 0)} {pt(-10.5, 0)} Z"
    return p


def svg_header(w, h, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" font-family="Helvetica,Arial,sans-serif">'
            f'<rect width="{w}" height="{h}" fill="white"/>'
            f'<text x="{w/2}" y="28" text-anchor="middle" font-size="20" '
            f'font-weight="bold">{title}</text>')


def draw_board(g, side, board):
    """Return svg elements: outline, screw circle, fingers, courtyards+refs."""
    e = []
    e.append(f'<path d="{outline_path()}" fill="#eef3ee" stroke="#333" stroke-width="2"/>')
    # screw semicircle
    e.append(f'<circle cx="{11*S}" cy="{1.0*S}" r="{1.75*S}" fill="white" stroke="#333" stroke-width="2"/>')
    e.append(f'<circle cx="{11*S}" cy="{1.0*S}" r="{2.75*S}" fill="none" stroke="#999" stroke-width="1" stroke-dasharray="4 3"/>')
    # gold fingers strip
    for x0, x1 in ((-9.25, 4.75), (6.5, 9.25)):
        n = int(round((x1 - x0) / 0.5))
        for i in range(n + 1):
            fx = x0 + i * 0.5 + (0.25 if side == "B" else 0.0)
            if fx > x1:
                continue
            e.append(f'<rect x="{(fx+11-0.175)*S:.1f}" y="{39.5*S}" width="{0.35*S:.1f}" '
                     f'height="{2.5*S}" fill="#d4af37" stroke="none"/>')
    # footprints on this side as courtyard rects
    layer = pcbnew.F_CrtYd if side == "F" else pcbnew.B_CrtYd
    for fp in board.GetFootprints():
        if fp.GetReference() == "J1":
            continue
        on_top = fp.GetLayerName() == "F.Cu"
        if (side == "F") != on_top:
            continue
        if fp.GetReference() == "U2":
            # WROOM footprint courtyard includes its antenna keep-out;
            # draw the true module body (18 x 25.5, datasheet Table 1-1)
            cx, cy = card_xy(fp)
            x, y, w, h = cx - 9.0, cy - 12.75, 18.0, 25.5
            e.append(f'<rect x="{(x+11)*S:.1f}" y="{y*S:.1f}" width="{w*S:.1f}" height="{h*S:.1f}" fill="#cfd8dc" stroke="#455a64" stroke-width="1.2"/>')
            # antenna region = module top 6 mm (toward card top edge)
            e.append(f'<rect x="{(x+11)*S:.1f}" y="{y*S:.1f}" width="{w*S:.1f}" height="{6*S:.1f}" fill="#eceff1" stroke="#455a64" stroke-width="0.8"/>')
            e.append(f'<text x="{(x+11+w/2)*S:.1f}" y="{(y+3)*S+4:.1f}" text-anchor="middle" font-size="10" fill="#607d8b">PCB ANTENNA</text>')
            e.append(f'<text x="{(x+11+w/2)*S:.1f}" y="{(y+h/2+2)*S:.1f}" text-anchor="middle" font-size="13" fill="#263238">U2</text>')
            continue
        bb = fp.GetCourtyard(layer).BBox()
        if bb.GetWidth() == 0:
            continue
        x = pcbnew.ToMM(bb.GetX()) - ORIGIN[0]
        y = pcbnew.ToMM(bb.GetY()) - ORIGIN[1] + 42.0
        w = pcbnew.ToMM(bb.GetWidth())
        h = pcbnew.ToMM(bb.GetHeight())
        if side == "B":   # mirror for bottom view (viewed from bottom)
            x = -(x + w)
        big = w * h > 30
        e.append(f'<rect x="{(x+11)*S:.1f}" y="{y*S:.1f}" width="{w*S:.1f}" height="{h*S:.1f}" '
                 f'fill="{"#cfd8dc" if big else "#b0bec5"}" stroke="#455a64" stroke-width="1.2"/>')
        fs = 11 if w * h > 8 else 8
        e.append(f'<text x="{(x+11+w/2)*S:.1f}" y="{(y+h/2)*S+3:.1f}" text-anchor="middle" '
                 f'font-size="{fs}" fill="#263238">{fp.GetReference()}</text>')
    if side == "F":
        # antenna keep-out zone
        e.append(f'<rect x="{1*S}" y="{4.4*S}" width="{20*S}" height="{6.2*S}" fill="none" '
                 f'stroke="#c62828" stroke-width="1.5" stroke-dasharray="6 4"/>')
        e.append(f'<text x="{11*S}" y="{4.4*S-5}" text-anchor="middle" font-size="12" '
                 f'fill="#c62828">RF KEEP-OUT</text>')
    return e


def callouts(board, side, defs, board_left_px, mirror):
    """Numbered circles with leader lines + legend rows."""
    e, legend = [], []
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    special = {"ANT": (0.0, 7.5), "SCR": (0.0, 1.0),
               "J1": (0.0, 40.5)}
    for i, (ref, text) in enumerate(defs, 1):
        if ref in special:
            cx, cy = special[ref]
        else:
            cx, cy = card_xy(fps[ref])
        if mirror:
            cx = -cx
        px, py = board_left_px + (cx + 11) * S, 46 + cy * S
        lx = board_left_px - 40 if (i % 2) else board_left_px + 22 * S + 40
        e.append(f'<line x1="{px}" y1="{py}" x2="{lx}" y2="{py}" stroke="#888" stroke-width="1"/>')
        e.append(f'<circle cx="{lx}" cy="{py}" r="11" fill="#1a237e"/>')
        e.append(f'<text x="{lx}" y="{py+4}" text-anchor="middle" font-size="12" '
                 f'fill="white" font-weight="bold">{i}</text>')
        legend.append((i, text))
    return e, legend


def make_view(board, side, title, fname):
    W, H = 820, 560
    bl = (W - 22 * S) / 2
    svg = [svg_header(W, H, title)]
    svg.append(f'<g transform="translate({bl},46)">')
    svg += draw_board([], side, board)
    svg.append('</g>')
    co, legend = callouts(board, side,
                          TOP_CALLOUTS if side == "F" else BOT_CALLOUTS,
                          bl, side == "B")
    svg += co
    svg.append('</svg>')
    (IMG / f"{fname}.svg").write_text("\n".join(svg))
    subprocess.run(["rsvg-convert", "-w", "1640", "-f", "png", "-o",
                    str(IMG / f"{fname}.png"), str(IMG / f"{fname}.svg")],
                   check=True)
    return legend


def dim_h(svg, x0, x1, y, label):
    svg.append(f'<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" stroke="#000" stroke-width="1" marker-start="url(#a)" marker-end="url(#b)"/>')
    svg.append(f'<text x="{(x0+x1)/2}" y="{y-6}" text-anchor="middle" font-size="14">{label}</text>')


def dim_v(svg, x, y0, y1, label):
    svg.append(f'<line x1="{x}" y1="{y0}" x2="{x}" y2="{y1}" stroke="#000" stroke-width="1" marker-start="url(#a)" marker-end="url(#b)"/>')
    svg.append(f'<text x="{x-8}" y="{(y0+y1)/2}" text-anchor="middle" font-size="14" transform="rotate(-90 {x-8} {(y0+y1)/2})">{label}</text>')


def make_mechanical():
    W, H = 760, 620
    bl = 160.0
    svg = [svg_header(W, H, "Mechanical data (mm)")]
    svg.append('<defs>'
               '<marker id="a" markerWidth="8" markerHeight="8" refX="1" refY="3" orient="auto"><path d="M7,0 L1,3 L7,6" fill="none" stroke="black"/></marker>'
               '<marker id="b" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto"><path d="M1,0 L7,3 L1,6" fill="none" stroke="black"/></marker>'
               '</defs>')
    svg.append(f'<g transform="translate({bl},60)">')
    svg.append(f'<path d="{outline_path()}" fill="none" stroke="#333" stroke-width="2"/>')
    svg.append(f'<circle cx="{11*S}" cy="{1.0*S}" r="{1.75*S}" fill="none" stroke="#333" stroke-width="2"/>')
    for x0, x1 in ((-9.25, 4.75), (6.5, 9.25)):
        svg.append(f'<rect x="{(x0+11)*S}" y="{39.5*S}" width="{(x1-x0)*S}" height="{2.5*S}" fill="none" stroke="#999" stroke-width="1"/>')
    svg.append('</g>')
    # dimensions
    dim_h(svg, bl, bl + 22 * S, 50, "22.00")
    dim_v(svg, bl - 26, 60, 60 + 42 * S, "42.00")
    dim_h(svg, bl + 16 * S, bl + 17.2 * S, 60 + 38.2 * S, "")
    svg.append(f'<text x="{bl+22*S+14}" y="{60+40.5*S}" font-size="13">Key B notch</text>')
    svg.append(f'<text x="{bl+22*S+14}" y="{60+1.0*S+4}" font-size="13">Mounting notch Ø3.50</text>')
    svg.append(f'<line x1="{bl+11*S+1.75*S}" y1="{60+1.0*S}" x2="{bl+22*S+10}" y2="{60+1.0*S}" stroke="#888" stroke-width="1"/>')
    svg.append(f'<text x="{bl+22*S+14}" y="{60+40.9*S+18}" font-size="13">Gold fingers 0.5 mm pitch, bevelled</text>')
    svg.append('</svg>')
    (IMG / "mechanical.svg").write_text("\n".join(svg))
    subprocess.run(["rsvg-convert", "-w", "1520", "-f", "png", "-o",
                    str(IMG / "mechanical.png"), str(IMG / "mechanical.svg")],
                   check=True)


def main():
    IMG.mkdir(parents=True, exist_ok=True)
    board = pcbnew.LoadBoard(str(HERE / "kicad" / "esp32_m2_companion.kicad_pcb"))
    lt = make_view(board, "F", "Top side", "view_top")
    lb = make_view(board, "B", "Bottom side (viewed from bottom)", "view_bottom")
    make_mechanical()
    print("TOP legend:", lt)
    print("BOTTOM legend:", lb)


if __name__ == "__main__":
    main()
