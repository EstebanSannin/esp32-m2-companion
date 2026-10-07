# v2 parts check (ESP32-S3 M.2 companion, JLCPCB assembly)

Date: 2026-10-07. Sources:
- **JLC status and stock**: live JLCPCB API (`/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList`). `base` means Basic, `expand` means Extended. Stock is a snapshot from today.
- **Electrical specs**: the manufacturer datasheet PDFs that LCSC links. They were downloaded to `scratchpad/ds/` and read with pdftotext.
- **Footprints**: the installed KiCad 9 library (`~/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints`).
- **TI land patterns**: the local TI datasheets in `docs/datasheets/` (tps25947.pdf is SLVSFC9C, rev. May 2026; tmux1511.pdf is SCDS390B, rev. Mar 2025). These are the same documents as the ti.com symlinks.

## 1. Ferrite bead replacing GZ2012D101TF (C1015) on the ESP32-S3 3V3 rail

Only one ferrite bead in 0603/0805 is both JLC Basic and within spec (≥1.5 A, ≤50 mΩ, 60–220 Ω). That is **BLM18PG121SN1D**. The JLC Basic list for these packages holds just 4 beads: C14709, C1002, C1015 and C1017.

| # | MPN | LCSC | JLC | Stock (today) | Z @100 MHz | DCR max | Rated I | Pkg | Datasheet check |
|---|---|---|---|---|---|---|---|---|---|
| A | Murata BLM18PG121SN1D | **C14709** | **Basic** | 1,908,752 | 120 Ω ±25 % | 0.05 Ω | 2000 mA* | 0603 | Verified. Murata catalogue row: "BLM18PG121SN1 120Ω±25% 2000 0.05". *The derating curve is on a page missing from the LCSC excerpt, so the derating above 85 °C is unverified. DCR sits exactly at the 50 mΩ limit. |
| B | Murata BLM21PG121SN1D | C79382 | Extended | 47,524 | 120 Ω ±25 % | 0.03 Ω (initial) | 3000 mA @85 °C / 1550 mA @125 °C | 0805 | Verified (Murata spec sheet, Rating table). Same 0805 footprint as C1015. |
| C | TDK MPZ2012S101AT000 | C15957 | Extended | 132,251 | 100 Ω ±25 % | 0.020 Ω | 4 A | 0805 | Verified (TDK MPZ2012 table, plus a derating curve to 125 °C). Same impedance as C1015 and a drop-in 0805 replacement. |

Other in-spec Extended parts at JLC that I did not open the datasheet for (specs come from JLC's listing only):
- MPZ2012S221AT000 C76818 (220 Ω, 3 A, 40 mΩ)
- BLM21PG221SN1D C85840 (220 Ω, 2 A, 45 mΩ)
- BLM18KG221SN1D C88980
- BLM18SG121TN1D C113030 (120 Ω, 3 A, 25 mΩ, 0603, 12k in stock)

Recommendation:
- **C14709** if you want to stay Basic. It moves the footprint to 0603 and leaves no DCR margin, but the worst case is 0.05 Ω × 0.5 A = 25 mV.
- **C15957** if you want to keep the 0805 footprint and get real margin. This costs one Extended slot.

### Is a 0 Ω link acceptable per Espressif?
Yes. Nothing Espressif publishes calls for a ferrite at the module's 3V3 input:
- **HDG §1.3.2 (chip-level guidance)** asks for:
  - a ≥500 mA supply
  - an ESD diode plus ≥10 µF at the main power entrance
  - an "LC circuit to the VDD3P3 power rail", with the inductor rated preferably ≥500 mA.
  
  That LC belongs to the bare chip's analog VDD3P3 pins. It is **already inside the WROOM-1 module**: module datasheet v1.8, Fig. 8-1, shows L1 = 2.0 nH from VDD33 to VDD3P3 (pins 2/3), with 10 µF/1 µF/0.1 µF.
- **WROOM-1 datasheet §9, Fig. 9-1 (peripheral schematic)** feeds the module's 3V3 pin directly from VDD33, with only 22 µF + 0.1 µF and an ESD diode. There is no ferrite and no series element.
- **HDG ferrite and 0 Ω mentions**: the HDG mentions ferrites and 0 Ω parts only for SPI lines (series R or ferrite) and as zero-ohm placeholders. It never mentions them for the 3V3 input.

So a 0 Ω link (or a bead footprint fitted with 0 Ω) matches Espressif's reference design. A bead is optional EMC filtering, not a requirement.

## 2. 0402 4.7 kΩ 1 % (Basic)
- **C25900**, UNI-ROYAL 0402WGF4701TCE: **Basic**, 15,354,779 in stock, ±1 %, ±100 ppm, 62.5 mW. The UniOhm datasheet ordering code confirms WG = 1/16 W and F = ±1 %.

## 3. 0402 0.1 % thin film, ≤25 ppm/°C
No Basic part exists for either value. Every 0.1 % 0402 match is Extended.

| Value | MPN | LCSC | JLC | Stock | Tol / TCR |
|---|---|---|---|---|---|
| 100 kΩ | **YAGEO RT0402BRD07100KL** | **C852472** | Extended | 973,925 | ±0.1 % / ±25 ppm |
| 52.3 kΩ (E96) | **YAGEO RT0402BRD0752K3L** | **C852832** | Extended | 25,395 | ±0.1 % / ±25 ppm |
| 52.3 kΩ alt. | UNI-ROYAL TC0225B5232TCC | C50670108 | Extended | 8,837 | ±0.1 % / ±25 ppm (25 V rating; no datasheet link on JLC) |
| 52.3 kΩ alt. | Panasonic ERA-2AEB5232X | C2074813 | Extended | 7,149 | ±0.1 % / ±25 ppm |
| 100 kΩ alt. | Viking ARG02BTC1003 | C2984406 | Extended | 20,911 | ±0.1 % / ±25 ppm |

- **YAGEO RT datasheet**: B = ±0.1 % and TCR code D = 25 ppm/°C. RT0402 at ±25 ppm/±0.1 % covers 4.7 Ω–240 kΩ, so both values are in range. **Verified.**
- **Sourcing**: using the same RT0402 family for both resistors gives matched TCR tracking.
- **Stock**: 52.3 k stock is thin (25k), which is fine for prototype quantities.

## 4. KiCad 9 stock footprints

| Need | Exact .kicad_mod | Status |
|---|---|---|
| SOT-563 | `Package_TO_SOT_SMD:SOT-563.kicad_mod` | Exists |
| TPS259470A RPW (VQFN-HR-10 2×2) | **None** | **No RPW0010A footprint in KiCad 9.** The nearest names are different TI packages: `Texas_RPU0010A_VQFN-HR-10_2x2mm_P0.5mm` (TPS62912), `Texas_RUN0010A_WQFN-10_2x2mm_P0.5mm` and `DFN-10_2x2mm_P0.4mm`. None of these matches RPW, so a custom footprint is required. |
| TMUX1511 RSV (UQFN-16 1.8×2.6 P0.4) | `Package_DFN_QFN:UQFN-16_1.8x2.6mm_P0.4mm.kicad_mod` | Exists. It has no EP, matching RSV. A `QFN-16-1EP_1.8x2.6mm…` variant also exists but has an EP and is wrong for RSV. |
| 4×0402 convex array | `Resistor_SMD:R_Array_Convex_4x0402.kicad_mod` | Exists (descr: ROHM MNR04) |

### TPS259470A RPW0010A: TI land pattern (drawing 4225183/A)
The package is a VQFN-HR with irregular pads, so no generic QFN footprint can be used.
- **Pins 5 (IN) and 6 (OUT)**: full-length bars crossing the package.
- **Corner pins 1, 4, 7 and 10**: L-shaped. Each has a 0.6 mm side arm plus a vertical leg running to the package edge.
- **Pins 2, 3, 8 and 9**: 0.6 × 0.25 mm side pads.

Key TI dims (in mm, all reference values from the board-layout drawing): 1.8 / 1.45 overall X, 2.4 overall Y, 8X 0.6 side-pad length, 4X 0.25 / 4X 0.3 pad heights, 4X 0.475 and 4X 0.225 pitch offsets, 2X 0.3 / 4X 0.25 bar and leg widths, 2X 1.75 corner-pad span, and R0.05 corners.

Build it from TI's CAD model for RPW0010A (Ultra Librarian / TI EDA) rather than hand-reading the drawing. My reading of the exact coordinates of the L-pad legs from the PDF is **unverified**. Use NSMD mask (0.05 mm).

### TMUX1511 RSV0016A vs KiCad UQFN-16_1.8x2.6mm_P0.4mm
Package (TI 4220314/C): body 1.8 × 2.6 mm, leads 0.4 long (pin 1 is 0.5 long), 0.2 wide, 0.4 pitch.
- **Pin-1 location and pin order**: they match. Pin 1 is top-left on the long left side; 1–4 run down the left, 5–8 along the bottom, 9–12 up the right, 13–16 along the top.
- **Pitch and widths**: they match (0.4 / 0.2).
- **Pad length mismatch**: KiCad pads are longer, and their extra length mostly extends outward past the package edge (toe):

| Pads | TI land | KiCad |
|---|---|---|
| Side pads 2–4, 9–12 | 0.6 long at x = ±0.8, spanning 0.5–1.1 | 0.8 long at x = ±0.85, spanning 0.45–1.25 |
| Pin 1 | 0.7 long, spanning 0.4–1.1 | 0.9 long, spanning 0.35–1.25 |
| Top/bottom pads | 0.6 long at y = ±1.2, spanning 0.9–1.5 | 0.8 long at y = ±1.25, spanning 0.85–1.65 |

- **Effect**: KiCad's toe is about 0.15 mm longer and its inner (heel) edge is 0.05 mm further inward. The corner gap between pin 4 and pin 5 is 0.15 mm in KiCad versus about 0.21 mm on TI's land.
- **Verdict**: KiCad's pattern is usable (IPC-generated), but it is not TI's. If you want TI's land exactly, shorten the pads to 0.6 / 0.7 mm at the TI centres. No pin-1 mismatch.

## 5. 4D02WGJ0221TCE (C25498)
- **Convex check (verified)**: the UniOhm datasheet (JLC-01-015, p. 4) lists 4D02/4D03 under **"Convex Terminal type"**. In the ordering code, D = convex, C = concave and F = flat.
  - Dimensions: L 2.0, W 1.0, P 0.50 pitch, end terminals A1 0.40 wider than inner terminals A2 0.30, B 0.20.
  - Circuit: R1 between pins 1–8, R2 between 2–7, R3 between 3–6, R4 between 4–5.
- **Match to KiCad (matches)**: `R_Array_Convex_4x0402` has 0.5 mm pitch, outer pads 0.5 × 0.4, inner pads 0.5 × 0.3, columns at x = ±0.5, and pin 1 opposite pin 8. The footprint's long axis is vertical, while the datasheet drawing's is horizontal, so set the JLC rotation accordingly.
- **Note**: C25498 is **Extended** (78,604 in stock). There is **no Basic 4×0402 array** at JLC: every 4D02 value is Extended. 4D02WGJ0103TCE (C25725) is "preferred" but still Extended.

## 6. Addendum (coordinator request)
- **470 kΩ 0402 1 %: no JLC Basic part exists.** Every 470 kΩ 0402 result from the JLC API is Extended. The best options:

  | MPN | LCSC | JLC | Stock |
  |---|---|---|---|
  | UNI-ROYAL 0402WGF4703TCE | **C25790** | Extended, but flagged "preferred" (no extended-part setup fee) | 256,368 |
  | YAGEO RC0402FR-07470KL | C137976 | Extended | 915,905 |

  The other UniOhm 0402 1 % values I checked near 470k are also Extended:
  - C25782 (390k)
  - C25786 (430k)
  - C25793 (499k)
  - C11616 (510k)
  - C132339 (560k)
  
  The nearest Basic values are 200 kΩ (C25764, 0402WGF2003TCE, 2,279,028 in stock), 100 kΩ (C25741) and 1 MΩ (C26083). If staying all-Basic matters, consider re-ratioing the divider to use those values.
- **C26083** = **0402WGF1004TCE** (1 MΩ ±1 % 100 ppm 62.5 mW): **Basic**, 2,417,898 in stock. Your MPN string is correct.
- **C25741** = **0402WGF1003TCE** (100 kΩ ±1 % 100 ppm 62.5 mW): **Basic**, 8,724,771 in stock. Your MPN string is correct.
