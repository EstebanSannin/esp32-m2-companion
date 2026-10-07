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
