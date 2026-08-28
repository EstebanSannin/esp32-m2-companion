"""Host-controlled recovery: Schottky-isolated EN/BOOT sidebands (ADR 0002).

Any host can only PULL LOW through the diodes; card nets idle at 3.3 V via
on-card pull-ups, so 1.8 V hosts (Verdin) never see the card rail and an
unconnected sideband means normal boot (SPEC 6.4).

  EN   <- A|<K- M.2 pin 50 PERST_n      (Mallow: SODIMM 244)
  IO0  <- A|<K- M.2 pin 20 PCIE_1_GPIO_5 (Mallow: X16.19 jumper)
       <- A|<K- M.2 pin 8  W_DISABLE1_n  (non-Mallow hosts)

BAT54A: pin 3 = common anode, pins 1/2 = cathodes
(docs/datasheets/lbat54a_schottky.pdf p.1).
EN RC per Espressif HDG §1.3.3: R = 10 k, C = 1 uF.
"""

from skidl import Pin

from blocks.common import BAT54A, C_0603, R_0603, TESTPOINT, subcircuit


@subcircuit
def sideband_recovery(en, io0_boot, perst_n, pcie_1_gpio_5, w_disable1_n,
                      v3v3, gnd):
    # EN: pull-up + RC delay + diode from PERST#
    r_en = R_0603("10k", lcsc="C25804", mpn="0603WAF1002T5E")
    r_en[1] += v3v3
    r_en[2] += en
    c_en = C_0603("1uF 25V", lcsc="C15849", mpn="CL10A105KB8NNNC")
    c_en[1] += en
    c_en[2] += gnd

    d_en = BAT54A()
    d_en[3] += en          # common anode
    d_en[1] += perst_n     # cathode -> host may pull low
    d_en[2].func = Pin.types.NOCONNECT   # second cathode deliberately unused
    d_en[2].do_erc = False

    # BOOT (IO0): pull-up + diode-OR from pin 20 and pin 8
    r_boot = R_0603("10k", lcsc="C25804", mpn="0603WAF1002T5E")
    r_boot[1] += v3v3
    r_boot[2] += io0_boot

    d_boot = BAT54A()
    d_boot[3] += io0_boot        # common anode
    d_boot[1] += pcie_1_gpio_5   # Mallow path
    d_boot[2] += w_disable1_n    # generic-host path

    # Test points (SPEC 6.7)
    TESTPOINT("TP_EN")[1] += en
    TESTPOINT("TP_BOOT")[1] += io0_boot
