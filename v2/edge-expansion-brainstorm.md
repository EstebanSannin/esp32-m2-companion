# v2 brainstorm — M.2 edge expansion bus (hardware-gated)

Status: **brainstorm, nothing accepted** · started 2026-10-06 on branch `rev-b` (local only)

> **Read §11 first.** The research results (2026-10-06) supersede several
> earlier choices in §4, §5.1–5.5 and §9. Superseded lines are marked ⟶ §11.

## 0. Goal

Route as many spare ESP32-S3 GPIOs as possible to the M.2 Key-B edge, so that
a **custom carrier** (relay board, sensor board, …) with a standard M.2 socket
can use the companion as its brain. Two hard requirements:

1. **Any** standard M.2 Key-B host — laptop WWAN slot, B+M SSD slot,
   Mallow, RPi modem HAT, cheap M.2→USB adapter — must see a card that is
   electrically no worse than v1, with **no damage to the host or the card**.
2. The protection must be **hardware**. It must hold with the card
   unpowered, with blank or bricked firmware, and with buggy firmware.

Not limited to Mallow: the reference is the M.2 standard (Socket 2, Key B).

## 1. Sources

- **[M2]** PCI-SIG *PCI Express M.2 Specification Rev 1.0* (2013), archive copy
  `docs/datasheets/m2_em_spec_rev1.0_2013_archive.pdf`:
  Table 25 (Socket 2 signal table, p. 118 ff.), Table 26 (GPIO port configs),
  Table 27 (CONFIG decodes, p. 129), Table 29 (USB3.0 WWAN module pinout,
  p. 131), §5.2 / Tables 46–47 (platform side, pp. 151–154).
- **[KEYB]** Quectel RM50xQ HW Design V1.2: Table 8 (pinout, newer WWAN
  usage), Tables 28–29 (CONFIG, p. 56).
- **[WROOM]** ESP32-S3-WROOM-1 datasheet v1.8, DC characteristics:
  VIH = 0.75 × VDD, VIL = 0.25 × VDD.
- **Gap:** current M.2 spec revisions (3.x/4.x/5.x) are paywalled. Rev 1.0 plus
  a 2022 modem datasheet show that pin definitions changed between
  revisions (see F1). Anything below marked *(verify)* needs a newer source.

## 2. What the standard actually says (findings)

**F1 — On an unknown host, any non-power pin may be driven by the host.**
Pin meanings depend on socket type (WWAN or SSD), spec revision and vendor:

| Pin | [M2] Rev 1.0 WWAN (card POV) | [M2] SSD socket | [KEYB] newer WWAN |
|---:|---|---|---|
| 38 | N/C | DEVSLP (host → card) | SDX2AP_STATUS (card → host) |
| 56 / 58 | N/C | MFG data/clock | RFFE_CLK / RFFE_DATA (card out) |
| 65 | ANTCTL3 (card out) | — | RFFE_VIO_1V8 (**card power out**, 50 mA) |
| 66 | SIM_DETECT (card in; **SIM switch grounds it** when empty) | — | UIM1_DET |
| 68 | SUSCLK (**host out, 3.3 V, 32 kHz**) | SUSCLK | AP2SDX_STATUS (card in) |
| 6 | FULL_CARD_POWER_OFF# (card in) — **notebooks tie it to 3.3 V** [M2 §5.2.2] | — | same |
| 41–49 | PCIe lane 0 | **SATA / PCIe from host** | PCIe |

Consequence: no "free" pin is safe to drive blindly. Each extra edge pin
must be **high-impedance and voltage-tolerant by default, including when
the card is unpowered**.

> Correction to the first chat brainstorm: there I called pins 38/68 "card
> outputs" and 56–64 "NC everywhere". Both claims depend on the revision and
> the socket type. Hardware gating is required, not optional.

**F2 — Voltage domains are mixed.** [M2 Table 25]
- 3.3 V: W_DISABLE1#, LED_1# (OD), PERST#, CLKREQ#, PEWAKE#, SUSCLK, CONFIG pull-ups.
- 1.8 V: GPIO_0..11, W_DISABLE2#, DPR, RESET#, COEX, SIM_DETECT, WAKE_ON_WWAN#.
- ANTCTL: 1.8 V nominal, 2.8 V max. HSIC on pins 23/26 (port config 3): **1.2 V**.
- FULL_CARD_POWER_OFF#: 1.8 or 3.3 V.
- The ESP32-S3 at 3.3 V needs VIH ≥ 2.475 V, so it **cannot read 1.8 V push-pull
  signals directly**, and its outputs must never reach a 1.8 V host pin.
- The rev-B Schottky cell can't read them either: a 1.8 V push-pull high
  forward-biases the diode (see `sideband_recovery/LESSONS.md`, GATE 2).

**F3 — The CONFIG pins are the standard's own protection mechanism.**
- [M2 Table 25 footnote]: hosts should use CONFIG "to ensure … that no
  electrically incompatible signals are driven onto these pins … prior to
  discovery of the module type".
- The host **must pull up** all four CONFIG pins [M2 §3.2.12]. The card
  only grounds them or leaves them NC.
- v1 / rev B leaves all four NC, which decodes as **state 15 = "No Module
  Present"**. That's harmless on Mallow (host doesn't read them). A host that
  does read CONFIG (laptop BIOS) may ignore the slot or keep it unpowered.
  *(Observation for rev B as well; not filed anywhere yet.)*
- Vendors also use RFU states: [KEYB] RM50xQ declares NC/GND/NC/NC as
  "Quectel defined".

**F4 — Some pins have useful standard meanings for a companion MCU.**
[M2 Table 26, §3.2.10]
- WAKE_ON_WWAN# (pin 23): open-drain card → host, wakes the host, so it can
  serve as an **IRQ line**.
- LED_1# (pin 10): open-drain 3.3 V.
- W_DISABLE2# (pin 26): host requests radio off.
- Port config 3 is literally "**IPC** — inter-processor communication between
  host and card" (GPIO_0..8 → IPC_0..7). But it also moves pins 23/26 to
  1.2 V HSIC.

## 3. Design principle

> **Default edge = v1 edge.** Every new edge connection passes through an
> isolation element. That element is high-impedance with the card
> unpowered, tolerates 0–3.6 V from the host, and is enabled only by a
> **hardware signature that no compliant host can produce**. Firmware is a
> second line of defence, never the first.

The new connections fall into three classes:

| Class | Enabled when | Isolation element |
|---|---|---|
| **A. Host-facing sidebands** (spec semantics) | always | voltage-agnostic buffers: OD output / low-threshold input, both with Ioff |
| **B. Carrier expansion bus** | carrier signature present | bidirectional bus switch, OE from signature logic |
| **C. Untouched** | never | — |

## 4. Class A — host-facing sidebands

These work on every host because they follow the standard's meaning.

- ⟶ §11.4: Rev A uses dual NMOS cells instead of the logic buffers below.
- **Outbound cell (card → host):** single open-drain buffer
  (74LVC1G07-class: Ioff, 5.5 V-tolerant output) *(verify part + LCSC)*. It
  can only pull low, so it's safe at any host pull-up voltage, and a firmware
  bug can't drive the pin high.
- **Inbound cell (host → card):** single-supply low-threshold buffer
  (SN74LV1T34-class: accepts 1.8 V high at Vcc = 3.3 V, Ioff, high-Z input)
  *(verify part + LCSC)*. It **replaces** the Schottky trick for 1.8 V
  push-pull hosts. Card pull-up/pull-down behind the buffer sets the
  "unconnected" state.

| Pin | Signal | Cell | Firmware meaning |
|---:|---|---|---|
| 23 | WAKE_ON_WWAN# | out OD | IRQ to host (data ready, event); 1 s pulse = spec wake |
| 10 | LED_1# | out OD | host-side activity LED |
| 26 | W_DISABLE2# | in | radio kill → WiFi/BLE off (rfkill semantics). Harmless if the host does HSIC here (buffer input only) |

Possible extension: an IPC group on GPIO_0..8 (pins 40–48, 22/24/28). Those
pins reach Verdin GPIOs through the Mallow X16 jumper header, so they'd give
a host↔card side channel. That costs ESP pins and competes with class B.
→ Open question Q4.

Existing sidebands (pins 8, 20, 50: BOOT/EN via Schottky) stay as in rev B.

## 5. Class B — carrier expansion bus

### 5.1 Carrier signature: the CONFIG trick

Our carrier **grounds CONFIG pins that the card leaves NC**.
- A compliant host must pull those pins up, so a hard 0 V on a card-NC
  CONFIG pin cannot happen on a compliant host.
- A host with no pull-up (e.g. Mallow, CONFIG NC on host side) leaves the
  pin floating. A weak card pull-up (~1 MΩ to 3V3) then reads it as high,
  so the switch stays off.
  - Back-feed into a 1.8 V host pull-up is ~1.5 µA, negligible.
  - The sense input must have high input impedance (buffer or FET gate)
    *(verify leakage budget)*.
- A real WWAN modem plugged into our carrier just has those CONFIG pins
  grounded. Nothing is driven into the modem.
- Use **two** CONFIG pins, AND-ed (both low → OE). One solder short or one
  odd adapter can't open the bus.

What the card declares (Q1) decides which CONFIG pins are free:

| Card declares | CONFIG 0/1/2/3 (pins 21/69/75/1) | Free for signature | Notes |
|---|---|---|---|
| state 15 (as rev B) | NC/NC/NC/NC | any two | "No Module Present" to CONFIG-aware hosts (F3) |
| state 5, WWAN-USB3.0, port cfg 1 | GND/NC/GND/NC | 69 + 1 | chosen at first (Q1) ⟶ §11.1: no real module uses it |
| **state 6**, WWAN-USB3.x, port cfg 2 | GND/GND/NC/NC | 75 + 1 | used by Telit FN990 and Sierra EM7455 — **chosen (owner, 2026-10-07)** |
| state 7, WWAN-USB3.0, port cfg 3 (IPC) | GND/NC/NC/NC | 69, 75, 1 | IPC semantics fit best, but pins 23/26 become 1.2 V HSIC → conflicts with class A |

USB 2.0 is supported on all WWAN configs [M2 Table 27 note 1], so declaring
USB3.0-WWAN with only USB2 lines active is legitimate. On the SS lanes, host
receiver detection finds no termination and the host falls back to USB2.

### 5.2 Enable logic

- `EXP_OE = !CONFIG_a AND !CONFIG_b` (one 74LVC1G-class gate, or two FETs). ⟶ §11.2: must be two low-Vth FETs, not an LVC gate.
  It must fail **off** when the card is unpowered or the inputs float.
- Optional: an RC delay so OE asserts only after 3V3 is stable and the
  ESP straps are sampled. That keeps the carrier out of the boot window.
- The ESP gets `EXP_OE` on one GPIO (readback / diagnostics). It cannot
  force OE.

### 5.3 Bus switch requirements (part TBD)

| Requirement | Why |
|---|---|
| Bidirectional, rail-to-rail 0–3.3 V pass | I2C / SPI / GPIO; NMOS-only CBT clips at ~Vcc − Vth ≈ 2.3 V < ESP VIH 2.475 V ✗ |
| **Powered-off protection** (high-Z with Vcc = 0, pins up to 3.6 V) | host keeps 3.3 V / SUSCLK / pull-ups alive while the card may be unpowered; plain CMOS transmission gates conduct when unpowered ✗ |
| OE default off (pull to the disabled level) | fail-safe |
| Ron ≲ 10 Ω, Coff ≲ 5 pF, ≥ 10 MHz | SPI-class speeds; small load on host lines when off |
| 8- or 16-channel package, LCSC stocked | area |

Candidates to evaluate *(all unverified)*: TI TMUX1574 / TMUX1511 family,
SN74CB3Q3245 / SN74CB3Q16244, Diodes PI3USB/PI5C (check Ioff).

### 5.4 Defence in depth

1. **Hardware gate** (above). Covers compliant hosts, blank or buggy firmware.
2. **Series resistors** 100–330 Ω on the ESP side of each line. They limit the
   fault current to ESP-safe levels if a non-compliant adapter grounds the
   signature pins *and* ties an expansion pin.
3. **Firmware:** after OE, read the carrier's ID EEPROM (I²C on two expansion
   lines, HAT-EEPROM style: vendor, product, pin-function map). Lines stay
   inputs until a valid ID is read.

### 5.5 Edge pin candidates for class B

Excludes power/GND, USB2 (7/9), CONFIG, rev-B sidebands (8/20/50), class A
(10/23/26).

| Pin(s) | Why usable | Concern | Rank |
|---|---|---|---|
| 56, 58 | N/C (Rev 1.0) / RFFE card-out (newer) | ⟶ §11.3: Dell Latitude drives 58 and senses 56 — demoted | ★ |
| 59, 61, 63, 65 | ANTCTL card-out | 65 = RFFE_VIO power out in newer revs | ★★★ |
| 60, 62, 64 | COEX 1.8 V | — | ★★★ |
| 30, 32, 34, 36 | UIM, card-driven by design | host side = SIM socket | ★★★ |
| 38, 68 | — | host-driven in SSD / Rev 1.0 (DEVSLP, SUSCLK) | ★★ |
| 25 | DPR | host-driven (SAR sensor) | ★★ |
| 40, 42, 44, 46, 48 / 22, 24, 28 | GPIO_0..8 | on Mallow these go to host GPIOs (X16); maybe better kept for class A IPC (Q4) | ★★ |
| 52, 54 | CLKREQ#/PEWAKE# OD 3.3 V | PCIe semantics; PEWAKE# is 1.8 V on Mallow | ★ |
| 66 | SIM_DETECT | grounded by the host SIM switch, so it **can't** be a signature pin | ★ |
| 6, 67 | power-off / reset | keep for a future host-controlled power/reset feature | ✗ |
| 29–37 odd, 41–49 odd, 53, 55 | high-speed lanes | keep for a future brain with USB3/PCIe | ✗ |

The ★★★ rows give **13 pins**. Adding 38/68/25 gives 16. **v2 Rev A uses 12 (Q3)**, all from the ★★★ rows.

### 5.6 ESP32-S3 side budget

- Spare in rev B: IO1, 2, 4, 5, 6, 7, 15, 16, 17, 18, 38, 39, 40, 41, 42, 47 → **16**.
- Class A takes 3 (LED, WAKE, W_DISABLE2) and `EXP_OE` readback takes 1,
  leaving **12** for class B.
- Options for more:
  - (a) Use IO35–37, which drops the N16R8 drop-in compatibility. → Q5
  - (b) Share I²C with Qwiic J3.
  - (c) An I²C GPIO expander on the carrier side.
- Rules:
  - No strapping pins (IO0/3/45/46) on the bus.
  - Put analog functions on **IO1–IO10** (ADC1); ADC2 is dead while WiFi runs.
  - IO39–42 = JTAG → carrier debug header option.
  - IO15/16 = XTAL_32K: pin 68 SUSCLK (host 32 kHz) could even feed the RTC.
    A curiosity, not a requirement.

## 6. The other direction: a standard modem in our carrier

Carrier design rules, so that plugging a real WWAN modem into a companion
carrier can't damage the modem:
- **Carrier → card signals are open-drain only**; the pull-up is on the card,
  behind the switch. A modem only ever sees pulls to GND on its 1.8 V pins.
- Card → carrier signals go into high-Z carrier inputs (transistor bases,
  logic inputs). A modem's 1.8 V outputs there are harmless.
- Carrier grounds only CONFIG pins (signature), never drives 3.3 V on any
  card pin.
- Carriers carry the ID EEPROM (§5.4.3). Relay/actuator boards should
  default outputs off (pull-downs on driver inputs) so a non-companion card
  can't click relays.

## 7. Space, layers, form factor

The owner allows **2252** or **+2 layers** if 2242 doesn't route.
- **2252**
  - Not a compatibility break: same socket. The host only needs a
    52 mm standoff.
  - Mallow supports 30/42/52 [MALLOW]. Laptop WWAN slots are 3042/3052, and
    a 22-wide card fits a 30-wide slot at the 52 position *(verify per
    host)*.
  - The Waveshare RPi HAT wiki lists 3042/3052 only, so **2252 may
    improve compatibility** there.
  - Gives ~10 mm more length for 2× switch + cells + signature logic.
- **6 layers:** more escape room near the edge, cost ↑ at JLC; keep
  0.8 mm. *(verify JLC 6L @ 0.8 mm stackup + impedance)*
- **Lesson** (`sideband_recovery/LESSONS.md` 2026-10-06): run a grid
  feasibility probe before declaring anything unroutable. Do it before
  choosing 2252 vs 6L.
- New parts estimate: 2× 8-ch switch (or 1× 16-ch), 1 gate,
  3 single-gate cells, ~2× 8 series-R arrays, 2–3 R/C.

## 8. Validation (ties to the platform-vision open problem)

- **Host-safety test card / fixture:** with the card inserted (powered and
  unpowered), measure every edge pin.
  - Leakage < X µA at 0 / 1.8 / 3.3 V, applied host-side.
  - OE must stay off with: CONFIG pins pulled up to 1.8 V; pulled up to
    3.3 V; floating; one pin grounded.
- **Carrier fixture:** grounds the signature pins, loops back expansion lines,
  carries an ID EEPROM. Firmware self-test proves every line both ways.
- Run on Mallow, a laptop WWAN slot, an M.2→USB adapter and a B+M SSD slot,
  checking the host survives and the USB function still works.

## 9. Owner decisions and open questions

Decided 2026-10-06 (brainstorm level, to be formalised as an ADR on the v2 branch):

- **Q1 → declare state 6** *(revised 2026-10-07, owner approved; originally
  state 5, superseded — see §11.1)*. Card grounds CONFIG_0 (pin 21) and
  CONFIG_1 (pin 69), leaves CONFIG_2 (pin 75) and CONFIG_3 (pin 1) NC;
  signature pair = 75 + 1. Original state-5 text follows for history:
  card grounds CONFIG_0 (pin 21) and CONFIG_2
  (pin 75), leaves CONFIG_1 (pin 69) and CONFIG_3 (pin 1) NC. That decodes
  as "WWAN, USB 3.0 host interface, port configuration 1" [M2 Table 27].
  Our card actually uses only USB 2.0, which the spec allows for every WWAN
  configuration. Pins 69 + 1 become the carrier-signature pair (§5.1).
  Owner delegated the choice.
- **Q3 → 12 lines for v2 Rev A.** Fits the current ESP budget (§5.6) with no
  module swap and no expander. Q5 (IO35–37) is therefore moot for Rev A.
  Widen in a later revision if a carrier needs it.
- **Q6 → no shared multi-MCU bus spec.** ESP32 family only for the
  foreseeable future (business analysis). Only zero-cost hygiene: generic
  net names (`EXP_0..11`, `EXP_OE`), and keep the ID-EEPROM layout
  documented in one place.

- **Q2 → CONFIG-only, two pins (69 + 1), AND-ed.** A compliant host must
  pull both up; both at a hard 0 V cannot happen on a compliant host, and a
  single short opens nothing. Non-compliant adapters are covered by the
  series resistors + ID-EEPROM check (§5.4).
- **Q4 → GPIO_0..8 (pins 40–48, 22/24/28) are NOT used as always-on class A.**
  Laptops and other hosts may wire them to a GNSS I²C, a PCM/I²S codec
  (host push-pull clocks) or a second SIM, so even an open-drain output
  there can fight a host driver. They are safe only behind the switch
  (class B). Rev A doesn't need them (12 lines come from the ★★★ pins), so
  they stay **NC** in Rev A and become the first reserve if the bus is widened.
  The Mallow X16 "host IPC side channel" idea is dropped: it can't be made
  safe for every host.
- **Q7 → evaluate 2242 first** (owner prefers 42; 52 acceptable).
  Order: 2242 + 4L → 2242 + 6L → 2252 + 4L, decided by the feasibility probe.

## 10. Next steps (as first proposed; status in §11.7)

1. Get a newer M.2 spec revision (or more modem/SSD datasheets) to close
   the *(verify)* marks on pins 38/56/58/65/68.
2. Part search on LCSC: bus switch (§5.3 table), OD buffer, LV1T34-class
   input, signature gate. Basic/Extended status + datasheets into a v2
   datasheets folder.
3. Draft block `edge_expansion` (switch + signature + cells) in SKiDL on
   the v2 branch. Placement and routing feasibility probe on 2242 first.

## 11. Research results and revised design (2026-10-06)

Sources: `research/m2_pins_research.md` (M.2 Rev 3.0 via congatec AN43, five
modem datasheets, Dell Latitude / Waveshare / Osmocom / Geniatech host
schematics) and `research/parts_research.md` (live JLC stock + manufacturer
datasheets, PDFs in `research/datasheets/`).

### 11.1 CONFIG declaration: state 6 instead of state 5 — **approved by owner 2026-10-07**

- **No real module declares state 5** (Rev 3.0 renames it "WWAN – PCIe,
  USB3.1 Gen1, PC1"). Hosts that whitelist by CONFIG, like Dell BIOS, may
  ignore an unusual pattern.
- **State 6** (pins 21 + 69 GND, 75 + 1 NC) is what **Telit FN990 and Sierra
  EM7455** declare. It is a field-proven "USB3/PCIe WWAN modem" pattern.
- Port config 2 only changes GPIO_0..8 (pins 40–48 → second SIM, 20–28 →
  RFU). Pins 10/23/26 (class A) keep their meaning.
- Signature pair becomes **75 + 1**.
- Other states in the field, for reference: SIMCom = state 4;
  Quectel = state 14, which Dell BIOS reads as "HCA-PCIe".

### 11.2 Carrier detect: low-threshold wired-NOR, not a logic gate

- **New risk.** Quectel and NVIDIA allow the host CONFIG pull-up to be
  **1.8 V**. A 74LVC gate (VIH 2.0 V at 3.3 V) or an ESP GPIO (VIH 2.475 V)
  would see 1.8 V as undefined or low. That means a **false carrier detect
  on a foreign host**, which is exactly the failure we must not have.
- **Fix:** two N-MOSFETs with **VGS(th) max ≤ ~1.0 V**, wired-NOR
  (drains → `EXP_OE`, 100 kΩ pull-up + 100 nF RC):
  - `EXP_OE` is high only when **both** sense pins are near 0 V (FETs off).
  - 1.8 V pull-up, 3.3 V pull-up, or floating (the card's own 1 MΩ pull-up)
    all turn a FET on, so OE stays low.
- **Insulated gates** behind 100 kΩ series resistors mean **no back-feed**
  into an unpowered card. The spec keeps host CONFIG pull-ups alive while
  the card is off (congatec AN43); 0.27 mA through an ESP clamp is avoided.
- Unpowered card: the OE pull-up rail is 0 V, so the switches are off.
- Part: **Toshiba SSM6N56FE** (§11.7).

### 11.3 Edge pins for the 12 lines (revised)

| Pins | Host risk (research) | Use |
|---|---|---|
| 59, 61, 63 | antenna-switch inputs / NC on every host found | EXP |
| 30, 32, 34, 36 | SIM socket only; no host source (36 = SIM VCC: never drive it while a SIM is inserted — firmware rule, carrier-only anyway) | EXP |
| 60, 62, 64, 65 | may be driven at 1.8 V by a host WiFi COEX / tuner — fine behind the switch | EXP |
| 40 | GPIO_0 = SIM_DET2 / GNSS_SCL on some hosts — fine behind the switch | EXP (12th) |
| 56, 58 | **Dell Latitude 7x80/7490: 58 = EC debug TX (driven), 56 = PORT80_DET#** | dropped |
| 38, 66, 68 | host-driven DEVSLP / SIM-detect ground / 32 kHz SUSCLK | never |

All host-side levels found are within 0–3.3 V, inside the switch's 0–3.6 V
powered-off rating.

### 11.4 Parts (JLC/LCSC, all **Extended**: JLC Basic has no switch/logic/array parts)

| Function | Part | LCSC | Key verified facts |
|---|---|---|---|
| 12-ch switch | **3× TI TMUX1511** RSV UQFN-16 (or PW TSSOP-14) | C2673275 (RSV, 4.1 k) / C2866750 (PW, 9.6 k) | IPOFF ±2 µA max at VDD = 0 with 3.6 V on I/O; RON 4.5 Ω; COFF 4 pF; passes rail-to-rail; **SELx active-high with internal 6 MΩ pull-down → fail-safe OFF** |
| fallback | 2× SN74CB3Q3245PW | C470961 | Ioff 1 µA, charge-pumped gate; /OE needs pull-up; 85 °C |
| carrier detect + class A | 3× **Toshiba SSM6N56FE** SOT-563 (fallback DMN2004DWK SOT-363) | C146449 (Ext, 7.3 k) | Vth 0.4–1.0 V @ 1 mA, RDS(on) 480 mΩ @ 1.8 V, IGSS ±1 µA @ ±6 V; insulated gates = inherent Ioff |
| series R | 0402 discrete (Basic: 100 Ω C25076 / 220 Ω C25091) or 4×0402 arrays (Ext) | — | |

Rejected:
- TMUX1574: enable is active-low with a pull-down, so it is on by default.
- CB3T3245: clamps to VCC, and its Ioff is 10 µA.
- CBTLV3245: NMOS-only, clips the high level.
- LV1T34: no Ioff spec.
- LVC1G02/32 as the detect gate: thresholds (§11.2).

### 11.4b Class A, lean variant (used by the probe)

Two dual NMOS parts replace three single-gate chips plus their three
decoupling caps:
- **Q2:** open-drain LED_1# and WAKE_ON_WWAN#. Works at any host pull-up
  voltage, can only pull low. Gate pull-downs keep it off during ESP reset.
- **Q3:** W_DISABLE2# input. The gate sits on the edge pin, with a card
  pull-up per spec (1 MΩ). The drain goes to IO1 (inverted logic), with a
  pull-up to 3V3. It reads 1.2/1.8/3.3 V hosts, and the insulated gate
  means no back-feed.

### 11.5 New finding outside the expansion bus: supply up to 4.4 V

M.2 Rev 3.0 labels the supply pins "3.3 V/VBAT", and modems accept
3.135–4.4 V. A tablet-style host may feed **VBAT up to ~4.4 V**. The
ESP32-S3 absolute maximum is 3.6 V, and **v1/rev B has no regulator**
(SPEC §6.2, 3V3 taken directly).
- Laptops, Mallow and the adapters found are 3.3 V, so this is a niche
  host class.
- Still, v2 should consider input OVP: an eFuse/load switch with an OVP
  clamp ≤ 3.6 V, or an LDO with ≤ 3.135 V input headroom (hard).
- *(Not filed in rev-B findings; flag for owner.)*

### 11.6 Rev B observation (unchanged, flagged)

v1/rev B declares CONFIG state 15 "No Module Present". Harmless on
Mallow and on USB adapters (they ignore CONFIG). A CONFIG-aware laptop BIOS
may ignore the slot.

### 11.7 Status of §10 steps

1. Newer pin definitions — **done** (11.1–11.3).
2. Part search — **done**. Dual low-Vth NMOS: **Toshiba SSM6N56FE** (SOT-563, LCSC C146449, Ext, 7.3 k; Vth 0.4–1.0 V @1 mA, IGSS ±1 µA; `research/dual_nmos_research.md`). Fallback DMN2004DWK (SOT-363, C156343).
3. Feasibility probe — see §12.

## 12. Routing feasibility probe on 2242 (2026-10-06)

**Setup** (`probe/`, nothing in `hardware/` touched):
- Rev-B board copy, all rev-B copper locked and unchanged.
- The v2 block (§11 lean variant) is auto-placed into the free **bottom** area.
  That area is under the module, between the antenna keep-out and the TP row.
- 47 new nets.
- Tools:
  - `probe.py` builds the placement.
  - `gridprobe.py` is a sequential grid router (0.05 mm grid, no rip-up,
    JLC 0.127/0.127 mm, 0.45/0.3 vias, hole clearance 0.25 mm). It writes
    real tracks into `probe_<L>L_grid.kicad_pcb`.
- **KiCad DRC is the judge:** both results have **0 copper / hole / keep-out
  violations**.

| Variant | Nets routed | Notes |
|---|---|---|
| 2242, 4 layers (F/B signal) | **17 / 47** | Module↔finger band is the wall. Between module and fingers: J3/J4 on top, TP/diode/cap rows on the bottom, so only two layers can cross it |
| 2242, 6 layers (F/In3/In4/B signal, In1 GND / In2 PWR planes) | **31 / 47** | 9 of 12 EXP lines + WAKE/W_DIS2/both CONFIG senses reach the fingers. Most of the 16 failures are **short local hops** inside the over-packed part cluster (switch ↔ series R, detect FET gates) |

**Freerouting is unusable on this board.** It reports 108 violations on the
*untouched* rev-B board and hits internal errors, so it was replaced by
`gridprobe.py`. This matches the routing-method lesson.

**Reading the result:**
- The probe is pessimistic (sequential, no rip-up, placement not
  routing-aware: the auto-placer packs parts against the antenna keep-out).
- So "routed" means feasible; "failed" doesn't prove infeasible.
- **Not enough on 2242 + 4 L with the rev-B placement frozen.** It is
  doubtful even with re-placement: the module↔finger band would need two
  more crossing layers, or the J3/J4 + TP rows moved.
- **2242 + 6 L is promising.** The edge band opens up. What fails now is
  local congestion that a real (routing-aware) placement normally solves.
  Estimate: feasible with a v2 re-placement *(not proven)*.
- **2252 + 4 L** was not probed. It adds 10 mm of board length, which
  relieves the cluster, but **not the module↔finger band**: the band stays
  between the same parts unless placement changes. Probe it only if 6 L is
  rejected for cost.

**Suggested next step (owner call):**
- Choose 2242 + 6 L as the baseline.
- Treat v2 as a real re-placement on the v2 branch, not a patch on rev B:
  - move the TP row,
  - consider moving J3/J4,
  - give the switch cluster room for UQFN escape.
- Then rerun `gridprobe.py` as the gate before hand-routing.
- **Cost check needed:** JLC 6-layer, 0.8 mm, ENIG + gold fingers vs 4-layer
  *(not quoted yet)*.

Artifacts: `probe/probe_{4,6}L_grid.kicad_pcb` (open in KiCad 9), `probe/grid_{4,6}L_result.txt`, `probe/drc_g{4,6}.json`.

## 13. Cost check (2026-10-07)

### 13.1 Bare PCB — JLCPCB instant quote, read 2026-10-07 (USD, web price)

How the numbers were obtained:
- JLC instant quote form filled by hand: no gerber upload, nothing ordered.
- Options for every variant: 0.8 mm, ENIG 1 U", gold fingers yes, no bevel,
  FR4 TG135, Specify Stackup off, 1 design, single PCB, standard build time.
- 6 layers is JLC's "Advanced PCB" product. 0.8 mm is offered with ready
  6-layer stackups (JLC06081H-2116 / -2313 / -7628 / -1080 …), and epoxy
  filled & capped vias are included at no extra cost.

| Variant | 5 pcs | 100 pcs | Δ vs baseline / board @ 100 |
|---|---|---|---|
| **2242, 4 L** (rev-B baseline) | **$24.80** | **$60.04** | — |
| 2242, 6 L | $48.80 | $115.60 | **+$0.56** |
| 2252, 4 L | $28.12 ¹ | $63.09 | +$0.03 |

¹ This includes $3.32 for "via plating method", an option the form carried
over from the 100-pcs run. On a like-for-like basis, 2252 costs the same
as 2242 at 5 pcs.

The 2242 4 L number matches the real rev-B order: PCB €23.34 for 5 pcs
(BUSINESS_EVAL_PROMPT.md).

The 100-pcs breakdown, single boards (not panelized):
- 6 L: engineering $66, ENIG $18.70, test $17.40, board $10.70, deburr $2.30, film $0.50.
- 4 L: engineering $25, ENIG $18.70, board $9.30, via plating $3.54, deburr $2.30, test $0.80.

**Reading:**
- **6 layers costs +$24 per prototype order** (+$4.80/board at 5 pcs).
- At volume it is **+$0.56/board**, which is noise next to the ~€6 component cost.
- 2252 is cost-neutral on the PCB.
- So the board-size choice is mechanical/marketing (42 vs 52), not cost.
- Assembly is unaffected by layer count (same stencil, same placement).

### 13.2 v2 BOM delta and OVP (JLC USD, 2026-10-07; `research/ovp_and_prices.md`)

**Expansion bus + host-facing pins** (the §11 lean variant, as placed in the probe):

| Item | Qty/board | @10 | @100 |
|---|---|---|---|
| TMUX1511RSVR (C2673275, Ext) | 3 | $1.57 | $1.20 |
| SSM6N56FE (C146449, Ext) | 3 | $0.61 | $0.49 |
| Passives (3× 1 MΩ, ~6× 100 kΩ, 12× 220 Ω, 4× 100 nF; all Basic) | ~25 | $0.08 | $0.08 |
| Placement (~28 extra parts, ≈ €0.011/part from the rev-B quote) | | ~$0.33 | ~$0.33 |
| **Total per board** | | **≈ $2.6** | **≈ $2.1** |

- New BOM lines: 2 ICs + up to 4 passive values, at €1.38 per line per order,
  so **≈ €5.5–8.3 per order**.
- Use 0603 like the rev-B BOM, where the 100 nF line already exists, to save
  one or two lines.
- The TSSOP-14 TMUX1511PWR is cheaper ($0.29 @100) but larger. Area is the
  constraint here, so keep the UQFN.

**Input OVP — recommended: TI TPS259470A eFuse** (C3662799; same footprint
TPS259474L C2864845 has more stock):
- **Trip point:** OVLO divider 100 k / 51 k (Basic) trips at 3.55 V typ.
  - Worst case with 1 % resistors is 3.46–3.67 V, which can sit ~70 mV above
    the ESP's 3.6 V absolute maximum. 0.1 % resistors give 3.47–3.63 V.
  - Recovers automatically at ~3.23 V (not latched).
- **Drop:** RON 45 mΩ max, so ≤ 22.5 mV at 0.5 A.
  - Worst case at the module on a 3.135 V host: 3.135 − 0.0225 − 0.075 (FB1)
    = **3.04 V**, above the 3.0 V minimum but with little margin.
  - Dropping FB1 would gain 75 mV.
- **On a 4.4 V host the card stays off safely.** It survives 5 V and more
  (VIN absolute max 28 V).
- **Cost:** ≈ **$0.81/board @100**, $1.07 @10. Up to 4 new BOM lines
  (≈ €5.5/order). ≈ 16 mm² (2×2 VQFN + 3 R + 1 C).

**Rejected:**
- LDO: from a 3.135 V host the module sees < 3.0 V.
- TVS/crowbar: would short a legitimate 4.4 V rail.
- Phone OVP switches: lowest threshold 4 V.
- Voltage-clamp eFuses: clamp at 3.8–4.2 V.
- Buck-boost: TPS63802, ~$0.61 plus 35–50 mm² and a switcher next to the
  antenna.

### 13.3 Totals vs rev B

| | Per board @100 | Per 5-pc prototype order |
|---|---|---|
| 6 L instead of 4 L | +$0.56 | +$24 |
| Expansion bus + host pins | +$2.1 | +$13 parts + ≈ €8 feeders |
| OVP eFuse | +$0.81 | +$5.4 parts + ≈ €5.5 feeders |
| **v2 total delta** | **≈ +$3.5 / board** | **≈ +$55–60 / order** |

- Rev-B reference (BUSINESS_EVAL_PROMPT.md): ≈ €9–10/board at 100 pcs and
  ≈ €190 per 5-pc order landed.
- So v2 is roughly **+35 % per board at volume**, and +30 % on a prototype
  order.
- OVP on its own is ≈ +8 % per board at volume.
- 2252 instead of 2242 is cost-neutral.

## 14. Owner decisions 2026-10-07

- **Form factor: 2242, 6 layers** (SIG / GND / SIG / SIG / PWR / SIG — exact
  stackup TBD from the JLC06081H family).
  - Reason: the small card looks more attractive.
  - A future "plus" model may use 2252 or 2260.
  - Feasibility rests on the §12 probe plus a routing-aware re-placement. It
    is not proven yet; the gate is `gridprobe.py` passing 47/47.
- **Input OVP: yes, done properly.** TPS259470A eFuse (§13.2).
  - Use **0.1 % OVLO divider resistors**, so the worst-case trip stays at or
    below ~3.63 V.
  - Revisit dropping FB1 (+75 mV margin on weak hosts).
- **CONFIG state 6** (approved earlier, §11.1).
