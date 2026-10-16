"""Restore the certified smiling eyes from the shipped source art.

2026-10-17 user correction: "这不是图层问题是旧工程的裁切问题". The shipped pair
(tex/source-012/013, produced by prepare.py's hand-drawn closed_polys) is not a layer problem:
the two hand-drawn polygons cut through the lid arc itself, so the lash tips and the pale
double-lid line never made it into the layer, and the arcs were rotated by the polygon shape
(+19 deg on the left, -9/+9 deg on the right). The CERTIFIED source
characters/atri-01/art-source/closed-happy.png has the correct art.

This script re-extracts the two eyes from that source with the same coverage/unmatte method
prepare.py uses for the other redrawn eyes, so nothing is generated and no pixel is drawn:
- ink  : the lid arc plus its lash tips (dark brown, differs from the blank face)
- fold : the pale double-lid line just above the arc
Hair that is dark in both the source and the blank face is never taken, and the brow/bang
strip above the eyes is excluded, so no scalp or fringe enters the layer.

It writes the two tracked new-art/ PNGs and mirrors them into the pack's tex/ directory, so
a fresh clone rebuilds the same pack.
"""
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
NEW_ART = HERE / 'new-art'
PACK_TEX = ROOT / 'scratch/candidates/atri-pure-components-01/tex'
SIZE = (1145, 1374)

# eye0 = viewer-left (near) eye, eye1 = viewer-right (far) eye
EYES = {'happy-arc-0': (470, 635), 'happy-arc-1': (660, 785)}
BANG_STRIP = (365, 475, 468, 655)   # brow/fringe rows above the near eye
FACE = (412, 548, 440, 800)

def largest(mask):
    lab, n = ndimage.label(mask)
    if n <= 1:
        return mask
    sizes = ndimage.sum(mask, lab, range(1, n + 1))
    return lab == (1 + int(np.argmax(sizes)))

def attach(mask, gap, min_size):
    """Largest component plus any small component that sits within gap px of it."""
    lab, n = ndimage.label(mask)
    if n == 0:
        return mask
    sizes = ndimage.sum(mask, lab, range(1, n + 1))
    keep = np.zeros(n + 1, bool)
    keep[1 + int(np.argmax(sizes))] = True
    near = ndimage.binary_dilation(keep[lab], np.ones((gap, gap)))
    for k in range(n):
        if keep[k + 1] or sizes[k] < min_size:
            continue
        if ((lab == (k + 1)) & near).any():
            keep[k + 1] = True
    return keep[lab]

def main():
    blank = np.asarray(Image.open(ROOT / 'characters/atri-01/art-source/face-clean-v2.png')
                       .convert('RGB')).astype(np.float32)
    source = np.asarray(Image.open(ROOT / 'characters/atri-01/art-source/closed-happy.png')
                        .convert('RGB')).astype(np.float32)
    lb, lc = blank.mean(axis=2), source.mean(axis=2)
    delta = lb - lc
    xs = np.arange(SIZE[0])

    face = np.zeros((SIZE[1], SIZE[0]), bool)
    face[FACE[0]:FACE[1], FACE[2]:FACE[3]] = True
    bang = np.zeros((SIZE[1], SIZE[0]), bool)
    bang[BANG_STRIP[0]:BANG_STRIP[1], BANG_STRIP[2]:BANG_STRIP[3]] = True
    hair_both = (lb < 165) & (lc < 165)

    for name, (x_from, x_to) in EYES.items():
        # lid arc + lash tips: dark ink that is not present in the blank face
        ink = (lc < 190) & (delta > 35) & ~hair_both & face & ~bang
        lid = largest(attach(ink & (xs >= x_from)[None, :] & (xs <= x_to)[None, :], 25, 4))

        # the pale double-lid line sits in a thin band just above the fitted arc
        ys, xsn = np.nonzero(lid)
        arc = np.polyfit(xsn.astype(float), ys.astype(float), 2)
        band = np.zeros((SIZE[1], SIZE[0]), bool)
        for x in range(int(xsn.min()), int(xsn.max()) + 1):
            centre = float(np.polyval(arc, x))
            band[max(0, int(round(centre)) - 22):int(round(centre)) - 6, x] = True
        fold = largest(attach(band & (delta > 7) & (lc < 239) & ~hair_both & face & ~bang, 9, 6))

        region = lid | fold
        rgba = np.dstack([source, np.where(region, 255, 0)]).astype(np.uint8)
        out = Image.fromarray(rgba, 'RGBA')
        out.save(NEW_ART / f'{name}.png')
        out.save(PACK_TEX / f'{name}.png')
        ys, xs2 = np.nonzero(region)
        print(f'{name}: {int(region.sum())} px, lid {int(lid.sum())}, fold {int(fold.sum())}, '
              f'bbox {(int(xs2.min()), int(ys.min()), int(xs2.max()) + 1, int(ys.max()) + 1)}')

if __name__ == '__main__':
    main()
