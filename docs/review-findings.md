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
