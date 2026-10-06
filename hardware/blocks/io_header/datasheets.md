# References — io_header
- SPEC §6.6; docs/pinmap.md §2 (GPIO selection rationale)
- ADR 0005: J3 = JST BM04B-SRSS-TB (Qwiic, C160390), J4 = JST BM08B-SRSS-TB
  (C160394) — **assembled**. I2C pull-ups R5/R6 10k **DNP**.
- Silk (rev B): legends `J3 QWIIC` / `J4 UART/SPI` beside the pin-1 arrows;
  per-pin pinout in DATASHEET.md (1.0 mm pitch is too fine for legible
  per-pin silk at the 0.8 mm minimum).
