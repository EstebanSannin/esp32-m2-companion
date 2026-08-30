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

## Amendment (2026-08-28, GATE 2 adversarial review)

The original "Consequences" overstated the isolation: the diode blocks only
when the host sideband is **Hi-Z or open-drain released**. A host driving
push-pull HIGH below ~2.8 V (e.g. 1.8 V) forward-biases the diode (~125 µA)
and drags EN/IO0 to ~2.0–2.1 V — inside the undefined input band
(VIL 0.825 V / VIH 2.475 V @ 3.3 V). Real constraint: host sidebands must
idle OD/Hi-Z or push-pull with V_OH ≥ ~2.8 V; recovery flows must RELEASE
BOOT/EN to input/Hi-Z, never drive them high. Mallow's documented paths
satisfy this. Two host-behavior failure modes recorded in docs/risks.md:
W_DISABLE1# held low at boot forces download mode (R10); a stock Mallow
image's PCIe driver may leave PERST# asserted (R9).

## Amendment (2026-08-30, owner): pin-8 (W_DISABLE1#) BOOT leg DROPPED in v1

The BOOT diode-OR originally took two inputs: M.2 pin 20 (PCIE_1_GPIO_5,
Mallow) and M.2 pin 8 (W_DISABLE1_n, generic non-Mallow hosts). The pin-8
leg is **removed for v1**. Two reasons:

1. **Redundant.** BOOT (IO0) is exposed on **TP2** and EN on **TP1**, so any
   host — Mallow or not — can force ROM download by driving TP1(EN)+TP2(BOOT)
   with flying leads (or jumping straight to the module). The Mallow in-slot
   path (pin 50 EN + pin 20 BOOT) is fully routed and unaffected. Pin 8 only
   added *automatic* BOOT on a non-Mallow host that (a) bricks, (b) can't be
   physically touched, AND (c) wires pin 8 to a controllable GPIO — a
   near-empty intersection. Note even Mallow only pulls pin 8 up through a
   resistor (not GPIO-driven), so pin 8 is non-functional there anyway.
2. **Unroutable in this placement.** Pin 8 sits in a 0.5 mm-pitch
   3-conductor interleave (USB D+/W_DISABLE/D− on M.2 pins 7/8/9) with no
   legal path to D2 on either copper layer; see docs/routing-method.md and
   review-findings.md.

Result: D2's second cathode (pin 2) is NC; the M.2 pin-8 edge finger is an
exposed but unconnected pad (kept for mechanical/standard-pinout reasons).
Recovery capability is preserved in full via host GPIO (Mallow) and
TP1/TP2 flying leads (universal). Recovery procedure: DATASHEET.md +
(Phase 4) docs/bringup.md.
