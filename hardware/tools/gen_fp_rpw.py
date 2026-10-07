"""Generate the TI RPW0010A (VQFN-HR 2x2, 10 pins) footprint for U6
TPS259470A. Source: docs/datasheets/tps25947.pdf, drawing 4225183/A:
p.73 "Example board layout" (copper/mask, NSMD 0.05 mm) and p.74
"Example stencil design" (paste: IN/OUT split in 2 x 0.28 x 1.06 mm,
L-pad paste 0.275 bar / 0.225 leg). Dimensions read from the rendered
drawing and cross-checked against every labelled dimension (GATE V3).

Coordinates: package centre (0,0), x right, y down, top view, pin 1 top-left.
L-shaped pins (1, 4, 7, 10) = two overlapping rect pads with the same
number (bar + leg). Run: uv run python tools/gen_fp_rpw.py
"""
from pathlib import Path

OUT = (Path(__file__).resolve().parent.parent / "kicad" / "footprints.pretty"
       / "TI_RPW_VQFN-10_2x2mm_P0.5mm.kicad_mod")
MASK = 0.05

# (number, x0, y0, x1, y1, paste) ; paste: "same" | "none" | "shrink"
PADS = []
# side pads 2, 3 (left), 9, 8 (right): 0.6 x 0.25 at y = -/+0.225
for num, x0, x1, yc in ((2, -1.2, -0.6, -0.225), (3, -1.2, -0.6, 0.225),
                        (9, 0.6, 1.2, -0.225), (8, 0.6, 1.2, 0.225)):
    PADS.append((num, x0, yc - 0.125, x1, yc + 0.125, "same"))
# L pads: bar 0.6 x 0.3 at y = +-0.70, leg 0.25 wide from bar to +-1.2
for num, sx, sy in ((1, -1, -1), (4, -1, 1), (7, 1, 1), (10, 1, -1)):
    bx0, bx1 = sorted((sx * 0.6, sx * 1.2))
    by0, by1 = sorted((sy * 0.55, sy * 0.85))
    lx0, lx1 = sorted((sx * 0.6, sx * 0.85))
    ly0, ly1 = sorted((sy * 0.85, sy * 1.2))
    PADS.append((num, bx0, by0, bx1, by1, "shrink"))
    PADS.append((num, lx0, ly0, lx1, ly1, "shrink"))
# IN (5) / OUT (6): 0.3 x 2.4 bars at x = -/+0.25, paste split separately
PADS.append((5, -0.4, -1.2, -0.1, 1.2, "none"))
PADS.append((6, 0.1, -1.2, 0.4, 1.2, "none"))
# paste-only apertures for 5/6: 0.28 x 1.06 centred at y = +-0.63
APERTURES = [(xc, yc) for xc in (-0.25, 0.25) for yc in (-0.63, 0.63)]


def pad(num, x0, y0, x1, y1, paste):
    cx, cy, w, h = (x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, y1 - y0
    layers = '"F.Cu" "F.Mask"' + (' "F.Paste"' if paste != "none" else "")
    extra = ""
    if paste == "shrink":
        extra = "\n\t\t(solder_paste_margin -0.0125)"
    return (f'\t(pad "{num}" smd roundrect (at {cx:.4f} {cy:.4f}) '
            f'(size {w:.4f} {h:.4f}) (layers {layers}) '
            f'(roundrect_rratio {min(0.05 / min(w, h), 0.25):.4f})'
            f'\n\t\t(solder_mask_margin {MASK}){extra})')


def main():
    lines = ['(footprint "TI_RPW_VQFN-10_2x2mm_P0.5mm"',
             '\t(version 20241229)', '\t(generator "gen_fp_rpw")',
             '\t(layer "F.Cu")',
             '\t(descr "TI RPW0010A VQFN-HR 2x2 mm 10 pins (TPS25947xx); '
             'land pattern + stencil per drawing 4225183/A (tps25947.pdf p.73-74)")',
             '\t(tags "VQFN-HR RPW0010A TPS25947 eFuse")',
             '\t(attr smd)',
             '\t(property "Reference" "REF**" (at 0 -2.1 0) (layer "F.SilkS") '
             '(effects (font (size 0.6 0.6) (thickness 0.1))))',
             '\t(property "Value" "TI_RPW_VQFN-10_2x2mm_P0.5mm" (at 0 2.1 0) '
             '(layer "F.Fab") (effects (font (size 0.4 0.4) (thickness 0.06))))']
    # fab body 2.0 x 2.0, pin-1 chamfer
    lines.append('\t(fp_poly (pts (xy -0.75 -1) (xy 1 -1) (xy 1 1) (xy -1 1) '
                 '(xy -1 -0.75)) (stroke (width 0.1) (type solid)) '
                 '(fill none) (layer "F.Fab"))')
    # courtyard: pads reach +-1.2 (+0.05 mask) -> +-1.45
    lines.append('\t(fp_rect (start -1.45 -1.45) (end 1.45 1.45) '
                 '(stroke (width 0.05) (type solid)) (fill none) (layer "F.CrtYd"))')
    # silk: pin-1 dot outside the copper, top-left
    lines.append('\t(fp_circle (center -1.35 -1.35) (end -1.27 -1.35) '
                 '(stroke (width 0.12) (type solid)) (fill solid) (layer "F.SilkS"))')
    for p in PADS:
        lines.append(pad(*p))
    for xc, yc in APERTURES:
        lines.append(f'\t(pad "" smd roundrect (at {xc} {yc}) (size 0.28 1.06) '
                     f'(layers "F.Paste") (roundrect_rratio 0.1786))')
    lines.append(')')
    OUT.write_text("\n".join(lines) + "\n")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
