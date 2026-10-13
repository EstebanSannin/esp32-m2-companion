# Review findings log (append-only — SPEC §12)

Format: `date · phase · severity · classification (BLOCK <name> / PROCESS / PROJECT) · finding · action`.
External-reviewer categorizations ("wrong" / "works but unprofessional" /
"fragile at scale") are preserved verbatim.

---

- 2026-08-28 · Phase 0 · medium · **PROJECT** · SPEC §6.4 sideband candidate
  list (RESET#/W_DISABLE#/FULL_CARD_POWER_OFF#) did not survive datasheet
  contact: only PERST# (pin 50) is SoM-wired on Mallow; W_DISABLE1# is
  pull-up-only; pins 6/67 have no documented driver, 67 is 1.8 V. → Mapping
  changed at GATE 1 (ADR 0002); noted in CLAUDE.md.
- 2026-08-28 · Phase 0 · medium · **BLOCK m2_keyb_edge** (self-caught) ·
  Host sideband GPIO domains vary (Verdin 1.8 V, not 3.3 V-tolerant); direct
  wiring of card 3.3 V pull-up nets to sideband pins would overvoltage 1.8 V
  hosts. → Schottky-diode isolation on every sideband input (ADR 0002);
  lesson recorded in block LESSONS.md.
- 2026-08-28 · GATE 2 · low · **PROJECT** (owner decision) · USB ESD array
  sourcing: ST USBLC6-2SC6 (C7519) primary, UMW clone (C2687116) approved
  second source. → BOM field `LCSC_2nd_source` added in usb_esd block.

## GATE 2 multi-agent adversarial review (2026-08-28, workflow wf_7e010569)

7 independent reviewers re-derived each block from source datasheets; every
finding attacked by 2 refutation verifiers (datasheet-evidence + circuit-
behavior lenses, xhigh effort). Core electrical design confirmed correct:
module pinout (0 findings), USB path polarity/pairing, recovery diode
topology & margins (≥145 mV worst-case), power budget (3.06 V worst case vs
3.0 V min). Confirmed findings:

- 2026-08-28 · GATE 2 · medium · **BLOCK sideband_recovery** · CONFIRMED (2/2
  uphold) · "Diode blocks when host high" claim false for push-pull-high
  hosts below ~2.8 V: net dragged to ~2.0–2.1 V (undefined input band),
  ~125 µA into host pin. Mallow paths unaffected (OD / open). → Docs
  corrected (pinmap §3.2, block docstring, ADR 0002 amendment); constraint
  stated; recovery flow = release to Hi-Z. LESSONS.md updated.
- 2026-08-28 · GATE 2 · low (verifiers downgraded from medium) · **BLOCK
  power_3v3 / esp32s3_companion** · CONFIRMED · BOM label "10uF 25V" wrong:
  C19702 (CL10A106KP8NNNC) is a 10 V part. Electrically fine at 3.3 V.
  → Relabeled "10uF 10V". Related: C15849 labeled 25 V is actually 50 V →
  relabeled "1uF 50V".
- 2026-08-28 · GATE 2 · low · **PROJECT** (docs) · CONFIRMED · pinmap [KEYB]
  column misquotes on NC pins: 41/43/47/49 (PCIe pair names transposed),
  38/68 (SDX2AP/AP2SDX shift), 56/58/60/64 (RFFE/WLAN/COEX names), and
  "12 × GND fingers" (actual 11). → All corrected in pinmap + _PINS.
- 2026-08-28 · GATE 2 · low · **PROCESS** (tooling) · DNP parts leaked into
  JLC assembly CSV: gen_bom keyed on a field the header block never set.
  → gen_bom now derives DNP from `do_not_populate`. Candidate rule for the
  shared hardware-design skill: "DNP handling must be enforced by the BOM
  generator, not by per-part convention."
- 2026-08-28 · GATE 2 · low · **BLOCK usb_esd** · HDG §1.3.13 series-R/
  shunt-C provision missing on USB D+/D−. → Added R7/R8 (0R populated,
  22–33R swappable) + C8/C9 (DNP), placed near module.
- 2026-08-28 · GATE 2 · low · **PROJECT** (risk) · Host-behavior failure
  modes undocumented: W_DISABLE1# low at boot ⇒ download mode (→ R10);
  stock Mallow PCIe driver may hold PERST# asserted (→ R9, verify at
  bring-up).
- 2026-08-28 · GATE 2 · low · **BLOCK power_3v3** · Rail margin is real but
  thin (~60 mV over module 3.0 V min worst-case); bead choice confirmed
  sound; recorded in LESSONS.md with "do not substitute higher-DCR bead".
- 2026-08-28 · Phase 2 · medium · **PROJECT** (self-caught) · Card exceeds
  the M.2 top-side height envelope (module 3.1 mm vs 1.5 mm): fine in open
  slots (Mallow), impossible in enclosed hosts. → risks.md R11, README note.
- 2026-08-28 · Phase 2 · medium · **PROJECT** (owner decision, ADR 0005) ·
  1×12 2.54 mm header cannot fit the 2242 card; replaced by JST SH-4
  (Qwiic) + SH-8, assembled. SPEC §6.6 amended.
- 2026-08-29 · Phase 2 · low · **PROCESS** (owner feedback) · netlistsvg
  renders have label/wire collisions (third-party layouter, not KiCad) —
  insufficient for review. → ADR 0001 fallback activated: tools/gen_sch.py
  generates a true .kicad_sch (global-label style, no crossing wires) with
  title block (project, git rev, license, credits); `make sch`. Candidate
  rule for the shared hardware-design skill: "schematic-as-code flows need a
  KiCad-native render path from day one."
- 2026-08-29 · Phase 2 · **high** · **BLOCK m2_keyb_edge** (OWNER-caught from
  3D render) · U1/C4/FB1 (bottom) and J3/J4 (top) courtyards intruded into
  the M.2 socket coverage zone: the mated connector overlaps the card's
  first ~4.8 mm on BOTH faces (EM spec Figs 38/39: 9.10 mm depth incl land
  pattern, 4.30 mm beyond card edge) — the card would not have seated.
  → All placements moved behind y=−4.8; the edge footprint now carries
  F/B.CrtYd rectangles over the zone so DRC catches this class forever.
  LESSONS.md updated. PROCESS candidate: "connector footprints must model
  the MATED envelope as courtyard, not just their own copper."
- 2026-08-29 · Phase 2 · medium · **BLOCK leds** (OWNER-caught) · Top-emitting
  LEDs invisible in-slot: card top faces away from host, bottom faces host
  at ~2.5 mm; a prior layout note claiming "bottom faces up on Mallow" was
  wrong (EM spec stack-ups: module component side faces away from host PCB).
  → Side-view LEDs at the left card edge (ADR 0003 amendment); layout-notes
  corrected; PROCESS candidate: "indicator LEDs on mezzanine cards must be
  edge-emitting or light-piped — check the mated orientation, not the bench
  view."
- 2026-08-30 · Phase 2 · high · **PROCESS** (self-caught, owner-flagged) ·
  Board routing burned ~28 full autorouter runs over a night by re-invoking
  freerouting to chase each DRC violation — every run is ~12 min AND
  reshuffles all auto-routed nets, so each fix invalidated the last. Root
  causes: (a) global-autorouter-in-the-loop instead of route-hard-nets-once-
  then-finish-by-hand; (b) guessing track coordinates instead of reading pad
  extents; (c) Python str.replace() edits silently no-matching as the file
  drifted; (d) autorouter slotting the GND/+3V3 plane layers; (e) over-strict
  skew assert on a USB-FS pair. → Full method captured in
  docs/routing-method.md. **Candidate rule for the shared hardware-design
  skill: "Never loop a global autorouter to fix individual DRC violations.
  Hand-route + lock the congested/critical nets once, autoroute the easy
  nets once, finish leftovers by hand without re-autorouting; the per-fix
  loop must be seconds (edit→DRC), not minutes."**
- 2026-08-30 · Phase 2 · medium · **BLOCK sideband_recovery** (owner
  decision) · M.2 pin-8 (W_DISABLE1_n) BOOT diode-OR leg DROPPED in v1:
  unroutable in the dense pin 7/8/9 interleave AND redundant with the
  TP1(EN)+TP2(BOOT) flying-lead recovery path. D2 pin 2 → NC; edge finger
  exposed/unconnected. Recovery preserved via host GPIO (Mallow pin 50+20)
  and test points (universal). → ADR 0002 amendment; block source +
  LESSONS.md updated; pinmap/datasheet regenerated.
- 2026-09-02 · Phase 2 · low · **BLOCK m2_keyb_edge** ($38, caught in JLCPCB
  review; backfilled from LESSONS.md 2026-09-03) · The mounting semicircle is a
  **plated (PTH) hole** centred on the top edge → the fab sees a half-cut
  plated hole and flags "castellated holes not selected"; proper castellated
  processing cost **$38 flat** (specialty-process setup fee, independent of
  hole count) on the v1 run. The hole carries **no net** — purely mechanical —
  so the plating buys nothing electrical. → Fix for rev B (and the RP2350
  sibling reusing this edge): make the mounting hole **NPTH**. PROCESS
  candidate: "mechanical mounting holes NPTH unless grounded to the standoff
  for shielding."
- 2026-09-02 · Phase 2 · low · **BLOCK m2_keyb_edge** (caught in JLCPCB
  production-file review, **not** our DRC; backfilled 2026-09-03) · A
  `USBH3_D_N` via + redundant GND stub sit at the B-key notch; outline milling
  grazes the via pad (barrel 0.15 mm clear → survives) and clips the GND stub
  (harmless plane copper). **Root cause:** `esp32_m2_companion.kicad_dru`
  waives `edge_clearance` for *all* `memberOfFootprint('J1')` — added so the
  gold fingers can legally touch the edge, but it also **suppressed the
  legitimate copper-near-notch warning**; DRC passed green, JLC's independent
  check caught it. → Fix (rev B): pull the USB via ≥0.3 mm inboard; delete the
  GND stub; tighten the dru so edge-clearance is waived only for finger *pads*
  (condition on pad/net), never vias/tracks. Proceeded on v1 (prototype, barrel
  clear, no net severed). PROCESS candidate: "scope DRC waivers to pads/nets,
  never whole-footprint or vias/tracks."
- 2026-10-05 · bring-up · medium · **BLOCK leds** (owner-caught on hardware) ·
  D3+D4 assembled **180° reversed** → every indicator LED reverse-biased
  in-circuit (dark) on both v1 boards, though all still light under a meter's
  diode test. Isolated by measurement (3V3 at R3/R4, IO48 toggles 0/3.5 V,
  ~3.5 V across the LED with zero current) and confirmed visually: R4 solders to
  the LED **cathode**, not the anode. **Schematic/footprint were correct**
  (netlist ties R-series→anode); the flip entered at **JLC assembly sign-off** —
  JLC's placement preview rendered the LED with "+" on the chip-side pad (their
  LCSC polarity/rotation convention for C273612/C273616 is opposite our
  footprint pin-1), they asked us to confirm, and **we approved it by eye without
  checking against the netlist.** Fixable at assembly with NO respin (correct
  D3/D4 CPL rotation +180°, or instruct "+ on the resistor-side pad"); rev-B
  bakes it into the CPL export + re-confirm emit face + R3→~68-100 Ω. **PROCESS
  candidate (shared hw skill): "never eyeball-approve a fab's LED/diode placement
  preview — verify the '+' lands on the pad wired to the series resistor; JLC/LCSC
  LED polarity convention frequently differs from the KiCad footprint and silently
  flips the part."**

## Rev B (v2) — pre-respin audit (2026-10-06)

- 2026-10-06 · Rev B · **high** · **BLOCK m2_keyb_edge** (self-caught;
  **corrects** the 2026-09-02 entry) · The `USBH3_D_N` via centre was
  **0.29 mm inside** the B-key notch cut-out (pcbnew measurement), so the drill
  was entirely in milled-away area — not "barrel 0.15 mm clear". D− was
  severed on v1, consistent with the bring-up hand-jumper. The "redundant" GND
  stub was J1.11's only tie to GND, so J1.11 also floated after milling.
  → Corner reroute (D−/D+ vias out of the notch, J1.11 own via), pending the
  pin-8 owner decision. LESSONS.md corrected.
- 2026-10-06 · Rev B · high · **PROCESS** (self-caught) · The
  `memberOfFootprint('J1')` edge-clearance waiver disabled edge clearance
  **board-wide**: J1 owns the whole Edge.Cuts outline. `min_copper_edge_clearance`
  was also 0.0. With a pad-scoped waiver + 0.3 mm the board flags exactly the
  notch copper and the mounting-hole copper, nothing else. → Fixed (commit
  c68b81b). **PROCESS candidate:** "Never key a DRC waiver on a footprint
  that owns the board outline; waive by item type + footprint, and prove the
  waiver still flags a known violation before trusting a green DRC."
- 2026-10-06 · Rev B · **high** · **BLOCK usb_esd / sideband_recovery**
  (self-caught) · On v1 **U1.2 (USBLC6 GND)** and **C5.2 (EN RC cap GND)**
  were B.Cu GND islands enclosed by locked tracks → no ESD ground return, no
  EN RC delay. DRC reported both as "unconnected items" and they shipped
  untriaged; fab gerbers and board share commit 5cf2c15, so v1 hardware
  matches. **Owner to confirm on a v1 board:** continuity U1 pin 2 ↔ GND and
  C5 pin 2 ↔ GND (expect open). → Each pad now has its own via to L2
  (eb07bec); tools/gnd_islands.py added. **PROCESS candidate:** "'DRC clean'
  = zero non-excluded violations AND zero unconnected items; every exclusion
  committed with a reason (`make drc`)."
- 2026-10-06 · Rev B · medium · **PROJECT** · v1 U1 (USBLC6) orientation
  cannot be proven by function (its GND floated; a 180° placement still sits
  on the SOT-23-6 land). → Owner: check the pin-1 dot on a v1 board; rev-B
  checklist row added.
- 2026-10-06 · Rev B · low · **BLOCK esp32s3_companion** (route.py) · 12
  EPAD GND vias co-located with the JLC module footprint's own plated pad-41
  satellite holes (24 `holes_co_located`, double drill hits). → Removed.
- 2026-10-06 · Rev B · low · **PROJECT** · `fp-lib-table` lacked the
  `esp32m2` library → DRC could never check board-vs-library footprint
  parity. → Registered; J1 now verifiably matches its edited library copy.
- 2026-10-06 · Rev B · low · **PROCESS** · `gen_fab.py` kept its own DNP
  list despite the 2026-08-28 rule. → CPL placed set now = generated BOM.
- 2026-10-06 · Rev B · low · **PROJECT** (labels) · DATASHEET.md calls the
  mounting notch a "plated GND pad"; it never had a net, and in rev B it is
  NPTH. Bottom silk still reads "v1.0 … 2026-08". → Label review (GATE B2).
- 2026-10-06 · Rev B · medium · **BLOCK sideband_recovery** (owner decision)
  · M.2 pin-8 (W_DISABLE1_n) BOOT diode-OR leg **restored** (ADR 0002 rev-B
  amendment). v1 dropped it as "unroutable" on a hand trace; my own rev-B hand
  trace also called the long run blocked. A one-net feasibility probe found a
  legal 0.15 mm corridor in seconds. R10 (W_DISABLE1# low at boot → download
  mode) is live again. **PROCESS candidate:** "Before declaring a net
  unroutable, run a one-net feasibility search with all other copper fixed;
  a human trace of a dense corner is not evidence."
- 2026-10-06 · Rev B · low · **PROCESS** (tooling) · KiCad 9.0.9's bundled
  macOS Python segfaults in interpreter finalization after every pcbnew
  script → "Python quit unexpectedly" dialog per run (owner-reported; results
  unaffected). → All pcbnew tools exit via `kicad_exit.hard_exit()`.

## Rev B label pass (2026-10-06, toward GATE B2)

- 2026-10-06 · Rev B labels · **high** · **BLOCK leds** (self-caught) · The
  `LED_TJ-S1706_SideView` footprint had **no silkscreen polarity mark** —
  the one part family that was assembled reversed on v1 carried nothing on
  the board to check against. → Silk cathode bar at pad 1 (= the part's
  black cathode mark); assembly drawing shows explicit '+'/'K'.
  **PROCESS candidate:** "Every polarized footprint carries a silk polarity
  mark that matches the part's physical marking; custom footprints are
  checked for this at creation."
- 2026-10-06 · Rev B labels · medium · **PROCESS** (self-caught) · DNP lived
  only in the netlist/BOM; the board had no DNP attribute, so the assembly
  drawing would have shown R5/R6/C8/C9 as fitted. → `tools/sync_dnp.py`;
  `make drawings` refuses on mismatch. Extends the 2026-08-28 rule: "DNP
  is enforced by the generator **in every output**, including drawings."
- 2026-10-06 · Rev B labels · medium · **PROJECT** (self-caught) · v1 label
  errors in DATASHEET.md: "bevelled gold fingers" (never possible — JLC
  can't bevel <50 mm boards) and "plated GND pad" (never had a net). v1
  fab/README listed 7 Extended parts but named only 5 lines (LEDs missing).
  → Corrected.
- 2026-10-06 · Rev B labels · low · **BLOCK io_header** · Per-pin silk on
  1.0 mm-pitch JST SH cannot be legible at the 0.8 mm minimum text height
  (~0.05 mm between columns), and J3 pins 2–3 sit over the B-key notch. →
  Proposal: connector legends + pin-1 arrows, pinout in DATASHEET (owner
  decision L3 at GATE B2).
- 2026-10-06 · Rev B labels · low · **PROCESS** (tooling) · KiCad 9's SWIG
  build returns raw, unwrapped pointers for the rest of a process after any
  `Remove()` (board or footprint), and segfaults on `Flip()` of an off-board
  footprint. → label_pass runs Remove-stages in their own process; library
  footprints are parsed as text. Recorded in tools docstrings.
- 2026-10-06 · Rev B labels · low · **PROCESS** · kicad-cli's PDF plot has no
  scale option, so assembly drawings of a 22×42 mm card are unreadable on A4.
  → `tools/asm_view.py` draws scaled assembly/fab sheets from the board.
- 2026-10-06 · GATE B2 · low · **PROJECT** (owner decision) · Unit serial
  number = ESP32-S3 factory base MAC, externally readable from the module's
  Data Matrix (`<6-digit prefix><MAC>`; owner scan of a v1 module:
  `1326113C0F027321E4`). No PCB-printed serial / JLC barcode. Mapping
  inferred (Espressif OUI, neighbouring MAC to the bring-up unit), to be
  confirmed on one unit at rev-B bring-up (docs/bringup.md).
- 2026-10-06 · GATE B2 · low · **PROJECT** (owner decisions) · Labels
  approved with: L1 `N$1`/`N$2` → `LED_PWR_A`/`LED_STATUS_A`; L2 `IO0_BOOT`
  → `IO0` (naming rule); L3 connector legends; L4 TP function labels;
  L6 R2/U2 fab-only; L7 0.8 mm text. L5: board/version label **"v1.0 Rev B"**
  — rev B is fixes only; the major number is reserved for feature additions
  (supersedes the "tag v2.0" in the rev-B brief). Applied in d344173.
  **PROCESS candidate:** "Name every net in schematic-as-code — an
  auto-generated net name in a review artifact is a missing label."
- 2026-10-06 · Rev B · low · **PROCESS** (self-caught, **corrects my own
  earlier claim**) · D3/D4 on the board had **no library nickname**
  (`"LED_TJ-S1706_SideView"` instead of `esp32_m2_companion:…`), so KiCad
  could not link them and DRC library parity silently skipped them. My
  statements in ca83220 / 28ceb78 that "DRC library parity confirms" the LED
  re-sync were therefore **unverified**. → Linked; parity now actually checks
  them and passes (graphics, cathode bar, 3D model). All footprints now carry
  a library nickname. **PROCESS candidate:** "Before trusting a parity check,
  confirm every footprint is linked to a library (`lib:name` FPID)."

## v2.0 Rev A — GATE V0 (2026-10-07)

- 2026-10-07 · GATE V0 · — · **PROJECT** (owner decisions) · v2 scope approved:
  SPEC A3 + ADR 0006 (hardware-gated 12-line expansion bus, CONFIG state 6,
  carrier signature 75+1, host-facing LED_1#/WAKE_ON_WWAN#/W_DISABLE2#),
  ADR 0007 (TPS259470A eFuse OVP, 0.1 % OVLO divider — owner: "do it
  properly"), ADR 0008 (stay 2242, go 6 layers; 2252/2260 reserved for a
  future "plus" model). Q4: GPIO_0..8 pins not used always-on. Q6: ESP32
  family only, no multi-MCU bus spec. EXP numbering = ascending M.2 pin
  (proposed by me, accepted with A3). Branch renamed `v2.0-revA` → `v2`.
- 2026-10-07 · GATE V0 · medium · **BLOCK m2_keyb_edge** (self-caught, also
  applies to v1/Rev B) · v1/Rev B leaves all CONFIG pins NC = M.2 state 15
  "No Module Present"; a CONFIG-aware host (laptop BIOS) may ignore the slot.
  Harmless on Mallow and adapters. Fixed in v2 by G10 (state 6); Rev B
  unchanged (fix-only, already ordered).
- 2026-10-07 · GATE V0 · medium · **PROJECT** (self-caught) · M.2 Rev 3.0
  labels the supply pins "3.3V/VBAT" (up to ~4.4 V on tablet-style hosts);
  v1/Rev B has no protection (ESP32-S3 abs max 3.6 V). Fixed in v2 by G11
  (ADR 0007); Rev B: document "3.3 V hosts only".
- 2026-10-07 · GATE V0 · low · **PROCESS** (self-caught, tooling) ·
  Freerouting 2.3 reports 108 violations on the *untouched* rev-B board and
  hits internal errors, so its "unrouted" counts were meaningless here.
  Replaced by `v2/probe/gridprobe.py` (grid search, real JLC clearances,
  KiCad DRC as judge). **PROCESS candidate:** "Before trusting an
  autorouter's verdict, run it on the known-good baseline board first."

## v2.0 Rev A — GATE V1 package (2026-10-07, awaiting owner)

- 2026-10-07 · GATE V1 · high · **BLOCK edge_expansion** (self-caught) · The
  `EXP_OE` pull-up of 100 kΩ (brainstorm + probe) cannot hold the 12 TMUX1511
  SEL inputs high: IIH up to ±2 µA each + 6 MΩ internal pull-downs → up to
  ~30 µA → ~3 V drop, OE ≈ 0.3 V < VIH 1.2 V; the bus would never enable.
  → 10 kΩ (OE ≥ 2.99 V worst case), C 1 µF keeps τ ≈ 10 ms.
  **PROCESS candidate:** "Sum the input leakage of every pin on a shared
  pull-up net against the datasheet max, not typ."
- 2026-10-07 · GATE V1 · medium · **BLOCK power_3v3** (self-caught) · OVLO
  window conflict: host max 3.465 V vs ESP abs max 3.6 V leaves 135 mV, but
  the TPS259470A reference alone spans ±1.7 %. 100 k/51 k (ADR 0007) can let
  3.63 V through; proposed 100 k/52.3 k 0.1 % (3.44–3.57 V) → owner decision
  (`docs/v2-gate-v1.md` §1.4). ADR 0007 / A3 G11 window to be updated after.
- 2026-10-07 · GATE V1 · medium · **BLOCK edge_expansion** (self-caught) ·
  ID-EEPROM I²C pull-ups were specified "card side behind the switch" in the
  contract — that would put 3.3 V on host pins 30/32 with the bus off and
  break the high-Z promise. → MCU side of the switch (4.7 kΩ).
- 2026-10-07 · GATE V1 · low · **BLOCK esp32s3_companion** · ESP32-S3
  datasheet v2.2: IO39 (MTCK) has a weak pull-up at reset (EFUSE_DIS_PAD_JTAG
  = 0) and IO18 a 60 µs high glitch at power-up → neither may drive an
  always-on host pin (LED/WAKE gates); both placed on EXP lines (switch off
  during power-up).
- 2026-10-07 · GATE V1 · — · **PROJECT** (owner decision) · GATE V1
  approved: pin allocation (`docs/pinmap.md` §6), circuit values, ID EEPROM
  format v1 + firmware rule, EXP_0/1 permanently I²C, BOM approach. OVLO
  divider **100 k / 52.3 k 0.1 %** (trip 3.44–3.57 V, never above the 3.6 V
  abs max). Contract capability column + ID EEPROM now **fixed**.

## v2.0 Rev A — GATE V2 schematic (2026-10-07)

- 2026-10-07 · GATE V2 · high · **PROCESS** (self-caught, tooling) ·
  `tools/gen_sch.py` only placed parts listed in its hard-coded BLOCK_REFS;
  every new v2 part fell into an unplaced "misc" group, so the GATE PDF
  rendered clean **without any v2 circuitry** (37 of 63 parts). → v2 blocks
  added, generic box symbols for code-defined parts, and an assert that no
  part is unassigned. **PROCESS candidate:** "A review artifact generator
  must fail on anything it does not render — compare its part count with
  the netlist."
- 2026-10-07 · GATE V2 · medium · **PROJECT** (self-caught, corrects ADR
  0007 / A3 / contract) · "Survives up to 28 V" was the eFuse IC rating; with
  the 100 k / 52.3 k divider the OVLO pin (abs max 6.5 V) limits IN to
  ~18.9 V. Docs corrected; still far above any M.2/USB fault.
- 2026-10-07 · GATE V2 · low · **BLOCK power_3v3** · TPS25947 EN/UVLO must
  not be tied straight to IN when IN can exceed 5 V (Table 6.3 note 2:
  ≥ 350 kΩ pull-up) → 470 kΩ.
- 2026-10-07 · GATE V2 · low · **PROCESS** · New
  `tools/check_v2_netlist.py` (in `make check`) asserts the v2 contract
  pin-by-pin on the generated netlist (EXP chain finger→switch→array→module
  pad, edge nets touch only J1 + switch, detect, host cells, eFuse);
  mutation-tested (fails on a renamed net).
- 2026-10-07 · GATE V2 · — · **PROJECT** (owner decision) · GATE V2
  approved: schematic as generated, FB1 = BLM18PG121SN1D (low-DCR ferrite,
  not 0 Ω). Owner verbatim: "for me it's really hard review schematics like
  the one you produce because it's extremely time consuming understand how
  component are connected. I'll trust you". → **PROCESS:** a label-only
  generated schematic is not an effective owner-review artifact; the
  approval rests on `check_v2_netlist.py` + ERC. From GATE V3 on, provide a
  reviewer-oriented view (per-block connection diagram / net tables).

## v2.0 Rev A — GATE V3 layout (2026-10-07, in progress)

- 2026-10-07 · GATE V3 · — · **PROJECT** (owner decision) · Test points:
  keep TP1 (EN) / TP2 (BOOT) as 1.0 mm pads (flying-lead recovery on any
  host); drop TP3–TP6 (TXD0/RXD0/3V3/GND duplicate J4 pins 1/2 and J3 pins
  2/1). Frees the module↔finger band. Schematic re-checked (ERC + contract
  netlist check PASS), review PDF/BOM refreshed.
- 2026-10-07 · GATE V3 · medium · **PROCESS** (self-caught) · Rev B routed
  signals on its plane layers (IO8, EN, RXD0, LED_STATUS_n, +3V3 … on In1
  GND and on the +3V3 plane layer). On 6 layers L2 (GND) and L5 (+3V3) must
  stay solid and In2/In3 carry signals → all rev-B routing ripped up except
  the validated USB pair (42 items, locked), parts re-placed
  (`tools/v2_ripup.py`, `tools/v2_place.py`: nearest legal spot to a
  routing-aware target). Consistent with ADR 0008 ("re-placement, not a
  patch").
- 2026-10-10 · GATE V3 · high · **BLOCK usb_esd** (self-caught, revises
  my own GATE V3 decision) · The rev-B USB route kept "as validated" ran on
  B.Cu straight through the new switch strip and fenced U3/U5 in. → USB
  re-routed (scripted, locked, `tools/v2_usb_route.py`): U1 → vias at the
  right edge → In2 (on the L2 GND plane) → vias → F.Cu into module pads
  13/14 through the pad channels. Pair skew 5.2 mm (FS budget: rev B
  asserted < 10 mm). **PROCESS candidate:** "Kept routing from a previous
  placement is only 'validated' for that placement — re-check it against
  the new parts before locking."
- 2026-10-10 · GATE V3 · — · **PROJECT** (owner decision) · Removed R5/R6
  (DNP Qwiic pull-ups), C8/C9 (DNP USB SI shunts) and R7/R8 (0 Ω USB links):
  frees the row the bus switches need for pin escapes; U1 now connects
  straight to the module. ERC + contract netlist check PASS, BOM 25 lines.
- 2026-10-10 · GATE V3 · medium · **PROCESS** (self-caught, tooling) ·
  Sequential maze routing walled pads in twice: a wide power track around
  the eFuse OVLO pin, and a short net hugging a 0.5 mm-pitch array column.
  Fixes: neck-down for wide nets, sense branches routed thin, shortest
  nets first, and escape fan-out (stub + via per fine-pitch pad) before
  any net routing. Iterated dangling-copper removal also unravelled nets
  whose end no longer met a moved pad — rerouted, but **don't iterate
  dangling cleanup blindly**.
- 2026-10-10 · GATE V3 · medium · **BLOCK edge_expansion** (self-caught) ·
  RN2/RN3 were placed rotated 180° wrong: MCU-side pads facing the module's
  thermal EPAD vias, switch-side pads facing the module's left IO pads, so
  every IO line wrapped the array. Flipped; all MCU-side IO lines now route.
  **PROCESS candidate:** "When placing a two-sided array, check which pad
  column faces which neighbour before routing."
- 2026-10-10 · GATE V3 · low · **BLOCK edge_expansion** · TMUX1511 footprint
  switched to TI's RSV0016A land pattern (`tools/gen_fp_rsv.py`, pads 0.15 mm
  shorter than KiCad's) for escape room; orphaned fan-out from moved parts
  removed by `tools/v2_drop_orphan_fanout.py` (anchored-to-pad test, not
  DRC's dangling list, which unravels signal nets).
- 2026-10-10 · GATE V3 · — · **PROJECT** (owner decision) · Smaller vias:
  JLC option "Min via 0.2mm/(0.3/0.35mm)" approved (quote 2026-10-10:
  100 pcs $156.80 → $207.49, +$0.51/board; adds 4-wire Kelvin test + FR4
  TG155; 8 layers was no cheaper at 100 pcs ($202.60) and +$149 engineering
  fee per order). As built: 90 of 213 vias are 0.35/0.2, on every EXP net and
  the crowded module/sideband nets — wider use than the "switch escapes
  only" first proposed; same per-order fee. → must be selected at order
  (GATE V4, CLAUDE.md design rules).
- 2026-10-10 · GATE V3 · medium · **PROJECT** (self-caught) · Hole-to-copper
  rule relaxed 0.25 → 0.2 mm = JLC capabilities "Inner layer via hole to
  copper clearance 0.2mm" (checked on the page 2026-10-10). The 0.25 mm
  margin, not via size, was what sealed the 0.4 mm-pitch switch pins.
- 2026-10-10 · GATE V3 · high · **BLOCK usb_esd** (self-caught; supersedes the
  2026-10-10 "In2 → F through the pad channels" entry) · The F.Cu leg of
  USB_D_P/N ran under U4/U5 at y 135.2/136.5 and blocked every escape via
  there. → In2 down the module's left pad column, via-in-pad on U2.13/14;
  no F/B run under the switches (`tools/v2_usb_route.py`).
- 2026-10-10 · GATE V3 · high · **BLOCK m2_keyb_edge** (self-caught) · Four
  GND fingers (3/5, 11, 57) were not connected on the card side: their F
  pour pieces were cut off by other nets' vias right above them (the +3V3_M2
  fingers-2/4 via, the LED_1_n escape, a thin +3V3_M2 link running along the
  finger tops). DRC showed it only as "unconnected" between pour islands.
  → vias moved, finger-57 stub + via, stitching tool, rule areas
  GND11_STRIP/BAND for finger 11's only F pour path. CLAUDE.md rule added.
- 2026-10-10 · GATE V3 · high · **PROCESS** (self-caught, tooling) · The grid
  router ran thin tracks between gold fingers 70-74 (contact area) and walled
  EXP fingers 59-65 with a sideways +3V3_M2 trunk. → finger-zone keep-out in
  the router; +3V3_M2 trunk and the EXP_7/10, LED_1_n fan-ins hand-routed and
  locked (`v2_power_route.py`, `v2_fanin_route.py`).
- 2026-10-10 · GATE V3 · medium · **PROCESS** (self-caught, tooling) · Router
  bugs found while hand-finishing: (1) a net could not change layer through
  its own existing via (escape vias were unusable); (2) terminals ignored
  copper already attached to a pad (hand stubs / escapes); (3) rule areas
  blocked every layer, not their own; (4) grid quantisation refuses legal
  45° paths 0.47 mm from a via. Fixed (1)-(3); (4) worked around by hand.
  `--debug/--dump` reachability added — use it before rip-up guessing.
- 2026-10-10 · GATE V3 · medium · **PROCESS** (self-caught, repeat) · Pruning
  on KiCad's track_dangling flag unravelled complete nets again (KiCad flags
  route ends on rounded pad corners). → `v2_prune_branches.py` prunes by
  real copper overlap; `v2_tie_vias.py` handles "dangling" single-layer vias.
  A hand stub was also placed after probing only its via spot, not its path
  (finger 57 → short to an EXP_6 via): probe the whole path.
- 2026-10-10 · GATE V3 · medium · **BLOCK power_3v3** (self-caught) · RPW
  footprint L-pins: bar and leg rects only abutted, so KiCad saw U6 pin 1
  (EN) as two unconnected pads. → leg overlaps bar 0.15 mm
  (`gen_fp_rpw.py`). Also: C14/R34 sat in the J1 courtyard (DRC error carried
  since the first placement) → eFuse cluster re-placed: C1/C2 bulk caps moved
  to the module 3V3 pin, U6 +1.7 mm, FB1 right above U6 (OUT hop 1.5 mm).
- 2026-10-10 · GATE V3 · low · **PROJECT** (owner decision) · USBH3_D_N
  (rev-B locked route) finger-9 via moved 1.7 mm up (0.35/0.2 via, +0.2 mm
  length): it capped finger 10 (LED_1_n, new in v2) against the B-key notch.
- 2026-10-10 · GATE V3 · low · **PROJECT** (owner decision) · Silkscreen:
  name on top split around the notch; back = logo + version + "Designed in
  Italy" + samnium.tech; owner hand-edited reference labels; 0.8 mm minimum
  kept (owner's 0.5/0.6 mm drafts raised). DRU waiver `gnd_single_spoke_pads`
  (R28.2, C11.2, Q1.4 via-backed; J1.21 no room). NB: `min_resolved_spokes`
  takes a bare number — `(min 1)` made KiCad silently drop the whole .kicad_dru.
- 2026-10-10 · GATE V3 · low · **PROCESS** · GATE V2 asked for the RPW
  footprint "from TI's CAD model, not PDF reading"; it was drawn from the
  datasheet land/stencil drawings (every labelled dimension cross-checked).
  → open item: compare against TI's CAD model before GATE V4.
- 2026-10-10 · GATE V3 · — · **PROCESS** · SPEC A3 GATE V3 names
  `v2/probe/gridprobe.py` as the pre-route gate; in practice it grew into the
  production router `hardware/tools/v2_route.py` (same obstacle model) and
  the gate evidence is `make drc` = 0 violations / 0 unconnected.
- 2026-10-10 · GATE V3 · — · **PROJECT** (owner decision) · **GATE V3
  approved** as packaged in `docs/v2-gate-v3.md` (incl. the 0.35/0.2 via
  option, hole-to-copper 0.2 mm, `gnd_single_spoke_pads`, GND11 rule areas).
  Module stays ESP32-S3-WROOM-1-N8R2. → GATE V4 (fab package) started.
- 2026-10-10 · GATE V4 · medium · **PROJECT** (owner decision) · Supply risk:
  SSM6N56FE (Q1–Q3) JLC stock fell 7,293 → 124 in four days (300 needed per
  100 boards). Kept for prototypes; **Vishay SI1024X-T1-GE3 (C86784)
  approved as 2nd source** (same SOT-563 pinout; VGS max ±6 V vs our ±8 V
  margin criterion — gates ≤ 3.6 V in this design). NTZD3154N rejected (IGSS
  up to 5 µA vs the 1 MΩ CONFIG detect divider). → `LCSC_2nd_source` field,
  review-BOM column "Approved 2nd source".
## GATE B3 — JLC assembly DFM (2026-10-13)

- 2026-10-13 · GATE B3 · **high** · **BLOCK leds** (caught by JLC
  engineering, physical part) · **The TJ-S1706 side-view LED's lens/electrode
  relationship is mirrored relative to our footprint.** JLC places these parts
  "according to the tape direction": with the emitting face toward the board
  edge, the **cathode** lands on the pad wired to R3/R4. So with this part and
  this footprint you get *either* correct polarity with the lens facing
  **inward** (toward R3/R4), *or* the lens facing the edge with reversed
  polarity (dark = v1). Rotation cannot fix it, and a part cannot be mirrored.
  **This corrects the v1 conclusion** (bringup.md, leds LESSONS 2026-10-05)
  that the hand-rotated D4 "restored polarity AND emit direction together":
  polarity was verified, the emit direction was assumed. → **Owner decision
  for this batch (option A):** keep correct polarity, LEDs mounted with the
  lens inward; observe how visible the glow is from the card edge in the
  slot. Rejected: lens out with reversed polarity (dark), DNP + hand-fit
  (same limit without a mirrored part), part swap (delay). **Next revision
  (required):** fix the footprint ↔ part relationship — verify lens vs
  cathode mark on the TOGIALED drawing, then either swap the footprint pad
  numbering and move the resistor connection to the other pad, or choose a
  side-view LED whose lens/polarity matches. **PROCESS candidate:** "For
  side-view/directional parts, polarity AND emit direction are a single
  physical constraint; verify both against the vendor tape drawing before
  layout — a correct-polarity check alone is not enough."
- 2026-10-13 · GATE B3 · low · **PROJECT** · Rest of the final DFM verified:
  U2 centred, pin 1 NW; J3/J4 pin 1 at the same end (the pre-order preview's
  J4 inconsistency was fixed by JLC engineering); D1/D2/U1 pin-1 correct;
  DNP R5/R6/C8/C9 empty. PCB production files checked with
  `make jlc-check`: PASS (upload identical, 57/57 holes, standard CAM
  adjustments only).
