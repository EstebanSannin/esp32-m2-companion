"""3.3 V input: eFuse overvoltage protection + filtering (SPEC 6.2, A3 G11).

v2.0 Rev A (ADR 0007, docs/v2-gate-v1.md §1.4):
  M.2 3.3 V/VBAT (+3V3_M2) -> U6 TPS259470A eFuse -> +3V3_EFUSE
  -> FB1 ferrite -> card +3V3 rail (bulk capacitance).

U6 (docs/datasheets/tps25947.pdf):
- OVLO divider IN -> 100k / 52.3k (0.1 %) -> GND: trip 3.44-3.57 V
  (VOV(R) 1.183/1.20/1.223 V x 2.912), re-enable < ~3.17 V
  (VOV(F) 1.09 V). Owner choice at GATE V1: never exceed the ESP32-S3
  3.6 V abs max. OVLO pin abs max 6.5 V => IN survives up to ~18.9 V
  (not the IC's 28 V: the divider tap is the limit).
- EN/UVLO: 1M pull-up to IN (Table 6.3 note 2: >= 350k when IN may
  exceed 5 V); EN/UVLO threshold 1.2 V, so the device enables as soon as
  its own VIN UVP releases.
- ILM 3.3k -> current limit 0.85 / 1.007 / 1.15 A (RILM range 549-6650 R).
- DVDT: C15 2.2 nF 50 V (RC1 review power-3/K1). Open DVDT = fastest slew
  (~12-15 V/ms) = 0.5-1 A inrush into the ~65 uF card rail, at the current
  limit and above a 200 mA M.2 host soft-start (M.2 Table 39). 2.2 nF:
  SR ~0.7 V/ms typ, <= 1.3 V/ms at max IdVdt (3.82 uA) -> inrush <= ~90 mA;
  slowest ~0.25 V/ms (~13 ms ramp). Rated >= VIN + 5 V (datasheet Rec. Op.).
  NB: restart after an OVLO trip bypasses dVdt (current-limited start).
- OVLO: C16 1 nF 50 V filter at the divider tap (RC1 review power-1): the
  34 kOhm node had no filter and tOVLO is 1.2 us with no deglitch, so hot-plug
  ringing could trip it. tau 34 us; trip delay on a hard 3.3 -> 5 V step
  ~4 us (rail rises ~0.1 V behind the current limit, stays < 3.6 V).
  OVLO RELEASE is 3.13-3.25 V at IN (VOV(F) x 2.912): on a nominal 3.3 V host
  a trip keeps the card OFF until the slot is power-cycled (documented, not
  auto-recovering).
- OUT: C17 1 uF at +3V3_EFUSE next to U6 (TI 8.3.1/8.4.1 ">= 1 uF close to
  OUT"; FB1 put inductance straight on OUT - RC1 review power-4).
- ITIMER open (fastest OC response); FLT_n and AUXOFF (open-drain outputs)
  unused.
- Second source: NONE approved. TPS259474L is NOT drop-in (latch-off
  circuit breaker; pins 3/4 = PG/PGTH) - RC1 review power-2. Keep spares of
  TPS259470ARPWR instead.
- CIN 100 nF at IN.

FB1: Murata BLM18PG121SN1D (C14709, Basic, 0603, 2 A, <= 50 mR) replaces
rev-B GZ2012D101TF (150 mR) -> ~50 mV more margin on a 3.135 V host.
(A 0 R link would also be acceptable: the WROOM-1 module contains its own
LC filter, module datasheet Fig. 8-1.)
Bulk per Espressif HDG: 2 x 22 uF + 10 uF on +3V3.
"""

from skidl import Part, Pin

from blocks.common import (C_0402, C_0603, C_0805_22U, R_0402, TPS259470A,
                           subcircuit)


@subcircuit
def power_3v3(v3v3_m2, v3v3_efuse, v3v3, gnd, ovlo, en_uvlo, ilm, dvdt):
    u = TPS259470A(ref="U6")
    u["IN"] += v3v3_m2
    u["OUT"] += v3v3_efuse
    u["GND"] += gnd
    u["OVLO"] += ovlo
    u["EN_UVLO"] += en_uvlo
    u["ILM"] += ilm
    u["DVDT"] += dvdt
    for name in ("ITIMER", "FLT_n", "AUXOFF"):
        u[name].func = Pin.types.NOCONNECT
        u[name].do_erc = False

    # 0.1 % 25 ppm matched pair (YAGEO RT0402); no Basic 0.1 % parts exist
    r_top = R_0402("100k 0.1%", lcsc="C852472", mpn="RT0402BRD07100KL",
                   jlc="Extended", ref="R31")
    r_top.fields["JLC_note"] = "0.1 % needed for the OVLO window (ADR 0007)"
    r_top[1] += v3v3_m2
    r_top[2] += ovlo
    r_bot = R_0402("52.3k 0.1%", lcsc="C852832", mpn="RT0402BRD0752K3L",
                   jlc="Extended", ref="R32")
    r_bot.fields["JLC_note"] = "0.1 % needed for the OVLO window (ADR 0007)"
    r_bot[1] += ovlo
    r_bot[2] += gnd
    # >= 350k per Table 6.3 note 2; 1M reuses the Basic line already in the
    # BOM (no Basic 470k exists). EN leakage 0.1 uA x 1M = 0.1 V << 1.2 V.
    r_en = R_0402("1M", lcsc="C26083", mpn="0402WGF1004TCE", ref="R33")
    r_en[1] += v3v3_m2
    r_en[2] += en_uvlo
    r_ilm = R_0402("3.3k", lcsc="C25890", mpn="0402WGF3301TCE", ref="R34")
    r_ilm[1] += ilm
    r_ilm[2] += gnd
    c_in = C_0603("100nF 50V", lcsc="C14663", mpn="CC0603KRX7R9BB104",
                  ref="C14")
    c_in[1] += v3v3_m2
    c_in[2] += gnd
    # RC1 review: inrush slew, OVLO filter, OUT decoupling (see docstring)
    c_dvdt = C_0402("2.2nF 50V", lcsc="C1531", mpn="0402B222K500NT", ref="C15")
    c_dvdt[1] += dvdt
    c_dvdt[2] += gnd
    c_ovlo = C_0402("1nF 50V", lcsc="C1523", mpn="0402B102K500NT", ref="C16")
    c_ovlo[1] += ovlo
    c_ovlo[2] += gnd
    c_out = C_0402("1uF 25V", lcsc="C52923", mpn="CL05A105KA5NNNC", ref="C17")
    c_out[1] += v3v3_efuse
    c_out[2] += gnd

    # Murata BLM18PG121SN1D: 120 R @ 100 MHz, 2 A, DCR <= 50 mR, JLC Basic
    # (v2/research/v2_parts_check.md). Rev-B GZ2012D101TF had 150 mR.
    fb = Part(
        "Device", "FerriteBead", ref="FB1", value="120R@100MHz 2A",
        tag="FB1", footprint="Inductor_SMD:L_0603_1608Metric",
    )
    fb.fields.update(LCSC="C14709", JLC="Basic", MPN="BLM18PG121SN1D")
    fb[1] += v3v3_efuse
    fb[2] += v3v3

    for ref in ("C1", "C2"):
        c = C_0805_22U(ref=ref)
        c[1] += v3v3
        c[2] += gnd
    c10 = C_0603("10uF 10V", lcsc="C19702", mpn="CL10A106KP8NNNC", ref="C3")
    c10[1] += v3v3
    c10[2] += gnd
