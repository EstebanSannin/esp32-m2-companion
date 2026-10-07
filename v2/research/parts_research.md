# v2 expansion-bus parts research (ESP32-S3 M.2 companion)

Date: 2026-10-06. Stock / Basic-Extended status pulled live from the JLCPCB parts API
(`selectSmtComponentList`) on this date; stock moves daily, so recheck before ordering.
Datasheet facts come from the manufacturer PDFs, downloaded and converted with
`pdftotext`. Page numbers are PDF pages (the page that holds the table). The raw
text copies are in `scratchpad/ds/*.txt`.

**Library finding that affects every category:** a Basic-only API query
(`componentLibraryType: base`) returns **no** 74LVC1G, LV1T, bus-switch or analog-switch
part. The only Basic resistor arrays are 0603x4 (4D03WGJ0102T5E C20197 1 kΩ,
4D03WGJ0472T5E C1980 4.7 kΩ, 4D03WGJ0103T5E C29718 10 kΩ). There is **no 4x0402 array
in Basic**. 4D02WGJ0221TCE C25498 is listed as Extended, both in the API and on its
jlcpcb.com partdetail page.

---

## 1. 12-channel bidirectional bus/analog switch

| Part | Mfr | LCSC # | Lib | Stock | Package | Verified specs (datasheet page) | Datasheet |
|---|---|---|---|---|---|---|---|
| **TMUX1511PWR** | TI | C2866750 | Ext | 9 633 | TSSOP-14 | 4x SPST, 1 SELx per channel, **active-high (low = OFF)**, **internal 6 MΩ pull-down on each SELx** (p4 pin table). VDD 1.5–5.5 V; "supports input voltage beyond supply", VS 0…VDD×2 (≤5.5 V). RON 2 Ω typ / **4.5 Ω max** at VS 0…VDD×2, ISD 8 mA (p6). **IPOFF: VDD = 0 V, VS = 0–3.6 V, VD = 0 V: ±2 µA max over −40…125 °C; ±10 nA max at 25 °C (VS 0–3 V)** (p6). COFF 2.5 typ / **4 pF max** (p7). BW 3 GHz (p7). VIH 1.2 V min (1.8 V logic) (p6). | https://www.ti.com/lit/ds/symlink/tmux1511.pdf |
| TMUX1511RSVR | TI | C2673275 | Ext | 4 161 | UQFN-16 1.8×2.6 | same die | same |
| TMUX1511RWBR | TI | C47068278 | Ext | **0** | X2QFN-12 1.6×1.6 | same die | same |
| TMUX1574PWR / RSVR | TI | C2673443 / C2673120 | Ext | 7 628 / 3 998 | TSSOP-16 / UQFN-16 | 4-ch **2:1 mux** (SPDT); use one throw as SPST. RON 2 Ω typ / 4.5 Ω max; **IPOFF ±2 µA max, VDD = 0, VS 0–3.6 V** (p6); COFF 3.5 typ / 6 pF max; BW 2 GHz (p7). **EN is active-low with an internal 6 MΩ pull-down, so it defaults ON** (p4); needs an external pull-up to be fail-safe, and with VDD = 0 the pull-up has no rail. | https://www.ti.com/lit/ds/symlink/tmux1574.pdf |
| SN74CB3Q3245PWR | TI | C470961 | Ext | 2 974 | TSSOP-20 (also RGYR VQFN-20 C201559, 71 pcs) | 8-bit, single **/OE (active-low)**. Charge-pumped gate: "0 to 5 V switching with 3.3 V VCC" (p1). ron at VCC = 3 V: 4 typ / 6 max (VI = 0), 4 typ / **8 Ω max** (VI = 2.4 V) (p4). **Ioff: VCC = 0, VO = 0–5.5 V, VI = 0: 1 µA max** (p4). Cio(OFF) 3.5 typ / 5 pF max (p4). BW up to 500 MHz (p1). Datasheet: "OE must be tied to VCC through a pullup resistor" to guarantee Hi-Z during power-up/down (p1). VCC 2.3–3.6 V, TA −40…85 °C. | https://www.ti.com/lit/ds/symlink/sn74cb3q3245.pdf |
| SN74CB3Q3125PWR | TI | C2653302 | Ext | **49** | TSSOP-14 | 4-bit, 4 separate /OE. ron at 3 V: 4/6 Ω (VI = 0), 4/8 Ω (VI = 2.4 V) (p5). **Ioff 1 µA max, VCC = 0, VO 0–5.5 V** (p5). Cio(OFF) 4/5 pF (p5). 500 MHz. OE pull-up note (p8). | https://www.ti.com/lit/ds/symlink/sn74cb3q3125.pdf |
| SN74CB3Q16244DGGR | TI | C2674767 | Ext | **23** | TSSOP-48 | 16-bit, 4 /OE. ron at 3 V: 6/8 Ω (VI = 0), 5/9 Ω (VI = 2.4 V); **Ioff 1 µA max**; Cio(OFF) 4/6 pF (p6). Large and low stock. | https://www.ti.com/lit/ds/symlink/sn74cb3q16244.pdf |
| SN74CB3Q3384APWR | TI | C469874 | Ext | 4 895 | TSSOP-24 | 2× 5-bit, 2 /OE (10 ch). ron at 3 V: 3/6 Ω (VI = 0), 3.5/8 Ω (VI = 2.4 V); **Ioff 1 µA max**; Cio(OFF) 3.5/5 pF (p7). Needs another part for the last 2 channels. | https://www.ti.com/lit/ds/symlink/sn74cb3q3384a.pdf |
| SN74CB3T3245PWR | TI | C15298 | Ext | 4 222 | TSSOP-20 | 8-bit, /OE. **Output voltage tracks VCC (level-translating clamp)** (p1, p8, Fig 7-1). ron 5 typ / 7 Ω max (VI = 0, VCC = 3 V); **Ioff 10 µA max** (VCC = 0, VO 0–5.5 V); Cio(OFF) 5 pF typ; **II up to −40 µA at VI 0.7…VCC−0.7 with the switch ON** (p5). Works, but its input loading and Ioff are 10x worse than CB3Q. Not preferred. | https://www.ti.com/lit/ds/symlink/sn74cb3t3245.pdf |
| 74CBTLV3245PW / SN74CBTLV3245APWR | Nexperia / TI | C458790 / C7156 | Ext | 4 692 / 1 175 | TSSOP-20 | NMOS-only, no charge pump. **Rejected** per the brief (clips near VCC−Vth). | — |
| TS3A27518E (PWR/RTWR) | TI | C443721 / C2651937 | Ext | 4 693 / 10 727 | TSSOP-24 / WQFN-24 | 6-ch 1:2 mux with EN. Datasheet has **no Ioff / powered-off spec**. Cx(OFF) 8.5–9 pF. **Rejected.** | https://www.ti.com/lit/ds/symlink/ts3a27518e.pdf |
| TMUX154E | TI | C2870320 | Ext | 2 500 | MSOP-10 | Only 2 ch; Ron 10 Ω max; VCC 3–4.3 V. IOFF ±2 µA (p5). Too few channels. Not useful. | https://www.ti.com/lit/ds/symlink/tmux154e.pdf |
| PI3C3125 / PI3C3245 / PI5C3245 | Diodes | C2674884 / C2674508 / … | Ext | **0** (all variants ≈0) | TSSOP | Not stocked. PI5C is a 5 V part. Datasheets not fetched (**unverified**). | — |
| QS3VH245 / QS3VH16244 | Renesas | C7329915 / … | Ext | 20 / 0 | QSOP-20 / TSSOP-48 | Effectively not stocked. **Unverified.** | — |
| CH440 (WCH), TPCH440 (TECH PUBLIC) | WCH / TECH PUBLIC | C282323 / C54195052 | Ext | 2 134 / 2 775 | TSSOP-16 | CH440 is VCC 4–5.5 V per LCSC (wrong supply). TPCH440 lists 1.5–5.5 V but powered-off behaviour is **unverified**. Rejected. | — |
| Runic RS2117, SGM6505 | Runic / SGMICRO | C5372464 / C700311 | Ext | 3 757 / 1 732 | QFN-10 / TQFN-24 | 2:1 analog mux; Ioff **unverified**; SGM6505 is 15 pF. Not pursued. | — |

No Chinese pin-for-pin substitute for TMUX1511 or CB3Q3245 turned up in the JLC catalogue. Searches tried: 1511, 1574, CB3Q, power-off SPST and others.

**Recommendation: 3× TMUX1511PWR (C2866750), or TMUX1511RSVR (C2673275) if the 1.8×2.6 mm UQFN fits.**
Why: it is the only candidate that is all of these at once:
- the I/Os are guaranteed high-Z unpowered (±2 µA, VDD = 0, I/O up to 3.6 V) over −40…125 °C;
- Ron ≤ 4.5 Ω and COFF ≤ 4 pF, both max values;
- it is **intrinsically fail-safe off**: SELx is active-high with an internal 6 MΩ pull-down, so an unpowered or tri-stated driver gives OFF;
- it passes rail-to-rail and beyond VDD;
- it is in good stock.

Tie all 12 SELx pins to one `EXP_OE` net. Add an external ~100 kΩ pull-down for a defined OFF state; the internal 6 MΩ pull-downs in parallel come to 0.5 MΩ. Drive the net with the NOR gate from §4.

Fallback: 2× SN74CB3Q3245PWR (C470961, 2 974 stock), with /OE pulled up to 3V3 and driven by the OR gate. Ioff is 1 µA max but only at 85 °C, and the part draws ICC 1 mA typ for the charge pump. Stock for 2 per board is fine for prototypes, not for volume.

---

## 2. Single open-drain buffer, Ioff, 5.5 V tolerant (74LVC1G07)

| Part | Mfr | LCSC # | Lib | Stock | Package | Verified specs | Datasheet |
|---|---|---|---|---|---|---|---|
| **SN74LVC1G07DBVR** | TI | C7829 | Ext | 71 948 | SOT-23-5 | VCC 1.65–5.5 V; VI 0–5.5 V and **VO 0–5.5 V (open-drain)** (p5). VIH 2.0 V at VCC 3–3.6 V (p5). **Ioff ±10 µA max, VCC = 0, VI or VO = 5.5 V** (p6). IOL 32 mA. | https://www.ti.com/lit/ds/symlink/sn74lvc1g07.pdf |
| SN74LVC1G07DCKR | TI | C7830 | Ext | 45 827 | SC-70-5 | same die | same |
| 74LVC1G07GW,125 | Nexperia | C282345 | Ext | 35 042 | TSSOP-5 (SC-88A) | Datasheet downloaded but not parsed (**Ioff value unverified**; LCSC lists 4 µA ICC). | https://assets.nexperia.com/documents/data-sheet/74LVC1G07.pdf |
| 74LVC1G07GV,125 | Nexperia | C12511 | Ext | 2 634 | SOT-753 | as above | as above |

No Basic option exists. **Recommendation: SN74LVC1G07DBVR (C7829).** All its specs are verified and stock is deep. Use the DCKR (C7830) if SC-70 is wanted.

---

## 3. Single-supply low-threshold input buffer (1.8 V in at VCC = 3.3 V), Ioff

| Part | Mfr | LCSC # | Lib | Stock | Package | Verified specs | Datasheet |
|---|---|---|---|---|---|---|---|
| **SN74LV1T34DCKR** | TI | C78541 | Ext | 93 674 | SC-70-5 | **VIH 1.37 V (25 °C) / 1.39 V (−40…125 °C) at VCC 3–3.3 V; 1.48 V at 3.6 V** (p6). VIL 0.8/0.65 V. VI 0–5.5 V (p5); abs max VI −0.5…7.0 V, which is independent of VCC (p5). **No Ioff parameter anywhere in the datasheet**: powered-off behaviour is **unverified**. | https://www.ti.com/lit/ds/symlink/sn74lv1t34.pdf |
| SN74LV1T34DBVR | TI | C100024 | Ext | 24 625 | SOT-23-5 | same | same |
| SN74LV1T125DBVR | TI | C473338 | Ext | 206 947 | SOT-23-5 | Same VIH table (p6). **No Ioff spec.** | https://www.ti.com/lit/ds/symlink/sn74lv1t125.pdf |
| 74LV1T34GW (H) | Nexperia | C5199768 | Ext | 294 | TSSOP-5 | VIH 1.35 V (25 °C) / 1.37 V (−40…125 °C) at VCC 3.0–3.3 V (p4). Abs max: VI −0.5…+7 V, and **"output in power-off state" −0.5…4.6 V** (p3), which implies power-off tolerance. **No IOFF current spec.** | https://assets.nexperia.com/documents/data-sheet/74LV1T34.pdf |
| **SN74LV4T125PWR** (quad, documented Ioff) | TI | C90755 | Ext | 6 636 | TSSOP-14 (RGYR VQFN-14 C411879, 2 019) | **Ioff 5 µA max (0.5 typ), VCC = 0, VO or VI 0–5.5 V** (p6). **VIH 1.3 V (25 °C) / 1.35 V (−40…125 °C) at VCC 3–3.6 V.** | https://www.ti.com/lit/ds/symlink/sn74lv4t125.pdf |
| SN74AUP1T34 / Nexperia 74AUP1T34 | TI / Nexperia | — | — | — | SC-70 / TSSOP5 | **Dual-supply** (VCCA/VCCB). The IOFF spec is there (Nexperia ±0.2 µA, p5), but the part needs a 1.8 V input-side rail. Rejected because it is not single-supply. | ti.com sn74aup1t34.pdf / nexperia 74AUP1T34.pdf |
| TP74LV1T34S5, 74LV1T34GV-TP, T74LV1T34 (3PEAK) | TECH PUBLIC / 3PEAK | C47117591 / C52098009 / C53477533 | Ext | 4 592 / 1 224 / 459 | SOT-23-5 | LCSC text claims "Power-off protection". Datasheets not checked: **unverified.** | — |

**Recommendation:**
- If a **datasheet-guaranteed Ioff** is a hard requirement: SN74LV4T125PWR (C90755). It is the only single-supply low-VIH buffer found with a specified Ioff, and its 4 buffers can cover several sideband inputs.
- If a single gate is mandatory: SN74LV1T34DCKR (C78541). Flag its powered-off behaviour as an open item. Its inputs are rated to 7 V regardless of VCC, but TI does not specify Ioff for the LV1T family. Close the item with a bench check (VCC = 0, 3.3 V on A, measure leakage) or a TI E2E answer.

---

## 4. 2-input gate for EXP_OE (Ioff)

EXP_OE must assert only when CONFIG_a and CONFIG_b are both low.
- Switch OE active-high (TMUX1511 SELx): use **NOR**, Y = NOT(a OR b).
- Switch /OE active-low (CB3Q): use **OR**, /OE = a OR b.

| Part | Mfr | LCSC # | Lib | Stock | Package | Verified specs | Datasheet |
|---|---|---|---|---|---|---|---|
| **SN74LVC1G02DCKR** (NOR) | TI | C113520 | Ext | 40 246 | SC-70-5 | Inputs accept up to 5.5 V; **Ioff ±10 µA max, VCC = 0, VI or VO = 5.5 V** (p5). VIH 2.0 V at VCC 3–3.6 V (p4). | https://www.ti.com/lit/ds/symlink/sn74lvc1g02.pdf |
| SN74LVC1G02DBVR (NOR) | TI | C16360 | Ext | **2** | SOT-23-5 | same | same |
| 74LVC1G02GW,125 (NOR) | Nexperia | C353856 | Ext | 11 729 | TSSOP-5 | Datasheet downloaded, Ioff value not parsed (**unverified**) | https://assets.nexperia.com/documents/data-sheet/74LVC1G02.pdf |
| **SN74LVC1G32DBVR** (OR) | TI | C10096 | Ext | 112 328 | SOT-23-5 | **Ioff ±10 µA (−40…85 °C) / ±25 µA (−40…125 °C), VCC = 0, VI or VO = 5.5 V** (p7). Inputs up to 5.5 V. VIH 2.0 V at 3–3.6 V (p6). | https://www.ti.com/lit/ds/symlink/sn74lvc1g32.pdf |
| SN74LVC1G32DCKR (OR) | TI | C7840 | Ext | 36 802 | SC-70-5 | same | same |
| 74LVC1G32GV,125 (OR) | Nexperia | C12517 | Ext | 27 597 | SOT-753 | Ioff **unverified** | https://assets.nexperia.com/documents/data-sheet/74LVC1G32.pdf |

**Recommendation:** with the TMUX1511 choice, use **SN74LVC1G02DCKR (C113520)**. If CB3Q is used instead, use **SN74LVC1G32DBVR (C10096)**.

The NOR suits fail-safe behaviour:
- If the card's 3V3 is off, the NOR has no supply; its Ioff output goes high-Z, so the SELx pull-downs keep every switch OFF.
- An edge pin left floating is pulled high by its 1 MΩ pull-up, which gives OFF.

The 1 MΩ pull-ups to the edge feed powered-off gate inputs. Ioff ≤ 10 µA is a max limit; the real input leakage is far lower.

---

## 5. 4x0402 resistor arrays, 100–330 Ω

| Part | Mfr | LCSC # | Lib | Stock | Value | Datasheet |
|---|---|---|---|---|---|---|
| 4D02WGJ0101TCE | UNI-ROYAL | C48442 | **Ext** | 304 153 | 100 Ω ±5 %, 62.5 mW/element, convex 0402x4 | LCSC |
| 4D02WGJ0151TCE | UNI-ROYAL | C474169 | Ext | 9 807 | 150 Ω | LCSC |
| 4D02WGJ0221TCE | UNI-ROYAL | C25498 | **Ext** (confirmed on its jlcpcb.com partdetail page) | 77 694 | 220 Ω | https://www.lcsc.com/datasheet/lcsc_datasheet_2304140030_UNI-ROYAL-Uniroyal-Elec-4D02WGJ0221TCE_C25498.pdf |
| 4D02WGJ0331TCE | UNI-ROYAL | C43557 | Ext | 29 123 | 330 Ω | LCSC |
| YC124-JR-07100RL | YAGEO | C326873 | Ext | 53 261 | 100 Ω (concave) | — |
| *(Basic discrete alternative)* 0402WGF1000TCE | UNI-ROYAL | C25076 | **Basic** | 4 032 314 | 100 Ω 1 % 0402 | — |
| *(Basic discrete)* 0402WGF2200TCE | UNI-ROYAL | C25091 | **Basic** | 1 392 818 | 220 Ω | — |
| *(Basic discrete)* 0402WGF3300TCE | UNI-ROYAL | C25104 | **Basic** | 1 181 738 | 330 Ω | — |

**There is no 4x0402 array in JLC Basic.** The only Basic arrays are 0603x4 (1 k / 4.7 k / 10 k).
**Recommendation:** use 4D02WGJ0101TCE (C48442, 100 Ω) or 4D02WGJ0221TCE (C25498, 220 Ω) as one Extended line. That line costs one Extended-part loading fee and saves 12 placements. The alternative is 12 discrete Basic 0402s (C25076 / C25091 / C25104), which need no extra fee but take more area.

---

## Unverified list

1. SN74LV1T34 / SN74LV1T125 (TI) and 74LV1T34/125 (Nexperia): **powered-off input/output leakage is not specified**. There is no Ioff row. Nexperia gives only an abs-max "output in power-off state −0.5…4.6 V".
2. TECH PUBLIC / 3PEAK / Changjing LV1T clones: the "Power-off protection" claims come from LCSC text only.
3. Nexperia 74LVC1G07/02/32 Ioff values: PDFs downloaded to `ds/`, numbers not extracted.
4. Diodes PI3C3125 / PI3C3245 / PI5C3245 and Renesas QS3VH245/16244: datasheets not fetched (effectively zero JLC stock).
5. TPCH440, RS2117, SGM6505 powered-off behaviour: not checked.
6. Basic/Extended status and stock: JLC API snapshot on 2026-10-06. The API and partdetail page agree for C25498; the other parts were not cross-checked on partdetail pages.
7. Bandwidth for the CB3Q parts is the "up to 500 MHz" feature-list figure; there is no table entry.
