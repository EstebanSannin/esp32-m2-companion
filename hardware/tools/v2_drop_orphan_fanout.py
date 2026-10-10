"""Hand-finish helper: remove orphaned plane fan-out - GND/+3V3 vias and
stubs that no longer lead to any pad (left behind when a part moved or
changed footprint). Fan-out = pad -> stub -> via; an item is anchored if it
touches a plane-net pad or an anchored item of the same net. Plane zones
are ignored (they would anchor everything). Separate process.
  $KPY tools/v2_drop_orphan_fanout.py
"""
import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "tools"))
PCB = HERE / "kicad" / "esp32_m2_companion.kicad_pcb"
PLANES = {"GND", "+3V3"}
T = pcbnew.ToMM


def main():
    b = pcbnew.LoadBoard(str(PCB))
    pads = {}
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if p.GetNetname() in PLANES:
                bb = p.GetBoundingBox()
                pads.setdefault(p.GetNetname(), []).append(
                    (T(bb.GetLeft()), T(bb.GetTop()), T(bb.GetRight()), T(bb.GetBottom())))
    items = [t for t in b.GetTracks() if t.GetNetname() in PLANES]

    def ends(t):
        if t.Type() == pcbnew.PCB_VIA_T:
            return [(T(t.GetX()), T(t.GetY()))]
        return [(T(t.GetStart().x), T(t.GetStart().y)), (T(t.GetEnd().x), T(t.GetEnd().y))]

    def in_pad(net, x, y):
        return any(l - 0.01 <= x <= r + 0.01 and tp - 0.01 <= y <= bt + 0.01
                   for l, tp, r, bt in pads.get(net, []))
    anchored = set()
    changed = True
    while changed:
        changed = False
        pts = {(t.GetNetname(), round(x, 3), round(y, 3))
               for t in items if id(t) in anchored for x, y in ends(t)}
        for t in items:
            if id(t) in anchored:
                continue
            n = t.GetNetname()
            if any(in_pad(n, x, y) or (n, round(x, 3), round(y, 3)) in pts for x, y in ends(t)):
                anchored.add(id(t))
                changed = True
    gone = 0
    for t in items:
        if id(t) not in anchored:
            b.Remove(t)
            gone += 1
    pcbnew.SaveBoard(str(PCB), b)
    print(f"removed {gone} orphaned plane vias/stubs (kept {len(anchored)})")


if __name__ == "__main__":
    from kicad_exit import run
    run(main)
