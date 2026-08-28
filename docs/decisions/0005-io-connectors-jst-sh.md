# ADR 0005 — IO header replaced by JST SH connectors (SPEC §6.6 amendment)

Date: 2026-08-28 · Status: accepted (owner)

## Context

SPEC §6.6 asked for an unpopulated 1×12 2.54 mm header "along the long card
edge". Geometry veto: 12 × 2.54 = 30.5 mm > 22 mm card width, and the strips
beside the 18 mm module are 2 mm. Owner direction: "something small, one or
two connectors with small footprints".

## Decision

Two JST SH (1.0 mm) side-entry SMT connectors, **assembled** (no longer
unpopulated — SH is not hand-solder-friendly, and cables are pre-made):

- **J3 = SM04B-SRSS-TB (LCSC C160404, Extended)** — Qwiic/STEMMA-QT pinout
  (GND, 3V3, SDA, SCL): the I2C ecosystem standard; sensors plug in with
  off-the-shelf cables.
- **J4 = SM08B-SRSS-TB (LCSC C160407, Extended)** — TX, RX, CS, MOSI, CLK,
  MISO, IO14, IO21: full native FSPI set + UART0 + two GPIO.

All 12 originally-planned signals remain exposed. I2C pull-ups stay DNP.

## Consequences

- Owner needs SH-4 (Qwiic) and SH-8 1.0 mm cable assemblies instead of
  2.54 mm jumper wires.
- Two more Extended BOM lines (justified: no Basic 1 mm connectors exist).
- In-slot cable routing is tight (side entry, 1.6 mm tall); primary IO use
  case is bench / extender / flipped carrier.
