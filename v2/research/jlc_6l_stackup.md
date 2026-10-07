# JLCPCB 6-layer 0.8 mm stackups — research for esp32-m2-companion (M.2 2242)

Date: 2026-10-07. All data pulled live from JLCPCB's own endpoints (not from third-party pages).

## Sources

| ID | What | URL / endpoint |
|----|------|----------------|
| S1 | Quote-UI stackup list (same data the order page uses; names, layer order, thicknesses, order flags) | `POST https://jlcpcb.com/api/overseas-core-platform/shoppingCart/getImpedanceTemplateSettings` body `{"stencilLayer":6,"stencilPly":0.8,"cuprumThickness":1,"insideCuprumThickness":0.5}` (endpoint found in the JS of https://jlcpcb.com/impedance) |
| S2 | Impedance-calculator stackup templates (adds **Dk per layer**, glass style + resin content, finished-thickness label) | `POST https://jlcpcb.com/api/jlcTools/impedance/selectPageImpedanceDefaultTemplate` body `{"pageNum":1,"pageSize":99999,"plateLayerNumber":6,"plateThickness":0.8,"cuprumThickness":1,"innerCopperThickness":0.5,"boardType":1,"usePurpose":1}` (used by https://jlcpcb.com/pcb-impedance-calculator) |
| S3 | Calculator config: outer trace copper thickness / etch delta, solder-mask coating thicknesses | `POST https://jlcpcb.com/api/jlcTools/impedance/impedance-config/copper-trace-width/list`, `.../coverlay/list` |
| S4 | JLC impedance **solver** (the calculator's backend; error strings show it is Polar **SI9000**) | `POST https://jlcpcb.com/api/jlcTools/impedance/calc` + result over `wss://tools.jlc.com/jlcTools/webSocket/<uuid>`; model `DiffEdgeCoupledCoatedMicrostrip1B` ("差分阻抗（外层）" = differential, outer layer) |
| S5 | Capabilities page | https://jlcpcb.com/capabilities/pcb-capabilities |

Raw dumps kept next to this file: `tpl_6L_*.json` (S1), `calc_tpl_6L.json` (S2), `pics.json` (models), `sweep.txt` (S4 results), `jlccalc.mjs` (the script that drove S4).

Notes on the endpoints: the static https://jlcpcb.com/impedance page only *renders* the 1.6 mm sets (its server-side text says 6-layer "1.2/1.6/2.0 mm"), but its own API returns the 0.8 mm 6-layer set, and the capabilities page (S5) lists 6-layer thickness "0.8/1.0/1.2/1.6/2.0 mm". The quote UI list you saw matches S1 exactly.

## 1. All JLC06081H stackups (finished 1 oz outer / 0.5 oz inner)

Common to all: L1/L6 copper 0.035 mm (1 oz finished; calculator models outer trace as T1 = 1.6 mil from 0.5 oz base + plating, S3); L2–L5 copper 0.0152 mm (0.5 oz); every core is "H/HOZ, thickness excludes copper"; copper Dk entry 4.2 (irrelevant). Cores: L2/L3 share core A, L4/L5 share core B — so L2↔L3 and L4↔L5 are always the thin core pairs, L3↔L4 is the middle prepreg. All stackups are mirror-symmetric.

Dk and glass/resin from S2; thicknesses agree between S1 and S2 except where noted.

| Stackup | L1–L2 PP (mm, type, Dk) | Core L2/L3 (mm, Dk) | L3–L4 PP (mm, Dk) | Core L4/L5 | L5–L6 PP | Finished (S2 label) | S2 label / S1 flags |
|---|---|---|---|---|---|---|---|
| **JLC06081H-2116** | **0.1164, 2116 RC54 %, 4.16** | 0.13, 4.17 | 0.2028, 7628 RC49 %, 4.4 (S1 lists 0.2028 under "No requirement", 0.2104 under the named entry) | 0.13 | = L1–L2 | 0.83 ± 0.10 | **"通用免费" (general / free)**; expedite = yes. "No requirement" maps to this stackup |
| JLC06081H-2313 | 0.0964, 2313 RC58 %, 4.27 | 0.15, 4.35 | 2× 0.0964 2313 (= 0.1928), 4.27 | 0.15 | 0.0964 | 0.82 ± 0.10 | "特殊 Tg170" (special); expedite = no |
| JLC06081H-2116A | 0.1194, 2116 RC57 %, 4.29 | 0.13, 4.03 | 2× 0.0784 1080 (= 0.1568), 3.99 | 0.13 | 0.1194 | 0.79 ± 0.10 | special Tg170; expedite = no |
| JLC06081H-7628A | 0.2084, 7628 RC50 %, 4.46 | 0.075, 4.14 | 0.1118 2116 (S1: 0.1194), 4.29 | 0.075 | 0.2084 | 0.81 ± 0.10 | special Tg170; expedite = no |
| JLC06081H-7628 | 0.2104, 7628 RC49 %, 4.4 | 0.075, 3.99 | 0.1088 2116 (S1: 0.1164), 4.16 | 0.075 | 0.2104 | 0.81 ± 0.10 | S1: fixedFee 200 / coefficient 50 (units not shown — **probably a surcharge, unverified**) |
| JLC06081H-1080B | 0.0784, 1080 RC69 %, 3.99 | 0.15, 4.35 | 0.2008 7628 (S1: 0.2084), 4.46 | 0.15 | 0.0784 | 0.79 ± 0.10 | special Tg170; expedite = no |
| JLC06081H-1080 | 0.0764, 1080 RC67 %, 3.91 | 0.13, 4.17 | 2× 0.1164 2116 (= 0.2328), 4.16 | 0.13 | 0.0764 | 0.78 ± 0.10 | S1: fixedFee 200 / coefficient 50 (**surcharge? unverified**) |
| JLC06081H-1080A | 0.0764, 1080, 3.91 | 0.075, 3.99 | 1080 0.0764 + 7628 0.218 + 1080 0.0764 (= 0.3708) | 0.075 | 0.0764 | 0.80 ± 0.10 | special |
| JLC06081H-1080C | 0.0764, 1080, 3.91 | 0.13, 4.17 | 2× 0.0764 1080 (= 0.1528), 3.91 | 0.13 | 0.0764 | **0.7 ± 0.10** (thin!) | special |
| (JLC06081H-1080D, calculator only, not in quote list) | 0.0764 1080 | 0.20 | 0.0918 3313 | 0.20 | 0.0764 | 0.78 | — |

Reference — current 4-layer JLC04081H-3313: PP 0.0994 (3313 RC57 %, Dk 4.1) / core 0.5 (Dk 4.48) / PP 0.0994; label "通用免费", 0.80 ± 0.10.

## 2. Which stackup for SIG/GND/SIG/SIG/PWR/SIG with thin L1–L2

Every option is symmetric and every option has L2/L3 and L4/L5 on shared thin cores, so SIG/GND/SIG/SIG/PWR/SIG fits all of them: L3 references L2 GND across the core, L4 references L5 PWR across the core, and L3↔L4 is the thick middle prepreg (helps limit L3/L4 crosstalk; route L3/L4 orthogonally anyway).

Thin L1–L2 ranking: 1080 family 0.076–0.078 < 2313 0.096 < 2116 0.116–0.119 << 7628 0.21 (7628A/7628 are wrong for this, since their thick PP sits on the outside).

**Recommendation: JLC06081H-2116.**
- It is JLC's general/free stackup for 0.8 mm 6L (S2 label "通用免费"; the only one with expedite = yes in S1; "No requirement" maps to it). So it does not depend on JLC having special Tg170 laminate in stock, and the impedance-controlled order costs nothing extra.
- L1–L2 = 0.1164 mm (4.58 mil), only 17 µm thicker than today's 4-layer 3313 (0.0994). The USB pair geometry barely changes.
- L2/L3 core 0.13 mm gives tight GND coupling for L3 too.
- Runner-up: **JLC06081H-2313** (0.0964 mm, almost the same as the current 4L) if a slightly narrower pair is wanted. It is Tg170 "special" and has no expedite. The **1080** variants give the thinnest L1–L2, but 1080 and 7628 carry the S1 fee flag, and 1080C finishes at 0.7 mm, outside the M.2 0.8 mm nominal.

### 90 Ω differential, L1 over L2 GND (edge-coupled coated microstrip)

Solved on **JLC's own calculator backend (S4, Polar SI9000)**, driven by script with the parameters the web UI would send. The UI was not used directly, but these are the same inputs and the same solver. Inputs: H1 = L1–L2 PP, Er1 = that PP's Dk (S2), T1 = 1.6 mil, etch W2 = W1 − 0.5 mil (S3 outer 1 oz, base 0.5 oz), solder mask C1 = 1.0 / C2 = 0.6 / C3 = 1.0 mil, CEr = 3.8 (S3/S5).

W for exactly 90 Ω at a given gap S (bisection, result ±0.05 Ω):

| Stackup (H1, Er) | S = 0.09 mm | S = 0.1016 | S = 0.127 | S = 0.1524 |
|---|---|---|---|---|
| **2116** (0.1164, 4.16) | W 0.111 | W 0.125 | **W 0.146** | W 0.162 |
| 2116A (0.1194, 4.29) | 0.110 | 0.123 | 0.146 | 0.161 |
| 2313 (0.0964, 4.27) | 0.095 | 0.105 | 0.122 | 0.134 |
| 1080 (0.0764, 3.91) | 0.085 | 0.094 | 0.107 | 0.115 |
| 1080B (0.0784, 3.99) | 0.086 | 0.094 | 0.107 | 0.117 |
| 7628 (0.2104, 4.4) | 0.148 | 0.171 | 0.212 | 0.243 |

Spot checks (forward solve):
- **2116, W 0.15 / S 0.13 mm → 89.6 Ω** ← recommended netclass (round numbers, ≥ 0.09 min, same W as today)
- 2116, W 0.145 / S 0.127 → 90.3 Ω
- 2116, W 0.15 / S 0.15 (today's `USB_DIFF` netclass unchanged) → 92.5 Ω (inside ±10 %)
- 2116, W 0.125 / S 0.10 → 89.5 Ω (tighter option for the escape near the ESP32 / M.2 pins)
- 2313, W 0.12 / S 0.127 → 90.6 Ω; 2313 at 0.15/0.15 → 85.5 Ω
- Current 4L JLC04081H-3313 at 0.15/0.15 → 87.8 Ω (baseline for comparison)
- Fab tolerance on 2116 0.145/0.127, with ±20 % track width (S5) and the gap moving the other way: 78.9 to 102.9 Ω (worst case). JLC's impedance tolerance is ±10 % (S5), and USB 2.0 FS (12 Mb/s, edge rates of a few ns) is very forgiving.

KiCad stackup entry for JLC06081H-2116 (top→bottom): F.Cu 0.035 / PP 0.1164 Er 4.16 / In1 0.0152 / core 0.13 Er 4.17 / In2 0.0152 / PP 0.2028 Er 4.4 / In3 0.0152 / core 0.13 Er 4.17 / In4 0.0152 / PP 0.1164 Er 4.16 / B.Cu 0.035; mask Er 3.8. Total about 0.826 mm.

## 3. Fab rules for 6-layer (S5, quoted)

- **Min track/space, 1 oz:** "Multilayer: 0.09 / 0.09 mm (3.5 / 3.5 mil). 3 mil is acceptable in BGA fan-outs." (1–2 layer is 0.10/0.10.) So 0.09/0.09 is the multilayer minimum, not a premium option. The project rule ≥ 5/5 mil (0.127) sits comfortably above it. 2 oz multilayer: 0.15/0.15. Track width tolerance ±20 %.
- **Vias (multilayer):** "0.15 mm hole size / 0.25 mm via diameter (0.1mm hole size / 0.2mm via diameter only available for board thickness ≤1mm; ENIG/OSP surface finish required)". "Preferred Min. Via hole size: 0.2mm". "0.1mm or 0.15mm hole size with any size via diameter, and 0.2mm or 0.25mm hole size with via diameter less than 0.45mm, will cost more." So the current ≥ 0.3 mm drill is the no-surcharge choice; 0.2 mm drill with ≥ 0.45 mm pad is also free. PTH annular ring, multilayer 1 oz: recommended 0.20 mm, absolute minimum 0.15 mm. Inner-layer via-hole-to-copper clearance 0.2 mm.
- **Via-in-pad / filled vias:** "Epoxy Filled & Capped" or "Copper paste Filled&Capped": "This process is the default for 6-layer and above multilayer boards." Via diameters 0.15–0.55 mm. This explains why the quote UI pre-selects "Epoxy Filled & Capped". It is included, not an add-on (pricing not separately verified here). Consequence: every through-via is filled and plated over, so via-in-pad and vias near fingers or pads are no problem. Tented vs. plugged no longer matters.
- **Blind/buried:** HDI "Currently support (1-step / 2-step / 3-step)". Laser blind 0.075–0.15 mm; mechanical buried 0.15–0.55 mm (epoxy filled & capped); HDI trace/space 3/3 mil. Separate (costly) HDI product, not needed here.
- **Surface finish:** "FR-4/HDI boards with 6 or more layers … do not support HASL", so 6L means ENIG anyway (already the plan for gold fingers).
- Outer copper (multilayer): 1 oz / 2 oz; inner 0.5 / 1 / 2 oz (0.5 oz default). Impedance tolerance ±10 %. Capabilities FR-4 Dk table: 7628 4.4, 3313 4.1, 2116 4.16 (matches S2).

## Unverified / caveats

- The S1 `fixedFee 200 / coefficient 50` on JLC06081H-7628 and -1080: meaning and units are not shown. It is probably a surcharge for non-standard laminate. Check in the quote UI.
- S1 and S2 differ by about 8 µm on a few middle prepregs (noted in the table). The values that matter for USB (L1–L2) agree exactly.
- Impedance numbers come from JLC's SI9000 backend called directly, not from a screenshot of the web UI. Before ordering, re-run "DiffEdgeCoupledCoatedMicrostrip, L1, ref L2" in https://jlcpcb.com/pcb-impedance-calculator (6L / 0.8 / 1 oz / 0.5 oz → JLC06081H-2116, W 0.15, S 0.13) as a 1-minute cross-check.
- Pricing of the 6L 0.8 mm board vs 4L was not checked.
