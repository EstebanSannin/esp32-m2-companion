"""v2.0 Rev A bring-up boot.py (MicroPython): hold the expansion bus off.

MicroPython runs boot.py on every boot and on every soft reset (Ctrl-D),
before main.py and before the REPL. Its only statement drives IO38 HIGH,
which turns Q3b on, pulls EXP_OE low and keeps all 12 EXP switches off
(docs/carrier-interface.md §4.3.1, firmware rule 5; docs/pinmap.md §6.3).

Why it is needed (RC1 delta review bus_enable-1): a chip reset (EN/PERST#,
brown-out, power-up) returns IO38 to input and R35 holds the bus off by
itself, but on the ESP32-S3 a software or watchdog reset (machine.reset(),
WDT, panic) is a CPU-only reset that most likely keeps IO38 driven, and a
MicroPython soft reset does not touch GPIOs at all. Stock MicroPython never
drives IO38, so without this file a released bus would stay on. Whether
the CPU reset really keeps IO38 low is still to be measured (SPEC S-v2-2,
procedure 8.5).

Install: mpremote connect <port> cp v2/firmware/boot.py :
Release the bus only on purpose (v2_selftest.bus_on(), or main()).
"""

from machine import Pin

Pin(38, Pin.OUT, value=1)   # IO38 high = bus held off (Q3b on, R35 pull-up)
