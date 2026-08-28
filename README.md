# esp32-m2-companion

M.2 Key-B 2242 card with an ESP32-S3-WROOM-1 acting as a USB companion MCU
for embedded Linux hosts. Spec: [SPEC.md](SPEC.md) (contract, frozen v1).

Current phase: **Phase 0 — Groundwork** → awaiting GATE 1 review of
[docs/pinmap.md](docs/pinmap.md).

## Host compatibility

| Host | Status |
|---|---|
| Toradex Mallow (Verdin) M.2 Key-B slot | Primary target — pin mapping verified against Mallow V1.1 datasheet |
| Raspberry Pi 5 + Waveshare "PCIe TO 4G/5G M.2 USB3.2 HAT+" | Best effort — HAT officially fits 3042/3052 (2242 standoff TBD), sideband wiring unpublished |
| Raspberry Pi official M.2 HAT+ | **NOT compatible** — M-key, PCIe only, no USB on the socket |

## Layout

- `docs/datasheets/` — all reference documents (provenance in its README)
- `docs/pinmap.md` — M.2 edge + ESP32-S3 pin allocation (GATE 1)
- `docs/decisions/` — ADRs
- `docs/risks.md` — risk register
- `docs/environment.md` — tool install log
- `hardware/` — schematic-as-code + KiCad (Phase 1+)
- `firmware/` — ESP-IDF project (Phase 4)
