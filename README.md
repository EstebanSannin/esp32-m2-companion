<p align="center">
  <img src="docs/img/samnium_tech_logo.png" alt="Samnium Tech" width="240">
</p>

# esp32-m2-companion

M.2 Key-B 2242 card with an ESP32-S3-WROOM-1 acting as a USB companion MCU
for embedded Linux hosts. Spec: [SPEC.md](SPEC.md) (contract, frozen v1).

**Current revision: v1.0 Rev B** — a fix-only respin of v1.0 (v1.0 was built
and fully brought up, see [docs/bringup.md](docs/bringup.md)). Major version
numbers are reserved for feature additions.

<p align="center">
  <img src="docs/img/board_iso.png" alt="3D render of the v1.0 Rev B card" width="560">
</p>
<p align="center"><sub>
  Generated render of the v1.0 Rev B board · <a href="docs/img/board_top.png">top</a> ·
  <a href="docs/img/board_bottom.png">bottom</a> (silk logo) · regenerate with <code>make render</code>
</sub></p>

**[→ Product datasheet](DATASHEET.md)** — features, specs, pinout, recovery interface.
**[→ Layer stackup & routing](docs/stackup.md)** — 4-layer stack, impedance, per-layer copper views.
**[→ Interactive 3D viewer](https://estebansannin.github.io/esp32-m2-companion/3d/viewer.html)**
(GitHub Pages; or download [docs/3d/viewer.html](docs/3d/viewer.html) — fully
offline, GLB embedded) · [STEP](docs/3d/esp32_m2_companion.step) /
[GLB](docs/3d/esp32_m2_companion.glb) for MCAD · regenerate with `make 3d`.

**Open source hardware** — © 2026 Stefano Viola, licensed under
[CERN-OHL-P v2](LICENSE). Designed by Stefano Viola with Claude (Anthropic);
schematic-as-code in SKiDL, all outputs generated (see *Build targets*). The vendored M.2 card-edge footprint derives from
[timonsku/M.2-Card-Footprints](https://github.com/timonsku/M.2-Card-Footprints)
(CERN-OHL-P v2).

## Status — v1.0 Rev B

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
(layout) and B2 (labels) approved; GATE B3 (JLC preview check + order) pending.
Rev B review artifacts: [docs/review/](docs/review/) · findings log:
[docs/review-findings.md](docs/review-findings.md).

## Build targets

| Target | Output |
|---|---|
| `make check` | ERC + netlist + BOM (after every schematic-source change) |
| `make drc` | DRC gate — fails on any non-excluded violation or unconnected item |
| `make sch` | generated KiCad schematic + PDF |
| `make drawings` | assembly + fab drawings PDF (`docs/review/`) |
| `make labels` | label inventory (`docs/review/`) |
| `make fab` | JLCPCB gerbers/BOM/CPL + polarity checklist (`fab/`); exit 2 = order blocked |
| `make datasheet` | DATASHEET.md |
| `make render` / `make layers` / `make 3d` | renders, per-layer views, GLB/STEP/viewer |

## Host compatibility

| Host | Status |
|---|---|
| Toradex Mallow (Verdin) M.2 Key-B slot | Primary target — **validated on hardware** (v1.0 bring-up on Verdin iMX8MP, docs/bringup.md) |
| Raspberry Pi 5 + Waveshare "PCIe TO 4G/5G M.2 USB3.2 HAT+" | Nice-to-have (ADR 0004) — HAT officially fits 3042/3052 (2242 standoff TBD), sideband wiring unpublished |
| Raspberry Pi official M.2 HAT+ | **NOT compatible** — M-key, PCIe only, no USB on the socket |

Note: the card is taller than the M.2 single-sided envelope (module 3.1 mm,
JST plug ≈ 6.3 mm on the top side vs 1.5 mm) — fine in open slots like Mallow's,
not for enclosed hosts (risks R11).

## Layout

- `docs/datasheets/` — all reference documents (provenance in its README)
- `docs/pinmap.md` — M.2 edge + ESP32-S3 pin allocation (GATE 1)
- `docs/decisions/` — ADRs
- `docs/risks.md` — risk register
- `docs/bringup.md` — v1.0 bring-up log + Rev B checks
- `docs/review/` — Rev B schematic, drawings, label inventory
- `fab/README.md` — JLCPCB order settings + polarity-preview procedure
- `docs/environment.md` — tool install log
- `hardware/` — schematic-as-code + KiCad (Phase 1+)
- `firmware/` — ESP-IDF project (Phase 4)
