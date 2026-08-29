# References — leds
- ADR 0003 (+ 2026-08-29 amendment: side-view at left card edge).
- D3: TOGIALED TJ-S1706SW6TGLC2G-A5 green side-view (LCSC C273616, Extended)
- D4: TOGIALED TJ-S1706SW6TGLC2R-A5 red side-view (LCSC C273612, Extended)
- R3/R4: 330R 0603 (C23138, Basic). Green InGaN Vf(20mA) 2.8–3.4 V → runs
  ~1–2 mA at 3.3 V by design; red ~3.5 mA. Verify brightness at bring-up.
- KiCad Device:LED pin 1 = K, pin 2 = A. Land pattern currently 0603
  placeholder — GATE 3: check against TOGIALED S1706 drawing AND mark the
  emitting-face orientation on the assembly drawing (180° = shines inward).
