# Project conventions — esp32-m2-companion

SPEC.md is the contract; STOP at every GATE (SPEC §9) for owner review.
Knowledge management per SPEC §12 (findings log, block LESSONS.md, this file).

## Naming

- Revisions (SPEC §13 A2): fix-only respin = same version + revision letter
  (**v1.0 Rev B**); major number only for feature additions. Tag each
  fabricated revision on the exact commit whose fab package was ordered
  (e.g. `v1.0-revB`).
- Every net is named — no SKiDL auto nets (`N$x`) in review artifacts
  (LED anodes: `LED_PWR_A`, `LED_STATUS_A`; BOOT strap: `IO0`).
- Unit serial = ESP32-S3 base MAC, printed as the module's Data Matrix.
  v2 also has a human-readable board serial: JLC "Number only" serial in
  the 2 x 10 mm silk field on the back (fab/README.md); record serial <-> MAC
  at bring-up.

- Net names follow the source datasheets **verbatim**:
  - M.2 edge nets: Mallow X17 names where they exist (`USBH3_D_P`,
    `USBH3_D_N`, `PERST#` → schematic-safe `PERST_n`), M.2 WWAN standard
    names otherwise (`W_DISABLE1_n`, `FULL_CARD_POWER_OFF_n`).
  - MCU nets: ESP32-S3-WROOM-1 pin names (`IO0`, `EN`, `IO19`/`USB_D_N`,
    `IO20`/`USB_D_P`, `TXD0`, `RXD0`).
  - `#` suffix in datasheets = `_n` suffix in sources (tools dislike `#`).
- v2 edge nets (ADR 0006): J1 **pin names** keep the Mallow/WWAN names
  (traceability); the **nets** on them carry contract names: `EXP_0..11`
  (edge side), `EXP_n_S` (switch source side), `IOxx` (MCU side),
  `CONFIG_0..3`, `LED_1_n`, `WAKE_ON_WWAN_n`, `W_DISABLE2_n`, `EXP_OE`.
- Blocks (SPEC §12.2): `m2_keyb_edge`, `esp32s3_companion`, `usb_esd`,
  `power_3v3`, `leds`, `io_header`, plus `sideband_recovery` (EN/BOOT diode
  isolation — kept separate because the RP2350 sibling card reuses it as-is),
  and for v2 `edge_expansion` (switches + carrier detect) and `host_sideband`.
  Each block dir: sources + `datasheets.md` (references) + `LESSONS.md`.

## Tools

- KiCad 9.0.9 (pinned by SPEC §8; installed under ~/Applications, see
  docs/environment.md) — `kicad-cli` for headless ERC/DRC/exports.
- Schematic-as-code: **SKiDL 2.3** (ADR 0001 — atopile rejected: CLI
  deprecated in favor of SaaS app). Sources: `hardware/blocks/*/`,
  top-level `hardware/design.py`, uv-managed venv in `hardware/`.
- `make check` = ERC + netlist + BOM (runs `hardware/design.py`) + the v2
  contract netlist check (`tools/check_v2_netlist.py`); run after
  every schematic-source change and show the result to the owner.
  `make sch` = generated KiCad schematic + PDF with title block
  (build/esp32_m2_companion_schematic.pdf) — the review/GATE artifact.
  `make svg` = auxiliary per-block netlistsvg renders (less readable).
- `make drc` = DRC gate: fails on any non-excluded violation or unconnected
  item (exclusions + reasons in `hardware/tools/check_drc.py`). "DRC clean"
  means this passes — never a hand-picked subset.
- `make drawings` (assembly + fab PDF), `make labels` (label inventory) →
  `docs/review/`; `make render` / `make layers` / `make 3d` / `make datasheet`
  regenerate the published figures — rerun them before pushing a revision.
- `make fab` = JLCPCB package. **Exit 2 = ORDER BLOCKED** until every
  polarized part's rotation in `gen_fab.py` `JLC_ROT` carries a date verified
  against JLC's placement preview (`fab/polarity_checklist.md`). Never
  approve a fab's LED/diode preview by eye: the "+" must be on the pad wired
  to the series resistor (v1 LEDs were assembled reversed).
- `make jlc-check JLC=<zip>` = compare JLC's processed production files with
  `fab/` before confirming them (stored upload identical, every drill hole,
  per-layer diff images). Must PASS.
- KiCad-Python: run pcbnew scripts with KiCad's bundled python; exit via
  `tools/kicad_exit.py` (finalization segfaults); never `Remove()` and keep
  using the board in the same process (SWIG returns raw pointers after it).
- Pin-assignment traceability: block code references module pins by
  datasheet pin number; runtime asserts compare KiCad symbol pin names
  against the datasheet table on every build.

## Design rules

- JLCPCB standard capability, ≥5/5 mil trace/space, ≥0.3 mm drill, 0.8 mm,
  ENIG hard-gold fingers, **no bevel** (JLC can't bevel < 50 mm boards —
  SPEC §13 A1; hand-chamfer the leading edge). Rev B: 4-layer
  SIG/GND/PWR/SIG. **v2: 6-layer JLC06081H-2116, SIG/GND/SIG/SIG/PWR/SIG**
  (ADR 0008, `docs/stackup.md`); In1 GND and In4 +3V3 stay solid planes —
  no signal tracks on them. v2 vias: 0.45/0.3, 0.45/0.2 and 0.35/0.2 (the
  paid JLC "0.2mm/(0.3/0.35mm)" option, owner-approved GATE V3 — order with
  it selected); hole-to-copper 0.2 mm (JLC inner-layer value).
- Directional parts (side-view LEDs, anything with an emitting/receiving
  face): the footprint must encode emit direction AND polarity together,
  verified against the physical part (tape / vendor drawing / JLC engineers)
  — a CPL rotation cannot fix a mirrored footprint (GATE B3: lens inward on
  Rev B; fixed in v2 by renumbering the TJ-S1706 pads).
- Gold fingers: no copper between fingers; enter each finger from its top
  edge only. Every GND finger must reach the GND plane (v2 had 4 floating
  ones hidden behind other nets' vias — DRC "unconnected" on pour islands).
- DRC: copper-to-edge clearance 0.3 mm; the edge-clearance waiver covers only
  J1's SMD finger pads — never a whole footprint, vias, tracks or zones (a
  J1-wide waiver hid a via milled away in the B-key notch on v1). Mounting
  notch is routed in the outline (no drill, no copper). Every footprint must
  carry a library nickname so DRC library parity can check it.
- USB diff pair `USBH3_D_P/N`: 90 Ω differential, length-matched, referenced
  to L2 GND, no stubs.
- Antenna keep-out at top card edge per Espressif HDG.
- **Routing method (MANDATORY — see docs/routing-method.md):** hand-route +
  lock the congested/critical nets once, autoroute the easy nets once, finish
  leftovers by hand WITHOUT re-running the autorouter. Never loop a global
  autorouter to chase individual DRC violations. Read real pad extents before
  placing tracks; verify every edit applied.

## Carrier interface (v2)

- `docs/carrier-interface.md` is the contract for every carrier/accessory
  board (ADR 0006–0008). Any change to edge pins, CONFIG, power or mechanics
  updates it **in the same commit**. Carrier repos `@`-import it from their
  own CLAUDE.md, so keep it self-contained and mark items fixed/proposed.

## Parts

- Every BOM line: LCSC part number + Basic/Extended status; Extended parts
  need one-line justification.

## Gate protocol

- Work autonomously within a phase; never cross a GATE without explicit owner
  approval. Findings at gates → docs/review-findings.md (append-only), with
  external reviewers' categorization preserved verbatim.
