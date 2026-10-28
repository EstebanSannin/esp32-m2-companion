# v2.0 Rev A — bring-up and acceptance test procedure

How to validate the v2.0 Rev A card on the day boards arrive. The goal is to show the
success criteria **S-v2-1..4** (SPEC §13 A3) and the host sidebands (G9) with written evidence.

This procedure closes review findings contract_test-2, contract_test-5 and mcu_io-7 in
`docs/review/v2_rc1_design_review.md`. It includes the RC1 change: **bus ON = carrier signature
AND firmware**, with IO38 as the active-low release (`docs/pinmap.md` §6.3).

- **Firmware:** `v2/firmware/v2_selftest.py` (MicroPython). How to run it:
  `v2/firmware/README.md`.
- **Dev carrier:** its own plan in `m2-dev-carrier/docs/bringup.md` covers the carrier side.
  Steps 1–4 of that plan must pass on a carrier board before a v2 card goes in. This document is
  the card side and replaces that plan's §7 for v2 cards.
- **Board #1** runs every step. Boards #2+ run the short path in §12.
- Record values in the results table (§13), findings in `docs/review-findings.md`, and lessons
  in the block `LESSONS.md`.
- Never write unit serials or MACs into tracked files (repo CLAUDE.md). Keep them on the paper
  or local results sheet.

## Coverage

| Criterion | What it asks | Steps | Executable as written? |
|---|---|---|---|
| S-v2-1 | EXP bus off, ≤ 2 µA per EXP pin at 0 / 1.8 / 3.3 V, on Mallow, a laptop WWAN slot, an M.2→USB adapter, and the dev carrier with signature open / 1.8 V / 3.3 V; also unpowered | 7, 10 | **Dev carrier: yes.** Mallow: only on the pins it exposes. Laptop and USB adapter: **proxy only** (§10) |
| S-v2-2 | Bus on with the signature grounded; every EXP line proven both ways by a firmware self-test | 8 | Yes, with the J3 loopback jumpers. The EEPROM path needs a hand-fitted 24C02 on one dev carrier (U4 is DNP) |
| S-v2-3 | OVP trips at 3.44–3.57 V, survives 5 V, recovers below ~3.17 V | 4 | Yes. Needs a bench limit of ≥ 1.2 A for the recovery step |
| S-v2-4 | All v1 criteria (SPEC §10) still pass | 11 | Yes, except item 4 (needs a Qwiic sensor) and item 6 (RPi5, best effort) |
| G9 / mcu_io-7 | LED_1#, WAKE#, W_DISABLE2# on every host; 1.8 V levels; no back-feed | 7.3, 9, 10 | W_DISABLE2# at 1.8 / 1.2 V: yes. LED_1#/WAKE# with a 1.8 V pull-up: **not on the dev carrier** (§9.3) |

## 0. Equipment

| Item | Used in | Note |
|---|---|---|
| Dev carrier (`m2-dev-carrier`) that has passed its own steps 1–4 | 3–9 | |
| DMM: V, Ω, **µA range with ≤ 0.1 µA resolution** | all | the µA range is for S-v2-1 |
| Bench supply 0–6 V, current limit, **≥ 1.2 A** | 3, 4, 9.3 | the dev-carrier list says ≥ 1 A; the OVLO restart needs up to 1.15 A |
| Scope, 2 channels | 3, 4, 8.5 | needed for the inrush and reset-glitch steps; the OVP static window works without it |
| 0.1 Ω shunt resistor (optional) | 3 | inrush current on the scope |
| 2 × 100 kΩ resistors with Dupont leads | 7, 8 | bus-state indicator on J3 |
| 6 × female-female Dupont jumpers, 2.54 mm | 8 | J3 loopback |
| One dev carrier with **U4 fitted** (M24C02-WMN6TP, LCSC C7562, SOIC-8) + C11 100 nF, **JP7/JP8 bridged** | 8.3 | **hand rework**: U4/C11 are DNP and JP7/JP8 open as built |
| 1 kΩ resistor | 9.3 | 1.2 V W_DISABLE2# test |
| Qwiic I²C sensor + Qwiic cable (one with flying leads is handy as a +3V3 probe point) | 3, 11 | owner may not have a sensor: v1 criterion 4 needs one |
| Mallow + Verdin SoM, jumper wires for X16 | 10.1, 11 | X16.19 → SoM GPIO for BOOT (ADR 0002) |
| Laptop with an M.2 Key-B WWAN slot | 10.2 | **owner may not have one**; enclosed bays don't fit (R11) |
| M.2 Key-B → USB adapter board | 10.3 | **owner may not have one** |
| RPi5 + Waveshare Key-B HAT | 10.4, 11 | best effort (ADR 0004, R4) |
| Loupe or phone macro | 1 | |
| PC with `esptool` and `mpremote` | 5, 6 | `pip install esptool mpremote` |

### Measurement points

| What | Where |
|---|---|
| Card `+3V3` rail (after eFuse + FB1) | card **J3 (Qwiic) pin 2**, GND = J3 pin 1 (top side) |
| Card supply input (`+3V3_M2`) | dev carrier **J5 hdr 3** `+3V3_CARD` |
| `EXP_OE` (bus switch enable) | **C13 pad 1** or R26 pad 2 (card bottom; locations in the assembly drawing, `make drawings`) |
| `CONFIG_2` / `CONFIG_3` on the card | **R22 / R23 pad 2** (card bottom) |
| EXP_0..11 at the edge | dev carrier **J3** odd pins: EXP_n = hdr 2n+1 (EXP_0 = 1, EXP_1 = 3 … EXP_11 = 23), even pins = GND |
| Sidebands | dev carrier **J4**: hdr 1 PERST#, 3 BOOT, 5 W_DISABLE1#, 7 CONFIG_0, 9 CONFIG_1, 11 CONFIG_2, 13 CONFIG_3, 15 LED_1#, 17 WAKE#, 19 W_DISABLE2# |
| Carrier rails | dev carrier **J5**: hdr 1 `+3V3`, 3 `+3V3_CARD`, 5 `+1V8_REF`, 7 `+5V` |

Dev-carrier jumpers:
- **JP1:** REG / BENCH / OFF (removed).
- **JP2 / JP3:** CONFIG_2 / CONFIG_3 to GND\* / open / 10 k→1V8 / 10 k→3V3.
- **JP4:** pin 8 ↔ BOOT.
- **JP5:** W_DISABLE2# ↔ GND.
- **JP6:** WAKE LED D6.
- **JP7 / JP8:** EEPROM SDA / SCL solder jumpers.
- **D5:** LED_1# indicator. **D6:** WAKE indicator. **SW1:** RESET (PERST#). **SW2:** BOOT.

### Bus-state indicator (works with any firmware)

Fit a **100 kΩ from J3 hdr 1 (EXP_0) to hdr 2 (GND)**. EXP_0 has a 4.7 kΩ card pull-up (R20) on
the **MCU side** of the switch, so the edge pin shows the switch state:

- **Bus ON:** 3.3 V × 100 / 104.9 ≈ **3.15 V** (3.0–3.3 V).
- **Bus OFF:** **< 0.05 V**. The switch is open and the 100 kΩ pulls the floating edge pin down.

A second 100 kΩ on hdr 3 (EXP_1, R21) gives the same reading. The firmware can't read EXP_OE any
more (RC1), so this indicator, the EEPROM ACK and the loopback are the only ways to see the bus.

---

## 1. Visual and assembly checks (card unpowered)

Setup: card on the bench, loupe. Use `fab/polarity_checklist.md` with the as-ordered JLC
preview next to it. N = screw-notch edge, S = finger edge.

| # | Action | Expected | Pass | Covers |
|---|---|---|---|---|
| 1.1 | U3, U4, U5 (TMUX1511, UQFN-16): pin-1 dot against the silk dot | pin 1 = SEL1 (EXP_OE): U3 at the **SE** corner, U4 and U5 at the **NE** corner | [ ] | S-v2-1/2 |
| 1.2 | U6 (TPS259470A, VQFN-10) | pin 1 (EN/UVLO, L-shaped corner pad) at the **NE** corner | [ ] | S-v2-3 |
| 1.3 | Q1, Q2, Q3 (SSM6N56FE, SOT-563) | pin-1 mark at the **NE** corner on all three. On Q2, 180° swaps LED_1# and WAKE# (step 9.1 catches it too) | [ ] | S-v2-1, G9 |
| 1.4 | D3 (green), D4 (red), side-view | "+" (anode) on the **S** pad, level with R3.2 / R4.2; cathode bar toward **N**; lens facing **outward**, away from R3/R4 toward the long card edge. **Both must hold** (GATE B3) | [ ] | S-v2-4 |
| 1.5 | D1, D2 (BAT54A), U1 (USBLC6) | pin 1 at the **SW** corner | [ ] | S-v2-4 |
| 1.6 | 0.4 mm-pitch parts U3–U6, RN1–RN3 | no bridges along the package edges (0.1 mm mask dams, review dfm-3); no tombstoned 0402s | [ ] | — |
| 1.7 | Gold fingers | no solder or flux on them; leading edge **hand-chamfered** before first insertion (SPEC A1) | [ ] | — |
| 1.8 | U2 module, J3/J4 JST connectors | module flat, castellations wetted; JST shell legs soldered | [ ] | S-v2-4 |

## 2. Unpowered resistance checks (card out of any slot)

Setup: DMM in Ω, **red lead on the first-named point**, black on the second. Let the reading
settle: the caps charge. Fingers: odd pins on the top side, even on the bottom.

| # | Between | Expected | Pass | Covers |
|---|---|---|---|---|
| 2.1 | VCC finger (2, 4, 70, 72 or 74) ↔ GND finger (3) | ≈ 150 kΩ (OVLO divider R31 + R32 = 152.3 kΩ ‖ eFuse IN); pass **> 100 kΩ** | [ ] | S-v2-3 |
| 2.2 | Card `+3V3` (J3 pin 2) ↔ GND (J3 pin 1) | **> 1 kΩ** after settling (no short); record | [ ] | — |
| 2.3 | VCC finger ↔ J3 pin 2 | **> 1 kΩ** (eFuse off, not bypassed) | [ ] | S-v2-3 |
| 2.4 | CONFIG_0 (21) ↔ GND; CONFIG_1 (69) ↔ GND | **< 1 Ω** (state 6) | [ ] | G10 |
| 2.5 | CONFIG_2 (75) ↔ J3 pin 2; CONFIG_3 (1) ↔ J3 pin 2 | **1.00 MΩ ± 5 %** (R22 / R23) | [ ] | S-v2-1 |
| 2.6 | W_DISABLE2# (26) ↔ J3 pin 2 | **100 kΩ ± 5 %** (R29; RC1 value) | [ ] | G9 |
| 2.7 | LED_1# (10) ↔ GND; WAKE# (23) ↔ GND | **> 1 MΩ** (NMOS off). Reversed leads show the body diode, which is normal | [ ] | G9 |
| 2.8 | Each EXP finger (30, 32, 34, 36, 40, 59–65) ↔ GND | **> 1 MΩ** (switches off, unpowered) | [ ] | S-v2-1 |
| 2.9 | Adjacent EXP fingers 59↔60 … 64↔65, 30↔32, 34↔36 | **> 1 MΩ** (no bridge) | [ ] | S-v2-2 |

## 3. First power: bench supply through the dev carrier (dVdt inrush)

Setup:
- Dev carrier USB-C to the PC (carrier logic and USB data).
- Card fitted and screwed. JP2/JP3 on GND, JP4 fitted, JP5/JP6 open, **JP1 removed (OFF)**.
- Bench supply at **3.30 V, limit 0.5 A**, wired to J6 with its output off.
- Scope CH1 on card J3 pin 2 (card `+3V3`), CH2 on J5 hdr 3 (input). Optional: 0.1 Ω shunt in
  the bench + lead, measured differentially.

| # | Action | Expected | Pass | Covers |
|---|---|---|---|---|
| 3.1 | Bench output on, JP1 still OFF | J5 hdr 3 < 0.3 V; bench current ≈ 0 | [ ] | — |
| 3.2 | Output off. Fit **JP1 = BENCH**. Trigger the scope on CH2 rising, then switch the output on | CH1 ramps **monotonically** from 0 to 3.3 V in **2.5–13 ms** (typ ≈ 5 ms; C15 2.2 nF, SR 0.25–1.3 V/ms). No step, no sag back below 2.4 V (UVP chatter, review power-3) | [ ] | K1 |
| 3.3 | Inrush current (shunt or bench readout) | rail-charging current **≤ 0.15 A** (≈ 45 mA typ, ≤ 90 mA worst for ~65 µF), then the ESP32 boot current. The bench never goes into CC at 0.5 A | [ ] | K1 |
| 3.4 | Steady state | D3 green on; card `+3V3` (J3 pin 2) = input − ≤ 50 mV: **3.25–3.30 V**; idle current **30–90 mA** (record) | [ ] | S-v2-4 |
| 3.5 | Touch test after 1 min | U6, FB1 and the module not warm | [ ] | — |

**Stop** if the rail is missing, the bench is in CC, or anything gets warm.

## 4. Over-voltage cutoff, OVLO (S-v2-3)

Setup as at the end of §3 (JP1 = BENCH, card running).
- Monitor the **input** on J5 hdr 3 with the DMM: read it there, not on the supply display (lead
  drop).
- Monitor the **card rail** on J3 pin 2 (DMM or scope).
- **Raise the bench limit to 1.2 A for this section:** after an OVLO trip the eFuse restarts in
  current limit (0.85–1.15 A) and bypasses dVdt (TPS25947 §7.3.3). This departs from the
  dev-carrier R8 rule (≤ 0.5 A), and only for this step.
- **Never above 5.5 V** in this procedure. The design survives ~18 V, but S-v2-3 asks for 5 V.

| # | Action | Expected | Pass | Covers |
|---|---|---|---|---|
| 4.1 | From 3.30 V, raise the input in **10 mV** steps, 2 s per step, watching J3 pin 2 | rail collapses to < 0.3 V at **V_trip = 3.44–3.57 V** (record). D3 off, USB disconnects. If nothing trips at 3.60 V: **stop, FAIL** | [ ] | S-v2-3 |
| 4.2 | Go back down to **3.30 V** | card **stays off** (release is 3.13–3.25 V). This is expected: on a 3.3 V host, a trip needs a slot power cycle (ADR 0007, `power_3v3.py`) | [ ] | S-v2-3 |
| 4.3 | Keep lowering in 10 mV steps | rail returns at **V_release = 3.13–3.25 V** (record; SPEC "~3.17 V"). Restart is current-limited: a brief bench current up to ~1.15 A is normal | [ ] | S-v2-3 |
| 4.4 | Back to 3.30 V | card runs, enumerates again (§5) | [ ] | S-v2-3 |
| 4.5 | **5 V survival.** Card running at 3.30 V. Scope CH1 on J3 pin 2, single trigger. Step the supply to **5.00 V** (preset + output switch, or the fastest knob turn), hold 10 s | card rail peak **≤ 3.6 V** (record; design ≈ +0.1 V over 3.3 V, then off). Rail then < 0.3 V. Nothing warm | [ ] | S-v2-3, G11 |
| 4.6 | Output off (0 V), then 3.30 V on | card boots, enumerates; §7 self-test still PASS | [ ] | S-v2-3 |

Set the limit back to 0.5 A. Output off, **JP1 = REG** for the rest unless a step says BENCH.

## 5. USB enumeration

Setup: JP1 = REG, USB-C to the PC.

| # | Action | Expected | Pass | Covers |
|---|---|---|---|---|
| 5.1 | Plug in (blank flash from JLC) | `lsusb` / System Information shows Espressif **303a:1001** (USB JTAG/serial debug unit). Port `/dev/ttyACM<n>` or `/dev/cu.usbmodem<n>` | [ ] | S-v2-4 (§10.1) |
| 5.2 | `esptool --chip esp32s3 -p <port> flash_id` | ESP32-S3, flash **8 MB** | [ ] | S-v2-4 |
| 5.3 | `esptool --chip esp32s3 -p <port> read_mac` | record on the local sheet only (unit serial) | [ ] | — |
| 5.4 | Flip the USB-C plug | enumerates both ways | [ ] | — |

## 6. Flash MicroPython

Follow `v2/firmware/README.md` §1 (stock ESP32_GENERIC_S3, default variant, **not**
SPIRAM_OCT). Then copy the script:
`mpremote connect <port> cp v2/firmware/v2_selftest.py :`.

| # | Action | Expected | Pass | Covers |
|---|---|---|---|---|
| 6.1 | Flash and reset | re-enumerates as MicroPython (TinyUSB CDC, **303a:4001**); REPL banner shows ESP32S3 | [ ] | S-v2-4 (§10.2) |
| 6.2 | Bus indicator fitted (J3 hdr 1, 100 kΩ), JP2/JP3 on **GND**, MicroPython idle (script not run) | J3 hdr 1 **< 0.05 V**: the bus stays held off with the signature present and no firmware release (R35 → Q3b) | [ ] | RC1 hold-off |

## 7. Self-test without a carrier signature: bus must stay off (S-v2-1)

Setup: dev carrier, JP1 = REG, bus indicator on J3 hdr 1 and hdr 3. J3 loopback jumpers fitted
(§8.2 map); with no signature they must not conduct.

### 7.1 Firmware run, signature absent

For each JP2/JP3 setting below, run
`v2_selftest.main(signature=False, loopback=True, window=20)`. In the 20 s window, read J3 hdr 1
and hdr 3. The firmware is **releasing** the bus during the window, so this is the worst case.

| # | JP2 (CONFIG_2) / JP3 (CONFIG_3) | Expected | Pass |
|---|---|---|---|
| 7.1a | open / open (= Mallow, floating) | report A/B/C **PASS**, loopback 0/5 pairs conduct; J3 hdr 1 and 3 **< 0.05 V** in the window | [ ] |
| 7.1b | 1V8 / 1V8 (10 k → 1.8 V) | same | [ ] |
| 7.1c | 3V3 / 3V3 (10 k → 3.3 V) | same | [ ] |
| 7.1d | GND / open (one pin shorted) | same: one grounded pin opens nothing | [ ] |
| 7.1e | open / GND | same | [ ] |

Run §8.2 (signature grounded) once before trusting 7.1. The "0/5 pairs conduct" result only
means "off" after the same jumpers have been seen conducting.

### 7.2 EXP leakage, card powered, bus off (G8: ≤ 2 µA at 0–3.6 V)

Setup:
- Remove the J3 loopback jumpers and the 100 kΩ indicators.
- JP2/JP3 **open**. Run `main(signature=False, window=600)`: the firmware releases the bus, and
  the signature keeps it off.
- DMM in **µA** in series between the source and the J3 pin.
- Sources: GND (J3 even pin), `+1V8_REF` (J5 hdr 5), `+3V3` (J5 hdr 1).

| # | Action | Expected | Pass | Covers |
|---|---|---|---|---|
| 7.2a | Board #1: each of the 12 EXP pins (J3 hdr 1, 3 … 23) at **0 V, 1.8 V, 3.3 V** (36 readings) | **\|I\| ≤ 2 µA** each (TMUX1511 off leakage is nA-level; record the worst) | [ ] | S-v2-1 |
| 7.2b | Repeat at 3.3 V only with JP2/JP3 = 1V8, then 3V3 | ≤ 2 µA | [ ] | S-v2-1 |

Shortcut for boards #2+: tie all 12 J3 signal pins together with a female header and a bus wire,
then measure once per source voltage. Pass: total ≤ 2 µA. That bounds every single pin as long as
the off-state leakages flow the same way, which they do in practice. If the total is > 2 µA, measure pin by pin.

### 7.3 Card unpowered (S-v2-1 "also unpowered", G9 no back-feed)

Setup: **JP1 OFF** (card unpowered), carrier on USB (sources alive), JP2/JP3 = 3V3, JP5 open.

| # | Action | Expected | Pass | Covers |
|---|---|---|---|---|
| 7.3a | Each EXP pin at 0 / 1.8 / 3.3 V (or the 12-pin shortcut) | **≤ 2 µA** | [ ] | S-v2-1 |
| 7.3b | Card rail J3 pin 2 with everything applied | **< 0.3 V** (record) | [ ] | G9 |
| 7.3c | D5 (LED_1#) | off: Q2a has no drive, no path | [ ] | G9 |
| 7.3d | J4 hdr 17 (WAKE#) | ≈ 3.3 V (carrier 10 k): no pull-down from an unpowered card | [ ] | G9 |
| 7.3e | µA meter J5 hdr 1 (3.3 V) → J4 hdr 19 (W_DISABLE2#); then from J5 hdr 5 (1.8 V) | **≈ 33 µA at 3.3 V, ≈ 18 µA at 1.8 V**: the RC1 R29 100 kΩ pull-up feeds the card rail. Record it, and record the rail on J3 pin 2 while applied (expect < 0.3 V) | [ ] | G9 (info) |
| 7.3f | µA meter J5 hdr 1 → J4 hdr 11 (CONFIG_2), JP2 open | **≈ 3.3 µA** (R22 1 MΩ) | [ ] | info |

## 8. With the dev carrier signature: release, hold, EEPROM, loopback (S-v2-2)

Setup: JP1 = REG, **JP2/JP3 = GND**, bus indicator on J3 hdr 1.

### 8.1 Hold-off is hardware

| # | Action | Expected | Pass | Covers |
|---|---|---|---|---|
| 8.1a | Power up, MicroPython idle (same as 6.2) | J3 hdr 1 **< 0.05 V**; EXP_OE at C13 **< 0.1 V** (optional probe) | [ ] | RC1 |
| 8.1b | REPL: `import v2_selftest; v2_selftest.bus_on()` | J3 hdr 1 **3.0–3.3 V**; EXP_OE ≈ 3.3 V | [ ] | S-v2-2 |
| 8.1c | `v2_selftest.bus_off()` | J3 hdr 1 **< 0.05 V** | [ ] | S-v2-2 |
| 8.1d | Scope on J3 hdr 1: `bus_on()`, then `bus_off()` | turns on **1.5–5.1 ms** after release (R26/C13 RC; carrier-interface §4.3.1); turns off in **< 0.1 ms** (contract: ~20 µs) | [ ] | RC1 |

### 8.2 Loopback, every EXP line both ways

Jumpers on J3: **5↔7** (EXP_2–3), **9↔11** (EXP_4–5), **13↔15** (EXP_6–7), **17↔19**
(EXP_8–9), **21↔23** (EXP_10–11). For EXP_0/1, choose one:
- **(a) EEPROM path (§8.3):** JP7/JP8 bridged on the reworked carrier, no 1↔3 jumper;
- **(b) jumper 1↔3** (EXP_0–EXP_1), EEPROM disconnected (JP7/JP8 open).

Run (b) for the SCL direction even if (a) is available: an EEPROM never drives SCL.

| # | Action | Expected | Pass | Covers |
|---|---|---|---|---|
| 8.2a | (b): `main(signature=True, loopback=True, loop01=True)` | A **PASS** (held: nothing conducts), B **PASS** (released: 5/5 pairs + EXP_0/1 conduct), `loopback EXP_2..11` **PASS** (10 lines, both directions, no cross-shorts), `loopback EXP_0/1` **PASS**, C **PASS** | [ ] | S-v2-2 |
| 8.2b | Any FAIL: the line name points to the RN / TMUX channel (pinmap §6.2) | — | | |

### 8.3 ID EEPROM (needs the reworked dev carrier: U4 + C11 fitted, JP7/JP8 bridged)

| # | Action | Expected | Pass | Covers |
|---|---|---|---|---|
| 8.3a | Blank part: `main(signature=True, loopback=True, program=True)` | `EEPROM program` **PASS** (written + verified) | [ ] | S-v2-2 |
| 8.3b | `main(signature=True, loopback=True)` | A **PASS** (no ACK while held), B **PASS** (ACK at 0x50), header printed: magic `M2CI`, format 1, vendor 0xffff, rev 'A', CRC stored = calc, `EEPROM header` **PASS**, C **PASS** (ACK gone) | [ ] | S-v2-2, contract §4.3 |
| 8.3c | Optional: corrupt one byte (REPL `writeto_mem`), rerun | `EEPROM header` FAIL, "carrier 'unknown'" (firmware rule) | [ ] | contract §4.3 |

### 8.4 Partial signature with the firmware releasing

Repeat 7.1d/7.1e here if not done: a single grounded CONFIG pin must keep the bus off.

### 8.5 Resets keep the bus off (review expansion-5; pinmap §6.3 "to be confirmed at bring-up")

Setup: indicator on J3 hdr 1. Scope CH1 on J3 hdr 1, CH2 on **J3 hdr 9 (EXP_4 = IO18**, which has
the 60 µs power-up high glitch) with a 100 kΩ to GND. Before each reset, release the bus with
`v2_selftest.bus_on()` and check that hdr 1 reads ≈ 3.15 V.

| # | Reset | Expected | Pass |
|---|---|---|---|
| 8.5a | Press **SW1 RESET** (PERST# → EN) | hdr 1 falls to 0 V **at reset** and stays < 0.05 V through boot; hdr 9 shows **no pulse > 0.5 V** | [ ] |
| 8.5b | REPL `import machine; machine.reset()` | same | [ ] |
| 8.5c | REPL `from machine import WDT; WDT(timeout=2000)`, then leave it idle | reset after ~2 s; same | [ ] |
| 8.5d | REPL Ctrl-D (MicroPython **soft** reset: no chip reset) | **record**. A soft reset may leave IO38 low and the bus on; then any firmware must drive IO38 high as its first init step | [ ] |
| 8.5e | Power cycle (JP1 off/on) | hdr 1 and hdr 9 stay < 0.05 V from power-up through boot | [ ] |

Record 8.5 in `hardware/blocks/edge_expansion/LESSONS.md`.

## 9. Host sidebands on the dev carrier (G9, mcu_io-7)

Setup: JP1 = REG, JP6 fitted (D6 = WAKE). Use the interactive REPL for y/n answers:
`v2_selftest.main(interactive=True, wifi=False)`.

### 9.1 Outputs: LED_1# (pin 10) and WAKE_ON_WWAN# (pin 23)

| # | Action | Expected | Pass | Covers |
|---|---|---|---|---|
| 9.1a | Self-test LED_1# pattern | **D5** blinks **5× at 1 Hz** (slow, even) | [ ] | G9 |
| 9.1b | Self-test WAKE# pattern | **D6** shows **3 short + 1 long** pulse. If D5/D6 show the other's pattern, Q2 is rotated 180° (polarity checklist) | [ ] | G9 |
| 9.1c | Scope J4 hdr 15 and hdr 17 during the patterns | low level **≤ 0.1 V**; hdr 17 high ≈ 3.3 V (10 k) | [ ] | G9 |
| 9.1d | Card in reset (hold SW1) | D5 off, hdr 17 ≈ 3.3 V (gate pull-downs R27/R28 keep Q2 off) | [ ] | G9 |

### 9.2 Input: W_DISABLE2# (pin 26) → IO40, inverted

| # | Action | Expected | Pass | Covers |
|---|---|---|---|---|
| 9.2a | JP5 open (pin 26 at the card 100 kΩ pull-up) | IO40 = **0** (radio allowed) | [ ] | G9 |
| 9.2b | JP5 fitted (pin 26 to GND) | IO40 = **1** (radio kill). Self-test `radio kill honoured` (run with `wifi=True`) | [ ] | G9, contract §4.4 |
| 9.2c | JP5 open. Wire J4 hdr 19 → **J5 hdr 5 (+1V8_REF)**: 1.8 V push-pull host | IO40 = **0**; hdr 19 reads 1.80–1.85 V (15 µA from R29 into the 1V8 divider) | [ ] | mcu_io-7 |
| 9.2d | Wire J4 hdr 19 → J5 hdr 1 (+3V3) | IO40 = 0 | [ ] | G9 |
| 9.2e | **1.2 V host** (HSIC level), optional: bench supply 1.20 V, limit 10 mA, through 1 kΩ to J4 hdr 19 (JP1 = REG, bench otherwise unused) | IO40 = **0** expected (Q3a VGS(th) ≤ 1.0 V); record the hdr 19 voltage. A 1 here is a finding, not a stop | [ ] | mcu_io-7 |

Read IO40 in the REPL with `from machine import Pin; Pin(40, Pin.IN).value()`.

### 9.3 Outputs at a 1.8 V pull-up: not executable on the dev carrier

The dev carrier pulls pin 10 (D5 + 1 kΩ) and pin 23 (10 kΩ) to its own +3V3 on-board. A 1.8 V
pull-up test of LED_1#/WAKE# needs a host whose lines idle at 1.8 V (Mallow X16, if its level is
1.8 V: check the Mallow datasheet Table 22) or a rework of the dev carrier's own pull-ups (its R20 / R21, not the card's). The NMOS cell
pulls low the same way at any pull-up voltage. Accepting this by analysis plus 9.1c is an owner
decision.

## 10. Hosts listed in S-v2-1

Run on each host: enumeration, `main(signature=False, wifi=True)` (no fixture, so A/B/C SKIP),
and the bus proxy listed for that host.

- **EXP_OE proxy:** card bottom accessible. Run `main(signature=False, window=60)` and probe C13
  pad 1 in the window. Pass: **< 0.1 V** (Q1 on: host signature absent) while the firmware
  releases.

### 10.1 Mallow (primary host)

CONFIG_2/3 are NC on Mallow, so the card's 1 MΩ pull-ups hold them high and the bus stays off.
Mallow wiring (`docs/pinmap.md` §1):
- EXP_0..3 (30/32/34/36) → Mallow UIM lines;
- EXP_4 (40) → X16 pin 24;
- EXP_5..11 (59–65) are NC on Mallow;
- LED_1# → X16.15, WAKE# → X16.13, W_DISABLE2# → X16.14.

| # | Action | Expected | Pass | Covers |
|---|---|---|---|---|
| 10.1a | Insert, boot Torizon, `dmesg` | Espressif CDC device (303a:4001 with MicroPython) | [ ] | S-v2-4 (§10.1) |
| 10.1b | Self-test via the host's `mpremote` | all non-SKIP items PASS | [ ] | S-v2-4 |
| 10.1c | Leakage at X16 pin 24 (EXP_4), card running with `window=600`: µA meter to Mallow GND and to Mallow 3.3 V; 1.8 V from an external source with a shared GND | **≤ 2 µA** | [ ] | S-v2-1 |
| 10.1d | Same at the Mallow SIM-holder contacts for UIM_RESET/CLK/DATA/PWR, if fitted and reachable | ≤ 2 µA | [ ] | S-v2-1 |
| 10.1e | EXP_OE proxy, if the card bottom is reachable | < 0.1 V | [ ] | S-v2-1 |
| 10.1f | Sidebands: jumper X16.15 / X16.13 / X16.14 to free SoM GPIOs. **Check the X16 level in the Mallow datasheet first.** Read pins 10/23 with `gpioget` during the patterns; drive pin 26 with `gpioset …=0`, then release | 10/23 follow the patterns; IO40 = 1 while pin 26 is low, 0 when released | [ ] | G9 |
| 10.1g | Same with the card unpowered (slot off), if Mallow can switch the slot | no back-feed: J3 pin 2 < 0.3 V | [ ] | G9 |

EXP_5..11 have no Mallow connection, so nothing can leak into Mallow there. Their leakage is
covered by 7.2 on the dev carrier.

### 10.2 Laptop WWAN slot: proxy only

**Not executable as written.**
- The card is 3.1 mm tall at the module and does not fit an enclosed WWAN bay (R11). The test
  needs a laptop run with the bottom cover off and the card supported.
- The EXP pins sit inside the socket on the laptop board, so they can't be measured.
- The owner may not have a suitable laptop.

| # | Action | Expected | Pass | Covers |
|---|---|---|---|---|
| 10.2a | Boot with the card in the slot | BIOS accepts the card (state 6; R-v2-3 whitelist risk); the OS sees the CDC device if the slot routes USB 2.0 | [ ] | R-v2-3 |
| 10.2b | `main(signature=False)` | no FAIL. The laptop's sideband pull-ups make 10/23/26 behave per 9.x | [ ] | G9 |
| 10.2c | EXP_OE proxy (card bottom faces the mainboard: usually not reachable) | < 0.1 V | [ ] | S-v2-1 proxy |
| 10.2d | Any host misbehaviour (fans, rfkill, refusing to boot) | none | [ ] | — |

### 10.3 M.2 Key-B → USB adapter: proxy only

**EXP pins are not exposed**, so S-v2-1 leakage can't be measured here. The owner may not have
an adapter.

| # | Action | Expected | Pass | Covers |
|---|---|---|---|---|
| 10.3a | Adapter output voltage at the card (J3 pin 2 and, if reachable, the VCC fingers) | 3.135–3.465 V. Above 3.44 V the card may OVLO-trip: record it as a real-world S-v2-3 case | [ ] | S-v2-3 |
| 10.3b | Enumeration, self-test `signature=False` | PASS | [ ] | S-v2-4 |
| 10.3c | CONFIG_2 / CONFIG_3 at R22 / R23 pad 2 | record. Any value > 1.0 V on either pin keeps the bus off | [ ] | S-v2-1 proxy |
| 10.3d | EXP_OE proxy (adapter boards are open, so the card bottom is usually reachable) | **< 0.1 V** in the release window | [ ] | S-v2-1 proxy |

### 10.4 RPi5 + Waveshare Key-B HAT (best effort, ADR 0004)

The HAT has no 2242 standoff (R4): support the card by hand or with a spacer. Do 10.3b–10.3d.
Results are informative only.

## 11. v1 regression (S-v2-4 = SPEC §10 items 1–6, plus Rev B fixes)

| # | v1 criterion | Action | Expected | Pass |
|---|---|---|---|---|
| 11.1 | §10.1 | Mallow `dmesg` (10.1a) | Espressif CDC device | [ ] |
| 11.2 | §10.2 | `esptool` flashes over that port (§6, on Mallow too) | write + verify OK | [ ] |
| 11.3 | §10.3 | Brick: `head -c 4096 /dev/urandom > junk.bin; esptool --chip esp32s3 -p <port> write_flash 0x0 junk.bin`. Recover on Mallow with host GPIOs only: X16.19 → SoM GPIO (BOOT) `gpioset …=0`, pulse PERST# (`gpioset $(gpiofind SODIMM_244)=0`, ≥ 5 ms, then release to input), release BOOT to input, then `esptool --before no_reset write_flash` MicroPython | card recovered, REPL back (ADR 0002 flow; DT overlay on iMX8M*) | [ ] |
| 11.3b | Rev B pin-8 leg | On the dev carrier: recovery with SW2 + SW1, once with JP4 fitted and once removed (dev-carrier §5) | download mode both ways; pin 8 carries BOOT | [ ] |
| 11.4 | §10.4 | Status LED: self-test D4 blink (lens out of the card edge, visible in the slot). Qwiic sensor on J3: self-test `Qwiic I2C` lists its address (or `machine.SoftI2C(scl=Pin(9), sda=Pin(8)).scan()`) | D4 visible; sensor found. **Needs a Qwiic sensor** | [ ] |
| 11.5 | §10.5 | Self-test `WiFi scan` PASS, then connect in the REPL: `network.WLAN(network.STA_IF).connect("<ssid>", "<password>")` typed by hand (never stored in the repo) | `isconnected()` True | [ ] |
| 11.6 | §10.6 | RPi5 + HAT: enumeration (10.4) | best effort | [ ] |
| 11.7 | Rev B R12 | Dev carrier REG, WiFi scan in a loop for 30 s (`for _ in range(20): w.scan()`); DMM min/max on J3 pin 2 | card rail min **≥ 3.0 V** (ESP32-S3 VDD min); input J5 hdr 3 min ≥ 3.135 V | [ ] |
| 11.8 | Rev B J3/J4 | Self-test `J3/J4 pull sweep` (nothing plugged) | PASS | [ ] |
| 11.9 | Rev B D3/D4 | Card in the slot, self-test running | both LEDs visible from the card edge; green steady, red blinks | [ ] |

## 12. Boards #2+ (short path)

- Steps 1 and 2 in full.
- §3: steps 3.4–3.5 only.
- §4: 4.1 without stepping to the limit. Ramp to 3.40 V and confirm the card is still on (no
  early trip). The full window is checked on board #1.
- §5, §6.
- §8.2a (loopback + EXP_0/1). §8.3b if a programmed EEPROM carrier is at hand.
- §7.2 with the 12-pin shortcut at 3.3 V.
- §9.1a/b, 9.2a/b.
- §11.8.

## 13. Results

Card serial = base MAC: keep it on the local sheet only. In the repo, use board numbers.

| Board | 1 visual | 2 Ω | 3 ramp ms / inrush mA / idle mA | 4 V_trip / V_release / 5 V peak | 5–6 USB / flash | 7 max leak µA (pwr / unpwr) | 8 hold / loop / EEPROM / resets | 9 sidebands (1.8 V / 1.2 V) | 10 hosts | 11 v1 | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| #1 | | | | | | | | | | | |
| #2 | | | | | | | | | | | |
| #3 | | | | | | | | | | | |
| #4 | | | | | | | | | | | |
| #5 | | | | | | | | | | | |

## 14. What a failure means

| Symptom | Likely cause | First action |
|---|---|---|
| A or C FAIL (bus on while IO38 high) | Q3 rotated, R35 missing, IO38 not reaching Q3b | 1.3; probe IO38 (should be 3.3 V) and EXP_OE |
| B FAIL with signature grounded | Q1 rotated or CONFIG_2/3 not at 0 V; TMUX SEL not at EXP_OE | measure R22/R23 pad 2 and C13; 1.1 |
| B ON with signature absent | Q1 / R22–R25 fault, or a host-side load pulling CONFIG low (review expansion-1) | measure CONFIG_2/3 at R22/R23 |
| One loopback pair fails | RN or TMUX channel solder joint | loupe on that channel (pinmap §6.2) |
| Cross-short reported | bridge between adjacent fingers, RN pads or TMUX pins | 2.9; loupe |
| IO40 inverted or stuck | Q3 rotated (Q3a/Q3b swapped), R30 missing | 1.3; 2.6 |
| D5/D6 patterns swapped | Q2 rotated 180° | 1.3 |
| No trip by 3.60 V, or a trip outside the window | R31/R32 wrong value or tolerance; C16 missing | measure the OVLO tap: trip at 1.183–1.223 V |
| Ramp too fast / bench in CC at power-up | C15 missing or wrong value | measure U6 pin 7 to GND |
| Octal-PSRAM boot loop | wrong MicroPython variant | reflash the default ESP32_GENERIC_S3 |
