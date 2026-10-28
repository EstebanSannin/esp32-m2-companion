"""Callout definitions shared by gen_views (figures) and gen_datasheet
(legend tables) so they cannot drift apart."""

TOP_CALLOUTS = [
    ("U2", "ESP32-S3-WROOM-1-N8R2 module"),
    ("ANT", "Module PCB antenna + RF keep-out zone"),
    ("J4", "J4 - UART / SPI / GPIO (JST SH-8, top entry)"),
    ("J3", "J3 - Qwiic / STEMMA-QT I2C (JST SH-4, top entry)"),
    ("J1", "M.2 Key-B card edge (USB 2.0, sidebands, 12 switched EXP pins)"),
    ("SCR", "Mounting notch (M.2 screw; routed, no copper)"),
]
BOT_CALLOUTS = [
    ("U6", "eFuse + over-voltage cut-off on the M.2 3.3 V input (TPS259470A)"),
    ("FB1", "3.3 V filter bead after the eFuse"),
    ("U3", "Edge-expansion switches U3-U5 (TMUX1511): EXP_0..11 high-Z until a carrier is detected AND firmware releases the bus"),
    ("Q1", "Carrier detect (CONFIG_2/3 both low -> EXP_OE)"),
    ("Q2", "Host sideband cells Q2/Q3a (LED_1#, WAKE_ON_WWAN#, W_DISABLE2#) + Q3b bus hold-off (IO38)"),
    ("RN1", "Series resistor arrays RN1-RN3 (MCU side of the switches)"),
    ("U1", "USBLC6-2 USB ESD protection"),
    ("D1", "Recovery diodes (EN <- pin 50; IO0 <- pins 20 + 8)"),
    ("TP1", "Test points EN / BOOT"),
    ("D3", "Power LED (green, side-view, left edge; silk bar = K)"),
    ("D4", "Status LED (red, IO48, side-view; silk bar = K)"),
]
