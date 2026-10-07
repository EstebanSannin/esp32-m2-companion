# ADR 0007 — v2 input overvoltage protection (eFuse with OVLO)

Date: 2026-10-07 · Status: **accepted** (owner: "yes, let's do it properly") · amended GATE V1 2026-10-07 (divider)

## Context

M.2 Rev 3.0 labels the supply pins "3.3 V/VBAT", and modems accept
3.135–4.4 V, so tablet-style hosts may feed ~4.4 V. The ESP32-S3-WROOM-1
absolute maximum is 3.6 V (recommended 3.0–3.6 V). v1/Rev B feeds the module
straight from the M.2 rail (only FB1 in between, 150 mΩ).

## Decision

- **TI TPS259470A eFuse** (LCSC C3662799; same-footprint TPS259474L C2864845
  as second source), 2×2 mm VQFN.
- **OVLO divider:** 100 k / 51 k **0.1 %**, so the trip lands at ~3.47–3.63 V
  (3.55 V typ).
  - With 1 % resistors the worst case would be 3.67 V, 70 mV above the
    absolute maximum. That's why 0.1 % is used.
  - Auto-recovers at ~3.23 V; not latched.
- **Current limit:** ILM 3.3 kΩ → ~1 A.
- **Drop:** RON 45 mΩ max, so ≤ 22.5 mV at 0.5 A. Worst case at the module
  on a 3.135 V host is 3.04 V.
  - Re-evaluate dropping or replacing FB1, which would gain 75 mV of margin.

## Consequences

- A 4.4 V host leaves the card **off and undamaged**. It also survives 5 V
  or more by mistake (VIN absolute max 28 V).
- **Cost:** +$0.81/board @100, up to 4 new BOM lines (Extended: no Basic
  eFuse with adjustable OVLO; 0.1 % resistors are Extended too).
  About 16 mm² on the board.
- **Rejected:**
  - LDO: the module sees < 3.0 V on a 3.135 V host.
  - TVS/crowbar: would short a legitimate 4.4 V rail.
  - Phone OVP switches: thresholds ≥ 4 V.
  - Clamp-type eFuses: output can reach 3.8–4.2 V.
  - Buck-boost: area, a switcher next to the antenna, 5.5 V max input.
  - Details: `v2/research/ovp_and_prices.md`.
- **Fixture:** the dev carrier provides a bench-supply input to test the trip
  point. Rev-B cards must never see > 3.6 V.

## Amendment (GATE V1, 2026-10-07, owner): divider 100 k / 52.3 k

The host maximum (3.465 V) and the ESP absolute maximum (3.6 V) are 135 mV apart. The OVLO
reference tolerance alone (±1.7 %) is wider than that, so no divider satisfies both.

- The owner chose **never exceed 3.6 V**: 100 k / **52.3 k** 0.1 % trips at **3.44–3.57 V**
  (3.49 V typ) and re-enables below ~3.17 V.
- A worst-case part may trip on a host sitting at its +5 % limit.
- This supersedes "100 k / 51 k, 3.47–3.63 V" above. Details: `docs/v2-gate-v1.md` §1.4.
