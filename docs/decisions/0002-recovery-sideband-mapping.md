# ADR 0002 — Recovery sideband mapping & Schottky isolation

Date: 2026-08-28 · Status: **accepted** (GATE 1, owner)

## Decision

- **EN** ← M.2 pin 50 (PERST#), via small-signal Schottky (anode on card net),
  on-card 10 kΩ pull-up to 3V3 + RC (10 kΩ/1 µF) per Espressif HDG.
- **BOOT (GPIO0)** ← diode-OR of M.2 pin 20 (Mallow X16 jumper path) **and**
  pin 8 (W_DISABLE1#, for hosts that wire it), on-card 10 kΩ pull-up.
- All sideband inputs are diode-isolated so 1.8 V hosts (Verdin GPIOs are not
  3.3 V-tolerant) can pull low without ever seeing our 3.3 V pull-ups.

## Context

Mallow V1.1 wires only PERST# (pin 50 → SODIMM 244) to the SoM; W_DISABLE1#
is pull-up-only; pins 6/67 have no documented driver (67 is 1.8 V domain).
Pins routed to X16 allow jumpering BOOT to any SoM GPIO. Details and rejected
candidates: docs/pinmap.md §3.

## SODIMM 244 usability as GPIO (verified in mainline device trees)

| Verdin SoM | SoC line for SODIMM 244 | Default DT owner | To free for gpioset |
|---|---|---|---|
| iMX8M Plus | GPIO4_IO19 (SAI1_TXD7 pad) | `&pcie` `reset-gpio` (imx8mp-verdin.dtsi:800–804) | overlay disabling `&pcie` |
| iMX8M Mini | GPIO3_IO19 (SAI5_RXFS pad) | `&pcie0` `reset-gpio` (imx8mm-verdin.dtsi:706–708) | overlay disabling `&pcie0` |
| AM62 | MCU_GPIO0_0 | gpio-hog present but `status = "disabled"` (k3-am62-verdin.dtsi:1432–1438) | free by default |

iMX8MP and AM62 dtsi name the line `"SODIMM_244"`, so
`gpioset $(gpiofind SODIMM_244)=0` works without chip/line hunting.
Exact overlay steps per owner's SoM go into docs/bringup.md (Phase 4).

## Consequences

- Recovery on Mallow needs one jumper wire (X16.19 → chosen SoM GPIO) for
  BOOT; EN works with zero carrier modification.
- Hosts can only assert (pull low), never drive high — sufficient for the
  recovery flow; default state comes from on-card pull-ups.
