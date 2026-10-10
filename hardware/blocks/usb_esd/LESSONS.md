- 2026-08-28 (GATE 2 review): Espressif HDG §1.3.13 wants reserved series-R
  (22/33 R start) + shunt-C footprints near the chip on USB D+/D-. Added as
  0R populated + DNP caps. Cheap respin insurance, especially with a
  gold-finger transition in the path.
- 2026-10-06 (rev B, self-caught): on v1 U1 pin 2 (USBLC6 GND) sat on a B.Cu
  GND island fenced in by the locked D+/D− tracks - no copper path to GND, so
  the ESD array had **no ground return** (USB still worked; protection did
  not). DRC reported it as an "unconnected item" that nobody triaged. Lesson:
  give the TVS GND pin its own via to the reference plane, placed with the
  pre-routed pair, not left to the pour; run tools/gnd_islands.py. Side
  effect: v1 U1 *orientation* is not proven by function either.
- 2026-10-10 (GATE V3, self-caught): a USB leg on an outer layer under a
  fine-pitch part blocks every escape via of that part (through vias need
  all layers). Run the pair on In2 (over the In1 GND plane) and drop into
  the module pads with via-in-pad (6-layer vias are filled + capped).
