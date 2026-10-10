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
- 2026-10-06 (**rev B, CORRECTS the 2026-09-02 entry above**): the
  `USBH3_D_N` via was not "grazed" - measured with pcbnew its centre sat
  **0.29 mm inside the notch cut-out**, the whole 0.3 mm drill in milled-away
  area. D− *was* severed on v1 (bring-up board needed a finger-9 → U1.3
  jumper). The rev-A GND "stub" was also not redundant: it was J1.11's
  (the USB pair's adjacent GND finger) only tie to the pour, routed across
  the notch - so the milling floated J1.11 too.
- 2026-10-06: a waiver keyed on `memberOfFootprint('J1')` is board-wide when
  J1 owns the Edge.Cuts outline (KiCad evaluates the rule with A/B either
  way, and every edge segment is a J1 member). Waive by item type + pad
  (`A.Type == 'Pad' && A.memberOfFootprint('J1') && A.Pad_Type == 'SMD'`),
  never `min_copper_edge_clearance = 0`, and prove the rule still flags a
  known violation before fixing it.
- 2026-10-06: mounting notch now NPTH with no copper (library + board). The
  NPTH still sits inside U2's antenna keep-out - unavoidable (M.2 screw
  position is fixed); documented DRC exclusion in tools/check_drc.py.
- 2026-10-10 (GATE V3, self-caught): a GND finger is only grounded if its
  pour piece reaches the plane. A via of another net right above a finger
  (fingers alternate F/B at 0.25 mm) isolates it, and DRC reports it only
  as "unconnected" between pour islands — four GND fingers were floating.
  Keep the strip above each GND finger via-free or give it a stub + GND via.
- 2026-10-10 (GATE V3): fingers next to the B-key notch (10, 11) have one
  0.5 mm strip between the notch edge and the next run: it holds either a
  via or a pour path, never both. Plan these before routing.
- 2026-10-10 (GATE V3): no copper between gold fingers — enter every finger
  from its top edge (the router once joined 70/72/74 across the contact area).
