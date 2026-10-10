<p align="center">
  <img src="docs/img/samnium_tech_logo.png" alt="Samnium Tech" width="240">
</p>

# esp32-m2-companion

M.2 Key-B 2242 card with an ESP32-S3-WROOM-1 acting as a USB companion MCU
for embedded Linux hosts. Spec: [SPEC.md](SPEC.md) (contract; v2 = amendment A3).

**This branch (`v2`): v2.0 Rev A, in design.** v2 is a feature revision: it adds 12 expansion
lines on the M.2 edge for carrier boards (switched off on every normal host), input
over-voltage protection, and moves to 6 layers. Layout is done (GATE V3 approved); the fab
package is ready but **paused** until the Rev B boards are back. See [v2 status](#status--v20-rev-a-branch-v2).
The ordered board is **v1.0 Rev B** (branch `rev-b`; summary [below](#previous-revision--v10-rev-b)).

<p align="center">
  <img src="docs/img/board_iso.png" alt="3D render of the v2.0 Rev A card" width="560">
</p>
<p align="center"><sub>
  Generated render of the v2.0 Rev A board · <a href="docs/img/board_top.png">top</a> ·
  <a href="docs/img/board_bottom.png">bottom</a> (silk logo) · regenerate with <code>make render</code>
</sub></p>

**[→ Product datasheet](DATASHEET.md)** — features, specs, pinout, recovery interface.
**[→ Carrier interface](docs/carrier-interface.md)** — the contract for carrier and accessory boards (v2).
**[→ Layer stackup & routing](docs/stackup.md)** — 6-layer stack (v2), impedance, per-layer copper views.
**[→ Interactive 3D viewer](https://estebansannin.github.io/esp32-m2-companion/3d/viewer.html)**
(GitHub Pages; or download [docs/3d/viewer.html](docs/3d/viewer.html) — fully
offline, GLB embedded) · [STEP](docs/3d/esp32_m2_companion.step) /
[GLB](docs/3d/esp32_m2_companion.glb) for MCAD · regenerate with `make 3d`.

**Open source hardware** — © 2026 Stefano Viola, licensed under
[CERN-OHL-P v2](LICENSE). Designed by Stefano Viola with Claude (Anthropic);
schematic-as-code in SKiDL, all outputs generated (see *Build targets*). The vendored M.2 card-edge footprint derives from
[timonsku/M.2-Card-Footprints](https://github.com/timonsku/M.2-Card-Footprints)
(CERN-OHL-P v2).

## Status — v2.0 Rev A (branch v2)

| Gate | What | State |
|---|---|---|
| V0 | SPEC amendment A3, ADR 0006–0008, [carrier contract](docs/carrier-interface.md) | approved 2026-10-07 |
| V1 | [pinmap, values, ID EEPROM, BOM](docs/v2-gate-v1.md) | approved 2026-10-07 |
| V2 | [schematic](docs/v2-gate-v2.md) (`make check` + pin-by-pin contract check) | approved 2026-10-07 |
| V3 | [layout](docs/v2-gate-v3.md): `make drc` 0 violations / 0 unconnected | approved 2026-10-10 |
| V4 | [fab package](docs/v2-gate-v4.md): `make fab` ready, cost check done | **paused**: JLC placement-preview check of the polarized parts still to do; waiting for the Rev B boards |

What v2 adds (no change for existing hosts):
- **12 expansion lines (EXP_0..11) on otherwise-unused M.2 pins.** They go to ESP32 GPIOs through
  3× TI TMUX1511 switches and stay high-Z unless a carrier grounds CONFIG_2 + CONFIG_3 (the carrier
  signature). EXP_0/1 carry I²C with a carrier ID EEPROM. Contract:
  [docs/carrier-interface.md](docs/carrier-interface.md).
- **Host sidebands:** WWAN LED#, WAKE#, W_DISABLE2# through NMOS cells.
- **Input protection:** TI TPS259470A eFuse on the M.2 3.3 V (≈ 1 A limit, over-voltage cut-off
  3.44–3.57 V).
- **PCB:** 6 layers (JLC06081H-2116), small vias 0.35/0.2; same 2242 size, same module position.
- **Cost:** ≈ $48/board for 5 prototypes, ≈ $11/board at 100 (`docs/v2-gate-v4.md`).

v2 review artifacts: [docs/review/](docs/review/) (`v2_reva_*`: per-block connection tables,
schematic, drawings, BOM, label inventory) · findings log:
[docs/review-findings.md](docs/review-findings.md).

## Previous revision — v1.0 Rev B

Ordered at JLC (W2026100715339652); the board files live on branch `rev-b`.
v1.0 was fabbed, assembled and brought up: every subsystem works on real
hardware ([docs/bringup.md](docs/bringup.md)). Rev B fixes the v1 defects found
there — nothing new functionally:

| v1.0 defect | Rev B fix |
|---|---|
| D3/D4 LEDs assembled 180° reversed (dark) | JLC CPL rotation +180°; `make fab` blocks the order until each polarized part is verified against JLC's preview; silk cathode bar added |
| Green LED under-driven | R3 330 Ω → 100 Ω |
| USB D− via milled away in the B-key notch (needed a jumper) | vias moved out of the notch ([before/after](docs/img/revb_notch_corner.png)) |
| Plated mounting notch → $38 castellation fee | routed notch in the outline: not plated, no copper, no drill |
| USBLC6 and EN-RC capacitor grounds floating | dedicated GND vias |
| DRC waiver hid the notch problem | edge-clearance waiver scoped to the finger pads; `make drc` gate |

Also restored: the M.2 pin-8 (W_DISABLE1#) BOOT leg. Review record: GATE B1
(layout), B2 (labels) approved; ordered 2026-10. Rev B review artifacts:
`docs/review/rev_b_*` · findings log: [docs/review-findings.md](docs/review-findings.md).

## Build targets

| Target | Output |
|---|---|
| `make check` | ERC + netlist + BOM + v2 contract netlist check (after every schematic-source change) |
| `make drc` | DRC gate — fails on any non-excluded violation or unconnected item |
| `make sch` | generated KiCad schematic + PDF |
| `make drawings` | assembly + fab drawings PDF (`docs/review/`) |
| `make labels` | label inventory (`docs/review/`) |
| `uv --directory hardware run python tools/gen_connections.py` | per-block connection tables (`docs/review/v2_reva_connections.md`) |
| `make fab` | JLCPCB gerbers/BOM/CPL + polarity checklist (`fab/`); exit 2 = order blocked |
| `make datasheet` | DATASHEET.md |
| `make render` / `make views` / `make layers` / `make 3d` | renders, labelled views, per-layer views (6 L), GLB/STEP/viewer |

## Host compatibility

| Host | Status |
|---|---|
| Toradex Mallow (Verdin) M.2 Key-B slot | Primary target — **validated on hardware** (v1.0 bring-up on Verdin iMX8MP, docs/bringup.md) |
| Raspberry Pi 5 + Waveshare "PCIe TO 4G/5G M.2 USB3.2 HAT+" | Nice-to-have (ADR 0004) — HAT officially fits 3042/3052 (2242 standoff TBD), sideband wiring unpublished |
| Raspberry Pi official M.2 HAT+ | **NOT compatible** — M-key, PCIe only, no USB on the socket |
| Companion carrier boards (v2) | EXP bus enabled by the carrier signature; first one: dev carrier (separate repo `m2-dev-carrier`) |

Note: the card is taller than the M.2 single-sided envelope (module 3.1 mm,
JST plug ≈ 6.3 mm on the top side vs 1.5 mm) — fine in open slots like Mallow's,
not for enclosed hosts (risks R11).

## Layout

- `docs/datasheets/` — all reference documents (provenance in its README)
- `docs/pinmap.md` — M.2 edge + ESP32-S3 pin allocation (GATE 1; v2 in §6)
- `docs/carrier-interface.md` — v2 card ↔ carrier contract
- `docs/v2-gate-v*.md` — v2 gate packages (V1–V4)
- `docs/decisions/` — ADRs
- `docs/risks.md` — risk register
- `docs/bringup.md` — v1.0 bring-up log + Rev B checks
- `docs/review/` — review artifacts (`v2_reva_*` for v2, `rev_b_*` kept as history)
- `fab/README.md` — JLCPCB order settings (v2, 6 L) + polarity-preview procedure
- `v2/` — research and history behind v2 (brainstorm, part research, routing probe)
- `docs/environment.md` — tool install log
- `hardware/` — schematic-as-code + KiCad (Phase 1+)
- `firmware/` — ESP-IDF project (Phase 4)
