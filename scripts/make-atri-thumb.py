# -*- coding: utf-8 -*-
"""Build a proper `thumb` for the ATRI pack.

Why this exists: the manifest pointed `thumb` at `tex/head-clean.png`, which is a full-canvas
1145x1374 body texture whose content only occupies the head. The dress/装扮 card draws the thumb
straight into a small box, so a mostly-empty canvas reads as "预览图有问题" - the figure is a speck in
the corner or missing altogether.

This crops the actual character silhouette out of an assembled render and letterboxes it into a
square, so the card shows the whole figure at a usable size.

Sources, in order of preference:
    1. packs/<pack>/preview.png          - a full-body render already in the pack, if present
    2. characters/atri-01/master.png     - the master art (single flat figure)
    3. characters/atri-01/official-regeneration/pure-generation/preview-current.png

Usage:
    .venv/Scripts/python.exe scripts/make-atri-thumb.py [pack-dir-name] [--size 512] [--bust]
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
args = [a for a in sys.argv[1:] if not a.startswith("--")]
PACK_NAME = args[0] if args else "atri-v011"
PACK = ROOT / "packs" / PACK_NAME
SIZE = 512
BUST = False
for a in sys.argv[1:]:
    if a.startswith("--size="):
        SIZE = int(a.split("=", 1)[1])
    if a == "--bust":
        BUST = True

CANDIDATES = [
    PACK / "preview.png",
    ROOT / "characters/atri-01/master.png",
    ROOT / "characters/atri-01/official-regeneration/pure-generation/preview-current.png",
]

# the card draws the thumb small; a little transparent margin keeps the hair edge off the border
MARGIN = 0.04

# 2026-10-31 user feedback: "预览界面不要用全身，截取上半身就好了". At 512 px in a card slot the full
# body makes the face a thumbnail of a thumbnail. BUST keeps the top fraction of the figure's own
# height (head, shoulders, both bows, the ponytail roots) and crops the rest, so the card reads as a
# portrait. 0.62 covers down to about the waist on this master.
BUST_FRACTION = 0.62


def content_bbox(im: Image.Image):
    a = np.asarray(im.convert("RGBA"))
    ys, xs = np.nonzero(a[..., 3] > 12)
    if not len(xs):
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def main():
    src = next((p for p in CANDIDATES if p.is_file()), None)
    if src is None:
        sys.exit("no source image found; looked for:\n  " + "\n  ".join(str(p) for p in CANDIDATES))
    im = Image.open(src).convert("RGBA")
    box = content_bbox(im)
    if box is None:
        sys.exit(f"{src} has no opaque pixels")
    x0, y0, x1, y1 = box
    if BUST:
        cut = y0 + round((y1 - y0) * BUST_FRACTION)
        box = (x0, y0, x1, cut)
    figure = im.crop(box)
    print(f"source {src.relative_to(ROOT)} {im.size} -> "
          f"{'bust' if BUST else 'full'} {figure.size} at {box}")

    # fit the figure inside (1-2*MARGIN) of the square, centred, keeping aspect
    inner = int(SIZE * (1 - 2 * MARGIN))
    w, h = figure.size
    k = min(inner / w, inner / h)
    nw, nh = max(1, round(w * k)), max(1, round(h * k))
    figure = figure.resize((nw, nh), Image.LANCZOS)

    out = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    out.alpha_composite(figure, ((SIZE - nw) // 2, (SIZE - nh) // 2))
    dest = PACK / "tex" / "thumb.png"
    dest.parent.mkdir(parents=True, exist_ok=True)
    out.save(dest, optimize=True)
    print(f"wrote {dest.relative_to(ROOT)} {out.size} ({dest.stat().st_size/1024:.0f} KB)")

    mf = PACK / "figure.json"
    d = json.loads(mf.read_text(encoding="utf-8"))
    d["thumb"] = "tex/thumb.png"
    mf.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"figure.json thumb -> {d['thumb']}")


if __name__ == "__main__":
    main()
