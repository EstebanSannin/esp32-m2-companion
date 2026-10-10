"""Hand-finish helper: after hand-routing a PROTECTED net group, clear what
collides with it. Reads a KiCad DRC JSON, finds every violation pairing a
protected item with another track/via:
  - signal nets: ripped entirely (re-routed afterwards)
  - plane nets (GND/+3V3): only the colliding via/track segments removed
    (their pads get re-fanned-out by `v2_route.py --fanout-missing`)
Separate process (never keep using a board after Remove()).

  $KPY tools/v2_clear_conflicts.py DRC.json NET1,NET2,...   (protected nets)
"""
import json
import re
import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "tools"))
PCB = HERE / "kicad" / "esp32_m2_companion.kicad_pcb"
PLANES = {"GND", "+3V3"}


def main():
    drc = json.load(open(sys.argv[1]))
    prot = set(sys.argv[2].split(","))
    rip_nets, plane_hits = set(), []
    for v in drc["violations"]:
        if v["type"] not in ("shorting_items", "clearance", "tracks_crossing",
                             "hole_clearance", "hole_to_hole"):
            continue
        items = v["items"]
        nets = [re.search(r"\[([^\]]+)\]", i["description"]) for i in items]
        nets = [m.group(1) if m else None for m in nets]
        if not any(n in prot for n in nets):
            continue
        for it, n in zip(items, nets):
            d = it["description"]
            if n in prot or n is None or "Zone" in d or d.startswith("Pad"):
                continue
            if n in PLANES:
                plane_hits.append((n, it["pos"]["x"], it["pos"]["y"]))
            else:
                rip_nets.add(n)
    b = pcbnew.LoadBoard(str(PCB))
    gone_sig = gone_plane = 0
    for t in list(b.GetTracks()):
        n = t.GetNetname()
        if n in rip_nets:
            b.Remove(t)
            gone_sig += 1
            continue
        if n in PLANES:
            # DRC item positions are mm; match vias/segments near them
            for pn, x, y in plane_hits:
                if pn != n:
                    continue
                pos = pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))
                if t.HitTest(pos, pcbnew.FromMM(0.05)):
                    b.Remove(t)
                    gone_plane += 1
                    break
    pcbnew.SaveBoard(str(PCB), b)
    print(f"ripped nets ({len(rip_nets)}): {','.join(sorted(rip_nets))}")
    print(f"removed {gone_sig} signal items, {gone_plane} plane vias/segments")


if __name__ == "__main__":
    from kicad_exit import run
    run(main)
