"""Shared part factories with LCSC/JLC BOM fields (SPEC rule 5).

All LCSC numbers verified against the JLCPCB parts library (jlcsearch
mirror) on 2026-08-28; re-verify at order time (Phase 3 checklist).
"""

from skidl import Part, subcircuit  # re-exported for blocks

__all__ = [
    "subcircuit", "R_0603", "C_0603", "C_0805_22U", "LED_0603", "LED_0805",
    "BAT54A", "TESTPOINT",
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


def R_0603(value, lcsc, mpn, dnp=False):
    p = Part("Device", "R", value=value, tag=_next_tag("R"),
             footprint="Resistor_SMD:R_0603_1608Metric")
    return _bom(p, lcsc, "Basic", mpn, dnp)


def C_0603(value, lcsc, mpn):
    p = Part("Device", "C", value=value, tag=_next_tag("C"),
             footprint="Capacitor_SMD:C_0603_1608Metric")
    return _bom(p, lcsc, "Basic", mpn)


def C_0805_22U():
    p = Part("Device", "C", value="22uF 25V", tag=_next_tag("C"),
             footprint="Capacitor_SMD:C_0805_2012Metric")
    return _bom(p, "C45783", "Basic", "CL21A226MAQNNNE")


def LED_0603(color, lcsc, mpn):
    p = Part("Device", "LED", value=color, tag=_next_tag("LED"),
             footprint="LED_SMD:LED_0603_1608Metric")
    return _bom(p, lcsc, "Basic", mpn)


def LED_0805(color, lcsc, mpn):
    p = Part("Device", "LED", value=color, tag=_next_tag("LED"),
             footprint="LED_SMD:LED_0805_2012Metric")
    return _bom(p, lcsc, "Basic", mpn)


def BAT54A():
    """Dual Schottky, common anode: pin 3 = A, pins 1/2 = K.

    Pinout: docs/datasheets/lbat54a_schottky.pdf p.1 internal-schematic
    figure (note: that doc's *title* wrongly says 'Dual Series'; the drawing
    and the standard BAT54A config are common anode).
    """
    p = Part("Diode", "BAT54A", tag=_next_tag("D"),
             footprint="Package_TO_SOT_SMD:SOT-23")
    return _bom(p, "C12743", "Extended", "LBAT54ALT1G")


def TESTPOINT(name):
    p = Part("Connector", "TestPoint", value=name, tag=_next_tag("TP"),
             footprint="TestPoint:TestPoint_Pad_D1.5mm")
    p.fields.update(LCSC="", JLC="PCB", MPN="")
    return p
