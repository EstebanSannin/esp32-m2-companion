"""IO connectors (SPEC 6.6 as amended by ADR 0005).

Owner decision at GATE 2 follow-up: the 2.54 mm 1x12 header physically
cannot fit a 2242 card with an 18 mm module (30.5 mm > 22 mm card width).
Replaced by two JST SH 1.0 mm side-entry connectors, ASSEMBLED:

  J3 = SH-4, Qwiic / STEMMA-QT standard pinout: 1=GND 2=3V3 3=SDA 4=SCL
       -> off-the-shelf I2C sensor cables just plug in (SPEC success
       criterion 4).
  J4 = SH-8: 1=TX(IO43) 2=RX(IO44) 3=CS(IO10) 4=MOSI(IO11) 5=CLK(IO12)
       6=MISO(IO13) 7=IO14 8=IO21 -> full native FSPI set + UART0 + 2 GPIO.

I2C pull-up footprints 10k DNP (Qwiic peripherals usually carry their own).
Rail test points per SPEC 6.7.
"""

from skidl import Part

from blocks.common import R_0603, TESTPOINT, subcircuit


@subcircuit
def io_header(v3v3, gnd, ios, txd0, rxd0):
    j3 = Part("Connector_Generic", "Conn_01x04", ref="J3", tag="J_QWIIC",
              footprint="Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal")
    j3.fields.update(LCSC="C160404", JLC="Extended",
                     MPN="JST SM04B-SRSS-TB")
    j3.fields["JLC_note"] = "Qwiic I2C port; no Basic 1mm connector exists"
    j3[1] += gnd          # Qwiic order
    j3[2] += v3v3
    j3[3] += ios["IO8"]   # SDA
    j3[4] += ios["IO9"]   # SCL

    j4 = Part("Connector_Generic", "Conn_01x08", ref="J4", tag="J_IO",
              footprint="Connector_JST:JST_SH_SM08B-SRSS-TB_1x08-1MP_P1.00mm_Horizontal")
    j4.fields.update(LCSC="C160407", JLC="Extended",
                     MPN="JST SM08B-SRSS-TB")
    j4.fields["JLC_note"] = "UART/SPI/GPIO port; no Basic 1mm connector exists"
    j4[1] += txd0
    j4[2] += rxd0
    j4[3] += ios["IO10"]  # SPI CS
    j4[4] += ios["IO11"]  # SPI MOSI
    j4[5] += ios["IO12"]  # SPI CLK
    j4[6] += ios["IO13"]  # SPI MISO
    j4[7] += ios["IO14"]
    j4[8] += ios["IO21"]

    # Optional I2C pull-ups, DNP (SPEC 6.6)
    for sig, ref in (("IO8", "R5"), ("IO9", "R6")):
        r = R_0603("10k", lcsc="C25804", mpn="0603WAF1002T5E", dnp=True,
                   ref=ref)
        r[1] += v3v3
        r[2] += ios[sig]

    # Rail test points (SPEC 6.7)
    TESTPOINT("TP_3V3", ref="TP5")[1] += v3v3
    TESTPOINT("TP_GND", ref="TP6")[1] += gnd
