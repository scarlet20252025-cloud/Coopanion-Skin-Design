"""Measure each accepted open eye's iris centre and size from the art itself.

The 期待 stars go on the iris, and the 大哭 stream starts at the lower lid, so both need the real
iris geometry rather than a guess: the rig's eye boxes are not the iris (tex/source-014.png is
148x111 while the rig box is 53x42). Prints the table that is pasted into renderer-template.js
as FX_IRIS, and writes 8x zooms with the star placement marked so it can be eyeballed.

    python characters/atri-01/official-regeneration/pure-generation/probes/measure-iris-centre.py
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[5]
PACK = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "scratch/candidates/atri-pure-components-01"
OUT = ROOT / "scratch/fx-probe"

EYES = (
    ("standing", "0", "source-014", True),
    ("standing", "1", "source-015", False),
    ("seated", "0", "source-025", True),
    ("seated", "1", "source-026", False),
)
# the whale figure paints both stars at the iris centre, offset by these fractions of the iris box,
# with a radius of .25 / .135 of the iris width
STARS = ((-0.16, -0.2, 0.25), (0.2, 0.2, 0.135))

OUT.mkdir(parents=True, exist_ok=True)
rows = []
for pose, idx, tex, near in EYES:
    im = Image.open(PACK / "tex" / f"{tex}.png").convert("RGBA")
    a = np.array(im)
    r, g, b = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
    iris = (a[..., 3] > 200) & (r > 110) & (r - g > 45) & (b - g > 12)
    ys, xs = np.nonzero(iris)
    if len(xs) == 0:
        print(f"{pose} eye {idx} ({tex}): no iris pixels matched")
        continue
    cx, cy = float(xs.mean()), float(ys.mean())
    iw, ih = float(xs.max() - xs.min() + 1), float(ys.max() - ys.min() + 1)
    print(f"{pose} eye {idx} ({tex}): iris {iw:.0f}x{ih:.0f} centre ({cx:.1f},{cy:.1f}) px={len(xs)}")
    rows.append((pose, idx, cx, cy, iw, ih))

    m, z = 24, 8
    bx0, by0 = int(xs.min()) - m, int(ys.min()) - m
    crop = im.crop((bx0, by0, int(xs.max()) + m, int(ys.max()) + m))
    crop = crop.resize((crop.width * z, crop.height * z), Image.NEAREST)
    d = ImageDraw.Draw(crop)
    for i, (fx, fy, rr) in enumerate(STARS):
        px, py = (cx + fx * iw - bx0) * z, (cy + fy * ih - by0) * z
        colour = (0, 255, 0) if i == 0 else (255, 255, 0)
        d.line([(px - 14, py), (px + 14, py)], fill=colour, width=2)
        d.line([(px, py - 14), (px, py + 14)], fill=colour, width=2)
        d.ellipse([px - rr * iw * z, py - rr * iw * z, px + rr * iw * z, py + rr * iw * z], outline=colour, width=2)
    out = OUT / f"iris-{pose}-{idx}-stars-8x.png"
    crop.save(out)
    print(f"   zoom -> {out}")

print("")
print("paste into renderer-template.js:")
print(" const FX_IRIS={")
for pose in ("standing", "seated"):
    row = [t for t in rows if t[0] == pose]
    if len(row) != 2:
        continue
    entries = ", ".join(f"{{cx:{c:.1f},cy:{y:.1f},w:{w:.0f},h:{h:.0f}}}" for _, _, c, y, w, h in row)
    print(f"  {pose}:[{entries}],")
print(" };")
