"""USB 2.0 ESD protection: USBLC6-2SC6 between edge fingers and MCU.

Pinout: docs/datasheets/usblc6-2sc6.pdf p.1 -
  1 = I/O1, 2 = GND, 3 = I/O2, 4 = I/O2, 5 = VBUS, 6 = I/O1.
Pins 1/6 and 3/4 are internally paired for pass-through routing; the
edge-side signal enters one pin, the MCU-side leaves on its pair.
VBUS is tied to the card +3V3 (self-powered, clamp rail) + 100 nF.

Part: ST USBLC6-2SC6, LCSC C7519, Extended (spec-named part, SPEC 6.3;
no Basic equivalent exists).
"""

from skidl import Part

from blocks.common import C_0603, subcircuit


@subcircuit
def usb_esd(usb_edge_p, usb_edge_n, usb_mcu_p, usb_mcu_n, v3v3, gnd):
    u = Part("Power_Protection", "USBLC6-2SC6", tag="U_ESD",
             footprint="Package_TO_SOT_SMD:SOT-23-6")
    u.fields.update(LCSC="C7519", JLC="Extended", MPN="USBLC6-2SC6 (ST)")
    # Owner decision at GATE 2: ST (C7519) primary, UMW (C2687116) approved
    # second source if ST is out of stock at order time.
    u.fields["LCSC_2nd_source"] = "C2687116 (UMW)"

    u[1] += usb_edge_p   # I/O1 edge side
    u[6] += usb_mcu_p    # I/O1 MCU side
    u[3] += usb_edge_n   # I/O2 edge side
    u[4] += usb_mcu_n    # I/O2 MCU side
    u[5] += v3v3         # VBUS clamp rail
    u[2] += gnd

    c = C_0603("100nF 50V", lcsc="C14663", mpn="CC0603KRX7R9BB104")
    c[1] += v3v3
    c[2] += gnd
