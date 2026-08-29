"""Embed the current GLB into the self-contained 3D viewer (docs/3d/).
Run after `kicad-cli pcb export glb` (see Makefile `3d` target)."""
import base64
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
ROOT = HERE.parent
glb = base64.b64encode(
    (HERE / "build" / "esp32_m2_companion.glb").read_bytes()).decode()
tpl = (HERE / "tools" / "viewer_template.html").read_text()
marker = '<script type="text/plain" id="glb">'
i = tpl.index(marker) + len(marker)
out = ROOT / "docs" / "3d" / "viewer.html"
out.write_text(tpl[:i] + glb + tpl[i:])
print("wrote", out)
