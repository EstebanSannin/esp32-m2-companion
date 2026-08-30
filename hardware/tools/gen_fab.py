"""Generate the JLCPCB fab package: gerbers.zip + BOM + CPL.

Run: uv run python tools/gen_fab.py   (or `make fab`)
Outputs into hardware/build/fab/ and copies the 3 upload files to repo fab/.

CPL excludes DNP parts + non-placed features (edge connector, test points)
so JLC's pick-and-place does not try to place things that aren't there.
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

# refs to keep OUT of the pick-and-place file
DNP = {"R5", "R6", "C8", "C9"}                       # DNP passives
NONPLACED = {"J1"} | {f"TP{i}" for i in range(1, 7)}  # edge + test points

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
    run("pcb", "export", "drill", "--output", f"{GERB}/", str(PCB))
    run("pcb", "export", "pos", "--format", "csv", "--units", "mm",
        "--side", "both", "--output", str(FAB / "cpl_raw.csv"), str(PCB))

    # zip the standard fab layers + drill
    import zipfile
    zf = FAB / "esp32_m2_companion_gerbers.zip"
    with zipfile.ZipFile(zf, "w", zipfile.ZIP_DEFLATED) as z:
        for g in STD_GLOBS:
            for f in sorted(GERB.glob(g)):
                z.write(f, f.name)

    # CPL -> JLC format, filtered
    rows = list(csv.DictReader(open(FAB / "cpl_raw.csv")))
    placed = [r for r in rows
              if r["Ref"] not in DNP and r["Ref"] not in NONPLACED]
    cpl = FAB / "esp32_m2_companion_cpl_jlc.csv"
    with open(cpl, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["Designator", "Mid X", "Mid Y",
                                          "Layer", "Rotation"])
        w.writeheader()
        for r in placed:
            w.writerow({"Designator": r["Ref"], "Mid X": r["PosX"],
                        "Mid Y": r["PosY"], "Layer": r["Side"],
                        "Rotation": r["Rot"]})

    # BOM (already JLC-format + DNP-excluded from gen_bom)
    bom = FAB / "esp32_m2_companion_bom_jlc.csv"
    shutil.copy(HERE / "build" / "bom.csv", bom)

    # publish the 3 upload files to the committed repo fab/ dir
    out = ROOT / "fab"
    out.mkdir(exist_ok=True)
    for f in (zf, bom, cpl):
        shutil.copy(f, out / f.name)

    print(f"fab package: {len(placed)} placed parts")
    print(f"  {zf}")
    print(f"  {bom}")
    print(f"  {cpl}")
    print(f"copied upload files -> {out}")


if __name__ == "__main__":
    main()
