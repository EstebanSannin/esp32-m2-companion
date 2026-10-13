# Bring-up log — v1.0 board

Board: v1.0 as-built (JLCPCB, 5 pcs assembled). Unit under test = the
hand-repaired sample (D− jumpered finger-pin-9 → U1 pin 3; see
`hardware/blocks/m2_keyb_edge/LESSONS.md` for why the notch milling severed it).

Host: Verdin iMX8MP on Mallow carrier (Torizon), card in the M.2 slot.
Firmware: MicroPython ESP32_GENERIC_S3 v1.29.0 flashed at 0x0.
Method: host-USB REPL over `mpremote` (`/dev/ttyACM0`), SSH-driven from dev Mac.
Chip unique_id / base MAC: `3c:0f:02:73:21:f8`.

## 2026-09-11 — software self-test (no external hardware)

All software-exercisable functions pass. Only the LEDs are outstanding
(deferred — see below).

| Domain | Test | Result |
|---|---|---|
| USB | native USB-Serial-JTAG enumerates on host, full REPL/flash comms | **PASS** (on repaired D−) |
| CPU | `machine.freq()` | 160 MHz |
| Flash | `esp.flash_size()` = 8 MB; 32 KB FS write/read SHA-256 match | **PASS** (matches N8**8**R2) |
| PSRAM | 1 MB alloc + strided readback OK; ~2 MB free heap | **PASS** (quad PSRAM active → N8**R2** confirmed) |
| Temp | `esp32.mcu_temperature()` = 56 °C | normal |
| RTC | set + 1.2 s tick readback | **PASS** |
| WiFi | `scan()` → 5 APs, strongest −58 dBm | **PASS** (antenna + 2.4 GHz RF good) |
| BLE | `BLE().active(True)`, MAC `…21:fa` | **PASS** (radio init) |
| J3 Qwiic I2C | HW `I2C(0, sda=8, scl=9)` init; bus scan | **PASS** (init OK; 0 devices, nothing plugged) |
| J4 + J3 pins | PU/PD integrity sweep on IO8,9,10,11,12,13,14,21,43,44 | **PASS** (all PU=1/PD=0 → no shorts, no cold joints, no stuck pins) |
| GPIO drive | IO14, IO21 output toggle readback | **PASS** |

Interpretation: the entire active signal chain — module power, both memories,
RF front-end, native USB, and every broken-out header pin (both JST connectors,
all solder joints) — is functional. The PU/PD sweep in particular clears the
connector assembly (no bridges between adjacent 1.0 mm-pitch pins).

## Outstanding / not yet exercised

- **LEDs (D3 green power, D4 red IO48):** both dark. Deferred. IO48 toggles in
  firmware (verified by earlier blink install), so D4's driver GPIO is proven —
  the fault is downstream (emit-face orientation and/or brightness, or a
  meter that couldn't forward-bias them). Needs a working meter or coin-cell
  bench test on a spare LED. Rev-B footprint carries an emit-direction caveat
  (`hardware/blocks/leds/datasheets.md`).
  **→ Resolved 2026-10-05:** LEDs were assembled 180° reversed (see below);
  emit face confirmed by a hand-rotated D4. Fixed in Rev B.
- **SPI loopback:** needs IO11 (MOSI) ↔ IO13 (MISO) jumpered on J4 — not run
  (would require external wiring).
- **I2C sensor:** needs a Qwiic peripheral on J3 — not run.
- **Sideband recovery (EN/BOOT diode isolation):** exercised implicitly — board
  boots, resets, and re-enumerates cleanly under `mpremote` soft-reboot.

## 2026-09-11 — real-firmware run (Aktualino Uptane OTA client)

Flashed the owner's own **Aktualino** firmware (github.com/EstebanSannin/aktualino,
v0.1.2) — a from-scratch Uptane/TUF OTA client in ESP-IDF — as an end-to-end
application test beyond MicroPython.

**Key finding — PSRAM variant mismatch (NOT a board fault):** the public
`aktualino-esp32s3` release binary is compiled for **octal PSRAM**
(`CONFIG_SPIRAM_MODE_OCT=y`, targets an N16R8 module). Our card is populated with
**ESP32-S3-WROOM-1-N8R2 = 2 MB *quad* PSRAM**. Octal-mode init on quad silicon
aborts at startup → boot loop:
`E octal_psram: PSRAM chip is not connected, or wrong PSRAM line mode`.
The board is fine (MicroPython already proved the quad PSRAM works). Rebuilt the
exact v0.1.2 tag with the one-line change `CONFIG_SPIRAM_MODE_OCT` →
`CONFIG_SPIRAM_MODE_QUAD` (built on the m920x host via the project's
`espressif/idf:release-v5.4` Docker pipeline, no-secrets/clean tree), merged to a
`0x0` image, flashed.

**Result — PASS.** Quad image boots clean:
`esp_psram: Found 2MB PSRAM device / Speed 80MHz / SPI SRAM memory test OK`,
then app_main runs and opens the SoftAP setup portal:
`SETUP PORTAL UP — join open Wi-Fi "aktualino-7321f8"`, DHCP + captive DNS on
`192.168.4.1`. STA MAC `3c:0f:02:73:21:f8`, SoftAP MAC `…f9`. This exercises the
full ESP-IDF stack on the board: quad PSRAM heap pool, WiFi STA+AP, and the
antenna (AP is broadcasting) — a complete application-level bring-up pass.

**Takeaway for any ESP-IDF firmware on this card:** it MUST be built
`CONFIG_SPIRAM_MODE_QUAD` (N8R2). An octal build silently boot-loops. (The board
HW supports both N8R2/N16R8 per the drop-in variant policy in
`hardware/blocks/esp32s3_companion/esp32s3_companion.py`, but firmware must match
the populated part.)

## 2026-10-05 — LED fault isolated: open LED, drive circuit proven good

Second (new, virgin) board on the beerus bench. Both LEDs (D3 green, D4 red)
dark, clearly visible and genuinely off — same as the first unit. Ruled out, in
order: reversed polarity (design puts anode toward the M.2 edge, matches the
owner's diode-mode "+"), missing parts (R3/R4/D3/D4 all in the CPL), emit
direction (LEDs plainly visible and off), and the +3V3 branch (present at the
resistors).

**Decisive measurements** (MicroPython blink on IO48, meter DC-volts to GND):
- Both ends of **R4 = 3.54 V** during the ON window → **zero drop → zero current**.
- **IO48 (U2 pin 25) toggles cleanly 0 V (ON) / ~3.5 V (OFF)** — driver + trace good.
- So during ON: anode 3.54 V, cathode 0 V → **~3.5 V across the red LED with no
  current**. A healthy red LED would draw ~4.5 mA and drop R4 ~1.5 V.

**Conclusion:** the entire drive path (MCU, IO48 GPIO, trace, R4, 3V3 rail,
firmware) is **fully functional**. The red LED is NOT dead — it **lights under a
meter's diode test** — yet passes **no current in-circuit under full forward
(design) voltage**. That signature = the LED is **reverse-mounted** (180°, so it's
reverse-biased in normal operation) or has an **open LED↔PCB joint** the probes
bypass. Both LEDs dark on two boards + all still light under a meter →
**systematic: a CPL/footprint pin-1 rotation error at assembly** (green is then
also reverse-biased 3V3→GND → dark), NOT dead parts, electronics, or firmware.
The whole "LEDs don't work" investigation was never a software issue.

**CONFIRMED 2026-10-05 (owner diode-test + JLC preview):** R4 is soldered to the
LED's **cathode (−)**; the anode (+) is on the chip-side pad → **the LEDs are
mounted 180° reversed** (both D3/D4, both boards; green reverse-biased 3V3→GND so
also dark). The schematic/footprint are CORRECT (netlist ties R4→anode). The
error entered at **assembly sign-off**: JLC's placement preview showed the LED
flipped (their LCSC part polarity/rotation convention for C273612/C273616 is
opposite our footprint), JLC asked us to confirm, and **we approved it** — the
"+" was on the chip-side pad, not the resistor pad, and we didn't catch it.
Classic JLC LED-rotation trap. **So this is an assembly-data/process gap, not a
PCB bug.**

**VERIFIED FIX 2026-10-05:** a board with D4 hand-rotated 180° → the red LED
**blinks correctly** under the IO48 firmware. Confirms the reversal diagnosis and
that a corrected orientation needs no other change (design/firmware/drive all
good). The 180° rotation restores polarity AND emit direction together.

Fix (no respin required): re-run assembly on the SAME v1 PCB with D3/D4 rotation
corrected (+180° in the CPL) or an explicit "+ on the resistor-side pad"
instruction, and **verify JLC's preview against the netlist before approving**
(the "+" must land on the pad that connects to the series resistor). For rev-B,
bake the corrected rotation into the CPL export, re-confirm the emit face, and
drop R3→~68-100 Ω (green under-drive). Current boards: no software fix (polarity
is physical); hand-rotating a 0603 side-view LED 180° is possible but not worth
it on prototypes — everything else on the card works.
**→ Correction 2026-10-13 (GATE B3):** JLC engineering states that with
correct polarity this LED's lens faces *inward* (toward R3/R4) on our
footprint — the "emit direction restored" above was not actually verified.
See review-findings.md (GATE B3).
**→ Done in Rev B:** D3/D4 CPL rotation +180° (`gen_fab.py` `JLC_ROT`, order
blocked until preview-verified), emit face confirmed, R3 = 100 Ω (C22775),
silk cathode bar added.

**Rev-B actions (LEDs):** revisit the custom `LED_TJ-S1706_SideView` footprint —
verify pad size/pitch against the part terminals so it reliably solders; confirm
emit-face orientation on a sample; consider a more standard/forgiving LED
package. Also drop the green series resistor (R3) from 330 Ω toward ~68–100 Ω
(green runs sub-mA at 3.3 V by design). See `hardware/blocks/leds/`.
**→ Rev B outcome:** footprint kept (1.80 mm c-c pads soldered fine on v1;
the hand-rotated part works), silk cathode bar added, R3 = 100 Ω. No package
change needed.

## Rev B — unit identification check (first rev-B board)

Owner decision 2026-10-06: the unit serial = ESP32-S3 base MAC, printed as the
module's Data Matrix (format `<6-digit prefix><MAC>`, e.g. a v1 module read
`132611` + `3C0F027321E4`). Inferred from one module whose MAC could not be
read (v1 board without the D− jumper). **Confirm once on a single unit:**

1. Scan the module Data Matrix (Data Matrix-capable app; phone camera QR
   readers don't decode it).
2. `esptool.py --port /dev/ttyACM0 read_mac` on the same card.
3. Last 12 hex digits of (1) must equal (2). Record both here.
