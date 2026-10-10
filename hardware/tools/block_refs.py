"""Part -> block map, shared by gen_sch (schematic sheets) and gen_connections
(per-block connection tables) so the two review artifacts cannot drift.
Explicit designators: skidl 2.3 has no usable hierarchy attribute."""

BLOCK_REFS = {
    "m2_keyb_edge": {"J1"},
    "power_3v3": {"FB1", "C1", "C2", "C3",
                  "U6", "R31", "R32", "R33", "R34", "C14"},
    "usb_esd": {"U1", "C4"},
    "sideband_recovery": {"R1", "R2", "C5", "D1", "D2", "TP1", "TP2"},
    "esp32s3_companion": {"U2", "C6", "C7"},
    "leds": {"R3", "R4", "D3", "D4"},
    "io_header": {"J3", "J4"},
    # v2.0 Rev A (ADR 0006)
    "edge_expansion": {"RN1", "RN2", "RN3", "R20", "R21", "U3", "U4",
                       "U5", "C10", "C11", "C12", "R22", "R23", "R24",
                       "R25", "Q1", "R26", "C13"},
    "host_sideband": {"Q2", "Q3", "R27", "R28", "R29", "R30"},
}

ORDER = ["m2_keyb_edge", "power_3v3", "usb_esd", "sideband_recovery",
         "esp32s3_companion", "leds", "io_header", "edge_expansion",
         "host_sideband"]

TITLES = {
    "m2_keyb_edge": "M.2 KEY-B 2242 EDGE",
    "power_3v3": "POWER 3V3 + eFUSE (SPEC 6.2, ADR 0007)",
    "usb_esd": "USB + ESD (SPEC 6.3)",
    "sideband_recovery": "SIDEBAND RECOVERY (ADR 0002)",
    "esp32s3_companion": "ESP32-S3 MODULE",
    "leds": "LEDS (ADR 0003)",
    "io_header": "IO CONNECTORS (ADR 0005)",
    "edge_expansion": "EXPANSION BUS + CARRIER DETECT (ADR 0006)",
    "host_sideband": "HOST SIDEBANDS (ADR 0006)",
}


def block_of(ref):
    for b, refs in BLOCK_REFS.items():
        if ref in refs:
            return b
    return "misc"
