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
- 2026-09-02 (**$38 lesson**, caught in JLCPCB review): the M.2 mounting
  semicircle is a **plated (PTH) hole centred on the top edge** → the fab sees
  a half-cut plated hole and flags "castellated holes not selected". Choosing
  proper castellated processing cost **$38 flat** (specialty-process setup fee,
  independent of hole count) on the v1 run. But our mounting hole carries **no
  net** — it's purely mechanical — so the plating buys nothing electrical.
  **Fix for rev B (and the RP2350 sibling that reuses this edge): make the
  mounting hole NPTH (non-plated).** A bare routed notch still takes the screw,
  drops no castellation flag, and avoids the fee. Only keep it PTH if you
  actually ground the mounting hole to the standoff for shielding (we don't).
- 2026-09-02 (caught in JLCPCB production-file review, **not** by our DRC): a
  `USBH3_D_N` (host-USB) via and a redundant GND stub sit right at the B-key
  notch. The outline milling grazes the via **pad** (drilled barrel is 0.15 mm
  clear, so the via survives) and clips the GND stub (harmless plane copper).
  **Root cause:** our `esp32_m2_companion.kicad_dru` waives `edge_clearance`
  for *all* `memberOfFootprint('J1')` — added so the gold fingers can legally
  touch the edge, but it **also suppressed the legitimate copper-near-notch
  warning**. DRC passed green; JLC's independent check caught it. **Fix (rev
  B):** (1) pull that USB via ≥0.3 mm inboard of the notch; (2) delete the
  dangling GND stub; (3) tighten the dru so edge-clearance is waived only for
  the finger *pads* (condition on pad/net), never vias/tracks — so a real
  copper-in-the-mill-path error can't hide again. Proceeded on v1 (prototype,
  barrel clear, no signal net severed).
