"""Convert the Samnium Tech logo PNG into silkscreen rectangles (JSON).

Crops the gear logomark out of the full logo (drops the wordmark), thresholds
it to 1-bit, and emits run-length horizontal rectangles in mm for placement on
B.SilkS by tools/add_silk.py.

Run:  uv run --no-project --with pillow python hardware/branding/gen_logo_silk.py
Source: logo_samnium_tech.png (samnium.tech, logo_samnium_tech_no_bg_no_name.png,
3167x1255, fetched 2026-08-30). Owner-supplied company logo.
"""
import json
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
SRC = HERE / "logo_samnium_tech.png"
OUT = HERE / "logo_silk_rects.json"
LOGO_H_MM = 4.0      # silk logo height; width follows the gear aspect
TARGET_PX = 240      # downsample height (smooth outline, sane polygon count)
THRESH = 140         # luminance below -> silk ink


def main():
    im = Image.open(SRC).convert("RGBA")
    W, H = im.size
    ap = im.split()[3].load()
    # gear = first non-transparent column run from the left; stop at the gap
    colmax = [max(ap[x, y] for y in range(0, H, 4)) for x in range(W)]
    x = 0
    while x < W and colmax[x] <= 20:
        x += 1
    start = x
    while x < W and colmax[x] > 20:
        x += 1
    gear = im.crop((start, 0, x, H))
    gear = gear.crop(gear.split()[3].getbbox())
    gw, gh = gear.size
    gear = gear.resize((max(1, int(gw * TARGET_PX / gh)), TARGET_PX), Image.LANCZOS)
    w, h = gear.size
    comp = Image.alpha_composite(Image.new("RGBA", (w, h), (255,) * 4), gear).convert("L")
    px = comp.load()
    mmpp = LOGO_H_MM / h
    rects = []
    for y in range(h):
        xx = 0
        while xx < w:
            if px[xx, y] < THRESH:
                x0 = xx
                while xx < w and px[xx, y] < THRESH:
                    xx += 1
                rects.append([x0 * mmpp, y * mmpp, xx * mmpp, (y + 1) * mmpp])
            else:
                xx += 1
    json.dump({"w_mm": w * mmpp, "h_mm": h * mmpp, "rects": rects}, open(OUT, "w"))
    print(f"{OUT.name}: {len(rects)} rects, {w*mmpp:.2f}x{h*mmpp:.2f} mm")


if __name__ == "__main__":
    main()
