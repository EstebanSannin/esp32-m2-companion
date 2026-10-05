- 2026-08-28 (GATE 2 review): diode isolation only blocks toward Hi-Z/OD
  hosts. Push-pull HIGH below ~2.8 V forward-biases the diode → card net
  ~2.0–2.1 V = undefined input. State the host-side constraint explicitly;
  recovery flows release lines to Hi-Z, never drive high.
- 2026-08-28 (GATE 2 review): W_DISABLE#-to-BOOT mapping means a host that
  asserts W_DISABLE# at power-up forces download boot. Document the
  incompatible host class; keep that diode leg DNP-able.
- 2026-08-30: Dropped the M.2 pin-8 (W_DISABLE1#) BOOT leg in v1. Lesson:
  don't rely on M.2 sideband pins for a *secondary* recovery path when the
  same signal is already on a test point — the test point + flying lead
  covers every host, while a second edge-pin leg adds routing load in the
  worst corner for near-zero real benefit. Expose EN/BOOT on test points
  and keep the sideband count minimal.
- 2026-10-06 (rev B, self-caught): on v1 C5 pin 2 (EN RC cap GND) was a B.Cu
  GND island enclosed by the EN and USB_D_*_ESD tracks → no RC delay on EN;
  the card booted on the 10k pull-up alone. Same root cause as usb_esd: a
  pad boxed in by locked tracks, never reached by the pour. Now its own
  0.5 mm via to L2.
- 2026-10-06 (rev B, owner decision pending): pin-8 BOOT leg stays dropped
  unless the owner routes it - see ADR 0002 rev-B amendment.
