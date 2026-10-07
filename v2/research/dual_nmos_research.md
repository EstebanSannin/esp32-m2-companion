# Dual N-MOSFET for M.2 wired-NOR detect + open-drain outputs

Date: 2026-10-06. JLC data comes from the JLCPCB parts API
(`selectSmtComponentList`): `componentLibraryType` (base/expand) and `stockCount`, which is
JLC's own stock. Electrical data comes from the manufacturer datasheets, fetched as LCSC
mirrors (`wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/<name>.pdf`) and read with pdftotext.
The local copies are in `scratchpad/ds/`.

Requirements: VGS(th) max ≤ 1.0 V (ideally ≤ 0.9 V), RDS(on) specified at VGS 1.5–1.8 V,
IGSS ≤ 1 µA at ±5–8 V, VDS ≥ 20 V, VGS max ≥ ±8 V, package SOT-363/SC-70-6/SOT-563.
Wanted pinout: 1 S1, 2 G1, 3 D2, 4 S2, 5 G2, 6 D1.

## JLC Basic

**No dual N-MOSFET in SOT-363 or SOT-563 is a JLC Basic part.** None of the API queries
returned `componentLibraryType=base` or `preferredComponentFlag=true`. The queries covered
every candidate MPN plus generic searches ("2 N-Channel SOT-363", "2 N-Channel SOT-563",
2N7002DW, BSS138DW, UM6K1N, FDG6301N and others). Every option is Extended.

## Candidates

| MPN (LCSC) | JLC / stock | Pkg | Pinout | VGS(th) min–max @ ID | RDS(on) max, lowest VGS | IGSS max | VDS / VGSmax | Verdict |
|---|---|---|---|---|---|---|---|---|
| **Toshiba SSM6N56FE,LM (C146449)** | Ext / 7 293 | SOT-563 (ES6) | 1 S1, 2 G1, 3 D2, 4 S2, 5 G2, 6 D1 (exact match) | 0.4–1.0 V @ **1 mA**, VDS = 3 V | 840 mΩ @ 1.5 V/50 mA; 480 mΩ @ 1.8 V/200 mA | ±1 µA @ ±6 V | 20 V / ±8 V | **PASS on all criteria** |
| Diodes DMN2004DWK-7 (C156343) | Ext / 5 112 | SOT-363 | Diagram (no pin numbers): bottom S2 G2 D1, top D2 G1 S1. With the standard pin 1 at bottom-left this is 1 S2, 2 G2, 3 D1, 4 S1, 5 G1, 6 D2: the same topology with Q1/Q2 labels swapped | 0.5–1.0 V @ 250 µA | 0.9 Ω @ 1.8 V/350 mA | ±1 µA @ ±4.5 V (only) | 20 V / ±8 V | PASS (IGSS specified only at 4.5 V) |
| onsemi NTZD3154NT1G (C145189) | Ext / 34 692 | SOT-563 | 1 S1, 2 G1, 3 D2, 4 S2, 5 G2, 6 D1 | 0.45–1.0 V @ 250 µA | 0.9 Ω @ 1.8 V/350 mA | **±5 µA @ ±4.5 V** | 20 V / **±7 V** | Marginal: IGSS and VGS max miss spec |
| Vishay SI1024X-T1-GE3 (C86784) | Ext / 33 554 | SOT-563 | 1 S1, 2 G1, 3 D2, 4 S2, 5 G2, 6 D1 (100 Ω gate resistor inside) | 0.45–0.9 V @ 250 µA | 1.25 Ω @ 1.8 V/350 mA | ±1 µA @ ±4.5 V | 20 V / **±6 V** | Fails VGS max ≥ ±8 V; otherwise the best Vth |
| Nexperia NX3008NBKS,115 (C396098) | Ext / 4 446 | SOT-363 | 1 S1, 2 G1, 3 D2, 4 S2, 5 G2, 6 D1 | 0.6–**1.1** V @ 250 µA | 2.8 Ω @ 1.8 V/10 mA | 1 µA @ 8 V | 30 V / ±8 V | Fails Vth max (1.1 V) |
| Vishay SI1922EDH-T1-GE3 (C141538) | Ext / **8** | SC-70-6 | 1 S1, 2 G1, 3 D2, 4 S2, 5 G2, 6 D1 | 0.4–1.0 V @ 250 µA | 0.263 Ω @ 1.8 V/0.2 A | 1 µA @ ±4.5 V; **±25 µA @ ±8 V** | 20 V / ±8 V | No stock; high IGSS at 8 V |
| Toshiba SSM6N43FU,LF (C17287625) | Ext / 2 198 | SOT-363 (US6) | not verified | LCSC lists "1 V" | 1.52 Ω @ 1.5 V (LCSC and a web summary) | not verified | 20 V / ±10 V (web summary) | **Unverified**: datasheet download blocked |
| Nexperia PMDXB600UNEZ (C552764) | Ext / 10 046 | **DFN1010-6** | 1 S1, 2 G1, 3 D2, 4 S2, 5 G2, 6 D1 | 0.45–0.95 V @ 250 µA | 1.3 Ω @ 1.8 V; 3 Ω @ 1.5 V | 10 µA @ 8 V | 20 V / ±8 V | Wrong package; IGSS too high |
| Diodes DMN26D0UDJ-7 (C151602) | Ext / **0** | **SOT-963** | — | 0.45–1.05 V | 6 Ω @ 1.8 V; 10 Ω @ 1.5 V | 100 nA @ ±5 V | 20 V / 10 V | Wrong package, no stock |
| Diodes DMN63D8LDW-7 (C211422) | Ext / 3 244 | SOT-363 | — | 0.8–**1.5** V | 13 Ω @ 2.5 V | 10 µA @ ±20 V | 30 V / ±20 V | Fails Vth |
| onsemi NTJD4001NT1G (C190019) | Ext / 29 999 | SOT-363 | 1 S1, 2 G1, 3 D2, 4 S2, 5 G2, 6 D1 | 0.8–**1.5** V @ 100 µA | 2.5 Ω @ 2.5 V | ±1 µA @ ±10 V | 30 V / ±20 V | Fails Vth; no 1.8 V spec |
| Toshiba SSM6N7002KFU,LF (C6916295) | Ext / 1 341 | SOT-363 | 1 S1, 2 G1, 3 D2, 4 S2, 5 G2, 6 D1 | 1.1–**2.1** V | spec only ≥ 4.5 V | ±10 µA @ ±16 V | 60 V / ±20 V | Fails Vth |
| Toshiba SSM6N58NU (C262142) | Ext / 96 | **UDFN-6 2×2** | — | 0.4–1.0 V @ 1 mA | 180 mΩ @ 1.8 V | ±10 µA @ ±10 V | 30 V / ±12 V | Wrong package |
| Diodes BSS138DW-7-F (C154900) | Ext / 51 417 | SOT-363 | — | 0.5–**1.5** V | only at 10 V | 100 nA @ ±20 V | 50 V / ±20 V | Fails Vth |
| DMG1012UDW / PMGD290UN | none at JLC | — | — | — | — | — | — | DMG1012UDW returned nothing; DMG6968UDM is SOT-23-6 (wrong package); PMGD290UN was not checked at JLC and its datasheet download failed |

Chinese clones found at JLC: Tech-Public TPNTZD3154NT1G (C2940615) and NTZD3154NT1G
(C2940619); VBsemi NTZD3154NT1G-VB and Si1024X-T1-GE3-VB (SC-75-6, "400 mV" Vth);
Tech-Public NX3008NBKS-TP (C48543207, 3 905) and DMN2004DWK (C3011186). Only the LCSC
parametrics were looked at for these, not their datasheets. No Basic part among them.

## Datasheet references (pages)

- SSM6N56FE (Toshiba, Rev 1.0, 2014-04-10): p1 has the pin assignment and the RDS(on)
  summary. p3 §5.1 gives Vth, IGSS and RDS(on). p2 §4 gives VGSS ±8 V.
  https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/1806150923_TOSHIBA-SSM6N56FE-LM_C146449.pdf
- DMN2004DWK (Diodes, DS30935 Rev 8-2): p1 has the pin diagram. p2 has the ratings and
  electrical table.
  https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/1806091426_Diodes-Incorporated-DMN2004DWK-7_C156343.pdf
- NTZD3154N (onsemi): p1 has the SOT-563 pinout and ratings. p2 has the electrical table.
  https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/1810301515_onsemi-NTZD3154NT1G_C145189.pdf
- SI1024X (Vishay, S11-0854 Rev E): p1 has the pinout and ratings. p2 has the electrical table.
  https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/1806122032_Vishay-Intertech-SI1024X-T1-GE3_C86784.pdf
- NX3008NBKS (Nexperia): p2 Table 2 has the pinning. The static characteristics table
  (around p5) gives Vth and RDS(on). https://assets.nexperia.com/documents/data-sheet/NX3008NBKS.pdf
- PMDXB600UNE (Nexperia): https://assets.nexperia.com/documents/data-sheet/PMDXB600UNE.pdf
- SI1922EDH (Vishay): p1 has the pinout, p2 has the electrical table.
  https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2411220707_Vishay-Intertech-SI1922EDH-T1-GE3_C141538.pdf
- DMN63D8LDW, NTJD4001N, DMN26D0UDJ, BSS138DW, SSM6N7002KFU, SSM6N58NU: the LCSC-mirror
  datasheets linked in the JLC API results, p2–3 in each.

## Recommendation

**Toshiba SSM6N56FE,LM, LCSC C146449 (JLC Extended, 7 293 in stock, SOT-563/ES6).**
- It is the only stocked part that meets every requirement, and its pinout matches the
  wanted one exactly (1 S1, 2 G1, 3 D2, 4 S2, 5 G2, 6 D1).
- Vth max is 1.0 V measured at 1 mA. The other parts specify Vth at 250 µA, so Toshiba's
  test is stricter and the device needs less VGS to conduct 33 µA. RDS(on) is guaranteed
  at 1.5 V (840 mΩ max at 50 mA). At VGS = 1.8 V and ID = 33 µA the drain sits at a few
  mV, far below 0.4 V.
- IGSS is ±1 µA at ±6 V. Across 100 kΩ that drops at most 0.1 V.
- VGSS is ±8 V and VDSS is 20 V.
- Extended justification: no Basic dual N-FET exists. 1.8 V gate drive requires a
  sub-1 V-threshold part, and the common 2N7002DW and BSS138DW fail on Vth.
- Caveat: V(BR)DSX drops to 15 V when the gate is reverse-biased (−5 V). That cannot
  happen here.

Fallback if SOT-363 is required: **Diodes DMN2004DWK-7, C156343** (Extended, 5 112 in
stock). It passes everything, but IGSS is specified only at ±4.5 V. The diagram is drawn
with Q2 on pins 1–2, which is the same topology as the wanted pinout with the transistor
labels swapped.

Not recommended: NTZD3154N, despite the highest stock (34.7 k). VGS max is ±7 V, and IGSS
is ±5 µA, which across 100 kΩ could cost 0.5 V of the 1.8 V gate drive.

## Unverified / open items
- SSM6N43FU: Toshiba and mirror datasheet downloads were blocked, so the pinout, Vth max
  and IGSS were not confirmed.
- DMN2004DWK pin numbering: the datasheet diagram has no pin numbers. Pin 1 at
  bottom-left (standard SOT363) was assumed; check against the Diodes SOT363 package
  outline before drawing the symbol.
- Stock figures are JLC `stockCount` on 2026-10-06. LCSC stock may differ.
- Chinese clones were not checked against their own datasheets.
- PMGD290UN and DMG1012UDW: no JLC listing was found, and their datasheets were not
  retrieved.
