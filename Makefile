# esp32-m2-companion — top-level targets (SPEC ground rule 6)

HW := hardware
UV := cd $(HW) && uv run

.PHONY: check netlist bom sch svg render datasheet 3d clean

# ERC + netlist + BOM: run after every schematic-source change.
check:
	$(UV) python design.py

# Human-readable KiCad schematic (.kicad_sch + PDF with title block).
sch:
	$(UV) python tools/gen_sch.py

# Auxiliary per-block SVG renders (netlistsvg; less readable than make sch).
svg:
	$(UV) python tools/gen_svg.py

# Product datasheet (DATASHEET.md) with live pin tables from the design.
datasheet:
	$(UV) python tools/gen_datasheet.py

# 3D renders for the README (docs/img/, committed).
KCLI := $(HOME)/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli
render:
	$(KCLI) pcb render --rotate "-35,20,30" --zoom 0.85 --quality high --width 1600 --height 1200 --output docs/img/board_iso.png $(HW)/kicad/esp32_m2_companion.kicad_pcb
	$(KCLI) pcb render --side top --quality high --width 1200 --height 1600 --output docs/img/board_top.png $(HW)/kicad/esp32_m2_companion.kicad_pcb
	$(KCLI) pcb render --side bottom --quality high --width 1200 --height 1600 --output docs/img/board_bottom.png $(HW)/kicad/esp32_m2_companion.kicad_pcb

# 3D package for the repo: GLB + STEP + self-contained HTML viewer.
3d:
	KICAD9_3DMODEL_DIR=$(HOME)/Applications/KiCad/KiCad.app/Contents/SharedSupport/3dmodels $(KCLI) pcb export glb --subst-models --include-tracks --include-zones --include-silkscreen --include-soldermask --output $(HW)/build/esp32_m2_companion.glb $(HW)/kicad/esp32_m2_companion.kicad_pcb
	$(KCLI) pcb export step --subst-models --output docs/3d/esp32_m2_companion.step $(HW)/kicad/esp32_m2_companion.kicad_pcb
	cp $(HW)/build/esp32_m2_companion.glb docs/3d/
	$(UV) python tools/gen_3d.py

clean:
	rm -rf $(HW)/build
