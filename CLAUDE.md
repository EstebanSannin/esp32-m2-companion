# Project conventions — esp32-m2-companion

SPEC.md is the contract; STOP at every GATE (SPEC §9) for owner review.
Knowledge management per SPEC §12 (findings log, block LESSONS.md, this file).

## Naming

- Net names follow the source datasheets **verbatim**:
  - M.2 edge nets: Mallow X17 names where they exist (`USBH3_D_P`,
    `USBH3_D_N`, `PERST#` → schematic-safe `PERST_n`), M.2 WWAN standard
    names otherwise (`W_DISABLE1_n`, `FULL_CARD_POWER_OFF_n`).
  - MCU nets: ESP32-S3-WROOM-1 pin names (`IO0`, `EN`, `IO19`/`USB_D_N`,
    `IO20`/`USB_D_P`, `TXD0`, `RXD0`).
  - `#` suffix in datasheets = `_n` suffix in sources (tools dislike `#`).
- Blocks (SPEC §12.2): `m2_keyb_edge`, `esp32s3_companion`, `usb_esd`,
  `power_3v3`, `leds`, `io_header`, plus `sideband_recovery` (EN/BOOT diode
  isolation — kept separate because the RP2350 sibling card reuses it as-is).
  Each block dir: sources + `datasheets.md` (references) + `LESSONS.md`.

## Tools

- KiCad 9.0.9 (pinned by SPEC §8; installed under ~/Applications, see
  docs/environment.md) — `kicad-cli` for headless ERC/DRC/exports.
- Schematic-as-code: **SKiDL 2.3** (ADR 0001 — atopile rejected: CLI
  deprecated in favor of SaaS app). Sources: `hardware/blocks/*/`,
  top-level `hardware/design.py`, uv-managed venv in `hardware/`.
- `make check` = ERC + netlist + BOM (runs `hardware/design.py`); run after
  every schematic-source change and show the result to the owner.
  `make sch` = generated KiCad schematic + PDF with title block
  (build/esp32_m2_companion_schematic.pdf) — the review/GATE artifact.
  `make svg` = auxiliary per-block netlistsvg renders (less readable).
- Pin-assignment traceability: block code references module pins by
  datasheet pin number; runtime asserts compare KiCad symbol pin names
  against the datasheet table on every build.

## Design rules (Phase 2)

- JLCPCB standard capability, ≥5/5 mil trace/space, ≥0.3 mm drill, 0.8 mm
  4-layer (SIG/GND/PWR/SIG), gold fingers + 45° bevel.
- USB diff pair `USBH3_D_P/N`: 90 Ω differential, length-matched, referenced
  to L2 GND, no stubs.
- Antenna keep-out at top card edge per Espressif HDG.
- **Routing method (MANDATORY — see docs/routing-method.md):** hand-route +
  lock the congested/critical nets once, autoroute the easy nets once, finish
  leftovers by hand WITHOUT re-running the autorouter. Never loop a global
  autorouter to chase individual DRC violations. Read real pad extents before
  placing tracks; verify every edit applied.

## Parts

- Every BOM line: LCSC part number + Basic/Extended status; Extended parts
  need one-line justification.

## Gate protocol

- Work autonomously within a phase; never cross a GATE without explicit owner
  approval. Findings at gates → docs/review-findings.md (append-only), with
  external reviewers' categorization preserved verbatim.
