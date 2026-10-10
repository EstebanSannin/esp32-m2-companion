"""Hand-finish helper: prune dead branches (e.g. escape stub + via that the
net's route never used) by real copper overlap, NOT by KiCad's
track_dangling flag: KiCad flags many correct route ends that stop on a
pad's rounded corner, and pruning on that flag unravels complete nets
(GATE V3, twice).

Graph per net: nodes = tracks/vias (+ pads as fixed anchors), edge = shapes
overlap on a shared copper layer. A track/via with <= 1 neighbour is a
leaf of a dead branch and is removed; repeat until stable. A real route
end always touches its pad + the previous segment (2 neighbours), so it is
never removed. The USB nets are never touched.
  $KPY tools/v2_prune_branches.py [--dry] [--nets N1,N2]
"""
import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "tools"))
PCB = HERE / "kicad" / "esp32_m2_companion.kicad_pcb"
PROTECTED = {"USBH3_D_P", "USBH3_D_N", "USB_D_P_ESD", "USB_D_N_ESD", "USB_D_P", "USB_D_N"}
PLANES = {"GND", "+3V3"}   # zones anchor everything there; use drop_orphan_fanout
DRY = "--dry" in sys.argv
ONLY = set(sys.argv[sys.argv.index("--nets") + 1].split(",")) if "--nets" in sys.argv else None


def main():
    b = pcbnew.LoadBoard(str(PCB))
    cu = list(b.GetEnabledLayers().CuStack())
    by_net = {}
    for t in b.GetTracks():
        n = t.GetNetname()
        if n in PROTECTED or n in PLANES or (ONLY and n not in ONLY):
            continue
        by_net.setdefault(n, {"items": [], "pads": []})["items"].append(t)
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if p.GetNetname() in by_net:
                by_net[p.GetNetname()]["pads"].append(p)

    def layers(o):
        return [l for l in cu if o.IsOnLayer(l)]

    def touch(a, b_):
        for l in layers(a):
            if b_.IsOnLayer(l) and a.GetEffectiveShape(l).Collide(b_.GetEffectiveShape(l), 0):
                return True
        return False

    doomed = []
    for n, g in by_net.items():
        items, pads = g["items"], g["pads"]
        nb = {i: set() for i in range(len(items))}
        padn = {i: 0 for i in range(len(items))}
        for i, a in enumerate(items):
            for j in range(i + 1, len(items)):
                if touch(a, items[j]):
                    nb[i].add(j); nb[j].add(i)
            padn[i] = sum(1 for p in pads if touch(a, p))
        alive = set(nb)
        while True:
            leaves = [i for i in alive if len(nb[i] & alive) + padn[i] <= 1]
            if not leaves:
                break
            alive -= set(leaves)
        dead = [items[i] for i in nb if i not in alive]
        if dead:
            print(f"  {n:16s} -{len(dead)}")
        doomed += dead
    print(f"{'would remove' if DRY else 'removed'} {len(doomed)} dead-branch items")
    if not DRY:
        for t in doomed:
            b.Remove(t)
        pcbnew.SaveBoard(str(PCB), b)


if __name__ == "__main__":
    from kicad_exit import run
    run(main)
