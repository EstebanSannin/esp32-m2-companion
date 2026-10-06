# ADR 0003 — Status LED: plain LED on IO48

Date: 2026-08-28 · Status: **accepted** (GATE 1, owner)

Plain LED, active-low, series resistor, on GPIO48 (module pin 25). WS2812B-2020
option rejected for v1: extra part (Extended at JLCPCB), timing-sensitive
driver, no functional gain for a heartbeat indicator. IO48 has devkit
precedent (RGB LED on ESP32-S3-DevKitC), is not a strapping pin, and is free
on N8R2/N16R8 (the 1.8 V VDD_SPI caveat applies only to R16V variants,
WROOM-1 datasheet v1.8 Table 3-1 note c).

## Amendment (2026-08-29, owner-caught): side-view LEDs at the card edge

Top-emitting LEDs are useless on an M.2 card in-slot: the top faces away
from the host PCB (downward on Mallow, socket on carrier bottom) and the
bottom faces the host at ~2.5 mm. Replaced with side-view LEDs emitting out
of the LEFT card edge (visible in any orientation, standard on commercial
M.2 cards): D3 green TJ-S1706SW6TGLC2G-A5 (C273616), D4 red
TJ-S1706SW6TGLC2R-A5 (C273612), both Extended, 330R series (C23138 Basic).
Land pattern = 0603 placeholder — verify against the TOGIALED drawing and
emitting-face orientation on the assembly drawing at GATE 3.
An earlier note claiming "the card bottom faces up in the Mallow slot" was
WRONG and is corrected in docs/layout-notes.md.

## Amendment (2026-10-06, owner, v1.0 Rev B): LED assembly orientation + drive

- **v1 was assembled with D3/D4 180° reversed** (dark, reverse-biased). The
  footprint/netlist were right; JLC/LCSC's rotation convention for
  C273616/C273612 differs from the footprint and the flipped placement
  preview was approved by eye. Rev B: CPL rotation = KiCad +180°
  (`hardware/tools/gen_fab.py` `JLC_ROT`), `make fab` stays ORDER BLOCKED
  until every polarized part is checked against JLC's preview
  (`fab/polarity_checklist.md`), and the anode-on-resistor-side rule is
  asserted by `tools/polarity_report.py`.
- Land pattern: the 0603 placeholder above was replaced (2026-08-30) by the
  custom `LED_TJ-S1706_SideView` (1.80 mm c-c, per datasheet); it soldered
  fine on v1. Rev B adds a **silk cathode bar** at pad 1.
- Emit face **confirmed on v1 hardware** (a hand-rotated D4 blinks and is
  visible from the left edge).
- Series resistors: **R3 (green) 100R C22775** (330R under-drove the green
  InGaN part at 3.3 V); R4 (red) stays 330R C23138.
