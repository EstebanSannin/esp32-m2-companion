# v2.0 Rev A — release-candidate design review (2026-10-28)

Independent multi-agent review (owner-requested): 6 reviewers, one per area, each finding then challenged by a separate skeptic that tried to refute it from the primary sources (SKiDL blocks, board file via KiCad python, datasheets, JLC library data, the dev carrier repo). Read-only; nothing was changed.

**Result: 59 findings survived verification — 1 blocker, 2 major, 32 minor, 24 info** (1 info finding left *uncertain* by its skeptic). Severity below is the skeptic's corrected severity. Known items given to the reviewers beforehand: K1 eFuse inrush (DVDT open), K2 side-view LED fix unverified, K3 bottom-side rotation sign guessed, K4 SSM6N56FE stock, K5 carrier contract gaps CG1–CG8.

## Index

| Id | Severity | Verdict | Finding |
|---|---|---|---|
| [dfm-1](#dfm-1) | blocker | confirmed | Bottom-side CPL rotations: offsets from the library comparison are very likely 180° wrong for U4, U5, Q1–Q3, probably also U6 and U3 |
| [contract_test-1](#contract_test-1) | major | confirmed | EXP bus turns on ~9 ms before the ESP32 leaves reset: power-up pin glitches reach the carrier, and the 'high-Z until EEPROM' promise is false in hardware |
| [power-1](#power-1) | major | confirmed | OVLO hysteresis means any overvoltage trip keeps the card off on a nominal 3.3 V host until the slot is power-cycled; the OVLO pin has no filter, so microsecond spikes trip it |
| [contract_test-10](#contract_test-10) | minor | confirmed | Risk register (docs/risks.md) misses several open v2 risks |
| [contract_test-2](#contract_test-2) | minor | confirmed | No v2 firmware exists; S-v2-1/S-v2-2 and the W_DISABLE2#/LED_1#/WAKE# functions cannot be validated when boards arrive |
| [contract_test-3](#contract_test-3) | minor | confirmed | Contract §5 rules contradict the EXP bus, and the bus has no electrical spec (drive, max voltage, speed, ESD) |
| [contract_test-4](#contract_test-4) | minor | confirmed | Carrier-contract gaps CG1-CG8 are all still open, but the design answers most of them; numbers to put in the contract |
| [contract_test-5](#contract_test-5) | minor | confirmed | S-v2-1..4 cannot all be executed as written with the dev carrier and the listed hosts; no v2 test procedure exists yet |
| [contract_test-6](#contract_test-6) | minor | confirmed | IO38 is hard-wired to EXP_OE with no series resistor: firmware can fight the carrier-detect FET |
| [contract_test-7](#contract_test-7) | minor | confirmed | Single-source new silicon, and the documented U6 alternate is not drop-in (latch-off circuit breaker) |
| [contract_test-8](#contract_test-8) | minor | confirmed | Contract is not self-contained or internally consistent on the EEPROM format and firmware-dependent promises |
| [contract_test-9](#contract_test-9) | minor | confirmed | DATASHEET.md is stale and inaccurate in places for v2 |
| [dfm-2](#dfm-2) | minor | confirmed | The committed v2 assembly/fab drawing is a stale build and contradicts the order settings |
| [dfm-3](#dfm-3) | minor | confirmed | 0.4 mm-pitch UQFN and RPW parts have 0.1 mm solder-mask dams, and the mask colour is not specified |
| [dfm-4](#dfm-4) | minor | confirmed | The Rev B 'verified' offsets in JLC_ROT include a JLC correction, not a calibration (U1) |
| [expansion-1](#expansion-1) | minor | confirmed | Carrier detect enables the bus in a normal host whenever a host-side load pulls CONFIG_2/3 low (pull-up to an unpowered rail, SoC default pull-down, GPIO driven low) |
| [expansion-2](#expansion-2) | minor | confirmed | IO38 is wired straight to EXP_OE: firmware driving it push-pull high fights Q1 (about 40 mA); its useful output-low 'kill' behaviour is not documented |
| [expansion-3](#expansion-3) | minor | confirmed | Contract contradicts itself: §4.3 offers UART/SPI/digital inputs from the carrier, but §5 rules 1 and 3 forbid carriers from driving any card pin high; state 6 is identical to a Telit FN990 |
| [expansion-4](#expansion-4) | minor | confirmed | No I2C speed or bus-capacitance budget for the EXP_0/EXP_1 bus with the card's fixed 4.7 kOhm pull-ups |
| [expansion-7](#expansion-7) | minor | confirmed | No ESD rule for carriers that bring EXP lines off-board; card-side protection is chip-level only (TMUX1511 HBM ±2 kV) |
| [layout-1](#layout-1) | minor | confirmed | Unprotected host +3V3 on fingers 2/4 reaches the eFuse only through ~0.23 Ω of 0.127 mm tracks (some on 0.5 oz inner layers) |
| [layout-2](#layout-2) | minor | confirmed | eFuse OUT node (+3V3_EFUSE) has no local capacitor; the first capacitor sits behind ferrite FB1 |
| [layout-3](#layout-3) | minor | confirmed | GND pour fills the gaps between gold fingers 69/71/73 and 3/5 on F.Cu, contrary to the GATE V3 claim of no copper between fingers |
| [layout-4](#layout-4) | minor | confirmed | Sparse GND stitching: 7 GND fingers share 2 vias, and outer pours run up to 7 mm from any GND via |
| [mcu_io-1](#mcu_io-1) | minor | confirmed | W_DISABLE2# card pull-up R29 = 1 MOhm is outside the M.2 spec range (100-200 kOhm); the docs wrongly say it follows the spec |
| [mcu_io-2](#mcu_io-2) | minor | confirmed | Q3a gate sits directly on edge finger 26 with no ESD clamp; the SSM6N56FE has no ESD rating and no gate protection |
| [mcu_io-3](#mcu_io-3) | minor | confirmed | BOOT leg on M.2 pin 20 (GPIO_5/AUDIO_0, 1.8 V) contradicts ADR 0006 sec. 4 and is missing from the risk register |
| [mcu_io-5](#mcu_io-5) | minor | confirmed | SI1024X second source (K4): no datasheet in the repo, pinout and limits only asserted in a code comment, and no JLC_ROT entry |
| [mcu_io-6](#mcu_io-6) | minor | confirmed | WAKE_ON_WWAN# cannot wake a host that holds PERST# low while asleep; the contract does not say so |
| [mcu_io-7](#mcu_io-7) | minor | confirmed | The v2 bring-up plan does not exercise the W_DISABLE2#/IO40 input or the 1.8 V host levels on the new host-facing cells |
| [power-2](#power-2) | minor | confirmed | The approved eFuse second source TPS259474LRPWR is not a drop-in: it is a latch-off circuit breaker, and with ITIMER open any overload above 0.85 A latches the card off |
| [power-3](#power-3) | minor | confirmed | K1 extended: M.2 lets hosts soft-start the slot at 200 mA; how to size CdVdt over IdVdt tolerance, its voltage rating, and the OVLO-recovery restart that skips dVdt |
| [power-4](#power-4) | minor | confirmed | No capacitor at the eFuse OUT pin: +3V3_EFUSE connects straight into ferrite FB1, against TI's '≥1 uF close to OUT' guidance |
| [power-5](#power-5) | minor | confirmed | Drop budget leaves out socket contacts and copper, and J3 (Qwiic +3V3 out) has no current budget against the 0.85 A limit |
| [power-6](#power-6) | minor | confirmed | Stale or inconsistent power documentation |
| [contract_test-11](#contract_test-11) | info | confirmed | Lifecycle: ESP32-S3R2 die is EOL (upgraded to S3RH2); SSM6N56FE stock collapse is unexplained |
| [contract_test-12](#contract_test-12) | info | confirmed | Product markings and access: decide before ordering |
| [dfm-5](#dfm-5) | info | confirmed | The documented second-source swap for Q1–Q3 bypasses the fab tooling |
| [dfm-6](#dfm-6) | info | confirmed | About 30 vias sit fully or partly inside SMD pads, including 0.2 mm UQFN pads, so filled-and-capped vias are mandatory |
| [dfm-7](#dfm-7) | info | confirmed | Small inconsistencies in the fab package and docs |
| [dfm-8](#dfm-8) | info | confirmed | RSV stencil area ratio is marginal |
| [expansion-5](#expansion-5) | info | confirmed | Bus stays enabled across ESP32 resets (PERST#/RESET button, WDT, brown-out, SW reset); the 'glitches are harmless because the bus is off at power-up' argument covers cold power-up only |
| [expansion-6](#expansion-6) | info | confirmed | Enable and disable timing not stated; IO38 reports 'on' ~10 ms after the switches already conduct |
| [expansion-8](#expansion-8) | info | confirmed | CONFIG_2/3 are not 'NC' on the card: the 1 MOhm to 3.3 V lifts host 1.8 V nets slightly and back-feeds an unpowered card rail (docstring/ADR say 'no back-feed') |
| [expansion-9](#expansion-9) | info | confirmed | Floating-host case (e.g. Mallow, pins 1/75 NC) depends on gate leakage and board leakage at a 1.1 MOhm node, which are specified only at 25 C |
| [layout-10](#layout-10) | info | confirmed | Low-risk margins: copper to the V-cut long edges, broadside coupling between In2 and In3, router artifacts |
| [layout-5](#layout-5) | info | confirmed | Finished 6-layer thickness (0.83 ± 0.10 mm) can exceed the M.2 card-edge thickness of 0.80 ± 0.08 mm |
| [layout-6](#layout-6) | info | confirmed | USB routing does not meet the 'length-matched, referenced to L2 GND' rule; functionally irrelevant at Full Speed |
| [layout-7](#layout-7) | info | confirmed | Bottom parts sit at the limit of M.2's bottom-side component zone (5.20 mm from the card edge); CG1 heights quantified |
| [layout-8](#layout-8) | info | confirmed | Antenna: keep-out matches the WROOM-1 antenna area, but the inner planes surround it on three sides (same as Rev B) |
| [layout-9](#layout-9) | info | confirmed | About 100 pads rely on filled and capped via-in-pad, including the bottom 0.4 mm-pitch UQFN pads, the JST pads and FB1's only +3V3 plane via |
| [mcu_io-10](#mcu_io-10) | info | confirmed | J3/J4 (cabled user connectors) go straight to ESP32 pins: no ESD protection, no TX series resistor |
| [mcu_io-4](#mcu_io-4) | info | confirmed | K3 extended: a wrong JLC rotation sign on Q1-Q3 is electrically harmless, and the checklist text claiming otherwise is wrong |
| [mcu_io-8](#mcu_io-8) | info | confirmed | USB pair: no series R is fine (same as Rev B 0R), but the 'length-matched' and '90 Ohm' claims do not hold for the new In2 route |
| [mcu_io-9](#mcu_io-9) | info | confirmed | The N16R8 'drop-in fallback' is limited to 65 °C ambient |
| [power-10](#power-10) | info | confirmed | Fingers 2 and 4 contribute almost nothing: they reach U6 through a ~0.2 Ω 5-mil trace, and R31's OVLO sense pad sits in that path |
| [power-7](#power-7) | info | uncertain | Reverse-current blocking on a noisy host rail can make the card sag below the host rail for tens of microseconds |
| [power-8](#power-8) | info | confirmed | eFuse status cannot be observed or controlled: FLT, AUXOFF, DVDT and ITIMER have no pads or test points, EN is hard-wired, and the host cannot power-cycle the card |
| [power-9](#power-9) | info | confirmed | ILM sense trace runs a long way round on F.Cu near SPI CLK and RXD0 |

## Blocker (1)

<a id="dfm-1"></a>

### dfm-1 — Bottom-side CPL rotations: offsets from the library comparison are very likely 180° wrong for U4, U5, Q1–Q3, probably also U6 and U3

Reviewer severity **blocker**, skeptic: **confirmed / blocker**, reviewer confidence medium.

**Evidence.** KiCad pos-export rotation equals the footprint orientation: Q1 is at 180 in KiCad and 270 in the CPL with JLC_ROT +90; D3 is at 90 with +0. The EasyEDA/JLC library footprints, from the easyeda.com components API, relative to ours (y down, KiCad's counter-clockwise sense):
- C12743 BAT54A: pin 1 at (+1.235,+0.95), pin 3 at (-1.235,0). KiCad SOT-23 has pin 1 at (-0.94,-0.95), pin 3 at (+0.94,0), so the library is ours rotated 180°.
- C7519 USBLC6: library = ours rotated +90°.
- C2673275 TMUX1511: library pin 1 at (-0.6,+0.768), bottom row; ours pin 1 at (-0.8,-0.6), left column. Library = ours rotated +90°: the map (x,y)→(y,-x) lands every pad.
- C146449 SSM6N56FE: library = ours rotated +90°. The second source C86784 has the same orientation.
- C3662799 TPS259470A: library = ours, pin 1 top-left.
- C273616/C273612 LEDs: library lens toward -y with cathode '-' on pad 1 at -x; ours has lens toward +y with cathode on pad 1 at +x. Library = ours rotated 180°, same handedness.

Rev B outcomes (git v1.0-revB fab CPL, docs/review-findings.md GATE B3):
- D1/D2 were bottom, CPL 0, pin 1 correct.
- LEDs at KiCad 90: CPL 90 (v1) gave the lens toward the edge; CPL 270 (Rev B) gave the lens inward.
- U1 was at CPL 0, which does not fit JLC's library at all, so JLC must have re-rotated it.

Only one simple model reproduces D1 (with no correction) and both LED results: JLC mirrors bottom library parts about the vertical axis (the checklist's own 'E/W swap'), while KiCad flips about the horizontal axis. Under it the correct bottom CPL is the KiCad rotation + library rotation + 180°.

Predictions vs the current CPL:
| Part | Model | Current CPL |
|---|---|---|
| D1 | 0 | 0 (agrees) |
| D3/D4 | 90 | 90 (agrees) |
| U3 | 0 | 180 |
| U4, U5 | 90 | 270 |
| Q1–Q3 | 90 | 270 |
| U6 | 0 | 180 |
| U1 | 270 | 0 |

Check with U4: at CPL 270, JLC's pin 1 lands at local (-0.77,+0.6); the board pin 1 is at (+0.75,-0.60), the NE corner, which is diametrically opposite. The alternative mirror model, which only fits D1 if JLC corrected it by hand, still gives 90 for U4, U5 and Q1–Q3; it gives U3 = 180 and U6 = 0.

All these land patterns are symmetric under 180°:
- RSV: only the pin-1 pad is 0.1 mm longer.
- RPW: pads 5/6 are both 0.3x2.4 and the corner L-pads are point-symmetric.
- SOT-563: fully symmetric.

**Why it matters.** A 180° error on a 180°-symmetric land pattern seats perfectly, so neither the placement machine nor the solder joints reveal it.
- U3–U5: pin 8 (GND) and pin 16 (VDD) swap. +3V3 drives the IC's GND pin through its substrate/ESD path, the three switches die and the +3V3 rail is loaded until the eFuse current-limits.
- U6: IN (pad 5) and OUT (pad 6) swap, and EN/OVLO/ILM go to the wrong nets, so the card does not power up correctly.
- Q1–Q3: the two channels swap; CONFIG/LED/WAKE functions are crossed.

fab/README.md and docs/v2-gate-v4.md call U6 'high confidence (sign-free)', so U6 is the row least likely to get scrutiny in the final DFM.

**Recommendation.** Before ordering:
1. Change JLC_ROT: C2673275 → 270, C146449 → 270, C3662799 → 180. Optionally set C7519 → 270 so U1 needs no JLC correction. Keep C12743 at 0 and the LEDs at 0, which the same model confirms.
2. Regenerate, and check that the CPL reads U3 0, U4/U5 90, Q1–Q3 90, U6 0.
3. Add an order remark: 'Bottom side: U3–U6, Q1–Q3 pin 1 per silkscreen dot. Please confirm against our silk, do not rely on CPL.'
4. In the final DFM, check the N/S position of pin 1 for U6 as rigorously as for U3–U5. The current checklist rows (U3 pin 1 S, U4/U5/U6/Q pin 1 N) are correct and are the authority.
5. Record in gen_fab.py the rule 'bottom offset = library rotation + 180°' rather than reusing top-side reasoning.

**Skeptic.** I tried to refute this from the board, the CPL, JLC's own library data and the project's two JLC builds. It survives for U4, U5 and Q1-Q3 under every bottom-side model that fits the project's history. It survives for U3 and U6 under the model that fits best.

**The project's formula.** gen_fab.py:154 writes CPL = KiCad orientation + JLC_ROT offset, with no term for bottom-side mirroring. KiCad shows a bottom part as its footprint mirrored about the horizontal axis and then rotated by K. D1 at K=0 has pad 1 at (-0.938, +0.95), where the top-side footprint has it at -0.95.

**Library footprints.** I fetched them from the easyeda.com API, and the reviewer's coordinates are exact:
- RSV, SOT-563 (both C146449 and C86784) and SOT-23-6 are our footprint rotated +90° counter-clockwise.
- C12743 (BAT54A) and the LEDs are our footprint rotated 180°.
- RPW is identical to ours.

**Candidate models for JLC's bottom transform.** Four candidates: two mirror axes, each with a CW or CCW rotation sense.
- Model A: mirror left-right, then rotate CCW.
- Model B-CW: mirror top-bottom, then rotate CW. This equals A(180-θ).
- The usual 'view from the bottom' formula, 180 - K + correction.
- The project's implicit model (mirror top-bottom, rotate CCW).

**Calibration against JLC history.**
- v1: JLC's automatic preview at CPL 90 put '+' on the chip-side pad. Both v1 boards were built reversed (leds/LESSONS.md:4-27). Only A and B-CW reproduce this. The view-from-bottom formula and the project's model both predict correct polarity at CPL 90.
- Rev B: CPL 270 gave correct polarity with the lens inward (review-findings GATE B3). This also fits A and B-CW.

**What A and B-CW predict.** They agree on ±90 cases. For U4/U5 (K=180, library +90) and Q1-Q3, both require CPL 90; the CPL has 270.
- U4 check: library pin 1 (-0.6, 0.768), mirrored to (0.6, 0.768).
- At R(90) it lands at (0.768, -0.6), which matches board pad 1 at (0.75, -0.60).
- At R(270) it lands at (-0.77, 0.6), the opposite corner.

**U3 and U6.** For U3 (K=90) and U6 (K=180, library = ours), A gives 0 and B-CW gives 180 (the current value). Three things favour A:
- D1 at CPL 0 came out correct with no recorded JLC correction.
- The project itself says JLC's bottom preview mirrors E/W (polarity_report.py:17,140), which is A's mirror axis.
- B-CW needs a top-bottom mirror.

**Silent failure.** The land patterns barely change under 180°:
- RSV: only pad 1 differs, 0.7 mm long against 0.6 mm (footprint line 13).
- RPW: point-symmetric, including the L-shaped corner pads (lines 21-48).
- SOT-563: fully symmetric.

A 180° error therefore seats with no visible misfit. On U3-U5 it swaps pin 8 (GND) with pin 16 (+3V3); on U6 it swaps pad 5 (+3V3_M2) with pad 6 (+3V3_EFUSE).

**Severity.** The mitigation is real: polarity_checklist.md has the correct N/S corners, and a 180° error flips N/S, so a diligent final-DFM check catches it. The CPL itself is still wrong for 5 to 8 power-path parts, so I keep blocker.

**What would settle U3/U6 (A versus B-CW):** ask JLC which mirror axis its bottom rotation uses, or check U3/U6 pin 1 N/S in their final DFM.

## Major (2)

<a id="contract_test-1"></a>

### contract_test-1 — EXP bus turns on ~9 ms before the ESP32 leaves reset: power-up pin glitches reach the carrier, and the 'high-Z until EEPROM' promise is false in hardware

Reviewer severity **major**, skeptic: **confirmed / major**, reviewer confidence medium.

**Evidence.** edge_expansion.py:86-91: EXP_OE = R26 10k to 3V3 plus C13 1uF (tau 10 ms). The final value is ~3.0-3.25 V because of the 12 SEL loads. Crossing TMUX1511 VIH 1.2 V (tmux1511.pdf §5.5, line 327) takes t = 10 ms x ln(1/(1-1.2/3.25)) = 4.6 ms (5.1 ms worst case). EN = R1 10k / C5 1uF (sideband_recovery.py:23,35,38). CHIP_PU releases at VIH_nRST 0.75 x VDD (esp32-s3_datasheet Table 5-x, txt line 3710): 10 ms x ln4 = 13.9 ms. So the switches are ON for ~9 ms while the MCU is still in reset, and then through ROM boot. ESP32-S3 DS v2.2 Table 2-2 lists 'power-up glitches' of ~60 us: an actively driven low on GPIO1, 2, 4-7, 15, 16 and 17, which are EXP_2, 3, 5-8, 9, 10 and 11, and a low then a high-level glitch on GPIO18 = EXP_4. They pass through RN 220R plus the closed TMUX1511 onto M.2 pins 34, 36, 40 and 59-65. CHIP_PU low 'disables the chip (powered down)' (DS line 1436), so I infer that every PERST#/esptool/BOOT reset is also a chip power-up while EXP_OE stays high: OE depends only on CONFIG_2/3 and +3V3. docs/pinmap.md:261 justifies the IO18 choice with 'the bus switch is off during power-up (§6.3 RC)', but pinmap has no §6.3. docs/v2-gate-v1.md §1.1 'Timing' only argues that the rails are stable. carrier-interface.md §4.3 promises EXP_2..11 'stay high-Z until a valid EEPROM is read'. Confidence is medium only on exactly when the Table 2-2 glitch happens (VDD ramp or CHIP_PU release); the OE-before-CHIP_PU ordering is computed.

**Why it matters.** Carriers following the contract may hang edge-sensitive loads on EXP lines: an interrupt to a carrier MCU, SPI CS/clock, a UART RX (sees a break), counters, SSR/MOSFET loads on EXP_4, which gets a 60 us high pulse. Firmware cannot suppress this. Fixing it after the order needs a layout respin. A carrier ecosystem built on a wrong 'high-Z until firmware decides' promise is hard to walk back.

**Recommendation.** Owner decision before ordering. (a) Best: make firmware consent part of the gate, using the unused Q3b half. Today the netlist ties its gate to GND (host_sideband.py:39) and leaves its drain NC. Change it to drain = EXP_OE, gate pulled up to 3V3 (~100k) and driven by IO38. IO38 is IE-only at reset, so the bus is held off through every reset and ROM boot; firmware drives IO38 low only after init. The hardware carrier-detect safety (Q1) is unchanged, but the EXP_OE readback is lost (the EEPROM ACK can replace it), and G8's 'independent of firmware' wording becomes 'enable needs carrier AND firmware'. (b) BOM-only partial fix: C13 = 4.7 uF puts OE at ~22 ms vs CHIP_PU at 13.9 ms. This covers cold power-up only, not host resets, and the margin is eaten by X5R DC-bias derating. (c) At minimum, correct pinmap §6.1, fix the dangling §6.3 reference and state in contract §4.3 that EXP_2..11 can carry ~60 us glitches, with EXP_4 able to glitch high, on every card reset. Whatever is chosen, scope EXP_4 and EXP_5 against PERST# at bring-up (add this to S-v2-2).

**Skeptic.** The ordering holds. EXP_OE is R26 10k to +3V3 plus C13 1 uF. The 12 TMUX1511 SEL pins each have an internal 6 MOhm pull-down, about 500k in parallel, so the final value is about 3.24 V. EXP_OE crosses VIH 1.2 V at about 4.6 ms (10 ms x ln(3.24/2.04)). EN (R1 10k / C5 1 uF) reaches VIH_nRST = 0.75 x VDD at 13.9 ms (10 ms x ln 4). On a carrier, Q1 is off because CONFIG_2/3 are grounded, so the switches are on for about 9 ms before CHIP_PU releases. SEL high = ON (tmux1511 pin table). ESP32-S3 DS v2.2 Table 2-2 lists 60 us actively driven low glitches on GPIO1-17 and a low then a high glitch on GPIO18. pinmap.md:259-261 relies on 'bus switch is off during power-up (§6.3 RC)', but pinmap has no §6.3 (it ends at §6.2), and the RC actually turns the bus on before the MCU. carrier-interface.md §4.3 promises EXP_2..11 'stay high-Z until a valid EEPROM is read', which ROM-time glitches contradict. Still open: whether the glitches also occur on a CHIP_PU-only reset (PERST#/esptool), as opposed to a VDD ramp. A scope capture of EXP_4 against EN would settle that. Kept major because the stated design rationale is false, and a hardware hold-off needs a layout change. It only matters on carriers with edge-sensitive loads.

<a id="power-1"></a>

### power-1 — OVLO hysteresis means any overvoltage trip keeps the card off on a nominal 3.3 V host until the slot is power-cycled; the OVLO pin has no filter, so microsecond spikes trip it

Reviewer severity **major**, skeptic: **confirmed / major**, reviewer confidence high.

**Evidence.** Datasheet §7.3.3 (p.26-27): after a trip the device 'wait[s] for the voltage at the OVLO pin to fall below the OVLO falling threshold VOV(F)'. EC table: VOV(F) is 1.076/1.09/1.116 V and VOV(R) is 1.183/1.20/1.223 V. tOVLO is 1.2 us and the comparator has no deglitch. The divider R31/R32 (power_3v3.py:48-57) gives a ratio of 152.3/52.3 = 2.912. Trip level is 3.437-3.570 V (including 0.1 % and ±0.1 uA x 34.3 kΩ). Release level is 1.076-1.116 V x 2.912 = 3.133-3.250 V. At a nominal 3.30 V the OVLO pin sits at 1.133 V, above the maximum VOV(F) of 1.116 V, so no part re-enables while the host is at or above 3.25 V. A typical part needs the host below 3.17 V, and a low-threshold part needs it below 3.133 V, which is below the M.2 minimum of 3.135 V. Trip margin above nominal is only 137 mV. The EFUSE_OVLO node is 34.3 kΩ Thevenin with no capacitor; the netlist has only R31, R32 and U6.2. Two plausible trip sources: (a) hot-plug or power-switch ringing of C14 (100 nF, the only input capacitance) against connector and host inductance, which can reach about 2 x VIN; (b) the inductive input spike when U6 fast-trips at 2 x ILIM (§8.3.1 Eq.24: 3.3 V + 2.3 A x sqrt(L/C), about 4.9 V for 50 nH and 100 nF). The documents describe this as self-healing: SPEC.md:262-263 'auto-recovers below ~3.17 V', carrier-interface.md:61, S-v2-3 'recovers below ~3.17 V'. The dev-carrier bring-up plan (bringup.md §3, §7) only records a release voltage and never checks behaviour after a trip with the rail back at 3.3 V.

**Why it matters.** A single overshoot on a legitimate host makes the card vanish (no USB, no EXP bus) until the whole slot is power-cycled. The host cannot do that for the card alone: EN is tied to IN through 1 MΩ and pin 6 FULL_CARD_POWER_OFF# is NC. The firmware cannot tell what happened because FLT is NC, and FLT does not assert on OVLO anyway (Table 7-3). Hosts with a rail set at 3.35-3.40 V plus load-release overshoot (for example when the card's own ~0.35 A TX bursts end) sit within 50-100 mV of the low end of the trip window.

**Recommendation.** Before ordering: add a 1 nF C0G capacitor (rated 25 V or more) from EFUSE_OVLO to GND next to R32 (B.Cu, about 93.7,143.0). τ = 34 us, which attenuates MHz ringing about 300 times. For a hard 3.3 V to 5 V step the trip delay is 0.12τ, about 4.2 us. Behind the fast-trip and current limit (≤ 1.15 A into ≥ 43 uF effective) the rail rises about 0.11 V, so it stays below 3.6 V. Do not go above about 2.2 nF (about 9 us delay, about 0.24 V rise). Correct SPEC A3 G11, S-v2-3, ADR 0007 and carrier-interface §3 to say that recovery needs the host rail below 3.13-3.25 V, which in practice means a slot power cycle. Add a bring-up step: trip at about 3.5 V, return to 3.30 V, and confirm (and document) that the card stays off. Scope EFUSE_OVLO during a dev-carrier JP1 hot-connect.

**Skeptic.** I checked the hysteresis arithmetic and it holds. The divider ratio is (100k+52.3k)/52.3k = 2.912. VOV(F) of 1.076/1.09/1.116 V gives a release level of 3.133/3.174/3.250 V. At 3.30 V the OVLO pin sits at 1.133 V, which is above the maximum VOV(F), so after any trip no part re-enables on a nominal host. A typical part needs the rail below about 3.17 V, which is below most real 3.3 V rails. SPEC and ADR say "auto-recovers below ~3.17 V". That is literally true, but they never state the consequence, which is that the card stays off at 3.3 V until the slot is power-cycled. EFUSE_OVLO has no capacitor: its only members are R31.2, R32.1 and U6.2. The datasheet gives tOVLO = 1.2 us and describes no deglitch. Two points add to the finding. First, ADR 0007 accepts that a low-threshold part trips at 3.445 V on a host still within spec (up to 3.465 V), and such a unit would then never come back even after the host settles. Second, on a hot-connect U6 is not yet running when the first overshoot peak arrives, so an overshoot above 3.45 V latches the OV state from the start. What is not proven is that real hosts produce such transients: the ringing and fast-trip spike scenarios have not been measured. I keep it at major because the failure is plausible on adapters and benches and the fix is a cheap 1 nF footprint. If a scope on dev-carrier hot-connects shows no overshoot, it would drop to minor (documentation only).

## Minor (32)

<a id="contract_test-10"></a>

### contract_test-10 — Risk register (docs/risks.md) misses several open v2 risks

Reviewer severity **minor**, skeptic: **confirmed / minor**, reviewer confidence high.

**Evidence.** The R-v2 table (risks.md, 'state 2026-10-10') has no entry for: K1 eFuse inrush near ILIM, plus the OVLO-recovery current-limited start (tps25947 §7.3.3); K2 D3/D4 side-view LED footprint renumbered with CPL +0 unconfirmed (R-v2-7 covers only U3-U5/Q1-Q3); missing v2 firmware (contract_test-2); EXP power-up glitches (contract_test-1); the TMUX1511 single source; the ESP32-S3R2 die EOL; or the S-v2-1 laptop test vs R11 height. R10 (W_DISABLE1# held low forces download mode) still applies to v2 but sits in the v1 table. The top table header still reads 'updated 2026-10-06, v1.0 Rev B'.

**Why it matters.** The register is meant to be the owner's checklist at the order decision. Known risks missing from it get dropped.

**Recommendation.** Add R-v2-8..R-v2-13 for the items above with owner and mitigation, carry R10/R11 forward explicitly for v2, and update the dates.

**Skeptic.** The risks.md R-v2 table (state 2026-10-10) lists R-v2-1..7 only. grep for inrush/dvdt/firmware/glitch/D3/TMUX/EOL in risks.md returns nothing. R-v2-7 covers only U3-U5/Q1-Q3 rotation, not D3/D4. The top table header reads 'updated 2026-10-06, v1.0 Rev B'.

<a id="contract_test-2"></a>

### contract_test-2 — No v2 firmware exists; S-v2-1/S-v2-2 and the W_DISABLE2#/LED_1#/WAKE# functions cannot be validated when boards arrive

Reviewer severity **major**, skeptic: **confirmed / minor**, reviewer confidence high.

**Evidence.** <workspace>/esp32-m2-companion/firmware is an empty directory, and the v2 worktree has no firmware/. `git ls-tree -r main` shows no firmware files. A grep across ~/code finds EXP_OE/M2CI only in docs and hardware. SPEC §7 requires an ESP-IDF project in firmware/, and SPEC §9 Phase 4 says 'Firmware ready before boards arrive'. v1/Rev B validation used MicroPython ESP32_GENERIC_S3 and Aktualino (docs/bringup.md:8, :52). S-v2-2 requires 'every EXP line proven both ways by a firmware self-test'. The dev carrier's own plan relies on firmware: bringup.md §7 says 'firmware reports EXP_OE on', and its SPEC:224 says switch-off proof is 'firmware reading EXP_OE over USB'. Host-facing functions all depend on firmware: IO40 = W_DISABLE2# inverted (Q3a drain with R30 10k), IO42 → LED_1#, IO47 → WAKE#.

**Why it matters.** Without firmware, two of the four acceptance criteria and the contract's radio-kill promise (§4.4 'pull low = radio off') cannot be demonstrated. The release decision for the 100-unit run would rest on untested behaviour.

**Recommendation.** Before the boards arrive, write a minimal firmware (ESP-IDF or MicroPython) covering: (1) QUAD PSRAM build (CONFIG_SPIRAM_MODE_QUAD, 80 MHz), since octal builds boot-loop on N8R2 (memory/bringup log). Also confirm the ESP-IDF version supports chip rev v0.2 / S3RH2 silicon. (2) IO38 read-only EXP_OE readback reported over the CDC console. (3) After OE goes high, I2C on IO39 (SDA) / IO41 (SCL) only, 24C02 at 0x50: read 256 B, check the 'M2CI' magic and CRC-32 over 0x00..0xFB, apply the function map, refuse impossible functions (ADC only on EXP_2, 3, 5-8), and keep everything else high-Z otherwise. (4) W_DISABLE2#: IO40 high means the host asserted kill, so stop WiFi/BLE, with a stated latency. (5) LED_1# on IO42 and WAKE# on IO47 as outputs (high = asserted low on the edge). (6) Never enable the external 32 kHz crystal: IO15/IO16 are EXP_9/10. (7) A loopback self-test command for S-v2-2 with a jumper map for the dev carrier J_EXP. (8) A host-side tool to program and verify the carrier EEPROM (WP jumper, page writes). Record the firmware rules in the contract.

**Skeptic.** There is no firmware anywhere. The v2 worktree has no firmware/, `git ls-tree HEAD` has no firmware paths, and the main checkout's firmware/ is empty (created Aug 28). S-v2-2 explicitly needs a 'firmware self-test'. The finding is real, but it is a process and testability gap: it does not make the ordered boards fail and needs no respin. It can be closed while the boards are in fab. Downgraded to minor under the stated severity scale. It should still be tracked as a precondition for signing off the release candidate.

<a id="contract_test-3"></a>

### contract_test-3 — Contract §5 rules contradict the EXP bus, and the bus has no electrical spec (drive, max voltage, speed, ESD)

Reviewer severity **minor**, skeptic: **confirmed / minor**, reviewer confidence high.

**Evidence.** carrier-interface.md §5 rule 1: 'Carrier → card signals are open-drain only (pull low, never drive high)'. Rule 3: 'Never drive 3.3 V onto any card pin'. §4.3, by contrast, says EXP is 'bidirectional', for 'GPIO, UART, SPI', with 0x09/0x0A UART RX and SPI MISO in the EEPROM function codes (v2-gate-v1.md §2), all of which need carrier push-pull drive. Missing specs: (a) Output impedance: 220R (RN1-3) + Ron ≤ 4.5 Ω (tmux1511 §5.5) + ESP driver, about 250 Ω total. VOH drops ~0.22 V at 1 mA, and the short-circuit current is ~13 mA. (b) The TMUX1511 passes VS up to 2 x VDD, max 5.5 V, when ON (tmux line 16-17, 288-293). A 5 V carrier signal reaches the ESP pin through ~225 Ω, putting ~5-7 mA into its clamp. (c) No max signalling rate: 225 Ω x (6 pF CON + carrier C) gives tau ~5-10 ns. (d) Exposed carrier headers have no ESD rule. The dev carrier SPEC says 'no protection on EXP header'. (e) The required level for 'grounded' on CONFIG_2/3 is undefined. Q1 Vth min is 0.4 V (ssm6n56fe p.? 'Gate threshold 0.4-1.0 V'), and with the 1 MΩ card pull-up a carrier resistor to GND must be ≤ ~100 kΩ (≤ 0.3 V).

**Why it matters.** Carrier repos @-import this file as normative. Read literally, it forbids SPI/UART peripherals on carriers. Read loosely, it says nothing about 5 V parts or ESD on exposed connectors.

**Recommendation.** Scope rules 1 and 3 to sideband and CONFIG pins. Add an EXP electrical table: logic 0-3.3 V with abs max 3.6 V (the switch passes up to 5.5 V and does not protect the MCU); source impedance ~250 Ω and ≤ 5 mA recommended per line; carrier may drive push-pull only into EXP lines whose EEPROM function is an input; ≤ 2 uA leakage when off or unpowered; recommended max ~10 MHz; carrier ESD protection on any EXP line routed to an external connector; CONFIG_2/3 'grounded' = ≤ 0.1 V or ≤ 10 kΩ to GND.

**Skeptic.** carrier-interface.md §5 rule 1 says carrier-to-card signals are 'open-drain only (pull low, never drive high)', and rule 3 says 'Never drive 3.3 V onto any card pin'. Both literally conflict with the bidirectional EXP bus in §4.3 (UART RX/SPI MISO function codes). TMUX1511 passes signals up to 2 x VDD, max 5.5 V, when on (tmux l.14-17, 288-293), so the card does not block 5 V. Ron is at most 4.5 Ohm. The CONFIG grounding math is correct: V = 3.3 x R/(1M + R) ≤ 0.3 V gives R ≤ 100k. One small correction: the TMUX1511 IPOFF is ≤ 10 nA at VD = 0 (l.306). The 2 µA figure is the SEL/off-leakage class number, not IPOFF.

<a id="contract_test-4"></a>

### contract_test-4 — Carrier-contract gaps CG1-CG8 are all still open, but the design answers most of them; numbers to put in the contract

Reviewer severity **minor**, skeptic: **confirmed / minor**, reviewer confidence high.

**Evidence.** carrier-interface.md has no section for CG1-8 (m2-dev-carrier/docs/contract-gaps.md: all 'open'). Numbers from the design: CG1: the tallest bottom-side parts are U1 SOT-23-6 (A max ~1.45 mm) and C1/C2 0805 22 uF CL21A226MAQNNNE (~1.25 ±0.2 mm). Rev B measured 1.55 mm (CG1 note), while DATASHEET.md:78/220 claims ≤ 1.5 mm. CG2: on 2242 the keep-out is 31.4-37.6 mm from the card stop (42 - 10.6 / 42 - 4.4); plus cards are undefined. CG3: the notch is routed with no copper (CLAUDE.md, DATASHEET.md:222); no standoff net is required. CG4: only C14 = 100 nF sits directly on +3V3_M2. Behind U6 are C1+C2+C3+C7 = 64 uF nominal plus 5x100 nF plus the module. With DVDT open, SR = 12.1 V/ms at 2.7 V (tps25947 §6.7) gives ~0.8 A inrush for ~0.25 ms, bounded by ILIM 0.85/1.01/1.15 A (R34 3.3k, RILM = 3334/I). This extends K1: per tps25947 §7.3.3 (txt line 1810), 'While recovering from a OVLO event, the TPS259470x variants bypass the inrush control (dVdt) and start up in a current limited manner'. A DVDT capacitor therefore does not cover OVLO recovery, which always draws up to 1.15 A. The contract's '≥ 1 A' is below ILIM max. CG6: unspecified. CG7, card unpowered with 3.3 V carrier pull-ups: 21/69 are card GND, so 0.33 mA per 10k pull-up, powered or not. 75, 1 and 26 each back-feed the card +3V3 through 1 MΩ (R22, R23, R29), 3.3 uA each. 10/23 see Q2 IDSS ≤ 1 uA. 50/20/8 see reverse-biased BAT54A. Each EXP pin sees IPOFF ≤ 2 uA (tmux line 311). Worst case is ~40 uA total, ~10 uA of it into the card rail. CG8: SSM6N56FE ID 800 mA DC, PD 150 mW, RDS(on) ≤ 300 mΩ at VGS 2.5 V (gate driven at 3.3 V). The SI1024X 2nd source is 1.25 Ω at 1.8 V. CG5 is policy.

**Why it matters.** Every carrier designer needs these, and the dev carrier is running on interim assumptions. Two of them are currently wrong or unstated: the supply sizing (≥ 1 A vs a 1.15 A current-limited restart) and the bottom height (1.5 vs a measured 1.55).

**Recommendation.** Add a 'closed gaps' block to the contract, marked fixed. Bottom parts ≤ 1.6 mm including solder. 2242 antenna keep-out in card-stop coordinates; plus cards TBD. Notch no copper, standoff no net. Input: 0.1 uF direct, ~65 uF behind an eFuse, inrush ≤ 1.15 A for < 0.5 ms (also after every OVP recovery), carrier supply ≥ 1.2 A transient. EEPROM VCC = the same carrier 3.3 V that feeds the card, A2..0 = GND, WP = GND or jumper. Per-pin unpowered behaviour as computed above (≤ 40 uA total, no latch-up path). LED_1#/WAKE# sink ≤ 50 mA, VOL ≤ 0.1 V at 50 mA, pull-up ≤ 3.6 V. A test-fixture exception for OVP testing (CG5). Then mark CG1-8 closed in the dev-carrier repo.

**Skeptic.** All CG1-CG8 entries in contract-gaps.md are 'open', and carrier-interface.md has no section for them. U6 is TPS259470A (common.py:176-194). Datasheet §7.3.3 says the 470x variants bypass dVdt when recovering from OVLO and start current-limited, so a DVDT capacitor (the K1 fix) does not cover OVLO recovery. That is a valid extension of K1. Only C14 100 nF sits on +3V3_M2. Behind the eFuse are C1/C2 22 uF + C3/C7 10 uF = 64 uF nominal, and 64 uF x 12.1 V/ms ≈ 0.77 A. Real X5R DC-bias derating at 3.3 V makes the actual capacitance lower. The contract says 'Design for ≥ 1 A ... eFuse limit is ~1 A' (carrier-interface.md:57-58), below the 1.15 A ILIM maximum. In practice the OVLO case needs more than 3.6 V at the input first, so it is rare.

<a id="contract_test-5"></a>

### contract_test-5 — S-v2-1..4 cannot all be executed as written with the dev carrier and the listed hosts; no v2 test procedure exists yet

Reviewer severity **minor**, skeptic: **confirmed / minor**, reviewer confidence high.

**Evidence.** S-v2-1 (SPEC A3 §10) asks for EXP leakage on 'a laptop WWAN slot' and 'an M.2→USB adapter'. DATASHEET.md:258 and risks R11 say enclosed laptop bays are 'Not compatible' (3.1 mm module), and a USB adapter gives no access to the EXP pins. The dev carrier's bringup.md §7 refers to 'docs/host-safety-test.md', which does not exist in m2-dev-carrier/docs/. The card repo docs/bringup.md is a v1 log with no v2 section. S-v2-2 'both ways' needs a loopback, but J_EXP is a 2x12 header with odd = signal, even = GND (dev-carrier pinmap.md:96-111) and has no loopback scheme. The ID EEPROM is DNP with SJ_SDA/SJ_SCL open (dev-carrier bom.md:45), so the EEPROM path and the firmware rule are untestable as built. S-v2-3: the BENCH limit is '≤ 0.5 A' (bringup.md §7, R8), while the eFuse restarts current-limited at up to 1.15 A after an OVLO event (tps25947 §7.3.3). The recovery step will drive the bench into constant-current mode, and droop may look like a failed recovery. Observable points are fine: +3V3 is on J3 pin 2 (top side), D3 shows +3V3, and EXP_OE is visible only through IO38 firmware.

**Why it matters.** Acceptance criteria that cannot be run cannot be signed off. The release-candidate decision would rest on partial evidence.

**Recommendation.** Rewrite S-v2-1 per host. Measure leakage where pins are accessible (dev carrier J_EXP with JP_SIG2/3 in the open, 1.8 V and 3.3 V positions; Mallow X16; card unpowered via JP1 OFF). On closed hosts (USB adapter, a laptop with the cover off) accept 'IO38 reads 0 and CONFIG_2/3 measured' as the proxy. Write host-safety-test.md and a card-side v2 bring-up checklist now. For S-v2-2, define a Dupont loopback map on J_EXP (pairs EXP_2↔3, 4↔5 ... 10↔11; EXP_0/1 against a populated EEPROM) and hand-fit a 24C02 (C7562) on one dev carrier. For S-v2-3, raise the bench limit to ≥ 1.2 A for the recovery step, or record that droop is expected.

**Skeptic.** S-v2-1 (SPEC.md:296-299) requires tests on a laptop WWAN slot and an M.2-to-USB adapter. DATASHEET.md:258 says enclosed laptop bays are 'Not compatible' (R11), and a USB adapter does not expose the EXP pins. m2-dev-carrier/docs/bringup.md:208 references docs/host-safety-test.md, which does not exist in m2-dev-carrier/docs/. bringup.md:211 uses a ≤ 0.5 A bench limit, while the 470A restarts current-limited after OVLO. The finding stands as a test-plan gap.

<a id="contract_test-6"></a>

### contract_test-6 — IO38 is hard-wired to EXP_OE with no series resistor: firmware can fight the carrier-detect FET

Reviewer severity **minor**, skeptic: **confirmed / minor**, reviewer confidence high.

**Evidence.** design.py:81 '"IO38": exp_oe'. docs/review/v2_reva_connections.md:204 shows U2.31 IO38 directly on EXP_OE with Q1.D1/D2, R26, C13 and the 12 SEL pins. On a non-carrier host Q1 is on (RDS(on) ≤ 480 mΩ). If firmware configures IO38 as an output high (e.g. MicroPython Pin(38, Pin.OUT)), the 20 mA-class driver (DS Table 2-1 note 5) shorts into Q1. The bus still stays off, so safety holds, but the GPIO and FET are overstressed. Driving IO38 low on a carrier silently disables the bus.

**Why it matters.** G8 says the gate is 'independent of firmware'. A firmware bug cannot open the bus, but it can stress parts and produce confusing 'bus off' symptoms on carriers.

**Recommendation.** Either add a 0402 10k-100k in series with IO38 (one resistor, small layout change), or adopt the Q3b firmware-consent gate from contract_test-1, which repurposes IO38. At minimum, make 'IO38 is input-only' a normative firmware rule in the contract and the firmware.

**Skeptic.** IO38 (U2.31) sits directly on EXP_OE together with Q1 D1/D2, R26, C13 and the 12 SEL pins, with no series resistor (connections l.204). A firmware output-high on a non-carrier host would fight the on Q1. This is a short-circuit stress on the GPIO, not a safety loss: the bus stays off because Q1 wins. ESP32 GPIOs usually survive a short like this, but it is out of spec. Driving IO38 low on a carrier disables the bus. Real but low impact. It needs a firmware rule, or a layout change for the resistor.

<a id="contract_test-7"></a>

### contract_test-7 — Single-source new silicon, and the documented U6 alternate is not drop-in (latch-off circuit breaker)

Reviewer severity **minor**, skeptic: **confirmed / minor**, reviewer confidence high.

**Evidence.** docs/v2-gate-v1.md:136 lists 'U6 ... 2nd source TPS259474LRPWR C2864845'. tps25947 §4 comparison table: 474 = 'Circuit Breaker', L suffix = 'Latch-Off'. §7.3.5.2: after the ITIMER interval (ITIMER is open here, so minimal blanking) it turns the HFET off. Pins 3/4 become PG/PGTH instead of AUXOFF/FLT. With K1 inrush of ~0.8 A against ILIM min 0.85 A, a latch-off part could stay off until power is cycled, since EN is tied to IN via R33. docs/review/v2_reva_bom.md has no 2nd source for U6, U3-U5 TMUX1511 (JLC stock 1,013 vs 300 per 100 boards, v2-gate-v4.md §4), RN1-3, R31/R32 (0.1%) or D3/D4.

**Why it matters.** A buyer working from the gate docs could substitute a part that changes the fault behaviour. At 100-unit volume, any single-sourced Extended part can block a build.

**Recommendation.** Strike TPS259474LRPWR from v2-gate-v1.md, or name TPS259474ARPWR (auto-retry) only after checking circuit-breaker behaviour with the inrush; for prototypes U6 has no true 2nd source. Add approved alternates for the 0.1% pair (e.g. Panasonic ERA-2AEB 0402 0.1% 25 ppm) and the 4x0402 array. Record TMUX1511 and the side-view LEDs as single-source in risks.md, with a stock check at order time.

**Skeptic.** The documented 2nd source is in the source, common.py:193 ('2nd source TPS259474LRPWR C2864845'), and it is not drop-in. The 474L is the circuit-breaker, latch-off variant (tps25947 l.152-154). Pins 3/4 become PG/PGTH (Table 5-1), and the design leaves pin 4 unconnected (PGTH is an analog input). Fault recovery also differs. One sub-claim is weak: the circuit breaker trips at IOUT > 1.2 x ILIM after ITIMER (tCB l.559), so a ~0.8 A startup inrush is unlikely to latch it off. The non-drop-in conclusion still holds on pin function and latch-off behaviour. The single-source observations for U3-U5 and the RN/0.1% parts are consistent with the BOM.

<a id="contract_test-8"></a>

### contract_test-8 — Contract is not self-contained or internally consistent on the EEPROM format and firmware-dependent promises

Reviewer severity **minor**, skeptic: **confirmed / minor**, reviewer confidence high.

**Evidence.** carrier-interface.md §4.3 marks the EEPROM 'Fixed (GATE V1)' but defines the format only by reference ('docs/v2-gate-v1.md §2'). That section is still headed 'format v1 (proposed)' (v2-gate-v1.md:85). §5 rule 6 says 'once its format is fixed'. CLAUDE.md requires the contract to be 'self-contained' because carrier repos @-import only this file. The legend still says '*proposed* = to confirm at v2 GATE 1'. §4.4 states W_DISABLE2 'pull low = radio off' and §4.3 states the EXP init rule, but neither says they are firmware behaviour, and no firmware exists (contract_test-2).

**Why it matters.** A carrier session that imports only the contract cannot write a valid EEPROM image, and may treat firmware rules as hardware guarantees.

**Recommendation.** Copy the EEPROM layout and function-code table into the contract and mark them fixed. Update rule 6 and the v2-gate-v1 heading. Tag §4.3's init rule and §4.4's radio-kill as 'firmware ≥ <version>' with latency. Add a contract changelog line per revision so the dev carrier can track the close-out of CG1-8.

**Skeptic.** carrier-interface.md §4.3 marks the EEPROM 'Fixed (GATE V1)' but defers the format to docs/v2-gate-v1.md §2. That heading still reads '## 2. Carrier ID EEPROM — format v1 (proposed)' (line 88, not 85). Rule 6 says 'once its format is fixed'. CLAUDE.md requires the contract to be self-contained. The §4.3/§4.4 firmware behaviours are not tagged as firmware-dependent.

<a id="contract_test-9"></a>

### contract_test-9 — DATASHEET.md is stale and inaccurate in places for v2

Reviewer severity **minor**, skeptic: **confirmed / minor**, reviewer confidence high.

**Evidence.** DATASHEET.md:4 has the revision stamp 'v1.0-revB-27-g947e274-dirty' (generated from a dirty tree two commits behind HEAD a203a10). Lines 161-162 say 'footprints R5/R6 (10 k) can be fitted', but R5/R6 were removed at GATE V3 (review-findings.md:377; io_header.py:17, 53); the same text is in gen_datasheet.py:222. Lines 16-33 (Features) omit the v2 features: 12-line expansion bus, carrier detect, LED_1#/WAKE#/W_DISABLE2#, OVP. The block diagram (line 41) shows only '2x sideband GPIO'. Lines 78/220 claim bottom height '≤1.5 mm' while Rev B measured 1.55 mm (CG1). Line 258, 'Enclosed hosts not compatible', conflicts with S-v2-1's laptop test. There is no note that W_DISABLE1# on pin 8 (R10) and CONFIG state 6 (R-v2-3) can matter on generic hosts.

**Why it matters.** The datasheet is the customer-facing summary of a release candidate. Stale claims about pull-up footprints and height will mislead users and carrier designers.

**Recommendation.** Fix gen_datasheet.py (R5/R6 text, v2 features, block diagram, height '≤ 1.6 mm incl. solder'), and regenerate it from a clean tree on the commit that is ordered.

**Skeptic.** DATASHEET.md:4 stamps 'v1.0-revB-27-g947e274-dirty'. Line 162 says 'footprints R5/R6 (10 k) can be fitted', yet io_header.py:17,53 say v2 removed them, and the same text is in gen_datasheet.py:222. Lines 78/220 say ≤ 1.5 mm. These are documentation defects only.

<a id="dfm-2"></a>

### dfm-2 — The committed v2 assembly/fab drawing is a stale build and contradicts the order settings

Reviewer severity **minor**, skeptic: **confirmed / minor**, reviewer confidence high.

**Evidence.** docs/review/v2_reva_drawings.pdf (committed in 0476277) carries the title-block revision 'v1.0-revB-27-g947e274-dirty', dated 2026-10-13. Sheet 2 says:
- '4 layers SIG/GND/PWR/SIG, stackup JLC04081H-3313'
- 'Vias tented both sides'
- 'min drill 0.30 mm'
- '22 placed parts; DNP R5 R6 C8 C9'
- 'CPL: D3/D4 +180° vs KiCad'

Sheet 1's legend lists DNP R5/R6/C8/C9 and TP1-6. It gives pin numbers only for the legacy parts; there are no pin-1 marks for U3–U6, Q1–Q3 or RN1–RN3.

The actual v2 package is 6 layers JLC06081H-2116, epoxy filled and capped vias, 0.2 mm vias, 50 placed parts, no DNP, and LED offset +0.

**Why it matters.** This is the human-readable artifact the owner or JLC engineers would consult during the final DFM. It contradicts the CPL on exactly the items under dispute: the LED offset (K2) and the pin 1 of the new bottom ICs (dfm-1). CLAUDE.md also requires regenerating the drawings before pushing a revision.

**Recommendation.** Rerun `make drawings` on the final commit. Have gen_drawings.py take the layer count, stackup, via finish, DNP list and JLC_ROT from the board, BOM and gen_fab rather than constants. Add pin-1 and pad-number marks for U3–U6, Q1–Q3 and RN1–RN3 on the bottom view.

**Skeptic.** pdftotext of the committed drawing shows all the stale items the reviewer quotes. The drawing was last committed in 0476277, but its content still describes the Rev B 4-layer design.

The actual package differs on every point:
- The CPL has 50 placed parts (51 lines including the header).
- The board has 216 vias, 140 of them with 0.2 mm drills.
- The order settings are 6-layer JLC06081H-2116 with epoxy-filled and capped vias (fab/README.md:22,28).
- The LED offset is +0.

I agree it is a documentation and review-artifact defect, so minor.

<a id="dfm-3"></a>

### dfm-3 — 0.4 mm-pitch UQFN and RPW parts have 0.1 mm solder-mask dams, and the mask colour is not specified

Reviewer severity **minor**, skeptic: **confirmed / minor**, reviewer confidence medium.

**Evidence.** TI_RSV0016A footprint (hardware/kicad/footprints.pretty): pads 0.2 mm wide at 0.4 mm pitch (0.2 mm copper gap), solder_mask_margin 0.05, so the mask web is 0.10 mm. The same holds in TI_RPW_VQFN-10 between pads 2 and 3, between pad 2/3 and pad 5, and between pads 5 and 6. The 0.05 margin follows TI's NSMD recommendation ('0.05 MAX ALL AROUND', tmux1511.pdf RSV0016A board layout). The .kicad_pro has solder_mask_min_width 0, so DRC never checks dam width. fab/README.md 'Order settings' does not name a mask colour. JLC's published minimum dam is about 0.1 mm for green and larger for other colours (from memory; check it on their capabilities page).

**Why it matters.** At exactly the fab limit, JLC either keeps 0.1 mm dams (green) or removes them (any other colour, or after CAM adjustment). Without dams, the 0.4 mm-pitch U3–U5 and the U6 pads are prone to solder bridges. On U3–U5 a bridge between adjacent pads is often a contract-pin short (for example EXP_n to EXP_n_S, or SEL/EXP_OE to a signal).

**Recommendation.** State 'Solder mask: green' explicitly in fab/README.md. In `make jlc-check`, inspect B.Mask around U3–U6 in JLC's processed files to confirm the dams survived. Optionally set solder_mask_min_width to 0.1 in the .kicad_pro so DRC flags anything below the limit.

**Skeptic.** The geometry checks out:
- RSV: pads are 0.2 mm wide at 0.4 mm pitch, a 0.2 mm copper gap. A solder_mask_margin of 0.05 on each side leaves a 0.10 mm dam.
- RPW: pads 2/3 are 0.25 mm wide on 0.45 mm centres (0.2 mm gap). Pads 5/6 are 0.3 mm wide on 0.5 mm centres (0.2 mm gap). Pad 2's inner edge (-0.6) to pad 5's outer edge (-0.4) is also 0.2 mm, so every dam is 0.1 mm.
- solder_mask_min_width is 0.0 in .kicad_pro, so DRC never checks dam width.
- fab/README.md never mentions a mask colour (grep for colou/color finds nothing).

I did not verify JLC's exact minimum dam per colour; the reviewer flags that as from memory. The bridging consequence is plausible rather than proven, so minor is right.

<a id="dfm-4"></a>

### dfm-4 — The Rev B 'verified' offsets in JLC_ROT include a JLC correction, not a calibration (U1)

Reviewer severity **minor**, skeptic: **confirmed / minor**, reviewer confidence medium.

**Evidence.** gen_fab.py says C7519 (USBLC6) has offset 0, 'verified 2026-10-13', 'pin 1 correct in final DFM'. JLC's library footprint for C7519 (SOT-23-6_L2.9-W1.6-P0.95-LS2.8-BL) is KiCad's SOT-23-6 rotated 90°: pins 1–3 run along the bottom edge in JLC's footprint and down the left column in KiCad's. At CPL 0 the part cannot land on the pads, so JLC engineering must have re-rotated it, as they did with J4.

**Why it matters.** JLC_ROT dates are treated as proof that an offset is right. Here the date only shows that JLC fixed it by hand. It also hides the bottom-side rule found in dfm-1. With 6-pad SOT-23-6 the fix is evident, but the same trust in 'verified' would be dangerous on the 180°-symmetric v2 parts.

**Recommendation.** Set C7519 to 270 (the value from dfm-1's model). In the JLC_ROT basis strings, separate 'offset applied as-is by JLC' from 'JLC corrected it'.

**Skeptic.** This does not depend on any mirror model. The C7519 library has pins 1-3 in a horizontal row at y=+1.149. Our U1 has its pads in vertical columns: pads 1-3 at x=-1.137 and 4-6 at x=+1.137. At CPL 0, mirroring keeps the rows horizontal, so the part cannot land on the pads under any model. JLC must therefore have rotated U1 by 90° itself.

That makes the 'verified 2026-10-13, pin 1 correct in final DFM' basis a record of JLC's correction, not a calibration. GATE B3 records the J4 correction but not this one. The value that model A and B-CW both predict is 270.

<a id="expansion-1"></a>

### expansion-1 — Carrier detect enables the bus in a normal host whenever a host-side load pulls CONFIG_2/3 low (pull-up to an unpowered rail, SoC default pull-down, GPIO driven low)

Reviewer severity **minor**, skeptic: **confirmed / minor**, reviewer confidence medium.

**Evidence.** edge_expansion.py:69-84. The only card source on CONFIG_2 (J1.75) and CONFIG_3 (J1.1) is R22/R23 = 1 MOhm to +3V3, then 100k to the Q1 gates (CFG2_G/CFG3_G). EXP_OE goes high (bus on) when Q1 sinks less than about (3.3-1.2-0.31)/10k = 0.18 mA. SSM6N56FE Fig. 7.2/7.6 plus the §5.1 Vth range 0.4-1.0 V at 1 mA put that between Vgs of about 0.2 V (min-Vth part, hot) and about 1.0-1.14 V (max-Vth part, -40 C). With a host load R_h to GND, V_cfg = 3.3*R_h/(1M+R_h). So R_h below about 65 kOhm always enables the bus, and 65-435 kOhm enables it depending on the part and temperature. Cases that produce this: a host pull-up whose rail is off while the slot 3.3 V is on (e.g. WWAN kept powered in S3), Intel PCH or SoC pads with a 20-100 kOhm default pull-down before firmware sets them, or a host GPIO output low. The research (v2/research/m2_pins_research.md:79,163) shows Dell routes CONFIG to EC/PCH GPIOs with the pull-up rail and value 'not visible'. carrier-interface.md §4.2 (lines 91-95) and ADR 0006 §2 cover only 'pull-up or floating'. The dev-carrier fixture (m2-dev-carrier SPEC §7.3: GND/open/10k-1V8/10k-3V3) and SPEC S-v2-1 have no pulled-down or unpowered-rail case. Result if it happens: R20/R21 (4.7 kOhm to +3V3, on EXP_0_S/EXP_1_S) reach M.2 pins 30/32 (UIM_RESET/UIM_CLK on WWAN hosts, Mallow X17 'SIM Card RESET/Clock'). That is about (3.3-0.6-1.8)/4.9k = 0.2-0.55 mA into a 1.8 V SIM net or SIM-card ESD diodes. Firmware's EEPROM probe also clocks SCL on UIM_CLK. EXP_2..11 stay high-Z only because of the firmware rule (§4.3 line 136).

**Why it matters.** The whole point of ADR 0006 is that the bus never connects in a standard host. The 1 MOhm card pull-up, chosen to stay safe on 1.8 V host nets, cannot tell carrier GND apart from a modest host pull-down. I found no damage path (injected current is under 1 mA), but the documented 'host-safe' guarantee is conditional, and S-v2-1 would not catch it.

**Recommendation.** No respin needed. (1) Firmware: when IO38 reads EXP_OE high and no device ACKs at 0x50 (or the CRC fails), drive IO38 open-drain low. That turns all 12 switches off through the existing 10k/1uF node, so exposure is limited to the boot-time probe window. Make that the default for unknown carriers, with a host override, and document IO38 as a firmware 'bus kill' in the contract. (2) Correct the claim in carrier-interface.md §4.2 and ADR 0006: the bus stays off only if each sense pin is above ~1.2 V or floating with no host load below ~500 kOhm to GND. (3) Add a risk-register entry (docs/risks.md) and a host-safety test row: CONFIG pins with 100k and 20k to GND (emulating SoC pull-downs and an unpowered pull-up rail), card powered.

**Skeptic.** The circuit math holds. The only card source on CONFIG_2/3 is 1 MOhm to +3V3, so any host load to GND below a few hundred kOhm divides the sense node below Q1's Vth. That turns Q1 off and lets R26 pull EXP_OE high (bus on). The thresholds check out: V_cfg = 3.3*R_h/(1M+R_h) is 0.2 V at 65k and 1.0 V at 435k. EXP_OE must sink about 0.18-0.21 mA (R26 10k, TMUX VIH 1.2 V, about 30 uA of SEL leakage), which is below the Vth test current of 1 mA. The host scenarios (an SoC default pull-down, a pull-up whose rail is off) are plausible but not shown on any specific host. Dell's rail and value are 'not visible' per the research. The consequence is small currents into SIM nets with no damage path, so minor is right. The contract text in carrier-interface.md §4.2 ('Any host pull-up ... or a floating pin, keeps the bus off') is accurate but incomplete, because it does not cover pull-downs.

<a id="expansion-2"></a>

### expansion-2 — IO38 is wired straight to EXP_OE: firmware driving it push-pull high fights Q1 (about 40 mA); its useful output-low 'kill' behaviour is not documented

Reviewer severity **minor**, skeptic: **confirmed / minor**, reviewer confidence high.

**Evidence.** design.py:81 "IO38": exp_oe; v2_reva_connections.md:204 U2.31 IO38 = EXP_OE together with Q1.3/Q1.6 drains, R26 and 12 SEL inputs. No series resistor. ESP32-S3 datasheet DC table: IOH 40 mA typ (line ~3702 of the extracted text), default drive 20 mA (Table 2-1 note 5). Q1 RDS(on) at 1.8 V gate is 290-480 mOhm (§5.1). With any CONFIG pin high (every normal host), an IO38 'output high' shorts the ESP pad into Q1 with only about 0.5 Ohm of load. pinmap.md:288 lists IO38 as 'in' (diagnostic) only, and no firmware exists in the repo yet to enforce it.

**Why it matters.** A firmware bug (e.g. a generic GPIO self-test that toggles every pin, or a board-support file that inits spare pins as outputs) would short-circuit-stress GPIO38 on every normal host. The opposite direction (output low = force the bus off) is a free safety feature that the contract does not mention.

**Recommendation.** Optionally put a series resistor (1-4.7k) between IO38 and EXP_OE in a future revision. Readback and open-drain override still work (4.7k/10k still reads above VIH when Q1 is off). For Rev A, state in pinmap §6.2, carrier-interface §4.2 and the firmware HAL: 'IO38 = input, or open-drain low only; never push-pull high'. Add it to the S-v2-2 firmware self-test exclusions.

**Skeptic.** IO38 sits directly on EXP_OE together with the Q1 drains, R26, C13 and the 12 SEL inputs, with no series resistor. On any normal host (Q1 on, RDS(on) ≤480 mOhm at 1.8 V Vgs), a push-pull high output from IO38 would be shorted into Q1, limited only by the ESP pad drive (IOH 40 mA typ). pinmap.md lists IO38 only as 'in' (diagnostic). Nothing documents 'never output-high' or the useful open-drain-low kill function. It is a firmware-hazard and documentation issue, not a hardware defect, so minor fits.

<a id="expansion-3"></a>

### expansion-3 — Contract contradicts itself: §4.3 offers UART/SPI/digital inputs from the carrier, but §5 rules 1 and 3 forbid carriers from driving any card pin high; state 6 is identical to a Telit FN990

Reviewer severity **minor**, skeptic: **confirmed / minor**, reviewer confidence high.

**Evidence.** carrier-interface.md:120 '"Digital" = GPIO, UART, SPI, PWM, RMT'. Any carrier UART TX, SPI MISO or push-pull sensor INT drives EXP lines high. Same file line 157 rule 1 'Carrier → card signals are open-drain only (pull low, never drive high)… keeps a real 1.8 V WWAN modem plugged into our carrier safe' and line 164 rule 3 'Never drive 3.3 V onto any card pin'. Card identification (§1 line 25, §4.2) uses CONFIG_0/1 grounded = state 6, which m2_pins_research.md:65 shows is exactly the Telit FN990 pattern. So a carrier cannot tell our card from a modem. On a modem, EXP pins 30/32/34/36 are UIM_RESET/UIM_CLK/UIM_DATA/UIM_PWR (outputs or supply) and 59-65 are ANTCTL/COEX (1.8 V I/O).

**Why it matters.** Carrier designers (who @-import this file) get conflicting rules. Either they cannot use the advertised UART/SPI capabilities, or they break the modem-safety rule with no way to detect the modem.

**Recommendation.** Rewrite the electrical rules for EXP lines explicitly. Either (a) carrier push-pull drivers onto EXP lines are allowed, with the documented consequence that a WWAN modem must never be inserted into such a carrier (silkscreen warning), or (b) carriers gate their drivers (e.g. a carrier-side bus switch, or drivers powered or enabled only after the ID EEPROM handshake). Keep rule 1 for the always-present pins (20/8/50) and the CONFIG pins only. Mark the item fixed or proposed per the legend.

**Skeptic.** The contradiction is real in the text. §4.3 advertises UART/SPI/PWM ('Digital' = GPIO, UART, SPI, PWM, RMT) and digital inputs, and any carrier UART TX or SPI MISO drives EXP lines high. §5 rule 1 says carrier→card signals are open-drain only, and rule 3 says 'Never drive 3.3 V onto any card pin'. The state-6 signature (CONFIG_0/1 GND, 2/3 NC as seen by the carrier) matches the Telit FN990 and Sierra EM7455. A carrier therefore cannot distinguish our card from a modem by CONFIG_0/1. The carrier's own 75/1 grounding is invisible to it. This is a contract-documentation defect that affects every carrier design, with no card respin needed, so minor.

<a id="expansion-4"></a>

### expansion-4 — No I2C speed or bus-capacitance budget for the EXP_0/EXP_1 bus with the card's fixed 4.7 kOhm pull-ups

Reviewer severity **minor**, skeptic: **confirmed / minor**, reviewer confidence high.

**Evidence.** R20/R21 = 4k7 (edge_expansion.py:48-51). I2C Fast-mode tr ≤ 300 ns gives C_bus ≤ 300 ns/(0.8473 x 4.7k) = 75 pF. Standard-mode tr ≤ 1000 ns gives ≤ 251 pF. Card share, estimated: TMUX1511 CON ≤ 6 pF (§5.6), about 30 mm of EXP_0/EXP_0_S copper (measured 12.0 + 17.5 mm), ESP pad and edge finger, about 12-15 pF total. carrier-interface.md:132-133 says carriers 'may hang other I²C devices on the same bus' but gives no frequency, capacitance limit, or rule about extra pull-ups or their voltage (Qwiic/STEMMA breakouts carry 10k, sometimes to 5 V).

**Why it matters.** A carrier with several devices or cabled breakouts at 400 kHz can exceed the rise-time limit and fail I2C intermittently, which looks like a dead or invalid ID EEPROM (the bus is then treated as an unknown carrier).

**Recommendation.** Add to §4.3: ID-EEPROM read at 100 kHz; 400 kHz only if the carrier-side bus capacitance is ≤ 60 pF; any extra carrier pull-ups only to the card supply (3.3 V), with combined pull-up ≥ 1.5 k (3 mA sink). Firmware reads the EEPROM at 100 kHz.

**Skeptic.** The arithmetic is correct: 300 ns/(0.8473*4.7k) = 75.3 pF for Fast-mode, and 1000 ns/(0.8473*4.7k) = 251 pF for Standard-mode. carrier-interface.md §4.3 lets carriers 'hang other I²C devices on the same bus' and says 'Carriers add none' for pull-ups. It gives no bus speed, capacitance budget, or rule for breakout pull-ups. This is a contract gap only; the card circuit is fine. Minor (documentation before release) is appropriate.

<a id="expansion-7"></a>

### expansion-7 — No ESD rule for carriers that bring EXP lines off-board; card-side protection is chip-level only (TMUX1511 HBM ±2 kV)

Reviewer severity **minor**, skeptic: **confirmed / minor**, reviewer confidence high.

**Evidence.** The 12 EXP edge nets go straight from J1 to the TMUX1511 D pins (U3-U5) with no TVS. tmux1511.pdf §5.2 gives HBM ±2000 V and CDM ±750 V, which are handling-level ratings, not IEC 61000-4-2. The dev carrier routes EXP_0..11 'straight to header' (m2-dev-carrier SPEC.md:198, 2.54 mm J3 with Dupont wires). carrier-interface.md §5 has no ESD requirement. The Q1 gates are fine: the SSM6N56FE §3 equivalent circuit shows gate-source protection zeners.

**Why it matters.** Relay or sensor carriers will expose EXP lines on terminals or connectors. A zap there reaches a TMUX1511 pin with only chip-level protection; failure means a card swap.

**Recommendation.** Add a contract rule: carriers that bring any EXP line to a connector, terminal or header used off-board place ESD/TVS protection on the carrier (≤ 3.6 V working, low capacitance on EXP_0/1). Note it as a dev-carrier lab-handling caveat.

**Skeptic.** The 12 EXP edge nets go from J1 to the TMUX1511 D pins with no TVS (edge_expansion.py has no ESD part). The TMUX1511 §5.2 ratings are HBM/CDM handling levels, not system-level. carrier-interface.md has no ESD rule for EXP lines: grep for ESD/TVS finds only the USB D- note at line 74. The dev carrier routes EXP_0..11 'straight to header'. This is a real contract gap; the risk depends on carrier usage. Minor is right.

<a id="layout-1"></a>

### layout-1 — Unprotected host +3V3 on fingers 2/4 reaches the eFuse only through ~0.23 Ω of 0.127 mm tracks (some on 0.5 oz inner layers)

Reviewer severity **minor**, skeptic: **confirmed / minor**, reviewer confidence high.

**Evidence.** The +3V3_M2 route from J1.2/J1.4 (x 109.0/108.5) runs as follows. A 0.2 mm B.Cu track (~2 mm) goes to via (108.75,145.6). From there 0.127 mm In2.Cu (3.8 mm) runs to via (106.5,141.7). Then 0.127 mm B.Cu (~7.6 mm, incl. (104.2,139.7)->(101.15,136.65)) runs to via (101.15,136.65). Then 0.127 mm In3.Cu (~11.5 mm, incl. (99.05,134.2)->(94.6,138.65)) runs to via-in-pad (93.7,139.7) on R31.1. From R31.1, 0.127 mm B.Cu (1.9 mm) runs to via (93.8,141.85), then 0.127 mm In3.Cu (5.3 mm) to via (92.35,145.65) on the 0.35 mm trunk. Four of the vias are 0.35/0.2. Using 0.49 mΩ/sq (outer, 35 µm) and 1.13 mΩ/sq (inner, 15.2 µm): R ≈ 4.9+34+29+102+7+47+~6 ≈ 230 mΩ. The left path (J1.70/72/74 -> C14 -> U6.5, 0.35 mm, ~5 mm) is ≈ 7 mΩ. With all 5 pins powered, fingers 2/4 carry only ≈ 3% (≈ 30 mA at 1 A), which is fine. IPC-2221 for an internal 0.127 mm × 0.5 oz trace gives ≈ 0.2 A at +20 °C. carrier-interface.md §3 says the carrier supplies pins 2, 4, 70, 72, 74, but nothing requires 70/72/74 specifically.

**Why it matters.** Suppose a carrier or fixture powers only pins 2/4, or the 70/72/74 contacts are intermittent. Then up to 0.5 A WiFi peaks (1.15 A at current limit) would flow through ~10 mm of 0.127 mm 0.5 oz In3 copper. That means about 115 mV of drop at 0.5 A (3.135 V supply minimum leaves under 3.0 V at the module) and enough heat to fuse the trace. This is pre-eFuse, unprotected host rail on a thin track crossing the whole card.

**Recommendation.** Preferred: give fingers 2/4 a wide connection to the eFuse IN trunk, for example a ≥0.35 mm outer-layer route or a short +3V3_M2 copper area. Alternative: state in carrier-interface.md §3 that pins 70/72/74 are mandatory and that 2/4 are only lightly tied, and leave the thin path as is.

**Skeptic.** I walked the +3V3_M2 net in the board file and the route is as described. J1.2/J1.4 connect through a 0.2 mm B.Cu track to via (108.75,145.6). That via is 0.45/0.3, not 0.35/0.2. From there the path is 0.127 mm In2 (about 4.8 mm), then 0.127 mm B.Cu (about 7.8 mm, including the 4.31 mm segment (104.2,139.7)->(101.15,136.65)), then 0.127 mm In3 (about 10.5 mm, including the 6.29 mm segment (99.05,134.2)->(94.6,138.65)) to the via at R31.1 (93.7,139.7). It continues with 0.127 mm B.Cu (1.9 mm) to via (93.8,141.85), then 0.127 mm In3 (about 5.3 mm) to via (92.35,145.65) on the 0.35 mm B.Cu trunk (92.375,146.225)-(92.375,144.3) to C14.1/U6.5. My resistance estimate (0.49 mOhm/sq for 35 um, 1.13 mOhm/sq for 15.2 um) is about 5+43+30+93+7+47 = 225 mOhm before vias, which matches the reviewer's ~230 mOhm. Pins 70/72/74 reach U6.5 through 0.35 mm B.Cu over a few mm, so fingers 2/4 carry a few percent of the current in normal operation. IPC-2221 internal for 0.127 mm x 0.5 oz (about 3 mil^2) gives 0.2 A at a 20 C rise. At 0.5 A the same formula extrapolates to a very large rise, so the hazard exists only when 70/72/74 are not powered. 'Enough heat to fuse' is overstated without a fusing calculation, and a compliant M.2 host powers all five pins. So: real margin/robustness issue and contract gap, not a functional defect on compliant hosts. Minor is correct.

<a id="layout-2"></a>

### layout-2 — eFuse OUT node (+3V3_EFUSE) has no local capacitor; the first capacitor sits behind ferrite FB1

Reviewer severity **minor**, skeptic: **confirmed / minor**, reviewer confidence medium.

**Evidence.** Net +3V3_EFUSE contains only U6.6 (OUT bar, 91.35,141.9) and FB1.1 (91.99,139.2), joined by a 0.35 mm track of 1.5 mm. The first capacitor is C3 (10 µF, 94.6,139.7). It sits on +3V3 after FB1 (BLM18PG121SN1D), 4.4 mm from FB1.2. TPS25947 datasheet §8.4.1: 'add a ceramic decoupling capacitor of 1μF or greater between OUT and GND ... physically close to the OUT pins'. Abs max VOUT is −0.3 V, with −0.8 V allowed for pulses <1 µs (§6.1). Fast-trip turn-off is 500 ns (tSC/tFT). Also from §8.4.1: RILM should sit close to the device, but R34 is 5.6 mm from U6.9 on a ~10 mm trace (F.Cu 8.9 mm + 2 vias). I estimate ≈ 2 pF, well under the 50 pF limit, with nothing running parallel within 0.4 mm, so that part is OK.

**Why it matters.** When the eFuse fast-trips on a downstream short (≈ 2× ILIM ≈ 2 A), the bead's inductance keeps driving current out of a node with almost no capacitance. Assuming ~0.1–0.2 µH, L·di/dt over 0.5 µs is several hundred mV negative on OUT, close to the −0.8 V pulse rating. This is a plausible stress estimate, not measured. It also deviates from TI's layout guideline on a part never built before.

**Recommendation.** Add a 1 µF 0402 (or larger) from +3V3_EFUSE to GND between U6.6 and FB1.1. There is B-side GND pour between U6 (y 140.7) and FB1 (y 139.2). Verify with an output-short test at bring-up (scope on U6.6).

**Skeptic.** The +3V3_EFUSE net has exactly two pins, U6.6 OUT and FB1.1, joined by about 1.5 mm of 0.35 mm B.Cu. The connections table says the same. The first capacitance is on +3V3 behind the BLM18PG121SN1D bead (C3 10 uF, etc.). The TPS25947 datasheet explicitly recommends a ≥1 uF ceramic at OUT close to the pins (Layout Guidelines, and §8.3.1 Transient Protection 'Connect a low ESR capacitor larger than 1μF at the OUT pin very close to the device'). It specifies an OUT minimum pulse of -0.8 V for <1 us, and turn-off times of 500 ns for tSC and tFT. The negative-spike magnitude depends on the bead's effective inductance, which is unquantified. Beads are lossy, and the reviewer correctly labels the figure as an estimate. The eFuse and FB1 arrangement is new in v2 and never built, and this is a clear deviation from the vendor layout guidance that costs one 0402. Minor is correct; bring-up short testing will tell whether the spike matters.

<a id="layout-3"></a>

### layout-3 — GND pour fills the gaps between gold fingers 69/71/73 and 3/5 on F.Cu, contrary to the GATE V3 claim of no copper between fingers

Reviewer severity **minor**, skeptic: **confirmed / minor**, reviewer confidence high.

**Evidence.** I sampled the GND_top fill polygon across the finger band:
- At y 148.75 the fill is continuous over x 91.13–92.31, spanning J1.73 (91.075–91.425), J1.71 and J1.69 (to 92.425), including both 0.15 mm gaps.
- At y 147.6–149.5 the fill is continuous over 91.13–91.83 (73/71) and 108.13–108.88 (J1.5/J1.3).
- The fill reaches y 149.7, so only the 0.3 mm edge clearance is open.
- The render shows an 'H' bar 0.3 mm tall (y≈148.64–148.93) joining fingers 71 and 69 mid-finger.
Cause: J1 pads 3/5/11/27…/71/73 have local zone_connect = solid (2); pads 21 and 69 inherit thermal. The 74 finger rule areas (147.3–150.2) only forbid vias, not copper pour. Rev B already had 71/73 and 3/5 bridged and was built. The 69↔71 spoke is new in v2. CLAUDE.md and v2-gate-v3.md both state 'Gold fingers: no copper between fingers'.

**Why it matters.** Electrically harmless, because all the bridged fingers are GND. But the finger geometry no longer matches the M.2 pad definition or the project's own rule. JLC's gold-finger DFM may query it, and the gate document claims something the board does not do.

**Recommendation.** Either correct the claim and accept the Rev B precedent, or fix it. To fix: set the J1 GND pads to thermal or none and connect each one from its top edge only, or add pour-forbidding rule areas over the 0.15 mm gaps. Then re-check that every GND finger still reaches the plane (`make drc`).

**Skeptic.** J1 GND pads 3/5/11/27/33/39/45/51/57/71/73 have local zone connection = 2 (solid). Pads 21 and 69 are inherited (-1). I hit-tested the F.Cu GND_top fill at each gap centre. The fill is present at x=91.5 (the 73/71 gap) and x=108.5 (the 3/5 gap) for y 147.6-149.5, and at x=92.0 (the 71/69 gap) only at y=148.75, which is the 'H bar'. Nothing is filled at y≥149.7. The Rev B board (git v1.0-revB) shows the same 73/71 and 3/5 bridging but no 71/69 bar, so the reviewer's precedent claim holds and the 69-71 spoke is new. The only bridged fingers are GND-GND, so the issue is electrically harmless. The board does contradict v2-gate-v3.md:52 and docs/stackup.md:109 ('no copper between fingers'). JLC built Rev B with this geometry, so the fabrication risk is low. Minor is the right level: a documentation/consistency fix plus optional cleanup.

<a id="layout-4"></a>

### layout-4 — Sparse GND stitching: 7 GND fingers share 2 vias, and outer pours run up to 7 mm from any GND via

Reviewer severity **minor**, skeptic: **confirmed / minor**, reviewer confidence high.

**Evidence.** The board has 38 GND vias plus the U2 EPAD holes. I mapped each F.Cu fill island and the GND vias inside it:
- Island with J1.11/21/27/33/39/45/51: only 2 GND vias, (100.98,144.3) and (95.25,146.6).
- J1.57: reaches GND only through a 0.127 mm, 1.35 mm track to via (95.25,146.6).
- Island with J1.3/J1.5: nearest via ~5 mm from the finger tops (107.95,138.5 / 107.65,142.6 / 104.25,142.1).
On a 0.25 mm grid, distances from pour to the nearest GND via:
- F.Cu: 265 points more than 4 mm away, worst 7.1 mm.
- B.Cu: 583 points, worst 7.3 mm. These cluster on the right edge (x 108–110.7, y 123–135), the band y 131–134 across the full width, and the finger band.
At layer changes:
- 91 signal vias switch between a GND-referenced layer (F, In2) and a +3V3-referenced layer (In3, B). Their median distance to a GND via is 1.87 mm, worst 5.56 mm (IO39 at 109.95,126.05).
- The USB transitions have no GND via within 2.3–4.4 mm. Espressif HDG §1.4.8 asks for 'a pair of ground return vias at each transition point'.

**Why it matters.** These are EMC and return-path margins on a card that transmits 2.4 GHz WiFi next to the host. A poorly stitched outer pour and a long GND-finger return raise radiated emissions and ESD/return inductance. This is not functional at GPIO or USB Full Speed rates, but it is cheap to fix before release.

**Recommendation.** Add GND vias at the top of every GND finger (y≈146.5–147.0, outside the finger rule areas). Add a perimeter via fence at ≤3–4 mm pitch, especially on the right edge (y 123–135) and across the y 131–134 band. Add one GND via next to each USB layer-change via pair.

**Skeptic.** There are exactly 38 GND vias on the board, and only 3 of them sit in the finger band below y 144 (100.98,144.3; 95.25,146.6; 91.1,143.85 plus 89.6,143.18). No GND via lies on the right edge between y 119.55 and 138.5, which matches the reviewer's 'right edge y 123-135' gap. The USB layer-change vias have their nearest GND via at 2.68 mm and 4.37 mm (USBH3_D_N/P at the edge), and at 2.26, 3.21, 1.69 and 1.58 mm (USB_D_N/P). That is consistent with the reported 2.3-4.4 mm for the edge transitions and conflicts with Espressif HDG's return-via advice. I did not re-run the full 0.25 mm grid distance map or the per-island analysis. The via positions I listed are consistent with them, though. This is not functional at FS USB or GPIO rates. It is cheap EMC/ESD margin on a WiFi card, so minor fits.

<a id="mcu_io-1"></a>

### mcu_io-1 — W_DISABLE2# card pull-up R29 = 1 MOhm is outside the M.2 spec range (100-200 kOhm); the docs wrongly say it follows the spec

Reviewer severity **minor**, skeptic: **confirmed / minor**, reviewer confidence high.

**Evidence.** hardware/blocks/host_sideband/host_sideband.py: R29 '1M' (C26083) from +3V3 to W_DISABLE2_n; the docstring says '1M card pull-up per M.2 spec'. docs/v2-gate-v1.md:61 and docs/carrier-interface.md:147 repeat 1 MOhm. M.2 EM spec Rev 1.0 sec. 3.1.11.3 (text p.109): 'a pull-up resistor between each wireless disable signal and +3.3 V is required on the card and should be in the range of 100 kOhm to 200 kOhm'. Board: J1.26 to R29.2 and Q3.2 (gate G1), nothing else. SSM6N56FE: Vth 0.4-1.0 V at 1 mA, IGSS up to 1 uA (datasheet p.3); 1 uA x 1 MOhm = 1 V of pull-up droop. A host that leaves pin 26 on a GPIO input with an internal pull-down (typically 50-100 kOhm) gives a gate voltage of 3.3*Rpd/(Rpd+1M) = 0.16-0.30 V. That is below Vth min, so Q3a is off, IO40 reads high, and the firmware reports 'radio disabled' (WiFi/BLE off) on that host. With 100 kOhm the same host gives 1.1-1.65 V and the FET is on.

**Why it matters.** The firmware can see a false radio kill on some generic Key-B hosts (fails on some hosts). The documentation also claims a compliance the card does not have.

**Recommendation.** Change R29 to 100k (C25741, already on the BOM, same 0402 footprint, no layout change). Into a 1.8 V push-pull host that is 15 uA (3.3-1.8)/100k, which is acceptable. Update host_sideband.py, docs/v2-gate-v1.md section 1.3 and docs/carrier-interface.md section 4.4.

**Skeptic.** The M.2 spec text is real and unambiguous. The card uses 1 MOhm and the docs claim spec compliance. The failure needs a host that puts an active pull-down on pin 26, which is uncommon (the spec expects an open-drain host), so the false-radio-kill case is plausible rather than typical. Even so, the non-compliance alone justifies minor. The fix to 100k (C25741, already on the BOM) is a value swap with no layout change. Divider check: 3.3*100k/(100k+1M) = 0.30 V, below Vth min 0.4 V, so Q3a is off and IO40 reads high. With 100k in place of 1M, the same host gives 1.65 V, which is above Vth max 1.0 V.

<a id="mcu_io-2"></a>

### mcu_io-2 — Q3a gate sits directly on edge finger 26 with no ESD clamp; the SSM6N56FE has no ESD rating and no gate protection

Reviewer severity **minor**, skeptic: **confirmed / minor**, reviewer confidence medium.

**Evidence.** Netlist and board: W_DISABLE2_n = J1.26, R29.2 and Q3.2. There is no series element and no clamp; the route goes finger, via (103.45,146.90), In2, vias (106.10,131.80)/(106.10,129.35), then the gate. SSM6N56FE datasheet p.2: VGSS +/-8 V and the note 'The MOSFETs in this device are sensitive to electrostatic discharge'. No HBM rating and no gate diode are shown. Every other edge-pin receiver is ESD-rated: ESP32-S3 HBM +/-2000 V (datasheet reliability table), TMUX1511 sec. 5.2 ESD ratings, USBLC6, BAT54A. Q1 gates (CONFIG_2/3) see the same exposure through 100k. A series resistor does not prevent charge sharing: an HBM model (100 pF at 2 kV) dumped onto a node of about 60 pF (Ciss 55 pF plus trace) settles near 2kV*100/160 = 1.25 kV, far above VGSS. This failure mode is my estimate, not a measurement.

**Why it matters.** These are new v2 exposed gates that Rev B never built. A card handled by its gold fingers can lose W_DISABLE2 sensing (gate punch-through usually means a short, so IO40 is stuck) or carrier detect.

**Recommendation.** For the first 5 boards: handle them with ESD precautions and add an IO40/EXP_OE sanity check to bring-up. For release: put a low-capacitance ESD diode on pin 26 (and on 75/1), or use a dual NMOS with integrated gate-protection diodes. Check whether SI1024X has them (I have not verified this). Record the decision in the risk register.

**Skeptic.** The SSM6N56FE datasheet gives no HBM rating and no gate-protection structure, and it carries an explicit ESD-sensitivity note. VGSS is +/-8 V. On the board, W_DISABLE2_n connects only J1.26, R29 and Q3 gate, so no clamp exists. CONFIG_2/3 reach the Q1 gates through 100k series resistors (carrier-interface.md:88). The damage mechanism and the 1.25 kV charge-sharing number are the reviewer's own estimate, and field exposure is limited to handling an internal card. Minor is the right severity. Note: the second-source SI1024X may have gate ESD protection, but I could not verify this because the repo has no datasheet for it.

<a id="mcu_io-3"></a>

### mcu_io-3 — BOOT leg on M.2 pin 20 (GPIO_5/AUDIO_0, 1.8 V) contradicts ADR 0006 sec. 4 and is missing from the risk register

Reviewer severity **minor**, skeptic: **confirmed / minor**, reviewer confidence high.

**Evidence.** sideband_recovery.py: D2 (BAT54A) pin 1 to PCIE_1_GPIO_5 (J1.20), anode to IO0, R2 10k pull-up. ADR 0006 Decision 4: 'GPIO_0..8 pins (20-28, 40-48) are not used always-on, because hosts may wire codecs, GNSS or SIM2 there'. M.2 spec Table 26 (p.126) and the pin list (line 'GPIO_5 - AUDIO_0/AUDIO_0/RFU/AUDIO_0 (I/O)(0/1.8V)') make pin 20 a 1.8 V audio pin in port configs 0, 1 and 3. Worked case: a 1.8 V push-pull host idling high gives IO0 = 1.8 V + Vf(BAT54 at (3.3-1.8-0.2)/10k = 0.13 mA, about 0.2 V) = about 2.0 V. That is below VIH 0.75*VDD = 2.475 V (ESP32-S3 datasheet Table 5-4), so the strap is undefined. A PCM clock toggling at EN release gives a random download boot. docs/risks.md covers pin 8 only (R10). Mitigating factor: CONFIG state 6 is port config 2, where pin 20 is RFU, so spec-following hosts should leave it alone. Mallow routes it only to header X16.19 (Mallow datasheet Table 22). Inherited from Rev B and only validated on Mallow.

**Why it matters.** On hosts that hard-wire WWAN audio and do not decode CONFIG, the card can boot into ROM download mode intermittently and look dead.

**Recommendation.** Add an R10-style risk entry for pin 20 (affected host class: hard-wired AUDIO_0 or a 1.8 V push-pull GPIO_5; mitigation: lift D2 pin 1). Amend ADR 0006 sec. 4 to name pin 20 as the deliberate exception, and list pins 8/20 in carrier-interface host notes.

**Skeptic.** The electrical behavior is real. D2 (BAT54A) has its common anode on IO0 and cathode 1 on pin 20 (PCIE_1_GPIO_5). A 1.8 V push-pull high forward-biases the diode, so IO0 sits at about 2.0-2.1 V, below VIH 0.75*VDD = 2.475 V. M.2 lists pin 20 as AUDIO_0 (1.8 V) in port configs 0, 1 and 3. Part of the finding needs correcting: the constraint is already documented. The block docstring (sideband_recovery.py:5-8, from the GATE 2 review) says push-pull 1.8 V highs give an undefined input, and carrier-interface.md:76 says pin 20 is BOOT, open-drain only. What is missing is a risk-register entry: risks R6 claims Schottky isolation mitigates 1.8 V hosts, which is false for a push-pull high, and only R10 (pin 8) covers this failure class. ADR 0006 sec. 4 also does not name pin 20 as the inherited exception. So this is a documentation and host-population gap, not a new circuit defect.

<a id="mcu_io-5"></a>

### mcu_io-5 — SI1024X second source (K4): no datasheet in the repo, pinout and limits only asserted in a code comment, and no JLC_ROT entry

Reviewer severity **minor**, skeptic: **confirmed / minor**, reviewer confidence medium.

**Evidence.** hardware/blocks/common.py SSM6N56FE(): LCSC_2nd_source 'C86784 (Vishay SI1024X-T1-GE3)', with the comment 'same SOT-563 pinout ... Vth 0.45-0.9 V, IGSS 1 uA; VGS max +-6 V'. docs/datasheets/ has no Vishay file (README lists none). hardware/tools/gen_fab.py JLC_ROT is keyed by LCSC number and has a C146449 row but none for C86784; grep finds no 2nd-source handling in gen_fab.py or fab/README.md. The BOM note says a 2nd source 'is swapped in by hand at order time', which bypasses the ORDER-BLOCKED rotation gate. The SI1024X package is SC-89-6 (similar to SOT-563, but JLC's library footprint and orientation may differ).

**Why it matters.** A stock-driven swap at order time would place an unverified pinout and orientation on 3 FETs that gate the host-facing pins and the expansion-bus enable.

**Recommendation.** Add the SI1024X datasheet to docs/datasheets. Verify the pinout and the drain-gate pairing against Table 3 of the SSM6N56FE datasheet. Add a JLC_ROT row for C86784, or make gen_fab refuse to run when the BOM carries a 2nd-source LCSC without a row.

**Skeptic.** There is no Vishay datasheet in docs/datasheets. The pinout and limits for the second source exist only as a code comment. JLC_ROT has a row for C146449 but none for C86784. The BOM note says the second source is swapped by hand at order time, which bypasses the gen_fab rotation/ORDER-BLOCKED gate. JLC would place C86784 using its own library footprint, whose orientation has not been checked. I could not verify the actual SI1024X pinout offline, so the claimed equivalence is unverified rather than wrong.

<a id="mcu_io-6"></a>

### mcu_io-6 — WAKE_ON_WWAN# cannot wake a host that holds PERST# low while asleep; the contract does not say so

Reviewer severity **minor**, skeptic: **confirmed / minor**, reviewer confidence medium.

**Evidence.** EN = U2.3, R1, C5, D1.3 and TP1; D1 cathode is PERST_n (J1.50). Q2b gate is driven by IO47 with R28 100k pull-down, so it is off whenever the ESP is in reset. On many platforms PERST# follows the platform reset (asserted in S3/D3cold), which puts the ESP in reset, which forces WAKE_ON_WWAN_n off. Also, GPIO47 is not an RTC GPIO (ESP32-S3 Table 2-1: RTC IO MUX covers GPIO0-21 only), so holding the pin low through ESP deep sleep needs gpio hold. docs/carrier-interface.md sec. 4.4 states 'open-drain NMOS (IRQ / wake to host)' with no caveat. M.2 spec sec. 3.2.10.3.5 expects a 1 s low pulse to wake the platform.

**Why it matters.** A feature on v2's contract silently fails on part of the host population (fails on some hosts).

**Recommendation.** Document in carrier-interface sec. 4.4 and the risk register: 'wake works only while the host keeps PERST# deasserted and the card powered; firmware must use gpio_hold for IO47 across sleep'. Add a test to the dev-carrier plan.

**Skeptic.** PERST_n holds EN low through D1, which puts the ESP32-S3 in reset. In reset, IO47 is undriven and R28 (100k) pulls the Q2b gate low, so WAKE_ON_WWAN_n cannot be asserted. A host that asserts PERST# in sleep (the D3cold case for which WAKE exists) therefore cannot be woken by the card. The contract states the wake function with no caveat. GPIO47 is outside the RTC GPIO range (0-21), so holding it through deep sleep relies on digital gpio hold; this is a firmware note, not a defect. This is a documentation and contract gap. No hardware respin is needed for the RC.

<a id="mcu_io-7"></a>

### mcu_io-7 — The v2 bring-up plan does not exercise the W_DISABLE2#/IO40 input or the 1.8 V host levels on the new host-facing cells

Reviewer severity **minor**, skeptic: **confirmed / minor**, reviewer confidence high.

**Evidence.** m2-dev-carrier docs/bringup.md sec. 7 checks only J4 hdr 7/9, D5 (LED_1), D6 (WAKE via JP6) and EXP_OE. The dev carrier has JP5 (W_DISABLE2_n to GND, hardware/blocks/host_pins/host_pins.py:8), but sec. 7 never toggles it or checks that IO40 inverts (low = radio allowed, high = disabled). Q3a with VGS 1.2-1.8 V (Key-B pin 26 is 1.8 V per M.2 Table, HSIC_STROBE 1.2 V) is untested.

**Why it matters.** The new host_sideband block has never been built. Without explicit steps, an inverted-logic or firmware mapping error would only show up in the field.

**Recommendation.** Add to sec. 7: JP5 open/closed gives IO40 0/1. Pin 26 driven at 1.8 V push-pull must give IO40 = 0. With the card unpowered, measure the pin 26 leakage. Read IO38 against EXP_OE for each signature state.

**Skeptic.** m2-dev-carrier bringup.md sec. 7 (lines 200-211) lists only the J4 hdr 7/9, D5, D6 and EXP_OE checks. JP5 is used only in the sec. 2 continuity check (lines 103-104), with no card fitted. The host-safety matrix is deferred to docs/host-safety-test.md, which does not exist yet. The W_DISABLE2_n to IO40 inversion is not exercised on a v2 card.

<a id="power-2"></a>

### power-2 — The approved eFuse second source TPS259474LRPWR is not a drop-in: it is a latch-off circuit breaker, and with ITIMER open any overload above 0.85 A latches the card off

Reviewer severity **major**, skeptic: **confirmed / minor**, reviewer confidence high.

**Evidence.** common.py:113-115 JLC_note, ADR 0007:14 ('same-footprint TPS259474L C2864845 as second source') and v2-gate-v1.md:136. Device Comparison Table (p.4): TPS259474LRPW has a 'Circuit Breaker' overcurrent response and 'Latch-Off' fault response, and pins 3/4 are PG/PGTH instead of AUXOFF/FLT. §7.3.5.2: once ITIMER expires, the breaker 'turns off the HFET immediately'. tCB is 2 us, and the ITIMER note says 'Leave the ITIMER pin open to allow the part to break the circuit with the minimum possible delay' (ITIMER is open here, power_3v3.py:43). Table 7-3: persistent overcurrent is 'Fault Latched Internally: Y'. Table 7-2 and §7.3.9: a latched fault clears only by cycling VIN to 0 V or pulling EN below VSD(F). EN is hard-wired to IN through R33 1 MΩ. The thermal-shutdown path is also latch-off on the L variant.

**Why it matters.** If JLC stock forces the swap, any brief load above 0.85-1.15 A leaves the card dead until the host power-cycles the slot. Examples: plugging a Qwiic cable with a capacitive load into the live J3, which feeds +3V3 directly, or a transient short. The TPS259470A, by contrast, current-limits and keeps running. Pin 4 also changes from an output (FLT) to an analog input (PGTH). Leaving it open is allowed, but it is a different part. The BOM 'Approved 2nd source' column for U6 is empty, so the docs disagree with each other.

**Recommendation.** Remove TPS259474L as an approved second source. If one is needed, approve only TPS259470L, and note that it is latch-off on thermal shutdown. Otherwise, if TPS259474A is used, a CITIMER is required and the auto-retry and circuit-breaker behaviour must be re-reviewed. Order spare TPS259470ARPWR stock instead.

**Skeptic.** The facts hold. In the Device Comparison Table TPS259474LRPW is 'Adjustable OVLO / Circuit Breaker / PG, PGTH / Latch-Off'. §7.3.5.2 says it turns the HFET off once ITIMER expires, and the ITIMER note 1 says an open ITIMER gives the minimum delay. Table 7-3 marks persistent overcurrent on 474x as latched (Y). A latched fault clears only by cycling VIN to 0 V or pulling EN below VSD, and EN is R33 1 MΩ to IN. If this part were fitted, any load above ILIM (0.85-1.15 A) would leave the card dead until the slot is power-cycled. Thermal shutdown latches on the L variant too. I downgrade to minor because the board as ordered uses the primary part. bom.csv carries only TPS259470ARPWR, and the BOM 'Approved 2nd source' column for U6 is empty. The defect is that ADR 0007, common.py and v2-gate-v1.md approve a part that is not functionally equivalent. It would become a field failure only if someone performs that swap at order time. It still has to be fixed before release, because K4 shows stock-driven swaps do happen.

<a id="power-3"></a>

### power-3 — K1 extended: M.2 lets hosts soft-start the slot at 200 mA; how to size CdVdt over IdVdt tolerance, its voltage rating, and the OVLO-recovery restart that skips dVdt

Reviewer severity **minor**, skeptic: **confirmed / minor**, reviewer confidence medium.

**Evidence.** M.2 Rev 1.0 Table 39: TSETTLE ≤ 5 ms 'should be achievable even with 330 uF module load and 200 mA Soft-Start current limit', so slot soft-start limits of about 200 mA are legitimate. Card +3V3 capacitance counted from the netlist: C1 and C2 22 uF, C3 and C7 10 uF, C4/C6/C10/C11/C12 5 x 0.1 uF, total 64.5 uF nominal plus the module's internal capacitors. Estimated effective capacitance at 3.3 V DC bias is about 43 uF (0805 25 V X5R about -25 %, 0603 10 V X5R about -45 %). C5 and C13 charge through resistors and are excluded. With DVDT open, SR is about 12-15 V/ms, giving 0.52-0.97 A of inrush, so above 200 mA on any host and up to ILIM. The UVP hysteresis (VUVP(R) 2.53 V, VUVP(F) 2.42 V typ) is narrow, so a current-limited host could make U6 chatter around 2.4-2.5 V; this is not verified. Sizing CdVdt: Eq.4 gives CdVdt[pF] ≈ 2000/SR[V/ms]. IdVdt is 0.81/2.21/3.82 uA, so SR spreads from 0.37x to 1.73x nominal. With 1.8 nF, SR is about 1.1 V/ms nominal and ≤ 1.9 V/ms worst case, so inrush is ≤ 0.14 A even at 75 uF. Slowest case is about 0.32 V/ms, about 10 ms to 3.3 V. EN is RC 10 kΩ/1 uF, so ESP32 tSTBL is still met. Rec. Op. table: the dVdt capacitor must be rated VIN + 5 V, so 25 V or more to match the ~18.9 V survival claim. §7.3.3: on recovery from OVLO the TPS259470x 'bypass the inrush control (dVdt) and start up in a current limited manner', i.e. 0.85-1.15 A, which no CdVdt fixes. There is no pad on U6 pin 7 (DVDT) today.

**Why it matters.** The planned K1 fix has to be sized against the M.2 host limit and the 4.7:1 IdVdt spread, not only against ILIM. Its capacitor needs the right voltage rating, or it fails during exactly the overvoltage event the eFuse is there for.

**Recommendation.** Add a CdVdt footprint now: 1.8-2.2 nF C0G, 50 V, 0402, from U6.7 to GND. 1.8 nF gives ≤ 0.14 A worst-case inrush. Record the 200 mA M.2 figure and the card's inrush in carrier-interface §3; this closes CG4. Document that restart after OVLO is current-limited at up to 1.15 A.

**Skeptic.** Every input checks out. M.2 Table 39 condition 1 cites a '330 µF module load and 200 mA Soft-Start current limit'. Card +3V3 capacitance is C1/C2 22 uF, C3/C7 10 uF and C4/C6/C10/C11/C12 100 nF, for 64.5 uF nominal. The 100 nF parts are 0603 per the BOM, not 0402, which does not matter here. SRON with dVdt open is 12.14 V/ms at 2.7 V. That gives 0.52 A into an effective 43 uF and 0.78 A into 64.5 uF, both above 200 mA. The Rec. Op. table requires the dVdt capacitor to be rated VIN + 5 V. §7.3.3 says OVLO recovery on 470x bypasses dVdt and starts up current-limited. One small correction: the datasheet table gives 0.87 V/ms typical at 2.7 V for 1800 pF, slightly below the 1.11 V/ms from Eq.4, so inrush is a little lower than computed. With the slowest IdVdt (0.81 uA) the ramp is about 8-10 ms. I checked the ESP EN RC (10k/1 uF) against a 0.33 V/ms ramp: EN is only about 1.2 V when VDD reaches 3.3 V, well below VIH, so the EN timing claim holds. The ramp affects only the card's own rail, not the host TSETTLE. The UVP chatter on 200 mA-limited hosts remains unverified, as the finding itself says.

<a id="power-4"></a>

### power-4 — No capacitor at the eFuse OUT pin: +3V3_EFUSE connects straight into ferrite FB1, against TI's '≥1 uF close to OUT' guidance

Reviewer severity **minor**, skeptic: **confirmed / minor**, reviewer confidence medium.

**Evidence.** The +3V3_EFUSE net has 2 members, U6.6 and FB1.1 (v2_reva_connections.md:424); the board has 1.49 mm of 0.35 mm B.Cu between them. Datasheet §8.3.1 (p.60-61): 'Connect a low ESR capacitor larger than 1uF at the OUT pin very close to the device' and 'Connect a Schottky diode from the OUT pin to ground to absorb negative spikes'. §8.4.1: 'TI recommends to add a ceramic decoupling capacitor of 1uF or greater between OUT and GND...physically close to the OUT pins.' Abs max VOUT,PLS is -0.8 V for under 1 us. On a fast trip (tSC/tFT 500 ns) the FB1 current has no local path, which drives OUT negative. The light-load linear-ORing regulation (VFWD 16.9 mV) and the RCB comparator then work into an inductive node. The effect on loop stability is not characterised by TI; I have not verified it.

**Why it matters.** This configuration is outside the datasheet's reference conditions, on a part that has never been built. Possible results are negative OUT spikes beyond the pulse rating on fault events, or ringing and oscillation at light load that the bring-up plan would not look for.

**Recommendation.** Either add a 1 uF X7R 0402 (rated 10 V or more) from +3V3_EFUSE to GND between U6.6 and FB1.1, or fit FB1 as 0 Ω. The second option is a BOM-only change: the bulk then sits at OUT, the drop margin gains up to 25 mV at 0.5 A, and the WROOM-1 has its own internal LC (per power_3v3.py:22-24). Either way, at bring-up scope U6 OUT at idle and during WiFi TX.

**Skeptic.** The +3V3_EFUSE net has exactly 2 members, U6.6 and FB1.1. On the board it is 3 B.Cu segments of 0.35 mm, 0.64 + 0.5 + 0.35 = 1.49 mm long, with no capacitor. Section 8.3.1 recommends a capacitor larger than 1 uF at OUT very close to the device, and a Schottky diode to OUT, against negative spikes. Section 8.4.1 recommends a ceramic capacitor of 1 uF or more between OUT and GND close to the OUT pins. The datasheet links negative OUT spikes to output inductance when current is interrupted, and the ferrite puts inductance in series at OUT. The abs-max pulse rating VOUT,PLS is -0.8 V for under 1 us. How large the spike would be, and whether there is any light-load stability effect, has not been quantified. The finding is a deviation from the datasheet's recommended configuration, not a demonstrated failure, so minor is right. Fitting FB1 as 0 Ω (the alternative already noted in power_3v3.py:23-24) removes the issue as a BOM-only change.

<a id="power-5"></a>

### power-5 — Drop budget leaves out socket contacts and copper, and J3 (Qwiic +3V3 out) has no current budget against the 0.85 A limit

Reviewer severity **minor**, skeptic: **confirmed / minor**, reviewer confidence high.

**Evidence.** ADR 0007 'Drop' section, v2-gate-v1.md:85 (≈3.09 V) and risks.md:25 (R-v2-4 '~40 mV margin') count only RON and FB1. The Amphenol socket datasheet gives 55 mΩ initial per contact, with 20 mΩ change allowed. On the board, fingers 70/72/74 feed U6 through about 5 mm of 0.35 mm B.Cu (about 7 mΩ). Fingers 2/4 come in through about 28 mm of 0.127 mm trace (In2/B.Cu/In3, about 0.2 Ω), so they carry almost nothing. Worst case at 0.5 A: 3 contacts in parallel 18-25 mΩ, plus GND return through about 11 contacts 5-7 mΩ, plus copper and vias about 12 mΩ, plus RON 45 mΩ, plus FB1 50 mΩ, totals about 130-139 mΩ, a 65-70 mV drop. That leaves 3.065-3.070 V at the module (minimum 3.0 V), about 65 mV of margin. At 0.85 A (ILIM min, for example ESP TX plus a 0.35 A Qwiic load) the drop is about 118 mV, leaving about 3.017 V. J3.2 is on +3V3 (io_header.py), and no current limit for it appears in SPEC, ADR 0005 or carrier-interface.md.

**Why it matters.** The risk register states a number that was never derived from all the series elements. An accessory that is fine on its own can push the card to the 3.0 V edge on a low host, or into active current limit (ITIMER open means it acts immediately).

**Recommendation.** Redo R-v2-4 including the contacts, and state the result: about 65 mV at 0.5 A with FB1, about 90 mV with FB1 = 0 Ω. Specify a J3 3V3 output budget, for example ≤ 150 mA, in SPEC/ADR 0005 and the user docs. Keep the bring-up measurement of the minimum +3V3 at the module during TX on a 3.135 V bench supply.

**Skeptic.** The Amphenol socket datasheet gives 55 mΩ maximum initial resistance plus 20 mΩ allowed change per contact, and 0.5 A per power contact. Fingers 70/72/74 reach U6 IN through about 6 mm of 0.35 mm 1 oz B.Cu, about 8 mΩ. The I2C path is In2/In3 0.5 oz plus B.Cu at 0.127 mm, about 0.2 Ω (see power-10). With RON 45 mΩ and FB1 50 mΩ the total is about 130-140 mΩ, which is 65-70 mV at 0.5 A and leaves about 3.065 V at the module from a 3.135 V host. That is 65 mV of margin, which is actually more than the ~40 mV in R-v2-4. The register figure is stale, apparently from the 150 mΩ FB1 era, and was never derived from the full series path. So the defect is documentation, not a supply shortfall. J3.2 is on +3V3 (connections.md:423), and no J3 current budget appears in ADR 0005 or carrier-interface.md. At 0.85 A the drop of about 118 mV leaves about 3.017 V, which is still at least 3.0 V.

<a id="power-6"></a>

### power-6 — Stale or inconsistent power documentation

Reviewer severity **minor**, skeptic: **confirmed / minor**, reviewer confidence high.

**Evidence.** hardware/blocks/power_3v3/datasheets.md:3-5 still lists FB 'Sunlord GZ2012D101TF ... 150 mR' (v1). LESSONS.md:1-5 budget uses 150 mΩ. ADR 0007:20 says 'Auto-recovers at ~3.23 V; not latched', which is the 51 k value, and the amendment only partly supersedes it. SPEC A3 says '~3.17 V' (see power-1). risks.md R-v2-4 says '~40 mV' (see power-5). The BOM 'Approved 2nd source' column is empty for U6 while ADR 0007 and common.py name TPS259474L (see power-2). review-findings.md GATE V2 says EN pull-up '→ 470 kΩ' but the design uses 1 MΩ, with the reason given in power_3v3.py:58-59.

**Why it matters.** These are the release-candidate docs that carriers and bring-up rely on.

**Recommendation.** Update datasheets.md and LESSONS for BLM18PG121SN1D (≤ 50 mΩ). Restate the OVLO recovery threshold everywhere as 3.13-3.25 V, with its consequence. Bring the second-source statements into line with power-2.

**Skeptic.** Each item checks out. datasheets.md:3-5 still names the GZ2012D101TF at 150 mΩ. ADR 0007:20 says 'Auto-recovers at ~3.23 V; not latched', a figure from the superseded 51k divider, and 'not latched' is misleading given power-1. ADR 0007:10 still says 'FB1 ... 150 mΩ'. risks.md:25 says ~40 mV. The BOM 2nd-source column for U6 is empty while ADR 0007:14 and common.py:193 name TPS259474L. Two items are weaker than stated. LESSONS.md:1-5 is a dated historical entry (2026-08-28, Rev B), not a live claim. review-findings.md:338 ('→ 470 kΩ') is an append-only log of what the reviewer said at the time, and power_3v3.py:58-59 documents the reason for 1 MΩ. Neither of these two is really stale; they are traceability gaps at most. Overall this is a valid documentation-hygiene finding for release-candidate docs.

## Info (24)

<a id="contract_test-11"></a>

### contract_test-11 — Lifecycle: ESP32-S3R2 die is EOL (upgraded to S3RH2); SSM6N56FE stock collapse is unexplained

Reviewer severity **info**, skeptic: **confirmed / info**, reviewer confidence medium.

**Evidence.** docs/datasheets/esp32-s3_datasheet_en.pdf v2.2, p.1 and Table 1-1 (txt lines 26-28, 641-642): 'ESP32-S3R2 – End of life (EOL), upgraded to ESP32-S3RH2', chip revision v0.2 only, 'see PCN'. WROOM-1-N8R2 is still listed without an NRND mark in the WROOM datasheet v1.8 (2026-03-02, txt line 120). SSM6N56FE JLC stock fell 7,293 → 124 in four days (v2-gate-v4.md §4); no lifecycle check is recorded.

**Why it matters.** New modules will carry S3RH2 / rev v0.2 silicon. The firmware toolchain must support it, and the Rev B units may differ from production units. A Toshiba EOL on SSM6N56FE would make SI1024X the primary part.

**Recommendation.** Read the Espressif PCN for S3R2→S3RH2, pin the minimum ESP-IDF/MicroPython version in the firmware README, and log the chip revision at bring-up (esptool chip_id). Check Toshiba's lifecycle status for SSM6N56FE,LM; if NRND, swap the primary to SI1024X-T1-GE3 before the 100-unit run.

**Skeptic.** The ESP32-S3 datasheet v2.2 lists 'ESP32-S3R2 – End of life (EOL), upgraded to ESP32-S3RH2' (l.28, 642, 656 'see PCN'), and S3RH2 is chip revision v0.2 (l.637). The BOM uses WROOM-1-N8R2 (C2913204). The SSM6N56FE stock drop is recorded in R-v2-6. Whether Toshiba lists the part as NRND was not checked here (no web access), so that part is unverified.

<a id="contract_test-12"></a>

### contract_test-12 — Product markings and access: decide before ordering

Reviewer severity **info**, skeptic: **confirmed / info**, reviewer confidence high.

**Evidence.** Board silkscreen (pcbnew dump): the top side has 'ESP32-M2', 'COMPANION', 'J4 UART/SPI', 'J3 QWIIC'. The bottom has 'v2.0 Rev A 2026-10', 'samnium.tech', 'Designed in Italy', 'EN', 'BOOT'. The revision is on the bottom only, which faces the host once inserted, so v2 and Rev B cannot be told apart in a slot without the D3/D4 behaviour or CONFIG readback. There is no CE/WEEE marking (business plan: self-declared CE first). TP1/TP2 (EN/BOOT) are on the bottom (108.4/107.4, 134-136 mm) and unreachable in any socket. EXP_OE, +3V3_M2 and +3V3_EFUSE have no test points; only IO38 and J3 pin 2 (+3V3) are observable in a socket.

**Why it matters.** Silkscreen changes after the order mean a respin. Regulatory marks and visual revision identification matter once units are sold or mixed with Rev B.

**Recommendation.** Consider a top-side 'v2' / 'Rev A' mark near J3/J4, and decide where the CE/WEEE marks go (card vs packaging). If space allows, add a small bottom pad on EXP_OE and on +3V3_EFUSE for bench debugging of the new blocks. They are not needed in a socket, where IO38 and J3 pin 2 cover it.

**Skeptic.** A pcbnew dump confirms the silkscreen. F.Silkscreen has 'J4 UART/SPI', 'J3 QWIIC', 'ESP32-M2', 'COMPANION'. B.Silkscreen has 'EN', 'BOOT', 'samnium.tech', 'v2.0 Rev A 2026-10', 'Designed in Italy'. TP1/TP2 are on B.Cu. The revision mark is bottom-only and there is no CE/WEEE mark. This is an observation and an owner decision.

<a id="dfm-5"></a>

### dfm-5 — The documented second-source swap for Q1–Q3 bypasses the fab tooling

Reviewer severity **minor**, skeptic: **confirmed / info**, reviewer confidence high.

**Evidence.** docs/v2-gate-v4.md §4: 'swap by hand only if it's out of stock at order time' (SI1024X-T1-GE3, C86784). JLC_ROT is keyed by LCSC number, and C86784 has no entry. JLC's library for C86784 (SOT-563_L1.6-W1.2-P0.50-LS1.6-BL) has pin 1 bottom-left with horizontal rows, the same orientation as C146449, so the same offset applies (and dfm-1 applies to it too). Current JLC stock is 33,554 for C86784 and 7,263 for C146449.

**Why it matters.** A swap done by hand in JLC's BOM editor means the CPL rotation is never re-derived or checked by `make fab`. The SSM6N56FE's 180°-symmetric pinout makes a wrong rotation silent: the two channels swap.

**Recommendation.** If the second source is ever used, swap it in the BOM source and run `make fab` again. Add a C86784 entry to JLC_ROT with the same offset as C146449, and note in the checklist that the pin-1 rule is unchanged.

**Skeptic.** The facts hold:
- docs/v2-gate-v4.md:104 and gen_bom.py:48-49 say the second source is swapped in by hand at order time.
- C86784 has no JLC_ROT entry.

I downgrade it to info. The C86784 library is in the same orientation as C146449: pin 1 bottom-left, horizontal rows, pads at y=±0.723 against ±0.762. JLC's CPL rotation is per designator, so a BOM-only swap keeps the same rotation and lands identically. Any hazard is the same as dfm-1's and creates no new one. Adding a JLC_ROT entry is good hygiene but changes no outcome.

<a id="dfm-6"></a>

### dfm-6 — About 30 vias sit fully or partly inside SMD pads, including 0.2 mm UQFN pads, so filled-and-capped vias are mandatory

Reviewer severity **info**, skeptic: **confirmed / info**, reviewer confidence high.

**Evidence.** From a pcbnew scan of 216 vias (88 at 0.35/0.2, 52 at 0.45/0.2, 76 at 0.45/0.3):
- Via centres inside pads: U2.13/14 (USB), U2.36/37, U4.13, U4.5, U3.5, U5.5, D3.2, D4.1, J4.1/4, R/C pads.
- Vias partly overlapping pads: U4.2/6, U5.2/9, U3.9/13, RN1.2/3, RN2.5–7, Q1.2, U6.1, among others.

The board has '(tenting front back)', and fab/README.md requires 'Via Covering: Epoxy Filled & Capped'. The U2 EPAD's 12 x 0.3 mm holes are PTH pads (component holes, open on F.Mask, covered on B.Mask), so filling may not cover them. They are unchanged from Rev B, which was built.

**Why it matters.** If the order were placed with tented or plugged vias, solder would wick off the 0.2 × 0.6 mm UQFN pads and from module pads 13/14 (USB), giving open joints that are hard to diagnose.

**Recommendation.** Keep the README requirement. In `make jlc-check` or at order confirmation, check that the production order states 'Epoxy Filled & Capped' (POFV) and that the vias appear as vias, not pads.

**Skeptic.** My pcbnew scan confirms the via counts: 216 vias, of which 88 are 0.35/0.2, 52 are 0.45/0.2 and 76 are 0.45/0.3.

The overlap is larger than the reviewer's 'about 30':
- 56 via-pad pairs have the drill centre inside an SMD pad. These include U2.13/14 and U3.5, U4.5, U4.13 and U5.5.
- About 42 more pads have a drill partly overlapping.

The board sets '(tenting front back)', and fab/README.md:28 requires Epoxy Filled & Capped. The requirement is already documented, so the finding stays at info.

<a id="dfm-7"></a>

### dfm-7 — Small inconsistencies in the fab package and docs

Reviewer severity **info**, skeptic: **confirmed / info**, reviewer confidence high.

**Evidence.** - Via count: fab/README.md says '90 vias are 0.35/0.2' and docs/stackup.md says '90 of 213'. The board has 88 of 216.
- No stackup: the board has no (stackup) section, so the gbrjob in the zip carries KiCad defaults (5 x 0.114 mm dielectric, 'Finish': 'None') and 'Revision': 'rev?'.
- The zip includes an empty NPTH.drl.
- The bottom-side checklist header says trust N/S, but each row gives corners in top-view E/W terms.

**Why it matters.** These are cosmetic, but the gbrjob stackup and finish contradict the order form (JLC06081H-2116, ENIG). A CAM engineer who reads the job file could query it and delay the order.

**Recommendation.** Define the 6-layer stackup and ENIG finish in Board Setup (or drop the gbrjob from the zip). Set the title-block revision. Update the via counts. Give each checklist corner as 'N/S + top-view E/W', or N/S only.

**Skeptic.** Each item checks out:
- Via counts: the board has 88 0.35/0.2 vias out of 216. fab/README.md:24 says 90, and docs/stackup.md:105 says '90 of 213'.
- The board file has no stackup section, so the gbrjob carries KiCad defaults: 'Revision': 'rev?', 'Finish': 'None' and 0.114 mm FR4 dielectrics.
- The NPTH.drl in the zip holds only a header and M30, no holes.

These are cosmetic, so info.

<a id="dfm-8"></a>

### dfm-8 — RSV stencil area ratio is marginal

Reviewer severity **info**, skeptic: **confirmed / info**, reviewer confidence medium.

**Evidence.** RSV paste apertures are 1:1 with the pads: 0.2 × 0.6 mm, which is TI's own example for a 0.125 mm stencil (tmux1511.pdf, example stencil design). The area ratio is 0.12 / (1.6 × 0.12) = 0.625 at a 0.12 mm stencil, below the IPC-7525 guideline of 0.66.

**Why it matters.** Paste release on 15 of the 16 pads per switch could be thin, giving opens. The TI-recommended aperture and Rev B's module make this low risk.

**Recommendation.** No change needed. If JLC lets you choose, a 0.10 mm stencil helps U3–U6. Inspect U3–U5 joints closely at bring-up.

**Skeptic.** The RSV paste is 1:1 with the pads: the footprint has F.Paste on the 0.2x0.6 pads and no paste margin. The area ratio is L·W / (2(L+W)·T) = 0.12 / (2·0.8·0.12) = 0.625, below the IPC-7525 guideline of 0.66. The roundrect corners lower it slightly further.

The stencil thickness of 0.12 mm is an assumption; JLC's default for this order is not recorded in the repo. This is a low-risk observation, so info stands.

<a id="expansion-5"></a>

### expansion-5 — Bus stays enabled across ESP32 resets (PERST#/RESET button, WDT, brown-out, SW reset); the 'glitches are harmless because the bus is off at power-up' argument covers cold power-up only

Reviewer severity **info**, skeptic: **confirmed / info**, reviewer confidence medium.

**Evidence.** EXP_OE depends only on CONFIG_2/3 and +3V3 (edge_expansion.py:68-91), not on EN. pinmap.md:258-261 justifies IO18 (EXP_4, '60 µs high-level glitch', ESP32-S3 datasheet Table 2-2) and IO1-17 low glitches by 'the bus switch is off during power-up (§6.3 RC)'. Table 2-2 is titled 'Power-Up Glitches'; the datasheet does not say whether an EN-pin reset reproduces them. During any reset with a carrier attached, every EXP line goes to its reset state (IE only; IO39 has a WPU; EXP_0/1 are held by R20/R21) while connected to the carrier.

**Why it matters.** A carrier actuator on EXP_4 could see a 60 us high pulse each time the host or carrier resets the card, if the glitch also occurs on EN reset. Carriers are not told that EXP lines go high-Z for the whole reset and boot time.

**Recommendation.** At bring-up (dev carrier, JP2/JP3 = GND), scope EXP_4 and one low-glitch line (EXP_2) while pulsing RESET (PERST#). Record the result in edge_expansion/LESSONS.md. Add to carrier-interface §4.3: 'EXP lines are high-Z (EXP_0/1 pulled up) during card reset and boot, up to ~300 ms; carriers must default outputs off'. Rule 5.2 already implies this but does not tie it to card resets.

**Skeptic.** Confirmed as a fact: EXP_OE depends only on CONFIG_2/3 and +3V3, not on EN, so the bus stays connected through any ESP reset. pinmap.md's glitch justification relies on 'the bus switch is off during power-up', which holds only for cold power-up. Whether EN/WDT resets reproduce the Table 2-2 glitches is not stated in the datasheet (Table 2-2 is titled 'Power-Up Glitches on Pins'). That part stays unverified and needs a scope measurement at bring-up. Carriers are already told actuators must default off (rule 5.2), so info is right.

<a id="expansion-6"></a>

### expansion-6 — Enable and disable timing not stated; IO38 reports 'on' ~10 ms after the switches already conduct

Reviewer severity **info**, skeptic: **confirmed / info**, reviewer confidence high.

**Evidence.** R26 10k x C13 1 uF, tau = 10 ms. TMUX VIL 0.45 V and VIH 1.2 V (§5.5, no hysteresis specified) are crossed at 10ms*ln(3.3/2.85) = 1.5 ms and 10ms*ln(3.3/2.1) = 4.5 ms (5.1 ms with worst leakage). The 12 SELs therefore pass through the undefined region over about 3 ms. ESP32 VIH = 0.75*VDD (2.35-2.475 V) is reached at about 13.9 ms typ and 17.7 ms worst (Vf = 2.83 V at 3.135 V). Disable is µs (Q1 discharges the 1 µF; peak current well under IDP 1.6 A, energy 5.4 µJ).

**Why it matters.** Harmless at cold boot (the ESP app starts far later). After a runtime signature change (dev-carrier jumper, connector bounce), firmware can briefly see 'off' while the bus is already on. Carriers are not told the about 5-20 ms enable delay or the fast-disable behaviour.

**Recommendation.** Document in carrier-interface §4.2: enable ≈ 5-20 ms after both pins reach 0 V with the card powered; disable < 10 µs. Firmware treats EXP_OE as valid only after it has been stable for ≥ 50 ms, and keeps EXP_2..11 high-Z whenever IO38 reads low.

**Skeptic.** I recomputed the numbers: tau = 10k*1uF = 10 ms. VIL 0.45 V is crossed at 10*ln(3.3/2.85) = 1.47 ms and VIH 1.2 V at 10*ln(3.3/2.1) = 4.5 ms. ESP VIH 0.75*3.3 = 2.475 V is reached at 10*ln(3.3/0.825) = 13.9 ms. Worst case, with Vf = 3.135 - 0.3 V leakage drop = 2.835 V and VIH = 2.35 V, it is 10*ln(2.835/0.485) = 17.7 ms. So IO38 reports 'on' about 10 ms after the switches conduct. Disable through Q1 is fast. This is a documentation and firmware observation only.

<a id="expansion-8"></a>

### expansion-8 — CONFIG_2/3 are not 'NC' on the card: the 1 MOhm to 3.3 V lifts host 1.8 V nets slightly and back-feeds an unpowered card rail (docstring/ADR say 'no back-feed')

Reviewer severity **info**, skeptic: **confirmed / info**, reviewer confidence high.

**Evidence.** R22/R23 1M +3V3 to CONFIG_2/CONFIG_3. Powered card, host 1.8 V pull-up R: V = 1.8 + 1.5*R/(1M+R), which is 1.815 V (10k), 1.94 V (100k), 2.05 V (200k). The M.2 module CONFIG output is 'GND or NC' (m2_pins_research.md:34). Unpowered card with a host or fixture pull-up: about 3.3 µA per pin flows into +3V3 through R22/R23. With Q1 on, R26 (10k) loads the rail, so the rail stays under ~0.3 V even with 12 x IPOFF, below the TMUX VDD < 1.5 V powered-off region. edge_expansion.py:12-14 and ADR 0006 §2 say 'host voltage only reaches insulated FET gates (no back-feed)'; carrier-interface §4.2 line 88 says 'NC on card'.

**Why it matters.** Electrically benign for host pull-ups ≤ ~150 kOhm on 1.8 V. However, the documentation is the contract the dev-carrier CG7 gap asks about, and it states something slightly different from the circuit.

**Recommendation.** Reword: 'card presents 1 MOhm to its 3.3 V rail on 75/1 (≤ 3.3 µA into an unpowered card, ≤ 1.5 µA into a 1.8 V host pull-up)'. That closes the CONFIG part of CG7.

**Skeptic.** The numbers check out: 1.8 + 1.5*100k/1.1M = 1.94 V at 100k, and the injected current is ≤1.5 uA. The docstring's 'no back-feed' and the contract's 'NC on card' are both inaccurate. There is a 1 MOhm path from the host pin to the card +3V3 rail (µA level, electrically benign because the unpowered rail is heavily loaded by the rest of the card). Documentation-only, so info.

<a id="expansion-9"></a>

### expansion-9 — Floating-host case (e.g. Mallow, pins 1/75 NC) depends on gate leakage and board leakage at a 1.1 MOhm node, which are specified only at 25 C

Reviewer severity **info**, skeptic: **confirmed / info**, reviewer confidence medium.

**Evidence.** Mallow X17 table: pin 1 NC, pin 75 not routed. Gate voltage = 3.135 - IGSS*1.1M must exceed Vth max at -40 C (about 1.14 V, Fig. 7.6 slope about -2.2 mV/C from the 1.0 V limit), which needs IGSS < 1.8 µA. SSM6N56FE IGSS is ±1 µA at ±6 V, 25 C only (§5.1); the second-source SI1024X is ±1 µA at 4.5 V. Surface leakage to GND below about 580 kOhm on the CONFIG/CFG nodes (R22-R25, Q1 at B.Cu ~(99.6-102, 119.8-123)) would also enable the bus on a floating host.

**Why it matters.** The margin exists but is not guaranteed over temperature or contamination. Failure enables the bus on the owner's primary host.

**Recommendation.** Include Mallow (floating CONFIG) at a hot-soak (~70 C) in S-v2-1. Ask JLC for standard board cleaning; no design change needed.

**Skeptic.** The margin arithmetic holds: (3.135 - 1.14)/1.1M = 1.8 uA allowed gate plus board leakage, against an IGSS spec of ±1 uA max measured at ±6 V and 25 C. The real operating point is about 3 V gate bias, so actual leakage should sit far below the spec limit, and the realistic risk is very low. I could not confirm the -40 C Vth extrapolation from Fig. 7.6 in text form. It stays an observation and test suggestion, so info is right.

<a id="layout-10"></a>

### layout-10 — Low-risk margins: copper to the V-cut long edges, broadside coupling between In2 and In3, router artifacts

Reviewer severity **info**, skeptic: **confirmed / info**, reviewer confidence medium.

**Evidence.** Copper to the long (V-cut) edges:
- Minimum is now 0.375 mm: USB_D_P via (110.4,144.25) and GND via (89.6,143.18).
- +3V3_M2 track at x 89.5 is 0.436 mm from the edge.
- Rev B's minimum was 0.48 mm. The planes stay at 0.3 mm, as in Rev B.
Broadside coupling:
- In2 and In3 are both signal layers, only 0.2028 mm apart (7628).
- Parallel overlaps within 0.2 mm laterally: EXP_6/EXP_11 6.8 mm, EXP_3_S/EXP_2_S 6.2 mm, EXP_7/EXP_5 6.0 mm, LED_STATUS_n/TXD0 4.3 mm.
- The USB pair only crosses In3 tracks perpendicularly.
Router artifacts: 54 collinear overlapping duplicate segments, and 0.05 mm stair-step segments (e.g. EFUSE_EN has 45 segments). There are no dangling ends.

**Why it matters.** None of these is functional for this order. The overlaps are short compared with GPIO rise-time saturation lengths. They are worth knowing if carriers later run fast SPI on EXP lines, and if JLC's DFM flags copper near the V-score.

**Recommendation.** No action for this order. For a future respin, keep In2/In3 parallel runs orthogonal and pull copper ≥0.5 mm from the V-cut edges.

**Skeptic.** The edge vias I found are consistent with the stated margins. USB_D_P via (110.4,144.25) and GND via (89.6,143.18) are 0.45 mm, which gives about 0.375 mm to a 89-111 mm outline. The +3V3_M2 B.Cu track at x 89.5 (0.127 mm) is 0.436 mm from the x=89 edge. Router stair-step 0.05 mm segments are plainly visible in the +3V3_M2 and +3V3_EFUSE dumps. I did not recompute the broadside-overlap figures. None of this is functional; info is correct.

<a id="layout-5"></a>

### layout-5 — Finished 6-layer thickness (0.83 ± 0.10 mm) can exceed the M.2 card-edge thickness of 0.80 ± 0.08 mm

Reviewer severity **minor**, skeptic: **confirmed / info**, reviewer confidence medium.

**Evidence.** docs/stackup.md:92 and v2/research/jlc_6l_stackup.md give JLC06081H-2116 as 'Finished 0.83 ± 0.10 mm' (0.73–0.93). The M.2 spec Rev 1.0 Fig. 15 (card edge) gives 0.80±0.08 (0.72–0.88). carrier-interface.md §2 says 'Card 22 mm wide, 0.8 mm'. My stack sum: 2×0.035 + 4×0.0152 + 2×0.1164 + 2×0.13 + 0.2028 = 0.826 mm before finish. This is new in v2; Rev B's 4-layer stack was nominal 0.8.

**Why it matters.** A thick-side board (>0.88 mm) raises insertion force and contact stress in tight sockets. Some hosts could be marginal. The contract does not reflect it either.

**Recommendation.** Ask JLC whether a 0.8 mm ±0.08 tolerance at the fingers is possible, or accept the risk explicitly. Measure the finger-area thickness of the 5 boards on arrival before inserting them into a host. Note the as-built thickness in carrier-interface.md §2.

**Skeptic.** docs/stackup.md:92 does say 'Finished 0.83 ± 0.10 mm' (0.73-0.93). The commonly cited M.2 card thickness is 0.8 ± 0.08 mm; I could not verify the exact figure locally. The '±0.10 mm' tolerance, however, is JLC's general tolerance for boards under 1 mm, and Rev B's 4-layer 0.8 mm board was ordered under the same tolerance. It was built and inserted into hosts without issue. The only thing that is new in v2 is a +0.03 mm shift of the nominal. The worst case (0.93 vs 0.88) existed in principle for Rev B too, apart from that 0.03 mm. The fingers are on a socket designed with spring contacts. Measuring the boards on arrival and recording the value in the contract is sensible. I downgrade to info: no evidence of a real defect, and the exposure is mostly inherited.

<a id="layout-6"></a>

### layout-6 — USB routing does not meet the 'length-matched, referenced to L2 GND' rule; functionally irrelevant at Full Speed

Reviewer severity **minor**, skeptic: **confirmed / info**, reviewer confidence high.

**Evidence.** Lengths from the board segments:
- USB_D_P 1.562 B + 42.26 total vs USB_D_N 36.09 total: 6.17 mm intra-pair.
- USBH3_D_P 5.76 vs USBH3_D_N 9.41: 3.65 mm the other way.
- Edge-to-module: P 48.0 vs N 45.5 mm (2.5 mm ≈ 17 ps).
Other observations:
- USBH3 has B.Cu runs (D_N 5.9 mm, D_P 3.9 mm) that reference In4 (+3V3), not In1 GND.
- The pair is coupled for only ~2 mm on F and on B, and its two vias differ (0.35/0.2 at 107.25,145.25 vs 0.45/0.3 at 108.1,146.95).
- USB_D_P on In2 at x=110.4 sits 0.525 mm from the board edge. The In1 plane extends only 0.225 mm past the trace edge (≈1.7·h, with h = 0.13 mm).
On In2 the pair is 0.15 mm wide at 0.5 mm pitch (0.35 mm gap). I estimate ≈ 87 Ω differential (asymmetric stripline, h1 0.13 mm to In1), within ±10%.

**Why it matters.** At 12 Mb/s (edges 4–20 ns) these skews and reference changes have no functional effect. But CLAUDE.md and Espressif HDG §1.4.8 state the rule, and docs/stackup.md claims compliance. The docs should not overstate the design. It would matter if the card is ever reused for High Speed.

**Recommendation.** Correct docs/stackup.md and the gate text to show the as-built skew and reference planes. Optionally move the right-edge In2 run ≥1 mm in from the edge and add a GND return via at each USB layer change (see layout-4).

**Skeptic.** I reproduced the lengths exactly: USB_D_P 42.26 mm (In2 40.70 + B 1.56), USB_D_N 36.09 mm (In2 35.03 + B 1.06), USBH3_D_P 5.76 mm (F 1.90 + B 3.86), USBH3_D_N 9.41 mm (F 3.50 + B 5.91). Edge-to-module skew is 48.02 vs 45.50, which is 2.5 mm. USBH3 does run on B.Cu, whose nearest plane is In4 +3V3, so 'referenced to L2 GND' is not true for that short section. However, the skew is already self-reported and accepted in docs/review-findings.md (GATE V3: 'Pair skew 5.2 mm (FS budget: rev B asserted < 10 mm)'). At 12 Mb/s it has no functional effect. What remains is wording in CLAUDE.md and stackup.md, so info rather than minor.

<a id="layout-7"></a>

### layout-7 — Bottom parts sit at the limit of M.2's bottom-side component zone (5.20 mm from the card edge); CG1 heights quantified

Reviewer severity **info**, skeptic: **confirmed / info**, reviewer confidence high.

**Evidence.** M.2 spec Rev 1.0 Fig. 17 sets the 'Bottom Side Component Zone Limit 5.20 MIN' (Fig. 16: top side 4 MIN). With the card edge at y=150.0, bottom bodies must stay at y ≤ 144.8. The B.Fab extents are:
- U1 (SOT-23-6, inherited from Rev B): 144.80, zero margin, courtyard 145.045.
- C14 (new eFuse input cap): body 144.75, pad 144.775, 0.05 mm margin, courtyard 145.075.
- C4: 144.15.
Top side: J3/J4 bodies end at 143.55 (2.45 mm margin).
Tallest bottom parts by datasheet (relevant to CG1): C1/C2 CL21A226MAQNNNE at 1.25±0.2 (1.45 max) and U1 SOT-23-6 at ≈1.45 max. That is over the 1.35 mm D2/D3 bottom limit but within D5's 1.5 mm. v2's new parts are lower: SOT-563, UQFN-16 (0.55 mm), VQFN-HR (≈1.0 mm).

**Why it matters.** These are inside the spec but with no placement tolerance. On a socket whose lower housing reaches exactly 5.2 mm, U1 or C14 could touch it. This is useful input for closing CG1.

**Recommendation.** If convenient, move C14 about 0.3 mm toward U6 (+y→−y). In the contract (CG1), state bottom parts ≤ 1.45 mm and ≥ 5.2 mm from the card edge, with U1/C14 at the limit.

**Skeptic.** The bottom-side B.Fab extents measured in the board match the finding: U1 fab bottom 144.80 (courtyard 145.045), C14 fab 144.75 / pad 144.775 (courtyard 145.075), and C4 fab 144.15 (pad 144.525). The other bottom parts end at y ≤ 143.8. I could not verify the 5.20 mm bottom-zone figure from the M.2 spec locally. If it is right, U1 and C14 sit at the limit. U1 is inherited from Rev B, which works in the Mallow socket. This is useful input for CG1 but not a defect, so info.

<a id="layout-8"></a>

### layout-8 — Antenna: keep-out matches the WROOM-1 antenna area, but the inner planes surround it on three sides (same as Rev B)

Reviewer severity **info**, skeptic: **confirmed / info**, reviewer confidence high.

**Evidence.** Rule area 'antenna_keepout_espressif_hdg' is (90,112.4)–(110,118.6) on all 6 layers, forbidding tracks, vias and pours. The module top edge is at 112.5, and the WROOM-1 land pattern gives a 6 mm antenna area with pin 1 at 7.49 mm, so the keep-out covers it. No track, via or pad intrudes: the closest GND vias are at y 118.85. F/B pours start at y 118.5. The In1 GND and In4 +3V3 fills do exist at (95,110.5), (100,112.2), (89.6,115) and (110.4,115), i.e. beyond the antenna tip and in 0.7 mm strips on both sides. The Rev B file has identical plane coverage, and its bring-up recorded WiFi scan at −58 dBm PASS. Espressif HDG §1.4.7 advises against a module 'in the center of the board with clearance created by hollowing out on all four sides'.

**Why it matters.** No change from a validated design, so the risk is low. Copper beyond the antenna tip detunes it slightly; the effect will show up as range or throughput rather than failure.

**Recommendation.** No change needed for this order. If an RF test (throughput or range) is planned for the release, include it in v2 bring-up.

**Skeptic.** I did not re-probe the antenna rule area in detail. The reviewer reports the plane coverage as identical to Rev B, and Rev B passed its WiFi scan, which makes this a no-change observation. No contrary evidence found; info is appropriate.

<a id="layout-9"></a>

### layout-9 — About 100 pads rely on filled and capped via-in-pad, including the bottom 0.4 mm-pitch UQFN pads, the JST pads and FB1's only +3V3 plane via

Reviewer severity **info**, skeptic: **confirmed / info**, reviewer confidence high.

**Evidence.** vip.py found vias whose drill lies inside the pad on U2.2/13/14/21/22/27/36/37/40/41, J4.1 (TXD0), J4.4, J3.1, U3.5/8/9/13/16, U4.5/8/13, U5.5/9, Q1/Q2/Q3 GND pads, RN1–RN3 and many 0402/0603 pads. FB1.2's only connection to the In4 plane is via (90.0,138.75, 0.3 mm drill), whose drill cuts the pad's rounded corner. fab/README.md:28 requires 'Via Covering: Epoxy Filled & Capped'. One 0.3 mm via ≈ 0.019 mm² of plating, enough for the 1.15 A limit.

**Why it matters.** If the order reaches production with tented or plugged-only vias, solder wicks away from the module USB pads, the UQFN pads and the JST pads. That causes opens and assembly failures.

**Recommendation.** Make 'Epoxy Filled & Capped' a hard checklist item on the order. Confirm it in JLC's production-file email and in `make jlc-check`. Consider adding a second +3V3 via at FB1.2.

**Skeptic.** fab/README.md:28 does make 'Via Covering: Epoxy Filled & Capped' a stated requirement, and docs/stackup.md says it is the 6-layer default. Several via-in-pads are visible in the data I pulled: the R31.1 via (93.7,139.7) and the USB vias into the module pads per v2-gate-v3.md:43 'via-in-pad into the module'. I did not recount all ~100 via-in-pad instances. The risk only materializes if the order option is changed, so this is an order checklist item, i.e. info.

<a id="mcu_io-10"></a>

### mcu_io-10 — J3/J4 (cabled user connectors) go straight to ESP32 pins: no ESD protection, no TX series resistor

Reviewer severity **info**, skeptic: **confirmed / info**, reviewer confidence high.

**Evidence.** Board: TXD0 = J4.1 and U2.37 only; RXD0 = J4.2 and U2.36; IO8/IO9 = J3.3/J3.4 and U2.12/U2.17; IO10-14 and IO21 likewise. HDG sec. 1.3.7: 'It is recommended to connect a 499 Ohm series resistor to the U0TXD line'. ESP32-S3 HBM is +/-2 kV. J3.2 supplies the card +3V3 rail to external cables with no limiter other than the eFuse (0.85-1.15 A). IO8-14 show 60 us low-level glitches at power-up (Table 2-2), which external SPI/I2C devices will see. Unchanged from Rev B (positions identical: J3 (106,142.5) and J4 (95.8,142.5)).

**Why it matters.** These are field-robustness and EMC margins on externally cabled ports, not a functional defect. They are inherited and already built.

**Recommendation.** Accept for this RC, but record it. A future revision could add a series R on TXD0 and a low-cap ESD array on J3/J4 if space allows.

**Skeptic.** This is inherited Rev B circuitry and has been built and validated. J3/J4 connect directly to ESP32 pins with no series resistor or ESD array. This is a robustness observation, not a defect. I did not re-verify the HDG 499 Ohm quote page, but the recommendation exists in the Espressif HDG and is commonly cited.

<a id="mcu_io-4"></a>

### mcu_io-4 — K3 extended: a wrong JLC rotation sign on Q1-Q3 is electrically harmless, and the checklist text claiming otherwise is wrong

Reviewer severity **info**, skeptic: **confirmed / info**, reviewer confidence high.

**Evidence.** fab CPL: Q1/Q2/Q3 bottom, 270 (KiCad 180 + JLC_ROT 90). The two candidate signs (+90/-90) differ by 180°. On a 180° turn of the SOT-563 (pinout 1 S1, 2 G1, 3 D2, 4 S2, 5 G2, 6 D1), physical pin k lands on pad k+3. Q2: S1/S2 stay on GND, physical G2/D2 land on IO42/LED_1_n and G1/D1 on IO47/WAKE_ON_WWAN_n, so gate-to-drain pairing is preserved and the function is identical. Q3: physical G2 on W_DISABLE2_n, D2 on IO40, G1 on the GND pad (pad 5), D1 on the NC pad (pad 3), so the function is identical. Q1 is symmetric (both drains on EXP_OE, both sources on GND). fab/polarity_checklist.md row Q2 says '180 off swaps LED_1#/WAKE#', which is incorrect. An actual 90° error leaves the 6 leads off the 2x3 pad rows and is obvious in the DFM.

**Why it matters.** K3 is a cosmetic risk for the FETs: only the pin-1 marker position is at stake. The wrong checklist text could lead the DFM reviewer to reject a correct placement or ask JLC for a needless rotation.

**Recommendation.** Correct the Q2 note in polarity_report.py so it reads '180 off is electrically equivalent (symmetric dual FET); 90 off does not land on the pads'. Keep the TMUX1511 (U3-U5) sign check as the real K3 concern; that part is not symmetric.

**Skeptic.** I checked the 180-degree mapping with pinout 1 S1, 2 G1, 3 D2, 4 S2, 5 G2, 6 D1, where physical pin k lands on pad k+3. Q2: physical G1/D1 land on pads 5/3 (IO47/WAKE) and G2/D2 on pads 2/6 (IO42/LED_1). Gate-to-drain pairing is preserved and both halves are identical, so the function is the same. Q3: physical G2/D2 land on pads 2/6 (W_DISABLE2_n/IO40) and G1 on pad 5 (GND), so it works. Q1 is symmetric. The checklist text '180 off swaps LED_1#/WAKE#' is misleading. The gen_fab comment ('swaps Q-halves') is literally true but harmless. The TMUX1511 sign is still the real K3 risk.

<a id="mcu_io-8"></a>

### mcu_io-8 — USB pair: no series R is fine (same as Rev B 0R), but the 'length-matched' and '90 Ohm' claims do not hold for the new In2 route

Reviewer severity **info**, skeptic: **confirmed / info**, reviewer confidence high.

**Evidence.** Board tracks: USB_D_P In2 40.70 + B 1.56 = 42.26 mm; USB_D_N In2 35.03 + B 1.06 = 36.09 mm (6.2 mm intra-pair). End to end with USBH3: P 48.0 mm and N 45.5 mm (2.5 mm, about 17 ps at FS, where 1 bit = 83 ns). Width 0.15 mm on In2, which sits 0.13 mm over In1 GND with In3 (signal) 0.20 mm below. docs/stackup.md computes impedance only for the L1-over-L2 microstrip. Series R: HDG sec. 1.3.13 asks to *reserve* 22/33 Ohm plus caps; Rev B had populated 0 Ohm links, so the electrical path matches the validated board. Both via-in-pad vias on U2.13/14 (0.45/0.30) rely on 'Epoxy Filled & Capped' (fab/README.md:28).

**Why it matters.** No functional risk at 12 Mb/s. The CLAUDE.md rule ('90 Ohm differential, length-matched') is not literally met, and a future HS use or re-tune would have no footprint left.

**Recommendation.** Record the deviation in the stackup and usb_esd LESSONS ('FS only; skew 2.5 mm accepted; In2 impedance not controlled'). Make sure the order keeps filled-and-capped vias selected.

**Skeptic.** I re-measured the USB track lengths with pcbnew and they match the reviewer's numbers. USB_D_P: In2 40.70 + B 1.56 = 42.26 mm. USB_D_N: In2 35.03 + B 1.06 = 36.09 mm. Adding the USBH3 sections (P 5.76 mm, N 9.41 mm) gives 48.0 mm vs 45.5 mm end to end, a 2.5 mm skew. At full speed (12 Mb/s) this has no functional effect. The literal CLAUDE.md rule ('90 Ohm, length-matched') is not met on In2, so recording the deviation is the right action.

<a id="mcu_io-9"></a>

### mcu_io-9 — The N16R8 'drop-in fallback' is limited to 65 °C ambient

Reviewer severity **info**, skeptic: **confirmed / info**, reviewer confidence high.

**Evidence.** WROOM-1 datasheet ordering table: N8R2 -40~85 °C; N16R8 (octal PSRAM) -40~65 °C, with a note on PSRAM ECC derating (datasheet lines around 104-126). docs/pinmap.md sec. 6.1 calls N16R8 a fallback, and IO35-37 are NC for it (verified: U2 pads 28-30 have no net). The R16V variants are not acceptable on IO47/IO48 (1.8 V); the circuit would tolerate it (Q2b VGS 1.8 V, red LED off at 1.8 V), but nothing documents it.

**Why it matters.** An M.2 slot inside an enclosure can exceed 65 °C. A stock-driven module swap would silently lower the card's rating.

**Recommendation.** State the 65 °C limit next to the fallback in pinmap/BOM notes, and explicitly exclude the *R16V variants.

**Skeptic.** The WROOM-1 datasheet Table 1-1 lists N16R8 at -40 to 65 °C (85 °C only with PSRAM ECC and 1/16 of the PSRAM lost), while N8R2 is rated -40 to 85 °C. pinmap.md calls N16R8 a drop-in fallback without the temperature caveat. One small correction: R16V is partly addressed. pinmap.md:264 notes that IO47 runs at 1.8 V on R8V/R16V chips, though it does not explicitly exclude those variants.

<a id="power-10"></a>

### power-10 — Fingers 2 and 4 contribute almost nothing: they reach U6 through a ~0.2 Ω 5-mil trace, and R31's OVLO sense pad sits in that path

Reviewer severity **info**, skeptic: **confirmed / info**, reviewer confidence high.

**Evidence.** +3V3_M2 path from J1.2/J1.4 (108.5-109, 148.75): 0.2 mm B.Cu, via 108.75,145.6, In2 0.127 mm, via 106.5,141.7, B.Cu 0.127 mm, via 101.15,136.65, In3 0.127 mm, via 93.7,139.7 to the R31 pad, then via 93.8,141.85, In3, via 92.35,145.65. That is about 28 mm of 0.127 mm, about 0.2 Ω. Fingers 70/72/74 use 0.35 mm, about 7 mΩ. Three contacts at 0.5 A each give 1.5 A, more than ILIM max 1.15 A, so this is acceptable. If a host or adapter wires only pins 2/4, the card would see about 0.1 V more drop and a hot 5-mil inner trace at 0.5 A.

**Why it matters.** It is not a defect, but the contract says 'pins 2, 4, 70, 72, 74' as if all five share the current.

**Recommendation.** Optionally widen the 2/4 feed in a future revision. Note it in the layout lessons.

**Skeptic.** I traced the board path. J1.2 and J1.4 (about 108.6-108.95,147.6) go through 0.2 mm B.Cu to a via at 108.75,145.6. From there: In2 0.127 mm (about 4.8 mm) to a via at 106.5,141.7, then B.Cu 0.127 mm (about 7.3 mm) to a via at 101.15,136.65, then In3 0.127 mm (about 11 mm) to a via at 93.7,139.7, the R31.1 pad and B.Cu. After that comes a via at 93.8,141.85, In3 for about 4.8 mm, and a via at 92.35,145.65 onto the 0.35 mm feed of fingers 70/72/74. That is roughly 28-30 mm of 0.127 mm trace, about 21 mm of it on 0.5 oz inner copper (about 7.7 mΩ/mm), so about 0.2 Ω in total. Fingers 2 and 4 therefore carry almost no current. Three contacts at 0.5 A each still give 1.5 A, above ILIM max 1.15 A, so this is not a defect. The OVLO tap (R31) sits on this path, but because the path carries little current, the voltage error there is negligible.

<a id="power-7"></a>

### power-7 — Reverse-current blocking on a noisy host rail can make the card sag below the host rail for tens of microseconds

Reviewer severity **info**, skeptic: **uncertain / info**, reviewer confidence low.

**Evidence.** Datasheet EC: RCB entry VREVTH is -22 to -36 mV (tRCB 1 us). Exit VFWDTH is 83-125 mV, then tSWRCB 50 us before VOUT rises. Light-load forward regulation VFWD is 16.9 mV. If the host rail dips by more than about (I x RON + 29 mV) faster than the about 43 uF card bulk discharges, the blocking FET opens. The card then runs on its bulk until VIN - VOUT exceeds 83-125 mV, plus up to 50 us. Speculative: at 0.35 A that could add roughly 0.1-0.4 V of extra droop, depending on whether the blocking FET's body diode conducts.

**Why it matters.** On hosts with fast load-step dips, for example a Pi HAT adapter feeding 3V3 from the SBC buck, the card could brown out where Rev B (no eFuse) would not.

**Recommendation.** Bring-up: scope +3V3_M2 and +3V3 together during WiFi TX and during host load steps on the dev carrier and Mallow. If dips appear, larger card bulk does not help; host-side capacitance does.

**Skeptic.** The mechanism is real per the datasheet. BFET fast turn-off happens when VIN - VOUT < VREVTH (-22 to -36 mV, within 1 us). Re-entry needs VIN - VOUT > VFWDTH (83-125 mV) plus tSWRCB (50 us). At 0.35 A into an effective 43 uF the card bulk discharges at about 8 mV/us, so the worst-case extra sag is bounded at about 0.1 V + 50 us × 8 mV/us ≈ 0.4-0.5 V. The BFET body diode, which in a common-drain back-to-back pair conducts forward, may clamp it earlier. Whether any host rail falls faster than the card bulk discharges, by more than about 30-40 mV, is unknown. No measurement exists, so the impact cannot be settled from documents. It would be settled by scoping +3V3_M2 and +3V3 together during WiFi TX and host load steps on Mallow and the dev carrier.

<a id="power-8"></a>

### power-8 — eFuse status cannot be observed or controlled: FLT, AUXOFF, DVDT and ITIMER have no pads or test points, EN is hard-wired, and the host cannot power-cycle the card

Reviewer severity **info**, skeptic: **confirmed / info**, reviewer confidence high.

**Evidence.** U6 pins 3, 4, 7 and 10 have no net (board pads with an empty netname; power_3v3.py:43-45). EN is R33 1 MΩ to IN, with no test point. M.2 §3.2.10.1 requires FULL_CARD_POWER_OFF# to have a card-side weak pull-down, so wiring pin 6 to EN would switch the card off on Mallow, which has no driver (pinmap.md:216). Correctly left NC.

**Why it matters.** Bring-up cannot tell a current-limit event (FLT asserts on persistent overcurrent, Table 7-3) apart from other dropouts. Recovering from power-1 needs a slot power cycle.

**Recommendation.** If layout allows, add a test pad on U6.4 (FLT), with a pull-up on the bring-up fixture, and on EFUSE_EN. No change to pin 6.

**Skeptic.** The board pads for U6 pins 3, 4, 7 and 10 have empty netnames. EFUSE_EN has only R33.2 and U6.1, with no test point (TP1/TP2 are EN and BOOT of the ESP). M.2 §3.2.10.1 requires a card-side weak pull-down on FULL_CARD_POWER_OFF#, so leaving pin 6 NC is correct. Table 7-3 shows FLT is not asserted (H) on input overvoltage, so FLT would not reveal an OVLO lockout anyway. A test pad on U6.4 and on EFUSE_EN is a reasonable testability addition, but the U6 surroundings on B.Cu are tight, so feasibility is unverified.

<a id="power-9"></a>

### power-9 — ILM sense trace runs a long way round on F.Cu near SPI CLK and RXD0

Reviewer severity **info**, skeptic: **confirmed / info**, reviewer confidence medium.

**Evidence.** EFUSE_ILM: 8.87 mm F.Cu plus 0.87 mm B.Cu with 2 vias, from U6.9 (90.7,141.68) to R34 (95.8,142.6, which is 5 mm away). Edge spacing is 0.32 mm to IO12 (J4 SPI CLK) over about 1.9 mm, and 0.27 mm to RXD0 over about 0.9 mm (F.Cu). Datasheet §8.4.1: keep ILM 'away from any noisy (switching) signals', with parasitic capacitance under 50 pF; the estimated about 2 pF is fine. With ITIMER open, an ILM disturbance acts immediately.

**Why it matters.** The risk is low, but this is the only analog control node next to a fast digital edge.

**Recommendation.** If U6 or R34 is touched for power-1, power-3 or power-4, move R34 next to U6.9 or guard the trace with GND. Otherwise accept it.

**Skeptic.** Geometry checked with KiCad python. EFUSE_ILM runs from U6.9 (90.7,141.68) through a via at 89.95,141.1, then about 8.9 mm of 0.127 mm F.Cu, then a via at 96.1,142.2 to R34.1 (96.31,142.6). R34 sits about 5.6 mm from U6.9, which is not 'close to the connection pins' as §8.4.1 asks. The nearest F.Cu neighbours edge to edge are IO12 at 0.32 mm over several segments, RXD0 at 0.273 mm, and EFUSE_EN at 0.32 mm. The capacitance is far below the 50 pF limit. The coupling risk is low and unquantified, so info is right.

## What the reviewers checked and found correct

### Expansion bus and carrier detect

I reviewed the expansion bus and carrier-detect area against the primary sources: hardware/blocks/edge_expansion/edge_expansion.py, hardware/design.py, the per-pin connection table, a pad-level dump of the KiCad board (Q1, U3-U5, RN1-RN3, R20-R26, C10-C13, J1), the TMUX1511 datasheet (SCDS390B §4, 5.2, 5.5, 5.7), the SSM6N56FE datasheet (§3, §5.1, Fig. 7.2/7.6), the ESP32-S3 datasheet v2.2 (Tables 2-1 and 2-2, DC characteristics), the Mallow X17 pin table, and the dev-carrier SPEC and blocks.

The netlist and copper match docs/carrier-interface.md §4.2/4.3 exactly: all 12 EXP lines go to the right M.2 pin, TMUX channel, 220R array element and GPIO. The board has 0 unconnected items. Logic levels have margin:
- EXP_OE high is at least 2.83 V at 3.135 V supply with the TMUX datasheet's maximum leakage (12 x 2 uA IIH plus 6 MOhm pull-downs), above both TMUX VIH (1.2 V) and ESP32 VIH (2.35 V).
- Q1 turns on with a 1.71 V host pull-up even at -40 C (Vth worst case about 1.14 V).
- Q1 has built-in gate protection zeners, so its gates are ESD-protected.
- With the card unpowered, the TMUX1511 meets the 2 uA leakage limit (IPOFF max +/-2 uA at 0-3.6 V), and the card rail stays well below 1.5 V.

I found no blocker or respin-class defect in this area. The main weakness is in the design and contract: the detect circuit treats "pin at 0 V" as "carrier present". Any host load stronger than about 65-435 kOhm to ground enables the bus. That includes a host pull-up to an unpowered rail, a SoC GPIO's default pull-down, or a GPIO driven low. In that case the bus turns on in a normal host. The likely effect is mild: about 0.3-0.6 mA from the card's 3.3 V I2C pull-ups into SIM lines, plus I2C probe traffic. Firmware can limit it at no cost by pulling IO38 low when no ID EEPROM answers. That same IO38 net is a contention risk if firmware ever drives it high (up to about 40 mA through Q1).

The rest are contract and documentation gaps:
- The contract advertises UART/SPI from the carrier into the card but also forbids carriers from driving card pins high.
- State 6 cannot be told apart from a Telit FN990 modem.
- There is no I2C speed or bus-capacitance budget.
- There is no ESD rule for carriers that bring EXP lines out to connectors.
- The bus stays enabled while the ESP32 is in reset, which the power-up glitch argument does not cover.
- The enable/disable timing is not stated.
- The "no back-feed" wording is not exact (about 3.3 uA flows through the 1 MOhm pull-ups into an unpowered card).

None of these changes the board.

- Net-to-pin path for all 12 EXP lines checked in the KiCad board, pad by pad: J1 pins 30/32/34/36/40/59-65 go to EXP_0..11, then TMUX D pins (U3/U4/U5 D1-D4), then EXP_n_S on the S pins, then the RN1-RN3 elements (R1=pads 1-8 ... R4=4-5), then IO39/41/1/2/18/4/5/6/7/15/16/17. This matches carrier-interface §4.3 and pinmap §6.2.
- TMUX1511 symbol and footprint pin numbering match the datasheet RSV/UQFN column (SEL1=1 ... VDD=16, NC 7/12 unconnected). Footprint pad order is counter-clockwise from pin 1 on the 1.8 x 2.6 mm body.
- SSM6N56FE pinout in common.py (1 S1, 2 G1, 3 D2, 4 S2, 5 G2, 6 D1) matches datasheet §3. On the board: Q1 G1=CFG2_G, G2=CFG3_G, both drains on EXP_OE, sources to GND. The second source SI1024X has the same pinout (dual_nmos_research.md:27).
- TMUX1511 SEL polarity is active-high with 6 MOhm internal pull-down (Pin Functions table). All 12 SELs are on EXP_OE. VDD is the card +3V3 (eFuse output), with one 100 nF per chip (C10-C12).
- EXP_OE high level: 3.3 V - 10k x (12 x 2 uA + 12 x 0.55 uA) ≈ 2.99 V (2.83 V at 3.135 V), above TMUX VIH 1.2 V and ESP32-S3 VIH 0.75*VDD (2.35-2.475 V), so IO38 readback is valid.
- Q1 on with a 1.8 V (-5%) host pull-up at -40 C: Vgs ≈ 1.6 V against Vth about 1.14 V worst. RDS(on) under 0.5 Ohm at 0.33 mA, so EXP_OE ≈ 0 V, below VIL 0.45 V. Off with carrier GND, including hot IDSS.
- Q1 gates have integral gate-protection zeners (datasheet §3 diagram), so the 100k-isolated gates are ESD-safe.
- Power-up sequencing: Q1 gates follow +3V3 within about 75 us (1.1 MOhm x ~70 pF), while EXP_OE needs ≥1.5 ms to reach TMUX VIL, so there is no enable glitch at power-up on a non-carrier host. Discharging C13 through Q1 stays within IDP 1.6 A and is only 5.4 uJ.
- Powered-off protection: TMUX1511 IPOFF ≤ ±2 µA at VDD=0, VS 0-3.6 V (§5.5), so the contract's '≤ 2 µA at 0–3.6 V' and S-v2-1 hold (25 C typ 10 nA). The card +3V3 stays under 1.5 V when unpowered with host pull-ups present (R26 load through Q1). Powered with the bus off: ID(OFF) ≤ 100 nA, and signals up to 2xVDD/5.5 V are allowed.
- I2C pull-ups R20/R21 4.7k sit on EXP_0_S/EXP_1_S (MCU side), so the edge is isolated when the bus is off. ESP low through 220R adds about 0.15 V, and slave low through Ron ≤ 4.5 Ohm adds about 3 mV; both are within I2C VIL.
- GPIO choices: no strapping pins (0/3/45/46) on EXP. ADC lines EXP_2/3/5/6/7/8 = IO1/2/4/5/6/7 = ADC1_CH0/1/3/4/5/6, usable with Wi-Fi. IO39 WPU at reset is redundant with R20. IO38 has no reset pull (IE only), so the readback adds no load. The IO18 power-up high glitch is masked by the EXP_OE RC at cold power-up. IO15/16 are XTAL_32K pins, fine as digital lines while the 32k crystal is unused.
- CONFIG_0 (J1.21) and CONFIG_1 (J1.69) are hard-wired to GND (state 6), and CONFIG_2/3 have only the 1M pull-up plus 100k gate path, matching carrier-interface §4.2.
- Mallow X17: pins 1/21/69 NC and 75 absent (floating, so the bus stays off). Pins 30-36 are SIM, 40 is a GPIO to header X16, and 59-65 are NC.
- Board connectivity: 0 unconnected items overall. EXP/EXP_S nets use only F.Cu/B.Cu/In2/In3 (no signal on the In1 GND or In4 PWR planes).
- Dev carrier: CONFIG_0/1 have 100k pull-ups (fine against card GND). JP2/JP3 offer GND/open/10k-1V8/10k-3V3. The ID EEPROM is at 0x50 with no carrier pull-ups and jumpers open by default. EXP goes straight to J3. All consistent with the card netlist.

### Power path and protection

Power path review (power_3v3 and everything on +3V3_M2, +3V3_EFUSE and +3V3) against the TPS25947 datasheet (SLVSFC9C), the ESP32-S3-WROOM-1 datasheet and HDG, M.2 Rev 1.0, the SKiDL sources, the connection tables and the routed board (read with KiCad python). The basics are correct: U6 pinout matches the footprint, the OVLO window works out to 3.437-3.570 V including 0.1 % resistors and pin leakage, the current limit is 0.85-1.16 A against roughly 0.4-0.5 A of real load, the ~18.9 V survival figure is right, reverse-current blocking protects the host from J3/J4 backfeed, and bulk decoupling is placed as the HDG asks.

The main new problem (power-1, major) is OVLO hysteresis. The release threshold divided back to IN is 3.133-3.250 V. A nominal 3.3 V host puts 1.133 V on the OVLO pin, which is above the 1.116 V maximum release threshold. So after any trip, even a microsecond spike, the card stays off until the slot is power-cycled. The OVLO pin has no filter, and the trip point is only 137 mV above 3.3 V. SPEC, the contract and S-v2-3 say "auto-recovers below ~3.17 V", which hides this.

Second (power-2, major if it is ever used): the "same-footprint" second source TPS259474LRPWR is a latch-off circuit-breaker part. With ITIMER open, any load above 0.85 A latches the card off until power-cycle. Its pins 3 and 4 are PG and PGTH, not AUXOFF and FLT.

Other findings, all minor or info:
- K1 refined: M.2 Table 39 lets hosts soft-start the slot at 200 mA. The proposed 1.8 nF DVDT capacitor still meets that at worst-case charging current, but it must be rated 25 V or more. After an OVLO trip, restart skips dVdt anyway.
- U6 OUT (+3V3_EFUSE) has no capacitor, though TI asks for at least 1 uF right at OUT. Fitting 0 R instead of FB1 would fix it with no layout change.
- The voltage-drop budget leaves out the socket contact resistance, and J3 (Qwiic) has no current budget.
- Several documents are stale.
- Info only: reverse-blocking behaviour on noisy host rails, no way to observe FLT or power-cycle the card, ILM routed near SPI CLK, and pins 2/4 fed through a thin trace.

- U6 footprint pin map against datasheet Fig. 5-1: EN at pin 1 (L-corner), OVLO at 2, AUXOFF and FLT at 3/4, IN strip on the pin 1-4 side, OUT on the pin 7-10 side, GND at 8, ILM at 9, and pin 10 sharing a row with pin 1. All correct, and the board reports 0 unconnected.
- +3V3_M2 net has only J1.2/4/70/72/74, U6.IN, C14, R31 and R33. Nothing else on the card sees the unprotected rail.
- OVLO window with 0.1 % resistors and ±0.1 uA leakage is 3.437-3.570 V, never above the ESP32-S3 3.6 V abs max for slow ramps. For a hard step the fast-trip (2 x ILIM within 500 ns) plus the 1.2 us OVLO response limits the rail rise to about 25 mV.
- The '~18.9 V survival' claim holds: 6.5 V OVLO abs max x 2.912 = 18.93 V. IN is rated 28 V, C14 is 50 V, and EN goes through 1 MΩ, which meets the ≥350 kΩ of Table 6.3 note 2. EN leakage drop is ≤ 0.1 V.
- EN/UVLO tied to IN: the device enables at VUVP(R) 2.44-2.64 V, well below the 3.135 V host minimum. Turn-off at VUVP(F) 2.35-2.55 V gives clean behaviour on a slow host ramp, and the +3V3 rail starts from about 2.5 V, so the ESP32 EN RC (10 kΩ/1 uF) still meets tSTBL of 50 us or more.
- ILM 3.3 kΩ (within the 549-6650 Ω RILM range) gives about 0.855-1.16 A from the 3.32 kΩ row. That is well above the ESP32-S3-WROOM-1 TX peak of 355 mA plus LEDs, TMUX and pull-ups, and meets the module's '≥0.5 A supply' requirement (WROOM Table 6-2, HDG §1.3.2).
- DVDT, ITIMER, FLT and AUXOFF left open is allowed by the datasheet (pin table, §7.3.5 notes). The auto-retry variant restarts every 110 ms after a hard short and thermal shutdown, so a shorted card cannot damage the host.
- Backfeed with the card unpowered: J3/J4 (Qwiic or UART adapters) phantom-power +3V3 but are blocked from the host by U6 reverse-current blocking (IREVLKG(OFF) ~4.9 uA). D1 (BAT54A) orientation lets EN pull PERST_n but never the reverse. The W_DISABLE2_n 1 MΩ pull-up passes at most ~3.3 uA. The USBLC6 VBUS pin on +3V3 does not backfeed from an idle host.
- ESD on the +3V3_M2 finger: IEC 8 kV/150 pF into C14 100 nF gives about 12 V, below the IN and OVLO (about 4.1 V at the pin) limits.
- Decoupling against the HDG and module datasheet: C1 22 uF (B.Cu, about 1.8 mm from module pin 2), C6 100 nF and C7 10 uF at the 3V3 pin, C3 10 uF at the FB1 output, and the In4 +3V3 plane fed by 27 vias. Main feed fingers 70/72/74 to C14 to U6.IN is about 5 mm of 0.35 mm B.Cu (about 7 mΩ). OUT to FB1 is 1.5 mm of 0.35 mm.
- FB1 BLM18PG121SN1D is rated 2 A with DCR ≤ 50 mΩ. The FB1-bulk LC (about 35 kHz, Q about 1.6) is well damped.
- OVLO divider sense point is about 4 mm from U6.IN via a thin, current-free branch (Kelvin-like). The IR error from the fingers 2/4 current through the R31 pad is ≤ 5 mV.

### MCU, sidebands, USB, LEDs, recovery

Area reviewed: MCU, sidebands, USB, LEDs and recovery (esp32s3_companion, host_sideband, sideband_recovery, usb_esd, leds, io_header). I checked the SKiDL sources against the board file pad by pad, then against the datasheets (ESP32-S3 v2.2 Tables 2-1 and 2-2, WROOM-1 Table 3-1, SSM6N56FE, USBLC6, TJ-S1706, M.2 EM spec Rev 1.0, Mallow Table 10). `make check` passes (ERC clean, v2 netlist check PASS on 76 nets). `make drc` passes (0 violations, 0 unconnected).

Nothing in this area blocks the order. Netlist and board agree on every net I traced. The strapping, reset-state and glitch rules are respected: IO42, IO47, IO40 and IO38 have no pull at reset and no power-up glitch. Q2 gates are held off by 100k while the ESP is in reset or download mode. The EN/BOOT diode isolation is unchanged from Rev B, and v2 adds nothing to the EN or IO0 nets. The side-view LED fix only swaps pad numbers, with the same placement, the same emit arrow and the v1 CPL rotation of +0, so it agrees with the GATE B3 evidence. JLC's confirmation on the physical part is still pending (K2).

The real issues are on the new host-facing input cell:
- R29 (1 MΩ) is outside the M.2 spec range of 100-200 kΩ, although the docs say it follows the spec. Fixing it is a value swap with no layout change.
- The Q3 gate sits directly on edge finger 26 with no ESD protection.
- The pin-20 BOOT leg contradicts ADR 0006's own rule against using pins 20-28 always-on, and it has no risk-register entry.
- WAKE_ON_WWAN# cannot work on hosts that hold PERST# low while asleep.

For K3: the two candidate rotations for Q1-Q3 differ by 180°, and a 180° turn of this SOT-563 dual FET is electrically harmless. The checklist text that says otherwise is wrong. The SI1024X second source has no datasheet in the repo and no JLC_ROT row. The remaining findings are documentation and testability items.

- Board vs netlist parity, pad by pad, for every net in my area: EN {U2.3,R1.2,D1.3,TP1,C5.1}, IO0 {U2.27,R2.2,D2.3,TP2}, PERST_n, PCIE_1_GPIO_5, W_DISABLE1_n, W_DISABLE2_n, IO40/42/47, LED_1_n, WAKE_ON_WWAN_n, USB_D_P/N, USBH3_D_P/N, LED_STATUS_n/A, LED_PWR_A, TXD0/RXD0, IO8/IO9, EXP_OE. make check (ERC clean, v2 netlist check PASS) and make drc (0 violations, 0 unconnected) both pass.
- Strapping: IO3 (pad 15), IO46 (pad 16) and IO45 (pad 26) are NC on the board. The defaults per ESP32-S3 Table 2-1 give SPI boot and 3.3 V VDD_SPI. GPIO46 WPD prevents the invalid IO0=0/IO46=1 combination. IO0 has 10k pull-up plus internal WPU.
- IO35-37 (pads 28-30) are NC, so N8R2 and N16R8 are pin-compatible. IO47/IO48 run at 3.3 V on N8R2 (ESP32-S3R2, not R8V/R16V); even at 1.8 V the circuit would still work (Q2b VGS 1.8 V, red LED stays off).
- Reset and glitch behaviour of the host-facing GPIOs (Table 2-1/2-2): IO38, IO40, IO41, IO42 and IO47 have no pull at reset and are not in the power-up glitch table. IO39 WPU and the IO18 high glitch are only on EXP lines behind the switches. Q2 gates are held at 0 V by R27/R28 100k (IGSS 1 uA gives at most 0.1 V), so LED_1# and WAKE_ON_WWAN# are released during power-up, reset, ROM download mode and firmware crash.
- Q2/Q3 pin mapping vs the Toshiba ES6 pinout (1 S1, 2 G1, 3 D2, 4 S2, 5 G2, 6 D1): IO42 drives D1 (LED_1_n), IO47 drives D2 (WAKE), W_DISABLE2 drives G1 with drain IO40 plus the 10k pull-up. The spare half has its gate and source on GND. RDS(on) at VGS 1.8 V is at most 480 mOhm, so IO40 sits near 0 V with a 0.33 mA load. Drains are 20 V-rated with body diodes reverse-biased for positive host pull-ups, so there is no back-feed when the card is unpowered.
- M.2 pin assignments vs spec Table 26: 10 = GPIO_9/LED_1# (OD, 3.3 V), 23 = GPIO_11/WAKE_ON_WWAN# (OD, host pull-up), 26 = GPIO_10/W_DISABLE2# (input, 1.8 V), 8 = W_DISABLE1#, 50 = PERST#, USB D+/D- on 7/9. On Mallow, pins 10/23/26 only reach header X16 (floating), so Q3 is on and IO40 reads 0 (radio allowed); pin 8 has a 47k pull-up.
- EN/BOOT recovery unchanged from Rev B: same parts, same positions, no v2 loads on EN or IO0. The BAT54A common anode (pin 3) is on the card side. EN RC is 10k/1uF (tau 10 ms, per HDG sec. 1.3.3). The diodes block host back-feed into an unpowered card.
- USBLC6-2SC6 is placed about 5 mm from fingers 7/9 at the same position as Rev B: pins 1/3 edge side, 6/4 MCU side, VBUS pin 5 on +3V3 with C4 100nF next to it. Its orientation matches the ST pinout (top row I/O1-VBUS-I/O2, bottom row I/O1-GND-I/O2), and it has a GND return (DRC shows 0 unconnected).
- Removing the USB series R is electrically identical to Rev B's populated 0R links, which were validated at FS. The via-in-pad on U2.13/14 is covered by the filled-and-capped option in fab/README.md.
- Side-view LED fix: the v2 footprint only renumbers pads (pin 1 = K at local +x). Placement, rotation (90, bottom) and the B.Fab emit arrow (pointing -x toward the edge at x=88.975) match Rev B exactly. The anode pads (D3.2 at y 130.70, D4.2 at y 127.30) are level with R3.2/R4.2 (130.625/127.225). The silk cathode bar sits at the pad-1 end. CPL is 90 for both, the same as v1, and Rev B used 270, which is consistent with the GATE B3 evidence. The land pattern matches the vendor's recommended layout (0.80x0.70 pads, 1.00 gap, 2.60 overall, 1.80 c-c).
- LED currents: green 100R gives about 5 mA typical and at most about 8.6 mA (rail 3.465 V, Vf 2.6 V), well under 30 mA abs max. Low-rail/high-Vf dimness is already documented. Red 330R gives about 3.6-4 mA sunk by IO48 (20 mA default drive). LEDs stay off while IO48 floats at reset.
- J3 Qwiic order 1 GND, 2 3V3, 3 SDA (IO8), 4 SCL (IO9). J4 1 TXD0, 2 RXD0, 3-6 IO10-13 (FSPI CS/MOSI/CLK/MISO), 7 IO14, 8 IO21. Pin 1 of both is at the west end. JLC_ROT J4 +180 is carried from the Rev B final DFM.
- Module decoupling C6 100nF and C7 10uF sit at the 3V3 pin (pad 2). U2 placement is identical to Rev B (100.0, 125.25).

### Contract, firmware readiness, testability, sourcing

Contract, firmware, testability and sourcing review of v2.0 Rev A. This was read-only: the only thing I ran was `make check`, which passed (76 nets, tree still clean).

**Verdict:** the hardware contract is mostly accurate against the netlist, but v2 is not yet releasable as a product. Three things stand in the way.

1. **No firmware exists.** The `firmware/` directory is empty in both worktrees, and nothing anywhere implements the expansion-bus enable readback (EXP_OE on IO38), the ID EEPROM read or the EXP init rule. Without it, S-v2-1 (bus-off check), S-v2-2 (bus-on self-test) and the W_DISABLE2# radio-kill promise cannot be shown working.
2. **The expansion bus switches on about 9 ms before the ESP32 leaves reset, on every power-up.** Computed from the two RC timings: EXP_OE reaches 1.2 V at about 4.6 ms (10 k / 1 uF), while the chip enable (CHIP_PU) only rises at about 13.9 ms. Two promises are therefore wrong: pinmap §6.1 says "the bus switch is off during power-up (§6.3 RC)", and §6.3 does not exist. The contract's firmware rule says EXP_2..11 "stay high-Z" until the EEPROM is read. During that window the ESP32-S3's documented 60 us power-up glitches (datasheet Table 2-2) reach the carrier pins. Fixing this after the order means a respin, so the owner should decide before ordering.
3. **The contract does not close any of CG1..CG8, and contradicts itself.** §5 rules 1 and 3 ban carrier→card drive, yet §4.3 relies on a bidirectional UART/SPI bus. Most gaps can now be closed with numbers taken from the design.

Smaller items:
- The second source for U6 named in the gate documents (TPS259474LRPWR) is a latch-off circuit-breaker part, so it is not a drop-in replacement.
- DATASHEET.md and the risk register are stale or incomplete.
- Several S-v2 tests cannot be run as written: a laptop WWAN slot conflicts with R11, and an M.2→USB adapter gives no access to the pins.
- Sourcing note: the ESP32-S3R2 die is end-of-life and has been upgraded to the S3RH2. WROOM-1-N8R2 is still listed as an active module.

- make check PASS on the v2 worktree (ERC + BOM + tools/check_v2_netlist.py: 'GATE V2 netlist check PASS (76 nets)'); git tree still clean afterwards
- EXP_n ↔ M.2 pin mapping in the netlist (connections.md J1.30/32/34/36/40/59-65 → U3-U5 D pins) matches carrier-interface.md §4.3 and DATASHEET.md exactly
- EXP ↔ GPIO mapping (esp32s3_companion.py EXP_MODULE_PINS = pads 32,34,39,38,11,4,5,6,7,8,9,10 → IO39, IO41, IO1, IO2, IO18, IO4-7, IO15-17) matches the contract. The ADC claims (IO1, 2, 4-7 = ADC1_CH0, 1, 3-6, usable with WiFi) are correct per the S3 datasheet
- CONFIG_0 (J1.21) and CONFIG_1 (J1.69) are on GND (state 6); CONFIG_2/3 have 1M pull-ups (R22/R23) plus 100k to the Q1 gates; Q1 drains are wired-NOR on EXP_OE with R26 10k / C13 1uF, as the contract states
- Host-facing cells: LED_1_n (pin 10) = Q2.D1, WAKE_ON_WWAN_n (pin 23) = Q2.D2, both open-drain with 100k gate pull-downs (R27/R28); W_DISABLE2_n (pin 26) = Q3.G1 with 1M R29 pull-up; IO40 inverted via R30 10k. Matches contract §4.4
- TMUX1511 claims verified in the datasheet: powered-off protection up to 3.6 V, IPOFF ≤ 2 uA, IOFF ≤ 100 nA, Ron ≤ 4.5 Ω, fail-safe SEL (VIH 1.2 V). Contract §4.3 '≤ 2 uA when off or unpowered' holds, with zero margin at the temperature extreme
- I2C pull-ups R20/R21 4k7 sit on the MCU side (EXP_0_S/EXP_1_S), so the edge is high-Z when the bus is off, as claimed
- OVLO divider 100k/52.3k 0.1% gives a 3.44-3.57 V trip and ~3.17 V re-enable from VOV(R)/VOV(F) in tps25947 §6.5; EN/UVLO 1M pull-up follows Table 6.3 note 2 (≥ 350k when IN > 5 V), so the 5 V survival in S-v2-3 is within ratings
- ILM 3.3k gives ILIM = 3334/3300 ≈ 1.01 A (0.85-1.15 A); FB1 BLM18PG121SN1D ≤ 50 mΩ
- SI1024X-T1-GE3 2nd source: same SOT-563 pinout (S1/G1/D2/S2/G2/D1) per v2/research/dual_nmos_research.md; VGS ±6 V is adequate because every gate in the design is ≤ 3.6 V
- All v2 bottom-side parts listed in contract §2 (U3-U6 UQFN/VQFN, Q1-Q3 SOT-563, RN1-RN3) are on B.Cu in the board file; the top side carries only U2, J1, J3, J4
- Strapping pins IO3/IO45/IO46 left floating and IO35-37 NC (N8R2 ⇄ N16R8 drop-in) confirmed in esp32s3_companion.py. No EXP or host GPIO is a strapping pin, and IO39's reset WPU is harmless behind the switch
- Dev carrier as built has what S-v2 testing needs: J_EXP header on all 12 EXP lines, JP_SIG2/3 (GND/open/10k→1V8/10k→3V3), CONFIG_0/1 readback on J4, W_DISABLE2 jumper, BENCH path for OVP, and a 2 A buck (meets the ≥ 1.2 A needed for the eFuse current-limited restart)

### Manufacturing, footprints and fab package

I reviewed the manufacturing, footprint and fab-package area of v2.0 Rev A. This was a read-only review: I ran `make drc` and `make check`, and wrote scratch files only under <scratch> is in good shape:**
- The board passes `make drc` with all severities (0 violations, 0 unconnected, 1 justified exclusion).
- The board pad nets match the regenerated SKiDL netlist exactly (0 differences on 257 nodes).
- The committed gerber and drill zip is byte-identical (apart from timestamps) to a fresh export of the current board.
- The custom TI RSV and RPW land patterns and the TJ-S1706 LED land pattern match their datasheets.
- The J1 finger footprint and the outline are identical to the validated Rev B.

**The main new risk is the bottom-side rotation in the CPL (dfm-1).** I fitted one bottom-side rotation model to JLC's own EasyEDA library footprints and to the Rev B outcomes JLC actually produced:
- D1 was accepted at CPL 0, even though JLC's SOT-23 library footprint is our KiCad footprint rotated 180°.
- The LED faced outward at CPL 90 (v1) and inward at CPL 270 (Rev B).
- The checklist's own note says JLC mirrors bottom previews east/west.

These facts fit one model: JLC mirrors bottom parts left/right, while KiCad flips them top/bottom. Under that model the correct bottom offset is the library rotation plus 180°. This gives:
- **The LED +0 offset holds.** This independently supports K2.
- **U4, U5 and Q1–Q3 (+90 now, should be 270).** Their CPL comes out 180° wrong. A second model that would also fit the LED data agrees for these five parts, so this does not depend on the first model.
- **U3 (+90 now, should be 270).** The first model also puts U3 180° wrong; the second model says U3 is correct.
- **U6 (offset 0 now, should be 180).** U6 is the part the docs call "sign-free, high confidence"; under the first model it is also 180° off.

Every one of these land patterns fits perfectly when rotated 180°, so nothing looks wrong to a placement machine. The consequences would be:
- U3–U5: the TMUX1511 pins 8 (GND) and 16 (VDD) swap, putting +3V3 straight into each switch's GND pin.
- U6: the eFuse IN and OUT bars swap.
- Q1–Q3: the two FET channels swap.

Only the engineers' final DFM pin-1 check stands between this and dead boards.

**Smaller issues:**
- The committed v2 assembly and fab drawing is a stale build. It shows 4 layers, tented vias, LED +180, and Rev B DNP parts.
- The 0.4 mm-pitch parts have 0.1 mm solder-mask dams, but the order settings don't specify a mask colour.
- U1's offset recorded as "verified" can't be the real one: at the CPL value it does not fit JLC's own library footprint, so JLC must have rotated it.
- A few documentation and job-file inconsistencies.

**Stock (JLC/jlcsearch, today):** TMUX1511 3,120; TPS259470A 3,333; SSM6N56FE 7,263 (recovered); second-source SI1024X 33,554. I could not check JLC stock for the WROOM-1-N8R2, the 0.1% resistors (R31/R32), USBLC6, BAT54A or the Basic passives, because jlcsearch does not index them. Re-check these in the live quote.

- `make drc` (kicad-cli, all severities) gives 0 violations and 0 unconnected, with 1 justified exclusion (lib_footprint_mismatch U2). The edge-clearance waiver in esp32_m2_companion.kicad_dru covers only J1 SMD pads.
- `make check` passes (ERC, netlist, BOM, v2 contract netlist: 76 nets). Board pad nets match the regenerated build/esp32_m2_companion.net exactly: 257 nodes, 0 mismatches.
- fab/esp32_m2_companion_gerbers.zip is identical (ignoring timestamps) to a fresh export of the current board. It has 6 copper layers, masks, paste, silk, outline, separate PTH/NPTH files, 228 PTH hits, and no NPTH holes, so the notch is routed and not drilled.
- Design rules match the README/JLC option: 6 layers, 0.8 mm; vias 0.35/0.2, 0.45/0.2 and 0.45/0.3 (annular ring 0.075 at minimum); track and clearance 0.127; hole clearance 0.2; hole-to-hole 0.25; copper to edge 0.3; no blind or micro vias; no tracks on In1 (GND) or In4 (+3V3).
- J1 finger footprint (67 pads, 0.35 x 2.5, mask margin 0.1016) and the board outline (22 x 42) are identical to the built v1.0-revB board. Copper keeps 0.3 mm from the long edges, as in Rev B.
- TI RSV0016A footprint matches tmux1511.pdf RSV0016A example board layout: rows 1.6 / 2.4 apart, 0.4 pitch, 0.2 x 0.6 pads, pin-1 pad 0.7, 0.05 NSMD margin. JLC library C2673275 matches it within about 0.03 mm (rotated 90°).
- TI RPW footprint matches tps25947.pdf RPW0010A land pattern and stencil: 0.6 x 0.25 side pads, L-shaped corner pads, 0.3 x 2.4 IN/OUT bars, pads 5/6 pasted with 4 x 0.28 x 1.06 apertures (82%), corner pads at 93%. JLC library C3662799 has the same orientation (pin 1 top-left).
- TJ-S1706 LED footprint pads (0.8 x 0.7 at ±0.9, 2.6 overall) match the TOGIALED recommended pad layout. Its handedness (lens +y, cathode/pad 1 at +x) equals JLC's library footprint for C273616 and C273612 rotated 180° (library: lens -y, '-' on pad 1 at -x). With the bottom-side model in dfm-1, the +0 CPL offset puts the lens toward the left card edge and the cathode on the GND/LED_STATUS_n pad. This supports the K2 derivation.
- Every footprint origin sits at the pad centroid (CPL centre correct) except U2. U2's offset is unchanged from Rev B and verified there.
- BOM: 25 lines, 50 placed parts, no DNP. The CPL lists exactly the BOM refs (J1 and TP1/TP2 excluded). Top side holds U2, J3, J4; bottom holds everything else, matching fab/README.md. The 13 Extended lines match the README list.
- LCSC part identities checked via the EasyEDA API: CL21A226MAQNNNE, CC0603KRX7R9BB104, CL10A105KB8NNNC, CL10A106KP8NNNC, LBAT54ALT1G, BLM18PG121SN1D, BM04B/BM08B-SRSS-TB, SSM6N56FE, the UniOhm 0603/0402 resistors, RT0402BRD07100KL / RT0402BRD0752K3L, 4D02WGJ0221TCE, USBLC6-2SC6, ESP32-S3-WROOM-1-N8R2, TMUX1511RSVR, TPS259470ARPWR. Values and packages match the BOM.
- The polarity checklist's pin-1 corners and nets match the board geometry for all 18 rows (for example U3 pin 1 at SE on EXP_OE, U4/U5/U6/Q1–Q3 pin 1 at NE, D3/D4 cathode toward N).
- Pin-1 silk dots exist on bottom silk next to pin 1 for U3–U6 and Q1–Q3. DRC reports no silk-over-copper.
- Second source C86784 (SI1024X): JLC's library footprint has the same orientation as C146449, and it is well stocked (33,554).
- No vias within 0.15 mm (copper) of a pad on a different net. Via-in-pad usage is consistent with the README's Epoxy Filled & Capped setting.

### Layout: SI, PI, thermal, EMC, mechanical

I reviewed the physical layout of v2.0 Rev A in hardware/kicad/esp32_m2_companion.kicad_pcb using KiCad 9 python and per-layer SVG renders. I also compared it with v1.0-revB (git show into the scratchpad) and checked it against the TPS25947, WROOM-1 and Espressif HDG datasheets and the M.2 Rev 1.0 spec. `make drc` passes: 0 violations and 0 unconnected, with warnings included (check_drc runs --severity-all).

I found no layout blocker. Nothing in the layout should stop the 5 boards from working, being assembled or damaging a host. The new v2 layout risks are all margin, robustness or documentation items. Each would be cheap to fix now and expensive after the order:

(a) Gold fingers 2/4 reach the eFuse only through a ~0.23 Ω path of 0.127 mm tracks.

(b) The eFuse OUT node has no capacitor before FB1.

(c) The GND pour fills the gaps between gold fingers 69/71/73 and 3/5. That contradicts the GATE V3 claim of no copper between fingers.

(d) GND stitching is sparse. Seven GND fingers share 2 vias, and parts of the outer pours are up to 7 mm from a GND via.

(e) The 6-layer board's finished thickness is 0.83 ± 0.10 mm, which can exceed M.2's 0.80 ± 0.08 mm.

(f) The USB routing does not meet the "length-matched, referenced to GND" rule. The functional impact at Full Speed is negligible.

What I verified as correct:
- Both planes are free of tracks and slots.
- The USB pair on In2 has a continuous reference plane.
- The power trunk widths are adequate.
- Decoupling placement is good.
- The antenna keep-out covers all 6 layers.
- Every GND finger reaches the plane.
- Bottom parts stay inside M.2's 5.2 mm component zone, though with near-zero margin.

All scratch scripts are in <scratch>

- `make drc`: 0 violations and 0 unconnected, with warnings included. check_drc.py runs kicad-cli with --severity-all, and copper_sliver, isolated_copper and track_dangling are warnings in the rule set. The finger edge-clearance waiver applies to J1 SMD pads only.
- In1 (GND) and In4 (+3V3) carry no tracks. Each fill is one outline (654.7 and 639.3 mm²), solid-connected (padconn 2), with only isolated or paired via antipads and no slots.
- Copper balance is symmetric: F and B pours, In1/In4 solid planes, In2/In3 sparse.
- USB_D pair on In2: the In1 reference is continuous along the full 39 mm centreline except the pair's own via antipads. Spacing is constant (0.5 mm pitch). No In2 neighbour runs parallel to it (max 3.2 mm, LED_PWR_A, DC), and it only crosses In3 tracks perpendicularly. Estimated ≈87 Ω differential. Each line has 3 vias; U1 (USBLC6) is a flow-through layout with no stubs; via stubs are ≤0.6 mm.
- +3V3_M2 trunk, J1.70/72/74 -> C14 -> U6.5: 0.35 mm 1 oz, ≈7 mΩ. IPC-2221 external gives ≈1.1 A at +10 °C and ≈1.5 A at +20 °C, against a 0.85–1.15 A limit. Fingers 70/72/74 at ≤0.38 A each are within M.2's 0.5 A per pin. The eFuse OUT -> FB1 hop is 0.35 mm × 1.5 mm, and FB1 is rated 2 A.
- eFuse: RPW has no thermal pad; at 28 mΩ × 1 A ≈ 28 mW, heat is negligible. GND pin 8 reaches a via through a short 0.2 mm track. C14 (100 nF) is 2.46 mm from IN. ILM parasitic capacitance is ≈2 pF, well under TI's 50 pF limit, with no parallel aggressor within 0.4 mm. The OVLO/EN dividers are local.
- Decoupling: U2.2 (3V3) has 2 vias-in-pad, C6 is 0.73 mm away, and C1/C2/C7 are within 2.6 mm, each with its own via. U2 GND pads 1/40 have vias-in-pad and the EPAD has 12 holes plus 2 vias. Switch caps C10–C12 and U1.5 have vias-in-pad. The TMUX1511 VDD caps are 1.7–4.5 mm away, acceptable for a passive switch.
- Antenna keep-out: the rule area covers all 6 layers and matches the WROOM-1 antenna area (6 mm). Nothing intrudes. Geometry is identical to Rev B, whose WiFi was validated.
- Gold fingers: every GND finger reaches In1. Fingers 69/71/73 sit on the main F island (22 vias); 11–51 on an island with 2 vias; 3/5 on an island with 3 vias; 57 by track to via (95.25,146.6); 21 by a single spoke (waived). Every track enters its finger from the top edge, and no via lies inside the finger rule areas.
- Notch and edges: copper-to-edge clearance of 0.3 mm is enforced board-wide (DRC). The mounting notch has no copper. There are no dangling tracks.
- Top-side component zone (M.2 Fig. 16, 4 mm): J3/J4 bodies end 6.45 mm from the edge, which passes. Bottom-side zone: see layout-7.
- Via geometry: 0.35/0.2 vias have a 0.075 mm annular ring, matching the paid JLC option recorded in fab/README. Hole-to-copper 0.2 mm and hole-to-hole 0.25 mm are enforced.

