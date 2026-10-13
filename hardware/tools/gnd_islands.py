"""Report copper islands of a net (default GND): union-find over zone fill
fragments, tracks, vias and pads by geometric overlap per layer.

Run with KiCad's python: .../python3 tools/gnd_islands.py [NET]
Prints every connected group except the largest, with its members.
"""

import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent.parent
NET = sys.argv[1] if len(sys.argv) > 1 else "GND"
b = pcbnew.LoadBoard(str(HERE / "kicad" / "esp32_m2_companion.kicad_pcb"))
CU = [l for l in b.GetEnabledLayers().CuStack()]

nodes = []   # (label, {layer: SHAPE})


def add(label, item, layers):
    shapes = {l: item.GetEffectiveShape(l) for l in layers}
    nodes.append((label, shapes, None))


for fp in b.GetFootprints():
    for p in fp.Pads():
        if p.GetNetname() == NET:
            add(f"{fp.GetReference()}.{p.GetNumber()}", p,
                [l for l in CU if p.IsOnLayer(l)])
for t in b.GetTracks():
    if t.GetNetname() != NET:
        continue
    if t.GetClass() == "PCB_VIA":
        p = t.GetPosition()
        add(f"via({p.x/1e6:.2f},{p.y/1e6:.2f})", t, CU)
    else:
        s = t.GetStart()
        add(f"trk[{b.GetLayerName(t.GetLayer())}]({s.x/1e6:.2f},{s.y/1e6:.2f})",
            t, [t.GetLayer()])
for z in b.Zones():
    if z.GetIsRuleArea() or z.GetNetname() != NET:
        continue
    for l in z.GetLayerSet().Seq():
        fps = z.GetFilledPolysList(l)
        for i in range(fps.OutlineCount()):
            poly = pcbnew.SHAPE_POLY_SET()
            poly.AddOutline(fps.Outline(i))
            for h in range(fps.HoleCount(i)):
                poly.AddHole(fps.Hole(i, h))
            c = fps.Outline(i).BBox().Centre()
            nodes.append((f"zone {z.GetZoneName()}[{b.GetLayerName(l)}]"
                          f"({c.x/1e6:.2f},{c.y/1e6:.2f}) "
                          f"{fps.Outline(i).Area()/1e12:.1f}mm2",
                          {}, (l, poly)))

parent = list(range(len(nodes)))


def find(i):
    while parent[i] != i:
        parent[i] = parent[parent[i]]
        i = parent[i]
    return i


def touch(a, b_):
    _, sa, za = a
    _, sb, zb = b_
    if za and zb:
        return False
    if za or zb:
        (l, poly), shapes = (za, sb) if za else (zb, sa)
        return l in shapes and poly.Collide(shapes[l], 0)
    return any(l in sb and sa[l].Collide(sb[l], 0) for l in sa)


for i in range(len(nodes)):
    for j in range(i + 1, len(nodes)):
        if find(i) != find(j) and touch(nodes[i], nodes[j]):
            parent[find(i)] = find(j)

groups = {}
for i, n in enumerate(nodes):
    groups.setdefault(find(i), []).append(n[0])
gs = sorted(groups.values(), key=len, reverse=True)
print(f"{NET}: {len(gs)} connected group(s); main group {len(gs[0])} items")
for g in gs[1:]:
    print("  ISLAND:", "; ".join(g))

from kicad_exit import hard_exit  # noqa: E402
hard_exit(0)
