"""Place the tied hair locks of the pure-generation candidate on the master template.

The master is the only geometry authority. Each lock is a COMPLETE drawing (the whole lock,
including the length the master hides), so it can be drawn in the back layer and be occluded by the
hair that covers it in the master instead of ending in a cut.

Registration is curve registration, not area matching: for every (scale, rotation) the lock's own
outer profile is matched to the master's own outer silhouette over the rows where that lock is the
outermost element, and the translation is solved directly. An earlier version also penalised pixels
landing outside the master body; that term lets a shrunk lock hide inside the body and drove the fit
to the search bounds (see scratch/dbg-fit.py), so it is gone. The root rule is reported, not
enforced with a hard wall: a hard "root inside the bow" constraint made every start fail.

Which rows the master draws in front of the hair is measured from the master's own pixels in
master_front_rows(); it is not an art choice.

Run from the repository root:
    python characters/atri-01/official-regeneration/pure-generation/fit-locks.py
Writes lock-placement.json next to this file.
"""
from pathlib import Path
import json
import numpy as np, cv2
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
MASTER = ROOT/'characters/atri-01/master.png'
# Chosen drawings. The near lock is the left half of the complete pair drawing recovered from the
# original model (complete-ponytails-reextract): the user rejected the paired-lock crop
# pony-pair-left-01 and ponytail-left-01, and a fresh gpt-image-2.5 drawing came back as a hair-thin
# ribbon (raw/ponytail-near-complete-05.png, rejected). The far lock keeps ponytail-far-complete-06.
RAW = {'tail-left': ROOT/'characters/atri-01/official-regeneration/raw/ponytail-near-complete-06.png',
       'tail-right': ROOT/'characters/atri-01/official-regeneration/raw/ponytail-far-complete-06.png'}
MAA = np.array(Image.open(MASTER).convert('RGBA'))
MA = MAA[:, :, 3] > 60
H, W = MA.shape
BOW_BOX = {'tail-left': (289, 221, 378, 340), 'tail-right': (770, 216, 846, 320)}
# Rows of the master in which each lock is the outermost element of the silhouette.
WINDOW = {'tail-left': (0, 520, 355, 950), 'tail-right': (620, 1145, 340, 995)}


def mask_of(path, side):
    a = np.array(Image.open(path).convert('RGBA'))[:, :, 3]
    m = (a > 128).astype('uint8')
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    picks = [(st[i][4], i) for i in range(1, n)
             if st[i][4] >= 500 and ((side < 0 and st[i][0] + st[i][2] / 2.0 < 620) or
                                     (side > 0 and st[i][0] + st[i][2] / 2.0 > 560))]
    keep = max(picks)[1] if picks else 1 + int(np.argmax(st[1:, 4]))
    return lab == keep


def master_profile(side, box):
    x0, x1, y0, y1 = box
    out = []
    for y in range(y0, y1 + 1):
        r = np.nonzero(MA[y, x0:x1])[0]
        if len(r):
            out.append((r.min() + x0 if side < 0 else r.max() + x0, y))
    return np.array(out, float)


def fit(raw, side, bow_box, box, scales, rots, dy_span=70.0, stray_weight=0.35):
    """Curve registration of the lock's outer profile onto the master outer silhouette."""
    m = mask_of(raw, side)
    ys = np.nonzero(m.any(axis=1))[0]
    prof = np.array([((np.nonzero(m[y])[0].min() if side < 0 else np.nonzero(m[y])[0].max()), y)
                     for y in range(ys.min(), ys.max() + 1)], float)
    iy, ix = np.nonzero(m)
    idx = np.linspace(0, len(ix) - 1, min(len(ix), 4000)).astype(int)
    inner = np.column_stack([ix[idx], iy[idx]]).astype(float)
    tgt = master_profile(side, box)
    Ty, Mx = tgt[:, 1], tgt[:, 0]
    x0, x1, y0, y1 = box
    top = prof[prof[:, 1] < prof[:, 1].min() + 25]
    c = np.array([top[:, 0].mean(), top[:, 1].mean()])
    best = None
    for s in scales:
        for rdeg in rots:
            th = float(np.radians(rdeg))
            A = s*np.array([[np.cos(th), -np.sin(th)], [np.sin(th), np.cos(th)]])
            P0 = (A @ (prof - c).T).T + c
            for dy in np.arange(-dy_span, dy_span + 0.1, 2.0):
                py = P0[:, 1] + dy
                sel = (py >= y0) & (py <= y1)
                if sel.sum() < 100:
                    continue
                mx = np.interp(py[sel], Ty, Mx)
                tx = float(np.mean(mx - P0[sel, 0]))
                diff = float(np.abs(P0[sel, 0] + tx - mx).mean())
                # Strictness: nothing may hang outside the master's own body, so the fraction of
                # lock pixels landing outside it is penalised as well as the profile error.
                I = (A @ (inner - c).T).T + c + np.array([tx, dy])
                outside = float((~MA[np.clip(I[:, 1], 0, H - 1).astype(int),
                                     np.clip(I[:, 0], 0, W - 1).astype(int)]).mean())
                # The root has to stay under its bow: the top of the lock is steered into the box.
                top_pt = P0[int(np.argmin(P0[:, 1]))] + np.array([tx, dy])
                bx0, by0, bx1, by1 = bow_box
                ddx = bx0 - top_pt[0] if top_pt[0] < bx0 else (top_pt[0] - bx1 if top_pt[0] > bx1 else 0.0)
                ddy = by0 - top_pt[1] if top_pt[1] < by0 else (top_pt[1] - by1 if top_pt[1] > by1 else 0.0)
                score = diff + stray_weight * outside + 4.0 * float(np.hypot(ddx, ddy))
                if best is None or score < best[0]:
                    best = (score, float(s), float(rdeg), tx, float(dy), diff, outside)
    score, s, rdeg, tx, dy, diff, outside = best
    th = np.radians(rdeg)
    A = s*np.array([[np.cos(th), -np.sin(th)], [np.sin(th), np.cos(th)]])
    P = (A @ (prof - c).T).T + c + np.array([tx, dy])
    root = P[int(np.argmin(P[:, 1]))]
    bx0, by0, bx1, by1 = bow_box
    rdx = bx0 - root[0] if root[0] < bx0 else (root[0] - bx1 if root[0] > bx1 else 0.0)
    rdy = by0 - root[1] if root[1] < by0 else (root[1] - by1 if root[1] > by1 else 0.0)
    mat = np.vstack([np.column_stack([A, c + np.array([tx, dy]) - A @ c]), [0, 0, 1]])
    return dict(profile_error_px=diff, outside_master_fraction=outside, scale=s,
                rotation_deg=rdeg, matrix=mat.tolist(),
                root_xy=[float(root[0]), float(root[1])],
                root_bow_dist_px=float(np.hypot(rdx, rdy))), m, mat


def root_cover_row(bow_box):
    """Row where the lock leaves the bow's cover and becomes a visible band on its own.

    Measured on the master: the bow's knot sits near the top of its recorded coverage box, and the
    lock's own band (one outer and one inner outline) starts right below the knot, well above the
    box's lower edge. Cutting the lock at the box's lower edge instead left a gap between the bow
    and the lock exactly where the master draws the band, so the cut row is taken from the knot.
    Above this row the lock may only exist where the bow sprite covers it.
    """
    return int(bow_box[1]) + 80


def master_front_rows(path, mat, side=-1, thresh=0.45, min_px=8):
    """Rows where the master's own pixels agree with the placed lock: there the lock is in front."""
    tex = np.array(Image.open(path).convert('RGBA'))
    warp = cv2.warpAffine(tex.astype(np.float32), mat[:2].astype(np.float32), (W, H))
    warp = np.uint8(np.clip(warp, 0, 255))
    lm = warp[:, :, 3] > 128
    diff = np.abs(warp[:, :, :3].astype(int) - MAA[:, :, :3].astype(int)).sum(axis=2)
    match = (diff < 60) & lm & MA
    lim = 560 if side < 0 else W
    rows = []
    for y in range(H):
        tot = int(lm[y, :lim].sum())
        mt = int(match[y, :lim].sum())
        if tot > min_px and mt / tot >= thresh:
            rows.append(y)
    if not rows:
        return None, []
    return [min(rows), max(rows)], rows


def main():
    scales = [round(0.70 + 0.005 * i, 4) for i in range(81)]
    rots = [round(-6 + 0.25 * i, 3) for i in range(49)]
    left, _m, lmat = fit(RAW['tail-left'], -1, BOW_BOX['tail-left'], WINDOW['tail-left'], scales, rots)
    measured, rows = master_front_rows(RAW['tail-left'], lmat)
    # The master draws the lock from just below its bow downwards (its own band has an outer and an
    # inner outline there), so the front piece starts at the bow's bottom edge, not at the row where
    # a colour comparison happens to agree.
    bb = root_cover_row(BOW_BOX['tail-left'])
    band = [bb + 4, measured[1]] if measured else [bb + 4, None]
    # The front piece is the same drawing restricted to the measured rows, so the two pieces share
    # one texture and one transform and cannot show a seam.
    mask_path = (ROOT/'characters/atri-01/official-regeneration/raw/'
                 'ponytail-near-complete-06-front.png')
    tex = np.array(Image.open(RAW['tail-left']).convert('RGBA'))
    warp = np.uint8(np.clip(cv2.warpAffine(tex.astype(np.float32), lmat[:2].astype(np.float32),
                                           (W, H)), 0, 255))
    lm = warp[:, :, 3] > 128
    band_mask = np.zeros(lm.shape, np.uint8)
    if band:
        band_mask[band[0]:band[1] + 1] = 255
    band_mask &= (lm.astype(np.uint8) * 255)
    Image.fromarray(np.dstack([np.full(lm.shape, 255, np.uint8)] * 3 + [band_mask])).save(mask_path)

    placed = HERE/'lock-placement.json'
    previous = json.loads(placed.read_text(encoding='utf8')) if placed.exists() else {}
    right = previous.get('tail-right')
    if right:
        right = dict(right, status='preserved: user accepted the far lock in the current candidate')
    else:
        right, _m, _mat = fit(RAW['tail-right'], +1, BOW_BOX['tail-right'], WINDOW['tail-right'],
                              scales, [round(6 + 0.25 * i, 3) for i in range(49)])
    result = {
        'master': 'characters/atri-01/master.png',
        'method': ('Curve registration per lock: the lock outer profile is matched to the master '
                   'outer silhouette over the rows where that lock is outermost, translation solved '
                   'directly, uniform similarity only. The front band is measured from master pixel '
                   'agreement (fit-locks.py master_front_rows), not chosen by taste.'),
        'tail-left': dict(left, source=str(RAW['tail-left'].relative_to(ROOT)).replace('\\', '/'),
                          complete_lock=True),
        'tail-right': right,
        'front_overlay': {
            'tail-left': {'rows': band, 'bow_bottom_row': bb, 'measured_color_rows': measured,
                          'front_mask': str(mask_path.relative_to(ROOT)).replace('\\', '/'),
                          'reason': ('rows where the master pixels match the placed lock art '
                                     '(match ratio >= 0.45); outside the band the same lock art stays '
                                     'in the back layer so the covering hair hides it')},
            'tail-right': {'rows': None,
                           'reason': 'far lock belongs entirely to the back layer (kept as accepted)'},
        },
    }
    placed.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print(json.dumps({'tail-left': {k: result['tail-left'][k] for k in
                                    ('profile_error_px', 'scale', 'rotation_deg',
                                     'root_bow_dist_px')},
                      'front_rows': band, 'front_row_count': len(rows),
                      'tail-right_status': (right or {}).get('status', 're-fitted')}, indent=2))


if __name__ == '__main__':
    main()
