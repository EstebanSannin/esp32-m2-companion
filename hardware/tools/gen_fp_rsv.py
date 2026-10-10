"""Generate the TI RSV0016A (UQFN-16, 1.8 x 2.6 mm, 0.4 mm pitch) footprint
for U3-U5 TMUX1511 from TI's land pattern (docs/datasheets/tmux1511.pdf
p.37 "Land pattern example", rendered + every labelled dimension checked):
side pads 0.6 x 0.2 centred at x = +-0.8 (pin 1: 0.7 long, extends
inward), top/bottom pads 0.2 x 0.6 centred at y = +-1.2, 0.4 mm pitch,
R0.05 corners, no exposed pad. KiCad's stock UQFN-16_1.8x2.6mm_P0.4mm pads
are 0.15 mm longer outward (GATE V2 parts check) - the TI land frees room
for escape vias. Top view, pin 1 top-left; x right, y down.
  uv run python tools/gen_fp_rsv.py
"""
from pathlib import Path

OUT = (Path(__file__).resolve().parent.parent / "kicad" / "footprints.pretty"
       / "TI_RSV0016A_UQFN-16_1.8x2.6mm_P0.4mm.kicad_mod")
MASK = 0.05
ys = [-0.6, -0.2, 0.2, 0.6]
xs = [-0.6, -0.2, 0.2, 0.6]
PADS = []
for k, y in enumerate(ys):              # left 1..4 (top -> bottom)
    if k == 0:
        PADS.append((1, -0.75, y, 0.7, 0.2))   # pin 1: x -1.1 .. -0.4
    else:
        PADS.append((k + 1, -0.8, y, 0.6, 0.2))
for k, x in enumerate(xs):              # bottom 5..8 (left -> right)
    PADS.append((5 + k, x, 1.2, 0.2, 0.6))
for k, y in enumerate(reversed(ys)):    # right 9..12 (bottom -> top)
    PADS.append((9 + k, 0.8, y, 0.6, 0.2))
for k, x in enumerate(reversed(xs)):    # top 13..16 (right -> left)
    PADS.append((13 + k, x, -1.2, 0.2, 0.6))


def main():
    L = ['(footprint "TI_RSV0016A_UQFN-16_1.8x2.6mm_P0.4mm"', '\t(version 20241229)',
         '\t(generator "gen_fp_rsv")', '\t(layer "F.Cu")',
         '\t(descr "TI RSV0016A UQFN-16 1.8x2.6 mm 0.4 mm pitch; TI land pattern '
         '(tmux1511.pdf p.37)")', '\t(tags "UQFN RSV0016A TMUX1511")', '\t(attr smd)',
         '\t(property "Reference" "REF**" (at 0 -2.2 0) (layer "F.SilkS") '
         '(effects (font (size 0.6 0.6) (thickness 0.1))))',
         '\t(property "Value" "TI_RSV0016A_UQFN-16" (at 0 2.2 0) (layer "F.Fab") '
         '(effects (font (size 0.4 0.4) (thickness 0.06))))',
         '\t(fp_poly (pts (xy -0.6 -1.3) (xy 0.9 -1.3) (xy 0.9 1.3) (xy -0.9 1.3) '
         '(xy -0.9 -1.0)) (stroke (width 0.1) (type solid)) (fill none) (layer "F.Fab"))',
         '\t(fp_rect (start -1.4 -1.8) (end 1.4 1.8) (stroke (width 0.05) (type solid)) '
         '(fill none) (layer "F.CrtYd"))',
         '\t(fp_circle (center -1.3 -1.65) (end -1.22 -1.65) (stroke (width 0.12) '
         '(type solid)) (fill solid) (layer "F.SilkS"))']
    for num, x, y, w, h in PADS:
        L.append(f'\t(pad "{num}" smd roundrect (at {x} {y}) (size {w} {h}) '
                 f'(layers "F.Cu" "F.Mask" "F.Paste") (roundrect_rratio 0.25)'
                 f'\n\t\t(solder_mask_margin {MASK}))')
    L.append(')')
    OUT.write_text("\n".join(L) + "\n")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
