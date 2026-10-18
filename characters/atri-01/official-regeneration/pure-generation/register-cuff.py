"""RETIRED diagnostic: a full cuff cannot be matched to a cuff partly hidden by torso."""
from pathlib import Path
import json
import cv2
import numpy as np
from PIL import Image
from scipy.optimize import least_squares
from scipy.spatial import cKDTree

P = Path(__file__).resolve().parent.parent
src = np.array(Image.open(P / 'raw/arm-far-complete-07.png').convert('RGBA'))
mother = np.array(Image.open(P.parent / 'art-source/master-leg-v2.png').convert('RGBA'))

def cuff(a, box=None):
    f = a.astype(float)
    mask = ((f[:, :, 1] > f[:, :, 0] + 20) & (f[:, :, 2] > f[:, :, 0] + 25)
            & (f[:, :, 1] > 70) & (f[:, :, 3] > 128)).astype('uint8')
    if box:
        x0, y0, x1, y1 = box
        region = np.zeros_like(mask)
        region[y0:y1, x0:x1] = 1
        mask *= region
    contours = [c for c in cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0] if cv2.contourArea(c) > 30]
    # White piping can separate the two teal panels. Measure their shared outer hull,
    # rather than comparing one panel on the source to a different panel on the mother.
    hull = cv2.convexHull(np.concatenate(contours))
    joined = np.zeros_like(mask)
    cv2.drawContours(joined, [hull], -1, 1, cv2.FILLED)
    contour = max(cv2.findContours(joined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0], key=cv2.contourArea)
    points = contour.reshape(-1, 2).astype(float)
    return points[::max(1, len(points) // 300)], float(cv2.contourArea(contour))

a, area_a = cuff(src, (650, 800, 920, 1060))
b, area_b = cuff(mother, (760, 850, 855, 990))
ca, cb = a.mean(0), b.mean(0)
tree_b = cKDTree(b)
initial_scale = np.sqrt(area_b / area_a)

def moved(params):
    scale, angle, dx, dy = params
    c, s = np.cos(angle), np.sin(angle)
    rot = np.array([[c, -s], [s, c]])
    return (a - ca) @ rot.T * scale + cb + [dx, dy]

def residual(params):
    x = moved(params)
    return np.r_[tree_b.query(x)[0], cKDTree(x).query(b)[0]]

fits = []
for angle in np.deg2rad([-25, -12, 0, 12, 25]):
    fit = least_squares(residual, [initial_scale, angle, 0, 0],
                        bounds=([initial_scale*.65, -.8, -30, -30], [initial_scale*1.4, .8, 30, 30]),
                        diff_step=.001, max_nfev=200)
    fits.append(fit)
fit = min(fits, key=lambda f: np.mean(f.fun**2))
scale, angle, dx, dy = fit.x
c, s = np.cos(angle), np.sin(angle)
linear = scale * np.array([[c, -s], [s, c]])
matrix = np.column_stack((linear, cb + [dx, dy] - linear @ ca))
report = dict(name='arm-far-complete-07', method='symmetric contour distance of teal cuff; colour masks for measurement only',
              matrix=matrix.tolist(), scale=float(scale), rotation_degrees=float(np.rad2deg(angle)),
              contour_rms=float(np.sqrt(np.mean(fit.fun**2))), contour_p95=float(np.percentile(fit.fun, 95)),
              status='withdrawn: full source cuff compared to partially occluded mother cuff; not a valid registration',
              alpha_policy='generated alpha only; no RGB replacement or alpha carving from cuff mask')
(P/'pure-generation/far-cuff-registration.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf8')
print(json.dumps(report))
raise SystemExit('Retired diagnostic; use full generated sleeve assembly behind generated torso, not partial-cuff hull fit')
