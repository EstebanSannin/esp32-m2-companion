# ADR 0001 — Schematic-as-code tool: SKiDL (atopile rejected)

Date: 2026-08-28 · Status: accepted

## Decision

**SKiDL 2.3.0** (Python, KiCad 9 toolchain) is the schematic source language.
atopile was evaluated first per SPEC §8 preference and rejected.

## Evidence against atopile (evaluated 0.15.8, 2026-08-28)

- The CLI itself warns on every run: *"atopile 0.15.8 is the last CLI release
  and is in maintenance mode only. The CLI has been replaced by the app at
  app.atopile.io (atopile 0.16+)."*
- Part picking now routes through their cloud service (`ato auth ...`).
- SPEC's fallback clause targeted "component/footprint availability"; the
  actual blocker is broader: a deprecated CLI and a SaaS dependency are
  incompatible with this project's hardware-as-code requirements (headless
  `make check`, git-only source of truth, reproducibility years from now).

## Why SKiDL fits

- Plain Python in git; blocks are functions → SPEC §12 reusable-block
  structure and the RP2350 sibling derivation (G7) map naturally.
- Native KiCad 9 support: uses the official KiCad symbol/footprint libraries
  (ESP32-S3-WROOM-1, USBLC6-2SC6, BAT54A all present), emits a KiCad netlist
  the owner imports into pcbnew for Phase 2.
- Built-in ERC, runs headless in `make check`.
- Pin assignments are made by module pin *number* with runtime asserts that
  the KiCad symbol's pin *name* matches the datasheet — traceability check
  executes on every build.

## Consequences / accepted trade-offs

- No classic schematic sheet as native output. GATE 2's "human-readable
  schematic PDF" is produced from the netlist (netlistsvg/graphviz rendering,
  one page per block); if review finds it insufficient, fallback is a
  one-time KiCad schematic derived from the netlist (kept generated, never
  hand-edited).
- KiCad 9.0.9 pinned (SPEC §8) even though KiCad 10 is current.

## Amendment (2026-08-29)

The netlistsvg render path proved insufficient at owner review (label
collisions). The fallback named above is now implemented as
`hardware/tools/gen_sch.py`: a generated KiCad 9 `.kicad_sch` (global-label
style), exported to PDF with a full title block (project, date, git rev,
CERN-OHL-P v2 license, credits). Still generated-only — never hand-edited.
