"""Hardware-gated carrier expansion bus (ADR 0006, docs/v2-gate-v1.md §1.1-1.2).

  IOxx --220R (RN)-- EXP_n_S --[TMUX1511 Sx..Dx]-- EXP_n (M.2 edge)
                                     SEL1..4 = EXP_OE

Carrier detect (wired-NOR, Toshiba SSM6N56FE):
  CONFIG_2 (pin 75) --1M-- 3V3,  --100k-- CFG2_G = Q1.G1
  CONFIG_3 (pin 1)  --1M-- 3V3,  --100k-- CFG3_G = Q1.G2
  Q1.D1 = Q1.D2 = EXP_OE --10k-- 3V3, --1uF-- GND  (tau ~10 ms)
EXP_OE is high ONLY when both sense pins are at 0 V (our carrier grounds
them). Host pull-ups (1.8 V or 3.3 V) or a floating pin (card 1M pull-up)
turn a FET on -> EXP_OE low -> all switches off. Card unpowered: 3V3 = 0,
TMUX SEL internal 6M pull-downs -> off; host voltage only reaches insulated
FET gates; only the 1M CONFIG pull-ups conduct (<= ~3.3 uA per pin into the
unpowered rail - RC1 delta review expansion-8/docs-8).

RC1 (review contract_test-1): EXP_OE is also pulled low by Q3b in
host_sideband (gate = IO38, R35 100k pull-up) until firmware drives IO38
LOW, so the bus is ON only when carrier signature AND firmware agree; it
drops again on any ESP32 reset. IO38 no longer senses EXP_OE.

10k (not 100k): 12 SEL inputs leak up to 12 x 2 uA + 12 x (3.3 V / 6 M)
= ~30 uA worst case (tmux1511.pdf §5.5 IIH, RPD); 100k would sag EXP_OE
below VIH 1.2 V (GATE V1 finding).

I2C pull-ups (EXP_0/EXP_1 = ID-EEPROM bus) sit on the MCU side of the
switch (EXP_n_S), so the edge stays high-Z when the bus is off.
"""

from blocks.common import (C_0603, R_0402, R_0603, R_ARRAY_4X0402, SSM6N56FE,
                           TMUX1511, subcircuit)

# TMUX1511 channel k -> (SELk, Sk, Dk) pin names
_CH = [("SEL1", "S1", "D1"), ("SEL2", "S2", "D2"),
       ("SEL3", "S3", "D3"), ("SEL4", "S4", "D4")]


@subcircuit
def edge_expansion(v3v3, gnd, mcu_ios, edge, exp_s, config_2, config_3,
                   cfg2_g, cfg3_g, exp_oe):
    """mcu_ios / exp_s / edge: lists of 12 nets, index = EXP number."""
    assert len(mcu_ios) == len(exp_s) == len(edge) == 12

    # 220R series, MCU side (3 x 4-element convex arrays)
    for a in range(3):
        rn = R_ARRAY_4X0402("220R", lcsc="C25498", mpn="4D02WGJ0221TCE",
                            ref=f"RN{a + 1}")
        for k in range(4):
            i = a * 4 + k
            rn[f"R{k + 1}a"] += mcu_ios[i]
            rn[f"R{k + 1}b"] += exp_s[i]

    # I2C pull-ups for EXP_0 (SDA) / EXP_1 (SCL), MCU side of the switch
    for i, ref in ((0, "R20"), (1, "R21")):
        r = R_0402("4k7", lcsc="C25900", mpn="0402WGF4701TCE", ref=ref)
        r[1] += v3v3
        r[2] += exp_s[i]

    # Bus switches U3..U5, 4 channels each, all SEL on EXP_OE
    for u_i in range(3):
        u = TMUX1511(ref=f"U{3 + u_i}")
        u["VDD"] += v3v3
        u["GND"] += gnd
        for k, (sel, s, d) in enumerate(_CH):
            i = u_i * 4 + k
            u[sel] += exp_oe
            u[s] += exp_s[i]
            u[d] += edge[i]
        c = C_0603("100nF 50V", lcsc="C14663", mpn="CC0603KRX7R9BB104",
                   ref=f"C{10 + u_i}")
        c[1] += v3v3
        c[2] += gnd

    # Carrier detect
    for sense, gate, r_pu, r_g in ((config_2, cfg2_g, "R22", "R24"),
                                   (config_3, cfg3_g, "R23", "R25")):
        pu = R_0402("1M", lcsc="C26083", mpn="0402WGF1004TCE", ref=r_pu)
        pu[1] += v3v3
        pu[2] += sense
        rg = R_0402("100k", lcsc="C25741", mpn="0402WGF1003TCE", ref=r_g)
        rg[1] += sense
        rg[2] += gate

    q = SSM6N56FE(ref="Q1")
    q["G1"] += cfg2_g
    q["G2"] += cfg3_g
    q["D1"] += exp_oe
    q["D2"] += exp_oe
    q["S1"] += gnd
    q["S2"] += gnd

    r_oe = R_0603("10k", lcsc="C25804", mpn="0603WAF1002T5E", ref="R26")
    r_oe[1] += v3v3
    r_oe[2] += exp_oe
    c_oe = C_0603("1uF 50V", lcsc="C15849", mpn="CL10A105KB8NNNC", ref="C13")
    c_oe[1] += exp_oe
    c_oe[2] += gnd
