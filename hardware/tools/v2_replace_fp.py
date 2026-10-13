"""Replace placed footprint instances with the current library version
(KiCad's "update footprint from library", headless), keeping position,
rotation, side, reference/value (+ their positions), fields, the schematic
link, and pad nets by PAD NUMBER (so a renumbered footprint takes its nets
from the numbers, not the old copper positions - re-route afterwards).

Two processes (SWIG Remove() rule):
  $KPY tools/v2_replace_fp.py save  D3,D4     # pose + fields -> build/replace_fp.json, remove
  $KPY tools/v2_replace_fp.py add             # load from the project library, restore
"""
import json
import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "tools"))
PCB = HERE / "kicad" / "esp32_m2_companion.kicad_pcb"
LIBS = {"esp32_m2_companion": HERE / "kicad" / "footprints.pretty",
        "esp32m2": HERE / "kicad" / "esp32m2.pretty"}
STATE = HERE / "build" / "replace_fp.json"


def main():
    b = pcbnew.LoadBoard(str(PCB))
    if sys.argv[1] == "save":
        refs = sys.argv[2].split(",")
        out = []
        for r in refs:
            fp = b.FindFootprintByReference(r)
            nets = {}
            for p in fp.Pads():
                if p.GetNumber():
                    nets[p.GetNumber()] = p.GetNetname()
            out.append({
                "ref": r, "fpid": fp.GetFPIDAsString(),
                "x": fp.GetX(), "y": fp.GetY(), "rot": fp.GetOrientationDegrees(),
                "flipped": fp.IsFlipped(), "value": fp.GetValue(),
                "path": fp.GetPath().AsString(),
                "ref_pos": [fp.Reference().GetX(), fp.Reference().GetY()],
                "ref_angle": fp.Reference().GetTextAngleDegrees(),
                "ref_visible": fp.Reference().IsVisible(),
                "ref_size": [fp.Reference().GetTextWidth(), fp.Reference().GetTextHeight()],
                "ref_th": fp.Reference().GetTextThickness(),
                "fields": {f.GetName(): f.GetText() for f in fp.GetFields()
                           if f.GetName() not in ("Reference", "Value", "Footprint")},
                "nets_by_number_old": nets,
                "locked": fp.IsLocked(),
            })
        STATE.write_text(json.dumps(out, indent=1))
        for r in refs:
            b.Remove(b.FindFootprintByReference(r))
        pcbnew.SaveBoard(str(PCB), b)
        print(f"saved + removed: {refs} -> {STATE}")
        return
    st = json.loads(STATE.read_text())
    for e in st:
        lib, name = e["fpid"].split(":")
        fp = pcbnew.FootprintLoad(str(LIBS[lib]), name)
        fp.SetFPIDAsString(e["fpid"])
        fp.SetReference(e["ref"]); fp.SetValue(e["value"])
        b.Add(fp)
        if e["flipped"]:
            fp.Flip(fp.GetPosition(), False)
        fp.SetPosition(pcbnew.VECTOR2I(e["x"], e["y"]))
        fp.SetOrientationDegrees(e["rot"])
        fp.SetPath(pcbnew.KIID_PATH(e["path"]))
        for k, v in e["fields"].items():
            fp.SetField(k, v)
        r = fp.Reference()
        r.SetPosition(pcbnew.VECTOR2I(*e["ref_pos"])); r.SetTextAngleDegrees(e["ref_angle"])
        r.SetVisible(e["ref_visible"]); r.SetTextSize(pcbnew.VECTOR2I(*e["ref_size"]))
        r.SetTextThickness(e["ref_th"])
        fp.SetLocked(e["locked"])
        # nets come from the netlist meaning of each pin number (pin 1 = K,
        # pin 2 = A for Device:LED), which is what the old pads carried
        for p in fp.Pads():
            n = e["nets_by_number_old"].get(p.GetNumber())
            if n:
                p.SetNet(b.FindNet(n))
        print(f"{e['ref']}: {e['fpid']} re-placed, pads " +
              ", ".join(f"{p.GetNumber()}@({pcbnew.ToMM(p.GetX()):.2f},{pcbnew.ToMM(p.GetY()):.2f})="
                        f"{p.GetNetname()}" for p in fp.Pads()))
    pcbnew.SaveBoard(str(PCB), b)


if __name__ == "__main__":
    from kicad_exit import run
    run(main)
