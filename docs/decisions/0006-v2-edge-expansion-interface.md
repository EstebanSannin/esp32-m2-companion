# ADR 0006 — v2 edge interface: hardware-gated expansion bus, CONFIG state 6, host-facing pins

Date: 2026-10-07 · Status: **accepted** (owner, v2 brainstorm 2026-10-06/07)
except the items marked *proposed* (to confirm at v2 GATE 1)

## Context

v1/Rev B leaves ~16 ESP32-S3 GPIOs unused. The owner wants as many as
possible on the M.2 edge, so that custom carriers (relay, sensor, dev boards)
can use the card as their brain. That must not break **any** standard
M.2 Key-B host: laptop WWAN slots, B+M SSD slots, Mallow, adapters.

Research (`v2/research/m2_pins_research.md`, M.2 Rev 1.0 + Rev 3.0 via
congatec AN43, five modem datasheets, Dell / Waveshare / Osmocom /
Geniatech host schematics) showed three things:
- Almost every non-power pin may be driven by *some* host.
- Levels are mixed: 1.2, 1.8 and 3.3 V.
- Host CONFIG pull-ups may be 1.8 V.

## Decision

1. **CONFIG state 6**: the card grounds CONFIG_0 (21) and CONFIG_1 (69) and
   leaves 75 and 1 NC. That reads as "WWAN, USB3/PCIe, port config 2", the
   pattern used by Telit FN990 and Sierra EM7455.
   - It replaces v1's state 15 ("no module present").
2. **Carrier signature = pins 75 + 1 both at 0 V.**
   - Detected by **two low-Vth NMOS in wired-NOR** (Toshiba SSM6N56FE,
     Vth 0.4–1.0 V), gates behind 100 kΩ, 1 MΩ card pull-ups, RC on the
     enable.
   - A host pull-up at 1.8 or 3.3 V, or a floating pin, keeps the bus off.
   - Insulated gates mean no back-feed into an unpowered card.
   - Logic gates were rejected: they can't separate a 1.8 V pull-up from a
     low.
3. **Expansion bus: 12 lines** on M.2 pins 30, 32, 34, 36, 40, 59–65.
   - Through **3× TI TMUX1511** (SEL active-high, internal pull-down,
     powered-off protection ±2 µA at 0–3.6 V).
   - ~220 Ω series resistors on the ESP side.
   - Named EXP_0..11 in ascending M.2 pin order (layout-independent).
   - Pins 56/58 are excluded: Dell Latitude drives 58 and senses 56.
   - 38/66/68 are excluded: host-driven or grounded.
   - Defence in depth: hardware gate → series R → firmware ID-EEPROM check.
4. **Host-facing pins**, always active, with standard meanings:
   - LED_1# (10) and WAKE_ON_WWAN# (23) as open-drain NMOS outputs.
   - W_DISABLE2# (26) as an NMOS-gate input (radio kill).
   - GPIO_0..8 pins (20–28, 40–48) are **not** used always-on, because hosts
     may wire codecs, GNSS or SIM2 there. Pin 40 is used only behind the
     switch.
5. **Carrier design rules and full pin contract:** `docs/carrier-interface.md`.
   That document is the single reference for carrier and accessory design.
6. *Proposed:*
   - the EXP_n → ESP32-S3 GPIO table, including ADC/I²C/UART capabilities;
   - the ID EEPROM (24C02 @ 0x50 on EXP_0/EXP_1) and its content format.

## Consequences

- **Parts** (+$2.1/board @100; all Extended, since JLC Basic has no
  switch/logic parts): 3× TMUX1511 RSV, 2–3× SSM6N56FE, ~25 passives.
  Placement is on the bottom side under the module.
- **Routing:** needs 2242 with **6 layers** (ADR 0008). The §12 probe
  routed 31/47 new nets DRC-clean before re-placement.
- **Firmware:**
  - expansion bus enable readback;
  - ID EEPROM handling;
  - W_DISABLE2# → rfkill;
  - WAKE_ON_WWAN# IRQ protocol (TBD).
- **Validation:** host-safety fixture. The dev carrier
  (`v2/carrier/DEV_CARRIER_PROMPT.md`) has signature jumpers for GND /
  open / 1.8 V / 3.3 V, plus measurements on Mallow, a laptop WWAN slot and
  an adapter.
- **Supersedes:** SPEC §3's "no level shifting" scope and §6.6's "IO only on
  card connectors". A SPEC amendment is needed (A3).

## Amendment (RC1, 2026-10-28, owner): bus ON = carrier AND firmware

Owner decision after the release-candidate review ("go with your
recommendations, approve the change list"); evidence in
`docs/review/v2_rc1_design_review.md`. The decisions above stay; this
section changes Decision 2/3 and the firmware consequences.

**Why** (review contract_test-1, expansion-2, expansion-5, contract_test-6):
- EXP_OE (R26 10 kΩ / C13 1 µF, τ 10 ms) crossed the TMUX1511 VIH 1.2 V at
  ~4.6 ms, while EN (R1 10 kΩ / C5 1 µF) releases CHIP_PU at ~13.9 ms. On a
  carrier the switches conducted for ~9 ms of ESP32 reset plus ROM boot, so
  the power-up glitches of ESP32-S3 DS v2.2 Table 2-2 (60 µs lows on
  GPIO1–17, a low-then-high glitch on GPIO18 = EXP_4) reached the carrier.
  The contract promise "EXP_2..11 high-Z until a valid EEPROM is read" was
  false in hardware.
- EXP_OE did not depend on EN, so the bus also stayed connected through
  every later ESP32 reset (PERST#, button, WDT, brown-out, software reset).
- IO38 was wired straight onto EXP_OE with no series resistor: a firmware
  push-pull high fought the conducting Q1 (~40 mA) on every normal host.

**Change:**
- The spare half **Q3b** (SSM6N56FE in `host_sideband`) now pulls EXP_OE
  low: drain = EXP_OE, source = GND, gate = **IO38** with **R35 100 kΩ**
  pull-up to +3V3. IO38 is no longer connected to EXP_OE.
- **Bus ON = carrier signature (Q1 off) AND firmware consent (IO38 LOW).**
  Either condition alone keeps all 12 switches off. Firmware still cannot
  open the bus on a host without the signature (Q1 wins).
- IO38 is IE-only with no pull at reset (DS v2.2 Table 2-1) and has no
  power-up glitch (Table 2-2 lists GPIO1–18 only), so R35 holds Q3b on
  through power-up, reset and ROM boot. During the supply ramp Q3b conducts
  as soon as +3V3 exceeds its Vth (0.4–1.0 V), before EXP_OE could reach
  1.2 V.
- IO38 may now be driven push-pull either way (it only drives a gate).
- The EXP_OE readback is lost. Carrier presence = the ID-EEPROM ACK at 0x50
  on EXP_0/1 after release.

**Timing:**
- Release: firmware drives IO38 low → Q3b off in µs → EXP_OE rises with
  τ = 10 ms and crosses VIH 1.2 V after ~4.6 ms (≤ 5.1 ms with worst SEL
  leakage). Firmware waits ≥ 50 ms (review expansion-6) before the EEPROM
  probe.
- Hold-off: firmware drives IO38 high, or any chip reset puts IO38 back to
  input → R35 charges the Q3b gate (100 kΩ × ~55 pF Ciss ≈ 6 µs) → Q3b
  discharges C13 in µs. All switches off within ~10–20 µs.
- Software/WDT resets: whether a core/system reset returns IO38 to its
  reset state is not stated in the datasheet. Firmware drives IO38 high as
  its first init step either way. Confirm at bring-up by scoping EXP_4 and
  EXP_2 against PERST#/EN (SPEC S-v2-2).

**Firmware rule (normative for firmware ≥ first v2 release):** keep IO38
high (bus held off) through init; release it only to probe the ID EEPROM;
if no ACK or the CRC fails, drive IO38 high again. This also limits the
host pull-down case of review expansion-1 (a host load < ~500 kΩ to GND on
CONFIG_2/3 can turn Q1 off) to the probe window.

**Decision 4 correction (review mcu_io-3):** Decision 4 says pins 20–28 and
40–48 are not used always-on. The M.2 GPIO_0..8 pins are 40/42/44/46/48
and 20/22/24/28; pins 23 (WAKE_ON_WWAN#) and 26 (W_DISABLE2#) in that span
are standard sidebands used on purpose. **Pin 20 (GPIO_5 / AUDIO_0,
1.8 V) is a deliberate, inherited exception:** it carries the BOOT leg
(BAT54A D2 to IO0, ADR 0002, unchanged since v1). A host that drives pin 20
push-pull high at 1.8 V leaves IO0 at ~2.0 V, below VIH 2.475 V (undefined
strap); a PCM clock there can cause a random download boot. Spec-following
hosts leave pin 20 alone in port config 2 (CONFIG state 6), where it is
RFU. Tracked as risk R-v2-11 (`docs/risks.md`); mitigation on an affected
host: lift D2 pin 1.
