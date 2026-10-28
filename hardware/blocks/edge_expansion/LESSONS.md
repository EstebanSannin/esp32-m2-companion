# LESSONS
- 2026-10-07 (GATE V1, self-caught): a shared enable net driving 12 logic
  inputs needs its pull-up sized against the SUM of the inputs' max leakage
  (+ internal pull-downs), not typ: 100k would have kept the bus off forever
  (TMUX1511 IIH ±2 µA ×12 + 12 × 6 MΩ). 10k chosen.
- 2026-10-07 (GATE V1, self-caught): pull-ups for an isolated bus belong on
  the MCU side of the isolation switch, or they leak onto the host's pins.
- 2026-10-10 (GATE V3): 0.4 mm-pitch escapes were sealed by the 0.25 mm
  hole-to-copper margin, not by via pad size; JLC's 0.2 mm (inner layers)
  plus 0.35/0.2 vias opened them. The 12 EXP edge nets end at 7 consecutive
  fingers (59-65) at 0.25 mm F/B pitch: fix 2-3 fan-ins by hand first.
- 2026-10-28 (v2 RC1 review contract_test-1): an enable RC
  that is FASTER than the MCU's EN RC (10 ms vs 13.9 ms to VIH_nRST) turns
  the bus on while the MCU is still in reset/ROM boot, so its power-up
  glitches reach the far side; and an enable that ignores EN stays on
  through every later reset. Compute both time constants against the
  reset release, and gate the enable with an MCU-reset-safe consent
  signal (fixed with Q3b/IO38 in host_sideband: bus ON = carrier AND
  firmware).
- 2026-10-28 (v2 RC1 review expansion-1): a 1 MΩ "carrier detect" pull-up
  cannot tell a carrier's GND from a host load of a few hundred kΩ to GND;
  "host pull-up or floating keeps it off" is not the same as "host-safe".
