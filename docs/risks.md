# Risk register

| ID | Risk | Status 2026-08-28 | Mitigation / next step |
|---|---|---|---|
| R1 | Mallow B-key USB wiring & sideband→SoM mapping unconfirmed | **Resolved.** USB 2.0 on pins 7/9 (via USB5744 hub port 3); PERST# (pin 50) → SODIMM 244 is the only SoM-wired sideband; W_DISABLE1# (pin 8) is pull-up-only; pins 6/67 have no documented driver; PCIE_1_GPIO_0..11 go to X16 header only (jumper wires needed for BOOT). SODIMM 244 confirmed a plain SoC GPIO on iMX8MP/iMX8MM/AM62 (ADR 0002); DT overlay needed on iMX8M* images. | Per-SoM `gpioset` steps → docs/bringup.md (Phase 4). |
| R2 | JLCPCB gold fingers + bevel on 0.8 mm 4-layer | Open | Check JLCPCB capability page / quote in Phase 2 before layout is frozen. |
| R3 | Antenna flat against carrier board | Accepted (v1) | Keep-out per Espressif HDG; best-effort. |
| R4 | 2242 fit in RPi5 Key-B HATs | **Accepted.** RPi5 demoted to nice-to-have at GATE 1 (ADR 0004). Waveshare HAT+ fits 3042/3052 only; no published schematic; USB 2.0 presence inferred from official SIM7600-M.2 (USB2-only modem) support. | Best-effort via test points / flying leads; no design decision may block on RPi5. |
| R5 | GPIO choice vs octal-PSRAM reservation | **Resolved by design.** IO35–37 kept NC; N8R2 ⇄ N16R8 drop-in compatible. | — |
| R6 | 1.8 V host GPIO domain (Verdin) vs 3.3 V card nets | New | Schottky-diode isolation on all sideband inputs (pinmap §3.2). |
| R7 | USBLC6 datasheet on file is the UMW clone, not ST original | **Resolved (sourcing).** Owner decision: ST C7519 primary, UMW C2687116 approved second source. | Owner to drop the ST PDF into docs/datasheets/ when convenient (st.com blocked from this machine); UMW doc on file covers the pin map either way. |
| R8 | M.2 EM spec (mechanical outline, gold-finger geometry) paywalled | New | Owner to provide spec PDF, or Phase 2 uses a derived/verified drawing (e.g. KiCad official M.2 edge footprints) with explicit dimension checks. |
