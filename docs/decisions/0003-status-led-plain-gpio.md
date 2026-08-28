# ADR 0003 — Status LED: plain LED on IO48

Date: 2026-08-28 · Status: **accepted** (GATE 1, owner)

Plain LED, active-low, series resistor, on GPIO48 (module pin 25). WS2812B-2020
option rejected for v1: extra part (Extended at JLCPCB), timing-sensitive
driver, no functional gain for a heartbeat indicator. IO48 has devkit
precedent (RGB LED on ESP32-S3-DevKitC), is not a strapping pin, and is free
on N8R2/N16R8 (the 1.8 V VDD_SPI caveat applies only to R16V variants,
WROOM-1 datasheet v1.8 Table 3-1 note c).
