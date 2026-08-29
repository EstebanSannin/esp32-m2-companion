"""Generate the Phase 2 starting .kicad_pcb from the SKiDL netlist.

Run with KiCad's bundled python (has pcbnew):
  ~/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3 tools/gen_pcb.py

Produces hardware/kicad/esp32_m2_companion.kicad_pcb:
  - all footprints with nets (kinet2pcb)
  - 4 copper layers, 0.8 mm board
  - J1 edge fingers at origin (its Edge.Cuts ARE the 2242 board outline)
  - placement proposal (owner adjusts/routes in the GUI)
  - net classes: USB_DIFF (90 ohm pair - GEOMETRY TBD from JLCPCB impedance
    calculator for their 0.8mm 4-layer stackup; placeholder values marked)
  - antenna keep-out rule area on all copper layers
  - JLCPCB-standard DRC minima

Placement rationale (docs/pinmap.md, EM spec Fig 19):
  Card coords: J1 at (0,0), card spans x -11..+11, y -42(top)..0(edge).
  - Mounting screw head owns a ~R3.5 zone at (0,-42): module must clear it.
  - Module (18 x 25.5, antenna at its top ~6 mm) centered in x, top edge at
    y=-37.5 => antenna zone y -37.5..-31.5, 4.5 mm below card top edge.
  - USBLC6 close to fingers (y ~ -4.5), diff pair straight shot to module
    IO19/IO20 which are on the module's right edge.
  - Recovery diodes near fingers (pins 8/20/50 all in right half).
"""

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent   # hardware/
OUT = HERE / "kicad"
NET = HERE / "build" / "esp32_m2_companion.net"
KICAD_FP = os.path.expanduser(
    "~/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints")

import kinet2pcb  # noqa: E402
import pcbnew  # noqa: E402


def build_pcb():
    pcb_path = OUT / "esp32_m2_companion.kicad_pcb"
    libs = [str(OUT), KICAD_FP]
    kinet2pcb.kinet2pcb(str(NET), str(pcb_path), libs)
    return pcb_path


def mm(v):
    return pcbnew.FromMM(v)


# Sheet origin for the card's (0,0) reference (J1 edge row)
ORIGIN = (100.0, 150.0)

# ref -> (x, y, rot_deg, side)  in card coords (J1 edge row at y=0)
PLACEMENT = {
    # Socket coverage zone: the mated M.2 connector overlaps the card's
    # first 4.8 mm on BOTH faces (EM spec Figs 38/39: 9.10 deep incl land
    # pattern, 4.30 beyond the card edge). J1's courtyard now covers it;
    # every courtyard below starts at y <= -4.8. Owner-caught at review.
    "J1": (0, 0, 0, "F"),
    "U2": (0, -24.75, 0, "F"),      # module center: top edge at -37.5
    # --- TOP: connectors only (vertical JST, courtyards 5.29 deep) ---
    "J4": (-4.2, -7.5, 0, "F"),     # SH-8 vertical: UART/SPI/GPIO
    "J3": (6.0, -7.5, 0, "F"),      # SH-4 vertical: Qwiic I2C
    # --- BOTTOM row 1 (y -6.7): clears socket zone ---
    "U1": (7.7, -6.7, 0, "B"),      # USBLC6, still nearest fingers 7/9
    "C4": (4.9, -6.7, 90, "B"),     # USBLC6 VBUS 100n
    "FB1": (-8.6, -6.7, 90, "B"),   # power entry near VCC fingers
    # --- BOTTOM row 2 (y -10.3) ---
    "C1": (-9.4, -10.3, 90, "B"),
    "C2": (-7.4, -10.3, 90, "B"),
    "C3": (-5.4, -10.3, 90, "B"),
    "D1": (-2.3, -10.3, 0, "B"),    # EN diode
    "D2": (1.6, -10.3, 0, "B"),     # BOOT diode
    "R2": (4.6, -10.3, 90, "B"),    # BOOT pull-up
    "R1": (6.5, -10.3, 90, "B"),    # EN pull-up
    "C5": (8.4, -10.3, 90, "B"),    # EN RC 1u
    # --- BOTTOM: TPs (y -13.4), DNP bare pads (y -15.9) ---
    "TP1": (-9.6, -13.4, 0, "B"),   # TP_EN
    "TP2": (-6.8, -13.4, 0, "B"),   # TP_BOOT
    "TP3": (-4.0, -13.4, 0, "B"),   # TP_TXD0
    "TP4": (-1.2, -13.4, 0, "B"),   # TP_RXD0
    "TP5": (1.6, -13.4, 0, "B"),    # TP_3V3
    "TP6": (4.4, -13.4, 0, "B"),    # TP_GND
    "R5": (-8.6, -15.9, 0, "B"),    # DNP I2C PU (bare pads)
    "R6": (-5.6, -15.9, 0, "B"),    # DNP I2C PU
    "C8": (-2.6, -15.9, 0, "B"),    # DNP USB shunt
    "C9": (0.4, -15.9, 0, "B"),     # DNP USB shunt
    # --- BOTTOM: under module (below antenna keepout) ---
    "R7": (-8.2, -17.7, 0, "B"),    # USB series 0R near module pins 13/14
    "R8": (-4.8, -17.7, 0, "B"),
    "D3": (-9.3, -20.2, 90, "B"),   # power LED at left edge (side glow)
    "R3": (-7.3, -20.2, 90, "B"),
    "D4": (-9.3, -23.6, 90, "B"),   # status LED at left edge
    "R4": (-7.3, -23.6, 90, "B"),
    "C6": (-8.2, -30.0, 90, "B"),   # 100n at module 3V3 (pin 2)
    "C7": (-6.2, -30.0, 90, "B"),   # 10u at module 3V3
}



def postprocess(pcb_path):
    board = pcbnew.LoadBoard(str(pcb_path))
    ds = board.GetDesignSettings()

    # 4 layers, 0.8 mm
    board.SetCopperLayerCount(4)
    ds.SetBoardThickness(mm(0.8))

    # JLCPCB-standard minima (SPEC section 5 / CLAUDE.md)
    ds.m_TrackMinWidth = mm(0.127)      # 5 mil
    ds.m_MinClearance = mm(0.127)
    # Edge clearance 0: the gold fingers legitimately touch the board edge
    # (140 J1 violations otherwise). Non-finger copper is kept off the edge
    # by courtyards/placement - visually check at GATE 3.
    ds.m_CopperEdgeClearance = 0
    ds.m_ViasMinSize = mm(0.45)
    ds.m_MinThroughDrill = mm(0.3)
    ds.m_SolderMaskMinWidth = 0
    # J1's 0.5 mm-pitch fingers share merged mask apertures - standard for
    # card edges; allow bridges inside a single footprint.
    ds.m_AllowSoldermaskBridgesInFPs = True

    # Netclasses (KiCad 9 NET_SETTINGS API)
    ns = ds.m_NetSettings
    default = ns.GetDefaultNetclass()
    default.SetTrackWidth(mm(0.15))
    default.SetClearance(mm(0.15))
    default.SetViaDrill(mm(0.3))
    default.SetViaDiameter(mm(0.6))

    # USB 90-ohm differential pair. PLACEHOLDER geometry: final width/gap
    # must come from JLCPCB's impedance calculator for their 0.8 mm 4-layer
    # stackup (JLC04081H) before routing - flagged in docs/risks.md.
    usb = pcbnew.NETCLASS("USB_DIFF")
    usb.SetTrackWidth(mm(0.15))
    usb.SetDiffPairWidth(mm(0.15))
    usb.SetDiffPairGap(mm(0.15))
    usb.SetClearance(mm(0.127))
    ns.SetNetclass("USB_DIFF", usb)
    for pat in ("USBH3_D_P", "USBH3_D_N", "USB_D_P", "USB_D_N"):
        ns.SetNetclassPatternAssignment(pat, "USB_DIFF")

    # Placement
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if ref in PLACEMENT:
            x, y, rot, side = PLACEMENT[ref]
            fp.SetPosition(pcbnew.VECTOR2I(mm(ORIGIN[0] + x),
                                           mm(ORIGIN[1] + y)))
            if side == "B" and fp.GetSide() != pcbnew.B_Cu:
                fp.Flip(fp.GetPosition(), False)
            fp.SetOrientationDegrees(rot)

    # Antenna keep-out: all-layer rule area over module antenna region
    # (module top 6 mm => card y -37.5..-31.5, full module width plus margin)
    zone = pcbnew.ZONE(board)
    zone.SetIsRuleArea(True)
    zone.SetDoNotAllowTracks(True)
    zone.SetDoNotAllowCopperPour(True)
    zone.SetDoNotAllowVias(True)
    zone.SetDoNotAllowPads(False)
    zone.SetZoneName("antenna_keepout_espressif_hdg")
    lset = pcbnew.LSET()
    for layer in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
        lset.AddLayer(layer)
    zone.SetLayerSet(lset)
    pts = [(-10.0, -37.6), (10.0, -37.6), (10.0, -31.4), (-10.0, -31.4)]
    outline = zone.Outline()
    outline.NewOutline()
    for (x, y) in pts:
        outline.Append(mm(ORIGIN[0] + x), mm(ORIGIN[1] + y))
    board.Add(zone)

    pcbnew.SaveBoard(str(pcb_path), board)
    print("post-processed", pcb_path)


def write_project(pcb_path):
    """KiCad 9 keeps DRC constraints in the .kicad_pro, not the board file."""
    import json
    def _cls(name, extra=None):
        c = {
            "bus_width": 6.0, "clearance": 0.127,
            "diff_pair_gap": 0.15, "diff_pair_via_gap": 0.25,
            "diff_pair_width": 0.15, "line_style": 0,
            "microvia_diameter": 0.3, "microvia_drill": 0.1,
            "name": name, "pcb_color": "rgba(0, 0, 0, 0.000)",
            "schematic_color": "rgba(0, 0, 0, 0.000)",
            "track_width": 0.15, "via_diameter": 0.6, "via_drill": 0.3,
            "wire_width": 6.0,
        }
        c.update(extra or {})
        return c

    pro = {
        "net_settings": {
            # USB_DIFF width/gap PLACEHOLDER until JLCPCB impedance calc
            # for the 0.8 mm 4-layer stackup (GATE 3)
            "classes": [_cls("Default"), _cls("USB_DIFF")],
            "netclass_patterns": [
                {"netclass": "USB_DIFF", "pattern": p}
                for p in ("USBH3_D_P", "USBH3_D_N", "USB_D_P", "USB_D_N",
                          "USB_D_P_ESD", "USB_D_N_ESD")
            ],
            "meta": {"version": 0},
            "net_colors": None,
        },
        "board": {
            "design_settings": {
                "rules": {
                    "allow_blind_buried_vias": False,
                    "allow_microvias": False,
                    "max_error": 0.005,
                    "min_clearance": 0.127,
                    # 0: gold fingers legitimately touch the edge; non-finger
                    # copper kept off edges by placement - check at GATE 3
                    "min_copper_edge_clearance": 0.0,
                    "min_hole_to_hole": 0.25,
                    "min_microvia_diameter": 0.2,
                    "min_microvia_drill": 0.1,
                    "min_through_hole_diameter": 0.3,
                    "min_track_width": 0.127,
                    "min_via_annular_width": 0.075,
                    "min_via_diameter": 0.45,
                    "solder_mask_clearance": 0.0,
                    "solder_mask_min_width": 0.0,
                },
            },
        },
        "meta": {"filename": pcb_path.stem + ".kicad_pro", "version": 1},
    }
    with open(pcb_path.with_suffix(".kicad_pro"), "w") as f:
        json.dump(pro, f, indent=2)


if __name__ == "__main__":
    p = build_pcb()
    postprocess(p)
    write_project(p)
