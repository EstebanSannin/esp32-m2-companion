# References — leds
- ADR 0003 (+ 2026-08-29 amendment: side-view at left card edge).
- D3: TOGIALED TJ-S1706SW6TGLC2G-A5 green side-view (LCSC C273616, Extended)
- D4: TOGIALED TJ-S1706SW6TGLC2R-A5 red side-view (LCSC C273612, Extended)
- R3 (green): 100R 0603 (C22775, Basic) — ~5 mA nominal (rev B; v1's 330R
  under-drove it). R4 (red): 330R 0603 (C23138, Basic) — ~4.5 mA.
- KiCad Device:LED pin 1 = K, pin 2 = A. **RESOLVED 2026-08-30** against the
  TOGIALED datasheet (`docs/datasheets/togialed_tj-s1706_sideview.pdf`):
  - Land pattern was a 0603 placeholder (1.576 mm c-c) — too tight for the
    1.70 mm body. Replaced with custom `LED_TJ-S1706_SideView` footprint
    (pads 0.80×0.70, **1.80 mm c-c** per datasheet). DRC clean; LED-net
    connectivity preserved (old track ends stay inside the new pads).
  - Polarity confirmed: pin 1 = cathode (black-mark end, diode symbol),
    pin 2 = anode — matches KiCad Device:LED and our netlist.
  - Emit face marked on F.Fab pointing −x (out the left card edge). Caveat:
    the datasheet 2D views do NOT distinguish the two long faces, so the
    front/back emit face is the *intended* direction — **confirmed on v1
    hardware 2026-10-05**.
  - Rev B: silk cathode bar at pad 1; JLC CPL rotation = KiCad +180°
    (v1 was assembled reversed — see ADR 0003 rev-B amendment).
