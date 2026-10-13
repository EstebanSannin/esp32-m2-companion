# esp32-m2-companion — top-level targets (SPEC ground rule 6)

HW := hardware
UV := cd $(HW) && uv run

.PHONY: check drc netlist bom sch svg render layers views datasheet 3d fab drawings labels jlc-check clean

# ERC + netlist + BOM: run after every schematic-source change.
# v2: the netlist must also implement the v2 contract pin-by-pin.
check:
	$(UV) python design.py
	$(UV) python tools/check_v2_netlist.py

# DRC gate: fails on any non-excluded violation (tools/check_drc.py).
drc:
	$(UV) python tools/check_drc.py

# Human-readable KiCad schematic (.kicad_sch + PDF with title block).
sch:
	$(UV) python tools/gen_sch.py

# Auxiliary per-block SVG renders (netlistsvg; less readable than make sch).
svg:
	$(UV) python tools/gen_svg.py

# Product datasheet (DATASHEET.md) with live pin tables from the design.
datasheet:
	$(UV) python tools/gen_datasheet.py

# Assembly (top/bottom, pad numbers, DNP crossed) + drill-map PDFs -> docs/review/.
drawings:
	$(UV) python tools/gen_drawings.py

# Label inventory for the owner's label review -> docs/review/ (needs make check).
KPY := $(HOME)/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3
labels:
	cd $(HW) && $(KPY) tools/polarity_report.py build/fab && $(KPY) tools/label_inventory.py
	cp $(HW)/build/esp32_m2_companion_schematic.pdf docs/review/v2_reva_schematic.pdf

# JLCPCB fab package: gerbers.zip + BOM + CPL (-> fab/).
fab:
	$(UV) python tools/gen_fab.py

# Compare JLC's processed production files with fab/ (before confirming them).
# Usage: make jlc-check JLC=~/Downloads/<order>_gerbers_Y6.zip
jlc-check:
	@test -n "$(JLC)" || { echo "usage: make jlc-check JLC=<jlc production zip>"; exit 2; }
	cd $(HW) && uv run --no-project --python 3.12 --with gerbonara==1.6.3 --with numpy --with pillow python tools/check_jlc_production.py $(JLC)

# 3D renders for the README (docs/img/, committed).
KCLI := $(HOME)/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli
render:
	$(KCLI) pcb render --rotate "-35,20,30" --zoom 0.85 --quality high --width 1600 --height 1200 --output docs/img/board_iso.png $(HW)/kicad/esp32_m2_companion.kicad_pcb
	$(KCLI) pcb render --side top --quality high --width 1200 --height 1600 --output docs/img/board_top.png $(HW)/kicad/esp32_m2_companion.kicad_pcb
	$(KCLI) pcb render --side bottom --quality high --width 1200 --height 1600 --output docs/img/board_bottom.png $(HW)/kicad/esp32_m2_companion.kicad_pcb

# Datasheet figures: labeled top/bottom views + mechanical drawing (docs/img/).
views:
	cd $(HW) && $(KPY) tools/gen_views.py

# Per-layer copper views for docs/stackup.md (docs/img/layers/).
# v2 6-layer JLC06081H-2116 (ADR 0008)
LAYERS := 1_top_signal:F.Cu 2_gnd_plane:In1.Cu 3_inner_signal:In2.Cu 4_inner_signal:In3.Cu 5_pwr_plane:In4.Cu 6_bottom_signal:B.Cu
layers:
	@for e in $(LAYERS); do n=$${e%%:*}; l=$${e##*:}; \
	  $(KCLI) pcb export svg --layers $$l,Edge.Cuts --mode-single --exclude-drawing-sheet --page-size-mode 2 \
	    --output $(HW)/build/$$n.svg $(HW)/kicad/esp32_m2_companion.kicad_pcb >/dev/null && \
	  rsvg-convert -w 500 -b white $(HW)/build/$$n.svg -o docs/img/layers/$$n.png && echo "wrote docs/img/layers/$$n.png"; done

# 3D package for the repo: GLB + STEP + self-contained HTML viewer.
3d:
	KICAD9_3DMODEL_DIR=$(HOME)/Applications/KiCad/KiCad.app/Contents/SharedSupport/3dmodels $(KCLI) pcb export glb --subst-models --include-tracks --include-zones --include-silkscreen --include-soldermask --output $(HW)/build/esp32_m2_companion.glb $(HW)/kicad/esp32_m2_companion.kicad_pcb
	$(KCLI) pcb export step --subst-models --output docs/3d/esp32_m2_companion.step $(HW)/kicad/esp32_m2_companion.kicad_pcb
	cp $(HW)/build/esp32_m2_companion.glb docs/3d/
	$(UV) python tools/gen_3d.py
	$(UV) python -c "import trimesh; s=trimesh.load('build/esp32_m2_companion.glb'); trimesh.util.concatenate(list(s.geometry.values())).export('../docs/3d/esp32_m2_companion.stl')"

clean:
	rm -rf $(HW)/build
