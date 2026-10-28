"""v2.0 Rev A bring-up self-test (MicroPython, stock ESP32_GENERIC_S3).

Prints a PASS / FAIL / SKIP / CHECK report over the USB CDC REPL (stock
MicroPython enumerates as TinyUSB CDC, 303a:4001) for
the v2 acceptance criteria (SPEC §13 A3, S-v2-1..4) and the host sidebands.
Procedure and pass criteria: docs/v2-test-procedure.md. Usage:
v2/firmware/README.md.

  CHECK = the script cannot see the result; the operator observes it
          (LED blink, scope, DMM) and ticks the box in the procedure.

Safety rules this script keeps (docs/carrier-interface.md §4.3, §5;
docs/pinmap.md §6.3):
- IO38 is driven HIGH (bus held off) as the very first action at import,
  and again on every exit path of main(), test_bus() and the released()
  context manager, including exceptions and Ctrl-C.
- bus_on() is the one deliberate exception: for manual REPL steps
  (procedure 8.1, 8.5) it leaves the bus released until bus_off(), a chip
  reset, or a Ctrl-C / error during its own wait. A MicroPython soft reset
  (Ctrl-D) and a software/WDT reset do not reset IO38 by themselves: install
  v2/firmware/boot.py, which drives IO38 high on every boot and soft reset
  (docs/carrier-interface.md §4.3.1, firmware rule 5).
- After the bus is released, only EXP_0/EXP_1 (I2C) are touched. EXP_2..11
  are driven only when the operator says the dev-carrier loopback jumpers
  are fitted (loopback=True): that is the "host override (dev use)" the
  contract allows. Never pass loopback=True with an unknown carrier.
- Every EXP line is returned to a plain input (high-Z) afterwards.

Every GPIO number below comes from the block sources, not from memory:
  hardware/design.py exp_map (EXP index -> WROOM pin name), checked by
  hardware/blocks/esp32s3_companion/esp32s3_companion.py EXP_MODULE_PINS /
  HOST_MODULE_PINS (module pad numbers, datasheet Table 3-1), the host cells
  in hardware/blocks/host_sideband/host_sideband.py, and docs/pinmap.md §6.2.
"""

import gc
import os
import time

import machine
from machine import Pin, SoftI2C

try:
    import esp
except ImportError:          # not on an ESP32 port
    esp = None
try:
    import esp32
except ImportError:
    esp32 = None

SCRIPT_VERSION = "0.2 (v2.0 Rev A RC2)"

# ---------------------------------------------------------------------------
# GPIO table - one place. (GPIO, WROOM-1 module pad, net / M.2 pin, source)
# ---------------------------------------------------------------------------
# Expansion bus, MCU side of RN1..RN3 (220R) + TMUX1511 U3..U5.
# design.py exp_map; esp32s3_companion.py EXP_MODULE_PINS; pinmap.md §6.2.
EXP_GPIO = [
    39,  # EXP_0  M.2 30  pad 32  I2C SDA (4k7 R20 on MCU side)
    41,  # EXP_1  M.2 32  pad 34  I2C SCL (4k7 R21 on MCU side)
    1,   # EXP_2  M.2 34  pad 39  ADC1_CH0
    2,   # EXP_3  M.2 36  pad 38  ADC1_CH1
    18,  # EXP_4  M.2 40  pad 11  digital
    4,   # EXP_5  M.2 59  pad 4   ADC1_CH3
    5,   # EXP_6  M.2 60  pad 5   ADC1_CH4
    6,   # EXP_7  M.2 61  pad 6   ADC1_CH5
    7,   # EXP_8  M.2 62  pad 7   ADC1_CH6
    15,  # EXP_9  M.2 63  pad 8   digital
    16,  # EXP_10 M.2 64  pad 9   digital
    17,  # EXP_11 M.2 65  pad 10  digital
]
ADC_EXP = (2, 3, 5, 6, 7, 8)   # carrier-interface.md §4.3 capability column

# Host sidebands and bus hold-off: host_sideband.py; HOST_MODULE_PINS.
IO_HOLD = 38       # pad 31, Q3b gate, R35 100k pull-up. HIGH = bus held off,
                   # LOW = released (bus on only if CONFIG_2/3 also at 0 V)
IO_WDIS2 = 40      # pad 33, Q3a drain, R30 10k pull-up. Inverted:
                   # LOW = pin 26 high = radio allowed; HIGH = pin 26 low = kill
IO_LED1 = 42       # pad 35, Q2a gate (R27 100k pull-down). HIGH = pin 10 low
IO_WAKE = 47       # pad 24, Q2b gate (R28 100k pull-down). HIGH = pin 23 low

# Unchanged from Rev B (esp32s3_companion.py, io_header.py, leds.py).
IO_STATUS_LED = 48  # pad 25, D4 red cathode, active LOW
QWIIC_SDA, QWIIC_SCL = 8, 9                        # J3 Qwiic, no card pull-ups
HEADER_GPIO = (8, 9, 10, 11, 12, 13, 14, 21, 43, 44)  # J3 + J4 (v1 sweep)

EEPROM_ADDR = 0x50  # 24C02 on EXP_0/EXP_1 (carrier-interface.md §4.3)

# Timing (pinmap.md §6.3, carrier-interface.md §4.3.1): EXP_OE rises
# through R26 10k / C13 1 uF and crosses VIH ~4.5 ms after release (about
# 1-6.5 ms with tolerances); Q3b pulls it down in microseconds. The
# contract minimum wait is 10 ms; this test uses 60 ms for margin.
T_RELEASE_MS = 60
T_HOLD_MS = 5

# Dev-carrier loopback pairs on its J3 header (odd pins = EXP_0..11 at
# header pin 2*n+1): EXP_2-3, 4-5, 6-7, 8-9, 10-11 (review contract_test-5).
LOOP_PAIRS = ((2, 3), (4, 5), (6, 7), (8, 9), (10, 11))

# ---------------------------------------------------------------------------
# Bus safety first: hold the expansion bus off before anything else runs.
# ---------------------------------------------------------------------------
_hold = Pin(IO_HOLD, Pin.OUT, value=1)


def bus_off():
    """Hold the expansion bus off (IO38 high) and float every EXP line."""
    _hold.value(1)
    for g in EXP_GPIO:
        Pin(g, Pin.IN, pull=None)
    time.sleep_ms(T_HOLD_MS)


def bus_on():
    """Release the firmware hold-off (IO38 low). The bus turns on only if
    the carrier signature is present too.

    For manual REPL steps: the bus deliberately STAYS released after this
    returns, until bus_off() or a reset (boot.py re-holds it on every boot
    and soft reset). A Ctrl-C or error during the wait re-holds it. For
    scripted use prefer `with released(): ...`, which always re-holds."""
    try:
        _hold.value(0)
        time.sleep_ms(T_RELEASE_MS)
    except BaseException:
        _hold.value(1)
        raise


class released:
    """Context manager: bus released inside the block, held off (IO38 high,
    EXP lines high-Z) on every way out, Ctrl-C and exceptions included.

        with v2_selftest.released():
            ...  # measure, probe the EEPROM
    """

    def __enter__(self):
        bus_on()
        return self

    def __exit__(self, exc_type, exc, tb):
        bus_off()
        return False


bus_off()

# ---------------------------------------------------------------------------
# Report helpers
# ---------------------------------------------------------------------------
_results = []


def report(status, name, detail=""):
    _results.append((status, name))
    print("[%-5s] %-22s %s" % (status, name, detail))


def ask(prompt, interactive, seconds=8):
    """Operator step. Interactive: wait for Enter, return the typed text.
    Otherwise print the instruction and give the operator `seconds`."""
    if interactive:
        return input(">>> " + prompt + " [Enter] ").strip().lower()
    print(">>> " + prompt + "  (%d s)" % seconds)
    time.sleep(seconds)
    return ""


def operator_check(name, what, interactive):
    """Interactive: operator types y/n. Otherwise: CHECK."""
    if interactive:
        a = input(">>> %s - seen? [y/n] " % what).strip().lower()
        report("PASS" if a.startswith("y") else "FAIL", name, what)
    else:
        report("CHECK", name, what)


# ---------------------------------------------------------------------------
# 1. Identity, flash, PSRAM (v1 bring-up log checks, still valid on v2)
# ---------------------------------------------------------------------------
def test_identity():
    u = os.uname()
    ok = "ESP32S3" in u.machine.replace("-", "").upper()
    report("PASS" if ok else "FAIL", "chip", u.machine)
    print("        micropython %s, script %s" % (u.release, SCRIPT_VERSION))
    # Base MAC = unit serial (CLAUDE.md naming). Shown at runtime only:
    # copy it to the results sheet, never into a tracked file.
    print("        unit serial (base MAC) %s"
          % ":".join("%02x" % b for b in machine.unique_id()))
    print("        cpu %d MHz, reset cause %d"
          % (machine.freq() // 1000000, machine.reset_cause()))
    if esp32 is not None and hasattr(esp32, "mcu_temperature"):
        print("        die temperature %d C" % esp32.mcu_temperature())


def test_flash():
    if esp is None:
        report("SKIP", "flash size", "no esp module")
        return
    mb = esp.flash_size() // (1024 * 1024)
    if mb == 8:
        report("PASS", "flash size", "8 MB (N8R2)")
    elif mb == 16:
        report("FAIL", "flash size", "16 MB: N16R8 fitted, not the BOM N8R2")
    else:
        report("FAIL", "flash size", "%d MB, expected 8" % mb)


def test_psram():
    gc.collect()
    total = gc.mem_free() + gc.mem_alloc()
    # Internal SRAM alone gives a heap of a few hundred kB; quad PSRAM
    # (2 MB) lifts it to ~2 MB (v1 log: ~2 MB free).
    if total < 1500000:
        report("FAIL", "PSRAM", "heap %d kB: no PSRAM (octal build?)"
               % (total // 1024))
        return
    try:
        buf = bytearray(1000000)
        for i in range(0, len(buf), 997):
            buf[i] = (i >> 3) & 0xFF
        bad = 0
        for i in range(0, len(buf), 997):
            if buf[i] != (i >> 3) & 0xFF:
                bad += 1
        del buf
        gc.collect()
    except MemoryError:
        report("FAIL", "PSRAM", "1 MB allocation failed")
        return
    report("PASS" if bad == 0 else "FAIL", "PSRAM",
           "heap %d kB, 1 MB strided r/w errors %d" % (total // 1024, bad))


# ---------------------------------------------------------------------------
# 2. Rev B regression on the header pins and the status LED (S-v2-4)
# ---------------------------------------------------------------------------
def test_header_sweep():
    """PU/PD sweep: each J3/J4 pin must follow its internal pull (no
    shorts, no stuck pins). Run with nothing plugged into J3/J4, except a
    Qwiic device: its own pull-ups make IO8/IO9 read 1 with PD (reported)."""
    bad = []
    ext_pu = []
    for g in HEADER_GPIO:
        p = Pin(g, Pin.IN, Pin.PULL_UP)
        time.sleep_ms(2)
        up = p.value()
        p.init(Pin.IN, Pin.PULL_DOWN)
        time.sleep_ms(2)
        down = p.value()
        p.init(Pin.IN, pull=None)
        if up == 1 and down == 0:
            continue
        if g in (QWIIC_SDA, QWIIC_SCL) and up == 1 and down == 1:
            ext_pu.append(g)
        else:
            bad.append("IO%d(PU=%d,PD=%d)" % (g, up, down))
    detail = "IO8-14, IO21, IO43/44"
    if ext_pu:
        detail += "; external pull-up on IO%s (Qwiic plugged)" % ext_pu
    report("FAIL" if bad else "PASS", "J3/J4 pull sweep",
           " ".join(bad) if bad else detail)


def test_status_led(interactive):
    led = Pin(IO_STATUS_LED, Pin.OUT, value=1)
    for _ in range(5):
        led.value(0)
        time.sleep_ms(200)
        led.value(1)
        time.sleep_ms(200)
    operator_check("status LED D4", "red D4 blinked 5x (lens out of the "
                   "card edge), green D3 on", interactive)


# ---------------------------------------------------------------------------
# 3. Host sidebands (G9; review mcu_io-7)
# ---------------------------------------------------------------------------
def test_w_disable2(interactive, window_s=10):
    """IO40 = inverted W_DISABLE2# (pin 26). Interactive: the operator sets
    the host line both ways. Otherwise: sample for window_s and report
    every state seen, so the operator can toggle it during the window."""
    p = Pin(IO_WDIS2, Pin.IN, pull=None)   # R30 10k pull-up on the card
    if interactive:
        ask("Pin 26 released / driven HIGH (dev carrier: JP5 open)", True)
        a = p.value()
        ask("Pin 26 pulled LOW (dev carrier: fit JP5)", True)
        b = p.value()
        ask("Release pin 26 again (remove JP5)", True)
        ok = (a == 0 and b == 1)
        report("PASS" if ok else "FAIL", "W_DISABLE2# -> IO40",
               "released IO40=%d (want 0), low IO40=%d (want 1)" % (a, b))
        return
    print(">>> toggle pin 26 (JP5 on/off) during the next %d s" % window_s)
    seen = set()
    changes = 0
    last = p.value()
    seen.add(last)
    t0 = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), t0) < window_s * 1000:
        v = p.value()
        if v != last:
            changes += 1
            last = v
            seen.add(v)
        time.sleep_ms(5)
    state = "radio KILL (pin 26 low)" if last else "radio allowed (pin 26 high)"
    if seen == {0, 1}:
        report("PASS", "W_DISABLE2# -> IO40",
               "both states seen, %d changes; now %s" % (changes, state))
    else:
        report("CHECK", "W_DISABLE2# -> IO40",
               "IO40=%d only: %s. Toggle pin 26 to test" % (last, state))


def test_host_outputs(interactive):
    """Distinct patterns so a swapped pin 10 / pin 23 path (firmware GPIO
    table or carrier wiring) shows: LED_1# = 5 slow blinks (1 Hz), WAKE# =
    3 short pulses + one 1 s pulse. A 180 deg Q2 is electrically equivalent
    (cross-drained SOT-563: each gate keeps its own drain), so it cannot
    swap them."""
    led1 = Pin(IO_LED1, Pin.OUT, value=0)
    wake = Pin(IO_WAKE, Pin.OUT, value=0)
    print(">>> LED_1# (pin 10): 5 x 0.5 s low, 1 Hz")
    for _ in range(5):
        led1.value(1)
        time.sleep_ms(500)
        led1.value(0)
        time.sleep_ms(500)
    operator_check("LED_1# pin 10", "pin 10 pulsed low 5x at 1 Hz "
                   "(dev carrier D5 blinked)", interactive)
    print(">>> WAKE_ON_WWAN# (pin 23): 3 x 100 ms low, then 1 x 1 s low")
    for _ in range(3):
        wake.value(1)
        time.sleep_ms(100)
        wake.value(0)
        time.sleep_ms(400)
    wake.value(1)
    time.sleep_ms(1000)
    wake.value(0)
    operator_check("WAKE_ON_WWAN# pin 23", "pin 23: 3 short + 1 long low "
                   "pulse (dev carrier D6 with JP6)", interactive)
    # Leave both outputs released (pins 10/23 high-Z on the edge).
    led1.value(0)
    wake.value(0)


# ---------------------------------------------------------------------------
# 4. Expansion bus: hold-off, release, ID EEPROM, loopback (S-v2-1, S-v2-2)
# ---------------------------------------------------------------------------
def _crc32(data):
    try:
        import binascii
        return binascii.crc32(data) & 0xFFFFFFFF
    except (ImportError, AttributeError):
        crc = 0xFFFFFFFF
        for b in data:
            crc ^= b
            for _ in range(8):
                crc = (crc >> 1) ^ (0xEDB88320 if crc & 1 else 0)
        return crc ^ 0xFFFFFFFF


def _i2c():
    # EXP_0 = SDA, EXP_1 = SCL. Card pull-ups R20/R21 sit on the MCU side,
    # so an off bus just gives no ACK (never a stuck bus).
    return SoftI2C(scl=Pin(EXP_GPIO[1]), sda=Pin(EXP_GPIO[0]), freq=100000)


def _release_i2c_pins():
    Pin(EXP_GPIO[0], Pin.IN, pull=None)
    Pin(EXP_GPIO[1], Pin.IN, pull=None)


def eeprom_present():
    try:
        return EEPROM_ADDR in _i2c().scan()
    finally:
        _release_i2c_pins()


def _drive_pair(a, b):
    """Return True if line a reaches line b both ways (b follows a high
    against its pull-down and low against its pull-up), False if b ignores
    a both ways, None for a mixed (faulty) result. Also returns the list of
    other EXP_2..11 lines that followed a (shorts)."""
    ga, gb = EXP_GPIO[a], EXP_GPIO[b]
    others = [i for i in range(2, 12) if i not in (a, b)]
    pa = Pin(ga, Pin.OUT, value=1)
    pb = Pin(gb, Pin.IN, Pin.PULL_DOWN)
    po = [Pin(EXP_GPIO[i], Pin.IN, Pin.PULL_DOWN) for i in others]
    time.sleep_us(200)
    hi = pb.value() == 1
    shorts = [others[k] for k, p in enumerate(po) if p.value() == 1]
    pa.value(0)
    pb.init(Pin.IN, Pin.PULL_UP)
    time.sleep_us(200)
    lo = pb.value() == 0
    for g in [ga, gb] + [EXP_GPIO[i] for i in others]:
        Pin(g, Pin.IN, pull=None)
    if hi and lo:
        return True, shorts
    if not hi and not lo:
        return False, shorts
    return None, shorts


def _loop01():
    """EXP_0 <-> EXP_1 jumper (no EEPROM): open-drain low on one, read the
    other (both have 4k7 card pull-ups). Both directions."""
    res = []
    for drv, rcv in ((0, 1), (1, 0)):
        d = Pin(EXP_GPIO[drv], Pin.OPEN_DRAIN, value=0)
        r = Pin(EXP_GPIO[rcv], Pin.IN, pull=None)
        time.sleep_us(200)
        res.append(r.value() == 0)
        d.value(1)
    _release_i2c_pins()
    if all(res):
        return True
    if not any(res):
        return False
    return None


def bus_evidence(loopback, loop01):
    """What the fixtures say about the bus. True = on, False = off,
    None = no fixture fitted (cannot tell). Returns (state, text)."""
    seen = []
    if loop01:
        s = _loop01()
        seen.append(s)
        txt = "EXP_0<->EXP_1 %s" % {True: "conducts", False: "open",
                                     None: "MIXED"}[s]
    else:
        s = eeprom_present()
        txt = "EEPROM 0x50 %s" % ("ACK" if s else "no ACK")
        if s:
            seen.append(True)
    if loopback:
        conducting = 0
        for a, b in LOOP_PAIRS:
            s, _ = _drive_pair(a, b)
            if s:
                conducting += 1
            seen.append(s)
        txt += ", loopback %d/%d pairs conduct" % (conducting,
                                                   len(LOOP_PAIRS))
    if any(s is True for s in seen):
        return True, txt
    if seen and all(s is False for s in seen):
        return False, txt
    if any(s is None for s in seen):
        return None, txt + " (MIXED)"
    return None, txt + " (no fixture: cannot see the bus)"


def parse_eeprom(img):
    """Format v1 (docs/v2-gate-v1.md §2). Prints the header, returns
    True if magic, version and CRC are valid and the map is legal."""
    magic = bytes(img[0:4])
    if magic == b"\xff\xff\xff\xff":
        print("        EEPROM blank (0xFF): run main(..., program=True)")
        return False
    crc_stored = int.from_bytes(img[0xFC:0x100], "little")
    crc_calc = _crc32(bytes(img[0:0xFC]))
    print("        magic %r  format %d  flags 0x%02x" % (magic, img[4], img[5]))
    print("        vendor 0x%04x  product 0x%04x  revision %r"
          % (int.from_bytes(img[6:8], "little"),
             int.from_bytes(img[8:10], "little"), chr(img[10])))
    print("        serial 0x%016x" % int.from_bytes(img[0x0C:0x14], "little"))
    name = bytes(img[0x2C:0x4C]).split(b"\0")[0]
    print("        name %r" % name)
    print("        CRC stored 0x%08x calc 0x%08x" % (crc_stored, crc_calc))
    fmap = [(img[0x14 + 2 * i], img[0x15 + 2 * i]) for i in range(12)]
    print("        map " + " ".join("%d:%02x/%02x" % (i, f, p)
                                    for i, (f, p) in enumerate(fmap)))
    illegal = []
    for i, (f, _) in enumerate(fmap):
        if f == 0x06 and i not in ADC_EXP:
            illegal.append("EXP_%d analog" % i)
        if f in (0x07, 0x08) and i not in (0, 1):
            illegal.append("EXP_%d I2C" % i)
    if fmap[0][0] not in (0x00, 0x07) or fmap[1][0] not in (0x00, 0x08):
        illegal.append("EXP_0/1 must be I2C")
    if illegal:
        print("        refused: " + ", ".join(illegal))
    return (magic == b"M2CI" and img[4] == 1 and crc_stored == crc_calc
            and not illegal)


def dev_image(name=b"m2-dev-carrier test image"):
    """A format-v1 test image: vendor 0xFFFF (dev), EXP_0/1 = I2C, every
    other line unused (stays high-Z). Product ID 0 = not assigned."""
    img = bytearray(256)
    img[0:4] = b"M2CI"
    img[4] = 1
    img[6:8] = (0xFFFF).to_bytes(2, "little")
    img[10] = ord("A")
    img[0x14], img[0x16] = 0x07, 0x08
    img[0x2C:0x2C + len(name)] = name[:32]
    img[0xFC:0x100] = _crc32(bytes(img[0:0xFC])).to_bytes(4, "little")
    return img


def program_eeprom(img):
    """Write 256 B in 8-byte pages and verify. 8 bytes is the smallest
    24C02 page (AT24C02; M24C02 has 16), so every 24C02-class part the
    contract allows works. tW <= 5 ms. Needs /WC low (the dev carrier ties
    /WC to GND). Bus must be on."""
    i2c = _i2c()
    try:
        for off in range(0, 256, 8):
            i2c.writeto_mem(EEPROM_ADDR, off, img[off:off + 8])
            time.sleep_ms(6)
        back = i2c.readfrom_mem(EEPROM_ADDR, 0, 256)
    finally:
        _release_i2c_pins()
    return bytes(back) == bytes(img)


def test_bus(signature, loopback, loop01, program, window_s, interactive):
    """A: held off -> B: released -> EEPROM / loopback -> C: held off.
    A and C can only be judged once B has shown the fixture (EEPROM ACK
    or a conducting loopback), so the verdicts are printed at the end."""
    print("--- expansion bus (signature=%s, loopback=%s, loop01=%s)"
          % (signature, loopback, loop01))
    try:
        bus_off()                                   # A: IO38 high
        a, a_txt = bus_evidence(loopback, loop01)
        bus_on()                                    # B: IO38 low
        b, b_txt = bus_evidence(loopback, loop01)
        if b is None:
            report("SKIP" if "no fixture" in b_txt else "FAIL",
                   "B released (IO38=0)", b_txt)
        elif signature is None:
            report("CHECK", "B released (IO38=0)",
                   b_txt + " -> bus %s" % ("ON" if b else "OFF"))
        else:
            report("PASS" if b == signature else "FAIL", "B released (IO38=0)",
                   b_txt + " (want %s)" % ("ON" if signature else "OFF"))

        # EEPROM read (bus released; only EXP_0/1 touched).
        if b is True and not loop01:
            if eeprom_present():
                if program:
                    ok = program_eeprom(dev_image())
                    report("PASS" if ok else "FAIL", "EEPROM program",
                           "dev image written + verified" if ok else
                           "verify failed")
                try:
                    img = _i2c().readfrom_mem(EEPROM_ADDR, 0, 256)
                finally:
                    _release_i2c_pins()
                valid = parse_eeprom(img)
                report("PASS" if valid else "FAIL", "EEPROM header",
                       "valid M2CI v1" if valid else
                       "invalid -> carrier 'unknown', lines stay high-Z")
            else:
                report("SKIP", "EEPROM header", "no ACK at 0x50")

        # Loopback detail, both directions, plus cross-short check (S-v2-2).
        if loopback and b is True:
            bad = []
            for p, q in LOOP_PAIRS:
                for drv, rcv in ((p, q), (q, p)):
                    s, shorts = _drive_pair(drv, rcv)
                    if s is not True:
                        bad.append("EXP_%d->EXP_%d %s" % (drv, rcv, s))
                    if shorts:
                        bad.append("EXP_%d shorts EXP_%s" % (drv, shorts))
            report("FAIL" if bad else "PASS", "loopback EXP_2..11",
                   "; ".join(bad) if bad else
                   "10 lines, both directions, no cross-shorts")
        if loop01 and b is True:
            report("PASS" if _loop01() is True else "FAIL", "loopback EXP_0/1",
                   "open-drain, both directions")

        # Optional manual window: bus released, operator measures (procedure).
        if window_s:
            ask("bus RELEASED for %d s: measure now" % window_s, interactive,
                window_s)

        bus_off()                                   # C: IO38 high again
        c, c_txt = bus_evidence(loopback, loop01)

        # Verdicts. Off-evidence counts only if the fixture was proven in B.
        proven = b is True
        for name, st, txt in (("A hold-off (IO38=1)", a, a_txt),
                              ("C re-hold (IO38=1)", c, c_txt)):
            if st is True:
                report("FAIL", name, txt + " -> bus ON while held")
            elif proven or st is False:
                report("PASS", name, txt + " -> bus off")
            else:
                report("SKIP", name, txt + " -> fixture never seen, cannot judge")
    finally:
        bus_off()                               # IO38 high on every way out


# ---------------------------------------------------------------------------
# 5. Radio (S-v2-4 / SPEC §10.5 proxy), honouring W_DISABLE2#
# ---------------------------------------------------------------------------
def test_wifi():
    if Pin(IO_WDIS2, Pin.IN).value() == 1:
        report("PASS", "radio kill honoured",
               "W_DISABLE2# asserted -> WiFi not started")
        return
    try:
        import network
        w = network.WLAN(network.STA_IF)
        w.active(True)
        aps = w.scan()
        w.active(False)
    except Exception as e:
        report("FAIL", "WiFi scan", repr(e))
        return
    if aps:
        best = max(ap[3] for ap in aps)
        report("PASS", "WiFi scan", "%d APs, strongest %d dBm"
               % (len(aps), best))
    else:
        report("CHECK", "WiFi scan", "0 APs: no AP in range, or RF fault")


# ---------------------------------------------------------------------------
# 6. Qwiic I2C (SPEC §10.4 proxy)
# ---------------------------------------------------------------------------
def test_qwiic():
    sda = Pin(QWIIC_SDA, Pin.IN, pull=None)
    scl = Pin(QWIIC_SCL, Pin.IN, pull=None)
    time.sleep_ms(2)
    if not (sda.value() and scl.value()):
        report("SKIP", "Qwiic I2C (J3)", "no pull-ups seen: nothing plugged")
        return
    found = SoftI2C(scl=scl, sda=sda, freq=100000).scan()
    Pin(QWIIC_SDA, Pin.IN, pull=None)
    Pin(QWIIC_SCL, Pin.IN, pull=None)
    report("PASS" if found else "FAIL", "Qwiic I2C (J3)",
           "devices %s" % [hex(a) for a in found])


# ---------------------------------------------------------------------------
def main(signature=None, loopback=False, loop01=False, program=False,
         window=0, interactive=False, outputs=True, wifi=True):
    """signature: True = CONFIG_2/3 grounded (dev carrier JP2/JP3 on GND),
                  False = not grounded (open / 1V8 / 3V3, or a normal host),
                  None = unknown (report only).
    loopback:  dev-carrier J3 jumpers EXP_2-3, 4-5, 6-7, 8-9, 10-11 fitted.
    loop01:    J3 jumper EXP_0-EXP_1 fitted (EEPROM disconnected).
    program:   write the dev test image into a blank EEPROM first.
    window:    seconds to leave the bus released for manual measurement.
    interactive: wait for the operator (use from `mpremote repl`)."""
    del _results[:]
    print("=" * 64)
    print("v2.0 Rev A self-test  %s" % SCRIPT_VERSION)
    print("=" * 64)
    try:
        test_identity()
        test_flash()
        test_psram()
        test_header_sweep()
        test_status_led(interactive)
        test_w_disable2(interactive)
        if outputs:
            test_host_outputs(interactive)
        test_bus(signature, loopback, loop01, program, window, interactive)
        if wifi:
            test_wifi()
        test_qwiic()
    finally:
        bus_off()                     # IO38 high, EXP lines high-Z
        Pin(IO_LED1, Pin.OUT, value=0)
        Pin(IO_WAKE, Pin.OUT, value=0)
    n = {}
    for s, _ in _results:
        n[s] = n.get(s, 0) + 1
    print("-" * 64)
    print("SUMMARY  " + "  ".join("%s %d" % (k, n.get(k, 0))
                                  for k in ("PASS", "FAIL", "SKIP", "CHECK")))
    print("RESULT   %s" % ("FAIL" if n.get("FAIL") else
                           "PASS (tick the CHECK items by hand)"
                           if n.get("CHECK") else "PASS"))
    print("bus held off (IO38=1) on exit")
    return n.get("FAIL", 0) == 0


if __name__ == "__main__":
    main()
