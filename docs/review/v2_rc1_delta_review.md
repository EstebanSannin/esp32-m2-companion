# v2.0 Rev A — RC1 delta review (2026-10-28)

Re-review of the RC1 changes (`247f285..0f842a8`) requested in the approved change list: 5 area reviewers (power, bus enable, layout, DFM, docs), each finding challenged by a skeptic that tried to refute it from the primary sources. Read-only; nothing was changed. Severity = skeptic's corrected severity.

**Result: 0 blocker, 1 major, 15 minor, 25 info** (1 refuted, 1 uncertain).

| Id | Severity | Verdict | Finding |
|---|---|---|---|
| [power-rc1-1](#power-rc1-1) | major | confirmed | C16 1 nF (tau 34 us) lets an overvoltage ramp drive the ESP32 rail to about 3.7-3.9 V before OVLO trips; the docs' 'stays < 3.6 V' only holds for a hard step |
| [bus_enable-1](#bus_enable-1) | minor | confirmed | Contract §4.3.1 says the bus drops on a software or watchdog reset 'because IO38 returns to input'. On ESP32-S3 esp_restart() is a CPU-only reset, so IO38 most likely stays driven LOW |
| [dfm-r1](#dfm-r1) | minor | confirmed | Regenerated assembly/fab drawing (docs/review/v2_reva_drawings.pdf) is still stale: the dfm-2 fix was only a re-run, and the text is hard-coded |
| [dfm-r2](#dfm-r2) | minor | confirmed | U1's offset changed (0 to 270, now unverified), and its SOT-23-6 land is also 180°-symmetric, but the order remark and README step 4 leave U1 out |
| [docs-1](#docs-1) | minor | confirmed | Test procedure, self-test and polarity checklist still say a 180° Q2/Q3 rotation swaps functions. Review mcu_io-4 showed it is electrically harmless |
| [docs-2](#docs-2) | minor | confirmed | Firmware wait after release: the contract says ≥ 10 ms, while ADR 0006, pinmap §6.3 and the GATE V1 note say ≥ 50 ms |
| [docs-3](#docs-3) | minor | confirmed | Contract's own firmware rule is 'Proposed' while ADR 0006 calls the same rule normative |
| [docs-4](#docs-4) | minor | confirmed | Risk R-v2-18 names host pull-down test rows as its mitigation, but the test procedure has none |
| [docs-5](#docs-5) | minor | confirmed | Step 8.5 cannot show what SPEC S-v2-2 and ADR 0006 ask for: EXP_2 against PERST#/EN, and the low-going glitches |
| [docs-6](#docs-6) | minor | confirmed | Wrong or fragile expected values in the procedure: 9.2c 1.80–1.85 V and 3.3 inrush |
| [docs-7](#docs-7) | minor | confirmed | R33 moved to the top side in RC1 is not recorded, and the contract's 'fixed' top-side description and DATASHEET are now inaccurate |
| [docs-9](#docs-9) | minor | confirmed | Stale pre-RC1 statements left in the test procedure, risk register, ADR 0006 and the GATE V4 doc |
| [layout-1](#layout-1) | minor | confirmed | New GND fence via (110.4,118.75) cuts the In4 +3V3 strip beside the antenna; the plane copper around the antenna now hangs open-ended (RF change vs validated Rev B) |
| [layout-2](#layout-2) | minor | confirmed | New C15 (DVDT 2.2 nF MLCC) sits 0.32 mm from the V-scored long edge, the closest component on the board |
| [power-rc1-2](#power-rc1-2) | minor | confirmed | Test 3.2 ramp window 2.5-13 ms is tighter than the datasheet/tolerance spread of C15 and can fail a legitimate part |
| [power-rc1-3](#power-rc1-3) | minor | confirmed | C17 is ~4 mm from the OUT pin, behind FB1 pad 1 and a 0.2 mm neck, not 'next to U6' |
| [bus_enable-2](#bus_enable-2) | info | refuted | Driving IO38 push-pull high dumps C13 (1 µF at ~3 V) through Q3b with a ~10 ns gate edge; estimated peak several A against IDP 1.6 A |
| [bus_enable-3](#bus_enable-3) | info | confirmed | The turn-on window '1.5-5.1 ms' leaves out C13 tolerance and the 3.3 V supply tolerance; test 8.1d can false-fail |
| [bus_enable-4](#bus_enable-4) | info | confirmed | The 'No back-feed' wording for W_DISABLE2# is stale now that R29 = 100 kΩ (≤ 33 µA into an unpowered card) |
| [bus_enable-5](#bus_enable-5) | info | confirmed | check_v2_netlist does not assert R35 (the safety default of the hold-off) or the R29/R26/C13 values |
| [bus_enable-6](#bus_enable-6) | info | confirmed | v2_selftest's 'IO38 high on every exit path, Ctrl-C included' holds only inside main(); direct bus_on() or test_bus() use from the REPL can leave the bus released |
| [bus_enable-7](#bus_enable-7) | info | confirmed | The sleep rule covers deep sleep only; light-sleep GPIO handling of IO38 is not stated |
| [dfm-r3](#dfm-r3) | info | confirmed | Q1-Q3: the RC1 text still claims a 180° error swaps the Q halves; mcu_io-4 (it is electrically harmless) was not applied |
| [dfm-r4](#dfm-r4) | info | confirmed | dfm-7 leftovers are not fixed and the via counts are now staler |
| [dfm-r5](#dfm-r5) | info | confirmed | LED wording in the new order remark is ambiguous ('lens toward the card edge') |
| [dfm-r6](#dfm-r6) | info | uncertain | C17 MPN text may not match LCSC C52923 (from memory, unverified) |
| [docs-10](#docs-10) | info | confirmed | Contract says dev carriers use a WP jumper for the ID EEPROM. The dev carrier ties /WC to GND |
| [docs-11](#docs-11) | info | confirmed | DATASHEET bottom-height claim is framed differently from the contract |
| [docs-12](#docs-12) | info | confirmed | DATASHEET revision stamp is from a dirty tree |
| [docs-13](#docs-13) | info | confirmed | Self-test docstring says the REPL runs over USB-Serial-JTAG, but stock MicroPython enumerates as TinyUSB CDC |
| [docs-14](#docs-14) | info | confirmed | Small executability gaps in the procedure |
| [docs-15](#docs-15) | info | confirmed | Sibling-repo items outside this repo: dev-carrier CLAUDE.md has an absolute personal path, and its bring-up §7 is pre-RC1 |
| [docs-8](#docs-8) | info | confirmed | 'No back-feed' claims (SPEC G9, DATASHEET, ADR 0006, block docstrings) contradict the contract, now 10× worse with R29 at 100 kΩ |
| [layout-3](#layout-3) | info | confirmed | GND finger 57 is still tied only by a 0.127 mm track; its F.Cu island has no via (review layout-4 named it) |
| [layout-4](#layout-4) | info | confirmed | New C16 sits exactly at the M.2 bottom-side component zone limit (5.20 mm), like U1/C14 |
| [layout-5](#layout-5) | info | confirmed | C17 is ~3.7 mm of track from U6 OUT, beyond FB1.1's pad on a 0.2 mm stub, not 'next to U6 OUT' as the change record says |
| [layout-6](#layout-6) | info | confirmed | Remaining GND stitching gaps after the fence |
| [layout-7](#layout-7) | info | confirmed | Fence vias overlap same-net GND pads and sit under bottom bodies; v2_gnd_fence.py does not check GND pads |
| [layout-8](#layout-8) | info | confirmed | Minor RC1 copper artifacts and thin In4 slivers next to new voids |
| [power-rc1-4](#power-rc1-4) | info | confirmed | C17 effective capacitance below TI's '>1 uF' after DC bias; review asked C0G for C16 but X7R was fitted |
| [power-rc1-5](#power-rc1-5) | info | confirmed | OVLO filter capacitor sits ~3 mm from the OVLO pin (beyond R32) |

<a id="power-rc1-1"></a>

### power-rc1-1 — C16 1 nF (tau 34 us) lets an overvoltage ramp drive the ESP32 rail to about 3.7-3.9 V before OVLO trips; the docs' 'stays < 3.6 V' only holds for a hard step

Reviewer severity **major**, skeptic: **confirmed / major**.

**Evidence.** The divider is R31 100k / R32 52.3k, so the tap Thevenin resistance is 34.3 kOhm and with C16 1 nF tau = 34.3 us (power_3v3.py:23-26, 93-95). Until OVLO trips, the HFET is fully on and OUT follows IN. The output can rise as fast as the eFuse current allows into the ~64.5 uF rail. The datasheet current limit is slow: tLIM = 400 us 'settling to within 5% of ILIM' (tps25947.txt:561). The fast bound is the scalable fast-trip at 2 x ILIM (tSC 500 ns, line 563; §7.3.5 line 2216). The filter lag adds about r x tau to the trip voltage on a ramp. A time-step model (<scratch> was run with VOV(R) max 1.223 V, current capped at only 1.15 A (optimistic) and 65 uF nominal. Peak +3V3: 3.56 V for a 20 us ramp from 3.3 V to 5 V, 3.70 V for 50 us, 3.84 V for 100 us, 3.86 V for 100 us from 3.135 V. With 2 x ILIM (2.3 A) and DC-bias-derated ~40 uF, a 20-50 us ramp gives 4.1-4.2 V. Without C16, the trip is at IN <= 3.57 V + 1.2 us, so OUT stays <= ~3.57 V (this is the original review's line 1126 claim, which C16 now invalidates). With 220 pF (tau 7.5 us), the same model worst case is ~3.59 V; with 100 pF, ~3.55 V. The hard-step delay is also understated: '~4 us' (power_3v3.py:25, ADR 0007 RC1, carrier-interface.md §3 'a sustained step trips in ~4 us') holds only for typical VOV(R) at 3.30 V. At VOV(R) max it is 5.7 us, and from a 3.135 V host 8.9 us, plus tOVLO 1.2 us. The '~0.1 V rise behind the current limit' assumes a current limit that settles in us, but the datasheet gives 400 us. This defeats the GATE V1 owner requirement 'never exceed the ESP32-S3 3.6 V abs max' (power_3v3.py:10-11) for the most plausible fault shape: a carrier or regulator fault ramping over tens of us.

**Recommendation.** Before ordering, either cut C16 to 100-220 pF 0402 X7R/C0G (tau 3.4-7.5 us still attenuates MHz hot-plug ringing about 20-50x; check the LCSC Basic part) or have the owner explicitly accept the ramp exceedance. In both cases, correct the claims in power_3v3.py:25-26, ADR 0007 RC1 amendment, SPEC G11 and carrier-interface.md §3 ('~4 us', 'stays < 3.6 V') with the worst-case delay (~9-10 us for a step) and the ramp case. Add a bring-up step: a 50-100 us ramp from 3.3 V to 5 V on the bench (or a function generator plus a power amplifier), scoping +3V3 at the module.

**Skeptic.** I could not refute the physics. The datasheet (tps25947.txt) gives tOVLO 1.2 us with no deglitch and tLIM 400 us (current-limit settling). Line ~1986 says the output current can temporarily exceed ILIM, up to the fast-trip threshold of 2 x ILIM (ISCGain 201 %). So until OVLO trips, OUT follows an input ramp whenever C*dV/dt is at or below about 1.15-2.3 A. I wrote an independent time-step model (<scratch> with tau 34.3 us, VOV(R) max 1.223 V x 2.912 = 3.561 V and a 1.2 us delay. For a ramp from 3.3 V to 5 V, peak OUT is 3.60 V at 20 us, 3.78 V at 50 us and 3.98 V at 100 us (1.15 A into 65 uF). With 2.3 A into 40 uF it is 4.22-4.27 V at 20-50 us. A 1 ms ramp still reaches 3.62 V. For a hard step, the trip delay is 5.7 us at VOV(R) max (about 4.1 us typical), matching the finding. So the claims '~4 us' and 'stays < 3.6 V' in power_3v3.py:25-26 hold only for a typical part and a hard step. The 1 nF value came from the original review (v2_rc1_design_review.md:192), which analysed only the step. The ramp case is a new problem that C16 introduced and that contradicts the GATE V1 owner requirement (power_3v3.py:10-11). One correction to the recommendation: in my model, 220 pF (tau 7.5 us) does NOT keep the worst case near 3.59 V. A 100 us ramp gives about 3.70 V (filter lag r*tau = 17 V/ms x 7.5 us = 0.13 V), and 2.3 A/20 us gives 3.83 V. Even with no filter, the margin is only about 40 mV (3.561 V maximum threshold against the 3.6 V abs max). Any capacitor larger than about 100 pF exceeds 3.6 V on ramps of 0.1-1 ms. The owner needs to decide on the filter-versus-ramp trade-off explicitly; simply moving to 220 pF does not settle it. The exceedance is short (tens of us, a few hundred mV) and the fix is a value change, so major, not blocker.

<a id="bus_enable-1"></a>

### bus_enable-1 — Contract §4.3.1 says the bus drops on a software or watchdog reset 'because IO38 returns to input'. On ESP32-S3 esp_restart() is a CPU-only reset, so IO38 most likely stays driven LOW

Reviewer severity **minor**, skeptic: **confirmed / minor**.

**Evidence.** docs/carrier-interface.md:206-208 (marked 'fixed') says: 'Off: within ~20 µs ... of any ESP32 reset (PERST#-driven EN, watchdog, brown-out, software reset), because IO38 returns to input'. ADR 0006 (docs/decisions/0006-...md, Timing block after line 116) and pinmap.md §6.3 say the opposite: whether software/WDT resets return IO38 to its reset state 'is not stated in the datasheet', to be confirmed at bring-up. On ESP32-S3, ESP-IDF esp_restart_noos() resets the CPUs only (esp_rom_software_reset_cpu; the boot log shows 'rst:0xc (RTC_SW_CPU_RST)'). A CPU reset does not reset IO_MUX or GPIO output registers, so a pin driven LOW stays LOW through ROM, the 2nd-stage bootloader and app init. The same path is taken by MicroPython machine.reset(), the panic handler, and the task/interrupt WDT, which panic and then restart. MicroPython machine.WDT uses the task WDT, so it takes this path too. Only EN/PERST#, brown-out, RTC-WDT, USB-JTAG chip reset and power loss reset the pads. As a result, v2-test-procedure.md:283-284 (8.5b machine.reset(), 8.5c WDT) expect 'hdr 1 falls to 0 V at reset' and will very likely FAIL on a good board. Also, stock MicroPython never touches IO38 after reboot, so the bus stays ON until v2_selftest is imported. This is PLAUSIBLE (based on IDF source behaviour, not measured), so confirm it at bring-up.

**Recommendation.** In §4.3.1, change the 'software reset / watchdog' clause to '[FW], to be confirmed (S-v2-2)', in line with ADR 0006. Firmware rule: drive IO38 high (or set it to input) in a shutdown handler before esp_restart, and in a custom 2nd-stage bootloader hook (bootloader_before_init) so every CPU-reset path, panic included, holds the bus within the bootloader time. For MicroPython bring-up, put Pin(38, Pin.OUT, value=1) in boot.py. Change the expected result of 8.5b/8.5c to 'record' (like 8.5d) until this is measured.

**Skeptic.** The documents contradict each other. docs/carrier-interface.md:206-208 states as fixed that the bus goes off on 'any ESP32 reset (... watchdog, brown-out, software reset), because IO38 returns to input'. ADR 0006 lines 117-120 say the datasheet does not state this and that it must be confirmed at bring-up (S-v2-2). pinmap §6.3:305 hedges the same way. v2/firmware/README.md:91 makes the same unhedged claim ('R35 holds IO38 high through reset and boot'). The mechanism is credible but has not been measured. On S3, esp_restart (machine.reset(), and task-WDT panic, which MicroPython's WDT uses) logs rst:0xc RTC_SW_CPU_RST. That is a CPU-only reset and does not reset the GPIO matrix or IO_MUX. Stock MicroPython also does not touch IO38 on boot. So 8.5b and 8.5c (v2-test-procedure.md:283-284, expected 'same', i.e. hdr 1 falls to 0 V) are likely to fail on a good board, and the contract gives carriers a guarantee nobody has verified. The firmware rule (drive IO38 high first) mitigates the risk. Minor is the right severity: this is documentation and test expectations, not hardware.

<a id="dfm-r1"></a>

### dfm-r1 — Regenerated assembly/fab drawing (docs/review/v2_reva_drawings.pdf) is still stale: the dfm-2 fix was only a re-run, and the text is hard-coded

Reviewer severity **minor**, skeptic: **confirmed / minor**.

**Evidence.** pdftotext of the committed PDF (commit 1b8b86e, stamp 'v1.0-revB-33-g828718c'), sheet 2 fab notes read: '4 layers SIG/GND/PWR/SIG, 0.80 mm, stackup JLC04081H-3313', 'min drill 0.30 mm', 'Vias tented both sides', 'Assembly: both sides; 22 placed parts; DNP R5 R6 C8 C9', 'CPL: D3/D4 +180° vs KiCad (JLC_ROT) - VERIFY PREVIEW'. Sheet 1: 'DNP (red X): R5 R6 (I2C pull-ups), C8 C9 (USB SI)', 'TP1-6'. All of these are string literals in hardware/tools/asm_view.py:170 and :228-236, so 'make drawings' can never update them. The real package is 6-layer JLC06081H-2116, 0.2 mm drills (142 vias), Epoxy Filled & Capped (fab/README.md:28), 54 placed parts, no DNP, LED offset +0, TP1/TP2 only. asm_view.py:25 POLAR = {D1,D2,D3,D4,U1,U2,J3,J4}, so the bottom view still has no pad numbers or pin-1 marks for U3-U6, Q1-Q3 or RN1-RN3. These are the parts whose 180° errors are silent, and dfm-2 recommendation 2 asked for those marks. The 'Vias tented' note contradicts the via-in-pad requirement (dfm-6).

**Recommendation.** Before the order, make asm_view.py derive the fab notes from the board, BOM and gen_fab: layer count, stackup, via finish, placed count, DNP list and the JLC_ROT summary. Add U3-U6, Q1-Q3 and RN1-RN3 to POLAR. Run 'make drawings' again on the ordered commit. If that slips, at least drop the 'Vias tented' and 'D3/D4 +180°' lines so nobody reads them as order settings.

**Skeptic.** Confirmed. pdftotext of docs/review/v2_reva_drawings.pdf (last touched by 1b8b86e) contains these lines: '4 layers SIG/GND/PWR/SIG, 0.80 mm, stackup JLC04081H-3313', 'Vias tented both sides', 'Assembly: both sides; 22 placed parts; DNP R5 R6 C8 C9', 'CPL: D3/D4 +180° vs KiCad', 'DNP (red X): R5 R6 ... C8 C9' and 'TP1-6'. All of them are string literals in hardware/tools/asm_view.py:170 and :228-236, so re-running the generator cannot fix them. POLAR at asm_view.py:25 is {D1,D2,D3,D4,U1,U2,J3,J4}, so U3-U6, Q1-Q3 and RN1-RN3 get no pin-1 marks. The real package is 6-layer, with epoxy-filled and capped vias (fab/README.md:28-29), 54 CPL rows and no DNP (README:43). LED offset is 0 (gen_fab C273616/C273612). Minor is the right severity: the order is driven by fab/README, the CPL and the checklist, not by this drawing. But the drawing contradicts the order settings ('Vias tented' against via-in-pad), so it should be fixed or the wrong lines dropped.

<a id="dfm-r2"></a>

### dfm-r2 — U1's offset changed (0 to 270, now unverified), and its SOT-23-6 land is also 180°-symmetric, but the order remark and README step 4 leave U1 out

Reviewer severity **minor**, skeptic: **confirmed / minor**.

**Evidence.** gen_fab.py JLC_ROT C7519 = (270, None) gives CPL U1 270 (fab/esp32_m2_companion_cpl_jlc.csv). Rev B shipped at 0 and JLC re-rotated it by an unrecorded amount (review dfm-4). On the board, U1 pads are pin 2 GND at (-1.14,0) and pin 5 +3V3 at (+1.14,0). A 180° placement seats perfectly on the 6-pad land and puts device GND (pin 2) on +3V3 and VBUS (pin 5) on GND. That forward-biases the USBLC6 GND-to-VBUS clamp across the rail, so the card is dead or U1 burns, and no pick-and-place or AOI check would catch it. fab/README.md order remark: 'Bottom side: U3, U4, U5, U6, Q1, Q2, Q3 - pin 1 per the silkscreen dot ... 180-degree symmetric'. README step 4 says to check pin 1 of 'every one' among 'U3–U6, Q1–Q3, RN1–RN3' and does not name U1. The checklist row for U1 (pin 1 SW) does exist and is correct. A smaller wording point: Q1-Q3 silk pin-1 marks are triangles, not dots (B.Silkscreen polygon at local (0.72,-1.03)). U3-U6 do have 0.28 mm silk circles, each in the corner the checklist expects.

**Recommendation.** Add U1 to the order remark and to the 'check every one' list in README step 4. Reword it as 'pin 1 per the silkscreen dot/triangle'.

**Skeptic.** Board scan of U1 (bottom, 0°): pad 2 GND is at (-1.14,0) and pad 5 +3V3 at (+1.14,0). Pads 1/3/4/6 are at (±1.14,±0.95), so the land is 180°-symmetric. Placed 180° off, device pin 2 (GND) lands on +3V3 and pin 5 (VBUS) lands on GND. That forward-biases the USBLC6 clamp across the rail. CPL line 50 gives U1 270, and gen_fab.py C7519 = (270, None), so the offset is unverified. In fab/README.md the order remark (line 56) lists only U3-U6 and Q1-Q3, and the step 4 'every one' sentence (lines 72-75) is about U3-U6, Q1-Q3 and RN1-RN3. U1 appears only in the offset list. Step 4 does say to check every row of polarity_checklist.md, and the U1 row is there, so the gap is in emphasis rather than total. That keeps it minor. I did not separately verify the silk dot vs triangle wording for Q1-Q3.

<a id="docs-1"></a>

### docs-1 — Test procedure, self-test and polarity checklist still say a 180° Q2/Q3 rotation swaps functions. Review mcu_io-4 showed it is electrically harmless

Reviewer severity **minor**, skeptic: **confirmed / minor**.

**Evidence.** SOT-563 pinout 1 S1/2 G1/3 D2/4 S2/5 G2/6 D1. Turned 180°, physical pin k lands on pad k+3, so each gate keeps its own drain. Q2 still gives IO42→LED_1_n and IO47→WAKE_ON_WWAN_n. Q3 still gives pin26→IO40 and IO38→EXP_OE. Every source is on GND. The RC1 docs repeat the wrong claim anyway: docs/v2-test-procedure.md:95 (1.3 'On Q2, 180° swaps LED_1# and WAKE#'), :300 (9.1b 'If D5/D6 show the other's pattern, Q2 is rotated 180°'), :435-436 (§14 'IO40 inverted or stuck → Q3 rotated (Q3a/Q3b swapped)', 'D5/D6 patterns swapped → Q2 rotated 180°'), v2/firmware/v2_selftest.py:283 ('Distinct patterns so a swapped Q2 (180 deg…) shows') and fab/polarity_checklist.md:14 ('180 off swaps LED_1#/WAKE#'). The mcu_io-4 recommendation was not applied. The text can make the DFM reviewer reject a correct placement, and it sends a bring-up debugger to the wrong part.

**Recommendation.** Say that a 180° turn of Q1–Q3 is equivalent and only a 90° error fails to land. In §14 point swapped D5/D6 patterns at a firmware or GPIO-table error. Point IO40 stuck at R30, R29 or the Q3 solder joints. Fix the polarity_report.py text that generates the checklist row.

**Skeptic.** host_sideband.py:28-46 puts S1 and S2 of both Q2 and Q3 on GND, and common.py:133-139 gives the pinout as 1 S1/2 G1/3 D2/4 S2/5 G2/6 D1. A 180° turn moves pin k to pad k+3, so each gate stays paired with its own drain and the function does not change. This is the mcu_io-4 result. The change record (review-findings.md:552-624) does not apply mcu_io-4, even though the owner approved 'go with your recommendations'. The wrong text is still in v2-test-procedure.md:95, :300, :435 and :436, in v2_selftest.py:283, in fab/polarity_checklist.md:14, and in its generator hardware/tools/polarity_report.py:44. The checklist is the order gate, so the wrong text can lead someone to reject a correct placement. Minor is the right severity.

<a id="docs-2"></a>

### docs-2 — Firmware wait after release: the contract says ≥ 10 ms, while ADR 0006, pinmap §6.3 and the GATE V1 note say ≥ 50 ms

Reviewer severity **minor**, skeptic: **confirmed / minor**.

**Evidence.** docs/carrier-interface.md:288 [FW] rule 2: 'Release (IO38 low), wait ≥ 10 ms, probe 0x50'. docs/decisions/0006…md:112: 'Firmware waits ≥ 50 ms (review expansion-6) before the EEPROM probe'. docs/pinmap.md:309: 'wait ≥ 50 ms before probing'. docs/v2-gate-v1.md RC1 note: 'waiting ≥ 50 ms'. v2_selftest.py:84 uses T_RELEASE_MS = 60. The 50 ms figure came from expansion-6, whose concern was EXP_OE readback stability. That readback no longer exists, and the worst-case turn-on is 5.1 ms. Related small mismatches: VIH crossing is 4.5 ms in the contract (§4.3.1) and test 8.1d, but ~4.6 ms in the ADR and pinmap; 10 ms·ln(3.3/2.1)=4.52 ms. The host-load threshold is '65–435 kΩ' in contract §4.2 but '< ~500 kΩ' in ADR 0006:125 and risks R-v2-18.

**Recommendation.** Pick one number, ≥ 10 ms or ≥ 50 ms, and use it in the contract (which carriers import), ADR 0006, pinmap §6.3 and the GATE V1 note. Align 4.5/4.6 ms and the 435/500 kΩ wording.

**Skeptic.** carrier-interface.md:288 says 'wait ≥ 10 ms'. ADR 0006:112, pinmap.md:309 and v2-gate-v1.md:175 say ≥ 50 ms, and the self-test uses T_RELEASE_MS = 60. Both values are safe against the 5.1 ms worst case. The problem is that the contract, which carriers import, disagrees with the ADR. The 4.5 ms value (contract:204) vs 4.6 ms (ADR:111, pinmap:308) and the 65–435 kΩ (contract:152) vs < ~500 kΩ (ADR:125, risks:42) wording also differ, as reported.

<a id="docs-3"></a>

### docs-3 — Contract's own firmware rule is 'Proposed' while ADR 0006 calls the same rule normative

Reviewer severity **minor**, skeptic: **confirmed / minor**.

**Evidence.** carrier-interface.md:291-294 marks rule 4 '*Proposed* (RC1)': on no ACK or bad CRC, firmware turns the bus off with a host override. Carriers may rely on fixed items only. ADR 0006:122-126 says 'Firmware rule (normative for firmware ≥ first v2 release): … if no ACK or the CRC fails, drive IO38 high again'. pinmap §6.3 and the GATE V1 RC1 note state it as the rule, and the change record lists it as owner-approved. The contract's §4.2 host-load mitigation and §5 rule 4 also depend on it.

**Recommendation.** Mark rule 4 fixed [FW] in the contract, or call it proposed in the ADR as well. Keep the host-override clause.

**Skeptic.** carrier-interface.md:291 marks rule 4 '*Proposed* (RC1)'. ADR 0006:122 calls the same rule 'normative for firmware ≥ first v2 release', and v2-gate-v1.md:175 states it as the rule. The change record says the owner approved the change list, so the status legend is inconsistent with that record.

<a id="docs-4"></a>

### docs-4 — Risk R-v2-18 names host pull-down test rows as its mitigation, but the test procedure has none

Reviewer severity **minor**, skeptic: **confirmed / minor**.

**Evidence.** docs/risks.md:42 mitigation: 'Host-safety test rows with 100 kΩ and 20 kΩ to GND on CONFIG_2/3' (review expansion-1 recommendation 3). docs/v2-test-procedure.md §7.1 tests only open, 1V8, 3V3, GND/open and open/GND. The dev-carrier JP2/JP3 positions are GND, open, 10k→1V8 and 10k→3V3 (m2-dev-carrier sig_select.py), so no pulled-down case exists in hardware. The row can still be run: JP2/JP3 open plus a hand resistor from J4 hdr 11/13 to GND. Expected result: bus ON after release with 20 k (below 65 k). This verifies that the firmware re-hold (rule 4) limits exposure to the probe window.

**Recommendation.** Add §7.1f/g: JP2/JP3 open with 100 kΩ and then 20 kΩ from J4 hdr 11 and 13 to GND. Run with signature=None and record. Expected: the bus may turn on when released (B) and must be off again in C and after the script exits.

**Skeptic.** risks.md:42 (R-v2-18) names 'Host-safety test rows with 100 kΩ and 20 kΩ to GND on CONFIG_2/3' as its mitigation. Procedure §7.1 (lines 195-199) has only the open, 1V8, 3V3, GND/open and open/GND rows. The dev-carrier sig_select.py offers only GND, open, 10k→1V8 and 10k→3V3, so no pulled-down case exists in the hardware. The mitigation named in the risk register is therefore not in the procedure.

<a id="docs-5"></a>

### docs-5 — Step 8.5 cannot show what SPEC S-v2-2 and ADR 0006 ask for: EXP_2 against PERST#/EN, and the low-going glitches

Reviewer severity **minor**, skeptic: **confirmed / minor**.

**Evidence.** SPEC S-v2-2 and ADR 0006:119-120 say 'scoping EXP_4 and EXP_2 against PERST#/EN'. Procedure 8.5 (v2-test-procedure.md:276-286) scopes CH1 on J3 hdr 1 (the EXP_0 indicator) and CH2 on hdr 9 (EXP_4) with 100 kΩ to GND. Neither channel is EN/PERST# and EXP_2 is not probed. DS Table 2-2 lists the IO1–17 glitches (EXP_2,3,5–11) as actively driven LOW. On a line pulled down by 100 kΩ, or left high-Z, a low glitch is invisible, so 8.5 can only catch the IO18 high glitch.

**Recommendation.** Add a 8.5 variant with CH2 on J3 hdr 5 (EXP_2) and a 100 kΩ pull-up to J5 hdr 1 (+3V3), expecting no dip below ~2.8 V. Trigger CH1 on J4 hdr 1 (PERST#), or on EN at TP1, as the SPEC asks. Or change the SPEC/ADR wording to match what is actually tested.

**Skeptic.** SPEC S-v2-2 and ADR 0006:119-120 ask for scoping EXP_4 and EXP_2 against PERST#/EN. Procedure 8.5 (lines 274-286) probes J3 hdr 1 (the bus indicator) and hdr 9 (EXP_4) with 100 kΩ to GND. EXP_2 (IO1) is not probed, and neither channel is EN or PERST#. pinmap.md:259 confirms that IO1–17 glitch only low, so a pulled-down line cannot show those glitches. The hdr 1 indicator does show whether the bus stays off, which is the functional hazard. That partly mitigates the gap, but the SPEC item is not tested as written.

<a id="docs-6"></a>

### docs-6 — Wrong or fragile expected values in the procedure: 9.2c 1.80–1.85 V and 3.3 inrush

Reviewer severity **minor**, skeptic: **confirmed / minor**.

**Evidence.** (a) 9.2c (v2-test-procedure.md:310) expects hdr 19 at '1.80–1.85 V'. +1V8_REF is a 2k/2k4 divider from the carrier +3V3 (m2-dev-carrier power_rails.py; spec 1.71–1.89 V). Board #1 measured 1.78 V (m2-dev-carrier docs/bringup.md results). R29 adds 15 µA × 1.09 kΩ ≈ +16 mV, so a good board reads ~1.796 V and fails the stated window. (b) 3.3 expects the rail-charging current at '≤ 0.15 A (≈45 mA typ, ≤90 mA)' through a shunt in the bench lead. The dev carrier has C9 22 µF + C10 100 nF straight on +3V3_CARD at the socket, which the bench charges at its own slew, before the card's dV/dt control. A fast bench output (e.g. 3.3 V in <0.5 ms) gives >145 mA on the shunt from C9 alone, unrelated to C15.

**Recommendation.** (a) Make 9.2c relative: hdr 19 = V(J5 hdr 5) + 10–25 mV, recording both readings. (b) Measure inrush as the slope of the card rail (CH1) × ~65 µF, or exclude the first edge caused by C9 charging. State that the shunt reading includes the carrier's 22 µF.

**Skeptic.** (a) The dev carrier's +1V8_REF is a 2k/2k4 divider, which is about 1.09 kΩ Thevenin. Board #1 measured 1.78 V (m2-dev-carrier bringup.md:235). R29 100 kΩ from 3.3 V into 1.8 V gives 15 µA, which adds about +16 mV, so a good board reads about 1.796 V. That is outside the 9.2c window of 1.80–1.85 V, a marginal false fail. (b) With JP1 = BENCH, the dev carrier's C9 22 µF on +3V3_CARD (power_rails.py:97) sits ahead of the card's dV/dt control. The step 3.3 shunt in the bench lead therefore also sees C9 charging: 22 µF × 3.3 V / 0.5 ms ≈ 145 mA. That reading is unrelated to C15.

<a id="docs-7"></a>

### docs-7 — R33 moved to the top side in RC1 is not recorded, and the contract's 'fixed' top-side description and DATASHEET are now inaccurate

Reviewer severity **minor**, skeptic: **confirmed / minor**.

**Evidence.** Commit 40b46ce message: 'R33 moved to the top side (strip between module and J4)'. The CPL now has 'R33,92.85,-139.30,top' (it was bottom at 247f285), and fab/README.md:41 lists 'top: U2, J3, J4, R33'. The RC1 change record in docs/review-findings.md never mentions the move. carrier-interface.md:44-45 (Fixed) still says 'Top: WROOM module … + 2 JST SH connectors', and DATASHEET.md:244 says 'top: module + connectors'. docs/v2-gate-v3.md:37 still places R33 in the eFuse group above fingers 70/72/74. CLAUDE.md requires mechanical changes to update the contract in the same commit. Carrier impact is nil (a 0402 on the face away from the carrier), but the 'fixed' text is now wrong.

**Recommendation.** Add a line to the RC1 change record. Update contract §2 (Top: module, J3/J4, one 0402 R33) and gen_datasheet.py (then regenerate). Add a dated note to the GATE V3 RC1 note. Optionally add R33 to visual check §1.8.

**Skeptic.** At 247f285 the CPL had R33 on the bottom (90.65, -137.37, bottom). Now it is on the top (92.85, -139.30, top), and fab/README.md:41 lists 'top: U2, J3, J4, R33'. The commit 40b46ce message mentions the move. The RC1 change record (review-findings.md:552-624) never mentions R33. carrier-interface.md:43-44 (Fixed) still says 'Top: WROOM module … + 2 JST SH connectors', DATASHEET.md:244 says 'top: module + connectors', and v2-gate-v3.md:37 still places R33 in the eFuse group. Carrier impact is nil, but the fixed contract text is now inaccurate. Minor is fine given the CLAUDE.md same-commit rule.

<a id="docs-9"></a>

### docs-9 — Stale pre-RC1 statements left in the test procedure, risk register, ADR 0006 and the GATE V4 doc

Reviewer severity **minor**, skeptic: **confirmed / minor**.

**Evidence.** v2-test-procedure.md:27 Coverage S-v2-3 'recovers below ~3.17 V', and :153 '(record; SPEC "~3.17 V")'. SPEC S-v2-3 now says 'stays off … restarts after the rail is taken to 0 V' and 3.13–3.25 V. risks.md:41 R-v2-17 still reads 'No v2 firmware yet … Open', but RC1 added v2/firmware/v2_selftest.py and the README says it closes contract_test-2. ADR 0006:61-62 Consequences still lists 'Firmware: expansion bus enable readback'; the amendment at :106 says it is lost, but the line is not struck through. docs/v2-gate-v4.md:20 still says 'BOM / CPL 25 lines / 50 placed parts'; fab now has 28 BOM lines and 54 CPL rows (C15/C16/C17/R35), and the RC1 note only qualifies the cost table.

**Recommendation.** Update Coverage S-v2-3 and step 4.3 to 'stays off at 3.30 V; returns at 3.13–3.25 V; restarts after a power cycle'. Set R-v2-17 to 'Mitigated: bring-up self-test (v2/firmware); no release firmware'. Mark the ADR 0006 readback consequence superseded. Add '28 lines / 54 parts' to the GATE V4 RC1 note.

**Skeptic.** Each stale statement checks out. v2-test-procedure.md:27 still has 'recovers below ~3.17 V' and :153 still has 'SPEC "~3.17 V"'. risks.md:41 R-v2-17 still reads 'No v2 firmware yet … Open', although v2/firmware/v2_selftest.py exists and its README says it closes contract_test-2. ADR 0006:61-62 still lists 'expansion bus enable readback' under Consequences. v2-gate-v4.md:20 still says '25 lines / 50 placed parts', while the fab BOM now has 28 lines and the CPL 54 rows (wc: 29/55 with headers), and the RC1 note (lines 115-135) qualifies only the cost table. All are documentation hygiene, so minor is acceptable (info would also be defensible).

<a id="layout-1"></a>

### layout-1 — New GND fence via (110.4,118.75) cuts the In4 +3V3 strip beside the antenna; the plane copper around the antenna now hangs open-ended (RF change vs validated Rev B)

Reviewer severity **minor**, skeptic: **confirmed / minor**.

**Evidence.** PWR_L5 (In4) fill, unfractured: at 247f285 the antenna keep-out (90,112.4)-(110,118.6) is a closed 125 mm² hole inside the plane, so the 0.7 mm strips on both long edges join the main plane at both bottom corners. At HEAD the keep-out void has merged into the outer outline (hole count changes, and the 125 mm² hole disappears from the hole list). Probes: In4 at (110.6,118.75) is True on old and False on new. In a render of In4 at x 107.5-111.2, y 116.5-120.5, the 0.85 mm antipad of GND via (110.4,118.75) 0.45/0.3 joins the keep-out edge (x 110.0) to the 0.3 mm edge pull-back. Result: the right strip (x≈110-110.7, y 112.4-118.6) is now a 6.2 mm open stub. The whole +3V3 area beyond the antenna tip reaches the main plane only through the 0.7 mm left strip. The In1 GND ring is unchanged and still connected on both sides. layout-8 relied on 'identical plane coverage to Rev B' (WiFi PASS at -58 dBm); that no longer holds.

**Recommendation.** Move this fence via clear of the strip (for example (110.4,119.4) or further inboard) or delete it, then refill and re-check that the In4 antenna hole is closed again. Pulling In4 back from the antenna entirely is a separate, deliberate future decision. Do not make it happen by accident.

**Skeptic.** I reproduced this with KiCad python on the In4 +3V3 fill, on a 0.05 mm grid over x 109.5-111.0, y 117.9-119.05. At 247f285 the right antenna strip (x~110.0-110.7) runs straight into the plane at y>=118.65. At HEAD rows y 118.40-118.60 are empty across the whole strip width, so the antipad of the new GND via (110.4,118.75) 0.45/0.3 cuts the strip off at its bottom corner. Point probes agree: (110.6,118.75) is True at 247f285 and False at HEAD, while (110.6,118.3) and (110.6,119.2) stay True. The In4 area drops 639.3 to 617.8 mm2 and remains one outline, so the strip is now an open stub fed only from the top. The In1 GND fill is unchanged at all probe points. This is an unintended change to plane geometry next to the antenna compared with Rev B, and it is easy to fix by moving the via, so minor is right.

<a id="layout-2"></a>

### layout-2 — New C15 (DVDT 2.2 nF MLCC) sits 0.32 mm from the V-scored long edge, the closest component on the board

Reviewer severity **minor**, skeptic: **confirmed / minor**.

**Evidence.** C15 is on B.Cu at (89.63,142.55), rot 90. Pad left edge x=89.32, fab body 89.33, courtyard 89.125, against the board edge at x=89.0. Distances: pad 0.32 mm, courtyard 0.125 mm. The next closest components are D3/D4 at 0.85 mm and C17 at 0.89 mm. fab/README.md:65 says V-cut on the long sides. MLCCs this close to a V-score are exposed to flex cracking at depanelling. A cracked DVDT cap leaks or shorts: the TPS25947 output ramp stalls or the card never turns on, or the cap goes open and the inrush returns to ~12-15 V/ms. The fence also added 5 GND vias at 0.375 mm from the V-cut edges: (89.6,121.7), (89.6,124.75), (110.4,118.75), (110.4,121.5), (110.4,127.6), (110.4,130.4). Before RC1 there were 2 such vias. Copper-wise this is no worse than the existing 0.3 mm plane pull-back, so it is low risk.

**Recommendation.** Move C15 inboard (≥1 mm from the edge, more if space allows), for example toward U6 pin 7 on the inner side, keeping the 1.2 mm DVDT trace short. Or confirm with JLC that the boards ship depanelled by router/cutter rather than snapped. Optionally move the edge fence vias to x 89.65/110.35 to give 0.4 mm.

**Skeptic.** C15 is at (89.63,142.55), rot 90, on B.Cu. Its pads start at x=89.32 (pad 2 at x 89.32-89.94) and its fab body at 89.33. The board edge is at x=89.0, so the pad is 0.32 mm from the V-cut long edge (fab/README.md:65). Before RC1 the edge-adjacent vias at x<89.7 or >110.3 were (89.6,143.18) GND and (110.4,144.25) USB_D_P. At HEAD six new GND vias sit at x 89.6/110.4 plus one at (89.65,129.1). The finding says 5 but lists 6, a small miscount that does not affect the conclusion. One mitigating point: the 0402's long axis runs parallel to the edge, which is the orientation least prone to flex cracks. Even so, it is the closest MLCC to the score line and is a new placement, so minor stands.

<a id="power-rc1-2"></a>

### power-rc1-2 — Test 3.2 ramp window 2.5-13 ms is tighter than the datasheet/tolerance spread of C15 and can fail a legitimate part

Reviewer severity **minor**, skeptic: **confirmed / minor**.

**Evidence.** From the datasheet SR table (tps25947.txt:587, 2.7 V row: 0.87 V/ms at 1800 pF, typ IdVdt 2.21 uA), scaled by Eq.4 (SR proportional to IdVdt/CdVdt): with C15 2.2 nF the typical SR is ~0.71 V/ms. The max is 0.71 x 3.82/2.21 / 0.9 (C15 -10 %) = 1.37 V/ms, which gives 3.3 V in 2.4 ms. The min is 0.71 x 0.81/2.21 / 1.1 = 0.237 V/ms, which gives 13.9 ms of ramp plus tD,ON (~0.6 ms typ at 1800 pF, ~2 ms for a slow part). docs/v2-test-procedure.md:131 requires '0 to 3.3 V in 2.5-13 ms'. power_3v3.py:21, ADR 0007 and carrier-interface §3 say '<= ~13 ms', which ignores the ±10 % on C15 and the turn-on delay. The inrush max of ~88 mA (nominal 64.5 uF, about 106 mA with +20 % caps) is still below the 0.15 A test limit and the 200 mA M.2 soft-start, so the electrical design is fine.

**Recommendation.** Widen the test 3.2 pass window to ~2-16 ms, or specify 10-90 % rise time with limits from the full IdVdt and C15 tolerance. Update the '<= ~13 ms' figure in the docstring, ADR, SPEC and carrier contract to '~16 ms incl. turn-on delay'.

**Skeptic.** I re-derived the numbers from the datasheet SR table (2.7 V row, 1800 pF: 0.87 V/ms, IdVdt min/typ/max 0.81/2.21/3.82 uA). Scaled to 2.2 nF, typical SR is 0.71 V/ms. At max IdVdt and C15 -10 % it is 1.37 V/ms, so 3.3 V is reached in 2.4 ms, below the 2.5 ms lower limit. At min IdVdt and C15 +10 % it is 0.237 V/ms, so the ramp takes 13.9 ms, beyond 13 ms. tD,ON (0.6 ms typ at 1800 pF, scaling up for 2.2 nF and a slow part) adds to the time measured from the CH2 trigger in the test 3.2 setup (docs/v2-test-procedure.md:131). Interpolating to 3.3 V input changes SR by only about 2 %. So a datasheet-compliant part can fail both ends of the window. This is a test-spec issue, not an electrical one: the inrush stays at or below about 0.1 A. Minor.

<a id="power-rc1-3"></a>

### power-rc1-3 — C17 is ~4 mm from the OUT pin, behind FB1 pad 1 and a 0.2 mm neck, not 'next to U6'

Reviewer severity **minor**, skeptic: **confirmed / minor**.

**Evidence.** U6 OUT (pin 6) pad spans y 140.7-143.1 at x 91.35. The route is OUT -> (91.35,140.8)->(91.35,140.3)->(91.8,139.85)->(91.8,139.5), 0.35 mm wide, to FB1 pad 1 (91.987,139.2). From there a 0.2 mm track (91.65,138.95)->(91.65,137.89)->(91.13,137.37) reaches C17 pad 1, about 3.9 mm of path in total. C17 returns through a GND via-in-pad at (90.17,137.37) to In1. U6 GND pin 8 returns through the via at (89.95,142.05), about 4.8 mm away. Electrically it is on the correct (+3V3_EFUSE, pre-bead) side. TI asks for the capacitor 'very close to the device' (tps25947.txt:3786, 3916). C17 simply took R33's old spot (R33 was at 90.65,137.37 B.Cu in 247f285).

**Recommendation.** Acceptable for Rev A if the space near the OUT end of U6 is blocked. Otherwise move C17 to the OUT end of U6 (between U6 and FB1, e.g. ~90.6,140.2) or widen the neck to 0.35 mm. Change the docstring and ADR wording from 'next to U6' to 'at FB1 pad 1, ~4 mm path'.

**Skeptic.** The board geometry matches the finding exactly (KiCad python). C17 is at (90.65,137.37) B.Cu, with pad 1 at (91.13,137.37). The +3V3_EFUSE route is: 0.35 mm tracks (91.35,140.8)->(91.35,140.3)->(91.8,139.85)->(91.8,139.5) into FB1 pad 1 (91.987,139.2, bb y 138.725-139.675), then a 0.2 mm track (91.65,138.95)->(91.65,137.89)->(91.13,137.37). That is about 3.5-4 mm of path from the U6 OUT pad (y 140.7-143.1) to C17. It is on the correct pre-bead net, but it is not 'very close' to OUT as TI asks (tps25947.txt:3786). The added inductance is a few nH, which matters only for fast-trip and hot-plug edges. Minor is appropriate; also fix the 'next to U6' wording.

<a id="bus_enable-2"></a>

### bus_enable-2 — Driving IO38 push-pull high dumps C13 (1 µF at ~3 V) through Q3b with a ~10 ns gate edge; estimated peak several A against IDP 1.6 A

Reviewer severity **minor**, skeptic: **refuted / info**.

**Evidence.** ssm6n56fe.pdf §4: IDP (pulsed) = 1600 mA, ID = 800 mA. §5.2: Ciss 55 pF. RDS(on) ≤ 300 mΩ at VGS 2.5 V. The ESP32 pad (default 20 mA, DS Table 2-1 note 5) charges 55 pF plus Miller in about 10-20 ns, so Q3b is fully on almost at once across C13 (EXP_OE ≈ 3.0 V). Peak ≈ 3.0 V / (≈0.25-0.3 Ω RDS(on) + ESR + trace) ≈ 5-10 A for about 0.3 µs (τ ≈ 1 µF × 0.3 Ω); energy ½CV² ≈ 4.5 µJ. That is thermally trivial but 3-6x the IDP abs-max. Board: C13 at (101.23,124.75) and Q3 at (104.0,129.4), both bottom side. The firmware rule ('drive IO38 high'), v2_selftest.py:94 and :99 (bus_off) and the docs ('IO38 may now be driven push-pull either way') all use the fast edge. The reset path (gate charged through R35 100 kΩ, τ ≈ 6 µs) and Q1 (gates behind 100 kΩ) ramp slowly and stay near or under IDP.

**Recommendation.** No hardware change is needed for Rev A. In firmware, hold the bus by setting IO38 to input (R35 pulls it up, giving the same ~10-20 µs off time with a soft gate ramp) instead of push-pull high, at least for routine bus_off(). Write this into the [FW] rules and v2_selftest. A future revision could add ~10 Ω in series with the Q3b drain (peak ≈ 0.3 A, off time still ≈ 10 µs) or a gate resistor.

**Skeptic.** In ssm6n56fe.pdf, IDP 1600 mA carries Note 1: 'Ensure that the channel temperature does not exceed 150 °C'. That is a thermal limit, not a hard current limit. The pulse energy is ½·1µF·(3V)² ≈ 4.5 µJ, part of it lost in ESR and trace. A die of about 0.3×0.3×0.1 mm has a heat capacity of roughly 1.5e-5 J/K, so the temperature rise is under 1 K. The current is also limited by FET saturation at VGS 3.3 V (|Yfs| 1.4 S), not by RDS(on) alone, so 5-10 A is an overestimate. Discharging a 1 µF cap through a small FET is routine. Gate drive is also not ~10 ns: Qg ≈ 1 nC at 20 mA is about 50 ns. No real stress or reliability risk. Using input mode for bus_off is an optional nicety.

<a id="bus_enable-3"></a>

### bus_enable-3 — The turn-on window '1.5-5.1 ms' leaves out C13 tolerance and the 3.3 V supply tolerance; test 8.1d can false-fail

Reviewer severity **minor**, skeptic: **confirmed / info**.

**Evidence.** C13 = CL10A105KB8NNNC (X5R, ±10%, about ±15% over temperature). R26 is 1%. The card rail is 3.3 V ±5% (M.2). Switching threshold is between VIL 0.45 V and VIH 1.2 V (tmux1511 §5.5), and the SEL leakage drop is ≤ 0.3 V. t = τ·ln(Vf/(Vf−Vth)): τ 7.65 ms, Vf 3.465 V, Vth 0.45 V gives 1.06 ms. Nominal τ 10 ms, Vf 3.135−0.3 = 2.835 V, Vth 1.2 V gives 5.5 ms. τ 11.1 ms gives 6.1 ms. The real window is about 1.1-6.1 ms. carrier-interface.md:203-204, pinmap.md:309 ('≤ 5.1 ms') and ADR 0006 (≤ 5.1 ms) use Vf = 3.0 V and nominal C. v2-test-procedure.md:246 (8.1d) uses '1.5-5.1 ms' as the pass criterion. Functionally this is harmless, because firmware waits ≥ 50 ms (v2_selftest T_RELEASE_MS = 60).

**Recommendation.** State 'about 1-6.5 ms (C13 ±10%/X5R, 3V3 ±5%, SEL leakage)' in §4.3.1, pinmap §6.3 and ADR 0006. Widen the 8.1d pass band to match. Keep the ≥ 50 ms firmware wait.

**Skeptic.** The arithmetic holds. C13 is CL10A105KB8NNNC (X5R ±10%, 50 V, so negligible DC-bias loss). With Vf = 3.135−0.3 = 2.835 V and nominal τ, the crossing of 1.2 V is 10·ln(2.835/1.635) ≈ 5.5 ms, above the documented 5.1 ms. With Vf = 3.465 V the 0.45 V crossing is ≈ 1.39 ms at nominal C and ≈ 1.26 ms at −10%, below 1.5 ms. The impact is small. The real SEL threshold sits between VIL and VIH (≈0.7-0.9 V typical, about 2.5-3 ms), so 8.1d (v2-test-procedure.md:246) would false-fail only at extreme corners. Firmware waits 60 ms. Downgraded to info: a documentation and pass-band refinement.

<a id="bus_enable-4"></a>

### bus_enable-4 — The 'No back-feed' wording for W_DISABLE2# is stale now that R29 = 100 kΩ (≤ 33 µA into an unpowered card)

Reviewer severity **info**, skeptic: **confirmed / info**.

**Evidence.** DATASHEET.md:36 still says 'W_DISABLE2# radio-kill input — voltage-agnostic NMOS cells, no back-feed'. ADR 0006:31 says 'Insulated gates mean no back-feed'. Pin 26 → R29 100 kΩ → +3V3 passes up to 3.3 V/100 kΩ = 33 µA into an unpowered card (10x the old 3.3 µA). carrier-interface.md:375 correctly says ≤ 33 µA. The effect is bounded: Q3b's gate follows the rail through R35, so once the rail passes Vth (0.4-1.0 V) Q3b grounds EXP_OE and R26 10 kΩ loads the rail (on hosts Q1 does the same). About 40 µA × 10 kΩ keeps the rail ≈ 0.4 V, which is below the TMUX1511 VDD minimum of 1.08 V. R35 has no edge connection (IO38 net = U2.31, Q3.5, R35.2 only), so it adds no back-feed path.

**Recommendation.** Change DATASHEET.md:36 to 'µA-level back-feed through the spec-mandated 100 kΩ pull-up (≤ 33 µA), see carrier-interface §5'. Optionally note in ADR 0006 that the RC1 amendment supersedes line 31.

**Skeptic.** DATASHEET.md:36 says 'W_DISABLE2# radio-kill input — voltage-agnostic NMOS cells, no back-feed'. Per host_sideband.py:8 and carrier-interface.md:375, pin 26 has a 100 kΩ pull-up to the card rail, allowing up to 33 µA into an unpowered card. carrier-interface.md:225 is also worded 'no back-feed' for the EXP lines, which is correct there. One correction: ADR 0006:31 refers to the carrier-signature gates (pins 75/1, 1 MΩ pull-ups, ≤3.3 µA), not to W_DISABLE2#, so R29 does not make it stale. The datasheet wording is the only real issue. Cosmetic.

<a id="bus_enable-5"></a>

### bus_enable-5 — check_v2_netlist does not assert R35 (the safety default of the hold-off) or the R29/R26/C13 values

Reviewer severity **info**, skeptic: **confirmed / info**.

**Evidence.** hardware/tools/check_v2_netlist.py (diff 247f285..HEAD) adds on('U2',31,'IO38'), on('Q3',5,'IO38'), on('Q3',3,'EXP_OE') and on('Q3',4,'GND'), but has no check that R35 ties IO38 to +3V3 (grep for R35, R29, R26, C13 or value in that file returns nothing). If R35 were dropped or wired to GND, the 'bus held off through reset/ROM boot' guarantee would silently become 'bus on as soon as the carrier is present', and make check would still pass.

**Recommendation.** Add on('R35',1,'+3V3') and on('R35',2,'IO38'), plus value asserts for R35 = 100k, R29 = 100k, R26 = 10k and C13 = 1uF, to the v2 contract check.

**Skeptic.** hardware/tools/check_v2_netlist.py:97-101 checks U2.31, Q3.5 and Q3.3 on IO38/EXP_OE. A grep for R35, R29, R26, C13 or 'value' returns nothing. R35 is defined at host_sideband.py:47 but the contract check does not assert it. This is a coverage gap only; the current design is correct.

<a id="bus_enable-6"></a>

### bus_enable-6 — v2_selftest's 'IO38 high on every exit path, Ctrl-C included' holds only inside main(); direct bus_on() or test_bus() use from the REPL can leave the bus released

Reviewer severity **info**, skeptic: **confirmed / info**.

**Evidence.** v2_selftest.py:617-633: only main() has try/finally → bus_off(). bus_on() (line 105) and test_bus() (line 483) have no guard of their own. The procedure tells the operator to call bus_on() by hand (v2-test-procedure.md:244, 278). A Ctrl-C, or a MicroPython soft reset (Ctrl-D, which does not reset GPIOs), then leaves IO38 LOW. Procedure 8.5d already notes this. v2/firmware/README.md:91 and the module docstring (lines 13-14) overstate the guarantee. GPIO numbers are verified correct (see checked list).

**Recommendation.** Wrap the body of test_bus() in try/finally: bus_off(). Narrow the README/docstring claim to 'main() and test_bus()'. Recommend a boot.py containing Pin(38, Pin.OUT, value=1), so every MicroPython boot or soft reset holds the bus.

**Skeptic.** v2_selftest.py: only main() (around line 617) wraps its tests in try/finally: bus_off(). test_bus() (line 483) calls bus_off() at the end (point C, around line 545) but has no finally of its own, and bus_on() (line 105) is unguarded. The docstring lines 13-14 and README.md:89-90 ('on every exit path, Ctrl-C included') are true only for main(). Procedure 8.1d and 8.5 call bus_on() by hand. MicroPython's Ctrl-D soft reset does not reset GPIOs, which 8.5d acknowledges. Documentation and robustness only.

<a id="bus_enable-7"></a>

### bus_enable-7 — The sleep rule covers deep sleep only; light-sleep GPIO handling of IO38 is not stated

Reviewer severity **info**, skeptic: **confirmed / info**.

**Evidence.** carrier-interface.md:213-214 covers only deep sleep ('digital GPIO hold needed'). ESP-IDF can switch pads to their sleep configuration during light sleep (gpio sleep-select / peripheral power-down options). If IO38 goes high-Z then, R35 turns Q3b on, and the bus drops and needs about 1-6 ms after wake to come back. This is safe (it fails off) but may surprise a carrier application. Not verified on hardware.

**Recommendation.** Add a [FW] note: in light sleep, keep IO38's active configuration (gpio_sleep_sel_dis(38) or gpio_hold_en), or accept that the bus drops during sleep.

**Skeptic.** carrier-interface.md:213-214 covers deep sleep only, so the documentation gap is real. Whether IO38 actually floats in light sleep depends on the IDF configuration (GPIO sleep-select or peripheral power-down options) and has not been shown. Any failure is fail-safe (the bus goes off). Worth a one-line [FW] note.

<a id="dfm-r3"></a>

### dfm-r3 — Q1-Q3: the RC1 text still claims a 180° error swaps the Q halves; mcu_io-4 (it is electrically harmless) was not applied

Reviewer severity **info**, skeptic: **confirmed / info**.

**Evidence.** SSM6N56FE and SI1024X pinout: 1 S1, 2 G1, 3 D2, 4 S2, 5 G2, 6 D1 (cross-drained). Under 180° each device pin k lands on pad k+3. On Q2, device G1 then sits on pad 5 (IO47) and D1 on pad 3 (WAKE_ON_WWAN_n), so IO47 still drives WAKE and IO42 still drives LED_1_n. The same holds for Q3 (IO38 to EXP_OE, W_DISABLE2_n to IO40) and for Q1 (both drains EXP_OE). The wrong claims are still present: gen_fab.py C146449 basis 'was 90 (GATE V4) = Q-halves swapped', polarity_report.py:44 / polarity_checklist.md Q2 row '180 off swaps LED_1#/WAKE#', and the change record. The checklist's 'net GND' cue at pin 1 cannot tell the two orientations apart either, because pad 4 is also GND.

**Recommendation.** Correct the Q basis strings and the Q2 checklist note to say that 180° is electrically equivalent and only a 90° error matters (pads would not land). Keep Q1-Q3 in the pin-1 check for consistency, but don't hold the order on them.

**Skeptic.** Board pads for Q2: 1 GND, 2 IO42, 3 WAKE_ON_WWAN_n, 4 GND, 5 IO47, 6 LED_1_n. With the cross-drained pinout (1 S1, 2 G1, 3 D2, 4 S2, 5 G2, 6 D1), a 180° turn maps device pin k to pad k+3. Then G1 is on IO47 and D1 is on WAKE, which is the same as the intended G2(IO47)→D2(WAKE). IO42→LED_1_n is also kept. Q3 is equivalent in the same way, and Q1 has both drains on EXP_OE. The halves are identical, so 180° is electrically harmless. These claims are therefore wrong: 'Q-halves swapped' at gen_fab.py:90, '180 off swaps LED_1#/WAKE#' at polarity_report.py:44, and the Q2 row of the checklist. The pin-1 'net GND' cue also matches pad 4, so it cannot tell the two orientations apart. This is a documentation inaccuracy with no hardware risk.

<a id="dfm-r4"></a>

### dfm-r4 — dfm-7 leftovers are not fixed and the via counts are now staler

Reviewer severity **info**, skeptic: **confirmed / info**.

**Evidence.** Board scan: 256 vias, of which 92 are 0.35/0.2, 50 are 0.45/0.2 and 114 are 0.45/0.3. fab/README.md:24 still says '90 vias are 0.35/0.2', and docs/stackup.md:105 says '90 of 213'. A fresh gbrjob export (identical to the one in the zip) still has 'Revision': 'rev?', Finish None and 0.114 mm default dielectrics, which contradicts the order form (JLC06081H-2116, ENIG). The polarity_checklist.md header still says to trust N/S while each row gives top-view E/W corners. The RC1 change record does not mention dfm-7.

**Recommendation.** Update the via counts. Define the stackup and finish in Board Setup, or drop the gbrjob from the zip. Give the checklist corners as N/S plus top-view E/W.

**Skeptic.** KiCad scan finds 256 vias: 114 are 0.45/0.3, 92 are 0.35/0.2 and 50 are 0.45/0.2. fab/README.md:24 says '90 vias are 0.35/0.2', and docs/stackup.md:105 says '90 of 213'. The gbrjob inside fab/esp32_m2_companion_gerbers.zip has 'Revision': 'rev?', 'Finish': 'None' and 0.114 mm FR4 dielectrics. The checklist header says 'trust N/S, not E/W' while its rows give corners such as NE and SW. JLC orders from the web form, not the gbrjob, so this is information only.

<a id="dfm-r5"></a>

### dfm-r5 — LED wording in the new order remark is ambiguous ('lens toward the card edge')

Reviewer severity **info**, skeptic: **confirmed / info**.

**Evidence.** fab/README.md order remark: 'D3/D4 side-view LEDs: lens toward the card edge'. In M.2 usage, 'card edge' means the gold-finger edge (S). The intended direction is the nearby long side: D3/D4 sit at x=90.2, the edge is at x≈89, and the lens faces away from R3/R4 (checklist rows D3/D4). README step 4 says 'left card edge', which is a top-view term, and JLC's bottom preview mirrors E/W.

**Recommendation.** Word the remark as: 'lens facing the nearest long side edge, away from R3/R4 (not toward the gold fingers); "+" on the pad level with R3/R4'.

**Skeptic.** The order remark at fab/README.md:58 reads 'lens toward the card edge', which on an M.2 card can be read as the finger edge. Step 4 at line 69 says 'left card edge', a top-view E/W term, while the checklist header says bottom previews mirror E/W. The checklist rows themselves are clear ('away from R3, toward the card's long edge'). The wording is ambiguous, and the checklist rows reduce the risk.

<a id="dfm-r6"></a>

### dfm-r6 — C17 MPN text may not match LCSC C52923 (from memory, unverified)

Reviewer severity **info**, skeptic: **uncertain / info**.

**Evidence.** power_3v3.py:96 and docs/review/v2_reva_bom.md list C17 as 'CL05A105KA5NNNC' with LCSC C52923. From memory, C52923 is Samsung CL05A105KA5NQNC: same 1 µF 25 V X5R 0402, Basic. JLC assembles by LCSC number, so the placed part is unaffected.

**Recommendation.** Check the MPN on the LCSC page for C52923 and correct the BOM text if it differs.

**Skeptic.** power_3v3.py:96 and hardware/build/bom.md:10 do give C17 as CL05A105KA5NNNC with LCSC C52923. I could not check the LCSC page offline. My own recollection also points to CL05A105KA5NQNC for C52923, but that is unverified. NNNC and NQNC differ only in packaging/suffix, have the same 1 µF 25 V X5R 0402 rating, and JLC places by LCSC number. Either way this cannot affect the build, so it is information at most.

<a id="docs-10"></a>

### docs-10 — Contract says dev carriers use a WP jumper for the ID EEPROM. The dev carrier ties /WC to GND

Reviewer severity **info**, skeptic: **confirmed / info**.

**Evidence.** carrier-interface.md:248-249 (wiring fixed RC1): 'WP = GND through a 0 Ω or a jumper (jumper on dev carriers)'. m2-dev-carrier hardware/blocks/id_eeprom/id_eeprom.py ties pin 7 /WC directly to GND (pins 1,2,3,4,7 → GND). v2_selftest.py:471 assumes the same ('dev carrier U4: tied to GND'). program_eeprom() also writes 16-byte pages (M24C02). A carrier that uses another '24C02-class' part with 8-byte pages (e.g. AT24C02, which the contract allows: 'Package free') would wrap within each page and fail verify.

**Recommendation.** Change the contract parenthesis to describe the dev carrier as built, or plan the jumper for the next dev-carrier revision. In the self-test, write 8-byte pages, which is safe for every 24C02.

**Skeptic.** m2-dev-carrier id_eeprom.py ties /WC (pin 7) to GND ('/WC = GND (writes enabled)'), but carrier-interface.md:248-249 says 'jumper on dev carriers'. v2_selftest.py:470-471 writes 16-byte pages (M24C02). An 8-byte-page 24C02 such as the AT24C02, which the contract allows ('24C02-class … Package free'), would wrap within each page and fail verify. Info.

<a id="docs-11"></a>

### docs-11 — DATASHEET bottom-height claim is framed differently from the contract

Reviewer severity **info**, skeptic: **confirmed / info**.

**Evidence.** DATASHEET.md:92/241: '≤1.6 mm … within the 2.54 mm B-side allowance of an H4.2 socket (M.2 EM spec Fig 38)'. carrier-interface.md:49-54: 'above the M.2 Rev 1.0 double-sided 1.5 mm figure; sockets with at least the card-bottom clearance of the Amphenol MDT420B01001 … fit'. Bottom keep-out: DATASHEET:242 says 'first 4.8 mm … kept component-free', while contract §2 says parts start 5.2 mm out and 'two parts sit exactly at that limit'. Measured pads to the finger edge (y=150.025): C16 (new in RC1) 5.22 mm, C14 5.25 mm, U1 body 5.22 mm, so three parts now sit at the limit, not two.

**Recommendation.** Give gen_datasheet.py the contract's wording (exceeds the 1.5 mm double-sided figure; socket-dependent) and the 5.2 mm figure. Change 'two parts' to 'three parts (U1, C14, C16)' in contract §2.

**Skeptic.** KiCad python on the board: the edge is at y = 150.025, and the closest bottom pads are C16 at 5.215 mm (new in RC1), C14 at 5.25 mm and U1 at 5.475 mm (pads; the reviewer's 5.22 mm for U1 is a body figure). By pads, at least two parts sit at the 5.2 mm limit, now C16 and C14. The 'two parts' wording is not strictly wrong, but the set has changed. The DATASHEET framing ('within the 2.54 mm B-side allowance', '4.8 mm') differs from the contract framing ('above the 1.5 mm double-sided figure', 5.2 mm), as reported. Wording only, so info.

<a id="docs-12"></a>

### docs-12 — DATASHEET revision stamp is from a dirty tree

Reviewer severity **info**, skeptic: **confirmed / info**.

**Evidence.** DATASHEET.md:4 'rev `v1.0-revB-34-g1b8b86e-dirty`'. It was generated before commit 0f842a8 and from uncommitted changes. The change record already says to regenerate from the clean, ordered commit.

**Recommendation.** Rerun `make datasheet` on the commit to be tagged v2.0-revA, before ordering.

**Skeptic.** DATASHEET.md:4 has the stamp 'v1.0-revB-34-g1b8b86e-dirty'. The change record already notes that it must be regenerated from the clean, ordered commit, so this is a reminder of an existing action, not a new defect.

<a id="docs-13"></a>

### docs-13 — Self-test docstring says the REPL runs over USB-Serial-JTAG, but stock MicroPython enumerates as TinyUSB CDC

Reviewer severity **info**, skeptic: **confirmed / info**.

**Evidence.** v2/firmware/v2_selftest.py:3: 'report over the USB-Serial-JTAG REPL'. docs/v2-test-procedure.md:179 (6.1) expects 'TinyUSB CDC, 303a:4001'. The dev-carrier bring-up log records 303A:4001 for MicroPython.

**Recommendation.** Change the docstring to 'USB CDC REPL'.

**Skeptic.** v2_selftest.py:3 says 'USB-Serial-JTAG REPL'. Stock ESP32_GENERIC_S3 MicroPython enumerates as TinyUSB CDC 303a:4001, which the procedure expects at 6.1 and 10.1a and the dev-carrier bring-up log records. The docstring is inaccurate and cosmetic.

<a id="docs-14"></a>

### docs-14 — Small executability gaps in the procedure

Reviewer severity **info**, skeptic: **confirmed / info**.

**Evidence.** 8.3c says 'corrupt one byte (REPL writeto_mem)' but does not say to call v2_selftest.bus_on() and build SoftI2C(scl=Pin(41), sda=Pin(39)) first; with the bus held the write NACKs. §10 runs main(signature=False) on laptops and adapters with outputs=True, so the script pulses WAKE_ON_WWAN# (pin 23) into a real host. 10.1b expects 'all non-SKIP items PASS', but the run always produces CHECK items. 7.3b/7.3e expect the card rail < 0.3 V with JP2/JP3 = 3V3. That turns Q1 on, so R26 10 kΩ loads the rail, and ~40 µA injected (7.3e) gives up to ~0.4 V if the unpowered ESP32 presents a high impedance.

**Recommendation.** Add the bus_on and I2C lines to 8.3c. Use outputs=False on foreign hosts unless the wake behaviour is the thing under test. Say 'no FAIL'. Record 7.3b/e as a measurement, or allow ≤ 0.5 V.

**Skeptic.** Partly confirmed. 8.3c gives no bus_on or I2C setup, and the self-test leaves the bus held (test C), so writeto_mem would NACK. main() defaults to outputs=True (v2_selftest.py:603-604), so §10 pulses WAKE# into a real host. 10.1b says 'all non-SKIP items PASS', but the script reports CHECK items and prints 'PASS (tick the CHECK items by hand)', so this is wording only. The 7.3b/e sub-claim is mostly refuted. With pin 26 driven at 3.3 V in 7.3e, Q3a is also on, so R30 10 kΩ is in parallel with R26 10 kΩ, about 5 kΩ. About 40 µA then gives about 0.2 V, below 0.3 V. In 7.3b only about 7 µA flows through R22/R23, about 70 mV. Info overall.

<a id="docs-15"></a>

### docs-15 — Sibling-repo items outside this repo: dev-carrier CLAUDE.md has an absolute personal path, and its bring-up §7 is pre-RC1

Reviewer severity **info**, skeptic: **confirmed / info**.

**Evidence.** m2-dev-carrier CLAUDE.md:4-5 (tracked) imports '@<scratch> a home path. The contract's own example uses '<workspace>'. m2-dev-carrier docs/bringup.md §7 still says 'the firmware reports `EXP_OE` on'; that readback is gone after RC1. The v2 procedure says it replaces that §7, so nothing breaks.

**Recommendation.** In the dev-carrier repo, replace the path with a relative or `<workspace>` form (CLAUDE.md global rule) and point §7 at docs/v2-test-procedure.md.

**Skeptic.** m2-dev-carrier CLAUDE.md is tracked (git ls-files) and its lines 4-5 contain an absolute home-directory path, against the global no-local-paths rule. m2-dev-carrier docs/bringup.md:206 still expects the firmware to report EXP_OE on, a readback RC1 removed. Both are in the sibling repo and do not block this order, so info.

<a id="docs-8"></a>

### docs-8 — 'No back-feed' claims (SPEC G9, DATASHEET, ADR 0006, block docstrings) contradict the contract, now 10× worse with R29 at 100 kΩ

Reviewer severity **minor**, skeptic: **confirmed / info**.

**Evidence.** SPEC.md G9: 'Voltage-agnostic, with no back-feed into an unpowered card'. DATASHEET.md:36: 'voltage-agnostic NMOS cells, no back-feed'. ADR 0006:31: 'Insulated gates mean no back-feed into an unpowered card'. host_sideband.py:4 says 'no back-feed when unpowered', and edge_expansion.py docstring says 'host voltage only reaches insulated FET gates (no back-feed)'. carrier-interface.md §5 table: pin 26 '100 kΩ to the card rail: ≤ 33 µA' and 75/1 '≤ 3.3 µA each', '~40 µA into the unpowered card rail'. Procedure 7.3e expects ≈33 µA. RC1 cut R29 from 1 MΩ to 100 kΩ, raising this path from 3.3 µA to 33 µA (review expansion-8 had already flagged the wording).

**Recommendation.** Reword G9, the DATASHEET feature line and the docstrings to 'no back-feed through the NMOS cells; the card pull-ups pass ≤ 33 µA (pin 26) / ≤ 3.3 µA (pins 75/1) into an unpowered card rail (contract §5)'. Add a dated amendment line under ADR 0006 Decision 2.

**Skeptic.** SPEC.md:266, ADR 0006:31, host_sideband.py:4 and edge_expansion.py:14 say 'no back-feed'. The contract's own §5 (carrier-interface.md:374-381) lists ≤ 33 µA on pin 26 (R29 100 kΩ, up from 3.3 µA at 1 MΩ) and ~40 µA into the unpowered card rail. This is expansion-8 (info), which the RC1 change record did not address, and RC1 made the current 10× larger. The circuit is benign: the rail stays < 0.3 V under the R26/R30 loads, and the contract table is correct. The issue is wording only, so info.

<a id="layout-3"></a>

### layout-3 — GND finger 57 is still tied only by a 0.127 mm track; its F.Cu island has no via (review layout-4 named it)

Reviewer severity **minor**, skeptic: **confirmed / info**.

**Evidence.** J1.57 (x 95.075-95.425) sits in GND_top island bbox [95.13,147.4,95.37,149.7], area 0.56 mm², with 0 vias. The only path is the locked 0.127 mm F.Cu track (95.25,147.7)->(95.25,147.45)->(95.55,147.15)->(95.55,146.9)->(95.25,146.6), about 1.35 mm, to via (95.25,146.6) 0.45/0.2. This is unchanged from 247f285. v2_gnd_fence.py step 1 skipped finger 57 because that via is within FINGER_R=1.0 of (95.25,146.8). The commit message does not list 57 among the fingers left without a spot. Every other GND finger now enters a pour island with ≥6 vias, 0.62-1.75 mm away.

**Recommendation.** Widen the finger-57 tie to ≥0.2 mm where clearance to fingers 55/59 allows, or add a second path. Otherwise record it in the change log as accepted (a single 0.127 mm tie, about 1-1.5 nH).

**Skeptic.** The facts check out. J1.57 is GND, x 95.075-95.425. It is still tied only by the four locked 0.127 mm F.Cu segments to via (95.25,146.6), and those segments are identical at 247f285 and HEAD. The review's layout-4 evidence named this tie, and the RC1 commit message (7aac3e4) does not mention finger 57. However, the review's recommendation was 'GND vias at the top of every GND finger (y~146.5-147.0)', and finger 57 already has one at y 146.6, 0.9 mm above its top. The fence script skipped it correctly by that rule. The leftover concern is about 1.3 nH of tie inductance on one of 13 GND fingers. That is not functional at these rates, so I downgrade it to info: record it as accepted, or widen the tie.

<a id="layout-4"></a>

### layout-4 — New C16 sits exactly at the M.2 bottom-side component zone limit (5.20 mm), like U1/C14

Reviewer severity **info**, skeptic: **confirmed / info**.

**Evidence.** C16 is on B.Cu at (94.5,144.5), rot 0. Fab body y 144.20-144.80, courtyard to 145.005. With the card edge at y=150.0, layout-7's limit is body y ≤ 144.8, so the margin is 0.00 mm. C14 was not moved the optional 0.3 mm that layout-7 suggested (it is unchanged between 247f285 and HEAD).

**Recommendation.** If convenient, shift C16 by about 0.2-0.3 mm toward -y (R32 is above it; check room). Otherwise add C16 to the CG1 note listing the parts at the limit (U1, C14, C16).

**Skeptic.** C16 is C_0402 on B.Cu at (94.5,144.5). Its B.Fab bbox is y 144.2-144.8, its pads reach 144.81 and its courtyard 144.985. That matches how the review measured U1, whose fab bbox ends at 144.80 and which was listed at 'zero margin'. C14 is unchanged at (91.6,144.3), so the optional 0.3 mm move from layout-7 was not made. This is a documentation and margin note only, so info is right.

<a id="layout-5"></a>

### layout-5 — C17 is ~3.7 mm of track from U6 OUT, beyond FB1.1's pad on a 0.2 mm stub, not 'next to U6 OUT' as the change record says

Reviewer severity **info**, skeptic: **confirmed / info**.

**Evidence.** C17 (1 µF) is on B.Cu at (90.65,137.37). The +3V3_EFUSE path runs from U6.6 (91.35,141.9) on 0.35 mm B.Cu to FB1.1 (91.99,139.2), then 0.2 mm (91.65,138.95)->(91.65,137.89)->(91.13,137.37) to C17.1. That is about 1.5 mm at 0.35 mm, the FB1.1 pad, then 1.8 mm at 0.2 mm, roughly 3 nH. The straight-line distance from U6.6 is 4.5 mm. GND is via-in-pad (90.17,137.37) to In1, which is good. Electrically it is on the correct, pre-bead side, and 3 nH is negligible at the 500 ns fast-trip time scale, so the layout-2 fix works. Only TI's 'very close to OUT' guidance and the wording in docs/review-findings.md are not literally met.

**Recommendation.** No change needed for the order. Optionally correct the change-record wording to 'on +3V3_EFUSE at FB1.1'. Keep the bring-up output-short scope test on U6.6.

**Skeptic.** The +3V3_EFUSE tracks at HEAD run 0.35 mm from (91.35,140.8) to (91.35,140.3), then (91.8,139.85), then (91.8,139.5), ending at FB1.1 (91.99,139.2). From there a 0.2 mm track runs (91.65,138.95) to (91.65,137.89) to (91.13,137.37), which is C17.1. C17.2 is GND on via-in-pad (90.17,137.37). C17 is on the correct pre-bead net but about 1.8 mm beyond FB1's pad, so 'next to U6 OUT' in docs/review-findings.md:582-583 overstates it. The electrical effect is negligible, so this is a wording note: info.

<a id="layout-6"></a>

### layout-6 — Remaining GND stitching gaps after the fence

Reviewer severity **info**, skeptic: **confirmed / info**.

**Evidence.** 0.25 mm grid of outer-pour points to the nearest GND via, outside the finger band. F.Cu: points >2.5 mm went from 1296 (28%) to 143 (3.0%), >4 mm from 248 to 0, worst from 6.99 to 3.95 mm. B.Cu: >2.5 mm from 1718 (38%) to 171 (3.7%), >4 mm from 540 to 0, worst from 7.14 to 3.95 mm. The remaining cluster is the left edge at (89.5-90.0, 132.75-133.75), 36-39 points >3 mm on both layers, plus smaller ones at (110.5,134.25), (93.25,126.25) and (99.25,136.75). USB layer changes without a return via within 1 mm: USB_D_N (109.9,142.35) 1.35 mm, U2-side pair USB_D_N (91.25,135.23) 1.69 mm and USB_D_P (91.25,136.5) 1.39 mm. USBH3_D_N/P and USB_D_P (110.4,144.25) now have 0.89/0.94/0.58 mm. The commit's '<= 2.5 mm wherever a legal spot exists' is accurate.

**Recommendation.** Acceptable for Full-Speed USB and GPIO rates. If the left-edge y≈133 area can take one via (for example by moving a track), add it. Otherwise no action.

**Skeptic.** I checked the USB return-via distances independently at HEAD: USBH3_D_N 0.89, USBH3_D_P 0.94, USB_D_N (109.9,142.35) 1.35, USB_D_N (91.25,135.23) 1.69, USB_D_P (110.4,144.25) 0.58 and USB_D_P (91.25,136.5) 1.39 mm. All match the finding, and the GND via count rose from 38 to 76. I did not rerun the grid map, but it agrees with the commit's own claim. There is no defect here, only residual margin: info.

<a id="layout-7"></a>

### layout-7 — Fence vias overlap same-net GND pads and sit under bottom bodies; v2_gnd_fence.py does not check GND pads

Reviewer severity **info**, skeptic: **confirmed / info**.

**Evidence.** In v2_gnd_fence.py, Board.__init__ collects only non-GND pads as obstacles, so new vias land in or under GND pads. Full via-in-pad: (90.17,137.37) 0.45/0.3 in C17.2 (0402). Partial overlaps: (89.65,129.1) on D3.1 (side-view LED), (95.1,144.95) on C16.2. C15.2 was placed partly over the existing via (89.95,142.05). Vias inside bottom courtyards: D4 (89.85,126.3) and (89.6,124.75), U1 (108.05,144.85), C2 (94.85,122.55), TP1 (107.5,135.25). Inside top courtyards: J3/J4 (99.95,142.9), (97.05,144.95), (95.1,144.95), (105.05,141.3). All rely on epoxy filled & capped vias (fab/README.md:28), as about 100 existing pads already do (layout-9).

**Recommendation.** Keep 'Epoxy Filled & Capped' selected (it is mandatory now). Optionally nudge the D3.1 and C16.2 partial overlaps off the pads. Also make the fence script treat same-net pads as obstacles for future runs.

**Skeptic.** A hit test of GND vias against GND pads at HEAD finds these new via-on-pad cases: D3.1 (89.65,129.1), C15.2 (89.95,142.05), C16.2 (95.1,144.95) and C17.2 (90.17,137.37), on top of the roughly 30 that already existed. D3.1 already had a via in its pad at (89.85,128.5) before RC1. Via covering 'Epoxy Filled & Capped' is set (fab/README.md:28). All of these are same-net, so this is a process note only: info.

<a id="layout-8"></a>

### layout-8 — Minor RC1 copper artifacts and thin In4 slivers next to new voids

Reviewer severity **info**, skeptic: **confirmed / info**.

**Evidence.** A new 0.07 mm +3V3_M2 B.Cu stub (108.6,147.55)-(108.55,147.5) lies entirely inside J1.4. It was not present at 247f285 and is harmless. The IO38 route uses 0.05 mm stair-step segments around (104.1-104.7,131.2-132.55). In4: three new fence vias, (106.55,133.5), (106.75,131.9) and (107.5,133.25), merge into one 3.4 mm² void (104.72-107.93, 131.42-133.93) and leave a ≈0.15 mm sliver against the IO38 via antipad at (104.8,132.65). Other new necks of 0.15-0.17 mm are at (109.4,137.85), (104.95,122.45), (107.05,124.2), (99.95,142.9) and (108.05,144.85). These are above JLC inner minimums and off the power path. The full-width In4 cross-section stays ≥12.96 mm, and the left FB1→U2.2 strip stays ≥3.38 mm. In4 area dropped 639.3 → 617.8 mm² (-3.4%) and remains a single island.

**Recommendation.** No action needed for this order. Clean up if the layout is touched again.

**Skeptic.** The new +3V3_M2 B.Cu stub (108.6,147.55)-(108.55,147.5) is present at HEAD and absent at 247f285, which I confirmed in the short-segment list. The In4 area of 639.3 to 617.8 mm2 with a single outline is confirmed. I did not measure the sliver widths separately, but JLC inner-layer minimums are below the 0.15 mm reported, and none of them lies on the power path. Harmless cleanup items: info.

<a id="power-rc1-4"></a>

### power-rc1-4 — C17 effective capacitance below TI's '>1 uF' after DC bias; review asked C0G for C16 but X7R was fitted

Reviewer severity **minor**, skeptic: **confirmed / info**.

**Evidence.** C17 is CL05A105KA5NNNC: 1 uF ±10 % X5R in 0402. At 3.3 V DC bias it retains roughly 0.7-0.8 uF, while TI §8 (tps25947.txt:3786) says 'larger than 1uF'. The BOM already carries C15849 (1 uF 50 V X7R 0603, Basic, used for C5/C13), which holds much more capacitance at 3.3 V. The original review recommendation for power-1 (v2_rc1_design_review.md:192) specified '1 nF C0G'. C16 is 0402B102K500NT, which is X7R ±10 %. At 1.13 V bias that difference is negligible: tau ±10 %.

**Recommendation.** Consider C15849 0603 for C17 (no new BOM line) if the footprint fits. Record that X7R for C16 is an accepted deviation (or use the smaller C0G value of power-rc1-1).

**Skeptic.** The facts are mostly right. C17 is CL05A105KA5NNNC, a 1 uF 25 V X5R 0402 part, and at 3.3 V DC bias it retains about 0.7-0.8 uF. C16 is 0402B102K500NT, an X7R part, whereas the review asked for C0G. Two corrections. First, the suggested alternative C15849 is CL10A105KB8NNNC, which is X5R (Samsung code 'A'), not X7R as the finding says; its only advantage is the larger 0603 case and 50 V rating, so less DC-bias loss. Second, the impact is negligible. TI's '>1 uF' is layout guidance; the rail has 54 uF of bulk just behind FB1 (50 mOhm); and X7R at about 1.1 V bias with ±10 % changes C16 tau only marginally, which is irrelevant next to power-rc1-1. Downgrade to info.

<a id="power-rc1-5"></a>

### power-rc1-5 — OVLO filter capacitor sits ~3 mm from the OVLO pin (beyond R32)

Reviewer severity **info**, skeptic: **confirmed / info**.

**Evidence.** C16 pad 1 is at (94.02,144.5). The track runs (94.02,144.5)->(93.8,143.6) to R32 pad 1 (93.728,143.557), then (93.45,143.3)->(93.05,142.9)->(93.05,141.9)->(92.75,141.75) to U6 pin 2 (92.5,141.675), about 2.9 mm of 0.127 mm track. The OVLO and DVDT traces sit on B.Cu over a solid In4 +3V3 plane (zone hit-tests confirm In4 +3V3 and In1 GND under every OVLO, DVDT and EN point checked), so the In2/In3 EXP_5/EXP_7/EXP_11 crossings are shielded. The nearest same-layer aggressor is the +3V3_M2 0.127 mm track (93.4,140.15-141.45) at ~0.57 mm, which is DC. Acceptable.

**Recommendation.** No action required. If C16 is changed per power-rc1-1, place the new part at the U6 pin-2 end of the trace (~92.9,142.3) instead.

**Skeptic.** The geometry is confirmed. C16 pad 1 is at (94.02,144.5). The OVLO net runs (94.02,144.5)->(93.8,143.6) to R32 pad 1 (93.728,143.557), then (93.45,143.3)->(93.05,142.9)->(93.05,141.9)->(92.9,141.75)->(92.75,141.75) to U6 pin 2 (92.5,141.675). That is about 0.93 mm plus about 2.0 mm, roughly 2.9 mm of 0.127-0.13 mm track. The placement matches what the original review asked for ('next to R32'). With a 1 nF filter on a 34 kOhm node, the residual trace pickup between C16 and the pin is not significant. Info, no action, as the finding says.
