# Datasheets — edge_expansion

| Part | File | Used for |
|---|---|---|
| TI TMUX1511 (U3–U5) | `docs/datasheets/tmux1511.pdf` (SCDS390B) | Table 4-1 UQFN pinout; §5.5 VIH 1.2 V / VIL 0.45 V / IIH ±2 µA / RPD 6 MΩ; IPOFF ±2 µA at VDD = 0; tON(VDD) 20–60 µs |
| Toshiba SSM6N56FE (Q1) | `docs/datasheets/ssm6n56fe.pdf` (Rev 1.0) | §3 pin assignment; VGS(th) 0.4–1.0 V @ 1 mA; RDS(on) 480 mΩ @ 1.8 V; IGSS ±1 µA |
| Vishay SI1024X-T1-GE3 (Q1 2nd source, C86784) | `docs/datasheets/si1024x.pdf` (Rev. E) | same pinout; Vth 0.45–0.9 V @ 250 µA, IGSS ±1 µA max — comparison in `hardware/blocks/host_sideband/datasheets.md` |
| 4D02WGJ0221TCE (RN1–RN3) | LCSC C25498 (UniOhm datasheet, `v2/research/v2_parts_check.md` §5) | convex type, pad order = KiCad R_Array_Convex_4x0402 |
| Research | `v2/research/parts_research.md`, `dual_nmos_research.md`, `m2_pins_research.md` | selection rationale |
