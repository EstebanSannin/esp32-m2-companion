"""esp32-m2-companion top-level design (SPEC v1 + A3 v2.0 Rev A; pinmap per docs/pinmap.md §1-§6).

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

from blocks.edge_expansion.edge_expansion import edge_expansion
from blocks.esp32s3_companion.esp32s3_companion import esp32s3_companion
from blocks.host_sideband.host_sideband import host_sideband
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
    v3v3_m2 = Net("+3V3_M2")     # M.2 3.3V/VBAT pins (host supply)
    v3v3_m2.drive = POWER        # supplied by the host slot
    v3v3_efuse = Net("+3V3_EFUSE")   # eFuse OUT -> ferrite (ADR 0007)
    v3v3_efuse.drive = POWER
    v3v3 = Net("+3V3")           # card rail
    v3v3.drive = POWER

    usbh3_d_p = Net("USBH3_D_P")     # edge side (Mallow net names)
    usbh3_d_n = Net("USBH3_D_N")
    usb_d_p = Net("USB_D_P")         # MCU side of ESD array
    usb_d_n = Net("USB_D_N")

    en = Net("EN")
    io0 = Net("IO0")          # WROOM-1 pin name (strapping pin; BOOT)
    perst_n = Net("PERST_n")
    pcie_1_gpio_5 = Net("PCIE_1_GPIO_5")
    w_disable1_n = Net("W_DISABLE1_n")
    led_status_n = Net("LED_STATUS_n")
    txd0 = Net("TXD0")
    rxd0 = Net("RXD0")
    header_ios = {n: Net(n) for n in
                  ("IO8", "IO9", "IO10", "IO11", "IO12", "IO13", "IO14",
                   "IO21")}

    # v2.0 Rev A edge interface (ADR 0006, docs/carrier-interface.md).
    # EXP index -> (M.2 pin, MCU net = WROOM pin name), docs/pinmap.md §6.2
    exp_map = [(30, "IO39"), (32, "IO41"), (34, "IO1"), (36, "IO2"),
               (40, "IO18"), (59, "IO4"), (60, "IO5"), (61, "IO6"),
               (62, "IO7"), (63, "IO15"), (64, "IO16"), (65, "IO17")]
    exp_mcu = [Net(io) for _, io in exp_map]
    exp_s = [Net(f"EXP_{i}_S") for i in range(12)]      # switch source side
    exp_edge = [Net(f"EXP_{i}") for i in range(12)]     # M.2 edge side
    config_2 = Net("CONFIG_2")
    config_3 = Net("CONFIG_3")
    cfg2_g = Net("CFG2_G")
    cfg3_g = Net("CFG3_G")
    exp_oe = Net("EXP_OE")
    led_1_n = Net("LED_1_n")
    wake_on_wwan_n = Net("WAKE_ON_WWAN_n")
    w_disable2_n = Net("W_DISABLE2_n")
    host_ios = {"IO42": Net("IO42"), "IO47": Net("IO47"),
                "IO40": Net("IO40"), "IO38": exp_oe}   # IO38 = EXP_OE readback
    ovlo = Net("EFUSE_OVLO")
    en_uvlo = Net("EFUSE_EN")
    ilm = Net("EFUSE_ILM")

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
    j1["W_DISABLE1_n"] += w_disable1_n   # BOOT leg restored in rev B (ADR 0002)
    # v2: CONFIG state 6 (21 + 69 to GND), signature sense on 75 + 1
    j1[21] += gnd
    j1[69] += gnd
    j1[75] += config_2
    j1[1] += config_3
    for i, (pin, _) in enumerate(exp_map):
        j1[pin] += exp_edge[i]
    j1[10] += led_1_n
    j1[23] += wake_on_wwan_n
    j1[26] += w_disable2_n

    # --- Blocks ---
    power_3v3(v3v3_m2, v3v3_efuse, v3v3, gnd, ovlo, en_uvlo, ilm,
              tag="blk_power")
    usb_esd(usbh3_d_p, usbh3_d_n, usb_d_p, usb_d_n, v3v3, gnd, tag="blk_usb")
    sideband_recovery(en, io0, perst_n, pcie_1_gpio_5, w_disable1_n,
                      v3v3, gnd, tag="blk_recovery")
    esp32s3_companion(v3v3, gnd, en, io0, usb_d_n, usb_d_p,
                      led_status_n, header_ios, txd0, rxd0, exp_mcu,
                      host_ios, tag="blk_mcu")
    edge_expansion(v3v3, gnd, exp_mcu, exp_edge, exp_s, config_2, config_3,
                   cfg2_g, cfg3_g, exp_oe, tag="blk_expansion")
    host_sideband(v3v3, gnd, host_ios["IO42"], host_ios["IO47"],
                  host_ios["IO40"], led_1_n, wake_on_wwan_n, w_disable2_n,
                  tag="blk_host")
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
