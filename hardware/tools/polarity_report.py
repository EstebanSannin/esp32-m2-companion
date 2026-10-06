"""Polarity / pin-1 report for every polarized placed part (rev B guard).

Run with KiCad's python (needs pcbnew); gen_fab.py calls it:
  .../python3 tools/polarity_report.py <out_dir>

Asserts, per LED: the anode pad (KiCad Device:LED pin 2 = A) shares its net
with a series resistor AND is the LED pad physically nearer that resistor
pad - i.e. "+" is on the resistor-side pad by design. Rev A's footprint
already satisfied this; the reversal entered at JLC, which is why the
report also prints where "+" / pin 1 must appear in the JLC preview.

Writes <out_dir>/polarity.json and <out_dir>/polarity_checklist.md.

Board directions (invariant under the bottom-side mirror in JLC's viewer):
  N = toward the top / screw-notch edge (smaller y)
  S = toward the M.2 gold fingers (larger y)
  E/W are given too, but the bottom-side preview MIRRORS them.
"""

import json
import math
import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent.parent
PCB = HERE / "kicad" / "esp32_m2_companion.kicad_pcb"

# ref prefix / footprint -> what pin 1 means
PIN1_MEANING = {
    "D1": "pin 1 = cathode-1 (BAT54A common-anode SOT-23: pins 1,2 = K, 3 = A)",
    "D2": "pin 1 = cathode-1 (BAT54A common-anode SOT-23: pins 1,2 = K, 3 = A)",
    "U1": "pin 1 = I/O1 (USBLC6-2SC6; package pin-1 mark)",
    "J3": "pin 1 = GND (Qwiic order GND, 3V3, SDA, SCL)",
    "J4": "pin 1 = TXD0",
    "U2": "module pin 1 = GND (antenna end toward N)",
}


def mm(v):
    return v / 1e6


def direction(dx, dy):
    parts = []
    if abs(dy) > 0.05:
        parts.append("N" if dy < 0 else "S")
    if abs(dx) > 0.05:
        parts.append("W" if dx < 0 else "E")
    return "".join(parts) or "centre"


def main(out):
    out.mkdir(parents=True, exist_ok=True)
    b = pcbnew.LoadBoard(str(PCB))
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    rows, errors = [], []

    for ref, fp in sorted(fps.items()):
        c = fp.GetPosition()
        side = "bottom" if fp.IsFlipped() else "top"
        pads = {p.GetNumber(): p for p in fp.Pads() if p.GetNumber()}
        if "LED" in fp.GetFPIDAsString():
            a, k = pads["2"], pads["1"]
            anet = a.GetNetname()
            # series resistor pad on the anode net
            rp = [(r, p) for r, f in fps.items() if r.startswith("R")
                  for p in f.Pads() if p.GetNetname() == anet]
            if len(rp) != 1:
                errors.append(f"{ref}: anode net {anet} has {len(rp)} "
                              f"resistor pads (want exactly 1)")
                continue
            rref, rpad = rp[0]
            da = (a.GetPosition() - rpad.GetPosition()).EuclideanNorm()
            dk = (k.GetPosition() - rpad.GetPosition()).EuclideanNorm()
            if not da < dk:
                errors.append(f"{ref}: anode pad is NOT the resistor-side pad "
                              f"({mm(da):.2f} mm vs cathode {mm(dk):.2f} mm)")
            ap = a.GetPosition()
            rows.append({
                "ref": ref, "kind": "LED", "value": fp.GetValue(), "side": side,
                "rot": fp.GetOrientationDegrees(),
                "plus_pad": "2 (anode)",
                "plus_xy": [round(mm(ap.x), 3), round(mm(ap.y), 3)],
                "plus_dir": direction(mm(ap.x - c.x), mm(ap.y - c.y)),
                "plus_net": anet,
                "resistor_side": f"{rref}.{rpad.GetNumber()}",
                "minus_net": k.GetNetname(),
                "check": (f"'+' (anode) on the {direction(mm(ap.x-c.x), mm(ap.y-c.y))[0]} "
                          f"pad = the one level with {rref}.{rpad.GetNumber()} "
                          f"(net {anet}); cathode mark toward "
                          f"{'S' if ap.y < c.y else 'N'}"),
            })
        elif ref in PIN1_MEANING:
            p1 = pads.get("1")
            pp = p1.GetPosition()
            rows.append({
                "ref": ref, "kind": "pin1", "value": fp.GetValue(), "side": side,
                "rot": fp.GetOrientationDegrees(),
                "plus_pad": "1", "plus_xy": [round(mm(pp.x), 3), round(mm(pp.y), 3)],
                "plus_dir": direction(mm(pp.x - c.x), mm(pp.y - c.y)),
                "plus_net": p1.GetNetname(),
                "check": f"{PIN1_MEANING[ref]}; pin 1 at the "
                         f"{direction(mm(pp.x-c.x), mm(pp.y-c.y))} corner, net "
                         f"{p1.GetNetname() or '(no net)'}",
            })

    json.dump({"parts": rows, "errors": errors},
              open(out / "polarity.json", "w"), indent=1)
    with open(out / "polarity_checklist.md", "w") as f:
        f.write("# Polarity / pin-1 checklist (generated - verify each row "
                "against the JLC placement preview BEFORE ordering)\n\n"
                "N = toward the screw-notch edge, S = toward the gold fingers. "
                "Bottom-side previews are mirrored: trust N/S, not E/W.\n\n"
                "| Ref | Side | Value | Must see in preview | Net | Preview OK? |\n"
                "|---|---|---|---|---|---|\n")
        for r in rows:
            f.write(f"| {r['ref']} | {r['side']} | {r['value']} | {r['check']} "
                    f"| {r['plus_net']} | [ ] |\n")
    for e in errors:
        print("POLARITY ERROR:", e)
    print(f"polarity: {len(rows)} parts, {len(errors)} errors -> {out}")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    from kicad_exit import run
    run(main, Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "build" / "fab")
