"""3.3 V input filtering (SPEC 6.2: no regulator in v1).

M.2 3.3 V rail -> ferrite bead -> card +3V3 rail with bulk capacitance.
Values per Espressif HDG (esp32-s3_hardware_design_guidelines_en.pdf
§1.3.2/§PCB-layout) and SPEC 6.2 (>= 2 x 22 uF bulk).

Bead choice (GATE 2 reviewable): GZ2012D101TF 100 R @ 100 MHz, 800 mA,
150 mR DCR, JLC Basic C1015. The 600 R sibling (C1017) is only rated
500 mA - too close to the ESP32-S3 TX burst. Alternative: 0 R link.
"""

from skidl import Part, TEMPLATE

from blocks.common import C_0603, C_0805_22U, subcircuit


@subcircuit
def power_3v3(v3v3_m2, v3v3, gnd):
    """Ferrite-bead entry filter + bulk capacitance on the card rail."""
    fb = Part(
        "Device", "FerriteBead", ref="FB1", value="100R@100MHz 800mA", tag="FB1",
        footprint="Inductor_SMD:L_0805_2012Metric",
    )
    fb.fields.update(LCSC="C1015", JLC="Basic", MPN="GZ2012D101TF")
    fb[1] += v3v3_m2
    fb[2] += v3v3

    # Bulk on the card rail: 2 x 22 uF + 10 uF (HDG: extra 10 uF at power
    # entrance; TX-burst support).
    for _ in range(2):
        c = C_0805_22U()
        c[1] += v3v3
        c[2] += gnd
    c10 = C_0603("10uF 25V", lcsc="C19702", mpn="CL10A106KP8NNNC")
    c10[1] += v3v3
    c10[2] += gnd
