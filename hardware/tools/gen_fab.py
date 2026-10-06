"""Generate the JLCPCB fab package: gerbers.zip + BOM + CPL.

Run: uv run python tools/gen_fab.py   (or `make fab`)
Outputs into hardware/build/fab/ and copies the 3 upload files to repo fab/.

CPL contains exactly the parts in the generated BOM (build/bom.csv, which
gen_bom already DNP-filters) - no hand-kept DNP list here (rev A had one;
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
            "C23138", "C22775", "C21189"}

# LCSC part -> (degrees added to KiCad rotation, verified-against-JLC-
# preview date for THIS revision or None, basis). Rev-B entries start
# unverified; fill the date only after checking the JLC preview against
# polarity_checklist.md (never by eye - the v1 LED trap).
JLC_ROT = {
    "C273616": (180, None, "TJ-S1706 green: v1 placed at +0 came out 180 deg "
                "reversed; hand-rotated part confirmed (bringup 2026-10-05)"),
    "C273612": (180, None, "TJ-S1706 red: same as C273616"),
    "C12743": (0, None, "BAT54A SOT-23: asymmetric pads, v1 placed correctly"),
    "C7519": (0, None, "USBLC6-2SC6: v1 orientation NOT proven electrically "
              "(U1.2 GND floated) - check pin-1 dot"),
    "C160390": (0, None, "JST SH-4: v1 pinout proven by PU/PD sweep"),
    "C160394": (0, None, "JST SH-8: v1 pinout proven by PU/PD sweep"),
    "C2913204": (0, None, "WROOM-1 module: v1 functional"),
}

STD_GLOBS = ["*.gtl", "*.g1", "*.g2", "*.gbl", "*.gts", "*.gbs",
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
    # separate PTH / NPTH files: rev B's mounting notch is NPTH - keep it in
    # its own file so JLC's CAM cannot plate it (v1: plated -> $38 fee)
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
