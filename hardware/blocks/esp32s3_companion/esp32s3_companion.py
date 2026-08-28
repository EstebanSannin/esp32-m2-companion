"""ESP32-S3-WROOM-1-N8R2 module block.

Pin numbers/names: esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf v1.8
Table 3-1 (pp. 11-12); strapping: §4. Runtime asserts verify the KiCad
symbol's pin names against the datasheet numbers on every build.

Variant policy (docs/pinmap.md §2): IO35-37 kept NC so N8R2 (quad PSRAM)
and N16R8 (octal) are drop-in interchangeable. Strapping pins IO3/IO45/
IO46 left floating (datasheet defaults give SPI boot, 3.3 V VDD_SPI).
Decoupling per HDG: 10 uF + 100 nF at the module 3V3 pin.
"""

from skidl import Part, Pin

from blocks.common import C_0603, TESTPOINT, subcircuit

# (module pin number, expected KiCad symbol pin name) - datasheet Table 3-1
_DATASHEET_PINS = {
    # 13/14: KiCad symbol uses the datasheet's bold default function names
    # (USB_D-/USB_D+) for IO19/IO20 - same pins per Table 3-1.
    3: "EN", 13: "USB_D-", 14: "USB_D+", 27: "IO0", 25: "IO48",
    12: "IO8", 17: "IO9", 18: "IO10", 19: "IO11", 20: "IO12",
    21: "IO13", 22: "IO14", 23: "IO21", 36: "RXD0", 37: "TXD0",
}


@subcircuit
def esp32s3_companion(v3v3, gnd, en, io0_boot, usb_d_n, usb_d_p,
                      led_status_n, header_ios, txd0, rxd0):
    """header_ios: dict {'IO8':net, 'IO9':net, 'IO10':..., 'IO14', 'IO21'}"""
    u = Part("RF_Module", "ESP32-S3-WROOM-1", ref="U2", tag="U_MCU",
             footprint="esp32m2:ESP32-S3-WROOM-1_JLC")  # vendored: EPAD vias 0.3mm drill (JLC min)
    u.fields.update(
        LCSC="C2913204", JLC="Extended", MPN="ESP32-S3-WROOM-1-N8R2")
    u.fields["JLC_note"] = "core MCU module; no Basic alternative exists"

    # Traceability check: KiCad symbol pin names must match datasheet
    for num, name in _DATASHEET_PINS.items():
        actual = u[num].name
        assert actual == name, (
            f"symbol/datasheet mismatch on module pin {num}: "
            f"symbol={actual!r} datasheet={name!r}")

    # Power (pins 1/2/40/41 = GND,3V3,GND,EPAD per Table 3-1)
    u[2] += v3v3
    u[1] += gnd
    u[40] += gnd
    u[41] += gnd  # EPAD
    c1 = C_0603("100nF 50V", lcsc="C14663", mpn="CC0603KRX7R9BB104", ref="C6")
    c1[1] += v3v3
    c1[2] += gnd
    c2 = C_0603("10uF 10V", lcsc="C19702", mpn="CL10A106KP8NNNC", ref="C7")
    c2[1] += v3v3
    c2[2] += gnd

    # Control / USB
    u[3] += en          # EN (CHIP_PU)
    u[27] += io0_boot   # IO0 strapping (boot)
    u[13] += usb_d_n    # IO19 USB_D-
    u[14] += usb_d_p    # IO20 USB_D+

    # Status LED (active low) on IO48
    u[25] += led_status_n

    # IO header nets
    u[12] += header_ios["IO8"]    # I2C SDA
    u[17] += header_ios["IO9"]    # I2C SCL
    u[18] += header_ios["IO10"]   # FSPICS0
    u[19] += header_ios["IO11"]   # FSPID
    u[20] += header_ios["IO12"]   # FSPICLK
    u[21] += header_ios["IO13"]   # FSPIQ
    u[22] += header_ios["IO14"]
    u[23] += header_ios["IO21"]

    # UART0 (doubles as ROM console fallback)
    u[37] += txd0
    u[36] += rxd0
    TESTPOINT("TP_TXD0", ref="TP3")[1] += txd0
    TESTPOINT("TP_RXD0", ref="TP4")[1] += rxd0

    # Everything else deliberately unconnected in v1:
    # strapping IO3(15)/IO45(26)/IO46(16) float per datasheet §4 defaults;
    # IO35-37 (28-30) reserved for octal-PSRAM variants; spares NC.
    for pin in (4, 5, 6, 7, 8, 9, 10, 11, 15, 16, 24, 26,
                28, 29, 30, 31, 32, 33, 34, 35, 38, 39):
        u[pin].func = Pin.types.NOCONNECT
        u[pin].do_erc = False
