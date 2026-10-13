# v2.0 Rev A — GATE V4 package (fab)

Status: **paused 2026-10-10 (owner)** while JLC produces v1.0 Rev B. Updated 2026-10-13 after
GATE B3:
- `main` merged in;
- side-view LED footprint fixed (GATE V3 amendment, `docs/v2-gate-v3.md`);
- `make jlc-check` extended to 6 layers;
- the order procedure is now the production-file check + JLC engineers' final DFM (step 1 below).

Previous gate: `docs/v2-gate-v3.md` (approved 2026-10-10; amendment 2026-10-13 awaiting owner review)

SPEC A3 §9: *GATE V4 = fab package (`make fab` exit 0), cost check.*

## State

| Item | State |
|---|---|
| `make fab` | package written to `fab/`, **exit 2 = ORDER BLOCKED** (by design): the new/changed polarized parts (D3/D4, U3–U6, Q1–Q3, RN1–RN3) await JLC's final DFM; the unchanged Rev-B footprints carry their 2026-10-13 final-DFM offsets |
| Gerber zip | **6 copper layers** + masks, silk, paste, outline, PTH/NPTH; `make fab` now asserts the copper count (the rev-B file list held only In1/In2 and would have dropped In3/In4) |
| BOM / CPL | 25 lines / 50 placed parts, no DNP |
| `make drc` / `make check` | 0 violations, 0 unconnected / PASS |
| `fab/README.md` | rewritten for v2 order settings |
| DATASHEET.md | v2 edge-pin functions, eFuse supply, 6-layer PCB, block diagram, test points |

## 1. Placement check (owner — at order time, procedure from the Rev B order)

The pre-order preview is automatic and for reference only. The real checks happen after ordering
(steps in `fab/README.md`):
1. **Production files:** `make jlc-check JLC=<zip>` must PASS. It now covers all 6 copper layers
   and fails if one is missing.
2. **Engineers' final DFM:** check every row of `fab/polarity_checklist.md` using N/S.
   - **D3/D4: lens toward the card edge AND "+" on the R3/R4 pad, both at once.** Ask the engineers
     to confirm on the physical part.
3. Then I set the verified dates in `JLC_ROT`, and `make fab` must exit 0.

Rotation offsets come from comparing JLC's own (EasyEDA) library footprint with ours, pad by pad:

| Part | JLC library vs ours | Offset | Confidence |
|---|---|---|---|
| U6 TPS259470A (RPW) | identical: pin 1 top-left; every pad within 0.015 mm | 0 | high (sign-free) |
| U3–U5 TMUX1511 (RSV) | rotated 90° | +90 | **sign is a guess** (bottom-side mirror) |
| Q1–Q3 SSM6N56FE (SOT-563) | rotated 90° | +90 | **sign is a guess** |
| RN1–RN3 4×0402 array | rotated 90°, 180°-symmetric | +90 | pads must land |
| D3/D4 TJ-S1706 side-view LEDs | footprint **renumbered** (GATE V3 amendment) | **0** (was +180) | derived from v1 (+0: lens out) and Rev B (+180: polarity right); **confirm lens + polarity** |
| D1/D2, U1, U2, J3 | unchanged footprints | as Rev B (0) | verified in Rev B's final DFM 2026-10-13 |
| J4 JST SH-8 | unchanged footprint | **+180** | verified in Rev B's final DFM 2026-10-13 |

If pin 1 of a U3–U5 or Q1–Q3 part shows up in the opposite corner, the sign is wrong: the offset
becomes 270.

## 2. U6 footprint (open item from GATE V2/V3)

Our RPW land pattern (drawn from the TI datasheet) was checked against JLC/LCSC's library footprint
for C3662799, which is the footprint JLC assembles with:
- every pad matches within 0.015 mm;
- the L-shaped corner pads have the same extents;
- the IN and OUT bars are at the same positions.

One cosmetic issue: the footprint is *named* `…P0.5mm`, but the side pins are at 0.45 mm pitch in
both footprints. Only the name is wrong; the geometry is correct. TI's own CAD model was not
downloaded: it needs a TI or Ultra Librarian login.

## 3. Cost check (2026-10-10)

PCB: quote with the order settings. Parts: JLC library prices at the order quantity. Assembly fees:
JLC's published Standard PCBA table (Sept 2025; check it in the live quote).

| | 5 boards | 100 boards |
|---|---|---|
| PCB 6L 0.8 mm, ENIG, gold fingers, 0.2/0.35 via option | $85.39 | $207.49 |
| Parts (25 lines, 13 Extended) | $50.20 ($10.04/board) | $762 ($7.62/board) |
| Assembly setup, double-sided Standard PCBA | $50 | $50 |
| Stencil (2 sides) | ≈ $16 | ≈ $16 |
| Feeder loading, $1.5 × 25 part lines | $37.50 | $37.50 |
| Solder joints, 241/board × $0.0016 | $1.93 | $38.56 |
| **Total before shipping** | **≈ $241 (≈ $48/board)** | **≈ $1,112 (≈ $11.1/board)** |

The module is $3.82 of the $7.62 per-board parts cost at 100 boards. The v2 silicon adds ≈ $2.5 at
100 boards: U3–U5 $1.11, U6 $0.93, Q1–Q3 $0.40, RN arrays, 0.1 % resistors.

## 4. Supply risk — decision needed

| Part | Need per 100 boards | JLC stock (2026-10-10) |
|---|---|---|
| **SSM6N56FE (Q1–Q3)** | 300 | **124** (7,293 on 2026-10-06) |
| TMUX1511 (U3–U5) | 300 | 1,013 |
| TPS259470A (U6) | 100 | 1,440 |
| ESP32-S3-WROOM-1-N8R2 | 100 | 18,402 |

5 prototypes need 15 SSM6N56FE, which stock covers if it doesn't drop further before ordering.
Same-footprint, same-pinout (SOT-563, 1 S1 / 2 G1 / 3 D2 / 4 S2 / 5 G2 / 6 D1) options, from the
V1 research (`v2/research/dual_nmos_research.md`):

| Option | Stock | Unit | Fit |
|---|---|---|---|
| keep SSM6N56FE (C146449) | 124 | $0.19 | passes every V1 criterion |
| Vishay SI1024X-T1-GE3 (C86784) | 945 | $0.36 | Vth 0.45–0.9 V (better), IGSS 1 µA. Fails only our own VGS-max ≥ ±8 V margin (±6 V); our gates never exceed 3.6 V |
| onsemi NTZD3154N (C145189) | 78,991 | $0.06 | IGSS up to 5 µA: too much for the 1 MΩ CONFIG detect divider. **Not recommended** |

**Owner decision (2026-10-10):**
- Prototypes: keep **SSM6N56FE** (C146449).
- **SI1024X-T1-GE3 (C86784) is the approved second source**, with no PCB change. It's recorded in
  the part's `LCSC_2nd_source` field and in the review BOM (`docs/review/v2_reva_bom.md`, column
  "Approved 2nd source"). The JLC upload carries the primary part; swap by hand only if it's out of
  stock at order time.

## 5. After the order

- Tag `v2.0-revA` on the exact commit whose fab files were ordered (CLAUDE.md naming rule).
- Bring-up and acceptance tests are SPEC S-v2-1…4 (bus off on every host, bus on with the carrier
  signature, OVP trip window, all v1 criteria).
