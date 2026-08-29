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
