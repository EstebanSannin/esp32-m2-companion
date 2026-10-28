# Polarity / pin-1 checklist (generated - verify each row against the JLC placement preview BEFORE ordering)

Corners are N/S plus TOP-VIEW E/W: N = toward the screw-notch edge, S = toward the gold fingers, E/W as seen from the top side (bottom parts seen through the board). JLC's bottom-side preview is seen from below, so E/W appear swapped there: N/S never change, E/W flip on bottom parts.

| Ref | Side | Value | Must see in preview | Net | Preview OK? |
|---|---|---|---|---|---|
| D1 | bottom | BAT54A | pin 1 = cathode-1 (BAT54A common-anode SOT-23: pins 1,2 = K, 3 = A); pin 1 at the SW corner, net PERST_n | PERST_n | [ ] |
| D2 | bottom | BAT54A | pin 1 = cathode-1 (BAT54A common-anode SOT-23: pins 1,2 = K, 3 = A); pin 1 at the SW corner, net PCIE_1_GPIO_5 | PCIE_1_GPIO_5 | [ ] |
| D3 | bottom | green | '+' (anode) on the S pad = the one level with R3.2 (net LED_PWR_A); cathode mark toward N; AND the lens (emitting face) faces OUTWARD - away from R3, toward the card's long edge (GATE B3: both must hold at once) | LED_PWR_A | [ ] |
| D4 | bottom | red | '+' (anode) on the S pad = the one level with R4.2 (net LED_STATUS_A); cathode mark toward N; AND the lens (emitting face) faces OUTWARD - away from R4, toward the card's long edge (GATE B3: both must hold at once) | LED_STATUS_A | [ ] |
| J3 | top | Conn_01x04 | pin 1 = GND (Qwiic order GND, 3V3, SDA, SCL); pin 1 at the SW corner, net GND | GND | [ ] |
| J4 | top | Conn_01x08 | pin 1 = TXD0; pin 1 at the SW corner, net TXD0 | TXD0 | [ ] |
| Q1 | bottom | SSM6N56FE | pin 1 = S1 (SSM6N56FE ES6; pin-1 mark, silk triangle) - 180 off is electrically equivalent (cross-drained: each gate keeps its own drain; pad 4 is GND too, so the GND cue cannot tell); only a 90 error fails (pads would not land) - record, do not hold the order on 180; pin 1 at the NE corner, net GND | GND | [ ] |
| Q2 | bottom | SSM6N56FE | pin 1 = S1 (SSM6N56FE ES6; pin-1 mark, silk triangle) - 180 off is electrically equivalent (cross-drained: each gate keeps its own drain; pad 4 is GND too, so the GND cue cannot tell); only a 90 error fails (pads would not land) - record, do not hold the order on 180; pin 1 at the NE corner, net GND | GND | [ ] |
| Q3 | bottom | SSM6N56FE | pin 1 = S1 (SSM6N56FE ES6; pin-1 mark, silk triangle) - 180 off is electrically equivalent (cross-drained: each gate keeps its own drain; pad 4 is GND too, so the GND cue cannot tell); only a 90 error fails (pads would not land) - record, do not hold the order on 180; pin 1 at the NE corner, net GND | GND | [ ] |
| RN1 | bottom | 220R | array: only the 90 deg matters (pads must land; 4 x 220R); pin 1 at the NE corner, net IO39 | IO39 | [ ] |
| RN2 | bottom | 220R | array: only the 90 deg matters (pads must land; 4 x 220R); pin 1 at the SW corner, net IO18 | IO18 | [ ] |
| RN3 | bottom | 220R | array: only the 90 deg matters (pads must land; 4 x 220R); pin 1 at the SW corner, net IO7 | IO7 | [ ] |
| U1 | bottom | USBLC6-2SC6 | pin 1 = I/O1 (USBLC6-2SC6; package pin-1 mark). Land is 180-symmetric: 180 off puts GND (pin 2) on +3V3 and VBUS (pin 5) on GND = dead card - must be right; pin 1 at the SW corner, net USBH3_D_P | USBH3_D_P | [ ] |
| U2 | top | ESP32-S3-WROOM-1 | module pin 1 = GND (antenna end toward N); pin 1 at the NW corner, net GND | GND | [ ] |
| U3 | bottom | TMUX1511_RSV | pin 1 = SEL1 (TMUX1511 RSV; package pin-1 dot); pin 1 at the SE corner, net EXP_OE | EXP_OE | [ ] |
| U4 | bottom | TMUX1511_RSV | pin 1 = SEL1 (TMUX1511 RSV; package pin-1 dot); pin 1 at the NE corner, net EXP_OE | EXP_OE | [ ] |
| U5 | bottom | TMUX1511_RSV | pin 1 = SEL1 (TMUX1511 RSV; package pin-1 dot); pin 1 at the NE corner, net EXP_OE | EXP_OE | [ ] |
| U6 | bottom | TPS259470A_RPW | pin 1 = EN/UVLO (TPS259470A RPW; L-shaped corner pad, pin-1 dot); pin 1 at the NE corner, net EFUSE_EN | EFUSE_EN | [ ] |
