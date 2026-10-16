"""Check that the official effect marks land on empty canvas in this pack's assembled art.

The mark positions in renderer-template.js are the official whale figure's, in kit logo units.
This converts them with ATRI's own logo_scale / center_x / feet_y and reports, for each mark, the
alpha of the union of every part texture at that pixel: 0 means the mark floats clear of the art.

    python characters/atri-01/official-regeneration/pure-generation/probes/check-fx-clearance.py
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[5]
PACK = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "scratch/candidates/atri-pure-components-01"

model = json.loads((PACK / "model.json").read_text(encoding="utf-8"))
W, H = model["canvas"]
S, CX, FEET = model["logo_scale"], model["center_x"], model["feet_y"]


def to_master(logo):
    return ((logo[0] - 128) / S + CX, (logo[1] - 256) / S + FEET)


MARK_LOGO = {
    "sweat": (196, 88),
    "anger": (190, 62),
    "bang_question": (206, 36),
    "orbit_top": (124, 34),
    "think_side": (204, 52),
    "listen": (214, 116),
}

union = np.zeros((H, W), dtype=np.uint8)
for path in sorted((PACK / "tex").glob("*.png")):
    a = np.array(Image.open(path).convert("RGBA"))
    if a.shape[:2] != union.shape:
        print("skip (canvas mismatch):", path.name, a.shape)
        continue
    np.maximum(union, a[..., 3], out=union)

print(f"pack {PACK.name}  canvas {W}x{H}  logo_scale {S:.6f}  center_x {CX}  feet_y {FEET}")
print("official mark spots (logo units) mapped onto this pack's master frame:")
ok = True
for name, logo in MARK_LOGO.items():
    x, y = to_master(logo)
    xi, yi = int(round(x)), int(round(y))
    on_canvas = 0 <= xi < W and 0 <= yi < H
    alpha = int(union[yi, xi]) if on_canvas else -1
    if not on_canvas or alpha > 0:
        ok = False
    row = union[yi] if on_canvas else None
    span = ""
    if row is not None:
        xs = np.nonzero(row > 8)[0]
        if len(xs):
            span = f"  art on that row: x {xs.min()}..{xs.max()}"
    print(f"  {name:14s} -> master ({xi:4d},{yi:4d})  alpha={alpha:3d}  on_canvas={on_canvas}{span}")
print("")
print("PASS: every mark sits in empty canvas" if ok else "FAIL: a mark lands on art or off-canvas")
