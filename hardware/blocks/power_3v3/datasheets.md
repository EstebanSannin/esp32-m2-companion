# References — power_3v3
- SPEC §6.2 (A3 §6.2 / G11 for v2); Espressif HDG power sections
- U6 TI TPS259470A eFuse: `docs/datasheets/tps25947.pdf` (SLVSFC9C) —
  Table 5-1 pinout; §6 EC table (VOV(R) 1.183/1.20/1.223 V, VOV(F)
  1.076/1.09/1.116 V, IdVdt 0.81/2.21/3.82 µA, tOVLO 1.2 µs); §7.3.3 OVLO
  (restart after OVLO bypasses dVdt, current-limited); Eq.4 CdVdt sizing;
  Rec. Op. (CdVdt rated ≥ VIN + 5 V); §8.3.1/§8.4.1 (≥ 1 µF at OUT);
  Device Comparison Table (474x = circuit breaker, L = latch-off: not a
  drop-in second source). ADR 0007 + its GATE V1 and RC1 amendments.
- FB1 (v2): Murata BLM18PG121SN1D (LCSC C14709, Basic, 0603) 120R@100MHz,
  2 A, DCR ≤ 50 mΩ (`v2/research/v2_parts_check.md`).
  - Superseded (v1/Rev B): Sunlord GZ2012D101TF (C1015, Basic)
    100R@100MHz, 800 mA, 150 mΩ. 0 Ω link remains the fallback (the WROOM-1
    has its own internal LC filter).
- M.2 EM spec Rev 1.0 (`docs/datasheets/m2_em_spec_rev1.0_2013_archive.pdf`)
  Table 39: hosts may soft-start the slot at 200 mA (sizes C15).
