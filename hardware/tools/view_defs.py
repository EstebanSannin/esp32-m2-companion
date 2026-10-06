"""Callout definitions shared by gen_views (figures) and gen_datasheet
(legend tables) so they cannot drift apart."""

TOP_CALLOUTS = [
    ("U2", "ESP32-S3-WROOM-1-N8R2 module"),
    ("ANT", "Module PCB antenna + RF keep-out zone"),
    ("J4", "J4 - UART / SPI / GPIO (JST SH-8, top entry)"),
    ("J3", "J3 - Qwiic / STEMMA-QT I2C (JST SH-4, top entry)"),
    ("J1", "M.2 Key-B card edge (75-pos, USB 2.0 + sidebands)"),
    ("SCR", "Mounting notch (M.2 screw; routed, no copper)"),
]
BOT_CALLOUTS = [
    ("U1", "USBLC6-2 USB ESD protection"),
    ("FB1", "3.3 V entry filter + bulk capacitors"),
    ("D1", "Recovery diodes (EN <- pin 50; IO0 <- pins 20 + 8)"),
    ("TP1", "Test points (silk: EN BOOT TX RX 3V3 GND)"),
    ("R7", "USB series resistors (0R)"),
    ("D3", "Power LED (green, side-view, left edge; silk bar = K)"),
    ("D4", "Status LED (red, IO48, side-view; silk bar = K)"),
    ("C6", "Module 3V3 decoupling"),
    ("R5", "DNP provisions (I2C pull-ups, USB shunt C)"),
]
