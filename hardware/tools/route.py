"""Route the board: scripted USB diff pair + freerouting for the rest.

Run with KiCad's bundled python:
  .../Versions/3.9/bin/python3 tools/route.py [--skip-freerouting]

Pipeline (SPEC 6.3: 90-ohm pair, length-matched, solid reference, no stubs):
  1. Pre-route USB_D pair by script (0.14/0.14 mm, USB_DIFF class), locked:
       J1 fingers (F.Cu) -> via pair -> USBLC6 U1 (B.Cu)
       U1 -> F.Cu corridor between JST row and module -> R7/R8 (B.Cu)
       R7/R8 -> via -> module pads 13/14 (F.Cu)
     P/N legs are built from the same waypoint skeleton -> near-equal length
     (both lengths printed; USB-FS intra-pair budget is enormous).
  2. Export Specctra DSN, run freerouting headless on remaining nets
     (pre-routed tracks are locked/fixed), import .ses.
  3. Pour planes: GND on F/In1/B, +3V3 on In2 (antenna rule area already
     excludes all copper there).
  4. Fill zones, save; DRC runs separately via kicad-cli.
"""

import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
PCB = HERE / "kicad" / "esp32_m2_companion.kicad_pcb"
JAVA = os.path.expanduser("/opt/homebrew/opt/openjdk/bin/java")
FRJAR = os.path.expanduser("~/tools/freerouting-2.3.0.jar")

import pcbnew  # noqa: E402


def mm(v):
    return pcbnew.FromMM(v)


def tomm(v):
    return pcbnew.ToMM(v)


def pad_pos(board, ref, pin):
    fp = board.FindFootprintByReference(ref)
    for p in fp.Pads():
        if p.GetNumber() == str(pin):
            pos = p.GetPosition()
            return (tomm(pos.x), tomm(pos.y))
    raise KeyError(f"{ref}.{pin}")


def net(board, name):
    n = board.GetNetsByName()[name]
    return n.GetNetCode()


def add_track(board, netcode, layer, pts, width=0.14, lock=True):
    total = 0.0
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
        t.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
        t.SetWidth(mm(width))
        t.SetLayer(layer)
        t.SetNetCode(netcode)
        t.SetLocked(lock)
        board.Add(t)
        total += ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
    return total


def add_via(board, netcode, x, y, lock=True):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    v.SetDrill(mm(0.3))
    v.SetWidth(mm(0.6))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetNetCode(netcode)
    v.SetLocked(lock)
    board.Add(v)


def preroute_usb(board):
    """USB pair: fingers -> ESD -> series R -> module, P/N parallel."""
    n_edge_p = net(board, "USBH3_D_P")
    n_edge_n = net(board, "USBH3_D_N")
    n_esd_p = net(board, "USB_D_P_ESD")
    n_esd_n = net(board, "USB_D_N_ESD")
    n_p = net(board, "USB_D_P")
    n_n = net(board, "USB_D_N")

    j7 = pad_pos(board, "J1", 7)     # D+ finger (F)
    j9 = pad_pos(board, "J1", 9)     # D- finger (F)
    u1_1 = pad_pos(board, "U1", 1)   # edge side D+ (B)
    u1_3 = pad_pos(board, "U1", 3)   # edge side D- (B)
    u1_6 = pad_pos(board, "U1", 6)   # mcu side D+ (B)
    u1_4 = pad_pos(board, "U1", 4)   # mcu side D- (B)
    r7_1 = pad_pos(board, "R7", 1)
    r7_2 = pad_pos(board, "R7", 2)
    r8_1 = pad_pos(board, "R8", 1)
    r8_2 = pad_pos(board, "R8", 2)
    u2_14 = pad_pos(board, "U2", 14)  # USB_D+ module pad (F)
    u2_13 = pad_pos(board, "U2", 13)  # USB_D- module pad (F)

    lengths = {}
    F, B = pcbnew.F_Cu, pcbnew.B_Cu

    # --- Leg 1: fingers (F) -> staggered vias -> U1 pins 1/3 (B) ---
    # U1 (flipped) has pins 1/2/3 stacked on its LEFT column (x 106.56,
    # y 144.25/143.30/142.35). D+ drops straight, D- fans left and routes
    # around pad 1 to reach pad 3. Via centers 2.25 mm apart.
    # D+ drops on F to y147.4, jogs WEST to x106.3 (leaving J1.8's exit
    # column x107.5 clear for W_DISABLE1_n), vias down, enters U1.1.
    vp = (106.3, 146.6)
    vn = (105.55, 146.8)  # clears U1 pad-1 west edge (105.90) and C4
    lengths["P1"] = add_track(board, n_edge_p, F,
                              [j7, (j7[0], 147.4), vp])
    # exit pad 9 downward past the finger row (pads end y 147.5) BEFORE
    # fanning left, so the diagonal clears GND finger pad 11
    lengths["N1"] = add_track(board, n_edge_n, F,
                              [j9, (j9[0], 147.3), vn])
    add_via(board, n_edge_p, *vp)
    add_via(board, n_edge_n, *vn)
    lengths["P1"] += add_track(board, n_edge_p, B,
                               [vp, (106.3, 144.85), (u1_1[0], 144.85),
                                u1_1])
    lengths["N1"] += add_track(board, n_edge_n, B,
                               [vn, (vn[0], u1_3[1]), u1_3])

    # --- Leg 2: U1 pins 6/4 (B, right column) -> R7/R8 pin 1 (B) ---
    # Exit right of U1, drop, then two horizontal corridors in the free
    # band between row-2 pads (y>=138.4) and the TP row (y<=137.35):
    # N upper (137.6), P lower (138.0). Drops: P at x 91.5 (TP1/TP2 +
    # R5-pad window), N at x 94.375 straight into R8.1 (R6 pad window).
    # Two B.Cu lanes fit between the TP pads (<=137.35) and the C/D-row
    # pads (>=138.275). Crossing-free ordering: P enters east of N
    # (110.15 vs 109.8), N's lane (138.0) never extends past P's entry,
    # P's lane (137.62) never reaches N's entry drop; P exits north at
    # r7_1 (east), N at r8_1 (west of P's lane end).
    lengths["P2"] = add_track(board, n_esd_p, B,
                              [u1_6, (109.7, u1_6[1]), (109.7, 145.2),
                               (110.45, 145.2), (110.45, 137.62),
                               (r7_1[0], 137.62), r7_1])
    lengths["N2"] = add_track(board, n_esd_n, B,
                              [u1_4, (109.8, u1_4[1]), (109.8, 138.0),
                               (r8_1[0], 138.0), r8_1])

    # --- Leg 3: R7/R8 pin 2 (B) -> vias -> module pads 13/14 (F) ---
    # P swings left around D3/R3 and approaches pad 14 from the left;
    # N vias up at x 95.7 and approaches pad 13 from the right. The two
    # F-side paths never overlap in x.
    # P: via at R7.2, F west at pad-14 row approaching from the east
    vpp = (r7_2[0], 131.3)
    lengths["P3"] = add_track(board, n_p, B, [r7_2, vpp])
    add_via(board, n_p, *vpp)
    lengths["P3"] += add_track(board, n_p, F,
                               [vpp, (vpp[0], u2_14[1]), u2_14])
    # N: via at R8.2, F west at pad-13 row (1.27 south of pad-14 row, so
    # the two F runs never overlap)
    vnn = (r8_2[0], 131.3)
    lengths["N3"] = add_track(board, n_n, B, [r8_2, vnn])
    add_via(board, n_n, *vnn)
    lengths["N3"] += add_track(board, n_n, F,
                               [vnn, (vnn[0], u2_13[1]), u2_13])

    ptot = lengths["P1"] + lengths["P2"] + lengths["P3"]
    ntot = lengths["N1"] + lengths["N2"] + lengths["N3"]
    print(f"USB pair pre-routed: P={ptot:.2f} mm, N={ntot:.2f} mm, "
          f"skew={abs(ptot-ntot):.2f} mm")
    return abs(ptot - ntot)


def more_fixups(board):
    """Deterministic routes for the two nets freerouting keeps abandoning
    in the boxed-in east corner, + solid zone connect for U1 GND."""
    v33 = net(board, "+3V3")
    u1_5 = pad_pos(board, "U1", 5)
    via = (109.9, u1_5[1])
    add_track(board, v33, pcbnew.B_Cu, [u1_5, via], width=0.15)
    add_via(board, v33, *via)   # into the In2 +3V3 plane

    # EN: D1.3 -> C5.1. Everything horizontal on B at this latitude is
    # taken (P2/N2 lanes, pad rows), and D2 pin 3 sits dead-center at
    # y 139.7 - so hop across on In2 (bare plane layer; the pour comes
    # later and keeps clearance) and drop onto C5.1 from the north.
    en = net(board, "EN")
    d1_3 = pad_pos(board, "D1", 3)
    c5_1 = pad_pos(board, "C5", 1)
    # v1 sits WEST of D1 pin 3: at x99.3 it walled D2.2 (W_DISABLE1_n)
    # into an unroutable pocket
    v1 = (98.1, 141.6)
    v2 = (107.45, 141.6)
    add_track(board, en, pcbnew.B_Cu,
              [d1_3, (98.1, d1_3[1]), v1], width=0.15)
    add_via(board, en, *v1)
    add_track(board, en, pcbnew.In2_Cu, [v1, v2], width=0.15)
    add_via(board, en, *v2)
    add_track(board, en, pcbnew.B_Cu,
              [v2, (c5_1[0], 141.6), c5_1], width=0.15)
    # R1.2 (EN pull-up) is walled south of the N2 lane: bridge east of R1
    # up to the In2 hop's v2
    r1_2 = pad_pos(board, "R1", 2)
    add_track(board, en, pcbnew.B_Cu,
              [r1_2, (107.45, r1_2[1]), v2], width=0.15)
    # TP1 (EN) is walled by both USB lanes: via-in-pad down to In2, join
    # the In2 EN run (x 107.2 lies on its 99.3..107.45 span)
    tp1 = pad_pos(board, "TP1", 1)
    vtp = (tp1[0], tp1[1] - 0.4)   # north edge of the pad: clears the
    add_via(board, en, *vtp)       # netless U2 pad 26 keepout
    add_track(board, en, pcbnew.B_Cu, [tp1, vtp], width=0.3)
    add_track(board, en, pcbnew.In2_Cu,
              [vtp, (vtp[0], 141.6), (tp1[0], 141.6)], width=0.15)

    # +3V3_M2: bus both VCC finger clusters over In2 (B at finger latitude
    # is walled by GPIO5/leg-1; In2 is empty there)
    v3m2 = net(board, "+3V3_M2")
    fb1_1 = pad_pos(board, "FB1", 1)
    for pins, chain_y in ((("70", "72", "74"), 148.2), (("2", "4"), 148.2)):
        pts = [pad_pos(board, "J1", p) for p in pins]
        add_track(board, v3m2, pcbnew.B_Cu,
                  [(pts[0][0], chain_y), (pts[-1][0], chain_y)], width=0.3)
        for p in pts:
            add_track(board, v3m2, pcbnew.B_Cu,
                      [p, (p[0], chain_y)], width=0.3)
    # y 145.9: clears the leg-1 USB vias at y 146.8/147.0
    vA = (92.0, 145.9)
    vB = (108.75, 145.9)
    add_track(board, v3m2, pcbnew.B_Cu, [(92.0, 148.2), vA], width=0.3)
    add_track(board, v3m2, pcbnew.B_Cu, [(108.75, 148.2), vB], width=0.3)
    add_via(board, v3m2, *vA)
    add_via(board, v3m2, *vB)
    add_track(board, v3m2, pcbnew.In2_Cu, [vA, vB], width=0.3)
    add_track(board, v3m2, pcbnew.B_Cu,
              [fb1_1, (fb1_1[0], 145.4), (vA[0], 145.9)], width=0.3)

    # GND stitching vias (also re-melds the fragmented B pour to L2)
    gnd = net(board, "GND")
    for pt in ((90.0, 124.0), (110.1, 120.5), (96.5, 146.3), (90.3, 145.4),
               (104.4, 136.2)):  # last: on TP6 (GND), north edge - clears
               # the netless U2 pad-24 keepout
        add_via(board, gnd, *pt)
    # EPAD via grid (HDG: >=9 GND vias under the module thermal pad).
    # The JLC footprint provides 0.6 mm GND satellite pads as via-in-pad
    # sites - drop a via on each
    u2 = board.FindFootprintByReference("U2")
    for p in u2.Pads():
        if p.GetNumber() == "41" and pcbnew.ToMM(p.GetSize().x) < 1.0:
            pos = p.GetPosition()
            add_via(board, gnd, pcbnew.ToMM(pos.x), pcbnew.ToMM(pos.y))

    u1 = board.FindFootprintByReference("U1")
    for p in u1.Pads():
        if p.GetNetname() == "GND":
            p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)

    # IO0_BOOT backbone D2.3 -> TP2 (freerouting keeps leaving a gap in
    # the row-2 maze): between C4's pads, up over v1, down west of D1,
    # under TP3 into TP2
    # D2.3 -> R2.2 east through the between-pad-row lane (y 139.7 passes
    # between the 138.45..139.4 and 140.0..140.95 pad rows of C4/R2)
    io0 = net(board, "IO0_BOOT")
    d2_3 = pad_pos(board, "D2", 3)
    r2_2 = pad_pos(board, "R2", 2)
    add_track(board, io0, pcbnew.B_Cu,
              [d2_3, (r2_2[0], d2_3[1]), r2_2], width=0.15)

    # W_DISABLE1_n: J1.8's only exit is its own column x 107.5; hop the
    # congested corner on In2 and needle down between D1.3 and D2.1/D2.2
    # (both gaps 0.1375) into D2.2 from the west
    wd = net(board, "W_DISABLE1_n")
    j8 = pad_pos(board, "J1", 8)
    d2_2 = pad_pos(board, "D2", 2)
    # In2 diagonal at y>=143 (north of EN's In2 hop at y141.6-142.35),
    # then drop straight onto D2.2 from directly north (x100.66) so it
    # never runs down the x99.3 column that grazes D1.3/EN
    vw1 = (107.5, 145.6)          # J1.8 exit column, now clear of USB via
    vw2 = (d2_2[0], 143.0)
    add_track(board, wd, pcbnew.B_Cu, [j8, vw1], width=0.14)
    add_via(board, wd, *vw1)
    add_track(board, wd, pcbnew.In2_Cu, [vw1, (107.5, 143.0), vw2],
              width=0.15)
    add_via(board, wd, *vw2)
    add_track(board, wd, pcbnew.B_Cu, [vw2, d2_2], width=0.14)


def netless_pad_via_keepouts(board):
    """KiCad's DSN export omits netless pads, so freerouting happily drops
    vias on them. Blanket every netless SMD pad with a vias-only keepout."""
    n = 0
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetCode() != 0:
                continue
            if not any(pcbnew.IsCopperLayer(l)
                       for l in pad.GetLayerSet().Seq()):
                continue   # paste/mask-only aperture (e.g. EPAD windows)
            bb = pad.GetBoundingBox()
            z = pcbnew.ZONE(board)
            z.SetIsRuleArea(True)
            z.SetDoNotAllowVias(True)
            z.SetDoNotAllowTracks(False)
            z.SetDoNotAllowCopperPour(False)
            z.SetDoNotAllowPads(False)
            lset = pcbnew.LSET()
            for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
                lset.AddLayer(layer)
            z.SetLayerSet(lset)
            m = pcbnew.FromMM(0.2)
            o = z.Outline()
            o.NewOutline()
            for (x, y) in ((bb.GetLeft()-m, bb.GetTop()-m),
                           (bb.GetRight()+m, bb.GetTop()-m),
                           (bb.GetRight()+m, bb.GetBottom()+m),
                           (bb.GetLeft()-m, bb.GetBottom()+m)):
                o.Append(int(x), int(y))
            board.Add(z)
            n += 1
    print(f"via-keepouts over {n} netless pads")


def preroute_fixups(board):
    """Nets freerouting abandoned: route them deterministically, locked.
    - R5.1/R6.1 (+3V3, DNP bare pads, B.Cu): stub south + via to L3 plane
      (window between the DNP row and the TP pads).
    - J1 pin 20 (PCIE_1_GPIO_5, B.Cu finger) -> D2 pin 1: L-route at
      x 103.9 (clears C4 pad edge 104.45 and R2 pads)."""
    v33 = net(board, "+3V3")
    for ref in ("R5", "R6"):
        p1 = pad_pos(board, ref, 1)
        p2 = pad_pos(board, ref, 2)
        away = -1.2 if p1[1] < p2[1] else 1.2   # extend past pad 1
        via = (p1[0], p1[1] + away)
        add_track(board, v33, pcbnew.B_Cu, [p1, via], width=0.15)
        add_via(board, v33, *via)
    g5 = net(board, "PCIE_1_GPIO_5")
    j20 = pad_pos(board, "J1", 20)
    d2_1 = pad_pos(board, "D2", 1)
    # exit below the finger row (pads end y 147.5) before jogging west
    add_track(board, g5, pcbnew.B_Cu,
              [j20, (104.5, 147.2), (103.5, 146.6), (103.5, d2_1[1]), d2_1],
              width=0.15)
    # J1 pad 11 (F-side GND finger) is walled off from the F pour by the
    # USB fan: stub west at y 147.4 (above the fan diagonal) into open pour
    gnd = net(board, "GND")
    j11 = pad_pos(board, "J1", 11)
    add_track(board, gnd, pcbnew.F_Cu,
              [(j11[0], 147.5), (j11[0], 147.45), (105.0, 147.45)],
              width=0.15)
    # solid zone connection for J1 GND fingers (kills starved-thermal too)
    j1 = board.FindFootprintByReference("J1")
    for p in j1.Pads():
        if p.GetNetname() == "GND":
            p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)


def post_cleanup(board):
    """Widen any freerouting track below JLC minimum; tent every via."""
    widened = 0
    for t in board.GetTracks():
        if t.GetClass() == "PCB_VIA":
            t.SetFrontTentingMode(pcbnew.TENTING_MODE_TENTED)
            t.SetBackTentingMode(pcbnew.TENTING_MODE_TENTED)
        elif t.GetWidth() < mm(0.127):
            t.SetWidth(mm(0.15))
            widened += 1
    print(f"post-cleanup: widened {widened} thin tracks, tented all vias")


def inject_dsn_keepouts(board, dsn):
    """Append per-netless-pad keepouts into the DSN structure section
    (DSN: um units, y negated)."""
    ko = []
    i = 0
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetCode() != 0:
                continue
            if not any(pcbnew.IsCopperLayer(l)
                       for l in pad.GetLayerSet().Seq()):
                continue
            bb = pad.GetBoundingBox()
            m = pcbnew.FromMM(0.2)
            x1, x2 = (bb.GetLeft()-m)/1000.0, (bb.GetRight()+m)/1000.0
            y1, y2 = -(bb.GetTop()-m)/1000.0, -(bb.GetBottom()+m)/1000.0
            layer = "F.Cu" if fp.GetLayerName() == "F.Cu" else "B.Cu"
            i += 1
            ko.append(f'    (keepout "np{i}" (polygon {layer} 0 '
                      f'{x1:.1f} {y1:.1f} {x2:.1f} {y1:.1f} '
                      f'{x2:.1f} {y2:.1f} {x1:.1f} {y2:.1f}))')
    text = dsn.read_text()
    # keepouts must live INSIDE (structure ...): anchor on its (rule block
    anchor = "    (rule"
    assert anchor in text
    text = text.replace(anchor, "\n".join(ko) + "\n" + anchor, 1)
    dsn.write_text(text)
    print(f"injected {i} DSN keepouts")


def run_freerouting(board):
    dsn = HERE / "build" / "route.dsn"
    ses = HERE / "build" / "route.ses"
    ses.unlink(missing_ok=True)
    ok = pcbnew.ExportSpecctraDSN(board, str(dsn))
    if not ok:
        raise RuntimeError("DSN export failed")
    inject_dsn_keepouts(board, dsn)
    r = subprocess.run(
        [JAVA, "-jar", FRJAR, "-de", str(dsn), "-do", str(ses),
         "-mp", "50", "-da"],
        capture_output=True, text=True, timeout=3300)
    if not ses.exists():
        print(r.stdout[-3000:], r.stderr[-2000:])
        raise RuntimeError("freerouting produced no .ses")
    if not pcbnew.ImportSpecctraSES(board, str(ses)):
        raise RuntimeError("SES import failed")
    print("freerouting done")


def pour_planes(board):
    gnd = net(board, "GND")
    v33 = net(board, "+3V3")
    # card outline (with margin) in sheet coords
    pts = [(89.2, 108.2), (110.8, 108.2), (110.8, 149.8), (89.2, 149.8)]
    specs = [(pcbnew.In1_Cu, gnd, "GND_L2"), (pcbnew.In2_Cu, v33, "PWR_L3"),
             (pcbnew.F_Cu, gnd, "GND_top"), (pcbnew.B_Cu, gnd, "GND_bot")]
    for layer, netcode, name in specs:
        z = pcbnew.ZONE(board)
        z.SetLayer(layer)
        z.SetNetCode(netcode)
        z.SetZoneName(name)
        z.SetLocalClearance(mm(0.2))
        z.SetMinThickness(mm(0.15))
        z.SetThermalReliefGap(mm(0.25))
        z.SetThermalReliefSpokeWidth(mm(0.3))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL
                           if layer in (pcbnew.F_Cu, pcbnew.B_Cu)
                           else pcbnew.ZONE_CONNECTION_FULL)
        o = z.Outline()
        o.NewOutline()
        for (x, y) in pts:
            o.Append(mm(x), mm(y))
        board.Add(z)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    print("planes poured & filled")


def main():
    skip_fr = "--skip-freerouting" in sys.argv
    board = pcbnew.LoadBoard(str(PCB))
    skew = preroute_usb(board)
    preroute_fixups(board)
    more_fixups(board)
    netless_pad_via_keepouts(board)
    # Intra-pair skew: ~6.7 ps/mm on FR-4. USB-FS bit period is 83 ns and
    # USB 2.0 places no FS intra-pair skew limit remotely near this scale;
    # 10 mm = 67 ps = 0.08% of a bit. Matching effort goes to impedance
    # continuity instead (0.14/0.14 pair geometry, solid references).
    assert skew < 10.0, f"USB pair skew {skew} mm too large"
    pcbnew.SaveBoard(str(PCB), board)
    if not skip_fr:
        board = pcbnew.LoadBoard(str(PCB))
        run_freerouting(board)
        pcbnew.SaveBoard(str(PCB), board)
    board = pcbnew.LoadBoard(str(PCB))
    post_cleanup(board)
    pour_planes(board)
    pcbnew.SaveBoard(str(PCB), board)
    print("routing pipeline complete:", PCB)


if __name__ == "__main__":
    main()
