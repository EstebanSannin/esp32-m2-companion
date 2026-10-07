"""v2 GATE V3: convert the rev-B 4-layer board to 6 layers (ADR 0008).

JLC06081H-2116 (v2/research/jlc_6l_stackup.md):
  L1 F.Cu  SIG   | 2116 prepreg 0.1164
  L2 In1   GND   | core 0.13
  L3 In2   SIG   | 7628 prepreg 0.2028
  L4 In3   SIG   | core 0.13
  L5 In4   PWR   | 2116 prepreg 0.1164
  L6 B.Cu  SIG
Rev B used In2 as the +3V3 plane (and routed a few tracks there): every
item on In2 moves to In4, leaving In2/In3 free for v2 signals.
Idempotent: refuses to run twice.
"""
import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "tools"))
PCB = HERE / "kicad" / "esp32_m2_companion.kicad_pcb"


def main():
    b = pcbnew.LoadBoard(str(PCB))
    if b.GetCopperLayerCount() == 6:
        print("already 6 layers - nothing to do")
        return
    assert b.GetCopperLayerCount() == 4
    moved_t = moved_z = 0
    for t in b.GetTracks():
        if t.Type() != pcbnew.PCB_VIA_T and t.GetLayer() == pcbnew.In2_Cu:
            t.SetLayer(pcbnew.In4_Cu)
            moved_t += 1
    for z in b.Zones():
        ls = z.GetLayerSet()
        if ls.Contains(pcbnew.In2_Cu) and not z.GetIsRuleArea():
            assert z.GetLayerSet().CuStack().size() == 1, "multi-layer copper zone on In2"
            z.SetLayer(pcbnew.In4_Cu)
            if z.GetZoneName() == "PWR_L3":
                z.SetZoneName("PWR_L5")
            moved_z += 1
    b.SetCopperLayerCount(6)
    # rule areas that covered all 4 copper layers must also cover In3/In4
    for z in b.Zones():
        if z.GetIsRuleArea():
            ls = z.GetLayerSet()
            if ls.Contains(pcbnew.In1_Cu) and ls.Contains(pcbnew.In2_Cu):
                ls.AddLayer(pcbnew.In3_Cu)
                ls.AddLayer(pcbnew.In4_Cu)
                z.SetLayerSet(ls)
    pcbnew.SaveBoard(str(PCB), b)
    print(f"6 layers; moved In2->In4: {moved_t} tracks, {moved_z} zones")


if __name__ == "__main__":
    from kicad_exit import run
    run(main)
