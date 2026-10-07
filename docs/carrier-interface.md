# Carrier interface — ESP32-S3 M.2 companion card

**The contract between the companion card and any carrier or accessory board.**
Single source of truth for carrier design sessions: import it from a carrier
repo's `CLAUDE.md` with
`@/Users/stefano.viola/code/esp32-m2-companion-v2/docs/carrier-interface.md`
(after v2 merges: `…/esp32-m2-companion/docs/carrier-interface.md`).

Version: **v2.0 Rev A, GATE V1 approved 2026-10-07**. Decisions: ADR 0006 (edge interface),
ADR 0007 (input OVP), ADR 0008 (form factor). Background, research and
rejected alternatives: `v2/edge-expansion-brainstorm.md`,
`v2/research/m2_pins_research.md`.

Status legend: **fixed** = owner-approved; *proposed* = to confirm at v2
GATE 1 (pinmap). Carriers may rely on **fixed** items only.

---

## 1. Card revisions a carrier must handle

| Card | Identify by | Edge features |
|---|---|---|
| v1.0 / **v1.0 Rev B** (fabricated) | CONFIG_0..3 all NC → host reads `1111` (state 15) | USB 2.0, power, PERST#→EN, BOOT on pin 20 (+ pin 8 on Rev B). **No expansion bus, no OVP, no host-facing pins.** |
| **v2.0 Rev A** (in design) | CONFIG_0 (21) + CONFIG_1 (69) grounded → state 6 | everything above + 12-line expansion bus + LED_1#/WAKE_ON_WWAN#/W_DISABLE2# + input OVP |

A carrier designed to this document works with both. With a Rev-B card,
the EXP pins and pins 10/23/26 are simply unconnected on the card.

## 2. Mechanical

- **Fixed:**
  - M.2 **Key B** socket.
  - Card **22 mm wide, 0.8 mm**, length **2242** for v1/v2.
  - Possible future "plus" cards at 2252 / 2260: put standoff positions for
    2242 / 2252 / 2260 on carriers.
- **Fixed:** the card has components on **both sides**.
  - Top: WROOM module (antenna at the far end from the fingers) + 2 JST SH
    connectors.
  - Bottom: passives, SOT-23/SOT-23-6, side-view LEDs, test points.
  - Choose the socket stack height so the bottom parts clear the carrier,
    and keep carrier components out of the card's footprint.
  - Measure heights from `docs/3d/esp32_m2_companion.step` (Rev B).
- **Fixed:** antenna keep-out. No metal (copper pour, shields, tall
  parts) under or over the **far end of the card**. The WROOM PCB antenna
  keep-out spans **4.4–10.6 mm from the card's far edge** (the mounting-screw
  end), all layers (Rev-B board, Espressif HDG). Carriers should keep the
  whole last ~11 mm of the card clear.
- Edge fingers are ENIG hard gold and **not bevelled** (hand-chamfered).

## 3. Power

- **Fixed:** the carrier supplies **3.3 V ±5 % (3.135–3.465 V)** on pins
  2, 4, 70, 72, 74.
  - Design for **≥ 1 A**: the card peaks at ~0.5 A on WiFi TX bursts, and
    the v2 eFuse current limit is ~1 A.
- **Fixed:** **never more than 3.6 V.**
  - Rev-B cards have no protection: the ESP32-S3 absolute maximum is 3.6 V.
  - v2 cards cut off at ~3.49 V (3.44–3.57 V window) and stay off, without damage, up to 28 V
    (ADR 0007). Even so, the 3.6 V limit applies to every carrier.
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
| 75 | CONFIG_2 | NC on card, 1 MΩ card pull-up behind 100 kΩ to a FET gate | **tie to GND** = "I am a companion carrier" |
| 1 | CONFIG_3 | same | **tie to GND** |

- **Fixed:** the v2 card enables its expansion bus **only when BOTH 75 and 1
  are at 0 V**.
  - Any host pull-up (1.8 V or 3.3 V), or a floating pin, keeps the bus off.
  - The detect is in hardware (two low-Vth NMOS, wired-NOR, RC-delayed) and
    is independent of firmware.
- A Rev-B card ignores these pins, so grounding them is harmless.
- A real WWAN modem in our carrier just sees two grounded CONFIG pins,
  which is also harmless.

### 4.3 Expansion bus EXP_0..11 (v2 only, active only on a carrier)

**Fixed: the M.2 pin ↔ EXP name mapping**, numbered by ascending M.2 pin, so
it is independent of layout:

| EXP | M.2 pin | WWAN name (reference) | **Capability (fixed, GATE V1)** | ESP32-S3 GPIO (informative — may swap within class until v2 fab) |
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
ADC1, usable with WiFi on. Layout may swap GPIOs **within a capability class only**; carriers
design against the capability column, never the GPIO column.

- **Fixed electrical:**
  - **3.3 V** logic, bidirectional through a TMUX1511 switch (Ron ≤ 4.5 Ω).
  - Behind ~220 Ω series resistors on the ESP side.
  - High-Z when the bus is off or the card is unpowered (≤ 2 µA at 0–3.6 V).
- **Fixed (GATE V1, 2026-10-07):** the capability column above (6 ADC lines, EXP_0/1 = I²C), and the
  **carrier ID EEPROM**, 24C02-class at I²C **0x50** on **EXP_0 (SDA) /
  EXP_1 (SCL)**.
  - The bus pull-ups are on the card, on the MCU side of the switch, so they stay isolated when
    the bus is off. Carriers add none, but may hang other I²C devices on the same bus.
  - Format v1: `docs/v2-gate-v1.md` §2 (magic `"M2CI"`, vendor/product/revision/serial, a 12-entry
    EXP function map, CRC-32).
  - **Firmware rule:** after the bus enables, only EXP_0/1 are initialised. EXP_2..11 stay high-Z
    until a valid EEPROM is read. With no EEPROM or an invalid one, the carrier is "unknown":
    inputs only, unless the host overrides.
  - Recommended on every production carrier. DNP on the dev carrier.

### 4.4 Host-facing pins (v2; also work in any normal M.2 host)

| Pin | Net | Card side | Carrier may |
|---:|---|---|---|
| 10 | `LED_1_n` | open-drain NMOS, can only pull low | LED + resistor to ≤ 3.3 V (activity LED) |
| 23 | `WAKE_ON_WWAN_n` | open-drain NMOS (IRQ / wake to host) | pull-up to ≤ 3.3 V and read it as an interrupt |
| 26 | `W_DISABLE2_n` | input, insulated NMOS gate, 1 MΩ card pull-up | pull low = radio off (WiFi/BLE disabled) |

### 4.5 Everything else

Leave **NC** on carriers: USB3/PCIe lanes, REFCLK, CLKREQ#, PEWAKE#,
SUSCLK 68, RESET# 67, FULL_CARD_POWER_OFF# 6, DPR 25, 22/24/28, 38,
42–48, 56/58, 66. The card leaves them NC too.

## 5. Carrier design rules (fixed)

1. **Carrier → card signals are open-drain only** (pull low, never drive
   high). The pull-ups live on the card. That keeps a real 1.8 V WWAN modem
   plugged into our carrier safe.
2. Card → carrier signals go into **high-impedance carrier inputs**:
   transistor gates/bases with pull-downs, logic inputs.
   - Actuators (relays, LEDs, motors) must **default off** with no card
     present, or with a non-companion card that drives junk.
3. Ground both signature pins (75 + 1). Never drive 3.3 V onto any card pin.
4. 3.3 V supply per §3. Never exceed 3.6 V.
5. Keep the antenna area clear (§2).
6. A production carrier should carry the ID EEPROM (§4.3) once its format
   is fixed.
7. Silkscreen: label every exposed M.2 signal with **M.2 pin number + net
   name** (e.g. `61 EXP_7`).
