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
  or more by mistake. Limit: the OVLO pin abs max 6.5 V caps IN at ~18.9 V
  with the 52.3 k divider (the IC itself is rated 28 V) — GATE V2 correction.
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

## Amendment (RC1, 2026-10-28, owner): soft-start, OVLO filter, OUT capacitor, latch-until-power-cycle, no second source

Owner decision after the release-candidate review ("go with your
recommendations, approve the change list"); evidence in
`docs/review/v2_rc1_design_review.md` (power-1..4, power-6,
contract_test-7). Authoritative values: `hardware/blocks/power_3v3/power_3v3.py`.

- **DVDT: C15 2.2 nF 50 V** (U6 pin 7 to GND; review power-3 / K1). With
  DVDT open the slew was ~12–15 V/ms, i.e. 0.5–1 A of inrush into the
  ~65 µF card rail: at the current limit, and above the 200 mA slot
  soft-start that M.2 allows hosts (M.2 Rev 1.0 Table 39). With 2.2 nF:
  ~0.7 V/ms typical, ≤ 1.3 V/ms at max IdVdt → inrush ≤ ~90 mA; over the
  full IdVdt spread and C15 ±10 % the rail goes 0 → 3.3 V in **~2–16 ms
  including the turn-on delay** (RC1 delta review power-rc1-2; "up to
  ~13 ms" before). The ESP32 EN RC (10 kΩ / 1 µF) still releases after the
  rail is up. Rated ≥ VIN + 5 V (datasheet Rec. Op.). X7R accepted (C0G
  would only narrow the slew spread). C15 sits 0.32 mm from the V-scored
  long edge (no room inboard of U6): accepted deviation — the 0402 runs
  parallel to the edge, a crack fails safe (short = card stays off, open =
  pre-RC1 fast ramp), and bring-up step 3.2 sees it.
- **OVLO filter: C16 100 pF 50 V C0G** (C1546, 0402CG101J500NT) at the
  divider tap (review power-1; value per RC2, below). The 34 kΩ node had no
  capacitor and tOVLO is 1.2 µs with no deglitch, so hot-plug ringing or
  the fast-trip input spike could trip it. τ ≈ 3.4 µs (still ~20× attenuation
  of MHz ringing). On a hard step the trip delay is a few µs plus tOVLO
  1.2 µs. **The worst case is a ramp**, not a
  step: until OVLO trips the HFET is fully on, OUT follows IN, and the
  current limit only settles in ~400 µs (tLIM), so the filter lag adds to
  the trip voltage. With 100 pF the worst-case ramp model puts +3V3 at
  **~3.56–3.6 V typ, up to ~3.65 V** for µs on 50–100 µs ramps (the max trip
  alone is 3.561 V, so no filter value meets "never > 3.6 V" on a ramp);
  see RC2 below.
- **OUT capacitor: C17 1 µF 25 V** (CL05A105KA5NQNC, C52923) on +3V3_EFUSE
  **at FB1 pad 1, ~4 mm of track from U6 OUT** (no closer spot on the
  bottom side; review power-4; TI §8.3.1/§8.4.1 "≥ 1 µF close to OUT").
  FB1 had put inductance straight on the OUT pin. The extra ~3 nH matters
  only on fast-trip / hot-plug edges (RC1 delta review power-rc1-3 /
  layout-5: accepted). X5R 0402 keeps ~0.7–0.8 µF at 3.3 V; 54 µF of bulk
  sit just behind FB1 (power-rc1-4: accepted).
- **OVLO recovery = slot power-cycle (accepted).** Trip 3.44–3.57 V;
  release 3.13–3.25 V at IN (VOV(F) 1.076–1.116 V × 2.912). At a nominal
  3.30 V the OVLO pin sits at 1.133 V, above the maximum VOV(F), so after
  any trip **the card stays off until the slot rail goes to 0 V and back**.
  This corrects "Auto-recovers at ~3.23 V; not latched" (51 k divider) and
  "re-enables below ~3.17 V" (GATE V1 amendment) above: those thresholds
  are right, but on a 3.3 V host they are never reached. The host cannot
  power-cycle the card alone (EN tied to IN via R33, FULL_CARD_POWER_OFF#
  NC), and firmware cannot see the event (FLT NC; FLT does not assert on
  OVLO). Accepted: the filter makes a spurious trip unlikely, and a real
  overvoltage must keep the card off.
- **Restart after an OVLO trip bypasses dV/dt** (datasheet §7.3.3: the
  TPS259470x "start up in a current limited manner"): up to the current
  limit 0.85 / 1.01 / 1.15 A (min/typ/max, R34 3.3 kΩ; "~1 A" above). C15
  does not cover it. Bench tests use a ≥ 1.2 A limit for that step.
- **No approved second source for U6.** "same-footprint TPS259474L
  C2864845 as second source" above is **withdrawn** (review power-2 /
  contract_test-7): the 474L is a latch-off circuit breaker (with ITIMER
  open, any overload above ILIM latches the card off until the slot is
  power-cycled), and its pins 3/4 are PG/PGTH instead of AUXOFF/FLT. Keep
  spare TPS259470ARPWR stock instead. Single-source risk: R-v2-13
  (`docs/risks.md`).
- **FB1** is Murata BLM18PG121SN1D (C14709, ≤ 50 mΩ DCR) since GATE V2,
  not the 150 mΩ bead named in Context. Drop at 0.5 A including socket
  contacts and copper: ~65–70 mV, i.e. ~3.065 V at the module from a
  3.135 V host (review power-5).

## Amendment (RC2, 2026-10-28, owner): OVLO filter 100 pF C0G

Owner decision after the RC1 delta review ("accept your recommendations";
`docs/review/v2_rc1_delta_review.md` power-rc1-1, major). Hardware commit
"v2 RC2: OVLO filter 100 pF C0G".

- **C16 1 nF X7R → 100 pF C0G** (C1546, 0402CG101J500NT, Basic). With 1 nF
  (τ 34 µs) an overvoltage **ramp** of tens of µs (a carrier or regulator
  fault) lifted +3V3 to ~3.7–3.9 V before the trip: the HFET stays on and
  the current limit settles in ~400 µs, so the filter lag (ramp rate × τ)
  adds to the 3.561 V maximum trip. The "~4 µs trip, stays < 3.6 V" claim of
  the RC1 amendment held only for a hard step on a typical part. With
  100 pF (τ 3.4 µs) the worst-case ramp model peaks at ~3.56–3.6 V typ and
  up to ~3.65 V (RC2 check power-1, including the eFuse RON + FB1 drop; the
  first RC2 text said ~3.55 V, which is below the 3.561 V max trip and was
  wrong). A hard step stays < 3.6 V (trip after a few µs plus tOVLO 1.2 µs).
  Residual: up to ~50 mV above the ESP32 3.6 V abs max for µs on a ramp -
  risk R-v2-9, owner to accept at GATE V4.
- The review's X7R remark on C16 (power-rc1-4) is moot: the part is C0G.
- Bring-up: step 4.5 of `docs/v2-test-procedure.md` now also asks for a
  50–100 µs ramp from 3.3 V to 5 V, scoping +3V3 at the module.
- Values: `hardware/blocks/power_3v3/power_3v3.py` (authoritative).
