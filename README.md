<p align="center">
  <img src="docs/img/samnium_tech_logo.png" alt="Samnium Tech" width="240">
</p>

# esp32-m2-companion

M.2 Key-B 2242 card with an ESP32-S3-WROOM-1 acting as a USB companion MCU
for embedded Linux hosts. Spec: [SPEC.md](SPEC.md) (contract, frozen v1).

<p align="center">
  <img src="docs/img/board_iso.png" alt="3D render of the card (pre-route placement)" width="560">
</p>
<p align="center"><sub>
  Generated render, pre-route placement · <a href="docs/img/board_top.png">top</a> ·
  <a href="docs/img/board_bottom.png">bottom</a> · regenerate with <code>make render</code>
</sub></p>

**[→ Product datasheet](DATASHEET.md)** — features, specs, pinout, recovery interface.
**[→ Layer stackup & routing](docs/stackup.md)** — 4-layer stack, impedance, per-layer copper views.
**[→ Interactive 3D viewer](https://estebansannin.github.io/esp32-m2-companion/3d/viewer.html)**
(GitHub Pages; or download [docs/3d/viewer.html](docs/3d/viewer.html) — fully
offline, GLB embedded) · **[quick 3D preview on GitHub](docs/3d/esp32_m2_companion.stl)**
(STL, rendered natively by GitHub) · [STEP](docs/3d/esp32_m2_companion.step) /
[GLB](docs/3d/esp32_m2_companion.glb) for MCAD · regenerate with `make 3d`.

**Open source hardware** — © 2026 Stefano Viola, licensed under
[CERN-OHL-P v2](LICENSE). Designed by Stefano Viola with Claude (Anthropic);
schematic-as-code in SKiDL, all outputs generated (`make check`, `make sch`,
`make svg`). The vendored M.2 card-edge footprint derives from
[timonsku/M.2-Card-Footprints](https://github.com/timonsku/M.2-Card-Footprints)
(CERN-OHL-P v2).

Current phase: **Phase 2 — Layout** (GATEs 1–2 passed). Owner routes
[hardware/kicad/esp32_m2_companion.kicad_pcb](hardware/kicad/esp32_m2_companion.kicad_pcb);
open items in [docs/layout-notes.md](docs/layout-notes.md).

## Host compatibility

| Host | Status |
|---|---|
| Toradex Mallow (Verdin) M.2 Key-B slot | Primary target — pin mapping verified against Mallow V1.1 datasheet |
| Raspberry Pi 5 + Waveshare "PCIe TO 4G/5G M.2 USB3.2 HAT+" | Nice-to-have (ADR 0004) — HAT officially fits 3042/3052 (2242 standoff TBD), sideband wiring unpublished |
| Raspberry Pi official M.2 HAT+ | **NOT compatible** — M-key, PCIe only, no USB on the socket |

## Layout

- `docs/datasheets/` — all reference documents (provenance in its README)
- `docs/pinmap.md` — M.2 edge + ESP32-S3 pin allocation (GATE 1)
- `docs/decisions/` — ADRs
- `docs/risks.md` — risk register
- `docs/environment.md` — tool install log
- `hardware/` — schematic-as-code + KiCad (Phase 1+)
- `firmware/` — ESP-IDF project (Phase 4)
