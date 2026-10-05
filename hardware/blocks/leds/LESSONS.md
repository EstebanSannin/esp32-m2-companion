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
