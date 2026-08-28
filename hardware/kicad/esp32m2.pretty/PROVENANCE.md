# Footprint provenance

- `M.2-B-KEY.kicad_mod`: from https://github.com/timonsku/M.2-Card-Footprints
  (CERN-OHL-P v2), vendored 2026-08-28. Author states the B-Key footprint is
  the one **verified on a fabricated PCB**; default size 2242 (exactly ours).
- To be verified pad-by-pad against docs/datasheets/m2_em_spec_rev1.0_2013_archive.pdf
  (card form-factor drawings) and docs/pinmap.md before GATE 3:
  pad numbering 1..75, notch at 12-19, odd/even side assignment, finger
  depth, notch offset (cross-check: Quectel Fig. 38, notch 4.3 mm feature).
- Derived working copy will be renamed `M2_KeyB_2242_EdgeFingers.kicad_mod`
  (name referenced by hardware/blocks/m2_keyb_edge) after verification.

## Verification record (2026-08-28, pre-GATE 3)

Checked `M2_KeyB_2242_EdgeFingers.kicad_mod` (derived from M.2-B-KEY.kicad_mod)
against M.2 EM Spec Rev 1.0 Figure 19 ("Key Detail for Keys G Thru M") +
Figure 21 and docs/pinmap.md:

- Pad counts: 34 odd on F.Cu / 33 even on B.Cu (spec: 34X / 33X) — OK
- Pad width 0.35 mm (spec 0.35±0.04), same-side pitch 0.5 mm, strip span
  18.5 mm, pin 1 ↔ pin 75 at ±9.25 mm — OK
- Key-B slot: width 1.2 mm, full-R end cap arcs r=0.6 at (5.6, −2.9) →
  depth 3.5 mm (spec 3.50±0.15), center 5.6 vs spec 5.625 (within tol) — OK
- Notch spans positions 12–19 (no pads there) — matches pinmap §1 — OK
- Outline 22 × 42 mm, corner radii, mounting semicircle Ø3.5 at top-edge
  center, plated GND pads Ø5.5 (top poly) / Ø6 (B.Cu ring) — OK
- CHANGED vs upstream: pads renamed `P$n` → `n` so pcbnew matches the
  SKiDL netlist pin numbers; module renamed.

Conclusion: footprint geometry confirmed against the EM spec; upstream's
"verified on fabricated PCB" claim independently cross-checked dimensionally.
