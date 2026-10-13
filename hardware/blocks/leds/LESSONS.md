- 2026-08-28 (GATE 2 review): tooling — DNP must be a BOM-generator-visible
  field, not just a schematic attribute; J3 leaked into the JLC assembly CSV
  because only `do_not_populate` was set. gen_bom now derives DNP from it.
- 2026-10-05 (**bring-up, both v1 boards**): D3 **and** D4 are mounted **180°
  reversed** — every LED is reverse-biased in-circuit (dark) yet lights fine
  under a meter's diode test. Isolated by measurement: 3V3 present at R3/R4,
  IO48 toggles 0/3.5 V cleanly, ~3.5 V across the LED with **zero current**, and
  the owner confirmed the LED's physical anode sits on the pad **not** connected
  to the series resistor. Drive circuit + firmware are 100% good; this is a
  **systematic assembly-orientation error** — the custom `LED_TJ-S1706_SideView`
  footprint's pin-1 (cathode) convention / exported CPL rotation (90°, bottom)
  does not match how JLC/LCSC orients C273612/C273616, so all parts were placed
  flipped. No v1 rework worth doing; no software fix (polarity is physical).
  **Rev-B fix:** make the footprint's pad-1 = the LCSC part's actual cathode
  (and/or add 180° to the D3/D4 CPL rotation), validate against a JLCPCB
  rotation-preview before ordering; re-confirm the emit face on a sample at the
  same time; and drop R3 (green) from 330 Ω to ~68-100 Ω (green runs sub-mA at
  3.3 V). This is the real cause behind the entire "LEDs don't light" hunt — it
  was never emit-direction, under-drive, firmware, or routing.
  **Root cause pinned (2026-10-05):** the schematic/footprint were CORRECT
  (netlist ties R4→anode); the reversal entered at **JLC assembly sign-off** — JLC's
  placement preview showed the LED flipped (their LCSC polarity/rotation
  convention for C273612/C273616 is opposite our footprint's pin-1), they asked
  us to confirm, and **we approved a preview with "+" on the chip-side pad instead
  of the resistor pad.** Fixable at assembly with NO respin: correct D3/D4 CPL
  rotation (+180°) or instruct "+ on the resistor-side pad". **PROCESS rule
  (shared hw skill candidate): never eyeball-approve a JLC LED placement preview —
  verify the "+" lands on the pad wired to the series resistor (i.e. against the
  netlist), because JLC/LCSC LED polarity convention frequently differs from the
  KiCad footprint and silently flips the part.**
- 2026-10-06 (rev B): fix lives in the fab export, not the footprint (pad
  numbering was right): tools/gen_fab.py JLC_ROT gives C273616/C273612 +180°
  and `make fab` stays ORDER-BLOCKED until each polarized part's rotation is
  dated as preview-verified; tools/polarity_report.py asserts anode =
  resistor-side pad and prints what the JLC preview must show. R3 330R →
  100R (C22775). Emit face: closed by v1 evidence (hand-rotated D4 blinks,
  polarity and emit direction restore together) - no package change.
- 2026-10-06 (rev B labels): the custom footprint had no silk polarity mark
  at all. Added a cathode bar at pad 1 (matches the part's black cathode
  mark). Any custom polarized footprint: silk mark from day one.
- 2026-10-13 (GATE B3, **corrects the 2026-10-05 entry**): JLC engineering,
  looking at the physical TJ-S1706 parts, reports that the lens is on the
  side where — with the lens toward the board edge — the CATHODE sits on our
  resistor pad. Our footprint therefore pairs "correct polarity" with "lens
  inward". v1's "rotation restores polarity AND emit direction" was an
  unverified inference (only polarity/lighting was checked). Rev B is
  assembled with correct polarity, lens inward (owner decision). **Next
  revision must fix it:** check lens vs cathode mark on the vendor drawing,
  then swap the footprint pad numbering (resistor to the other pad) or pick a
  matching side-view LED. Rule: for directional parts, verify polarity and
  emit direction TOGETHER against the tape/vendor drawing before layout.
