"""v2 GATE V3: named rule areas (no tracks, no vias; copper pour allowed)
that protect pour paths the router would otherwise cut. Idempotent: an area
whose name already exists is left as is.

  FGAP_* (F.Cu, also no pour; RC1 review layout-3): the 0.16 mm gaps
  between adjacent GND fingers 73/71, 71/69 and 5/3. The GND_top pour
  bridged them (fingers must have no copper between them); with these the
  pour still reaches each finger, from its top edge only.

  GND11_STRIP / GND11_BAND (F.Cu): GND finger 11 sits between the B-key notch
  and the USBH3_D_N F run; its only connection to the GND pour is F copper
  up this strip and left over the notch top (y <= 146.2 = notch top 146.5 -
  0.3 edge clearance). Without it finger 11 is floating on the card side.
  $KPY tools/v2_keepouts.py
"""
import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "tools"))
PCB = HERE / "kicad" / "esp32_m2_companion.kicad_pcb"

AREAS = [
    ("GND11_STRIP", "F.Cu", (106.45, 145.95, 107.05, 147.45)),
    ("GND11_BAND", "F.Cu", (104.95, 145.95, 106.50, 146.20)),
    ("FGAP_73_71", "F.Cu", (91.42, 147.5, 91.58, 150.3), "no_pour"),
    ("FGAP_71_69", "F.Cu", (91.92, 147.5, 92.08, 150.3), "no_pour"),
    ("FGAP_5_3", "F.Cu", (108.42, 147.5, 108.58, 150.3), "no_pour"),
]


def main():
    b = pcbnew.LoadBoard(str(PCB))
    mm = pcbnew.FromMM
    have = {z.GetZoneName() for z in b.Zones()}
    for name, lname, (x0, y0, x1, y1), *opt in AREAS:
        if name in have:
            print(f"{name}: exists")
            continue
        z = pcbnew.ZONE(b)
        z.SetIsRuleArea(True)
        z.SetZoneName(name)
        z.SetLayer(b.GetLayerID(lname))
        z.SetDoNotAllowTracks(True)
        z.SetDoNotAllowVias(True)
        z.SetDoNotAllowPads(False)
        z.SetDoNotAllowFootprints(False)
        z.SetDoNotAllowCopperPour("no_pour" in opt)
        ol = z.Outline()
        ol.NewOutline()
        for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
            ol.Append(mm(x), mm(y))
        b.Add(z)
        print(f"{name}: added on {lname} {x0},{y0} - {x1},{y1}")
    pcbnew.SaveBoard(str(PCB), b)


if __name__ == "__main__":
    from kicad_exit import run
    run(main)
