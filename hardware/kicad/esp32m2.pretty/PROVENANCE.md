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
