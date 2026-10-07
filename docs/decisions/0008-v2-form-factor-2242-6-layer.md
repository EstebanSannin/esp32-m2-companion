# ADR 0008 — v2 form factor: stay 2242, go 6 layers

Date: 2026-10-07 · Status: **accepted** (owner)

## Context

The v2 additions (ADR 0006/0007) add ~47 nets and ~35 parts. A routing
feasibility probe on the frozen rev-B placement
(`v2/edge-expansion-brainstorm.md` §12; `v2/probe/gridprobe.py`, judged by
KiCad DRC) gave:
- **4 layers: 17/47** nets routed. The strip between the module and the
  fingers is the wall.
- **6 layers: 31/47.** The failures are local congestion in a non-routing-aware
  placement.

JLC quote 2026-10-07 (0.8 mm, ENIG, gold fingers):

| Variant | 5 pcs | 100 pcs |
|---|---|---|
| 4 layers | $24.80 | $60.04 |
| 6 layers | $48.80 | $115.60 (+$0.56/board) |

2252 costs the same as 2242.

## Decision

- **2242, 6 layers, 0.8 mm.** Stackup from JLC's JLC06081H family
  (exact one TBD): SIG / GND / SIG / SIG / PWR / SIG, USB pair referenced to
  the adjacent GND.
- **v2 is a re-placement**, not a patch on rev B:
  - Move or merge the test-point row.
  - Consider moving J3/J4.
  - Give the switch cluster room for UQFN escape.
- **Gate before hand-routing:** `gridprobe.py` must route all new nets
  DRC-clean on the new placement.
- Owner prefers the small card ("looks more attractive"). A future "plus"
  model may use 2252/2260. Carriers get standoff positions for
  2242/2252/2260 (`docs/carrier-interface.md` §2).

## Consequences

- +$24 per 5-pc prototype order, +$0.56/board at 100 pcs.
- Supersedes the "4-layer (SIG/GND/PWR/SIG)" rule in CLAUDE.md and SPEC §5
  for v2 (needs SPEC amendment A3).
- **If the post-re-placement probe still fails, fall back to 2252 / 4 layers.**
  Revisit with the owner first.
