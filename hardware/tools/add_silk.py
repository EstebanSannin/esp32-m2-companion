"""Apply the bottom-side silkscreen label (logo + text) to the routed board.

Additive and idempotent: everything goes into a PCB_GROUP named "silk_label";
re-running removes the old group first, so it never duplicates and NEVER touches
copper, tracks, zones, or footprints. Safe on the routed master.

Run (KiCad's bundled python, which has pcbnew):
  <KiCad>/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 \
      hardware/tools/add_silk.py
"""
import json
from pathlib import Path
import pcbnew

HERE = Path(__file__).resolve().parent.parent
PCB = HERE / "kicad" / "esp32_m2_companion.kicad_pcb"
RECTS = HERE / "branding" / "logo_silk_rects.json"
GROUP = "silk_label"

# --- placement (absolute board mm; card top edge y=108, C6/C7 silk from ~118) ---
LOGO_CX, LOGO_CY = 93.0, 114.2       # logo center; x mirrored for bottom silk
TEXT_X = 96.0                        # text left edge (via right-justify + mirror)
TEXT = [("ESP32-M2-COMPANION", 112.6), ("v1.0  Stefano Viola", 114.6), ("2026-08", 116.6)]
TEXT_H = 0.8
TEXT_TH = 0.15


def mm(v):
    return int(v * 1e6)


def clear_group(board):
    for g in list(board.Groups()):
        if g.GetName() == GROUP:
            for it in list(g.GetItems()):
                board.Remove(it)
            board.Remove(g)


def main():
    board = pcbnew.LoadBoard(str(PCB))
    clear_group(board)
    grp = pcbnew.PCB_GROUP(board)
    grp.SetName(GROUP)
    board.Add(grp)

    data = json.load(open(RECTS))
    wm, hm = data["w_mm"], data["h_mm"]
    for x0, y0, x1, y1 in data["rects"]:
        ps = pcbnew.SHAPE_POLY_SET()
        ch = pcbnew.SHAPE_LINE_CHAIN()
        for cx, cy in [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]:
            X = LOGO_CX - (cx - wm / 2)      # mirror x (bottom silk)
            Y = LOGO_CY + (cy - hm / 2)
            ch.Append(pcbnew.VECTOR2I(mm(X), mm(Y)))
        ch.SetClosed(True)
        ps.AddOutline(ch)
        sh = pcbnew.PCB_SHAPE(board)
        sh.SetShape(pcbnew.SHAPE_T_POLY)
        sh.SetPolyShape(ps)
        sh.SetLayer(pcbnew.B_SilkS)
        sh.SetFilled(True)
        sh.SetWidth(0)
        board.Add(sh)
        grp.AddItem(sh)

    for s, y in TEXT:
        t = pcbnew.PCB_TEXT(board)
        t.SetText(s)
        t.SetLayer(pcbnew.B_SilkS)
        t.SetPosition(pcbnew.VECTOR2I(mm(TEXT_X), mm(y)))
        t.SetTextSize(pcbnew.VECTOR2I(mm(TEXT_H), mm(TEXT_H)))
        t.SetTextThickness(mm(TEXT_TH))
        t.SetMirrored(True)
        t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_RIGHT)  # -> left-aligned from below
        board.Add(t)
        grp.AddItem(t)

    board.Save(str(PCB))
    print(f"silk_label applied: {len(data['rects'])} logo rects + {len(TEXT)} text lines")


if __name__ == "__main__":
    main()
