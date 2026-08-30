"""esp32-m2-companion top-level design (SPEC v1, pinmap per docs/pinmap.md).

Build: `uv run python design.py` (or `make check` from repo root).
Outputs in hardware/build/: ERC log, KiCad netlist, XML netlist, BOM.
"""

import os
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

# KiCad 9 libraries (docs/environment.md)
_KICAD_SUPPORT = os.path.expanduser(
    "~/Applications/KiCad/KiCad.app/Contents/SharedSupport")
os.environ.setdefault("KICAD9_SYMBOL_DIR", f"{_KICAD_SUPPORT}/symbols")
os.environ.setdefault("KICAD9_FOOTPRINT_DIR", f"{_KICAD_SUPPORT}/footprints")

from skidl import (ERC, KICAD9, Net, POWER, generate_netlist, generate_xml,
                   set_default_tool)

set_default_tool(KICAD9)

from blocks.esp32s3_companion.esp32s3_companion import esp32s3_companion
from blocks.io_header.io_header import io_header
from blocks.leds.leds import leds
from blocks.m2_keyb_edge.m2_keyb_edge import m2_keyb_edge_template
from blocks.power_3v3.power_3v3 import power_3v3
from blocks.sideband_recovery.sideband_recovery import sideband_recovery
from blocks.usb_esd.usb_esd import usb_esd


def build():
    # --- Nets (names per CLAUDE.md conventions) ---
    gnd = Net("GND")
    gnd.drive = POWER
    v3v3_m2 = Net("+3V3_M2")     # edge side of the ferrite bead
    v3v3_m2.drive = POWER        # supplied by the host slot
    v3v3 = Net("+3V3")           # card rail
    v3v3.drive = POWER

    usbh3_d_p = Net("USBH3_D_P")     # edge side (Mallow net names)
    usbh3_d_n = Net("USBH3_D_N")
    usb_d_p = Net("USB_D_P")         # MCU side of ESD array
    usb_d_n = Net("USB_D_N")

    en = Net("EN")
    io0_boot = Net("IO0_BOOT")
    perst_n = Net("PERST_n")
    pcie_1_gpio_5 = Net("PCIE_1_GPIO_5")
    led_status_n = Net("LED_STATUS_n")
    txd0 = Net("TXD0")
    rxd0 = Net("RXD0")
    header_ios = {n: Net(n) for n in
                  ("IO8", "IO9", "IO10", "IO11", "IO12", "IO13", "IO14",
                   "IO21")}

    # --- M.2 edge fingers (J1) ---
    j1 = m2_keyb_edge_template()(tag="J_M2")
    j1.ref = "J1"
    for p in j1.pins:
        if p.name == "VCC_3V3":
            p += v3v3_m2
        elif p.name == "GND":
            p += gnd
    j1["USBH3_D_P"] += usbh3_d_p
    j1["USBH3_D_N"] += usbh3_d_n
    j1["PERST_n"] += perst_n
    j1["PCIE_1_GPIO_5"] += pcie_1_gpio_5
    # M.2 pin 8 (W_DISABLE1_n) BOOT leg dropped in v1 (ADR 0002 amendment):
    # exposed edge finger, no on-card connection. Recovery on non-Mallow
    # hosts is via TP1(EN)+TP2(BOOT) flying leads.
    j1["W_DISABLE1_n"].do_erc = False

    # --- Blocks ---
    power_3v3(v3v3_m2, v3v3, gnd, tag="blk_power")
    usb_esd(usbh3_d_p, usbh3_d_n, usb_d_p, usb_d_n, v3v3, gnd, tag="blk_usb")
    sideband_recovery(en, io0_boot, perst_n, pcie_1_gpio_5,
                      v3v3, gnd, tag="blk_recovery")
    esp32s3_companion(v3v3, gnd, en, io0_boot, usb_d_n, usb_d_p,
                      led_status_n, header_ios, txd0, rxd0, tag="blk_mcu")
    leds(v3v3, gnd, led_status_n, tag="blk_leds")
    io_header(v3v3, gnd, header_ios, txd0, rxd0, tag="blk_header")


def main():
    build()
    out = HERE / "build"
    out.mkdir(exist_ok=True)
    ERC()
    generate_netlist(file_=str(out / "esp32_m2_companion.net"))
    generate_xml(file_=str(out / "esp32_m2_companion.xml"))
    from tools.gen_bom import write_bom
    write_bom(out)
    print("build outputs in", out)


if __name__ == "__main__":
    main()
