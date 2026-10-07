"""v2 GATE V3: rip up rev-B routing except the USB pair (ADR 0008:
re-placement, In1 GND / In4 +3V3 planes must be solid; rev B routed signals
on its plane layers). Keeps every track/via of the USB nets. Separate
process (never keep using a board after Remove()).
  $KPY tools/v2_ripup.py
"""
import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "tools"))
PCB = HERE / "kicad" / "esp32_m2_companion.kicad_pcb"
KEEP = {"USBH3_D_P", "USBH3_D_N", "USB_D_P_ESD", "USB_D_N_ESD",
        "USB_D_P", "USB_D_N"}


def main():
    b = pcbnew.LoadBoard(str(PCB))
    gone = kept = 0
    for t in list(b.GetTracks()):
        if t.GetNetname() in KEEP:
            t.SetLocked(True)
            kept += 1
        else:
            b.Remove(t)
            gone += 1
    pcbnew.SaveBoard(str(PCB), b)
    print(f"ripped up {gone} tracks/vias, kept {kept} (USB pair, locked)")


if __name__ == "__main__":
    from kicad_exit import run
    run(main)
