"""DRC gate: fail on ANY violation or unconnected item not explicitly excluded.

Run: uv run python tools/check_drc.py   (or `make drc`)
Report: hardware/build/drc.json

"DRC clean" means zero entries left after EXCLUDE. Every exclusion needs a
reason; add sparingly. v1 shipped with 57 unexamined warnings plus a
board-wide edge-clearance waiver that hid a real fab defect.
"""

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
PCB = HERE / "kicad" / "esp32_m2_companion.kicad_pcb"
KCLI = Path.home() / "Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
OUT = HERE / "build" / "drc.json"

# (violation type, substring of any item description) -> reason
EXCLUDE = {
    ("items_not_allowed", "NPTH pad of J1"):
        "M.2 screw notch (top-edge centre, fixed by M.2 mechanical spec) lies "
        "inside U2's antenna keep-out. Rev B: NPTH, zero copper - only the "
        "unavoidable drilled notch remains (standoff/screw = accepted risk R3).",
    ("lib_footprint_mismatch", "Footprint U2"):
        "Serialization-only: board U2 vs esp32m2.pretty (KiCad-6 format) "
        "compared by script 2026-10-06 - 62 pads (pos/size/drill/layers/"
        "zone-connect), 24 graphics, keep-out zone, 3D model all identical.",
}


def excluded(v):
    for (typ, sub), _reason in EXCLUDE.items():
        if v["type"] == typ and any(sub in i["description"] for i in v["items"]):
            return True
    return False


def main():
    OUT.parent.mkdir(exist_ok=True)
    subprocess.run([str(KCLI), "pcb", "drc", "--severity-all", "--format",
                    "json", "--output", str(OUT), str(PCB)],
                   check=True, capture_output=True, text=True)
    d = json.load(open(OUT))
    bad = [v for v in d["violations"] if not excluded(v)]
    unconn = d.get("unconnected_items", [])
    for v in bad + unconn:
        items = " || ".join(i["description"][:70] for i in v["items"])
        print(f"{v.get('severity', 'error'):7} {v['type']}: {items}")
    n_ex = len(d["violations"]) - len(bad)
    print(f"DRC: {len(bad)} violations, {len(unconn)} unconnected, "
          f"{n_ex} excluded")
    sys.exit(1 if bad or unconn else 0)


if __name__ == "__main__":
    main()
