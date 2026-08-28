# Risk register

| ID | Risk | Status 2026-08-28 | Mitigation / next step |
|---|---|---|---|
| R1 | Mallow B-key USB wiring & sideband→SoM mapping unconfirmed | **Mostly resolved.** USB 2.0 on pins 7/9 (via USB5744 hub port 3); PERST# (pin 50) → SODIMM 244 is the only SoM-wired sideband; W_DISABLE1# (pin 8) is pull-up-only; pins 6/67 have no documented driver; PCIE_1_GPIO_0..11 go to X16 header only (jumper wires needed for BOOT). | Residual: confirm SODIMM 244 usable as GPIO on the owner's Verdin SoM/image (pinmap open item 3). |
| R2 | JLCPCB gold fingers + bevel on 0.8 mm 4-layer | Open | Check JLCPCB capability page / quote in Phase 2 before layout is frozen. |
| R3 | Antenna flat against carrier board | Accepted (v1) | Keep-out per Espressif HDG; best-effort. |
| R4 | 2242 fit in RPi5 Key-B HATs | **Confirmed real.** Waveshare PCIe TO 4G/5G M.2 USB3.2 HAT+ supports 3042/3052 only; no published schematic, sideband wiring unknown. USB 2.0 presence on socket inferred from official SIM7600-M.2 (USB2-only modem) support. | GATE 1 decision: accept best-effort (spacer/flying leads + test points) or choose another HAT. |
| R5 | GPIO choice vs octal-PSRAM reservation | **Resolved by design.** IO35–37 kept NC; N8R2 ⇄ N16R8 drop-in compatible. | — |
| R6 | 1.8 V host GPIO domain (Verdin) vs 3.3 V card nets | New | Schottky-diode isolation on all sideband inputs (pinmap §3.2). |
| R7 | USBLC6 datasheet on file is the UMW clone, not ST original | New | st.com unreachable from this machine; owner to supply ST PDF or approve UMW part (LCSC C323793) at BOM review. |
| R8 | M.2 EM spec (mechanical outline, gold-finger geometry) paywalled | New | Owner to provide spec PDF, or Phase 2 uses a derived/verified drawing (e.g. KiCad official M.2 edge footprints) with explicit dimension checks. |
