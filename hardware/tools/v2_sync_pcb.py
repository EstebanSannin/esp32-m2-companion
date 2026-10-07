"""v2: sync the rev-B board with the v2 netlist WITHOUT destroying the rev-B
routing (gen_pcb.py would rebuild from scratch). KiCad 9 has no headless
"Update PCB from netlist", so this does the equivalent:

  stage 1 (separate process - never keep using a board after Remove()):
      remove footprints whose footprint id changed (FB1 0805 -> 0603)
  stage 2: add footprints present in the netlist but not on the board
      (parked to the right of the card, x > 115 mm), then assign EVERY pad's
      net from the netlist (pads absent from the netlist -> no net).

Run with KiCad's bundled python from hardware/:
  $KPY tools/v2_sync_pcb.py stage1
  $KPY tools/v2_sync_pcb.py stage2
Then `$KPY tools/v2_sync_pcb.py report` lists unplaced parts / changes.
"""

import os
import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent.parent
# sexpdata is pure python: borrow it from the uv venv (KiCad's python lacks it)
sys.path.extend(str(p) for p in (HERE / ".venv" / "lib").glob("python3*/site-packages"))
import sexpdata  # noqa: E402
from sexpdata import Symbol  # noqa: E402

sys.path.insert(0, str(HERE / "tools"))
PCB = HERE / "kicad" / "esp32_m2_companion.kicad_pcb"
NET = HERE / "build" / "esp32_m2_companion.net"
STOCK = os.path.expanduser(
    "~/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints")
LIBS = {"esp32_m2_companion": HERE / "kicad" / "footprints.pretty",
        "esp32m2": HERE / "kicad" / "esp32m2.pretty"}
PARK_X, PARK_Y0 = 118.0, 108.0   # parking column right of the card


def netlist():
    data = sexpdata.loads(NET.read_text())
    comps, pins = {}, {}
    for node in data:
        if not (isinstance(node, list) and node):
            continue
        if node[0] == Symbol("components"):
            for c in node[1:]:
                d = {}
                for item in c[1:]:
                    if isinstance(item, list) and len(item) >= 2:
                        d[str(item[0])] = item[1]
                comps[str(d["ref"])] = (str(d.get("value", "")),
                                        str(d.get("footprint", "")))
        if node[0] == Symbol("nets"):
            for net in node[1:]:
                name = None
                for item in net[1:]:
                    if item[0] == Symbol("name"):
                        name = str(item[1])
                    elif item[0] == Symbol("node"):
                        d = {str(x[0]): str(x[1]) for x in item[1:]}
                        pins[(d["ref"], d["pin"])] = name
    return comps, pins


def fpid_str(fp):
    f = fp.GetFPID()
    return f"{f.GetLibNickname()}:{f.GetLibItemName()}"


def load_fp(fpid):
    lib, name = fpid.split(":", 1)
    path = LIBS.get(lib) or Path(STOCK) / f"{lib}.pretty"
    fp = pcbnew.FootprintLoad(str(path), name)
    assert fp is not None, fpid
    fp.SetFPID(pcbnew.LIB_ID(lib, name))   # keep the library nickname (DRC parity)
    return fp


def stage1():
    comps, _ = netlist()
    b = pcbnew.LoadBoard(str(PCB))
    gone = []
    for fp in list(b.GetFootprints()):
        ref = fp.GetReference()
        if ref not in comps:
            gone.append(f"{ref}: removed from netlist")
            b.Remove(fp)
        elif comps[ref][1] and fpid_str(fp) != comps[ref][1]:
            gone.append(f"{ref}: {fpid_str(fp)} -> {comps[ref][1]}")
            b.Remove(fp)
    pcbnew.SaveBoard(str(PCB), b)
    print("stage1 removed (footprint changed):", gone or "none")


def stage2():
    comps, pins = netlist()
    b = pcbnew.LoadBoard(str(PCB))
    on_board = {fp.GetReference(): fp for fp in b.GetFootprints()}
    added, y = [], PARK_Y0
    for ref, (value, fpid) in sorted(comps.items()):
        if ref in on_board or not fpid:
            continue
        fp = load_fp(fpid)
        fp.SetReference(ref)
        fp.SetValue(value)
        b.Add(fp)
        fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(PARK_X), pcbnew.FromMM(y)))
        y += 3.0
        on_board[ref] = fp
        added.append(ref)
    # nets
    netinfo = {}

    def net(name):
        if name not in netinfo:
            ni = b.FindNet(name)
            if ni is None:
                ni = pcbnew.NETINFO_ITEM(b, name)
                b.Add(ni)
            netinfo[name] = ni
        return netinfo[name]

    changed = []
    for ref, fp in on_board.items():
        if ref not in comps:
            continue
        for p in fp.Pads():
            num = p.GetNumber()
            if not num:
                continue            # paste-only apertures
            want = pins.get((ref, num))
            have = p.GetNetname()
            if want is None:
                if have:
                    changed.append(f"{ref}.{num}: {have} -> (none)")
                    p.SetNetCode(0)
                continue
            if have != want:
                changed.append(f"{ref}.{num}: {have or '(none)'} -> {want}")
                p.SetNet(net(want))
    extra = sorted(set(on_board) - set(comps))
    pcbnew.SaveBoard(str(PCB), b)
    print(f"stage2 added {len(added)} footprints: {' '.join(added)}")
    print(f"pad net changes ({len(changed)}):")
    for c in changed:
        print("  ", c)
    print("on board but not in netlist:", extra or "none")


if __name__ == "__main__":
    from kicad_exit import run
    run({"stage1": stage1, "stage2": stage2}[sys.argv[1]])
