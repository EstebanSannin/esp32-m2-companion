"""v2 edge-expansion routing feasibility probe (NOT a layout).

Takes a copy of the rev-B board (probe_base.kicad_pcb), keeps all rev-B
copper locked, drops placeholder footprints for the v2 edge-expansion block
into the free bottom-side area under the module, wires the new nets, and
lets freerouting try ONLY the new nets. Question answered: "does v2 Rev A
fit on 2242 with the rev-B placement untouched?"

Run with KiCad's bundled python, from repo root:
  $KPY v2/probe/probe.py [--layers 4|6] [--no-route]

Placeholders (footprints from KiCad stock libs; pinouts from the datasheets
in the parts research, see ../edge-expansion-brainstorm.md §11):
  SW1-SW3   TI TMUX1511 RSV UQFN-16 (1 SEL1, 2 S1, 3 D1, 4 SEL2, 5 S2, 6 D2,
            7 NC, 8 GND, 9 D3, 10 S3, 11 SEL3, 12 NC, 13 D4, 14 S4, 15 SEL4,
            16 VDD). SELx active-high, all tied to EXP_OE.
  Q1        dual low-Vth NMOS, SOT-363 (1 S1, 2 G1, 3 D2, 4 S2, 5 G2, 6 D1):
            wired-NOR carrier detect -> EXP_OE (part TBD)
  RN1-RN3   4x0402 convex arrays + R26 0402: series R, ESP side
  Q2        dual NMOS: open-drain LED_1# / WAKE_ON_WWAN# (R28/R29 gate pull-downs)
  Q3        dual NMOS: W_DISABLE2# input -> IO1 inverted (R30 pull-up, R22 1M edge pull-up)
  R20/R21 1M sense pull-ups, R23/R24 100k gate series, R25 100k + C26 OE RC,
  C20-C22 switch decoupling.
CONFIG declared as state 6 (pins 21 + 69 GND); signature on pins 75 + 1.
"""

import os
import subprocess
import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "hardware" / "tools"))
from route import inject_dsn_keepouts  # noqa: E402

FPLIB = os.path.expanduser(
    "~/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints")
JAVA = "/opt/homebrew/opt/openjdk/bin/java"
FRJAR = os.path.expanduser("~/tools/freerouting-2.3.0.jar")

LAYERS = int(sys.argv[sys.argv.index("--layers") + 1]) if "--layers" in sys.argv else 4
NO_ROUTE = "--no-route" in sys.argv
OUT = HERE / f"probe_{LAYERS}L.kicad_pcb"

mm = pcbnew.FromMM

# --- nets -------------------------------------------------------------------
# class B: (module pad, edge finger); module pad -> R -> SW S ; SW D -> finger
LEFT = [(4, 65), (5, 64), (6, 63), (7, 62), (8, 61), (9, 60), (10, 59)]
RIGHT = [(31, 30), (32, 32), (33, 34), (34, 36), (38, 40)]
EXP = LEFT + RIGHT  # EXP_0..EXP_11


def load_fp(lib, name):
    fp = pcbnew.FootprintLoad(f"{FPLIB}/{lib}.pretty", name)
    assert fp is not None, (lib, name)
    return fp


def main():
    board = pcbnew.LoadBoard(str(HERE / "probe_base.kicad_pcb"))

    # drop copper pours (re-poured after routing), keep rule areas
    # outer pours already stripped by strip.py (In1 GND / In2 +3V3 planes kept)
    for t in board.GetTracks():
        t.SetLocked(True)

    if LAYERS == 6:
        board.SetCopperLayerCount(6)
        # In1=GND, In2=+3V3 planes stay; In3/In4 become extra signal layers

    nets = {}

    def N(name):
        if name not in nets:
            ni = board.FindNet(name)
            if ni is None:
                ni = pcbnew.NETINFO_ITEM(board, name)
                board.Add(ni)
            nets[name] = ni
        return nets[name]

    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    U2, J1 = fps["U2"], fps["J1"]

    def setpad(fp, num, netname):
        hit = [p for p in fp.Pads() if p.GetNumber() == str(num)]
        assert hit, (fp.GetReference(), num)
        for p in hit:
            assert p.GetNetname() in ("", netname), (fp.GetReference(), num, p.GetNetname())
            p.SetNet(N(netname))

    # ---- auto-placer: nearest legal spot to the wanted position -------------
    import math
    T = pcbnew.ToMM

    def bbox_mm(b):
        return (T(b.GetLeft()), T(b.GetTop()), T(b.GetRight()), T(b.GetBottom()))

    def crt(fp):
        sh = fp.GetCourtyard(pcbnew.B_CrtYd if fp.IsFlipped() else pcbnew.F_CrtYd)
        if sh.OutlineCount():
            return bbox_mm(sh.BBox())
        return bbox_mm(fp.GetBoundingBox(False, False))

    def overlap(a, b, m=0.0):
        return not (a[2] + m <= b[0] or b[2] + m <= a[0] or a[3] + m <= b[1] or b[3] + m <= a[1])

    def dseg(px, py, a, b):
        (x1, y1), (x2, y2) = a, b
        dx, dy = x2 - x1, y2 - y1
        L = dx * dx + dy * dy
        u = 0 if L == 0 else max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / L))
        return math.hypot(px - (x1 + u * dx), py - (y1 + u * dy))

    def dbox(px, py, bx):
        x1, y1, x2, y2 = bx
        return math.hypot(max(x1 - px, 0, px - x2), max(y1 - py, 0, py - y2))

    # obstacles from rev B: B-side courtyards, copper reaching B.Cu
    crt_obs = [crt(fp) for fp in board.GetFootprints() if fp.IsFlipped()]
    cu_obs = []   # (seg_a, seg_b, halfwidth, net)
    for t in board.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T:
            q = (T(t.GetX()), T(t.GetY()))
            cu_obs.append((q, q, T(t.GetWidth(pcbnew.F_Cu)) / 2, t.GetNetname()))
        elif t.GetLayer() == pcbnew.B_Cu:
            cu_obs.append(((T(t.GetStart().x), T(t.GetStart().y)),
                           (T(t.GetEnd().x), T(t.GetEnd().y)), T(t.GetWidth()) / 2, t.GetNetname()))
    pad_obs = []  # (bbox, net) for pads on B.Cu (incl. PTH)
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if p.IsOnLayer(pcbnew.B_Cu):
                pad_obs.append((bbox_mm(p.GetBoundingBox()), p.GetNetname()))
    rule_obs = [bbox_mm(z.GetBoundingBox()) for z in board.Zones() if z.GetIsRuleArea()]
    REGION = (89.6, 118.9, 110.4, 147.0)   # bottom side, antenna keep-out .. finger band
    CLR = 0.2

    def legal(fp):
        c = crt(fp)
        if c[0] < REGION[0] or c[1] < REGION[1] or c[2] > REGION[2] or c[3] > REGION[3]:
            return False
        if any(overlap(c, o) for o in crt_obs):
            return False
        for p in fp.Pads():
            pb, n = bbox_mm(p.GetBoundingBox()), p.GetNetname()
            cx, cy = (pb[0] + pb[2]) / 2, (pb[1] + pb[3]) / 2
            r = math.hypot(pb[2] - pb[0], pb[3] - pb[1]) / 2
            if any(overlap(pb, ro, 0.1) for ro in rule_obs):
                return False
            for a, b, w, on in cu_obs:
                if (not n or on != n) and dseg(cx, cy, a, b) < r + w + CLR:
                    return False
            for ob, on in pad_obs:
                if (not n or on != n) and overlap(pb, ob, CLR):
                    return False
        return True

    def place(ref, lib, name, x, y, rot=0, pins=None):
        fp = load_fp(lib, name)
        fp.SetReference(ref)
        board.Add(fp)
        for num, netname in (pins or {}).items():
            setpad(fp, num, netname)
        fp.SetOrientationDegrees(rot)
        fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
        fp.Flip(fp.GetPosition(), False)  # bottom side
        best = None
        for r in [i * 0.1 for i in range(0, 140)]:
            n = max(1, int(2 * math.pi * r / 0.1))
            for k in range(n):
                a = 2 * math.pi * k / n
                for rr in (rot, rot + 90):
                    fp.SetOrientationDegrees(rr if not fp.IsFlipped() else 180 - rr)
                    fp.SetPosition(pcbnew.VECTOR2I(mm(x + r * math.cos(a)), mm(y + r * math.sin(a))))
                    if legal(fp):
                        best = True
                        break
                if best:
                    break
            if best:
                break
        if not best:
            print("NO LEGAL SPOT for", ref)
        crt_obs.append(crt(fp))
        for p in fp.Pads():
            pad_obs.append((bbox_mm(p.GetBoundingBox()), p.GetNetname()))
        return fp

    # edge + module nets
    for i, (mp, fg) in enumerate(EXP):
        setpad(U2, mp, f"EXP_{i}_MCU")
        setpad(J1, fg, f"EXP_{i}_EDGE")
    setpad(J1, 21, "GND")          # CONFIG_0
    setpad(J1, 69, "GND")          # CONFIG_1  -> state 6
    setpad(J1, 75, "CONFIG_2_SENSE")
    setpad(J1, 1, "CONFIG_3_SENSE")
    setpad(J1, 10, "LED_1_n")
    setpad(J1, 23, "WAKE_ON_WWAN_n")
    setpad(J1, 26, "W_DISABLE2_n")
    setpad(U2, 35, "IO42")   # -> U5 (LED_1#)
    setpad(U2, 24, "IO47")   # -> U6 (WAKE_ON_WWAN#)
    setpad(U2, 39, "IO1")    # <- U7 (W_DISABLE2#)
    setpad(U2, 11, "EXP_OE")  # IO18: readback of the detect output

    arr = ("Resistor_SMD", "R_Array_Convex_4x0402")
    groups = [(0, 1, 2, 3), (4, 5, 6), (7, 8, 9, 10)]
    for r, ((x, y, rot), g) in enumerate(zip([(95.3, 123.6, 90), (95.3, 126.4, 90),
                                               (106.6, 127.0, 90)], groups)):
        pins = {}
        for k, i in enumerate(g):
            pins[k + 1] = f"EXP_{i}_MCU"
            pins[8 - k] = f"EXP_{i}"
        place(f"RN{r+1}", *arr, x, y, rot, pins)
    r0402 = ("Resistor_SMD", "R_0402_1005Metric")
    c0402 = ("Capacitor_SMD", "C_0402_1005Metric")
    place("R26", *r0402, 100.0, 124.2, 90, {1: "EXP_11_MCU", 2: "EXP_11"})

    # switches: 4 ch each
    for s_, x in enumerate([97.0, 99.6, 104.8]):
        pins = {8: "GND", 16: "+3V3"}
        for k, (sel, sp, dp) in enumerate([(1, 2, 3), (4, 5, 6), (11, 10, 9), (15, 14, 13)]):
            i = s_ * 4 + k
            pins[sel] = "EXP_OE"
            pins[sp] = f"EXP_{i}"
            pins[dp] = f"EXP_{i}_EDGE"
        place(f"SW{s_+1}", "Package_DFN_QFN", "UQFN-16_1.8x2.6mm_P0.4mm", x, 120.4, 0, pins)
    for c, x in enumerate([97.0, 99.6, 104.8]):
        place(f"C{20+c}", *c0402, x, 122.4, 0, {1: "+3V3", 2: "GND"})

    # carrier detect: wired-NOR of two NMOS -> EXP_OE (high only if both sense pins at 0 V)
    place("Q1", "Package_TO_SOT_SMD", "SOT-363_SC-70-6", 102.2, 120.6, 0,
          {1: "GND", 2: "CFG2_G", 3: "EXP_OE", 4: "GND", 5: "CFG3_G", 6: "EXP_OE"})
    for ref, x, pins in [("R20", 101.0, {1: "CONFIG_2_SENSE", 2: "+3V3"}),
                         ("R21", 102.1, {1: "CONFIG_3_SENSE", 2: "+3V3"}),
                         ("R23", 103.2, {1: "CONFIG_2_SENSE", 2: "CFG2_G"}),
                         ("R24", 104.3, {1: "CONFIG_3_SENSE", 2: "CFG3_G"}),
                         ("R25", 105.4, {1: "EXP_OE", 2: "+3V3"})]:
        place(ref, *r0402, x, 124.2, 90, pins)
    place("C26", *c0402, 106.5, 124.2, 90, {1: "EXP_OE", 2: "GND"})

    # class A cells, lean variant: dual NMOS (SOT-363: 1 S1, 2 G1, 3 D2, 4 S2, 5 G2, 6 D1)
    # Q2 = open-drain outputs (LED_1#, WAKE_ON_WWAN#), gates pulled down
    # Q3 = W_DISABLE2# input: insulated gate on the edge pin, drain -> IO1 (inverted)
    sot363 = ("Package_TO_SOT_SMD", "SOT-363_SC-70-6")
    place("Q2", *sot363, 102.6, 127.0, 0, {1: "GND", 2: "IO42", 6: "LED_1_n",
                                         4: "GND", 5: "IO47", 3: "WAKE_ON_WWAN_n"})
    place("Q3", *sot363, 104.8, 129.6, 0, {1: "GND", 2: "W_DISABLE2_n", 6: "IO1",
                                         4: "GND", 5: "GND"})
    place("R28", *r0402, 101.0, 129.6, 90, {1: "IO42", 2: "GND"})
    place("R29", *r0402, 102.0, 129.6, 90, {1: "IO47", 2: "GND"})
    place("R30", *r0402, 103.0, 129.6, 90, {1: "IO1", 2: "+3V3"})
    place("R22", *r0402, 106.4, 129.6, 90, {1: "W_DISABLE2_n", 2: "+3V3"})

    # plane nets: one via per new GND/+3V3 pad, nudged to the nearest spot that
    # clears all existing copper (rev B routes signals on In1 here), rule areas
    # and other pads; short B.Cu stub pad -> via when nudged.
    import math
    newrefs = {"SW1", "SW2", "SW3", "Q1", "Q2", "Q3", "R20", "R21", "R22", "R25",
               "R28", "R29", "R30", "C20", "C21", "C22", "C26"}
    T = pcbnew.ToMM
    obst_seg, obst_box = [], []
    for t in board.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T:
            w = T(t.GetWidth(pcbnew.F_Cu)) / 2
            p0 = (T(t.GetX()), T(t.GetY()))
            obst_seg.append((p0, p0, w, t.GetNetname()))
        else:
            w = T(t.GetWidth()) / 2
            obst_seg.append(((T(t.GetStart().x), T(t.GetStart().y)),
                             (T(t.GetEnd().x), T(t.GetEnd().y)), w, t.GetNetname()))
    for fp in board.GetFootprints():
        for p in fp.Pads():
            bb = p.GetBoundingBox()
            obst_box.append(((T(bb.GetLeft()), T(bb.GetTop()), T(bb.GetRight()), T(bb.GetBottom())),
                             p.GetNetname(), p))
    keep = []
    for z in board.Zones():
        if z.GetIsRuleArea():
            bb = z.GetBoundingBox()
            keep.append((T(bb.GetLeft()), T(bb.GetTop()), T(bb.GetRight()), T(bb.GetBottom())))

    def dseg(px, py, a, b):
        (x1, y1), (x2, y2) = a, b
        dx, dy = x2 - x1, y2 - y1
        L = dx * dx + dy * dy
        u = 0 if L == 0 else max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / L))
        return math.hypot(px - (x1 + u * dx), py - (y1 + u * dy))

    def dbox(px, py, bx):
        x1, y1, x2, y2 = bx
        return math.hypot(max(x1 - px, 0, px - x2), max(y1 - py, 0, py - y2))

    VR, CL = 0.225, 0.2
    placed_vias = []

    edge_pts = []
    shapes = [d for d in board.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts]
    for fp in board.GetFootprints():
        shapes += [g for g in fp.GraphicalItems() if g.GetLayer() == pcbnew.Edge_Cuts]
    for sh in shapes:
        poly = sh.GetCorners() if False else None
        bb = sh.GetBoundingBox()
        x1, y1, x2, y2 = T(bb.GetLeft()), T(bb.GetTop()), T(bb.GetRight()), T(bb.GetBottom())
        if sh.GetShape() == pcbnew.SHAPE_T_SEGMENT:
            a_, b_ = sh.GetStart(), sh.GetEnd()
            for i in range(41):
                edge_pts.append((T(a_.x) + (T(b_.x) - T(a_.x)) * i / 40, T(a_.y) + (T(b_.y) - T(a_.y)) * i / 40))
        else:  # arcs/circles: conservative, bbox perimeter samples
            for i in range(21):
                f = i / 20
                edge_pts += [(x1 + (x2 - x1) * f, y1), (x1 + (x2 - x1) * f, y2),
                             (x1, y1 + (y2 - y1) * f), (x2, y1 + (y2 - y1) * f)]

    def ok(px, py, netname, own_pad):
        if any(math.hypot(px - ex, py - ey) < VR + 0.35 for ex, ey in edge_pts):
            return False
        for bx in keep:
            if dbox(px, py, bx) < VR + 0.05:
                return False
        for a, b, w, n in obst_seg:
            if n != netname and dseg(px, py, a, b) < VR + w + CL:
                return False
        for bx, n, p in obst_box:
            if p is own_pad:
                continue
            if n != netname and dbox(px, py, bx) < VR + CL:
                return False
        for (vx, vy, n) in placed_vias:
            if math.hypot(px - vx, py - vy) < 2 * VR + (0 if n == netname else CL) + 0.1:
                return False
        return True

    nvias, nnudge = 0, 0
    for fp in board.GetFootprints():
        if fp.GetReference() not in newrefs:
            continue
        for p in fp.Pads():
            if p.GetNetname() not in ("GND", "+3V3"):
                continue
            px, py = T(p.GetX()), T(p.GetY())
            fine = min(T(p.GetSize().x), T(p.GetSize().y)) < 0.3
            cands = [] if fine else [(px, py)]
            for r in (0.55, 0.7, 0.85, 1.0, 1.2, 1.4, 1.7, 2.0, 2.4):
                for k in range(16):
                    ang = 2 * math.pi * k / 16
                    cands.append((px + r * math.cos(ang), py + r * math.sin(ang)))
            for (vx, vy) in cands:
                # the stub must not cross foreign pads either
                if not ok(vx, vy, p.GetNetname(), p):
                    continue
                samples = [(px + (vx - px) * f / 10, py + (vy - py) * f / 10) for f in range(11)]
                if (vx, vy) != (px, py) and not all(
                        (n == p.GetNetname() or q is p or dbox(sx, sy, bx) > 0.075 + CL)
                        for (sx, sy) in samples for bx, n, q in obst_box):
                    continue
                if (vx, vy) != (px, py) and not all(
                        (n == p.GetNetname() or dseg(sx, sy, a, b) > 0.075 + w + CL)
                        for (sx, sy) in samples for a, b, w, n in obst_seg):
                    continue
                break
            else:
                print("NO VIA SPOT for", fp.GetReference(), p.GetNumber(), p.GetNetname())
                continue
            if (vx, vy) != (px, py):
                t = pcbnew.PCB_TRACK(board)
                t.SetStart(p.GetPosition())
                t.SetEnd(pcbnew.VECTOR2I(mm(vx), mm(vy)))
                t.SetWidth(mm(0.15)); t.SetLayer(pcbnew.B_Cu)
                t.SetNet(p.GetNet()); t.SetLocked(True)
                board.Add(t)
                obst_seg.append(((px, py), (vx, vy), 0.075, p.GetNetname()))
                nnudge += 1
            v = pcbnew.PCB_VIA(board)
            v.SetPosition(pcbnew.VECTOR2I(mm(vx), mm(vy)))
            v.SetWidth(mm(0.45)); v.SetDrill(mm(0.3))
            v.SetNet(p.GetNet()); v.SetLocked(True)
            board.Add(v)
            placed_vias.append((vx, vy, p.GetNetname()))
            obst_seg.append(((vx, vy), (vx, vy), VR, p.GetNetname()))
            nvias += 1
    print(f"power vias: {nvias} ({nnudge} nudged)")
    # J1 CONFIG_0/CONFIG_1 -> GND: F.Cu stub straight up from the finger to the
    # first legal via spot above the finger keep-outs
    for num in (21, 69):
        p = [q for q in J1.Pads() if q.GetNumber() == str(num)][0]
        px, py = T(p.GetX()), T(p.GetY())
        for dy in [1.9 + 0.1 * i for i in range(40)]:
            for dx in (0, -0.25, 0.25, -0.5, 0.5):
                vx, vy = px + dx, py - dy
                if ok(vx, vy, "GND", p):
                    break
            else:
                continue
            break
        else:
            print("NO VIA SPOT for J1", num)
            continue
        pts = [(px, py), (px, py - 1.6), (vx, vy)]
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1))); t.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
            t.SetWidth(mm(0.2)); t.SetLayer(pcbnew.F_Cu); t.SetNet(N("GND")); t.SetLocked(True)
            board.Add(t)
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(pcbnew.VECTOR2I(mm(vx), mm(vy))); v.SetWidth(mm(0.45)); v.SetDrill(mm(0.3))
        v.SetNet(N("GND")); v.SetLocked(True)
        board.Add(v)
    print(f"placed; new nets: {len(nets)}")

    pcbnew.SaveBoard(str(OUT), board)
    if NO_ROUTE:
        return

    # --- freerouting on the new signal nets only ---------------------------
    board = pcbnew.LoadBoard(str(OUT))
    dsn, ses = HERE / f"probe_{LAYERS}L.dsn", HERE / f"probe_{LAYERS}L.ses"
    ses.unlink(missing_ok=True)
    assert pcbnew.ExportSpecctraDSN(board, str(dsn))
    inject_dsn_keepouts(board, dsn)
    text = dsn.read_text()
    # rev B routes signals on In1, so the inner plane layers must stay "signal"
    # in the DSN (a "power" layer with wires on it = hundreds of violations and
    # freerouting internal errors). The plane zones stay as copper obstacles.
    for lyr in ("In1.Cu", "In2.Cu"):
        text = text.replace(f"(layer {lyr}\n      (type power)", f"(layer {lyr}\n      (type signal)")
    import re
    for pn in ("GND", "+3V3", "+3V3_M2"):
        text = re.sub(r"(\(net " + re.escape(pn) + r"\s*\n\s*\(pins)[^)]*\)",
                      r"\1)", text, count=1)
    dsn.write_text(text)
    r = subprocess.run([JAVA, "-jar", FRJAR, "-de", str(dsn), "-do", str(ses),
                        "-mp", "40", "-da"], capture_output=True, text=True, timeout=3000)
    (HERE / f"freerouting_{LAYERS}L.log").write_text(r.stdout + r.stderr)
    if not ses.exists():
        print(r.stdout[-3000:], r.stderr[-2000:])
        raise RuntimeError("freerouting produced no .ses")
    assert pcbnew.ImportSpecctraSES(board, str(ses))
    # outer GND pours (inner planes were kept), same params as route.py
    gnd = board.FindNet("GND")
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        z = pcbnew.ZONE(board)
        z.SetLayer(layer); z.SetNet(gnd); z.SetLocalClearance(mm(0.2))
        z.SetMinThickness(mm(0.15)); z.SetThermalReliefGap(mm(0.25))
        z.SetThermalReliefSpokeWidth(mm(0.3))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        o = z.Outline(); o.NewOutline()
        for (x, y) in [(89.2, 108.2), (110.8, 108.2), (110.8, 149.8), (89.2, 149.8)]:
            o.Append(mm(x), mm(y))
        board.Add(z)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(str(OUT), board)
    conn = board.GetConnectivity()
    conn.RecalculateRatsnest()
    print("unrouted connections:", conn.GetUnconnectedCount(True))
    print("saved", OUT)


if __name__ == "__main__":
    from kicad_exit import run
    run(main)
