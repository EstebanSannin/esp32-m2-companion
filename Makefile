# esp32-m2-companion — top-level targets (SPEC ground rule 6)

HW := hardware
UV := cd $(HW) && uv run

.PHONY: check netlist bom sch svg clean

# ERC + netlist + BOM: run after every schematic-source change.
check:
	$(UV) python design.py

# Human-readable KiCad schematic (.kicad_sch + PDF with title block).
sch:
	$(UV) python tools/gen_sch.py

# Auxiliary per-block SVG renders (netlistsvg; less readable than make sch).
svg:
	$(UV) python tools/gen_svg.py

clean:
	rm -rf $(HW)/build
