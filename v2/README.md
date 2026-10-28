# v2 — research and history behind v2.0 Rev A

Background material for the v2.0 feature revision (SPEC §13 A3). The design itself now lives in the
tracked sources: `hardware/`, `docs/v2-gate-v1.md` … `docs/v2-gate-v4.md`, ADR 0006–0008 and
`docs/carrier-interface.md` (the carrier contract). This folder keeps the research behind those
decisions.

- Branch `v2` (worktree `../esp32-m2-companion-v2`), branched from `rev-b` @ 27ee487 = the
  ordered Rev B state.
- Status (2026-10-10): GATE V0–V3 approved; GATE V4 fab package ready and **paused** until the
  Rev B boards are back from JLC (preview check of the polarized parts still to do).
- Not in git (see `.gitignore`): `research/datasheets/*.pdf` (re-download via
  `research/datasheets/SOURCES.md`) and the probe's generated boards and DRC JSON (re-run the probe
  below).
- `probe/gridprobe.py` was the routing-feasibility probe; it grew into the production router
  `hardware/tools/v2_route.py`.

## Contents

| Path | What |
|---|---|
| `edge-expansion-brainstorm.md` | The design history: hardware-gated carrier expansion bus. **Start at §11–§14.** |
| `carrier/DEV_CARRIER_PROMPT.md` | Kick-off prompt for the dev/test carrier repo (first test of `docs/carrier-interface.md`) |
| `research/ovp_and_prices.md` | Input OVP options + v2 part prices (ADR 0007) |
| `research/m2_pins_research.md` | What every Key-B pin means across spec revisions, modems and real hosts (Dell, Waveshare, Osmocom, Mallow…) |
| `research/parts_research.md`, `research/dual_nmos_research.md` | LCSC/JLC part selection with datasheet-verified specs; PDFs in `research/datasheets/` |
| `firmware/` | MicroPython bring-up self-test for v2.0 Rev A cards, used by `docs/v2-test-procedure.md` |
| `probe/` | Routing feasibility probe on 2242 (4 L / 6 L): `strip.py` → `probe.py --no-route` → `gridprobe.py`, judged by KiCad DRC |

Re-run the probe (KiCad bundled python, from repo root):

    KPY=~/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3
    $KPY v2/probe/strip.py
    $KPY v2/probe/probe.py --layers 6 --no-route
    $KPY v2/probe/gridprobe.py --layers 6
