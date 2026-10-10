"""Hand-finish helper: tie 'dangling' vias that are in fact connected.

A grid route that changes layer through an existing via (escape via) often
passes OVER the via centre's cell without ending exactly on the centre:
the copper overlaps (electrically connected), but KiCad only counts track
ENDPOINTS, so it reports via_dangling. For every via in the DRC list, add a
short own-net segment from the via centre to the nearest point of each
own-net track that overlaps the via (on that track's layer). Vias with no
overlapping own-net track are left alone (real dead ends: prune them).
  $KPY tools/v2_tie_vias.py DRC.json
  $KPY tools/v2_tie_vias.py DRC.json --drop-single-layer
--drop-single-layer: KiCad also flags a via whose connections are all on ONE
layer (an escape via the route never used to change layer). Remove those:
the tracks still meet at the via centre (tie segments end there).
"""
import json
import math
import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "tools"))
PCB = HERE / "kicad" / "esp32_m2_companion.kicad_pcb"


def main():
    drc = json.load(open(sys.argv[1]))
    pts = [(it["pos"]["x"], it["pos"]["y"]) for v in drc["violations"]
           if v["type"] == "via_dangling" for it in v["items"]]
    b = pcbnew.LoadBoard(str(PCB))
    T, mm = pcbnew.ToMM, pcbnew.FromMM
    tracks = [t for t in b.GetTracks() if t.Type() != pcbnew.PCB_VIA_T]
    vias = [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T]
    added, untied = 0, []
    if "--drop-single-layer" in sys.argv:
        gone = []
        for x, y in pts:
            v = next((v for v in vias if abs(T(v.GetX()) - x) < 0.01 and abs(T(v.GetY()) - y) < 0.01), None)
            if v is None or v.IsLocked():
                continue
            lays = {t.GetLayer() for t in tracks if t.GetNetCode() == v.GetNetCode() and any(
                math.hypot(T(p.x) - x, T(p.y) - y) < 0.005 for p in (t.GetStart(), t.GetEnd()))}
            if len(lays) <= 1:
                gone.append(v)
        for v in gone:
            b.Remove(v)
        pcbnew.SaveBoard(str(PCB), b)
        print(f"removed {len(gone)} single-layer vias; kept {len(pts) - len(gone)}")
        return
    for x, y in pts:
        v = next((v for v in vias if abs(T(v.GetX()) - x) < 0.01 and abs(T(v.GetY()) - y) < 0.01), None)
        if v is None:
            continue
        r = T(v.GetWidth(pcbnew.F_Cu)) / 2
        tied = False
        for t in tracks:
            if t.GetNetCode() != v.GetNetCode():
                continue
            ax, ay = T(t.GetStart().x), T(t.GetStart().y)
            bx, by = T(t.GetEnd().x), T(t.GetEnd().y)
            if math.hypot(ax - x, ay - y) < 0.005 or math.hypot(bx - x, by - y) < 0.005:
                continue                              # already ends on the via
            dx, dy = bx - ax, by - ay
            L = dx * dx + dy * dy
            u = 0 if L == 0 else max(0, min(1, ((x - ax) * dx + (y - ay) * dy) / L))
            px, py = ax + u * dx, ay + u * dy
            if math.hypot(px - x, py - y) > r + T(t.GetWidth()) / 2:
                continue                              # no copper overlap
            if math.hypot(px - x, py - y) < 0.005:
                # the track runs straight through the centre: tie along it to its
                # nearer endpoint (collinear same-net overlap, no zero-length stub)
                px, py = (ax, ay) if math.hypot(ax - x, ay - y) < math.hypot(bx - x, by - y) else (bx, by)
            s = pcbnew.PCB_TRACK(b)
            s.SetStart(pcbnew.VECTOR2I(mm(x), mm(y)))
            s.SetEnd(pcbnew.VECTOR2I(mm(px), mm(py)))
            s.SetWidth(t.GetWidth()); s.SetLayer(t.GetLayer()); s.SetNet(v.GetNet())
            b.Add(s)
            added += 1
            tied = True
        if not tied:
            untied.append((v.GetNetname(), x, y))
    pcbnew.SaveBoard(str(PCB), b)
    print(f"tie segments added: {added}; vias with no overlapping own track: {untied}")


if __name__ == "__main__":
    from kicad_exit import run
    run(main)
