# v2.0 Rev A — GATE V1 package (circuit values, ID EEPROM format, BOM delta)

Status: **approved 2026-10-07 (owner, OVLO 100 k / 52.3 k)** · Pin allocation: `docs/pinmap.md` §6 ·
Decisions behind it: SPEC A3, ADR 0006–0008 · Contract: `docs/carrier-interface.md`

---

## 1. Circuit values

### 1.1 Carrier detect → `EXP_OE` (ADR 0006 §2)

Per sense pin (CONFIG_2 = 75, CONFIG_3 = 1):

```
edge pin ──┬── R 1 MΩ ── 3V3          (card pull-up: floating host reads "not carrier")
           └── R 100 kΩ ── gate Qd(a/b)   (SSM6N56FE, source GND)
Qd drains (a ∥ b) ── EXP_OE ──┬── R 10 kΩ ── 3V3
                              ├── C 1 µF ── GND        (τ ≈ 10 ms)
                              ├── 12× TMUX1511 SEL (3 chips × 4)
                              └── IO38 (readback)
```

- **Pull-up is 10 kΩ, not the 100 kΩ in the brainstorm/probe. This is a finding from [TMUX1511]
  §5.5.**
  - Each SEL pin has IIH up to ±2 µA plus a 6 MΩ internal pull-down.
  - 12 SEL pins in parallel draw up to 24 µA + 6.6 µA.
  - Through 100 kΩ that drops ~3 V, so OE would sit near 0.3 V worst case. VIH is 1.2 V min:
    the bus would never turn on.
  - With 10 kΩ the drop is ≤ 0.31 V, so OE ≥ 2.99 V.
  - The FET then sinks 0.33 mA when on, which is trivial for the SSM6N56FE (RDS(on) ≤ 480 mΩ at
    VGS 1.8 V). OE low is then ≈ 0 V, below VIL 0.45 V.
- **Gate drive:**
  - 1.8 V host pull-up: VGS ≈ 1.8 V > VGS(th) max 1.0 V → on.
  - Floating: gate ≈ 3.3 V via 1.1 MΩ → on.
  - Carrier GND: 0 V → off.
  - IGSS ±1 µA × 100 kΩ = ±0.1 V, negligible.
- **Unpowered card:** the 3V3 rail is 0, so OE = 0 and the switches are off (their RPD holds
  them). A host pull-up only charges an insulated gate, so there is no back-feed.
- **Timing:** τ ≈ 10 ms (10 k × 1 µF) after 3V3 rises.
  - The FET gates settle in ~0.1 ms (1.1 MΩ × gate C).
  - TMUX tON(VDD) is 20–60 µs.
  - So the bus can only enable well after the rails are stable. No EXP line is a strapping pin,
    so a carrier cannot disturb boot.

### 1.2 Expansion lines

- **12 × 220 Ω** series, ESP side of the switch. Use 3 × 4×0402 arrays
  (4D02WGJ0221TCE, C25498, Ext) — area on 2242 matters more than one BOM line.
- **EXP_0/EXP_1 (I²C):** 4.7 kΩ pull-ups to 3V3 on the **MCU side of the switch**.
  - With the switch off they are isolated from the edge, so the "high-Z when off" promise holds.
  - With the switch on they pull up the carrier bus.
  - The brainstorm said "card side behind the switch"; this is the corrected position.
- **3 × 100 nF** (one per TMUX1511 VDD).

### 1.3 Host-facing cells (ADR 0006 §4)

| Cell | Parts | Values |
|---|---|---|
| Q2a: LED_1# (10) ← IO42 | SSM6N56FE half | gate pull-down 100 kΩ (off while the ESP is in reset / IO floating) |
| Q2b: WAKE_ON_WWAN# (23) ← IO47 | SSM6N56FE half | gate pull-down 100 kΩ |
| Q3a: W_DISABLE2# (26) → IO40 | SSM6N56FE half, gate on the edge pin | edge pull-up **1 MΩ** to 3V3 (spec: "pull-up on the card"; ≤ 1.5 µA into a 1.8 V host); drain pull-up **10 kΩ** to 3V3 → IO40 reads **inverted** (low = radio allowed) |
| Q3b | spare half | gate tied to GND |

### 1.4 Input OVP (ADR 0007) — **owner decision needed: trip-point trade-off**

TPS259470A (C3662799); VOV(R) = 1.183 / 1.20 / 1.223 V [research `ovp_and_prices.md`, TI datasheet].
ILM 3.3 kΩ → 0.85–1.15 A. EN/UVLO tied to IN, DVDT/ITIMER open, CIN 100 nF.

**The window can't be met both ways.**
- The legal host maximum is **3.465 V**; the ESP absolute maximum is **3.6 V**. That's a 135 mV
  window.
- The OVLO reference tolerance alone spans ±1.7 % (≈ ±60 mV at 3.55 V), before resistors.

| Divider (0.1 %) | Trip window | Risk |
|---|---|---|
| 100 k / 51.0 k | 3.50 – **3.63 V** | worst-case part lets a 3.62 V rail through (≤ 30 mV over abs max) |
| **100 k / 52.3 k (recommended)** | 3.44 – 3.57 V | never above 3.6 V. A worst-case part may trip on a host at its +5 % limit (3.44–3.465 V); real 3.3 V rails sit far below. Falling (re-enable) threshold 1.09 V × 2.91 ≈ 3.17 V |

Recommendation: **52.3 k**. Damage beats nuisance: a card that turns off on an out-of-tolerance
3.47 V rail is preferable to an ESP32 run 20 mV above absolute maximum. If you prefer the other
side, say so.

- **FB1:** replace the rev-B ferrite (C1015, 150 mΩ DCR) with a ≤ 50 mΩ DCR bead (part at
  GATE V2).
  - That gains ~50 mV, so the worst case at the module on a 3.135 V host becomes ≈ 3.09 V
    instead of 3.04 V.

## 2. Carrier ID EEPROM — format v1 (proposed)

- **Part on the carrier:** 24C02-class, 256 B, I²C **0x50** (A2..A0 = GND), on EXP_0 (SDA) /
  EXP_1 (SCL). WP to GND via a 0 Ω/jumper (production) or a jumper (dev).
- **Firmware rule (normative):**
  - After `EXP_OE` reads high, initialise **only** EXP_0/1 (I²C).
  - Keep EXP_2..11 high-Z until the EEPROM gives a valid magic **and** CRC.
  - With no EEPROM, a bad CRC or an unknown format → "unknown carrier": every line stays an
    input; the host may override explicitly (dev use).

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

Function codes:
- 0x00 unused (stay high-Z)
- 0x01 digital in
- 0x02 digital in + pull-up
- 0x03 digital in + pull-down
- 0x04 push-pull out (param = default level)
- 0x05 open-drain out
- 0x06 analog in
- 0x07/0x08 I²C SDA/SCL (EXP_0/1 always)
- 0x09/0x0A UART TX/RX (param = port)
- 0x0B–0x0E SPI SCK/MOSI/MISO/CS
- 0x0F PWM (param = channel)
- 0x10 WS2812/RMT data
- 0x80–0xFF vendor-defined

Firmware refuses functions a line can't do (e.g. analog on a non-ADC line).

## 3. BOM delta vs Rev B (new lines; prices JLC 2026-10-07 @100)

| Ref (prov.) | Part | LCSC | B/E | Qty | Justification (Extended) |
|---|---|---|---|---|---|
| U3–U5 | TI TMUX1511RSVR, UQFN-16 | C2673275 | Ext | 3 | no Basic analog switch; needs powered-off protection + fail-safe SEL (ADR 0006) |
| Qd, Q2, Q3 | Toshiba SSM6N56FE,LM, SOT-563 | C146449 | Ext | 3 | no Basic dual NMOS with VGS(th) ≤ 1.0 V |
| U6 | TI TPS259470ARPWR, VQFN-10 | C3662799 | Ext | 1 | no Basic eFuse with adjustable OVLO (ADR 0007). 2nd source TPS259474LRPWR C2864845 |
| RN1–RN3 | 4× 220 Ω 0402 array | C25498 | Ext | 3 | area on 2242 (vs 12 discrete) |
| R | 1 MΩ 0402 | C26083 | Basic | 3 | |
| R | 100 kΩ 0402 | C25741 | Basic | 4 (detect gate series ×2, Q2 gate pull-downs ×2) | |
| R | 4.7 kΩ 0402 | *at V2* | Basic | 2 | |
| R | 3.3 kΩ 0402 | C25890 | Basic | 1 (ILM) | |
| R | OVLO divider 100 k + 52.3 k **0.1 %** | *at V2* | Ext | 2 | 0.1 % needed for the §1.4 window |
| R/C reuse | 10 kΩ (C25804), 100 nF (C14663), 1 µF (C15849) — **existing Rev-B 0603 lines** | | Basic | 3+4+1 | reuse = no extra feeder fee |
| FB1 | low-DCR ferrite (replaces C1015) | *at V2* | — | 1 | |

- New BOM lines ≈ 9 (≈ €12.4 feeder fees per order).
- Silicon + arrays ≈ $1.20 + 0.49 + 0.80 + 0.05 ≈ **$2.55/board @100**, plus passives and
  placement ≈ **$2.9**.
- With the 6-layer delta: ≈ **+$3.5/board**, in line with the brainstorm §13.

## 4. Decisions needed at this gate

1. **OVLO trip point** (§1.4): 52.3 k (recommended, never > 3.6 V) or 51 k.
2. **Pin allocation** (`docs/pinmap.md` §6): approve as proposed.
3. **ID EEPROM format v1** (§2) and the firmware rule.
4. **EXP_0/EXP_1 permanently I²C** (4.7 k pull-ups on the card): OK?
5. BOM approach: arrays for the series R, reuse of 0603 lines.

On approval: `docs/carrier-interface.md` items move from *proposed* to *fixed*. Then GATE V2
(schematic).
