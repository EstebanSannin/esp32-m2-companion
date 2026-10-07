# v2.0 Rev A — GATE V2 package (schematic)

Status: **approved 2026-10-07 (owner, FB1 = low-DCR ferrite)** · Previous gate: `docs/v2-gate-v1.md` (approved)

## Review artifacts
- `docs/review/v2_reva_schematic.pdf` — generated KiCad schematic (A1, all 63 parts;
  v2 blocks: "POWER 3V3 + eFUSE", "EXPANSION BUS + CARRIER DETECT", "HOST SIDEBANDS").
- `docs/review/v2_reva_bom.md` — generated BOM (28 lines, 13 Extended).
- `make check` → ERC clean + **`tools/check_v2_netlist.py` PASS**. This checks the contract
  pin by pin on the generated netlist and was mutation-tested.

## What changed vs Rev B (schematic)
| Block | Change |
|---|---|
| `m2_keyb_edge` | CONFIG_0/1 → GND (state 6); 75/1 = signature sense; 12 EXP pins, 10/23/26 used |
| `power_3v3` | **U6 TPS259470A eFuse** + OVLO 100 k / 52.3 k 0.1 %, EN 1 M, ILM 3.3 k, CIN; **FB1 → BLM18PG121SN1D** (0603, 2 A, ≤ 50 mΩ) |
| `edge_expansion` (new) | U3–U5 TMUX1511, RN1–RN3 220 Ω, R20/21 4.7 k I²C pull-ups (MCU side), Q1 detect + R22–R25, EXP_OE 10 k / 1 µF |
| `host_sideband` (new) | Q2 (LED_1#, WAKE), Q3 (W_DISABLE2#), R27–R30 |
| `esp32s3_companion` | 16 new GPIO connections, all datasheet-asserted at build time |

## New BOM lines vs Rev B (10)
- Extended: SSM6N56FE, TMUX1511, TPS259470A, 4D02 array, 2× 0.1 % resistors (no Basic
  equivalents; justified in `JLC_note`).
- Basic: 4.7 k, 1 M, 100 k, 3.3 k (0402).
- FB1 swapped to a Basic part.
- Reused rev-B lines: 10 k, 100 nF, 1 µF.

## Open items carried to GATE V3 (layout)
1. **U6 footprint:** no KiCad stock footprint for TI RPW (VQFN-10 2×2, L-shaped corner pads).
   Draw `esp32_m2_companion:TI_RPW_VQFN-10_2x2mm_P0.5mm` from TI's CAD model (not from PDF
   reading).
2. TMUX1511 footprint: KiCad UQFN-16 pads are 0.15 mm longer than TI's land. Usable;
   consider trimming to TI's land pattern.
3. RN array long axis is vertical: check the JLC rotation in `JLC_ROT` at fab.
4. Placement, then `gridprobe.py` must route all new nets DRC-clean before hand-routing
   (A3 §9 GATE V3).

## Decisions for the owner
- Approve the schematic as shown.
- FB1: low-DCR bead (chosen) vs a 0 Ω link (also valid: the WROOM-1 has its own internal
  LC filter).
