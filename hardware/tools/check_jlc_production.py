"""Compare JLCPCB's processed production files with our fab package.

JLC sends its CAM output for approval ("Confirm Production File"):
a zip with `YG/<order>.zip` (our original upload as JLC stored it) and `ok/`
(their processed, panelized layers: tl l2 l3 bl ts bs to bo ko drl vcut ...,
inch units, whole panel). This checks, against `fab/*_gerbers.zip`:

1. the stored upload is byte-identical to ours (SHA-256 per file);
2. every drill hole: finds where our card sits in their panel by matching
   holes, then reports missing / resized / extra holes on the card
   (any difference = FAIL);
3. each layer rendered at 50 px/mm over the card area: pixels only in ours
   (red) and only in theirs (blue), as mm^2 plus a diff image per layer.
   Expected, harmless differences: etch compensation (thin outlines
   everywhere), plane pull-back from V-cut edges, gold-finger tips cut back,
   mask expansion / one mask window over the fingers, silk clipped off pads,
   panel frame on the outline layer. Inspect the diff images; WARN marks
   layers whose difference is unusually large.

Usage (from the repo root; needs network once for the pinned libraries and
`rsvg-convert` from Homebrew librsvg):
    make jlc-check JLC=~/Downloads/<order>_gerbers_Y6.zip
Writes hardware/build/jlc_check/{report.txt,diff_<layer>.png}. Exit 1 on FAIL.
"""

import hashlib
import subprocess
import sys
import zipfile
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image
from gerbonara import ExcellonFile, GerberFile
from gerbonara.utils import MM

HERE = Path(__file__).resolve().parent.parent
ROOT = HERE.parent
OURS_ZIP = ROOT / "fab" / "esp32_m2_companion_gerbers.zip"
OUT = HERE / "build" / "jlc_check"
STEM = "esp32_m2_companion"
PX = 50                      # px per mm
WARN_MM2 = 40.0              # per-layer difference worth a closer look
TOL = 0.02                   # mm, hole position / diameter tolerance
LAYERS = [("F_Cu.gtl", "tl"), ("In1_Cu.g1", "l2"), ("In2_Cu.g2", "l3"),
          ("B_Cu.gbl", "bl"), ("F_Mask.gts", "ts"), ("B_Mask.gbs", "bs"),
          ("F_Silkscreen.gto", "to"), ("B_Silkscreen.gbo", "bo"),
          ("Edge_Cuts.gm1", "ko")]

lines = []


def say(s=""):
    print(s)
    lines.append(s)


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def unpack(jlc_zip):
    if OUT.exists():
        subprocess.run(["rm", "-rf", str(OUT)], check=True)
    for d in ("ours", "jlc", "stored"):
        (OUT / d).mkdir(parents=True)
    zipfile.ZipFile(OURS_ZIP).extractall(OUT / "ours")
    zipfile.ZipFile(jlc_zip).extractall(OUT / "jlc")
    stored = list((OUT / "jlc").rglob("*.zip"))
    if stored:
        zipfile.ZipFile(stored[0]).extractall(OUT / "stored")
    ok = next((p for p in (OUT / "jlc").rglob("ok") if p.is_dir()), None)
    if ok is None:
        sys.exit("no 'ok/' production-layer folder in the JLC zip")
    return OUT / "ours", ok, OUT / "stored"


def check_stored(ours, stored):
    say("== 1. stored upload vs our fab package")
    bad = 0
    for f in sorted(ours.iterdir()):
        s = stored / f.name
        r = "same" if s.exists() and sha(s) == sha(f) else ("MISSING" if not s.exists() else "DIFF")
        bad += r != "same"
        say(f"  {r:7} {f.name}")
    say(f"  -> {'identical' if not bad else f'{bad} file(s) differ - FAIL'}")
    return bad == 0


def holes_ours(ours):
    h = []
    for f in sorted(ours.glob("*.drl")):
        if f.stat().st_size < 50:
            continue
        for o in ExcellonFile.open(f).objects:
            if hasattr(o, "x") and hasattr(o, "tool"):
                k = 1 if o.unit == MM else 25.4
                h.append((o.x * k, o.y * k, o.tool.diameter * k))
    return h


def holes_jlc(ok):
    h = []
    for o in GerberFile.open(ok / "drl").objects:
        if type(o).__name__ == "Flash":
            k = 1 if o.unit == MM else 25.4
            ap = o.aperture
            h.append((o.x * k, o.y * k, getattr(ap, "diameter", 0) * (1 if ap.unit == MM else 25.4)))
    return h


def check_drill(ours, ok):
    say("\n== 2. drill holes")
    ho, hj = holes_ours(ours), holes_jlc(ok)
    votes = Counter((round(X - x, 2), round(Y - y, 2))
                    for x, y, d in ho for X, Y, D in hj if abs(D - d) < TOL)
    (dx, dy), n = votes.most_common(1)[0]
    say(f"  ours {len(ho)} holes, JLC panel {len(hj)}; card offset in panel "
        f"({dx}, {dy}) mm, {n}/{len(ho)} holes agree")
    shifted = [(X - dx, Y - dy, D) for X, Y, D in hj]
    near = lambda a, b: abs(a[0] - b[0]) < TOL and abs(a[1] - b[1]) < TOL
    missing = [h for h in ho if not any(near(h, j) for j in shifted)]
    resized = [(h[2], j[2]) for h in ho for j in shifted if near(h, j) and abs(h[2] - j[2]) > TOL]
    xs, ys = [h[0] for h in ho], [h[1] for h in ho]
    on_card = [j for j in shifted if min(xs) - 2 < j[0] < max(xs) + 2 and min(ys) - 2 < j[1] < max(ys) + 2]
    extra = [j for j in on_card if not any(near(j, h) for h in ho)]
    say(f"  missing {len(missing)}, resized {len(resized)}, extra on card {len(extra)}")
    say(f"  JLC hole sizes (whole panel): {dict(Counter(round(D, 2) for *_, D in hj))}")
    ok_ = not (missing or resized or extra) and n == len(ho)
    say(f"  -> {'OK' if ok_ else 'FAIL'}")
    return ok_, dx, dy


def check_layers(ours, ok, dx, dy):
    say("\n== 3. layers (red = only ours, blue = only JLC; mm^2)")
    (bx0, by0), (bx1, by1) = GerberFile.open(ours / f"{STEM}-Edge_Cuts.gm1").bounding_box(unit=MM)
    bx0, by0, bx1, by1 = bx0 - 1, by0 - 1, bx1 + 1, by1 + 1
    W, H = int((bx1 - bx0) * PX), int((by1 - by0) * PX)

    def raster(path, ox, oy, name):
        svg = GerberFile.open(path).to_svg(arg_unit=MM, svg_unit=MM, fg="black", bg="white",
                                           force_bounds=((bx0 + ox, by0 + oy), (bx1 + ox, by1 + oy)))
        s, p = OUT / f"{name}.svg", OUT / f"{name}.png"
        s.write_text(str(svg))
        subprocess.run(["rsvg-convert", "-b", "white", "-w", str(W), "-h", str(H), str(s), "-o", str(p)],
                       check=True)
        return np.asarray(Image.open(p).convert("L")) < 128

    for mine, theirs in LAYERS:
        if not (ok / theirs).exists():
            say(f"  {theirs:4} (not in JLC zip)")
            continue
        a = raster(ours / f"{STEM}-{mine}", 0, 0, f"o_{theirs}")
        b = raster(ok / theirs, dx, dy, f"j_{theirs}")
        oo, jo = (a & ~b).sum() / PX / PX, (b & ~a).sum() / PX / PX
        img = np.full((H, W, 3), 255, np.uint8)
        img[a & b] = (180, 180, 180)
        img[a & ~b] = (220, 30, 30)
        img[b & ~a] = (30, 90, 220)
        Image.fromarray(img).save(OUT / f"diff_{theirs}.png")
        flag = "WARN - inspect" if max(oo, jo) > WARN_MM2 else ""
        say(f"  {theirs:4} {mine:18} ours-only {oo:7.2f}  JLC-only {jo:7.2f}  {flag}")
    say(f"  diff images: {OUT}/diff_<layer>.png")


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    ours, ok, stored = unpack(Path(sys.argv[1]).expanduser())
    a = check_stored(ours, stored)
    b, dx, dy = check_drill(ours, ok)
    check_layers(ours, ok, dx, dy)
    say(f"\nRESULT: {'PASS (review the diff images)' if a and b else 'FAIL'}")
    (OUT / "report.txt").write_text("\n".join(lines) + "\n")
    sys.exit(0 if a and b else 1)


if __name__ == "__main__":
    main()
