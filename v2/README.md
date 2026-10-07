# v2 — scratch area (NOT part of rev B)

Local-only brainstorm space for the next feature revision (v2.0 per SPEC §13 A2).

- Lives on branch `v2` (worktree `../esp32-m2-companion-v2`, branched
  from `rev-b` @ 27ee487 = the ordered rev-B state).
- Not in git (see `.gitignore`): `research/datasheets/*.pdf` (re-download via
  `research/datasheets/SOURCES.md`) and the probe's generated boards/DRC
  JSON (re-run the probe below).
- Decisions graduated out of this folder: ADR 0006–0008 and
  `docs/carrier-interface.md` (the carrier contract). This folder keeps the
  history and the research behind them.
- Nothing here is accepted. The tracked docs (`SPEC.md`, `docs/pinmap.md`,
  ADRs) remain the contract for rev B and are not modified by this work.

## Contents

| Path | What |
|---|---|
| `edge-expansion-brainstorm.md` | The design history: hardware-gated carrier expansion bus. **Start at §11–§14.** |
| `carrier/DEV_CARRIER_PROMPT.md` | Kick-off prompt for the dev/test carrier repo (first test of `docs/carrier-interface.md`) |
| `research/ovp_and_prices.md` | Input OVP options + v2 part prices (ADR 0007) |
| `research/m2_pins_research.md` | What every Key-B pin means across spec revisions, modems and real hosts (Dell, Waveshare, Osmocom, Mallow…) |
| `research/parts_research.md`, `research/dual_nmos_research.md` | LCSC/JLC part selection with datasheet-verified specs; PDFs in `research/datasheets/` |
| `probe/` | Routing feasibility probe on 2242 (4 L / 6 L): `strip.py` → `probe.py --no-route` → `gridprobe.py`, judged by KiCad DRC |

Re-run the probe (KiCad bundled python, from repo root):

    KPY=~/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3
    $KPY v2/probe/strip.py
    $KPY v2/probe/probe.py --layers 6 --no-route
    $KPY v2/probe/gridprobe.py --layers 6
