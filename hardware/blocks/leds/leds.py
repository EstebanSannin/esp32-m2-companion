"""LEDs (SPEC 6.5/G4, ADR 0003 as amended).

SIDE-VIEW LEDs at the LEFT CARD EDGE, bottom side, emitting out of the
slot gap (-x): on an M.2 card neither face is reliably visible once
inserted (top faces away from the host PCB, bottom faces it at ~2.5 mm),
so top-emitting indicators are useless in-slot. Side-view emission out of
the card edge is visible in any mounting orientation - standard practice
on commercial M.2 cards. Owner-caught at Phase 2 review.

Parts: TOGIALED TJ-S1706SW6T side-view LED (body 1.70 x 0.60 x 1.10 mm):
  D3 green C273616 (power), D4 red C273612 (status, active-low on IO48).
Series R (rev B): green InGaN Vf(20mA) is 2.8-3.4 V, leaving only
~0.3-0.6 V headroom at 3.3 V. v1's 330R ran it ~1.8 mA nominal /
~0.5 mA worst case (rail 3.06 V) - visibly dim. R3 = 100R (C22775, Basic):
~5 mA nominal, ~1-7 mA across Vf bin + rail spread (abs max 30 mA), close
to the red LED's ~4.5 mA on R4 = 330R so the two look similar. Brightness
spread is set by the Vf bin, not the resistor - headroom is the limit.

Footprint: custom LED_TJ-S1706_SideView (hardware/kicad/footprints.pretty),
pads 0.80x0.70, 1.80 mm centre-to-centre, per the datasheet land pattern
(docs/datasheets/togialed_tj-s1706_sideview.pdf). The generic 0603 land
(1.576 mm c-c) it replaced was too tight for the 1.70 mm body.
Pin 1 = K (cathode, black-mark end), pin 2 = A (anode), as KiCad Device:LED.
v2.0 Rev A FIX (GATE V3 amendment, 2026-10-13): the footprint pads are
RENUMBERED to match the physical part. JLC engineering (Rev B final DFM,
physical parts on tape) found that with the lens toward the card edge the
cathode sits where the rev-B footprint had the anode: v1 (CPL +0) = lens
out, polarity reversed (dark); Rev B (CPL +180) = polarity right, lens
inward. The v1 note "rotation restores polarity AND emit direction" was an
unverified inference. Now: cathode = pad at +x of the footprint when the
emit arrow (F.Fab, +y) points out of the card edge; R3/R4 rotated 180 so
their LED-side pad stays level with the new anode pad; CPL +0. Confirm BOTH
polarity and lens direction in JLC's final DFM (fab/polarity_checklist.md).
Silk bar = cathode end.
"""

from skidl import Net, Part

from blocks.common import R_0603, _bom, _next_tag, subcircuit


def _led_sideview(color, lcsc, mpn, ref):
    p = Part("Device", "LED", value=color, ref=ref, tag=_next_tag("LED"),
             footprint="esp32_m2_companion:LED_TJ-S1706_SideView")
    p.fields["note"] = ("SIDE-VIEW - emitting face toward the left card edge; "
                        "footprint renumbered v2 (lens + polarity together)")
    return _bom(p, lcsc, "Extended", mpn)


@subcircuit
def leds(v3v3, gnd, led_status_n):
    # Power LED: +3V3 -> R -> LED -> GND
    r_pwr = R_0603("100R", lcsc="C22775", mpn="0603WAF1000T5E", ref="R3")
    led_pwr = _led_sideview("green", "C273616", "TJ-S1706SW6TGLC2G-A5", "D3")
    led_pwr_a = Net("LED_PWR_A")      # named (rev B: was SKiDL auto "N$1")
    r_pwr[1] += v3v3
    r_pwr[2] += led_pwr_a
    led_pwr[2] += led_pwr_a  # anode
    led_pwr[1] += gnd        # cathode

    # Status LED: +3V3 -> R -> LED -> IO48 (GPIO low = ON)
    r_st = R_0603("330R", lcsc="C23138", mpn="0603WAF3300T5E", ref="R4")
    led_st = _led_sideview("red", "C273612", "TJ-S1706SW6TGLC2R-A5", "D4")
    led_status_a = Net("LED_STATUS_A")  # named (rev B: was SKiDL auto "N$2")
    r_st[1] += v3v3
    r_st[2] += led_status_a
    led_st[2] += led_status_a  # anode
    led_st[1] += led_status_n  # cathode -> GPIO sinks
