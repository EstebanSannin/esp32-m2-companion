# Datasheets — host_sideband

| Part | File | Used for |
|---|---|---|
| Toshiba SSM6N56FE (Q2, Q3) | `docs/datasheets/ssm6n56fe.pdf` | pinout, thresholds |
| Vishay SI1024X-T1-GE3 (approved 2nd source for Q1–Q3, LCSC C86784) | `docs/datasheets/si1024x.pdf` (Doc. 71170, S11-0854 Rev. E, 02-May-11) | pinout + limits vs SSM6N56FE (below) |
| ESP32-S3 | `docs/datasheets/esp32-s3_datasheet_en.pdf` v2.2 | IO42/IO47 reset states (Table 2-1) and glitches (Table 2-2); IO38 (Q3b hold-off gate, RC1): IE-only, no pull, no power-up glitch |
| M.2 spec Rev 1.0 | `docs/datasheets/m2_em_spec_rev1.0_2013_archive.pdf` | LED_1# (OD), WAKE_ON_WWAN# (OD, host pull-up), W_DISABLE2# (card pull-up 100–200 kΩ, §3.1.11.3 → R29 100 kΩ) — Table 25, §3.2.10 |

## SI1024X vs SSM6N56FE — verified from the PDFs (2026-10-28, RC1 review mcu_io-5)

| Item | SSM6N56FE (`ssm6n56fe.pdf` Rev 1.0) | SI1024X (`si1024x.pdf` Rev. E) | OK for this design? |
|---|---|---|---|
| Package / pinout (top view) | ES6 (SOT-563): 1 S1, 2 G1, 3 D2, 4 S2, 5 G2, 6 D1 (§3) | SOT-563 / SC-89: 1 S1, 2 G1, 3 D2, 4 S2, 5 G2, 6 D1 (p. 1 pin diagram) | **identical** — same footprint and pad-to-pin map |
| VDS max | 20 V (VDSS) | 20 V | yes |
| VGS max | ±8 V (VGSS) | **±6 V** | yes: gates here ≤ 3.6 V (fails only our own ≥ ±8 V margin criterion, GATE V4) |
| Vth | 0.4–1.0 V @ VDS = 3 V, ID = 1 mA | 0.45–0.9 V @ VDS = VGS, ID = 250 µA | yes (different test current; range inside the SSM6N56FE window) |
| IGSS | ±1 µA max @ VGS = ±6 V | ±0.5 µA typ, **±1 µA max @ VGS = ±4.5 V** | yes, same max; worst-case drop 1 µA × 1.1 MΩ on a floating CONFIG pin leaves Q1 gate ≈ 2.2 V > Vth max |
| RDS(on) | 480 mΩ max @ 1.8 V / 200 mA; 300 mΩ @ 2.5 V | 1.25 Ω max @ 1.8 V / 350 mA; 0.85 Ω @ 2.5 V; 0.70 Ω @ 4.5 V | yes: loads are EXP_OE (≤ 0.33 mA + C13 discharge), IO40 10 kΩ, LED_1#/WAKE# host pull-ups |
| ID (continuous) | 800 mA | 485 mA (steady state, TA 25 °C) | yes |
| PD | 150 mW | 250 mW steady state (TA 25 °C, FR4) | yes |
| Gate protection | none stated; ESD-sensitivity note | **gate-source ESD protected, 2000 V HBM**, 100 Ω series gate resistor in the symbol | better (relevant to review mcu_io-2: Q3a gate on pin 26) |
| Ordering | SSM6N56FE,LM (C146449) | Si1024X-T1-GE3, marking code "C" | — |

Conclusion: drop-in on footprint, pinout and every limit this circuit uses. CPL: same JLC
library orientation as C146449 (`gen_fab.py` `JLC_ROT` row C86784).
