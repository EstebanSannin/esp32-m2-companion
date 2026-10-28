"""Debug reference map: the kicad-cli 3D renders of both sides with EVERY
reference designator printed on its part (owner decision 2026-10-28: the
silkscreen labels only ICs / transistors / LEDs; passives are found here).

  uv run python tools/gen_ref_map.py <top.png> <bottom.png>

Inputs are `kicad-cli pcb render --side top|bottom` images (`make render`
writes them); outputs docs/img/ref_map_top.png, ref_map_bottom.png.
Image <-> board mapping: the board outline is found in the render (the
background is a blue-grey gradient), the bottom view is mirrored in x.
"""

import sys
from pathlib import Path

import sexpdata
from PIL import Image, ImageDraw, ImageFont
from sexpdata import Symbol

HERE = Path(__file__).resolve().parent.parent
PCB = HERE / "kicad" / "esp32_m2_companion.kicad_pcb"
IMG = HERE.parent / "docs" / "img"
FONT = "/System/Library/Fonts/Helvetica.ttc"
ORIGIN = (100.0, 150.0)  # must match gen_pcb.py


def sub(node, name):
    return [x for x in node if isinstance(x, list) and x and x[0] == Symbol(name)]


def board():
    """card outline: M.2 2242, 22 x 42 mm, finger edge at ORIGIN (gen_pcb.py)
    (the Edge.Cuts outline lives inside the J1 footprint)."""
    data = sexpdata.loads(PCB.read_text())
    parts = []
    for n in data:
        if isinstance(n, list) and n and n[0] == Symbol("footprint"):
            layer = str(sub(n, "layer")[0][1])
            at = sub(n, "at")[0]
            ref = next(str(p[2]) for p in sub(n, "property") if str(p[1]) == "Reference")
            if ref != "J1":
                parts.append((ref, layer, float(at[1]), float(at[2])))
    x0, y1 = ORIGIN
    return (x0 - 11.0, y1 - 42.0, x0 + 11.0, y1), parts


def outline_px(im):
    """board bbox in the render: the first/last non-background pixel on a
    row through the middle and a column at 1/4 width (clear of the notches)."""
    px, (w, h) = im.load(), im.size
    bg = lambda p: p[2] - p[0] > 12 and abs(p[0] - p[1]) < 4
    xs = [x for x in range(w) if not bg(px[x, h // 2])]
    ys = [y for y in range(h) if not bg(px[w // 4, y])]
    return min(xs), min(ys), max(xs), max(ys)


def draw(src, side, bb, parts, out):
    im = Image.open(src).convert("RGB")
    L, T, R, B = outline_px(im)
    sx, sy = (R - L) / (bb[2] - bb[0]), (B - T) / (bb[3] - bb[1])
    font = ImageFont.truetype(FONT, max(14, int(sx * 0.42)))
    d = ImageDraw.Draw(im)
    for ref, layer, x, y in parts:
        if (layer == "B.Cu") != (side == "bottom"):
            continue
        u = (R - (x - bb[0]) * sx) if side == "bottom" else (L + (x - bb[0]) * sx)
        v = T + (y - bb[1]) * sy
        d.text((u, v), ref, font=font, anchor="mm", fill=(255, 235, 60),
               stroke_width=3, stroke_fill=(0, 0, 0))
    im.save(out)
    print(f"wrote {out}")


def main():
    bb, parts = board()
    draw(sys.argv[1], "top", bb, parts, IMG / "ref_map_top.png")
    draw(sys.argv[2], "bottom", bb, parts, IMG / "ref_map_bottom.png")


if __name__ == "__main__":
    main()
