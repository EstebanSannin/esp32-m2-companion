# esp32-m2-companion — top-level targets (SPEC ground rule 6)

HW := hardware
UV := cd $(HW) && uv run

.PHONY: check netlist bom svg clean

# ERC + netlist + BOM: run after every schematic-source change.
check:
	$(UV) python design.py

# Schematic-style SVG/PDF render for human review (requires netlistsvg).
svg:
	$(UV) python tools/gen_svg.py

clean:
	rm -rf $(HW)/build
