"""Per-block schematic-style SVG renders -> one merged review PDF.

Whole-board netlistsvg output is unreadable (15 parts, power rails
everywhere); one page per SPEC §12 block reviews far better. Whole-board
connectivity is reviewed via the netlist + docs/pinmap.md.

Run: uv run python tools/gen_svg.py   (or `make svg`)
"""

import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent.parent
sys.path.insert(0, str(HERE))

_KICAD_SUPPORT = os.path.expanduser(
    "~/Applications/KiCad/KiCad.app/Contents/SharedSupport")
os.environ.setdefault("KICAD9_SYMBOL_DIR", f"{_KICAD_SUPPORT}/symbols")

import skidl
from skidl import KICAD9, Net, generate_svg, reset, set_default_tool

set_default_tool(KICAD9)

OUT = HERE / "build" / "svg"


def _nets(*names):
    nets = {}
    for n in names:
        net = Net(n)
        net.netio = "i"   # render as labeled I/O port in the block SVG
        nets[n] = net
    return nets


def blk_power_3v3():
    from blocks.power_3v3.power_3v3 import power_3v3
    n = _nets("+3V3_M2", "+3V3", "GND")
    power_3v3(n["+3V3_M2"], n["+3V3"], n["GND"], tag="blk")


def blk_usb_esd():
    from blocks.usb_esd.usb_esd import usb_esd
    n = _nets("USBH3_D_P", "USBH3_D_N", "USB_D_P", "USB_D_N", "+3V3", "GND")
    usb_esd(n["USBH3_D_P"], n["USBH3_D_N"], n["USB_D_P"], n["USB_D_N"],
            n["+3V3"], n["GND"], tag="blk")


def blk_sideband_recovery():
    from blocks.sideband_recovery.sideband_recovery import sideband_recovery
    n = _nets("EN", "IO0_BOOT", "PERST_n", "PCIE_1_GPIO_5", "W_DISABLE1_n",
              "+3V3", "GND")
    sideband_recovery(n["EN"], n["IO0_BOOT"], n["PERST_n"],
                      n["PCIE_1_GPIO_5"], n["W_DISABLE1_n"],
                      n["+3V3"], n["GND"], tag="blk")


def blk_esp32s3_companion():
    from blocks.esp32s3_companion.esp32s3_companion import esp32s3_companion
    ios = _nets("IO8", "IO9", "IO10", "IO11", "IO12", "IO13", "IO14", "IO21")
    n = _nets("+3V3", "GND", "EN", "IO0_BOOT", "USB_D_N", "USB_D_P",
              "LED_STATUS_n", "TXD0", "RXD0")
    esp32s3_companion(n["+3V3"], n["GND"], n["EN"], n["IO0_BOOT"],
                      n["USB_D_N"], n["USB_D_P"], n["LED_STATUS_n"], ios,
                      n["TXD0"], n["RXD0"], tag="blk")


def blk_leds():
    from blocks.leds.leds import leds
    n = _nets("+3V3", "GND", "LED_STATUS_n")
    leds(n["+3V3"], n["GND"], n["LED_STATUS_n"], tag="blk")


def blk_io_header():
    from blocks.io_header.io_header import io_header
    ios = _nets("IO8", "IO9", "IO10", "IO11", "IO12", "IO13", "IO14", "IO21")
    n = _nets("+3V3", "GND", "TXD0", "RXD0")
    io_header(n["+3V3"], n["GND"], ios, n["TXD0"], n["RXD0"], tag="blk")


def blk_m2_keyb_edge():
    from blocks.m2_keyb_edge.m2_keyb_edge import m2_keyb_edge_template
    j1 = m2_keyb_edge_template()(tag="J_M2")  # pragma: no cover (excluded)
    j1.ref = "J1"
    n = _nets("+3V3_M2", "GND", "USBH3_D_P", "USBH3_D_N", "PERST_n",
              "PCIE_1_GPIO_5", "W_DISABLE1_n")
    for p in j1.pins:
        if p.name == "VCC_3V3":
            p += n["+3V3_M2"]
        elif p.name == "GND":
            p += n["GND"]
    for sig in ("USBH3_D_P", "USBH3_D_N", "PERST_n", "PCIE_1_GPIO_5",
                "W_DISABLE1_n"):
        j1[sig] += n[sig]


# m2_keyb_edge excluded: netlistsvg's layouter fails on the 75-pin part and
# the block is a bare connector - docs/pinmap.md §1 IS its schematic.
BLOCKS = [
    ("power_3v3", blk_power_3v3),
    ("usb_esd", blk_usb_esd),
    ("sideband_recovery", blk_sideband_recovery),
    ("esp32s3_companion", blk_esp32s3_companion),
    ("leds", blk_leds),
    ("io_header", blk_io_header),
]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    pdfs = []
    # Phase 1: emit all SVGs (skidl launches netlistsvg asynchronously)
    for name, fn in BLOCKS:
        reset()
        set_default_tool(KICAD9)
        fn()
        generate_svg(file_=str(OUT / name))

    # Phase 2: wait for the async netlistsvg processes, then convert
    import time
    failed = []
    for name, _ in BLOCKS:
        svg = OUT / f"{name}.svg"
        for _try in range(60):
            if svg.exists() and svg.stat().st_size > 0:
                break
            time.sleep(0.5)
        try:
            pdf = OUT / f"{name}.pdf"
            subprocess.run(["rsvg-convert", "-f", "pdf", "-o", str(pdf),
                            str(svg)], check=True)
            pdfs.append(pdf)
            print("rendered", name)
        except Exception as exc:
            failed.append(name)
            print(f"RENDER FAILED for {name}: {exc}")
    # merge
    from pypdf import PdfWriter
    w = PdfWriter()
    for p in pdfs:
        w.append(str(p))
    merged = HERE / "build" / "esp32_m2_companion_blocks.pdf"
    with open(merged, "wb") as f:
        w.write(f)
    print("merged review PDF:", merged)


if __name__ == "__main__":
    main()
