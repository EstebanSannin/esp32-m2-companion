# M.2 Socket 2 (Key B): what each card-edge pin means and what hosts actually put on it

Research date 2026-10-06. Scope: Key-B card-edge pins 1, 21, 69, 75 (CONFIG), 25, 30, 32, 34, 36, 38,
56, 58–66, 68. **Direction is from the CARD's side.** "Host action" says whether any known host or adapter
drives the pin, ties it to a rail or ties it to GND.

## Sources (IDs used in the tables)

| ID | Source | Where |
|----|--------|-------|
| S10 | PCI-SIG M.2 spec **Rev 1.0** (2013), local `docs/datasheets/m2_em_spec_rev1.0_2013_archive.pdf` | Table 25 (p.118–120), §3.2.11–3.2.12 + Table 27 (p.128–130), Table 29 (p.131–132), Table 32 (p.135), Table 47 (p.154, platform view) |
| S30 | congatec **AN43** "M.2 Pinout Descriptions and Reference Designs" (2020), *states it is based on M.2 Spec **Rev 3.0 Ver 1.2***. https://www.congatec.com/fileadmin/user_upload/Documents/Application_Notes/AN43_M.2_Pinout_Descriptions_and_Reference_Designs.pdf | §3.1 pinout (p.8), §3.1.1 CONFIG table (p.9), Fig.2 reference design (p.10), §3.3 notes (p.11) |
| SQ1 | Quectel RM50xQ HW Design V1.2 (local `docs/datasheets/quectel_rm50xq_hardware_design_v1.2.pdf`) | Table 8 pin description (p.23–27), §4.5.5 DPR, §4.5.6 STATUS, §4.6 COEX, Table 27 antenna tuner, §4.8 Tables 28/29 + Fig.25 (p.55–57) |
| SQ2 | Quectel RM520N Series HW Design V1.3. https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/6382/Quectel_RM520N_Series_Hardware_Design_V1.3.pdf | pin assignment figure, pin table, Tables 29/30 (p.56–57) |
| ST | Telit FN990 Family HW Design Guide 1VV0301752 Rev 9 (2024-05-29). https://fccid.io/RI7FN990A28/User-Manual/Hardware-Design-Guide-7366516.pdf | Table 6 config pins (p.14), Table 13 pin-out (p.20–23) |
| SS | Sierra Wireless AirPrime EM7455 PTS rev 9. https://media.digikey.com/pdf/Data%20Sheets/Sierra%20Wireless%20PDFs/EM7455_Spec_Guidelines_rev9_7-31-16.pdf | Table 3-1 host interface (p.~28–30), audio table (I2C on 56/58), DPR §(p.57) |
| SC | SIMCom SIM8200EA-M2 HW Design V1.03. https://files.waveshare.com/upload/d/de/SIM8200EA-M2_Hardware_Design_V1.03.pdf | pin description (p.15–17), §3.11 Tables 29/30 (p.40) |
| SATA | SATA-IO TPR053 v11 "M.2 Card Format for SSDs" (2013). https://sata-io.org/sites/default/files/TP_053v11_SATA31_Mdot2_Card_Format_for_SSDs.pdf | pin lists (MFG1/2 "no connect on a host"), Table 5 electrical (VIH 2.0–3.6 V; VIL −0.5…0.5 V on CONFIG) |
| HW1 | **Waveshare "USB TO M.2 B KEY"** (M.2-to-USB3 dongle) schematic. https://files.waveshare.com/upload/4/4d/USB_TO_M.2_B_KEY_Sch.pdf (wiki https://www.waveshare.com/wiki/USB_TO_M.2_B_KEY) | single sheet, M.2 connector + SIM card block |
| HW2 | Waveshare SIM8200/RM5xx M.2 4G/5G HAT schematic. https://files.waveshare.com/upload/4/4d/SIMXXXX-M2_4G5G_HAT_SCH.pdf | M.2 symbol |
| HW3 | **sysmocom/Osmocom ngff-breakout** (M.2 WWAN to USB3, CC-BY-SA, Eagle source). https://gitea.osmocom.org/electronics/osmo-small-hardware/src/branch/master/ngff-breakout ; product page https://sysmocom.de/products/lab/m2_wwan_modem_breakout/index.html | `ngff-breakout.sch` (netlist parsed) |
| HW4 | Geniatech Jetson Orin NX/Nano carrier V1.0 (2025-01-07), "20_M.2 KEY-B (5G module)" sheet, posted on NVIDIA forum: https://cdck-file-uploads-global.s3.dualstack.us-west-2.amazonaws.com/nvidia/original/4X/9/8/f/98f697a7818f2cf5e0706aef82cae22422d3f9c7.pdf | p.20 |
| HW5 | **Dell Latitude 7280/7380/7480/7490** WWAN slot schematic excerpt (Compal-style), shown in https://www.mattmillman.com/does-the-dell-latitude-m-2-wwan-socket-have-the-sata-interface-on-it/ (image `.../2019/07/latitudem2slot.png`, `hca.png`) | the symbol uses Bellwether 80149 internal numbering = M.2 pin − 8 above the key; mapping checked against CONFIG_0→21, WAKE→23, CONFIG_1→69, CONFIG_2→75, 3.3 V→70/72/74 |
| HW6 | Toradex Mallow carrier V1.1 datasheet (local `docs/datasheets/mallow-carrier-board-datasheet.pdf`) | Table 10, X17 (p.15–17) |
| NV | NVIDIA forum "M.2 Key B CONFIG_X signals" https://forums.developer.nvidia.com/t/m-2-key-b-config-x-signals-config-0-config-1-etc/335890 | NVIDIA reply |
| EH | ESP32-S3-WROOM-1 datasheet v1.8 (local), Table 6-3 | VIH = 0.75×VDD, VIL = 0.25×VDD |

## 1. CONFIG pins (1, 21, 69, 75)

### Definitions

| Pin | Rev 1.0 (S10) | Rev 3.0 v1.2 (S30) / vendors | Card direction / level | Host side |
|---|---|---|---|---|
| 21 | CONFIG_0 | same name in every source | Card output: GND or NC only ("0 V (GND)/NC", Table 25) | Host pull-up required (S10 §3.2.12: "each of the CONFIG_0..3 signals needs to be fitted with a pull-up resistor"; S30: pull-up so the pins can be read "even if the M.2 expansion card is not powered") |
| 69 | CONFIG_1 | same | same | same. On the Socket 3 (Key M) pinout, pin 69 is PEDET, which is a different socket |
| 75 | CONFIG_2 | same | same | same |
| 1 | CONFIG_3 | same | same | same |

Pull-up rail: Quectel Fig.25 (SQ1 p.57) shows 10 k to `VCC_IO_HOST` and notes that it "could be **1.8 V or 3.3 V**". NVIDIA (NV) says to connect CONFIG to "any unused GPIOs keeping in mind the voltage signal levels required (like 1.8V or 3.3V)". congatec (S30 Fig.2) uses 10 k to 3.3 V on CONFIG_1 only. SATA-IO (SATA Table 5) gives CONFIG VIL from −0.5 V to 0.5 V.

### Decode table: Rev 1.0 compared with Rev 3.0 v1.2 (0 = GND, 1 = NC)

| State | C0/21 | C1/69 | C2/75 | C3/1 | Rev 1.0 Table 27 | Rev 3.0 v1.2 per congatec AN43 p.9 |
|---|---|---|---|---|---|---|
| 0 | 0 | 0 | 0 | 0 | SSD – SATA | SSD – SATA |
| 1 | 0 | 1 | 0 | 0 | SSD – PCIe | SSD – PCIe |
| 2 | 0 | 0 | 1 | 0 | WWAN – PCIe, PC0 | WWAN – PCIe (PC0) |
| 3 | 0 | 1 | 1 | 0 | WWAN – PCIe, PC1 | WWAN – PCIe (PC1) |
| 4 | 0 | 0 | 0 | 1 | WWAN – USB 3.0, PC0 | **WWAN – PCIe, USB3.1 Gen1 (PC0)** |
| **5** | **0** | **1** | **0** | **1** | **WWAN – USB 3.0, PC1** | **WWAN – PCIe, USB3.1 Gen1 (PC1)** |
| 6 | 0 | 0 | 1 | 1 | WWAN – USB 3.0, PC2 | WWAN – PCIe, USB3.1 Gen1 (PC2) |
| 7 | 0 | 1 | 1 | 1 | WWAN – USB 3.0, PC3 | WWAN – PCIe, USB3.1 Gen1 (PC3) |
| 8–11 | 1 | x | x | 0 | WWAN – SSIC PC0–3 | WWAN – SSIC PC0–3 |
| 12 | 1 | 0 | 0 | 1 | WWAN – PCIe, PC2 | WWAN – PCIe (PC2) |
| 13 | 1 | 1 | 0 | 1 | WWAN – PCIe, PC3 | WWAN – PCIe (PC3) |
| 14 | 1 | 0 | 1 | 1 | RFU | **WWAN – PCIe, USB3.1 Gen1 (vendor defined)** |
| 15 | 1 | 1 | 1 | 1 | No module present | No Add-in Card Present |

Telit (ST p.14–15) quotes what looks like a newer-spec footnote: "Used by an Add-in Card where USB 3.1 Gen1 is present on the connector and PCIe is No Connect. Only a single lane of PCIe is available in these configurations."

### What real modules declare (it doesn't always match the table)

- Quectel RM50xQ / RM520N: only CONFIG_1 is GND, which is **state 14**. Quectel calls it "Quectel defined" / "WWAN-PCIe, USB 3.1, Port Config 2 (Quectel defined)" (SQ1 Table 28, SQ2 Table 29).
- Dell Latitude 7x80/7490 BIOS table defines **state 14 = "HCA-PCIE (1 lane)"** (HW5 `hca.png`). So two vendors use the same state for different things, and state 14 already has two meanings in the field.
- Telit FN990: 21 GND, 69 GND, 75 NC, 1 NC, which is **state 6**. Telit calls it "PCIe or USB 3.1 Gen 2, Port Configuration 2" (ST Table 6).
- Sierra EM7455: 21 GND, 69 GND, 75 NC, 1 NC, also **state 6**. Sierra notes "Host must not repurpose this pin" (SS Table 3-1).
- SIMCom SIM8200EA-M2: 21, 69 and 75 GND, 1 NC, which is **state 4**. SIMCom labels it "WWAN – USB 3.1, Vender defined" (SC Table 29/30).
- **No module found that declares state 5.**

### Do hosts drive, ground or leave CONFIG floating?

| Host / adapter | CONFIG_0..3 handling | Source |
|---|---|---|
| Waveshare USB TO M.2 B KEY dongle | all four **NC** (no pull-up) | HW1 |
| Waveshare M.2 4G/5G HAT | all four NC | HW2 |
| Osmocom ngff-breakout | all four NC (no net on CONFIG pads) | HW3 |
| Geniatech Jetson Orin carrier | all four NC (X markers) | HW4 |
| Toradex Mallow X17 | 1, 21, 69 NC; 75 not listed | HW6 |
| Dell Latitude 7x80/7490 | all four to `SLOT2_CONFIG_x` nets on sheet 33 (EC/PCH GPIO; pull-up value and rail **not visible**) | HW5 |
| congatec reference design | CONFIG_1 has a 10 k pull-up to 3.3 V and drives a SATA/PCIe mux SEL. CONFIG_0/2/3 are not used | S30 Fig.2 |
| Telit / Quectel recommended host | 10 k pull-up on every pin to VCC_IO_HOST (1.8 or 3.3 V), into a GPIO | ST p.14, SQ1 Fig.25 |

**Nothing found grounds or actively drives a CONFIG pin from the host side.** Every source either leaves the pins floating or pulls them up (1.8 V or 3.3 V).

## 2. Other pins (card direction, voltage, host action)

| Pin | Rev 1.0 (S10 T25/T29/T32/T47) | Rev 3.0 v1.2 (S30) | Vendor repurposing | Card dir / V | Does any host drive it, tie it to a rail or ground it? |
|---|---|---|---|---|---|
| 25 | DPR, card input, 1.8 V (SAR sensor) | DPR (O from host) 0/1.8 V | Quectel DPR DI with PU. Telit TGPIO_02 "can be DPR". Sierra DPR with PU (host may use open-collector) | **Input**, 1.8 V | **Driven by host** (SAR sensor or GPIO). HW2 labels it "DPR(1.8/3.3V)", so a **3.3 V drive is possible** (*how far HW2 actually connects it beyond the symbol label is unverified*). Dell: 0 Ω stub, DNP to nothing, so NC. Mallow: NC |
| 30 | UIM_RESET, card output (SIM supply level) | UIM-RESET | all vendors USIM1_RST, 1.8/3.0 V | Output | Host connects it to a SIM socket with ESD (HW1 SMF05C TVS, HW3, HW6, Dell). **No host source** |
| 32 | UIM_CLK, card output | UIM-CLK | same | Output | same: SIM socket only |
| 34 | UIM_DATA, I/O | UIM-DATA | same (module has internal PU) | I/O | same: SIM socket only. A SIM card that is inserted loads the line |
| 36 | UIM_PWR, card **output** (SIM VCC 1.8/3 V) | UIM-PWR | Quectel USIM1_VDD PO. Telit UIM1_VCC O 1.8/2.95 V | **Power output** | Host side: SIM socket VCC plus decoupling (HW1 100 nF + 33 pF, HW3 100 nF). Dell names the net `+SIM_PWR` (*whether a host rail feeds it is unverified; it looks like a net name only*). **No host source found.** An inserted SIM card + 100 nF load the pin |
| 38 | WWAN: N/C. SSD: **DEVSLP** (host to SSD) | DEVSLP (O from host); congatec net `DEVSLP_3p3` | Quectel SDX2AP_STATUS DO. RM520N WLAN_TX_EN/NC (DI). Telit 1PPS O. SIMCom **I2C_SCL** | varies | **Driven by SSD-capable hosts at 3.3 V** (S30 Fig.2; SATA VIH max 3.6 V). Dell drives `M0042_DEVSLP` here (*rail unverified*). Hosts with WiFi COEX drive WLAN_TX_EN at 1.8 V. Mallow and Geniatech: NC (Geniatech label WLAN_Tx_EN, NC) |
| 56 | WWAN: N/C. SSD: MFG_DATA ("must be no-connect on the motherboard", §3.2.11.1) | NC (host pinout) / MFG_DAT (congatec) | Quectel/RM520N RFFE_CLK DO 1.8 V. Telit I2C_SDA 1.8 V (internal 2.2 k PU). Sierra I2C_DATA (codec) 1.8 V. SIMCom ANTCTL3/RFFE_SCLK. Waveshare dongle: test point only | varies, 1.8 V | **Dell Latitude: `PORT80_DET#` to EC** (sheet 33, *level unverified, likely 3.3 V EC domain*). Other hosts: RFFE tuner or codec I2C at 1.8 V, or NC (Mallow, Geniatech `MIPI_DATA` NC, HW1 TP) |
| 58 | WWAN: N/C. SSD: MFG_CLOCK | NC / MFG_CLK | Quectel RFFE_DATA. Telit I2C_SCL. Sierra I2C_CLK. SIMCom ANTCTL2/RFFE_SDATA | varies, 1.8 V | **Dell Latitude: `HOST_DEBUG_TX` (host to card, EC debug UART, ACTIVELY DRIVEN; *voltage unverified, likely 3.3 V*)**. Others: 1.8 V or NC |
| 59 | ANTCTL0, card output 1.8 V (2.8 V max per T25) | ANTCTL0 | Quectel RM50x **LAA_TX_EN** DO. Telit RFU. SIMCom ANTCTL0 | Output | Host: input of an antenna switch, test point, or NC (HW1 TP, Geniatech mmWave_Enable NC, Dell NC, Mallow NC). **No host source found** |
| 60 | COEX3, I/O 1.8 V | COEX3 I/O 1.8 V | Quectel **WLAN_TX_EN DI** (host WiFi drives). RM520N N79_TX_EN. Telit RFU. SIMCom I2S_MCLK DO | I/O | **May be driven at 1.8 V by the host's WiFi card** (COEX). Dell NC, Mallow NC, HW1 TP |
| 61 | ANTCTL1 out 1.8 V | ANTCTL1 | Telit **RFFE0_DATA** I/O. Quectel ANTCTL1 | Output (I/O on Telit) | Antenna tuner or NC. A tuner may drive SDATA only during an RFFE read, at 1.8 V |
| 62 | COEX2, I/O 1.8 V | COEX_TXD (O from host) | Quectel COEX_RXD DI. Telit TGPIO_03. SIMCom COEX2 = COEX_TX **DO** (opposite of Quectel) | **Input on Quectel**, output on SIMCom | **Driven at 1.8 V by the host WiFi COEX UART** when present. Dell NC, Mallow NC |
| 63 | ANTCTL2 out 1.8 V | ANTCTL2 | Telit RFFE0_CLK. SIMCom LAA_TX_EN | Output | Tuner input or NC. No host source |
| 64 | COEX1, I/O 1.8 V | COEX_RXD (I to host) | Quectel COEX_TXD DO. SIMCom COEX1 = COEX_RX **DI** | I/O; differs by vendor | **May be driven at 1.8 V by the host WiFi** (SIMCom-style hosts). Dell NC, Mallow NC |
| 65 | ANTCTL3 out 1.8 V | ANTCTL3 | **Quectel RFFE_VIO_1V8 = power OUT 1.8 V, 50 mA. Telit VREG_L6B_1P8 power OUT.** SIMCom WL_TX_EN **DI** (host WiFi drives). Geniatech names it `mmWave_1P85` | Output (power output on Quectel/Telit) | Host may hang an RFFE tuner VIO (a load) on it, or **drive it at 1.8 V** (SIMCom-style WL_TX_EN). No host-supplied *power* on this pin was found |
| 66 | SIM_DETECT, card **input** 1.8 V, card-side PU (Fig.90) | SIM DETECT | all vendors USIM1_DET DI | Input | **Host GROUNDS it via the SIM socket switch** when no SIM (S10 Fig.90). HW3: 47 k to GND plus socket switch. HW1: 1 k to socket CD. Mallow: UIM_CD |
| 68 | SUSCLK 32 kHz, card input, **3.3 V** | SUSCLK (O from host) 0/3.3 V | Quectel AP2SDX_STATUS DI 1.8 V. RM520N RESERVED. Telit TGPIO_01. SIMCom **I2C_SDA** 1.8 V | Input | **Driven by laptop-style hosts as a 3.3 V, 32 kHz clock** (S10, S30 `SUSCLK_3p3`). Dell, Mallow and Geniatech: NC |

Other things to know:
- **Supply pins.** S30 (Rev 3.0) labels pins 70/72/74 "3.3 V/VBAT". Modules accept 3.135–4.4 V (Quectel, Sierra, SIMCom). A tablet-style host may therefore put up to about 4.4 V on the 3.3 V pins.
- **GPIO pins.** Port Config only changes GPIO_0..11 (pins 10, 20–28, 40–48, 23, 26; S10 Table 26). It does **not** change 30–38, 56–68, or the CONFIG pins.

## 3. Risks for our plan

**(a) State 5 (CONFIG_0 GND, CONFIG_1 NC, CONFIG_2 GND, CONFIG_3 NC)**
- **It is not a reserved code.** Rev 1.0 calls it "WWAN – USB 3.0, PC1". Rev 3.0 v1.2 renames it "WWAN – PCIe, USB3.1 Gen1, PC1" (S30). The meaning is still "WWAN on USB3, GPIO block = GNSS+Audio v2".
- **What a host might do with it.** A BIOS that decodes it may enable the PCIe root port (harmless, the link never trains). It may also route GNSS I2C and audio onto pins 40–48 and 20–28. We don't use those pins for expansion, but they should stay high-Z on our card.
- **Firmware whitelists.** No surveyed module uses state 5. Hosts with CONFIG whitelists, like Dell (HW5), may refuse or ignore it.
- **Fine on plain adapters.** USB adapters ignore CONFIG entirely (HW1–HW4).
- *Whether Rev 4.x/5.x changed state 5 again is unverified (paywalled).*

**(b) Carrier signature: our carrier grounds CONFIG_1 (69) and CONFIG_3 (1)**
- **No grounding host was found.** No host or adapter grounds or drives CONFIG_1 or CONFIG_3. They float (HW1–HW4, HW6) or are pulled up (Dell to EC/PCH, congatec 10 k to 3.3 V, Telit/Quectel guidance).
- **RISK 1: a 1.8 V pull-up reads as a false "low".**
  - Quectel and NVIDIA both say the host pull-up may go to **1.8 V**.
  - The ESP32-S3 needs VIH ≥ 0.75 × 3.3 V = 2.475 V (EH).
  - On a 1.8 V-pull-up host, both lines sit in the undefined band and can read as low. That would be a **false carrier detection**, and the card would then enable the expansion switch on a foreign host.
  - Mitigation:
    - require "< 0.3 V" (spec VIL max 0.5 V), for example by sampling 69 and 1 with the ESP32 ADC instead of a digital read, or
    - add a third signature that a 1.8 V pull-up can't produce, for example a pin that our carrier ties to 3.3 V.
- **RISK 2: back-feed into an unpowered card.** The spec intends host pull-ups to be powered while the card is unpowered (S30: "read even if the M.2 expansion card is not powered"). A 3.3 V pull-up into an unpowered ESP32 IO back-feeds through the clamp diode, about 0.27 mA through 10 k. Add series resistance and/or isolate.
- If the card adds its own weak pull-up so that floating reads high, keep it ≥ 100 k so it doesn't change the host's decode (high = NC, so a card pull-up is benign for the host).

**(c) Expansion lines behind an analog switch (off on normal hosts)**

| Severity | Pins | Why |
|---|---|---|
| **Avoid / high** | **56, 58** | Dell Latitude 7280/7380/7480/7490 wires 58 = `HOST_DEBUG_TX` (EC actively drives it) and 56 = `PORT80_DET#` (EC input, probably pulled up). The voltage is probably 3.3 V (*unverified*), which is inside 0–3.6 V. But if our firmware closes the switch on a false detect (see RISK 1), we fight an EC output, and our signals land on a Dell debug detect line. Other hosts: 1.8 V RFFE tuner or I2C codec, or NC. SSD hosts must leave them NC (S10 §3.2.11.1, SATA) |
| **Medium** | **60, 62, 64** | COEX lines. A host WiFi card (or a SIMCom-style host on 65) may actively drive them at 1.8 V, so they are in range. Direction differs between Quectel and SIMCom on 62/64 |
| **Medium** | **65** | Quectel and Telit hosts treat 65 as a 1.8 V *supply output from the card*. A host may load it with a tuner VIO, or drive it at 1.8 V (SIMCom WL_TX_EN). No host source above 1.8 V found |
| **Low** | **59, 61, 63** | Host side is antenna-switch inputs, test points or NC. A tuner may drive 61 during RFFE reads at 1.8 V |
| **Low (watch loads)** | **30, 32, 34, 36** | Host has a SIM socket, a 5 V TVS array (SMF05C, HW1) and 100 nF on 36. **No host source.** But an inserted SIM card and its decoupling load the lines when the switch is on. Pin 36 is UIM_PWR: the card must never drive it as an expansion line on a host that has a SIM fitted |
| (not in our list, FYI) | 38, 68, 66 | Hosts actively drive 38 (DEVSLP 3.3 V) and 68 (SUSCLK 3.3 V, 32 kHz). Hosts ground 66 (SIM detect). Keep these out of the expansion set |

Overall, all observed host-side levels are 0–3.3 V. Nothing above 3.6 V or below 0 V was found on 30–36, 56–65. The only pins that carry > 3.6 V are the **supply pins (70/72/74 "3.3 V/VBAT", up to 4.4 V)**. Check that the card's own regulator, ESD parts and the analog switch supply tolerate that if they are fed from the edge 3.3 V. **Suggested pick of 12 pins:** 59, 61, 63, 60, 62, 64, 65, 30, 32, 34, 36 plus one of 56/58, or drop 56/58 entirely and accept 11. Avoid 56/58 if Dell laptops matter.

## 4. M.2 B-key to USB adapters with public schematics

- **Waveshare "USB TO M.2 B KEY"** (HW1). Datasheet: https://files.waveshare.com/upload/4/4d/USB_TO_M.2_B_KEY_Sch.pdf
  - CONFIG 1/21/69/75: NC, no pull-ups.
  - 56/58 (RFE_RFFE): test points only. 59/61/63/65 (ANTCTL): test points/labels. 60 (I2S_MCLK), 62/64 (COEX), 38/68 (labelled I2C_SCL/SDA): port labels only, no load found.
  - 66: through 1 k to the SIM socket CD contact. 30–36: SIM socket via 22 Ω/0 Ω with an SMF05C TVS and 100 nF + 33 pF on VCC.
  - Pin 6 (FULL_CARD_POWER_OFF#) has a 100 k pull-up to 3.3 V. Pin 67 RESET is driven.
- **Osmocom/sysmocom ngff-breakout** (HW3, CC-BY-SA, Eagle source).
  - CONFIG: NC.
  - 56/58 go to header X3 as SMB_DATA/SMB_CLK. 59–65 go to header X3. These are user-wired, so a user could put anything on them.
  - 66 has 47 k to GND plus the SIM switch. 30–36 go to the SIM socket through 47 Ω. 38 and 68: NC.
  - 25 (BODY_SAR), 26, 8, 67 have 10 k pull-ups to an on-board 1.8 V LDO.
- **Generic Amazon/eBay "NGFF Key-B to USB 3.0 + SIM" adapters** (e.g. HWTools UN32A https://www.hwtools.net/Adapter/UN32A.html): no schematics found. *Their CONFIG handling is unverified; most likely NC.*

## 5. Unverified (not confirmed from a primary source here)

1. Rev 3.0 decode table comes from congatec's transcription (S30), not the PCI-SIG document. **Rev 4.x/5.x tables were not seen.** Whether state 5 or any state was redefined after Rev 3.0 v1.2 is unknown.
2. The FN990 footnote ("PCIe is No Connect, single lane") may be a newer-spec footnote. Not confirmed.
3. Dell `HOST_DEBUG_TX` / `PORT80_DET#` (pins 58/56) voltage and exact driver. Dell `SLOT2_CONFIG_x` pull-up value and rail. Whether `+SIM_PWR` on pin 36 is host-sourced. All three are on sheets not shown.
4. Whether Lenovo, HP or other laptops use 56/58 or COEX pins for anything host-driven. No schematics found. Whether those laptops whitelist modules by CONFIG state or by USB VID/PID (*from memory: Lenovo/HP whitelist by USB ID in BIOS*) is unverified.
5. Raspberry Pi CM4/CM5 IO boards have **no** M.2 B-key (CM5IO is M-key). Third-party Pi 5 B-key HATs (Waveshare PCIe-to-4G/5G HAT+, Sixfab, etc.): no schematic was found for the HAT+. NXP EVK, Seeed reTerminal: not checked.
6. Fibocom L850/FM350 and Sierra EM9191 pin usage. Their documents were behind Cloudflare or not retrieved.
7. Whether ESP32-S3 IOs are safe (no back-power) when unpowered with an external 3.3 V pull-up. Not in the WROOM datasheet excerpt checked.
8. Whether HW2 (Waveshare HAT) actually drives DPR at 3.3 V. Only the symbol label "DPR(1.8/3.3V)" was seen.
