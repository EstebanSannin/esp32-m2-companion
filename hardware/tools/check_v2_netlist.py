"""GATE V2 netlist check: the generated KiCad netlist must implement the
v2 contract pin-by-pin (docs/carrier-interface.md, docs/pinmap.md §6,
docs/v2-gate-v1.md §1). Run after `make check`:

    uv run python tools/check_v2_netlist.py

Fails (exit 1) on the first mismatch list; prints PASS otherwise.
"""

import sys
from pathlib import Path

import sexpdata
from sexpdata import Symbol

import os
NET = Path(os.environ.get("V2_NETLIST") or Path(__file__).resolve().parent.parent / "build" / "esp32_m2_companion.net")

# EXP index -> (M.2 pin, WROOM-1 module pad, MCU net name)  [pinmap §6.2]
EXP = [(30, 32, "IO39"), (32, 34, "IO41"), (34, 39, "IO1"), (36, 38, "IO2"),
       (40, 11, "IO18"), (59, 4, "IO4"), (60, 5, "IO5"), (61, 6, "IO6"),
       (62, 7, "IO7"), (63, 8, "IO15"), (64, 9, "IO16"), (65, 10, "IO17")]
# TMUX1511 channel k -> (SEL, S, D) pin numbers (tmux1511.pdf Table 4-1, UQFN)
TMUX_CH = [(1, 2, 3), (4, 5, 6), (11, 10, 9), (15, 14, 13)]


def load():
    data = sexpdata.loads(NET.read_text())
    nets = {}
    for node in data:
        if isinstance(node, list) and node and node[0] == Symbol("nets"):
            for net in node[1:]:
                name, nodes = None, []
                for item in net[1:]:
                    if item[0] == Symbol("name"):
                        name = str(item[1])
                    elif item[0] == Symbol("node"):
                        d = {str(x[0]): str(x[1]) for x in item[1:]}
                        nodes.append((d["ref"], d["pin"]))
                nets[name] = set(nodes)
    vals = {}
    for node in data:
        if isinstance(node, list) and node and node[0] == Symbol("components"):
            for comp in node[1:]:
                d = {str(x[0]): x[1] for x in comp[1:] if isinstance(x, list) and len(x) > 1}
                vals[str(d.get("ref"))] = str(d.get("value"))
    pin2net = {}
    for name, nodes in nets.items():
        for rp in nodes:
            pin2net[rp] = name
    return nets, pin2net, vals


def main():
    nets, pin2net, vals = load()
    errs = []

    def on(ref, pin, net):
        got = pin2net.get((ref, str(pin)))
        if got != net:
            errs.append(f"{ref}.{pin}: expected {net!r}, got {got!r}")

    # CONFIG state 6 + signature
    on("J1", 21, "GND")
    on("J1", 69, "GND")
    on("J1", 75, "CONFIG_2")
    on("J1", 1, "CONFIG_3")

    # expansion bus, end to end
    for i, (m2, pad, io) in enumerate(EXP):
        u = f"U{3 + i // 4}"
        sel, s, d = TMUX_CH[i % 4]
        on("J1", m2, f"EXP_{i}")
        on(u, d, f"EXP_{i}")
        on(u, s, f"EXP_{i}_S")
        on(u, sel, "EXP_OE")
        rn, k = f"RN{1 + i // 4}", i % 4 + 1
        on(rn, k, io)              # Rk a
        on(rn, 9 - k, f"EXP_{i}_S")  # Rk b
        on("U2", pad, io)
    for u in ("U3", "U4", "U5"):
        on(u, 16, "+3V3")
        on(u, 8, "GND")
    # the edge-side EXP nets must touch ONLY the finger and the switch
    for i in range(12):
        refs = {r for r, _ in nets.get(f"EXP_{i}", set())}
        if refs - {"J1", f"U{3 + i // 4}"}:
            errs.append(f"EXP_{i} edge net touches {sorted(refs)} "
                        "(must be J1 + switch only: high-Z promise)")
    # I2C pull-ups on the MCU side of the switch
    for i in (0, 1):
        refs = {r for r, _ in nets[f"EXP_{i}_S"]}
        if not ({"R20", "R21"} & refs):
            errs.append(f"EXP_{i}_S has no I2C pull-up")

    # carrier detect: Q1 (S1 1, G1 2, D2 3, S2 4, G2 5, D1 6)
    on("Q1", 2, "CFG2_G")
    on("Q1", 5, "CFG3_G")
    on("Q1", 6, "EXP_OE")
    on("Q1", 3, "EXP_OE")
    on("Q1", 1, "GND")
    on("Q1", 4, "GND")
    # IO38 = firmware hold-off: gate of Q3b, whose drain holds EXP_OE low
    # (RC1 review); IO38 must NOT sit on EXP_OE itself any more
    on("U2", 31, "IO38")
    on("Q3", 5, "IO38")
    on("Q3", 3, "EXP_OE")
    on("Q3", 4, "GND")
    # the hold-off default: R35 pull-up keeps IO38 high (bus off) in reset
    on("R35", 1, "+3V3")
    on("R35", 2, "IO38")

    def val(ref, want):
        if not vals.get(ref, "").startswith(want):
            errs.append(f"{ref}: expected value {want!r}, got {vals.get(ref)!r}")

    # RC1 values (review): W_DISABLE2# pull-up per M.2 100-200k; hold-off
    # pull-up; EXP_OE RC; eFuse DVDT / OVLO filter (<= 100 pF, power-rc1-1)
    # / OUT cap
    val("R35", "100k")
    val("R29", "100k")
    val("R26", "10k")
    val("C13", "1uF")
    val("C15", "2.2nF")
    val("C16", "100pF")
    val("C17", "1uF")
    on("C15", 1, "EFUSE_DVDT")
    on("C16", 1, "EFUSE_OVLO")
    on("C17", 1, "+3V3_EFUSE")

    # host cells: Q2 (LED_1#, WAKE), Q3 (W_DISABLE2#)
    on("Q2", 2, "IO42")
    on("Q2", 6, "LED_1_n")
    on("Q2", 5, "IO47")
    on("Q2", 3, "WAKE_ON_WWAN_n")
    on("J1", 10, "LED_1_n")
    on("J1", 23, "WAKE_ON_WWAN_n")
    on("U2", 35, "IO42")
    on("U2", 24, "IO47")
    on("Q3", 2, "W_DISABLE2_n")
    on("Q3", 6, "IO40")
    on("J1", 26, "W_DISABLE2_n")
    on("U2", 33, "IO40")

    # eFuse (tps25947.pdf Table 5-1)
    on("U6", 5, "+3V3_M2")
    on("U6", 6, "+3V3_EFUSE")
    on("U6", 8, "GND")
    on("U6", 2, "EFUSE_OVLO")
    on("U6", 1, "EFUSE_EN")
    on("U6", 9, "EFUSE_ILM")
    on("FB1", 1, "+3V3_EFUSE")
    on("FB1", 2, "+3V3")
    on("U2", 2, "+3V3")
    for p in (2, 4, 70, 72, 74):
        on("J1", p, "+3V3_M2")

    if errs:
        print("GATE V2 netlist check FAILED:")
        for e in errs:
            print("  -", e)
        sys.exit(1)
    print(f"GATE V2 netlist check PASS ({len(nets)} nets)")


if __name__ == "__main__":
    main()
