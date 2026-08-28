"""IO header (SPEC 6.6): 12-pin 2.54 mm single row, UNPOPULATED (DNP).

Pin order (silkscreen labels in Phase 2):
  1=3V3 2=GND 3=SDA(IO8) 4=SCL(IO9) 5=TX(IO43) 6=RX(IO44)
  7=CS(IO10) 8=MOSI(IO11) 9=CLK(IO12) 10=MISO(IO13) 11=IO14 12=IO21

I2C pull-up footprints provided, DNP by default (SPEC 6.6).
"""

from skidl import Part

from blocks.common import R_0603, TESTPOINT, subcircuit


@subcircuit
def io_header(v3v3, gnd, ios, txd0, rxd0):
    j = Part("Connector_Generic", "Conn_01x12", ref="J3", tag="J_HDR",
             footprint="Connector_PinHeader_2.54mm:PinHeader_1x12_P2.54mm_Vertical")
    j.fields.update(LCSC="", JLC="DNP", MPN="unpopulated 2.54mm header")
    j.do_not_populate = True

    j[1] += v3v3
    j[2] += gnd
    j[3] += ios["IO8"]
    j[4] += ios["IO9"]
    j[5] += txd0
    j[6] += rxd0
    j[7] += ios["IO10"]
    j[8] += ios["IO11"]
    j[9] += ios["IO12"]
    j[10] += ios["IO13"]
    j[11] += ios["IO14"]
    j[12] += ios["IO21"]

    # Optional I2C pull-ups, DNP (SPEC 6.6)
    for sig, ref in (("IO8", "R5"), ("IO9", "R6")):
        r = R_0603("10k", lcsc="C25804", mpn="0603WAF1002T5E", dnp=True,
                   ref=ref)
        r[1] += v3v3
        r[2] += ios[sig]

    # Rail test points (SPEC 6.7)
    TESTPOINT("TP_3V3", ref="TP5")[1] += v3v3
    TESTPOINT("TP_GND", ref="TP6")[1] += gnd
