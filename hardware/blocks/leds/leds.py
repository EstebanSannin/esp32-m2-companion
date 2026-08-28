"""LEDs (SPEC 6.2 / 6.5, ADR 0003).

Power LED: green 0805, always on from +3V3.
Status LED: red 0603, active-low on a module GPIO (MCU sinks current).
1 k series -> ~1.3 mA: dim-but-visible indicator, low rail load. Note for
bring-up: swap to lower R if too dim (finding goes to LESSONS.md).

LED polarity: KiCad Device:LED pin 1 = K (cathode), pin 2 = A (anode).
"""

from blocks.common import LED_0603, LED_0805, R_0603, subcircuit


@subcircuit
def leds(v3v3, gnd, led_status_n):
    # Power LED: +3V3 -> R -> LED -> GND
    r_pwr = R_0603("1k", lcsc="C21190", mpn="0603WAF1001T5E", ref="R3")
    led_pwr = LED_0805("green", lcsc="C2297", mpn="KT-0805G", ref="D3")
    r_pwr[1] += v3v3
    r_pwr[2] += led_pwr[2]   # anode
    led_pwr[1] += gnd        # cathode

    # Status LED: +3V3 -> R -> LED -> IO48 (GPIO low = ON)
    r_st = R_0603("1k", lcsc="C21190", mpn="0603WAF1001T5E", ref="R4")
    led_st = LED_0603("red", lcsc="C2286", mpn="KT-0603R", ref="D4")
    r_st[1] += v3v3
    r_st[2] += led_st[2]     # anode
    led_st[1] += led_status_n  # cathode -> GPIO sinks
