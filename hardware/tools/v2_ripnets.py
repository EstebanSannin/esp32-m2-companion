"""Hand-finish helper: remove all tracks/vias of the named nets (separate
process - never keep using a board after Remove()). Refuses the USB nets.
  $KPY tools/v2_ripnets.py NET1,NET2,...
"""
import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "tools"))
PCB = HERE / "kicad" / "esp32_m2_companion.kicad_pcb"
PROTECTED = {"USBH3_D_P", "USBH3_D_N", "USB_D_P_ESD", "USB_D_N_ESD", "USB_D_P", "USB_D_N"}


def main():
    nets = set(sys.argv[1].split(","))
    if "--force-usb" not in sys.argv:
        assert not (nets & PROTECTED), "refusing to rip the hand-routed USB pair"
    b = pcbnew.LoadBoard(str(PCB))
    n = 0
    for t in list(b.GetTracks()):
        if t.GetNetname() in nets:
            b.Remove(t)
            n += 1
    pcbnew.SaveBoard(str(PCB), b)
    print(f"ripped {n} items of {sorted(nets)}")


if __name__ == "__main__":
    from kicad_exit import run
    run(main)
