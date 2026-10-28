"""Generate the JLCPCB fab package: gerbers.zip + BOM + CPL.

Run: uv run python tools/gen_fab.py   (or `make fab`)
Outputs into hardware/build/fab/ and copies the 3 upload files to repo fab/.

CPL contains exactly the parts in the generated BOM (build/bom.csv, which
gen_bom already DNP-filters) - no hand-kept DNP list here (v1 had one;
PROCESS rule: DNP is enforced by the BOM generator, not per-tool lists).

Polarity guard (rev B, after the v1 LED reversal):
  - every placed part is either known non-polar (NONPOLAR) or has a
    JLC_ROT entry keyed by LCSC part: rotation offset added to KiCad's
    rotation + the date it was verified against a JLC placement preview;
  - tools/polarity_report.py asserts each LED anode is the resistor-side
    pad and writes polarity_checklist.md (what the preview must show);
  - exit status 2 = package written but ORDER BLOCKED: some JLC_ROT entry
    is not yet preview-verified for this revision.
"""

import csv
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
ROOT = HERE.parent
PCB = HERE / "kicad" / "esp32_m2_companion.kicad_pcb"
KCLI = Path.home() / ("Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli")
FAB = HERE / "build" / "fab"
GERB = FAB / "gerbers"

KPY = Path.home() / ("Applications/KiCad/KiCad.app/Contents/Frameworks/"
                     "Python.framework/Versions/3.9/bin/python3")

# Non-polar LCSC parts (R, C, ferrite): any rotation is electrically fine.
NONPOLAR = {"C45783", "C19702", "C14663", "C15849", "C1015", "C25804",
            "C23138", "C22775", "C21189",
            # v2.0 Rev A: 0402 resistors + FB1 ferrite
            "C25900", "C26083", "C25741", "C25890", "C852472", "C852832",
            "C14709",
            # v2.0 RC1: eFuse DVDT / OVLO / OUT capacitors
            "C1531", "C1523", "C52923"}

# LCSC part -> (degrees added to KiCad rotation, date it was confirmed in
# JLC engineering's FINAL DFM placement for this footprint or None, basis).
# Fill the date only after checking the final DFM against
# polarity_checklist.md (never by eye - the v1 LED trap).
JLC_ROT = {
    # Rev-B parts with an UNCHANGED footprint: offsets verified 2026-10-13
    # against JLC engineering's FINAL DFM placement (GATE B3, v1.0 Rev B). The
    # offset maps our footprint to JLC's library part, so it carries over to
    # v2.0 Rev A; the v2 final DFM still re-checks every row. The pre-order
    # preview is automatic and not authoritative - see fab/README.md.
    "C12743": (0, "2026-10-13", "BAT54A SOT-23: pin 1 correct in final DFM (Rev B)"),
    # U1 USBLC6 (bottom): Rev B went out at 0 and JLC engineering RE-ROTATED
    # it (at 0 the library rows cannot land on our columns) - the Rev B date
    # recorded JLC's correction, not a calibration (RC1 review dfm-4).
    "C7519": (270, None, "USBLC6-2SC6 (bottom): library = ours +90 -> bottom "
              "rule 90+180 = 270; Rev B was corrected by JLC at 0"),
    "C160390": (0, "2026-10-13", "JST SH-4 (J3): pin 1 correct in final DFM (Rev B)"),
    "C160394": (180, "2026-10-13", "JST SH-8 (J4): at +0 JLC's auto preview put "
                "pin 1 at the opposite end from J3; JLC engineering rotated it "
                "180 in the final DFM (pin 1 = TXD0 at the same end as J3 pin 1). "
                "Rev B was ordered at +0 and corrected by JLC"),
    "C2913204": (0, "2026-10-13", "WROOM-1 module: pin 1 NW, correct in final DFM (Rev B)"),
    # TJ-S1706 side-view LEDs: footprint pads RENUMBERED in v2 (GATE V3
    # amendment, 2026-10-13) to match the physical part: with the lens toward
    # the emit arrow (card edge), the cathode is the pad at +x. Rev B (+180,
    # old footprint) = correct polarity, lens inward; v1 (+0, old footprint)
    # = lens toward the edge, polarity reversed. With the renumbered footprint
    # +0 gives both - derived, NOT yet confirmed by JLC on this footprint.
    "C273616": (0, None, "TJ-S1706 green: renumbered footprint, +0 = lens to "
                "the card edge AND anode on the R3 pad; confirm BOTH in the final DFM"),
    "C273612": (0, None, "TJ-S1706 red: same as C273616 (R4 pad)"),
    # v2.0 Rev A, BOTTOM side. Rule (RC1 review dfm-1, the only model that
    # reproduces D1 at 0, v1 LEDs at +0 = polarity reversed and Rev B LEDs at
    # +180 = lens inward): JLC mirrors a bottom library part about the
    # VERTICAL axis while KiCad flips about the horizontal one, so
    #     bottom offset = (JLC library rotation vs our footprint) + 180.
    # Library rotations from the easyeda.com component API (pad coordinates).
    # The RSV / RPW / SOT-563 lands are 180-symmetric: a wrong offset seats
    # perfectly and swaps pins (U3-U5 GND<->VDD, U6 IN<->OUT), so the final DFM
    # must check pin 1 (silk dot) of U3-U6 and Q1-Q3 against
    # polarity_checklist.md; the order remark says "pin 1 per silk dot".
    "C3662799": (180, None, "TPS259470A RPW (bottom): library = ours (0) -> "
                 "0+180 = 180; was 0 (GATE V4) = IN/OUT swapped under the model"),
    "C2673275": (270, None, "TMUX1511 RSV (bottom): library = ours +90 -> "
                 "270; was 90 (GATE V4) = pin 1 in the opposite corner"),
    "C146449": (270, None, "SSM6N56FE SOT-563 (bottom): library = ours +90 -> "
                "270; was 90 (GATE V4) = Q-halves swapped"),
    "C86784": (270, None, "SI1024X SOT-563, approved 2nd source of C146449: "
               "same library orientation -> 270"),
    "C25498": (90, None, "4D02 array: JLC lib long axis horizontal, KiCad "
               "vertical; 180-symmetric (4 equal resistors), so only the 90 "
               "matters - pads must land"),
}

# inner copper In1..In4 = *.g1..*.g4 (v2 is 6 layers; rev B shipped only
# g1/g2 - a 6-layer zip from that list would silently lack In3/In4)
STD_GLOBS = ["*.gtl", "*.g1", "*.g2", "*.g3", "*.g4", "*.gbl", "*.gts", "*.gbs",
             "*.gto", "*.gbo", "*.gtp", "*.gbp", "*.gm1", "*.drl",
             "*.gbrjob"]


def run(*args):
    subprocess.run([str(KCLI), *args], check=True,
                   capture_output=True, text=True)


def main():
    if FAB.exists():
        shutil.rmtree(FAB)
    GERB.mkdir(parents=True)

    run("pcb", "export", "gerbers", "--output", f"{GERB}/", str(PCB))
    # separate PTH / NPTH files: never let a non-plated hole share a file
    # with plated ones (v1: a plated notch hole cost $38 castellation)
    run("pcb", "export", "drill", "--excellon-separate-th",
        "--output", f"{GERB}/", str(PCB))
    run("pcb", "export", "pos", "--format", "csv", "--units", "mm",
        "--side", "both", "--output", str(FAB / "cpl_raw.csv"), str(PCB))

    # zip the standard fab layers + drill
    import zipfile
    zf = FAB / "esp32_m2_companion_gerbers.zip"
    with zipfile.ZipFile(zf, "w", zipfile.ZIP_DEFLATED) as z:
        for g in STD_GLOBS:
            for f in sorted(GERB.glob(g)):
                z.write(f, f.name)
        names = z.namelist()
    # every copper layer of the board must be in the zip (the 4L -> 6L trap)
    import re
    want = len(re.findall(r'^\s*\(\d+ "(?:F|B|In\d+)\.Cu" signal\)', PCB.read_text(), re.M))
    cu_files = [n for n in names if re.search(r"\.(gtl|gbl|g\d)$", n)]
    assert len(cu_files) == want, (f"gerber zip has {len(cu_files)} copper "
                                   f"layers, the board has {want}: {cu_files}")

    # placed set + LCSC per ref, straight from the generated BOM
    lcsc = {}
    for r in csv.DictReader(open(HERE / "build" / "bom.csv")):
        for ref in r["Designator"].split(","):
            lcsc[ref] = r["LCSC Part #"]
    rows = {r["Ref"]: r for r in csv.DictReader(open(FAB / "cpl_raw.csv"))}
    missing = sorted(set(lcsc) - set(rows))
    assert not missing, f"BOM parts missing from the board: {missing}"
    unknown = sorted(r for r, p in lcsc.items()
                     if p not in NONPOLAR and p not in JLC_ROT)
    assert not unknown, (f"polarized/unclassified parts with no JLC_ROT "
                         f"entry: {unknown} - add one (offset + basis)")

    cpl = FAB / "esp32_m2_companion_cpl_jlc.csv"
    unverified = set()
    with open(cpl, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["Designator", "Mid X", "Mid Y",
                                          "Layer", "Rotation"])
        w.writeheader()
        for ref in sorted(lcsc):
            r = rows[ref]
            off, verified, _ = JLC_ROT.get(lcsc[ref], (0, "n/a", ""))
            if verified is None:
                unverified.add(f"{ref} ({lcsc[ref]}, +{off} deg)")
            w.writerow({"Designator": ref, "Mid X": r["PosX"],
                        "Mid Y": r["PosY"], "Layer": r["Side"],
                        "Rotation": f"{(float(r['Rot']) + off) % 360:.6f}"})
    placed = list(lcsc)

    # LED anode-on-resistor-side assert + preview checklist (needs pcbnew)
    subprocess.run([str(KPY), str(HERE / "tools" / "polarity_report.py"),
                    str(FAB)], check=True)

    # BOM (already JLC-format + DNP-excluded from gen_bom)
    bom = FAB / "esp32_m2_companion_bom_jlc.csv"
    shutil.copy(HERE / "build" / "bom.csv", bom)

    # publish the 3 upload files to the committed repo fab/ dir
    out = ROOT / "fab"
    out.mkdir(exist_ok=True)
    for f in (zf, bom, cpl, FAB / "polarity_checklist.md"):
        shutil.copy(f, out / f.name)

    print(f"fab package: {len(placed)} placed parts")
    print(f"  {zf}")
    print(f"  {bom}")
    print(f"  {cpl}")
    print(f"copied upload files -> {out}")
    if unverified:
        print("\nORDER BLOCKED - JLC rotation not yet preview-verified for:")
        for u in sorted(unverified):
            print("  ", u)
        print("Upload, check every row of fab/polarity_checklist.md against "
              "JLC's placement preview, then set the dates in JLC_ROT.")
        raise SystemExit(2)


if __name__ == "__main__":
    main()
