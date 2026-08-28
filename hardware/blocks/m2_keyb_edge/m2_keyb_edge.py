"""M.2 Key-B 2242 card-edge gold fingers.

Pin table: docs/pinmap.md §1, cross-checked
  - Mallow V1.1 datasheet Table 10 (X17)
  - Quectel RM50xQ HW Design V1.2 Fig. 2 (standard WWAN Key-B usage)

The edge is a PCB feature (no BOM part). Footprint is a placeholder until
Phase 2 draws the gold-finger geometry.

Positions 12-19 are the Key-B notch: no pins exist there.
Pin 75 (CONFIG_2) is not listed in Mallow Table 10; kept NC.
"""

from skidl import Part, Pin, SKIDL, TEMPLATE

# name, number(s), pin function
_PWRIN = Pin.types.PWRIN
_BIDIR = Pin.types.BIDIR
_IN = Pin.types.INPUT
_NC = Pin.types.NOCONNECT

_PINS = [
    # (number, name, func)  -- names follow Mallow X17 verbatim where wired,
    # M.2 WWAN standard names otherwise ('#' -> '_n').
    (1, "CONFIG_3", _NC),
    (2, "VCC_3V3", _PWRIN),
    (3, "GND", _PWRIN),
    (4, "VCC_3V3", _PWRIN),
    (5, "GND", _PWRIN),
    (6, "FULL_CARD_POWER_OFF_n", _NC),   # no documented driver on Mallow
    (7, "USBH3_D_P", _BIDIR),
    (8, "W_DISABLE1_n", _IN),            # BOOT source (diode-OR), ADR 0002
    (9, "USBH3_D_N", _BIDIR),
    (10, "WWAN_LED_n", _NC),
    (11, "GND", _PWRIN),
    # 12-19: notch
    (20, "PCIE_1_GPIO_5", _IN),          # BOOT source via Mallow X16.19 jumper
    (21, "CONFIG_0", _NC),
    (22, "PCIE_1_GPIO_6", _NC),
    (23, "PCIE_1_GPIO_11", _NC),
    (24, "PCIE_1_GPIO_7", _NC),
    (25, "DPR", _NC),
    (26, "PCIE_1_GPIO_10", _NC),
    (27, "GND", _PWRIN),
    (28, "PCIE_1_GPIO_8", _NC),
    (29, "USBH3_SSRX_N", _NC),
    (30, "PCIE_1_UIM_RESET", _NC),
    (31, "USBH3_SSRX_P", _NC),
    (32, "PCIE_1_UIM_CLK", _NC),
    (33, "GND", _PWRIN),
    (34, "PCIE_1_UIM_DATA", _NC),
    (35, "USBH3_SSTX_N", _NC),
    (36, "PCIE_1_UIM_PWR", _NC),
    (37, "USBH3_SSTX_P", _NC),
    (38, "SDX2AP_STATUS", _NC),
    (39, "GND", _PWRIN),
    (40, "PCIE_1_GPIO_0", _NC),
    (41, "PCIE_1_L0_RX_N", _NC),
    (42, "PCIE_1_GPIO_1", _NC),
    (43, "PCIE_1_L0_RX_P", _NC),
    (44, "PCIE_1_GPIO_2", _NC),
    (45, "GND", _PWRIN),
    (46, "PCIE_1_GPIO_3", _NC),
    (47, "PCIE_1_L0_TX_N", _NC),
    (48, "PCIE_1_GPIO_4", _NC),
    (49, "PCIE_1_L0_TX_P", _NC),
    (50, "PERST_n", _IN),                # EN source, SODIMM 244 (ADR 0002)
    (51, "GND", _PWRIN),
    (52, "PCIE_CLKREQ_n", _NC),
    (53, "PCIE_1_CLK_N", _NC),
    (54, "PCIE_1_WAKE_n", _NC),          # 1.8 V domain on Mallow - keep NC
    (55, "PCIE_1_CLK_P", _NC),
    (56, "RFFE_CLK", _NC),
    (57, "GND", _PWRIN),
    (58, "RFFE_DATA", _NC),
    (59, "LAA_TX_EN", _NC),
    (60, "WLAN_TX_EN", _NC),
    (61, "ANTCTL1", _NC),
    (62, "COEX_RXD", _NC),
    (63, "ANTCTL2", _NC),
    (64, "COEX_TXD", _NC),
    (65, "RFFE_VIO_1V8", _NC),
    (66, "PCIE_1_UIM_CD", _NC),
    (67, "M2_CARD_RESET_n", _NC),        # 1.8 V domain, driver undocumented
    (68, "AP2SDX_STATUS", _NC),
    (69, "CONFIG_1", _NC),
    (70, "VCC_3V3", _PWRIN),
    (71, "GND", _PWRIN),
    (72, "VCC_3V3", _PWRIN),
    (73, "GND", _PWRIN),
    (74, "VCC_3V3", _PWRIN),
    (75, "CONFIG_2", _NC),
]


def m2_keyb_edge_template():
    """Return a TEMPLATE Part for the M.2 Key-B 2242 edge fingers."""
    part = Part(
        name="M2_KEYB_2242_EDGE",
        tool=SKIDL,
        dest=TEMPLATE,
        ref_prefix="J",
        tag="J_M2",
        description="M.2 Key-B 2242 card edge gold fingers (PCB feature)",
        footprint="esp32m2:M2_KeyB_2242_EdgeFingers",  # drawn in Phase 2
    )
    part.fields["LCSC"] = ""          # PCB feature - no BOM line
    part.fields["JLC"] = "PCB"
    for num, name, func in _PINS:
        part += Pin(num=num, name=name, func=func)
    return part
