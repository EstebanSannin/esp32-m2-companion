"""LEDs (SPEC 6.5/G4, ADR 0003 as amended).

SIDE-VIEW LEDs at the LEFT CARD EDGE, bottom side, emitting out of the
slot gap (-x): on an M.2 card neither face is reliably visible once
inserted (top faces away from the host PCB, bottom faces it at ~2.5 mm),
so top-emitting indicators are useless in-slot. Side-view emission out of
the card edge is visible in any mounting orientation - standard practice
on commercial M.2 cards. Owner-caught at Phase 2 review.

Parts: TOGIALED TJ-S1706SW6T (1.7 x 1.1 mm side-view, 0603-compatible
land pattern - verify against TOGIALED drawing at GATE 3):
  D3 green C273616 (power), D4 red C273612 (status, active-low on IO48).
330R series: green InGaN Vf(20mA) is 2.8-3.4 V, so at 3.3 V it runs at
low current by design (~1-2 mA, still bright: 600 mcd @ 20 mA rating);
red gets ~3.5 mA. Check brightness at bring-up.
LED polarity: KiCad Device:LED pin 1 = K (cathode), pin 2 = A (anode).
"""

from skidl import Part

from blocks.common import R_0603, _bom, _next_tag, subcircuit


def _led_sideview(color, lcsc, mpn, ref):
    p = Part("Device", "LED", value=color, ref=ref, tag=_next_tag("LED"),
             footprint="LED_SMD:LED_0603_1608Metric")
    p.fields["note"] = "SIDE-VIEW - emitting face toward left card edge"
    return _bom(p, lcsc, "Extended", mpn)


@subcircuit
def leds(v3v3, gnd, led_status_n):
    # Power LED: +3V3 -> R -> LED -> GND
    r_pwr = R_0603("330R", lcsc="C23138", mpn="0603WAF3300T5E", ref="R3")
    led_pwr = _led_sideview("green", "C273616", "TJ-S1706SW6TGLC2G-A5", "D3")
    r_pwr[1] += v3v3
    r_pwr[2] += led_pwr[2]   # anode
    led_pwr[1] += gnd        # cathode

    # Status LED: +3V3 -> R -> LED -> IO48 (GPIO low = ON)
    r_st = R_0603("330R", lcsc="C23138", mpn="0603WAF3300T5E", ref="R4")
    led_st = _led_sideview("red", "C273612", "TJ-S1706SW6TGLC2R-A5", "D4")
    r_st[1] += v3v3
    r_st[2] += led_st[2]     # anode
    led_st[1] += led_status_n  # cathode -> GPIO sinks
