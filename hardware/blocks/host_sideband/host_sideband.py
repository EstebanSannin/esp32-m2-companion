"""Host-facing M.2 sidebands, active on every host (ADR 0006 §4,
docs/v2-gate-v1.md §1.3). Voltage-agnostic NMOS cells (SSM6N56FE):
outputs can only pull low (any host pull-up level), the input is an
insulated gate (reads 1.2/1.8/3.3 V hosts, no back-feed when unpowered).

  Q2a: IO42 -> gate (100k pull-down) ; drain -> LED_1_n (pin 10)
  Q2b: IO47 -> gate (100k pull-down) ; drain -> WAKE_ON_WWAN_n (pin 23)
  Q3a: W_DISABLE2_n (pin 26, 1M card pull-up per M.2 spec) -> gate ;
       drain -> IO40 (10k pull-up)  => IO40 LOW = radio allowed (inverted)
  Q3b: unused, gate/source to GND, drain open.
Gate pull-downs keep the outputs off while the ESP32-S3 is in reset
(IO42/IO47: no reset pull, no power-up glitch - datasheet v2.2 T2-1/2-2).
"""

from skidl import Pin

from blocks.common import R_0402, R_0603, SSM6N56FE, subcircuit


@subcircuit
def host_sideband(v3v3, gnd, io42, io47, io40, led_1_n, wake_on_wwan_n,
                  w_disable2_n):
    q2 = SSM6N56FE(ref="Q2")
    q2["G1"] += io42
    q2["D1"] += led_1_n
    q2["S1"] += gnd
    q2["G2"] += io47
    q2["D2"] += wake_on_wwan_n
    q2["S2"] += gnd
    for net, ref in ((io42, "R27"), (io47, "R28")):
        r = R_0402("100k", lcsc="C25741", mpn="0402WGF1003TCE", ref=ref)
        r[1] += net
        r[2] += gnd

    q3 = SSM6N56FE(ref="Q3")
    q3["G1"] += w_disable2_n
    q3["D1"] += io40
    q3["S1"] += gnd
    q3["G2"] += gnd          # spare half: held off
    q3["S2"] += gnd
    q3["D2"].func = Pin.types.NOCONNECT
    q3["D2"].do_erc = False

    r_pu = R_0402("1M", lcsc="C26083", mpn="0402WGF1004TCE", ref="R29")
    r_pu[1] += v3v3
    r_pu[2] += w_disable2_n
    r_d = R_0603("10k", lcsc="C25804", mpn="0603WAF1002T5E", ref="R30")
    r_d[1] += v3v3
    r_d[2] += io40
