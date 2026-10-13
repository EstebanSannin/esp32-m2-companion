"""ONE-SHOT rev-B board edit (applied 2026-10-06; asserts v1 geometry, so
it refuses to run twice). Mirrors tools/route.py Leg 1 + preroute_fixups.
Usage: kicad-python tools/apply_rev_b_corner.py kicad/esp32_m2_companion.kicad_pcb"""
import sys
import pcbnew
mm = pcbnew.FromMM
P = sys.argv[1]
b = pcbnew.LoadBoard(P)
V = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))
near = lambda p, x, y: abs(p.x/1e6-x) < 0.005 and abs(p.y/1e6-y) < 0.005

kill = []
for t in b.GetTracks():
    n = t.GetNetname()
    if t.GetClass() == "PCB_VIA":
        if (n == "USBH3_D_N" and near(t.GetPosition(), 105.55, 146.8)) or \
           (n == "USBH3_D_P" and near(t.GetPosition(), 107.75, 147.0)):
            kill.append(t)
        continue
    s, e = t.GetStart(), t.GetEnd()
    segs = {
        "USBH3_D_N": [((107.25,147.3),(105.55,146.8)), ((107.25,148.75),(107.25,147.3)),
                      ((105.55,146.8),(105.55,142.35))],
        "USBH3_D_P": [((107.75,148.75),(107.75,147.0)), ((107.75,147.0),(106.95,144.85)),
                      ((106.95,144.85),(106.562,144.85))],
        "GND": [((106.75,147.5),(106.75,147.45)), ((106.75,147.45),(105.0,147.45))],
    }.get(n, [])
    if any((near(s,*a) and near(e,*c)) or (near(s,*c) and near(e,*a)) for a, c in segs):
        kill.append(t)
assert len(kill) == 10, len(kill)
for t in kill: b.Remove(t)

# give J1.8 + D2.2 the W_DISABLE1_n net; drop their netless-pad helper keepouts
net = pcbnew.NETINFO_ITEM(b, "W_DISABLE1_n"); b.Add(net)
targets = []
for ref, num in (("J1", "8"), ("D2", "2")):
    p = [q for q in b.FindFootprintByReference(ref).Pads() if q.GetNumber() == num][0]
    p.SetNet(net); targets.append(p)
for z in list(b.Zones()):
    if z.GetIsRuleArea() and z.GetDoNotAllowVias() and not z.GetDoNotAllowTracks():
        if any(z.Outline().Contains(p.GetPosition()) for p in targets):
            b.Remove(z); print("removed helper keepout over", z.GetBoundingBox().Centre())

def trk(n, layer, pts, w):
    for a, c in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b); t.SetStart(V(*a)); t.SetEnd(V(*c)); t.SetWidth(mm(w))
        t.SetLayer(layer); t.SetNet(b.FindNet(n)); t.SetLocked(True); b.Add(t)
def via(n, x, y, d):
    v = pcbnew.PCB_VIA(b); v.SetPosition(V(x, y)); v.SetDrill(mm(0.3)); v.SetWidth(mm(d))
    v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetNet(b.FindNet(n)); v.SetLocked(True); b.Add(v)
F, B = pcbnew.F_Cu, pcbnew.B_Cu
trk("USBH3_D_N", F, [(107.25,148.75),(107.25,147.5),(107.10,146.95)], 0.14)
via("USBH3_D_N", 107.10, 146.95, 0.45)
trk("USBH3_D_N", B, [(107.10,146.95),(106.6,146.45),(105.55,145.4),(105.55,142.35)], 0.14)
trk("USBH3_D_P", F, [(107.75,148.75),(107.75,147.5),(108.10,146.95)], 0.14)
via("USBH3_D_P", 108.10, 146.95, 0.45)
trk("USBH3_D_P", B, [(108.10,146.95),(108.10,145.5),(107.45,144.85),(106.562,144.85)], 0.14)
trk("W_DISABLE1_n", B, [(107.5,148.75),(107.5,147.5),(107.6,147.3),(107.6,146.45)], 0.15)
via("W_DISABLE1_n", 107.60, 146.45, 0.45)
trk("GND", F, [(106.75,147.5),(106.62,147.3),(106.62,146.1),(105.3,146.1),(104.99,145.3),(104.99,144.964)], 0.15)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(P, b)

# --- pin 8 long haul to D2.2 (found by the one-net feasibility probe):
# In1 NW from the escape via, west along y 144.45, via at (100.8,143.1),
# B.Cu through the D1.3 / D2 pad-column gap (beside IO14) into D2.2.
I1 = pcbnew.In1_Cu
trk("W_DISABLE1_n", I1, [(107.6,146.45),(107.2,146.45),(105.2,144.45),(102.15,144.45),(100.8,143.1)], 0.15)
via("W_DISABLE1_n", 100.8, 143.1, 0.45)
# exact corridor from the probe: threads between EN via (98.1,141.6), IO14
# via (99.345,140.92), D1.3's rounded corner and D2's pad column
trk("W_DISABLE1_n", B, [(100.8,143.1),(98.9,141.2),(98.9,141.15),(98.85,141.1),
    (98.85,141.05),(98.8,141.0),(98.8,140.75),(99.15,140.4),(99.2,140.4),
    (99.55,140.05),(99.55,140.0),(99.6,139.95),(99.6,139.55),(100.1,139.05),
    (100.6625,138.75)], 0.15)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(P, b)

from kicad_exit import hard_exit  # noqa: E402
hard_exit(0)
