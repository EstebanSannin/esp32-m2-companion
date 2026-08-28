"""USB 2.0 ESD protection: USBLC6-2SC6 between edge fingers and MCU.

Pinout: docs/datasheets/usblc6-2sc6.pdf p.1 -
  1 = I/O1, 2 = GND, 3 = I/O2, 4 = I/O2, 5 = VBUS, 6 = I/O1.
Pins 1/6 and 3/4 are internally paired for pass-through routing; the
edge-side signal enters one pin, the MCU-side leaves on its pair.
VBUS is tied to the card +3V3 (self-powered, clamp rail) + 100 nF.

Part: ST USBLC6-2SC6, LCSC C7519, Extended (spec-named part, SPEC 6.3;
no Basic equivalent exists).

GATE 2 review addition (HDG §1.3.13): series resistors on D+/D- close to
the module (populated 0R; swap to 22-33R for SI tuning) and shunt-C
footprints to GND (DNP) - tuning provision without a respin.
"""

from skidl import Net, Part

from blocks.common import C_0603, R_0603, subcircuit


@subcircuit
def usb_esd(usb_edge_p, usb_edge_n, usb_mcu_p, usb_mcu_n, v3v3, gnd):
    u = Part("Power_Protection", "USBLC6-2SC6", ref="U1", tag="U_ESD",
             footprint="Package_TO_SOT_SMD:SOT-23-6")
    u.fields.update(LCSC="C7519", JLC="Extended", MPN="USBLC6-2SC6 (ST)")
    # Owner decision at GATE 2: ST (C7519) primary, UMW (C2687116) approved
    # second source if ST is out of stock at order time.
    u.fields["LCSC_2nd_source"] = "C2687116 (UMW)"

    usb_p_esd = Net("USB_D_P_ESD")   # between ESD array and series R
    usb_n_esd = Net("USB_D_N_ESD")

    u[1] += usb_edge_p   # I/O1 edge side
    u[6] += usb_p_esd    # I/O1 MCU side
    u[3] += usb_edge_n   # I/O2 edge side
    u[4] += usb_n_esd    # I/O2 MCU side
    u[5] += v3v3         # VBUS clamp rail
    u[2] += gnd

    # Series elements (0R default; SI tuning per HDG). Explicit refs so
    # adding them does not renumber existing parts.
    r_p = R_0603("0R", lcsc="C21189", mpn="0603WAF0000T5E")
    r_p.ref = "R7"
    r_n = R_0603("0R", lcsc="C21189", mpn="0603WAF0000T5E")
    r_n.ref = "R8"
    r_p[1] += usb_p_esd
    r_p[2] += usb_mcu_p
    r_n[1] += usb_n_esd
    r_n[2] += usb_mcu_n

    # Shunt-C footprints, DNP (HDG: "initially unpopulated")
    for ref, net in (("C8", usb_mcu_p), ("C9", usb_mcu_n)):
        cs = C_0603("SI-tune", lcsc="", mpn="DNP - SI tuning provision")
        cs.ref = ref
        cs.fields["DNP"] = "DNP"
        cs.do_not_populate = True
        cs[1] += net
        cs[2] += gnd

    c = C_0603("100nF 50V", lcsc="C14663", mpn="CC0603KRX7R9BB104", ref="C4")
    c[1] += v3v3
    c[2] += gnd
