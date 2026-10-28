"""v2 GATE V3: board branding (owner request 2026-10-10).

Top (F.Silkscreen): the board name, split around the mounting notch - the
module covers the rest of the top, the only free silk is the strip between
the top edge (y 108.0) and the module silk line (y 112.3), cut by the notch
(x 98.25-101.75): "ESP32-M2" left, "COMPANION" right, same height, the
largest of 1.0 / 0.9 / 0.8 mm that fits both halves (0.3 mm edge margin).
Silk in the antenna keep-out is fine (the Espressif rule is about copper).

Back (B.Silkscreen): logo (owner-placed), then a column version / "Designed
in Italy" / samnium.tech at 0.8 mm (DRC min_text_height); the board name
moves to the top.

Back, below the website (owner request 2026-10-28): the JLC serial-number
field - a SOLID 2 x 10 mm B.Silkscreen rectangle, JLC "Mark on PCB ->
2D Barcode (Serial Number) -> Number only -> Specify Position" (jlcpcb.com
help "How to mark on PCB": the number is printed inside it, one row,
prefix + incrementing number). Aligned with the text column, clear of
vias / parts (first via at y 118.6). Idempotent.
  $KPY tools/v2_brand.py
"""
import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "tools"))
PCB = HERE / "kicad" / "esp32_m2_companion.kicad_pcb"
NAME = "ESP32-M2-COMPANION"
LEFT, RIGHT = "ESP32-M2", "COMPANION"
STRIP_Y = (108.3, 112.1)                      # usable band (edge / module silk)
LEFT_X, RIGHT_X = (89.3, 97.95), (102.05, 110.7)
BACK = [("v2.0 Rev A 2026-10", 111.0), ("Designed in Italy", 112.5), ("samnium.tech", 114.0)]
BACK_X, H_BACK, TH = 89.5, 0.8, 0.15
SERIAL = (89.5, 115.4, 99.5, 117.4)           # x0, y0, x1, y1: 10 x 2 mm


def main():
    b = pcbnew.LoadBoard(str(PCB))
    T, mm = pcbnew.ToMM, pcbnew.FromMM
    V = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))
    texts = {t.GetText(): t for t in b.GetDrawings() if isinstance(t, pcbnew.PCB_TEXT)}
    log = []

    def new_text(s, layer, h):
        t = pcbnew.PCB_TEXT(b)
        t.SetText(s); t.SetLayer(layer)
        t.SetTextSize(V(h, h)); t.SetTextThickness(mm(TH))
        if layer == pcbnew.B_SilkS:
            t.SetMirrored(True)
        b.Add(t)
        return t

    # ---- top: name split around the notch ----------------------------------
    # (removals only right before SaveBoard - SWIG Remove() rule)
    tl = texts.get(LEFT) or new_text(LEFT, pcbnew.F_SilkS, 1.0)       # idempotent
    tr = texts.get(RIGHT) or new_text(RIGHT, pcbnew.F_SilkS, 1.0)
    cy = (STRIP_Y[0] + STRIP_Y[1]) / 2
    for h in (1.0, 0.9, 0.8):
        for t in (tl, tr):
            t.SetTextSize(V(h, h)); t.SetTextThickness(mm(TH))
        tl.SetPosition(V(sum(LEFT_X) / 2, cy)); tr.SetPosition(V(sum(RIGHT_X) / 2, cy))
        ok = True
        for t, (x0, x1) in ((tl, LEFT_X), (tr, RIGHT_X)):
            bb = t.GetBoundingBox()
            ok &= x0 <= T(bb.GetLeft()) and T(bb.GetRight()) <= x1 and \
                STRIP_Y[0] <= T(bb.GetTop()) and T(bb.GetBottom()) <= STRIP_Y[1]
        if ok:
            log.append(f"top: '{LEFT}' / '{RIGHT}' at {h} mm")
            break
    else:
        raise SystemExit("board name does not fit the top strip even at 0.8 mm")

    # ---- back: logo + version / Designed in Italy / website ----------------
    doomed = [texts[NAME]] if NAME in texts else []
    ref = texts.get(BACK[0][0])
    for s, y in BACK:
        t = texts.get(s) or new_text(s, pcbnew.B_SilkS, H_BACK)
        t.SetTextSize(V(H_BACK, H_BACK)); t.SetTextThickness(mm(TH))
        if ref is not None:                   # same justification as the owner's column
            t.SetHorizJustify(ref.GetHorizJustify()); t.SetMirrored(ref.IsMirrored())
        t.SetPosition(V(BACK_X, y))
        log.append(f"back: '{s}' at {H_BACK} mm, y {y}")
    # ---- back: JLC serial-number field -------------------------------------
    x0, y0, x1, y1 = SERIAL
    have = [d for d in b.GetDrawings() if isinstance(d, pcbnew.PCB_SHAPE)
            and d.GetLayer() == pcbnew.B_SilkS and d.GetShape() == pcbnew.SHAPE_T_RECT
            and abs(T(d.GetStart().x) - x0) < 0.01 and abs(T(d.GetStart().y) - y0) < 0.01]
    if not have:
        r = pcbnew.PCB_SHAPE(b, pcbnew.SHAPE_T_RECT)
        r.SetLayer(pcbnew.B_SilkS)
        r.SetStart(V(x0, y0)); r.SetEnd(V(x1, y1))
        r.SetWidth(0); r.SetFilled(True)
        b.Add(r)
        log.append(f"back: JLC serial field {x1 - x0:.0f} x {y1 - y0:.0f} mm at ({x0}, {y0})")
    for t in doomed:
        b.Remove(t)
        log.append(f"back: '{NAME}' removed (now on top)")
    pcbnew.SaveBoard(str(PCB), b)
    print("\n".join(log))


if __name__ == "__main__":
    from kicad_exit import run
    run(main)
