# Pin map — esp32-m2-companion (GATE 1 deliverable)

Status: **draft for owner review** · 2026-08-28

Sources (see `docs/datasheets/README.md` for provenance):
- **[MALLOW]** Mallow Carrier Board V1.1 datasheet, Table 10 (M.2 X17), Table 22 (X16), §2.5.2
- **[KEYB]** Quectel RM50xQ HW Design V1.2, Fig. 2 / Table 8 (standard WWAN Key-B socket usage)
- **[WROOM]** ESP32-S3-WROOM-1 datasheet v1.8, Table 3-1, §4
- **[HDG]** ESP32-S3 Hardware Design Guidelines (master), §power-up & reset

---

## 1. M.2 Key-B edge connector — full pin table

Notation: card edge has 75 positions; positions 12–19 are the Key-B notch
(no pins). Odd pins on top row, even on bottom row per M.2 convention.
"—" = not present in Mallow Table 10 ⇒ not connected on Mallow.

Directions ("I/O") are from the **card's** point of view.

| Pin | M.2 WWAN function [KEYB] | Mallow X17 wiring [MALLOW] | Our usage |
|----:|---|---|---|
| 1 | CONFIG_3 | NC | NC |
| 2 | VCC (3.3 V) | +V3.3_PCIE_1 | **3V3 in** |
| 3 | GND | GND | GND |
| 4 | VCC (3.3 V) | +V3.3_PCIE_1 | **3V3 in** |
| 5 | GND | GND | GND |
| 6 | FULL_CARD_POWER_OFF# | PCIE_1_CARD_PWR_OFF#, +1.8/+3.3 V, driver not documented (no SODIMM pin) | NC in v1 (see §3.4) |
| 7 | USB_DP | USBH3_D_P (USB5744 hub port 3) | **USB D+ → IO20** (via ESD array) |
| 8 | W_DISABLE1# | 47 kΩ pull-up to +V3.3_PCIE_1 only — **not SoM-driven** | **NC in v1** — exposed edge finger, no on-card connection. BOOT leg dropped (ADR 0002 amendment); recovery via TP1/TP2 (§3) |
| 9 | USB_DM | USBH3_D_N (USB5744 hub port 3) | **USB D− → IO19** (via ESD array) |
| 10 | WWAN_LED# | PCIE_1_GPIO_9 → X16 pin 15 | NC |
| 11 | GND | GND | GND |
| 12–19 | — notch — | — notch — | — notch — |
| 20 | PCM_CLK / GPIO | PCIE_1_GPIO_5 → X16 pin 19 | **BOOT# input** via Schottky diode (Mallow path; see §3) |
| 21 | CONFIG_0 | NC | NC |
| 22 | PCM_DIN / GPIO | PCIE_1_GPIO_6 → X16 pin 18 | NC (spare sideband) |
| 23 | WAKE_ON_WAN# / GPIO | PCIE_1_GPIO_11 → X16 pin 13 | NC |
| 24 | PCM_DOUT / GPIO | PCIE_1_GPIO_7 → X16 pin 17 | NC (spare sideband) |
| 25 | DPR | NC | NC |
| 26 | W_DISABLE2# | PCIE_1_GPIO_10 → X16 pin 14 | NC |
| 27 | GND | GND | GND |
| 28 | PCM_SYNC / GPIO | PCIE_1_GPIO_8 → X16 pin 16 | NC |
| 29 | USB_SS_TX_M | USBH3_SSRX_N ¹ | NC |
| 30 | UIM1_RST | PCIE_1_UIM_RESET | NC |
| 31 | USB_SS_TX_P | USBH3_SSRX_P ¹ | NC |
| 32 | UIM1_CLK | PCIE_1_UIM_CLK | NC |
| 33 | GND | GND | GND |
| 34 | UIM1_DATA | PCIE_1_UIM_DATA | NC |
| 35 | USB_SS_RX_M | USBH3_SSTX_N ¹ | NC |
| 36 | UIM1_VDD | PCIE_1_UIM_PWR | NC |
| 37 | USB_SS_RX_P | USBH3_SSTX_P ¹ | NC |
| 38 | SDX2AP_STATUS | NC | NC |
| 39 | GND | GND | GND |
| 40 | (U)SIM2 / GPIO | PCIE_1_GPIO_0 → X16 pin 24 | NC |
| 41 | PCIE_TX_M ² | PCIE_1_L0_RX_N ² | NC |
| 42 | (U)SIM2 / GPIO | PCIE_1_GPIO_1 → X16 pin 23 | NC |
| 43 | PCIE_TX_P ² | PCIE_1_L0_RX_P ² | NC |
| 44 | (U)SIM2 / GPIO | PCIE_1_GPIO_2 → X16 pin 22 | NC |
| 45 | GND | GND | GND |
| 46 | (U)SIM2 / GPIO | PCIE_1_GPIO_3 → X16 pin 21 | NC |
| 47 | PCIE_RX_M ² | PCIE_1_L0_TX_N ² | NC |
| 48 | (U)SIM2 / GPIO | PCIE_1_GPIO_4 → X16 pin 20 | NC |
| 49 | PCIE_RX_P ² | PCIE_1_L0_TX_P ² | NC |
| 50 | PERST# (PCIE_RST_N) | PERST#, **SODIMM 244**, input to card, OD, 10 kΩ pull-up to +V3.3_PCIE_1 | **EN (reset) input** via Schottky diode (see §3) |
| 51 | GND | GND | GND |
| 52 | PCIE_CLKREQ_N | NC | NC |
| 53 | PCIE_REFCLK_M | PCIE_1_CLK_N | NC |
| 54 | PCIE_WAKE_N | PCIE_1_WAKE#, SODIMM 252, 10 kΩ PU to +V1.8 | NC (1.8 V domain — do not touch) |
| 55 | PCIE_REFCLK_P | PCIE_1_CLK_P | NC |
| 56 | RFFE_CLK | NC | NC |
| 57 | GND | GND | GND |
| 58 | RFFE_DATA | NC | NC |
| 59 | LAA_TX_EN / ANT | NC | NC |
| 60 | WLAN_TX_EN | NC | NC |
| 61 | ANTCTL1 | NC | NC |
| 62 | COEX_RXD | NC | NC |
| 63 | ANTCTL2 | NC | NC |
| 64 | COEX_TXD | NC | NC |
| 65 | RFFE_VIO_1V8 | NC | NC |
| 66 | UIM1_DET | PCIE_1_UIM_CD | NC |
| 67 | RESET# | M.2_CARD_RESET#, **+1.8 V domain**, driver not documented (no SODIMM pin) | NC in v1 (see §3.4) |
| 68 | AP2SDX_STATUS | NC | NC |
| 69 | CONFIG_1 | NC | NC |
| 70 | VCC (3.3 V) | +V3.3_PCIE_1 | **3V3 in** |
| 71 | GND | GND | GND |
| 72 | VCC (3.3 V) | +V3.3_PCIE_1 | **3V3 in** |
| 73 | GND | GND | GND |
| 74 | VCC (3.3 V) | +V3.3_PCIE_1 | **3V3 in** |
| 75 | CONFIG_2 | not listed in Mallow Table 10 | NC |

¹ Naming is host-referenced on Mallow, card-referenced in [KEYB]; TX/RX pair
directions are consistent between the two once that is accounted for.
² Same host/card naming inversion for the PCIe lane.

Power notes:
- +V3.3_PCIE_1: Mallow's 3V3 DC-DC is rated 7 A board-total (Table 4) —
  ESP32-S3 WiFi TX bursts (~0.5 A) are comfortably inside slot budget.
- Card power = 5 × VCC pins, 11 × GND fingers. Input filter per SPEC §6.2.
- Note [KEYB] modem VCC is 3.135–4.4 V (modem-specific); the *socket* rail on
  both our hosts is 3.3 V, which is what we design to.

## 2. ESP32-S3-WROOM-1 pin allocation

Module: **ESP32-S3-WROOM-1-N8R2** (LCSC C2913204, in stock ~9.8 k on
2026-08-28). Quad-SPI PSRAM ⇒ IO35–37 are *available* on N8R2, but they stay
**unused** so the N16R8 (octal, IO35–37 reserved) fallback stays drop-in
compatible [WROOM Table 1-1, note b].

| Mod. pin | Name | Chip fn (default) [WROOM] | Our usage | Notes |
|---:|---|---|---|---|
| 1 | GND | — | GND | |
| 2 | 3V3 | — | 3V3 rail | 2×22 µF bulk + 100 nF/pin per [HDG] |
| 3 | EN | CHIP_PU | **Reset**: 10 kΩ PU to 3V3 + 1 µF to GND (RC per [HDG] §1.3.3), Schottky from M.2 pin 50, test point | Do not float; VIL_nRST = 0.25·VDD |
| 4 | IO4 | GPIO4/ADC1_CH3 | spare (test point optional) | |
| 5 | IO5 | GPIO5 | spare | |
| 6 | IO6 | GPIO6 | spare | |
| 7 | IO7 | GPIO7 | spare | |
| 8 | IO15 | GPIO15/XTAL_32K_P | spare | |
| 9 | IO16 | GPIO16/XTAL_32K_N | spare | |
| 10 | IO17 | GPIO17/U1TXD | spare | |
| 11 | IO18 | GPIO18/U1RXD | spare | |
| 12 | IO8 | GPIO8 | **Header: I2C SDA** | opt. pull-up footprint, DNP |
| 13 | IO19 | **USB_D−** | **M.2 pin 9** via USBLC6 | native USB-Serial-JTAG |
| 14 | IO20 | **USB_D+** | **M.2 pin 7** via USBLC6 | native USB-Serial-JTAG |
| 15 | IO3 | GPIO3, strapping (JTAG src) | NC | leave floating [WROOM §4] |
| 16 | IO46 | GPIO46, strapping (boot/ROM log) | NC | weak PD default = SPI boot ✔ |
| 17 | IO9 | GPIO9 | **Header: I2C SCL** | opt. pull-up footprint, DNP |
| 18 | IO10 | GPIO10/FSPICS0 | **Header: GPIO / SPI CS** | native FSPI set |
| 19 | IO11 | GPIO11/FSPID | **Header: GPIO / SPI MOSI** | |
| 20 | IO12 | GPIO12/FSPICLK | **Header: GPIO / SPI CLK** | |
| 21 | IO13 | GPIO13/FSPIQ | **Header: GPIO / SPI MISO** | |
| 22 | IO14 | GPIO14/FSPIWP | **Header: GPIO** | |
| 23 | IO21 | GPIO21 | **Header: GPIO** | RTC-capable |
| 24 | IO47 | GPIO47 | spare | |
| 25 | IO48 | GPIO48 | **Status LED** (active-low, side-view red at left card edge, ADR 0003) | devkit precedent for RGB on IO48 |
| 26 | IO45 | GPIO45, strapping (VDD_SPI) | NC | weak PD default = 3.3 V flash ✔ |
| 27 | IO0 | GPIO0, strapping (boot) | **BOOT#**: 10 kΩ PU to 3V3, Schottky diode from M.2 pin 20, test point TP2 | weak PU default = SPI boot |
| 28 | IO35 | GPIO35 (octal-PSRAM res.) | NC | variant compat |
| 29 | IO36 | GPIO36 (octal-PSRAM res.) | NC | variant compat |
| 30 | IO37 | GPIO37 (octal-PSRAM res.) | NC | variant compat |
| 31 | IO38 | GPIO38 | spare | |
| 32 | IO39 | GPIO39/MTCK | spare (JTAG) | |
| 33 | IO40 | GPIO40/MTDO | spare (JTAG) | |
| 34 | IO41 | GPIO41/MTDI | spare (JTAG) | |
| 35 | IO42 | GPIO42/MTMS | spare (JTAG) | |
| 36 | RXD0 | GPIO44/U0RXD | **Header: UART RX** | ROM boot log lands here too |
| 37 | TXD0 | GPIO43/U0TXD | **Header: UART TX** | |
| 38 | IO2 | GPIO2 | spare | |
| 39 | IO1 | GPIO1 | spare | |
| 40 | GND | — | GND | |
| 41 | EPAD | — | GND, ≥9 vias [HDG] | |

### IO header (12 pins, 2.54 mm, unpopulated)

`3V3 · GND · IO8/SDA · IO9/SCL · IO43/TX · IO44/RX · IO10/CS · IO11/MOSI · IO12/CLK · IO13/MISO · IO14 · IO21`

- Full native (IOMUX) FSPI set among header GPIOs (IO10–13) → SPEC G3 ✔.
- No strapping pins, no octal-PSRAM pins, no USB pins on the header.
- UART on header = UART0: doubles as fallback ROM-bootloader/console path.

## 3. Recovery scheme (SPEC §6.4)

### 3.1 Chosen sideband mapping

| Card signal | M.2 pin | Why |
|---|---|---|
| **EN** | 50 (PERST#) | Only sideband Mallow wires to a SoM pin out of the box (SODIMM 244, OD + 10 k→3.3 V on carrier). Semantically "card reset" on every host family. |
| **BOOT (GPIO0)** | 20 (Mallow: X16.19 jumper) | pin 20 via the X16 jumper covers Mallow. The pin-8 (W_DISABLE#) diode-OR leg was **dropped in v1** (ADR 0002 amendment): unroutable in the dense pin 7/8/9 corner and redundant — BOOT is on TP2, so non-Mallow hosts recover by flying-lead on TP1(EN)+TP2(BOOT). |

### 3.2 Level-domain problem and the diode solution

Verdin GPIOs are **1.8 V** and not 3.3 V-tolerant; our EN/BOOT nets are pulled
to 3.3 V. Also, an unknown host may drive sidebands push-pull at 1.8 V.
Therefore every sideband input goes through a small-signal Schottky
(anode = card net, cathode = M.2 pin):

- Host (any voltage, push-pull or OD) pulls low → card net ≈ V_OL + V_f
  ≤ ~0.5 V < VIL (0.825 V @3.3 V) ✔
- Host Hi-Z or open-drain released → diode blocks, card net sits at 3.3 V via
  its own 10 kΩ, host pin never sees 3.3 V ✔
- **Constraint (GATE 2 review finding):** a host driving a sideband
  *push-pull HIGH below ~2.8 V* (e.g. 1.8 V) forward-biases the diode
  (~125 µA) and drags the card net to ~2.0–2.1 V — inside the undefined
  input band. Host sidebands must idle open-drain/Hi-Z, or push-pull with
  V_OH ≥ ~2.8 V. Recovery flows must *release* BOOT/EN to input/Hi-Z
  (`gpioset` back to input), never drive them high. Mallow's documented
  paths satisfy this (PERST# is OD; pin 20 is open until jumpered).
- Card unplugged / sideband unconnected → normal boot ✔ (SPEC §6.4 satisfied)

Trade-off: host can only assert (pull low), never drive high — which is all
the recovery flow needs. With 10 kΩ pull-ups, diode forward current ≈ 0.3 mA
⇒ V_f ≈ 0.2–0.3 V (BAT54-class).

EN keeps the [HDG] RC (10 kΩ + 1 µF); a host reset pulse of ≥ a few ms
discharges the 1 µF through the diode — trivial with `gpioset`.

### 3.3 Resulting flows

- **Normal flash**: `esptool.py` auto-reset over USB-Serial-JTAG. No GPIO.
- **Brick recovery (Mallow)**: jumper X16.19 → chosen Verdin GPIO (one-time
  bench setup). Then: hold BOOT low (that GPIO), pulse PERST# (SODIMM 244)
  low ≥ 5 ms, release → ROM `Joint Download Boot` [WROOM Table 4-3] →
  `esptool.py` over the same USB port → flash → release BOOT.
- **Brick recovery (RPi5/Waveshare HAT)**: sideband wiring unpublished;
  best-effort per SPEC. If the HAT drives nothing, recovery needs a flying
  lead to the card's EN/BOOT test points — which is why both get test points.

### 3.4 Rejected candidates (documented per SPEC §6.4)

- **Pin 67 RESET#**: 1.8 V domain on Mallow and no documented driver — can't
  rely on it. Left NC (safe: our nets don't touch it).
- **Pin 6 FULL_CARD_POWER_OFF#**: no documented driver on Mallow; standard
  meaning is "power the card off", which modems implement in the PMIC — we
  have no power switch in v1 (SPEC: no regulator). Left NC.

## 4. USB detail

- M.2 7/9 → USBLC6-2 array (close to edge fingers) → IO20/IO19.
  90 Ω diff pair, length-matched, solid L2 GND reference, no stubs.
- Polarity: pin 7 = D+ = IO20, pin 9 = D− = IO19 [MALLOW T.10, WROOM T.3-1].
- On Mallow the port is behind a USB5744 hub (port 3) — enumeration
  expectation in `docs/bringup.md` should mention the hub in `lsusb -t`.

## 5. GATE 1 outcomes (2026-08-28)

1. BOOT: pin 20 only (Mallow). Pin-8 diode-OR leg **dropped in v1** → ADR 0002 amendment (2026-08-30); recovery on other hosts via TP1/TP2.
2. Status LED: **plain LED on IO48** → ADR 0003.
3. SODIMM 244 as GPIO: **verified in mainline device trees** for Verdin
   iMX8MP/iMX8MM (claimed by PCIe node — free it with an overlay) and AM62
   (free by default). Per-SoM table in ADR 0002; exact steps for the owner's
   SoM go into `docs/bringup.md` (Phase 4).
4. RPi5: **demoted to nice-to-have** → ADR 0004 (risk R4 accepted).

Still open (not blocking Phase 1):
- ST vs UMW for the USB ESD array — decide at BOM review (Phase 1 / GATE 2);
  if ST, owner drops the ST PDF into `docs/datasheets/`.
- M.2 2242 mechanical outline source for Phase 2 (licensed M.2 EM spec or
  verified derived drawing) — needed before GATE 3, not before schematic.
