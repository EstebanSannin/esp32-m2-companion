"""Host-controlled recovery: Schottky-isolated EN/BOOT sidebands (ADR 0002).

Any host can only PULL LOW through the diodes; card nets idle at 3.3 V via
on-card pull-ups. Unconnected sidebands mean normal boot (SPEC 6.4).
CONSTRAINT (GATE 2 review): hosts must idle sidebands open-drain/Hi-Z (or
push-pull with VOH >= ~2.8 V). A push-pull HIGH below that (e.g. 1.8 V)
forward-biases the diode and drags the net to ~2.0-2.1 V = undefined input.
Recovery flows RELEASE BOOT/EN to Hi-Z, never drive high.

  EN   <- A|<K- M.2 pin 50 PERST_n      (Mallow: SODIMM 244)
  IO0  <- A|<K- M.2 pin 20 PCIE_1_GPIO_5 (Mallow: X16.19 jumper)

M.2 pin 8 (W_DISABLE1_n) BOOT leg DROPPED in v1 (ADR 0002 amendment
2026-08-30): its corner was unroutable in this placement, and it is
redundant - BOOT (IO0) is exposed on TP2, so any non-Mallow host recovers by
flying-lead on TP1(EN)+TP2(BOOT). D2's second cathode (pin 2) is left NC; the
edge finger (J1 pin 8) is an exposed but unconnected pad. See
docs/decisions/0002 and docs/review-findings.md.

BAT54A: pin 3 = common anode, pins 1/2 = cathodes
(docs/datasheets/lbat54a_schottky.pdf p.1).
EN RC per Espressif HDG §1.3.3: R = 10 k, C = 1 uF.
"""

from skidl import Pin

from blocks.common import BAT54A, C_0603, R_0603, TESTPOINT, subcircuit


@subcircuit
def sideband_recovery(en, io0_boot, perst_n, pcie_1_gpio_5, v3v3, gnd):
    # EN: pull-up + RC delay + diode from PERST#
    r_en = R_0603("10k", lcsc="C25804", mpn="0603WAF1002T5E", ref="R1")
    r_en[1] += v3v3
    r_en[2] += en
    c_en = C_0603("1uF 50V", lcsc="C15849", mpn="CL10A105KB8NNNC", ref="C5")
    c_en[1] += en
    c_en[2] += gnd

    d_en = BAT54A(ref="D1")
    d_en[3] += en          # common anode
    d_en[1] += perst_n     # cathode -> host may pull low
    d_en[2].func = Pin.types.NOCONNECT   # second cathode deliberately unused
    d_en[2].do_erc = False

    # BOOT (IO0): pull-up + single diode from pin 20 (Mallow path).
    # Pin-8 (W_DISABLE1_n) leg dropped in v1 - see module docstring.
    r_boot = R_0603("10k", lcsc="C25804", mpn="0603WAF1002T5E", ref="R2")
    r_boot[1] += v3v3
    r_boot[2] += io0_boot

    d_boot = BAT54A(ref="D2")
    d_boot[3] += io0_boot        # common anode
    d_boot[1] += pcie_1_gpio_5   # Mallow path
    d_boot[2].func = Pin.types.NOCONNECT   # pin-8 leg dropped (v1)
    d_boot[2].do_erc = False

    # Test points (SPEC 6.7)
    TESTPOINT("TP_EN", ref="TP1")[1] += en
    TESTPOINT("TP_BOOT", ref="TP2")[1] += io0_boot
