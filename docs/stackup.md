# Layer stackup & routing

4-layer, 0.8 mm, **SIG / GND / PWR / SIG** — JLCPCB **JLC04081H-3313** stackup.
Layer renders below are generated from the routed board
(`hardware/kicad/esp32_m2_companion.kicad_pcb`); regenerate with `make render`
plus the per-layer export in `docs/`. Blue = copper.

## Stackup (top → bottom)

| # | Layer | Copper | Role | Notes |
|--:|---|---|---|---|
| 1 | **F.Cu** (top) | 1 oz | Signal + components | Module, JST connectors; short signal runs. Prepreg **3313, 0.0994 mm, εr 4.1** to L2 → sets the USB microstrip impedance |
| 2 | **In1.Cu** | 0.5 oz | **Solid GND plane** | Continuous reference for the USB pair; the reason the diff pair is clean. Core (NP-155F) below |
| 3 | **In2.Cu** | 0.5 oz | **+3V3 power plane** | Card 3.3 V rail (post-ferrite); every +3V3 pad vias to here |
| 4 | **B.Cu** (bottom) | 1 oz | Signal + components | Most routing; all passives, USBLC6, diodes, LEDs, test points |

- Board thickness **0.8 mm** (M.2 requirement).
- **USB pair** `USBH3_D_P/N` / `USB_D_P/N`: 90 Ω differential, **0.14 mm width /
  0.14 mm gap**, routed on the outer layers referenced to the L2 GND plane, no
  stubs (SPEC §6.3).
- **At order: Specify Stackup = `JLC04081H-3313`** (Standard, 0.80 mm, prepreg
  3313 RC57% 0.0994 mm) — *not* the 7628 default (thicker 0.72 mm "Special"
  stack). Specifying the stackup pins the 0.0994 mm prepreg, which is what sets
  the pair impedance.
- **Impedance Control QC option: left OFF** (JLC charges ~€28). The ESP32-S3 USB
  is Full-Speed (12 Mbps) only, so controlled impedance is not functional here;
  the paid option only buys a TDR measurement, not a different board.
- **Verified 2026-08-30** against JLCPCB's live impedance calculator: on
  JLC04081H-3313, 90 Ω differential (5.5 mil gap) → **5.2 mil (0.132 mm) width**.
  Our 0.14 mm traces give ~88 Ω (inside a ±10 % window) — no board change.

## The four copper layers

### 1 — F.Cu (top signal)
![top signal](img/layers/1_top_signal.png)

Component pads for the module (U2) and the two JST connectors (J3/J4), plus
short top-side signal segments. The dashed rectangle at the top is the antenna
keep-out (no copper under the module antenna).

### 2 — In1.Cu (GND plane)
![gnd plane](img/layers/2_gnd_plane.png)

Solid ground pour — the USB pair's return-current reference. Kept continuous
under the signal layers; the antenna region is excluded.

### 3 — In2.Cu (+3V3 power plane)
![pwr plane](img/layers/3_pwr_plane.png)

The 3.3 V card rail. Every +3V3 component pad reaches this plane through a via,
so power distribution is the plane, not surface traces.

### 4 — B.Cu (bottom signal)
![bottom signal](img/layers/4_bottom_signal.png)

Where most of the routing lives. The gold fingers are at the bottom edge; the
dot grid under the module is the EPAD ground-via array (thermal + GND,
Espressif HDG) — in Rev B these are the module footprint's own 12 plated
holes (v1 also had a duplicate board via on each; removed). Thin traces threading the GND pour are the signal routes.

## How this was routed

Hand-routed + locked: the USB differential pair (impedance-critical) and the
recovery/boot nets — in Rev B also the pin-8 `W_DISABLE1_n` BOOT leg (B.Cu →
In1 → B.Cu through the D1/D2 gap) and the notch corner
([v1 vs Rev B](img/revb_notch_corner.png)); autorouted (freerouting, 80 passes): the header/UART/LED
signals; planes poured last. Method and the lessons behind it:
[`routing-method.md`](routing-method.md). Full source of truth for every
track/via is the KiCad PCB file — open it in the PCB Editor to explore
interactively (click a net to highlight it end-to-end).

---

## v2.0 Rev A — 6 layers, JLC06081H-2116 (ADR 0008, GATE V3, 2026-10-07)

Source: JLC's own stackup + impedance APIs (Polar SI9000 backend), `v2/research/jlc_6l_stackup.md`.

| Layer | KiCad | Use | Dielectric below |
|---|---|---|---|
| L1 | F.Cu (0.035) | SIG | 2116 prepreg 0.1164 mm, Dk 4.16 |
| L2 | In1.Cu (0.0152) | **GND** plane | core 0.13 mm, Dk 4.17 |
| L3 | In2.Cu | SIG (new) | 7628 prepreg 0.2028 mm, Dk 4.4 |
| L4 | In3.Cu | SIG (new) | core 0.13 mm |
| L5 | In4.Cu | **+3V3** plane (moved from rev-B In2) | 2116 prepreg 0.1164 mm |
| L6 | B.Cu (0.035) | SIG | — |

Finished 0.83 ± 0.10 mm. JLC's general/free 0.8 mm 6-layer stackup ("No requirement" maps to it,
expedite allowed). Multilayer minimum 0.09/0.09 mm; vias are epoxy-filled and capped by default on
6 layers (via-in-pad OK); 6 layers is ENIG-only.

**USB pair, L1 over L2 GND:** 90 Ω ⇒ W 0.15 / S 0.13 (89.6 Ω, JLC solver). The rev-B routed pair
(0.14/0.14) solves to ~92 Ω on this stackup, inside ±10 %, so it is kept as routed. The
`USB_DIFF` net class is set to 0.15/0.13 for any new USB routing.
