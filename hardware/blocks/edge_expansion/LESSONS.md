# LESSONS
- 2026-10-07 (GATE V1, self-caught): a shared enable net driving 12 logic
  inputs needs its pull-up sized against the SUM of the inputs' max leakage
  (+ internal pull-downs), not typ: 100k would have kept the bus off forever
  (TMUX1511 IIH ±2 µA ×12 + 12 × 6 MΩ). 10k chosen.
- 2026-10-07 (GATE V1, self-caught): pull-ups for an isolated bus belong on
  the MCU side of the isolation switch, or they leak onto the host's pins.
