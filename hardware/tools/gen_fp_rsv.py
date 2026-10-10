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
    L.append(f'\t(model "${{KIPRJMOD}}/3dmodels/{WRL.name}"\n\t\t(offset (xyz 0 0 0))'
             '\n\t\t(scale (xyz 1 1 1))\n\t\t(rotate (xyz 0 0 0)))')
    L.append(')')
    OUT.write_text("\n".join(L) + "\n")
    print("wrote", OUT)
    write_wrl()


# ---- 3D model (visual only): no stock KiCad model for RSV 1.8x2.6. Simple
# VRML: dark body 1.8 x 2.6 x 0.55 mm (TI RSV0016A max height), the 16
# terminals as tin blocks at the body edge, a pin-1 dot. VRML unit = 0.1 in;
# model y is up (footprint y is down).
WRL = OUT.parent.parent / "3dmodels" / "TI_RSV0016A_UQFN-16_1.8x2.6mm_P0.4mm.wrl"


def write_wrl():
    u = 1 / 2.54

    def box(x, y, z, sx, sy, sz, rgb):
        return (f"Transform {{ translation {x*u:.4f} {-y*u:.4f} {z*u:.4f} children Shape {{ "
                f"appearance Appearance {{ material Material {{ diffuseColor {rgb} }} }} "
                f"geometry Box {{ size {sx*u:.4f} {sy*u:.4f} {sz*u:.4f} }} }} }}")
    body, tin, dot = "0.15 0.15 0.15", "0.75 0.75 0.72", "0.9 0.9 0.9"
    out = ["#VRML V2.0 utf8", box(0, 0, 0.3, 1.8, 2.6, 0.5, body)]
    for num, x, y, w, h in PADS:
        if abs(x) > 0.5 and h < w:                   # left / right terminals
            out.append(box(0.8 if x > 0 else -0.8, y, 0.04, 0.25, 0.2, 0.08, tin))
        else:                                        # top / bottom terminals
            out.append(box(x, 1.2 if y > 0 else -1.2, 0.04, 0.2, 0.25, 0.08, tin))
    out.append(box(-0.5, -0.9, 0.555, 0.2, 0.2, 0.01, dot))
    WRL.write_text("\n".join(out) + "\n")
    print("wrote", WRL)


if __name__ == "__main__":
    main()
