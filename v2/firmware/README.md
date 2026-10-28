# v2 self-test firmware

`v2_selftest.py` is a one-file MicroPython bring-up test for the **v2.0 Rev A** card. It checks
the expansion-bus hold-off (IO38), the carrier ID EEPROM, the EXP loopback, the host sidebands
(LED_1#, WAKE_ON_WWAN#, W_DISABLE2#) and the Rev B basics. It prints a PASS / FAIL / SKIP / CHECK
report over the USB REPL. It needs no toolchain: stock MicroPython plus `mpremote`.

It serves the procedure in [`docs/v2-test-procedure.md`](../../docs/v2-test-procedure.md), which
says which run to do at which step and what counts as a pass. It closes review findings
contract_test-2 (no v2 firmware) and mcu_io-7 (sidebands not exercised) in
`docs/review/v2_rc1_design_review.md`.

## GPIO table

The script has the same table at its top. Sources: `hardware/design.py` `exp_map`,
`hardware/blocks/esp32s3_companion/esp32s3_companion.py` (`EXP_MODULE_PINS`,
`HOST_MODULE_PINS`, module pads per WROOM-1 Table 3-1), `hardware/blocks/host_sideband/`,
`docs/pinmap.md` §6.2–6.3. Cross-checked against the netlist from `make check`.

| GPIO | Pad | Net | Function in the test |
|---|---:|---|---|
| IO39 | 32 | EXP_0 (M.2 30) | I²C SDA to the ID EEPROM, 4.7 k R20 on the card |
| IO41 | 34 | EXP_1 (M.2 32) | I²C SCL, 4.7 k R21 |
| IO1, IO2 | 39, 38 | EXP_2, EXP_3 (34, 36) | loopback pair |
| IO18, IO4 | 11, 4 | EXP_4, EXP_5 (40, 59) | loopback pair |
| IO5, IO6 | 5, 6 | EXP_6, EXP_7 (60, 61) | loopback pair |
| IO7, IO15 | 7, 8 | EXP_8, EXP_9 (62, 63) | loopback pair |
| IO16, IO17 | 9, 10 | EXP_10, EXP_11 (64, 65) | loopback pair |
| IO38 | 31 | Q3b gate, R35 100 k pull-up | bus hold-off: **high = held off**, low = released |
| IO40 | 33 | Q3a drain, R30 10 k pull-up | W_DISABLE2# (pin 26), inverted: 0 = radio allowed |
| IO42 | 35 | Q2a gate | high = LED_1# (pin 10) pulled low |
| IO47 | 24 | Q2b gate | high = WAKE_ON_WWAN# (pin 23) pulled low |
| IO48 | 25 | D4 cathode | status LED, active low (Rev B) |
| IO8, IO9 | 12, 17 | J3 Qwiic SDA / SCL | Qwiic scan (Rev B) |

IO38 can no longer read EXP_OE (RC1 change). The firmware can only see the bus through a fixture:
an EEPROM ACK at 0x50, or loopback jumpers on the dev carrier's J3.

## 1. Flash MicroPython (once per card)

Use the stock **ESP32_GENERIC_S3** build (Rev B was validated on v1.29.0). Use the default
variant, **not** `SPIRAM_OCT`: this card has an N8R2 module with quad PSRAM, and octal builds
boot-loop. Download the `.bin` from micropython.org/download/ESP32_GENERIC_S3/.

```sh
pip install esptool mpremote
esptool --chip esp32s3 -p <port> erase_flash
esptool --chip esp32s3 -p <port> write_flash -z 0 ESP32_GENERIC_S3-<date>-v<version>.bin
```

`<port>` is `/dev/ttyACM<n>` on Linux and `/dev/cu.usbmodem<n>` on macOS. If the port doesn't
answer, enter download mode first: hold BOOT, tap RESET (PERST#), release BOOT.

## 2. Run

Copy the script once, then call `main()` with the arguments for the setup under test:

```sh
mpremote connect <port> cp v2/firmware/v2_selftest.py :
mpremote connect <port> exec "import v2_selftest; v2_selftest.main(signature=True, loopback=True)"
```

Or, with defaults (unknown host, no fixture, no operator prompts):

```sh
mpremote connect <port> run v2/firmware/v2_selftest.py
```

For operator prompts (y/n answers, JP5 steps), use the interactive REPL. `exec`/`run` can't read
the keyboard:

```sh
mpremote connect <port> repl
>>> import v2_selftest
>>> v2_selftest.main(signature=True, loopback=True, interactive=True)
```

| Argument | Meaning |
|---|---|
| `signature` | `True`: CONFIG_2/3 grounded (dev carrier JP2/JP3 on GND), bus must turn on when released. `False`: not grounded (JP2/JP3 open / 1V8 / 3V3, or a normal host), bus must stay off even when released. `None` (default): report only. |
| `loopback` | Dev carrier J3 jumpers fitted: EXP_2–3, 4–5, 6–7, 8–9, 10–11 (J3 pins 5–7, 9–11, 13–15, 17–19, 21–23). **Only with these jumpers fitted**: the test drives EXP_2..11, which an unknown carrier must never see. |
| `loop01` | J3 jumper EXP_0–EXP_1 (pins 1–3) fitted instead of an EEPROM (JP7/JP8 open). Proves both I²C lines in both directions. |
| `program` | Write the dev test image into a blank 24C02 first (vendor 0xFFFF, EXP_0/1 = I²C, all other lines unused), then read it back. |
| `window` | Seconds to leave the bus released for manual measurements (e.g. `window=30`). |
| `interactive` | Wait for the operator. Use only from `mpremote repl`. |
| `outputs`, `wifi` | `False` skips the LED_1#/WAKE# patterns or the WiFi scan. |

From the REPL, `v2_selftest.bus_on()` and `v2_selftest.bus_off()` release and hold the bus by
hand. Importing the module already drives IO38 high.

**Safety:** the script drives IO38 high at import and on every exit path, Ctrl-C included, and
floats every EXP line. A card that isn't running the script keeps the bus off (R35 holds IO38
high through reset and boot). The J3/J4 pull sweep reconfigures IO43/IO44 (UART0), which is
harmless on the USB REPL.

## 3. Expected output

Dev carrier, JP2/JP3 on GND, EEPROM fitted, loopback jumpers on, `signature=True,
loopback=True` (values vary):

```
================================================================
v2.0 Rev A self-test  0.1 (v2.0 Rev A RC1)
================================================================
[PASS ] chip                   Generic ESP32S3 module with ESP32S3
        micropython 1.29.0, script 0.1 (v2.0 Rev A RC1)
        unit serial (base MAC) <mac>
        cpu 160 MHz, reset cause 1
        die temperature 45 C
[PASS ] flash size             8 MB (N8R2)
[PASS ] PSRAM                  heap 2001 kB, 1 MB strided r/w errors 0
[PASS ] J3/J4 pull sweep       IO8-14, IO21, IO43/44
[CHECK] status LED D4          red D4 blinked 5x (lens out of the card edge), green D3 on
>>> toggle pin 26 (JP5 on/off) during the next 10 s
[PASS ] W_DISABLE2# -> IO40    both states seen, 2 changes; now radio allowed (pin 26 high)
>>> LED_1# (pin 10): 5 x 0.5 s low, 1 Hz
[CHECK] LED_1# pin 10          pin 10 pulsed low 5x at 1 Hz (dev carrier D5 blinked)
>>> WAKE_ON_WWAN# (pin 23): 3 x 100 ms low, then 1 x 1 s low
[CHECK] WAKE_ON_WWAN# pin 23   pin 23: 3 short + 1 long low pulse (dev carrier D6 with JP6)
--- expansion bus (signature=True, loopback=True, loop01=False)
[PASS ] B released (IO38=0)    EEPROM 0x50 ACK, loopback 5/5 pairs conduct (want ON)
        magic b'M2CI'  format 1  flags 0x00
        vendor 0xffff  product 0x0000  revision 'A'
        serial 0x0000000000000000
        name b'm2-dev-carrier test image'
        CRC stored 0x........ calc 0x........
        map 0:07/00 1:08/00 2:00/00 ... 11:00/00
[PASS ] EEPROM header          valid M2CI v1
[PASS ] loopback EXP_2..11     10 lines, both directions, no cross-shorts
[PASS ] A hold-off (IO38=1)    EEPROM 0x50 no ACK, loopback 0/5 pairs conduct -> bus off
[PASS ] C re-hold (IO38=1)     EEPROM 0x50 no ACK, loopback 0/5 pairs conduct -> bus off
[PASS ] WiFi scan              6 APs, strongest -55 dBm
[SKIP ] Qwiic I2C (J3)         no pull-ups seen: nothing plugged
----------------------------------------------------------------
SUMMARY  PASS 11  FAIL 0  SKIP 1  CHECK 3
RESULT   PASS (tick the CHECK items by hand)
bus held off (IO38=1) on exit
```

- **CHECK** means the operator has to look: an LED, or a scope or DMM on the pin. Record it in the
  procedure.
- With no fixture, A, B and C report **SKIP** ("cannot see the bus"). The bus state is then
  measured by hand (procedure §7).
- A blank EEPROM reports `EEPROM blank (0xFF)`. Rerun with `program=True`.
- Copy the unit serial to the results sheet only. Never commit it (repo CLAUDE.md).
