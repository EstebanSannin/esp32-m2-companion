"""Shared part factories with LCSC/JLC BOM fields (SPEC rule 5).

All LCSC numbers verified against the JLCPCB parts library (jlcsearch
mirror) on 2026-08-28; re-verify at order time (Phase 3 checklist).
"""

from skidl import Part, subcircuit  # re-exported for blocks

__all__ = [
    "subcircuit", "R_0603", "C_0603", "C_0805_22U", "LED_0603", "LED_0805",
    "BAT54A", "TESTPOINT",
    # v2.0 Rev A (GATE V2)
    "R_0402", "C_0402", "R_ARRAY_4X0402", "SSM6N56FE", "TMUX1511",
    "TPS259470A",
]


_tag_counter = 0


def _next_tag(prefix):
    """Deterministic part tags (stable netlist->PCB sync across builds)."""
    global _tag_counter
    _tag_counter += 1
    return f"{prefix}_{_tag_counter:03d}"


def _bom(part, lcsc, jlc, mpn, dnp=False):
    part.fields.update(LCSC=lcsc, JLC=jlc, MPN=mpn)
    if dnp:
        part.fields["DNP"] = "DNP"
        part.do_not_populate = True
    return part


def R_0603(value, lcsc, mpn, dnp=False, ref=None):
    p = Part("Device", "R", value=value, ref=ref, tag=_next_tag("R"),
             footprint="Resistor_SMD:R_0603_1608Metric")
    return _bom(p, lcsc, "Basic", mpn, dnp)


def C_0603(value, lcsc, mpn, ref=None):
    p = Part("Device", "C", value=value, ref=ref, tag=_next_tag("C"),
             footprint="Capacitor_SMD:C_0603_1608Metric")
    return _bom(p, lcsc, "Basic", mpn)


def C_0805_22U(ref=None):
    p = Part("Device", "C", value="22uF 25V", ref=ref, tag=_next_tag("C"),
             footprint="Capacitor_SMD:C_0805_2012Metric")
    return _bom(p, "C45783", "Basic", "CL21A226MAQNNNE")


def LED_0603(color, lcsc, mpn, ref=None):
    p = Part("Device", "LED", value=color, ref=ref, tag=_next_tag("LED"),
             footprint="LED_SMD:LED_0603_1608Metric")
    return _bom(p, lcsc, "Basic", mpn)


def LED_0805(color, lcsc, mpn, ref=None):
    p = Part("Device", "LED", value=color, ref=ref, tag=_next_tag("LED"),
             footprint="LED_SMD:LED_0805_2012Metric")
    return _bom(p, lcsc, "Basic", mpn)


def BAT54A(ref=None):
    """Dual Schottky, common anode: pin 3 = A, pins 1/2 = K.

    Pinout: docs/datasheets/lbat54a_schottky.pdf p.1 internal-schematic
    figure (note: that doc's *title* wrongly says 'Dual Series'; the drawing
    and the standard BAT54A config are common anode).
    """
    p = Part("Diode", "BAT54A", ref=ref, tag=_next_tag("D"),
             footprint="Package_TO_SOT_SMD:SOT-23")
    return _bom(p, "C12743", "Extended", "LBAT54ALT1G")


def TESTPOINT(name, ref=None):
    # v2: 1.0 mm pads (was 1.5 mm) - frees the module<->finger band (GATE V3)
    p = Part("Connector", "TestPoint", value=name, ref=ref, tag=_next_tag("TP"),
             footprint="TestPoint:TestPoint_Pad_D1.0mm")
    p.fields.update(LCSC="", JLC="PCB", MPN="")
    return p


# ---------------------------------------------------------------------------
# v2.0 Rev A parts (GATE V2). LCSC numbers: docs/v2-gate-v1.md §3 (JLC
# parts API 2026-10-07); pinouts from the datasheets in docs/datasheets/.
# Parts absent from the KiCad 9 stock symbol library are defined here with
# explicit pin numbers so the netlist traces 1:1 to the datasheet tables.
# ---------------------------------------------------------------------------

from skidl import Pin, SKIDL, TEMPLATE  # noqa: E402

_P = Pin.types


def R_0402(value, lcsc, mpn, jlc="Basic", ref=None, dnp=False):
    p = Part("Device", "R", value=value, ref=ref, tag=_next_tag("R"),
             footprint="Resistor_SMD:R_0402_1005Metric")
    return _bom(p, lcsc, jlc, mpn, dnp)


def C_0402(value, lcsc, mpn, ref=None):
    p = Part("Device", "C", value=value, ref=ref, tag=_next_tag("C"),
             footprint="Capacitor_SMD:C_0402_1005Metric")
    return _bom(p, lcsc, "Basic", mpn)


def _template(name, prefix, footprint, description, pins):
    t = Part(name=name, tool=SKIDL, dest=TEMPLATE, ref_prefix=prefix,
             footprint=footprint, description=description)
    for num, pname, func in pins:
        t += Pin(num=num, name=pname, func=func)
    return t


# 4 x 0402 convex array: element k = pins k (Rka) / 9-k (Rkb), k = 1..4.
# 4D02 (UniOhm) is the convex type; pad order matches KiCad
# R_Array_Convex_4x0402 (v2/research/v2_parts_check.md §5).
_RARRAY_T = _template(
    "R_Array_4x0402", "RN", "Resistor_SMD:R_Array_Convex_4x0402",
    "4 x resistor array, convex 0402",
    [(k, f"R{k}a" if k <= 4 else f"R{9 - k}b", _P.PASSIVE)
     for k in range(1, 9)])


def R_ARRAY_4X0402(value, lcsc, mpn, ref=None):
    p = _RARRAY_T(value=value, ref=ref, tag=_next_tag("RN"))
    return _bom(p, lcsc, "Extended", mpn)


# Toshiba SSM6N56FE, ES6 (SOT-563): docs/datasheets/ssm6n56fe.pdf §3
# "Packaging and Pin Assignment": 1 S1, 2 G1, 3 D2, 4 S2, 5 G2, 6 D1.
_SSM6N56FE_T = _template(
    "SSM6N56FE", "Q", "Package_TO_SOT_SMD:SOT-563",
    "Dual N-MOSFET 20 V, VGS(th) 0.4-1.0 V (Toshiba SSM6N56FE)",
    [(1, "S1", _P.PASSIVE), (2, "G1", _P.INPUT), (3, "D2", _P.PASSIVE),
     (4, "S2", _P.PASSIVE), (5, "G2", _P.INPUT), (6, "D1", _P.PASSIVE)])


def SSM6N56FE(ref=None):
    p = _SSM6N56FE_T(ref=ref, tag=_next_tag("Q"))
    p.fields["JLC_note"] = ("no Basic dual NMOS with VGS(th) <= 1.0 V "
                            "(ADR 0006)")
    # owner-approved 2nd source (GATE V4, 2026-10-10): same SOT-563 pinout
    # 1 S1 2 G1 3 D2 4 S2 5 G2 6 D1, Vth 0.45-0.9 V, IGSS 1 uA; VGS max +-6 V
    # (our gates <= 3.6 V). SSM6N56FE stock was 124 on 2026-10-10.
    p.fields["LCSC_2nd_source"] = "C86784 (Vishay SI1024X-T1-GE3)"
    return _bom(p, "C146449", "Extended", "SSM6N56FE,LM")


# TI TMUX1511, RSV UQFN-16: docs/datasheets/tmux1511.pdf Table 4-1
# (UQFN column): 1 SEL1, 2 S1, 3 D1, 4 SEL2, 5 S2, 6 D2, 7 NC, 8 GND,
# 9 D3, 10 S3, 11 SEL3, 12 NC, 13 D4, 14 S4, 15 SEL4, 16 VDD.
# Footprint: TI RSV0016A land pattern (tools/gen_fp_rsv.py; GATE V3) - the
# KiCad stock UQFN pads are 0.15 mm longer and starved the pin escapes.
_TMUX1511_T = _template(
    "TMUX1511_RSV", "U", "esp32_m2_companion:TI_RSV0016A_UQFN-16_1.8x2.6mm_P0.4mm",
    "4-ch 1:1 switch, powered-off protection, SEL pull-down (TI TMUX1511)",
    [(1, "SEL1", _P.INPUT), (2, "S1", _P.PASSIVE), (3, "D1", _P.PASSIVE),
     (4, "SEL2", _P.INPUT), (5, "S2", _P.PASSIVE), (6, "D2", _P.PASSIVE),
     (7, "NC7", _P.NOCONNECT), (8, "GND", _P.PWRIN), (9, "D3", _P.PASSIVE),
     (10, "S3", _P.PASSIVE), (11, "SEL3", _P.INPUT),
     (12, "NC12", _P.NOCONNECT), (13, "D4", _P.PASSIVE),
     (14, "S4", _P.PASSIVE), (15, "SEL4", _P.INPUT), (16, "VDD", _P.PWRIN)])


def TMUX1511(ref=None):
    p = _TMUX1511_T(ref=ref, tag=_next_tag("U"))
    p.fields["JLC_note"] = ("no Basic analog switch with powered-off "
                            "protection + fail-safe SEL (ADR 0006)")
    return _bom(p, "C2673275", "Extended", "TMUX1511RSVR")


# TI TPS259470A, RPW VQFN-10: docs/datasheets/tps25947.pdf Table 5-1:
# 1 EN/UVLO, 2 OVLO, 3 AUXOFF (470x), 4 FLT (470x), 5 IN, 6 OUT, 7 DVDT,
# 8 GND, 9 ILM, 10 ITIMER. No KiCad stock footprint for RPW: project
# footprint drawn from TI's land pattern at GATE V3.
_TPS259470A_T = _template(
    "TPS259470A_RPW", "U", "esp32_m2_companion:TI_RPW_VQFN-10_2x2mm_P0.5mm",
    "eFuse 2.7-23 V, adjustable OVLO, auto-retry (TI TPS259470A)",
    [(1, "EN_UVLO", _P.INPUT), (2, "OVLO", _P.INPUT),
     (3, "AUXOFF", _P.OPENCOLL), (4, "FLT_n", _P.OPENCOLL),
     (5, "IN", _P.PWRIN), (6, "OUT", _P.PWROUT), (7, "DVDT", _P.PASSIVE),
     (8, "GND", _P.PWRIN), (9, "ILM", _P.PASSIVE),
     (10, "ITIMER", _P.PASSIVE)])


def TPS259470A(ref=None):
    p = _TPS259470A_T(ref=ref, tag=_next_tag("U"))
    p.fields["JLC_note"] = ("no Basic eFuse with adjustable OVLO "
                            "(ADR 0007); no drop-in 2nd source (TPS259474L is "
                            "latch-off, pins 3/4 PG/PGTH - RC1 review)")
    return _bom(p, "C3662799", "Extended", "TPS259470ARPWR")
