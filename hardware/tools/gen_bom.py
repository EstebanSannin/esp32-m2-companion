"""Generate BOM (markdown for review + JLCPCB CSV) from the SKiDL circuit."""

import csv
from collections import defaultdict

import builtins


def _rows():
    groups = defaultdict(list)
    for part in builtins.default_circuit.parts:  # skidl-injected global
        jlc = part.fields.get("JLC", "")
        if jlc == "PCB":       # edge fingers / test points: PCB features
            continue
        if getattr(part, "do_not_populate", False) and "DNP" not in part.fields:
            part.fields["DNP"] = "DNP"   # never leak DNP parts into bom.csv
        key = (part.value_str if hasattr(part, "value_str") else str(part.value),
               part.footprint, part.fields.get("LCSC", ""),
               part.fields.get("MPN", ""), jlc,
               part.fields.get("DNP", ""))
        groups[key].append(part.ref)
    for (value, fp, lcsc, mpn, jlc, dnp), refs in sorted(
            groups.items(), key=lambda kv: sorted(kv[1])[0]):
        yield {
            "refs": ",".join(sorted(refs)), "qty": len(refs), "value": value,
            "mpn": mpn, "footprint": fp, "lcsc": lcsc, "jlc": jlc, "dnp": dnp,
        }


def write_bom(outdir):
    rows = list(_rows())
    with open(outdir / "bom.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
        for r in rows:
            if r["dnp"]:
                continue
            w.writerow([r["value"], r["refs"],
                        r["footprint"].split(":")[-1], r["lcsc"]])
    with open(outdir / "bom.md", "w") as f:
        f.write("# BOM — esp32-m2-companion (generated, do not edit)\n\n")
        f.write("| Refs | Qty | Value / MPN | LCSC | JLC status | DNP |\n")
        f.write("|---|---|---|---|---|---|\n")
        for r in rows:
            f.write(f"| {r['refs']} | {r['qty']} | {r['value']} / {r['mpn']} "
                    f"| {r['lcsc']} | {r['jlc']} | {r['dnp'] or ''} |\n")
    ext = [r for r in rows if r["jlc"] == "Extended" and not r["dnp"]]
    print(f"BOM: {len(rows)} lines, {len(ext)} Extended:")
    for r in ext:
        print(f"  {r['refs']}: {r['mpn']} ({r['lcsc']})")
