# LESSONS — m2_keyb_edge

- 2026-08-28: Host sideband GPIO voltage domains vary (Verdin = 1.8 V, not
  3.3 V-tolerant). Never expose card pull-up nets directly on sideband pins;
  isolate every sideband input with a Schottky diode (host can pull low,
  never sees the card rail). (ADR 0002)
- 2026-08-28: Don't trust SPEC-level assumptions about which sideband pins a
  host actually drives — read the carrier schematic/datasheet table; on
  Mallow only PERST# is SoM-wired.
- 2026-08-29: The mated M.2 socket covers the card's first ~4.8 mm on BOTH
  faces (EM spec Figs 38/39). Model it as F/B courtyard IN the edge-finger
  footprint so placement violations are DRC errors, not review luck.
  (Owner caught U1 sitting in the zone from a 3D render.)
- 2026-08-30: The M.2 edge fingers at pins 7/8/9 (USB_D+ / W_DISABLE1# /
  USB_D−) are a 0.5 mm-pitch 3-conductor interleave where the two USB nets
  need layer-change vias (0.6 mm > 0.5 mm pitch). This corner cannot be
  auto-/blind-routed; route it interactively (fan the USB via pair a few mm
  inboard first to open a lane for the middle net). Anticipate this on any
  card where the module width leaves <~2 mm side strips.
