# Carrier interface — ESP32-S3 M.2 companion card

**The contract between the companion card and any carrier or accessory board.**
Single source of truth for carrier design sessions: import it from a carrier
repo's `CLAUDE.md` with
`@<workspace>/esp32-m2-companion-v2/docs/carrier-interface.md`
(after v2 merges: `…/esp32-m2-companion/docs/carrier-interface.md`).
This file is self-contained: a carrier needs nothing else to design against it.

Version: **v2.0 Rev A, RC2 (release candidate 2, 2026-10-28)**. GATE V1 pinmap
2026-10-07, GATE V3 layout 2026-10-10, RC1 design review and RC1 delta
review 2026-10-28 (changes in §7); fab not ordered yet. Decisions: ADR 0006 (edge interface),
ADR 0007 (input OVP), ADR 0008 (form factor). Background, research and
rejected alternatives: `v2/edge-expansion-brainstorm.md`,
`v2/research/m2_pins_research.md`, `docs/review/v2_rc1_design_review.md`,
`docs/review/v2_rc1_delta_review.md`.

Status legend: **fixed** = owner-approved; *proposed* = not yet approved, may
change. Carriers may rely on **fixed** items only. **[FW]** = firmware
behaviour, not a hardware guarantee: no released firmware implements it yet;
the first firmware release that does will be named here.

---

## 1. Card revisions a carrier must handle

| Card | Identify by | Edge features |
|---|---|---|
| v1.0 / **v1.0 Rev B** (fabricated) | CONFIG_0..3 all NC → host reads `1111` (state 15) | USB 2.0, power, PERST#→EN, BOOT on pin 20 (+ pin 8 on Rev B). **No expansion bus, no OVP, no host-facing pins.** |
| **v2.0 Rev A** (in design) | CONFIG_0 (21) + CONFIG_1 (69) grounded → state 6 | everything above + 12-line expansion bus + LED_1#/WAKE_ON_WWAN#/W_DISABLE2# + input OVP |

A carrier designed to this document works with both. With a Rev-B card,
the EXP pins and pins 10/23/26 are simply unconnected on the card.

State 6 is also the CONFIG pattern of some WWAN modems (e.g. Telit FN990), so
a carrier **cannot** tell a v2 card from a modem by CONFIG_0/1 (see §5 rule 4).

## 2. Mechanical

- **Fixed:**
  - M.2 **Key B** socket.
  - Card **22 mm wide, 0.8 mm**, length **2242** for v1/v2.
  - Possible future "plus" cards at 2252 / 2260: put standoff positions for
    2242 / 2252 / 2260 on carriers.
- **Fixed:** the card has components on **both sides**.
  - Top: WROOM module (antenna at the far end from the fingers) + 2 JST SH
    connectors + one 0402 resistor (R33, eFuse EN pull-up, between the
    module and J4; on the top side since RC1).
  - Bottom: passives, SOT-23/SOT-23-6, side-view LEDs, test points; v2 adds
    UQFN/VQFN (TMUX1511 ×3, eFuse), SOT-563 ×3 and 4×0402 resistor arrays.
  - **Bottom-side height: design carriers for ≤ 1.6 mm** including solder
    (CG1). Tallest bottom parts by datasheet: 0805 22 µF capacitors
    (1.25 ± 0.2 mm) and the SOT-23-6 (≈ 1.45 mm max); Rev B measured 1.55 mm
    in its 3D model. This is above the M.2 Rev 1.0 double-sided 1.5 mm
    figure; sockets with at least the card-bottom clearance of the Amphenol
    MDT420B01001 (tested with Rev B) fit.
  - Bottom-side parts start **5.2 mm** from the finger edge (M.2 bottom-side
    component zone); three parts (U1, C14, C16) sit exactly at that limit.
  - Choose the socket stack height so the bottom parts clear the carrier,
    and keep carrier components out of the card's footprint.
  - Measure heights from `docs/3d/esp32_m2_companion.step` (on branch `v2`:
    the v2.0 Rev A layout; on `rev-b`: Rev B).
- **Fixed:** antenna keep-out. No metal (copper pour, shields, tall
  parts) under or over the **far end of the card**. The WROOM PCB antenna
  keep-out spans **4.4–10.6 mm from the card's far edge** (the mounting-screw
  end) = **31.4–37.6 mm from the finger edge** (card-stop datum) on a 2242,
  all layers (Espressif HDG; module position identical on Rev B and v2.0
  Rev A). Carriers should keep the whole last ~11 mm of the card
  (31–42 mm from the finger edge) clear.
  - *Proposed* (CG2): plus cards (2252/2260) are not defined yet; until they
    are, keep copper out from 31 mm to the far end of the longest card the
    carrier accepts.
- **Fixed** (CG3): the mounting notch is a Ø3.5 mm semicircle routed in the
  outline: not plated, no copper, no net. Standoffs need no net; screw
  **M2 × 0.4** (M.2 spec), on the socket centreline at **42 mm** from the
  card stop for 2242 (60 mm for 2260 per M.2 Rev 1.0; 52 mm *proposed*,
  extrapolated by the same rule).
- Edge fingers are ENIG hard gold and **not bevelled** (hand-chamfered).

## 3. Power

- **Fixed:** the carrier supplies **3.3 V ±5 % (3.135–3.465 V)** at the card
  fingers, under load, on pins 2, 4, 70, 72, 74. Connect all five; the card
  draws its current through 70/72/74 (2/4 reach the eFuse through a thin
  trace and carry almost nothing).
- **Fixed: current.**
  - Card load: ~0.5 A peak on WiFi TX bursts.
  - v2 eFuse (TPS259470A) current limit **0.85 / 1.01 / 1.15 A**
    (min/typ/max). The card plus anything on its J3 Qwiic +3V3 output must
    stay below 0.85 A. **Fixed:** J3 (Qwiic) +3V3 output budget
    **≤ 150 mA**.
  - **Design the carrier supply for ≥ 1.2 A** (covers the 1.15 A
    current-limited start after an overvoltage trip, below, and faults).
  - Drop from fingers to module at 0.5 A is ~65–70 mV including socket
    contacts, so 3.135 V at the fingers keeps the module ≥ 3.0 V.
- **Fixed: input capacitance and inrush (CG4).**
  - Directly on the slot rail: **100 nF** only.
  - Behind the eFuse: **~65 µF** nominal, charged under dV/dt control:
    slew ~0.7 V/ms typ (≤ 1.3 V/ms), **inrush ≤ ~90 mA**; the card rail goes
    0 → 3.3 V ~5 ms typ, **~2–16 ms** (incl. the eFuse turn-on delay) after
    the slot rail. Hosts that soft-start the slot at 200 mA (allowed by M.2)
    are fine.
  - Exception: a restart after an overvoltage trip skips dV/dt and starts
    current-limited (up to 1.15 A for < 0.5 ms).
- **Fixed:** **never more than 3.6 V.**
  - Rev-B cards have no protection: the ESP32-S3 absolute maximum is 3.6 V.
  - v2 cards: overvoltage trip at **3.44–3.57 V** (filtered, τ ≈ 3.4 µs:
    MHz ringing is attenuated ~20×). A hard step trips after a few µs plus
    the eFuse's 1.2 µs; the worst case is a ramp of tens of µs, which the
    worst-case model puts at ~3.56–3.6 V typ, up to ~3.65 V on the card rail
    for µs (ADR 0007 RC2; the max trip alone is 3.561 V).
    The card switches off without damage up to ~18 V (ADR 0007). Even so,
    the 3.6 V limit applies to every carrier (test-fixture exception: §5
    rule 8).
  - **A tripped v2 card stays off** until the input falls below
    **3.13–3.25 V**. On a nominal 3.3 V supply that does not happen by
    itself: the slot supply must be switched off and on. It is not
    auto-recovering.
  - The card cannot report a trip (eFuse fault output not connected): it
    disappears from USB and the EXP bus goes off. Carriers that may see
    overvoltage events should be able to power-cycle the slot.
  - No eFuse second source is approved: the same-footprint latch-off variants
    change this fault behaviour.
- GND on all 11 GND fingers (3, 5, 11, 27, 33, 39, 45, 51, 57, 71, 73).

## 4. Edge pins used by the card

Card point of view. `_n` = active low (`#` in datasheets).

### 4.1 Always present (v1, Rev B, v2)

| Pin | Net | Direction / level | Carrier provides |
|---:|---|---|---|
| 7 | `USBH3_D_P` (USB D+) | USB 2.0 FS | USB host or USB connector D+ |
| 9 | `USBH3_D_N` (USB D−) | USB 2.0 FS | D− (short, paired; card has its own USBLC6 ESD) |
| 50 | `PERST_n` → card EN (reset) | card input, Schottky-isolated, card pull-up | open-drain/button to GND only. Never drive high |
| 20 | BOOT (`IO0`) | card input, Schottky-isolated, card pull-up | open-drain/button to GND only |
| 8 | BOOT second leg (`W_DISABLE1_n`), **Rev B and v2 only** | same | optional; ground together with 20 |

Recovery (any card): hold BOOT low, pulse PERST# low ≥ 5 ms, release
PERST# → ROM download mode over the same USB → flash → release BOOT.

### 4.2 CONFIG pins and the carrier signature (v2)

| Pin | Name | Card (v2) | Carrier |
|---:|---|---|---|
| 21 | CONFIG_0 | **GND** | may read it (pull-up ≥ 10 k) |
| 69 | CONFIG_1 | **GND** | may read it (pull-up ≥ 10 k) |
| 75 | CONFIG_2 | not NC: 1 MΩ card pull-up to card 3.3 V, then 100 kΩ to a FET gate | **tie to GND** = "I am a companion carrier" |
| 1 | CONFIG_3 | same | **tie to GND** |

- **Fixed:** "tied to GND" = **≤ 0.1 V, or ≤ 10 kΩ to GND**.
- **Fixed:** the v2 expansion bus is on **only when BOTH 75 and 1 are at
  0 V AND the card firmware has released its hold** (§4.3.1).
  - The signature detect is in hardware (two low-Vth NMOS, wired-NOR,
    RC-delayed). Any host pull-up (1.8 V or 3.3 V), or a floating pin, keeps
    the bus off whatever the firmware does.
- **Fixed, limits of the detect:**
  - It reads "pin at 0 V" as "carrier". A host load to GND on **both** pins
    looks like a carrier: below ~65 kΩ always, 65–435 kΩ depending on part
    and temperature. Examples: a pull-up to an unpowered rail, a SoC pad's
    default pull-down, a GPIO driven low. Floating pins stay "no carrier"
    while gate plus board leakage stays below ~1.8 µA (met at 25 °C).
  - In that case the bus turns on once firmware releases the hold; the
    card's 4.7 kΩ I²C pull-ups then reach pins 30/32 (UIM_RESET/UIM_CLK on a
    WWAN host, ~0.2–0.55 mA into a 1.8 V SIM net) and the EEPROM probe clocks
    pin 32, until firmware turns the bus off again (§4.3.3, **[FW]**).
  - The 1 MΩ pull-ups lift a host 1.8 V net slightly (≤ 1.5 µA; 1.8 V →
    1.94 V with a 100 kΩ host pull-up) and pass ≤ 3.3 µA per pin into an
    unpowered card.
- A Rev-B card ignores these pins, so grounding them is harmless.
- A real WWAN modem in our carrier just sees two grounded CONFIG pins,
  which is also harmless.

### 4.3 Expansion bus EXP_0..11 (v2 only, active only on a carrier)

**Fixed: the M.2 pin ↔ EXP name mapping**, numbered by ascending M.2 pin, so
it is independent of layout:

| EXP | M.2 pin | WWAN name (reference) | **Capability (fixed, GATE V1)** | ESP32-S3 GPIO (**fixed for v2.0 Rev A** — routed, GATE V3) |
|---|---:|---|---|---|
| EXP_0 | 30 | UIM_RESET | **I²C SDA** (ID EEPROM bus, 4.7 k pull-up on card) | IO39 |
| EXP_1 | 32 | UIM_CLK | **I²C SCL** (ID EEPROM bus, 4.7 k pull-up on card) | IO41 |
| EXP_2 | 34 | UIM_DATA | digital, **ADC**, touch | IO1 |
| EXP_3 | 36 | UIM_PWR | digital, **ADC**, touch | IO2 |
| EXP_4 | 40 | GPIO_0 | digital | IO18 |
| EXP_5 | 59 | ANTCTL0 | digital, **ADC**, touch | IO4 |
| EXP_6 | 60 | COEX3 | digital, **ADC**, touch | IO5 |
| EXP_7 | 61 | ANTCTL1 | digital, **ADC**, touch | IO6 |
| EXP_8 | 62 | COEX2 | digital, **ADC**, touch | IO7 |
| EXP_9 | 63 | ANTCTL2 | digital | IO15 |
| EXP_10 | 64 | COEX1 | digital | IO16 |
| EXP_11 | 65 | ANTCTL3 | digital | IO17 |

"Digital" = GPIO, UART, SPI, PWM, RMT (ESP32-S3 GPIO matrix routes them to any line). ADC =
ADC1, usable with WiFi on. Since GATE V3 the GPIO column is the routed Rev A copper; a later card
revision may swap GPIOs **within a capability class only**; carriers
design against the capability column, never the GPIO column.

#### 4.3.1 Bus enable and timing (fixed, RC1)

- Bus on = **carrier signature (§4.2) AND firmware release**. Path:
  `EXP_OE` drives the select inputs of the three TMUX1511 switches; it is
  pulled up through 10 kΩ / 1 µF (τ = 10 ms) and pulled low by either the
  signature FETs or the firmware hold FET.
- **Hold:** the hold FET's gate is ESP32 `IO38` with a 100 kΩ pull-up. While
  the ESP32 is powering up, in a chip reset (EN/PERST#, brown-out) or in
  the ROM boot after one, IO38 is an input, the hold is on and all 12 lines are disconnected (high-Z on the edge side).
  The ESP32 power-up GPIO glitches therefore never reach the carrier.
- **Release:** firmware drives IO38 low. If the signature is present, the
  switches conduct **about 1–6.5 ms** later (nominal: select input crosses
  0.45 V at 1.5 ms and 1.2 V at 4.5 ms; the range covers C13 ±10 % / X5R,
  the 3.3 V ±5 % rail and the select-input leakage). The same delay applies
  when the signature appears after the release.
- **Off** (fixed, to be confirmed by measurement at bring-up, SPEC S-v2-2):
  within **~20 µs** of firmware driving IO38 high or back to input, and of
  every **chip reset** that returns IO38 to input: PERST#-driven EN,
  brown-out, RTC watchdog, power loss. Within **~0.3 ms** of either
  signature pin leaving 0 V. Immediately when the card loses power.
- **[FW], to be confirmed (S-v2-2): software and watchdog resets.** On the
  ESP32-S3 `esp_restart()`, MicroPython `machine.reset()`, the panic
  handler and the task/interrupt watchdog reset the CPUs only; GPIO
  outputs most likely keep their state, so IO38 may stay driven LOW and the
  bus stay on through the restart. Firmware therefore drives IO38 high in a
  shutdown handler before any software restart, and again as early as
  possible in boot (2nd-stage bootloader hook or first init step). Until
  bring-up measures it, carriers must not rely on the bus dropping on a
  software or watchdog reset.
- The card does not read `EXP_OE` back: firmware learns that a carrier is
  present only by releasing the hold and finding the ID EEPROM (§4.3.3). A
  carrier without an EEPROM looks the same as no carrier.
- **[FW]** In ESP32 deep sleep the bus stays on only if firmware holds IO38
  low (IO38 is not an RTC GPIO: digital GPIO hold needed).
- **[FW]** In light sleep, firmware either keeps IO38's active configuration
  (no GPIO sleep-select on IO38, or a GPIO hold) or accepts that the bus
  drops during sleep and needs 1–6.5 ms after wake. Either way it fails
  off (R35 holds the bus off if IO38 floats).

#### 4.3.2 EXP electrical spec (fixed, RC1)

| Item | Value |
|---|---|
| Path, card side | ESP32-S3 GPIO → **220 Ω** series (MCU side) → **TMUX1511** passive switch (Ron ≤ 4.5 Ω, 3 GHz bandwidth, C_on ≤ 6 pF) → M.2 pin |
| Card output impedance | ~250 Ω (220 Ω + Ron + ESP32 driver): VOH drops ~0.22 V at 1 mA; short-circuit current ~13 mA |
| Logic levels at the card | ESP32-S3 at 3.3 V: VIH ≥ 0.75 × VDD (~2.5 V), VIL ≤ 0.25 × VDD (~0.8 V); outputs 0 / 3.3 V less the drop above |
| Voltage on any EXP pin, every state | **0 to 3.3 V nominal, never < −0.3 V or > 3.6 V**. When on, the switch passes up to 5.5 V and does **not** protect the ESP32: 5 V signals are forbidden |
| Bus off, card powered | high-Z, ≤ 100 nA |
| Card unpowered | high-Z, ≤ 2 µA per line at 0–3.6 V (TMUX1511 powered-off protection); no back-feed into the card |
| Current per line | ≤ 5 mA recommended; contention with a card output is limited to ~15 mA by the 220 Ω |
| Signalling rate | ≤ ~10 MHz recommended (card side ~12–15 pF; τ ≈ 5–10 ns with carrier load) |
| ESD, card side | chip-level only (TMUX1511 HBM ±2 kV, CDM ±750 V) — carrier rule §5.7 |
| Glitches | none from the card during power-up, EN/PERST# reset and boot (bus held off, §4.3.1); software/watchdog resets **[FW]** (§4.3.1); confirm by scope at bring-up |

I²C on EXP_0 (SDA) / EXP_1 (SCL):

- The card's **4.7 kΩ pull-ups** to its 3.3 V sit on the MCU side of the
  switch: they reach the edge only while the bus is on. Carriers add none for
  the ID EEPROM.
- Budget: card side ~12–15 pF per line. **100 kHz:** carrier side
  ≤ ~235 pF. **400 kHz:** carrier side **≤ 60 pF**. **[FW]** the ID EEPROM is
  read at 100 kHz.
- **Fixed:** extra carrier pull-ups (e.g. Qwiic/STEMMA breakouts): only to
  the 3.3 V that feeds the card, never 5 V; combined with the card's 4.7 kΩ
  **≥ 2 kΩ** (carrier pull-up **≥ 3.9 kΩ**), because the card drives low
  through ~245 Ω.
- Other carrier I²C devices may share the bus but must not use address 0x50.

#### 4.3.3 Carrier ID EEPROM (fixed, GATE V1; wiring fixed RC1)

- **Part:** 24C02-class (256 B) at I²C **0x50**, on EXP_0 (SDA) / EXP_1 (SCL).
  Package free.
- **Wiring (CG6):** VCC = the same carrier 3.3 V that feeds the card;
  A2..A0 = GND; WP = GND through a 0 Ω or a jumper (the dev carrier as
  built ties /WC straight to GND). No pull-ups (card provides them).
- **[FW]** Page size: the card writes in 8-byte pages, which every 24C02 accepts
  (M24C02: 16-byte pages; AT24C02: 8-byte pages).
- Recommended on every production carrier. DNP on the dev carrier.

| Offset | Size | Field |
|---|---|---|
| 0x00 | 4 | magic `"M2CI"` |
| 0x04 | 1 | format version = 1 |
| 0x05 | 1 | flags (bit0: production programmed, others 0) |
| 0x06 | 2 | vendor ID (LE). 0x0001 = this project; 0xFFFF = unassigned/dev |
| 0x08 | 2 | product ID (LE) |
| 0x0A | 1 | product revision (ASCII, `'A'` = 0x41) |
| 0x0B | 1 | reserved 0 |
| 0x0C | 8 | serial number (binary, LE; 0 = none) |
| 0x14 | 24 | **EXP function map**: 12 × {function, param}, EXP_0 first |
| 0x2C | 32 | product name, ASCII, NUL-padded |
| 0x4C | 176 | vendor data (free) |
| 0xFC | 4 | CRC-32 (IEEE 802.3, LE) over 0x00..0xFB |

Function codes (card point of view; "in" = the carrier drives the line):

| Code | Function | Carrier side |
|---|---|---|
| 0x00 | unused (line stays high-Z) | nothing / high-Z |
| 0x01 / 0x02 / 0x03 | digital in / + pull-up / + pull-down | may drive push-pull |
| 0x04 | push-pull out (param = default level) | high-Z input |
| 0x05 | open-drain out | pull-up ≤ 3.3 V, input |
| 0x06 | analog in (ADC lines only) | may drive (0–3.3 V source) |
| 0x07 / 0x08 | I²C SDA / SCL (EXP_0/1 always) | open-drain only |
| 0x09 / 0x0A | UART TX / RX (param = port) | TX: input; RX: may drive |
| 0x0B–0x0E | SPI SCK / MOSI / MISO / CS (*proposed*: card = SPI controller) | MISO: may drive; others: input |
| 0x0F | PWM (param = channel) | input |
| 0x10 | WS2812/RMT data | input |
| 0x80–0xFF | vendor-defined | per vendor; the electrical rules of §5 apply |

**[FW] Firmware rules:**

1. Before releasing the hold, configure EXP_2..11 as inputs (high-Z) and
   EXP_0/1 as I²C.
2. Release (IO38 low), wait **≥ 10 ms** (worst-case turn-on ~6.5 ms,
   §4.3.1; the bring-up self-test waits 60 ms), probe 0x50 at 100 kHz.
3. Valid magic **and** CRC → configure the lines per the function map;
   refuse functions a line cannot do (e.g. analog on a non-ADC line).
4. **Fixed** (owner, RC1 delta review): no ACK, bad CRC or unknown format →
   "unknown carrier": firmware turns the bus off again (IO38 high or input).
   The host may override explicitly (dev use, e.g. a carrier without
   EEPROM: the dev carrier uses the override). This replaces the GATE V1
   rule "unknown carrier: inputs only".
5. Drive IO38 high as early as possible in boot and in a shutdown handler
   before any software restart (§4.3.1: software and watchdog resets may
   not return IO38 to input).

### 4.4 Host-facing pins (v2; also work in any normal M.2 host)

| Pin | Net | Card side | Carrier may |
|---:|---|---|---|
| 10 | `LED_1_n` | open-drain NMOS, can only pull low; sink **≤ 50 mA**, VOL ≤ 0.1 V at 50 mA | LED + resistor, or pull-up, to ≤ 3.3 V (abs. 3.6 V) (activity LED) |
| 23 | `WAKE_ON_WWAN_n` | open-drain NMOS (IRQ / wake to host); same ratings | pull-up to ≤ 3.3 V and read it as an interrupt |
| 26 | `W_DISABLE2_n` | input, insulated NMOS gate, **100 kΩ** card pull-up to 3.3 V (M.2: 100–200 kΩ) | pull low = radio off (WiFi/BLE disabled) **[FW]** |

- Both outputs are released (high-Z) while the ESP32 is in reset, ROM boot
  or crashed (gate pull-downs).
- **Fixed limit:** WAKE_ON_WWAN# works only while the host keeps PERST#
  deasserted and the slot powered. A host that holds PERST# low in sleep
  keeps the card in reset, so the card cannot wake it. **[FW]** across ESP32
  deep sleep the pin needs digital GPIO hold (IO47 is not an RTC GPIO).
- **[FW]** radio-off latency after pin 26 goes low: not specified yet.

### 4.5 Everything else

Leave **NC** on carriers: USB3/PCIe lanes, REFCLK, CLKREQ#, PEWAKE#,
SUSCLK 68, RESET# 67, FULL_CARD_POWER_OFF# 6, DPR 25, 22/24/28, 38,
42–48, 56/58, 66. The card leaves them NC too.

## 5. Carrier design rules (fixed, RC1)

1. **Sideband and CONFIG pins** (50, 20, 8, 26): carrier → card is
   **open-drain only** (pull low, never drive high). The pull-ups live on the
   card. That keeps a real 1.8 V WWAN modem plugged into our carrier safe.
   Pins 21/69: read only, pull-up ≥ 10 k. Pins 10/23: pull-up ≤ 3.3 V.
2. **Signature pins** 75 + 1: tie both to GND (≤ 0.1 V or ≤ 10 kΩ). Never
   drive or pull them high.
3. **EXP lines** (EXP_0..11):
   - The card tolerates 0–3.6 V on every EXP line in every state (unpowered,
     reset, bus off, bus on) without damage or back-feed (§4.3.2). A carrier
     driver that is active before the bus is on, or while the card is
     unpowered, is therefore electrically safe for the card. Power EXP
     drivers from the same 3.3 V that feeds the card where practical.
   - **Never above 3.6 V and never 5 V**, in any state.
   - A carrier may drive a line **push-pull** only if that line's function
     (§4.3.3) is a card input; I²C and open-drain lines are open-drain only;
     lines that are card outputs go into high-impedance carrier inputs.
   - Data is valid only while the bus is on (signature AND firmware release,
     §4.3.1). Before that, and during every card reset, the card side is
     high-Z: the carrier must not depend on any EXP level then.
   - *Proposed:* a carrier that needs to know the bus is on can sense EXP_1
     (SCL) idle high (the card's 4.7 kΩ pull-up reaches the edge only while
     the bus is on) with a ≥ 1 MΩ pull-down of its own.
4. **WWAN modems:** a carrier that drives any EXP line high is a
   companion-only carrier. A modem shares state 6 (§1), so the carrier cannot
   detect it. Either mark the socket "companion card only — no WWAN modem" on
   the silkscreen, or keep the drivers disabled until the carrier knows a
   companion card is present (e.g. a carrier bus switch enabled from the
   EXP_1 sense above).
5. **Card → carrier signals** go into **high-impedance carrier inputs**:
   transistor gates/bases with pull-downs, logic inputs.
   - Actuators (relays, LEDs, motors) must **default off** with no card,
     with a non-companion card that drives junk, with the card unpowered, and
     during card reset and boot (bus off, lines high-Z).
6. ≤ 5 mA per EXP line recommended (§4.3.2).
7. **ESD:** a carrier that brings any EXP line to a connector, terminal or
   header used off-board places ESD/TVS protection on the carrier (working
   voltage ≥ 3.3 V, lowest practical clamping voltage; low capacitance on
   EXP_0/1, counted in the I²C budget). The card has chip-level protection
   only. Bench headers on dev carriers: ESD-safe handling instead.
8. 3.3 V supply per §3. Never exceed 3.6 V.
   - *Proposed* (CG5): exception for lab fixtures that validate the v2 OVP:
     a deliberately switched, labelled bench path, v2 cards only, never the
     default supply.
9. Keep the antenna area clear (§2).
10. A production carrier should carry the ID EEPROM (§4.3.3, format fixed).
11. Silkscreen: label every exposed M.2 signal with **M.2 pin number + net
    name** (e.g. `61 EXP_7`).

**Card unpowered, carrier 3.3 V present** (fixed, CG7; totals computed from
datasheet maxima, to be measured on the dev-carrier fixture at bring-up):

| Pins | What the carrier sees |
|---|---|
| 21, 69 | card GND: the carrier pull-up current flows (e.g. 0.33 mA for 10 kΩ), powered or not |
| 75, 1 | 1 MΩ to the card rail: ≤ 3.3 µA each |
| 26 | 100 kΩ to the card rail: ≤ 33 µA |
| 10, 23 | NMOS drain, off: ≤ 1 µA |
| 50, 20, 8 | reverse-biased Schottky: ≤ 2 µA |
| EXP_0..11 | TMUX1511 powered-off: ≤ 2 µA each at 0–3.6 V |
| 7, 9 | USB ESD array: no back-feed from an idle USB host |

Worst case ≤ ~75 µA in total, ~40 µA of it into the unpowered card rail; no
latch-up path.

## 6. Contract gaps CG1–CG8 (from the dev carrier)

| ID | Topic | Answer | Status |
|---|---|---|---|
| CG1 | Bottom-side component height | ≤ 1.6 mm incl. solder; parts from 5.2 mm off the finger edge (§2) | **fixed** |
| CG2 | Antenna keep-out position | 2242: 31.4–37.6 mm from the finger edge; plus cards: 31 mm to the far end clear (§2) | **fixed** (2242); *proposed* (plus cards) |
| CG3 | Notch plating / standoff | routed, no copper, no net; M2 × 0.4 screw at 42 mm (§2) | **fixed**; 2252 position *proposed* |
| CG4 | Input capacitance / inrush | 100 nF direct + ~65 µF behind dV/dt; ≤ ~90 mA; 1.15 A after an OVP trip; supply ≥ 1.2 A (§3) | **fixed** |
| CG5 | Test fixtures above 3.6 V | §5 rule 8 | *proposed* |
| CG6 | ID EEPROM VCC / WP / address / package | §4.3.3 | **fixed** |
| CG7 | Carrier pull-ups with the card unpowered | per-pin table in §5 | **fixed** (to be measured) |
| CG8 | Sink rating of LED_1# / WAKE_ON_WWAN# | ≤ 50 mA, VOL ≤ 0.1 V at 50 mA, pull-up ≤ 3.3 V (§4.4) | **fixed** |

## 7. Change log

- **2026-10-07, GATE V1:** pinmap, EXP capabilities and ID EEPROM fixed.
- **2026-10-10, GATE V3:** GPIO column fixed to the routed Rev A copper.
- **2026-10-28, RC1** (RC1 design review): bus enable is now carrier AND
  firmware (IO38 hold, §4.3.1; the old "independent of firmware" and "high-Z
  until a valid EEPROM is read" wording was wrong: the bus used to turn on
  before the ESP32 left reset); new EXP electrical spec and I²C budget
  (§4.3.2); EEPROM format copied in and wiring fixed (§4.3.3); §5 rewritten
  for push-pull EXP drive, modems and ESD; OVP latch-until-power-cycle, inrush
  and current budget (§3); CONFIG_2/3 are not NC and host-load limits
  (§4.2); W_DISABLE2# pull-up 1 MΩ → 100 kΩ, sink ratings, wake limit
  (§4.4); CG1–CG8 answered (§6); **[FW]** tags.
- **2026-10-28, RC2** (RC1 delta review, `docs/review/v2_rc1_delta_review.md`;
  owner accepted the recommendations): OVLO filter 100 pF C0G, τ ≈ 3.4 µs
  (§3: the 1 nF / τ 34 µs filter let an overvoltage ramp reach ~3.7–3.9 V);
  card rail ramp ~2–16 ms (§3); R33 on the top side (§2); three parts at the
  5.2 mm bottom limit (§2); turn-on 1–6.5 ms, off times to be confirmed at
  bring-up, software/WDT resets **[FW]** (§4.3.1); light-sleep rule (§4.3.1);
  dev-carrier /WC tied to GND, 8-byte EEPROM pages (§4.3.3). Owner decisions
  now **fixed**: unknown-carrier rule 4 (§4.3.3), I²C pull-up minimum
  (§4.3.2), J3 +3V3 budget ≤ 150 mA (§3), off times (§4.3.1, to be
  measured), unpowered back-feed totals (§5, to be measured). New firmware
  rule 5 (IO38 high early in boot and before a software restart).
