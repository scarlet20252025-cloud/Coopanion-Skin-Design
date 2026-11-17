# -*- coding: utf-8 -*-
"""official03-rebuild 配准工具：把 chatgpt-sub 的编辑结果配准回母版坐标。

照官方 repro-kit docs/03 的做法（tools/oldflow/tools/lib.py + stage1.py）：
  1) SIFT + RANSAC 求相似变换（处理整体缩放/旋转/平移）
  2) ECC (MOTION_AFFINE) 在指定 roi 上精对
  3) warp 回母版画布 1086x1448

用法:
    python register_03.py <name> <ref> <x0> <y0> <x1> <y1>
    ref 可以是 'm'（母版）或另一个 name（用 al_<name>.png 作为参考）

输入:  parts/gen/<name>.png      （模型原始输出）
输出:  parts/gen/al_<name>.png   （配准到母版坐标）
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
GEN = ROOT / "parts" / "gen"
MASTER = ROOT / "03-master-d01-1086x1448.png"
CANVAS = (1086, 1448)


def load(p):
    return np.asarray(Image.open(p).convert("RGBA"))


def sift_register(ref, cur):
    import cv2
    g1 = cv2.cvtColor(ref[..., :3].astype(np.uint8), cv2.COLOR_RGB2GRAY)
    g2 = cv2.cvtColor(cur[..., :3].astype(np.uint8), cv2.COLOR_RGB2GRAY)
    sift = cv2.SIFT_create(4000)
    k1, d1 = sift.detectAndCompute(g1, None)
    k2, d2 = sift.detectAndCompute(g2, None)
    if d1 is None or d2 is None or len(k1) < 10 or len(k2) < 10:
        return None
    bf = cv2.BFMatcher()
    good = []
    for m, n in bf.knnMatch(d2, d1, k=2):          # cur -> ref
        if m.distance < 0.75 * n.distance:
            good.append(m)
    if len(good) < 12:
        print(f"    SIFT 匹配点只有 {len(good)} 个，跳过粗对")
        return None
    src = np.float32([k2[m.queryIdx].pt for m in good])
    dst = np.float32([k1[m.trainIdx].pt for m in good])
    M, mask = cv2.estimateAffinePartial2D(src, dst, method=cv2.RANSAC,
                                          ransacReprojThreshold=4.0)
    if M is None:
        return None
    inl = int(mask.sum()) if mask is not None else 0
    print(f"    SIFT 粗对: {len(good)} 匹配 / {inl} 内点")
    return M.astype(np.float32)


def eec_register(ref, cur, roi):
    import cv2
    x0, y0, x1, y1 = roi
    a = np.clip(ref[y0:y1, x0:x1, :3].mean(2) / 255.0, 0, 1).astype(np.float32)
    b = np.clip(cur[y0:y1, x0:x1, :3].mean(2) / 255.0, 0, 1).astype(np.float32)
    warp = np.eye(2, 3, dtype=np.float32)
    crit = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 500, 1e-6)
    try:
        _, warp = cv2.findTransformECC(a, b, warp, cv2.MOTION_AFFINE, crit, None, 5)
    except cv2.error as e:
        print(f"    ECC 失败（{e}），按原样返回")
    return warp


def apply_warp(img, warp, out_size):
    import cv2
    h, w = out_size
    return cv2.warpAffine(img, warp, (w, h), flags=cv2.INTER_LINEAR,
                          borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))


def main():
    if len(sys.argv) != 7:
        print(__doc__)
        return 1
    name, ref_name = sys.argv[1], sys.argv[2]
    roi = tuple(int(v) for v in sys.argv[3:7])

    GEN.mkdir(parents=True, exist_ok=True)
    ref_path = MASTER if ref_name == "m" else GEN / f"al_{ref_name}.png"
    raw_path = GEN / f"{name}.png"
    if not ref_path.exists():
        print(f"参考 {ref_path} 不存在")
        return 1
    if not raw_path.exists():
        print(f"缺少模型输出 {raw_path}")
        return 1

    A = load(ref_path)
    raw_img = Image.open(raw_path)
    B = load(raw_path)
    print(f"{name} <- {ref_name}   参考 {A.shape[1]}x{A.shape[0]}  编辑 {B.shape[1]}x{B.shape[0]}")

    target = (A.shape[0], A.shape[1])
    warp = sift_register(A, B)
    if warp is not None:
        B = apply_warp(B, warp, target)
    warp2 = eec_register(A, B, roi)
    B = apply_warp(B, warp2, target)

    out = GEN / f"al_{name}.png"
    Image.fromarray(B, "RGBA").save(out)

    warps_path = GEN / "warps.json"
    warps = json.loads(warps_path.read_text()) if warps_path.exists() else {}
    warps[name] = {"sift": warp.tolist() if warp is not None else None,
                   "ecc": warp2.tolist(), "roi": list(roi)}
    warps_path.write_text(json.dumps(warps, indent=1))

    # 置信度：不该变的区域应该几乎不变
    inside = np.zeros(A.shape[:2], bool)
    x0, y0, x1, y1 = roi
    inside[y0:y1, x0:x1] = True
    d = np.abs(A[..., :3].astype(int) - B[..., :3].astype(int)).max(2)
    ok = inside & (A[..., 3] > 200) & (B[..., 3] > 200)
    if ok.any():
        print(f"    配准残差 mean={d[ok].mean():.1f} p95={np.percentile(d[ok], 95):.0f} "
              f">20 占 {100*(d[ok] > 20).mean():.1f}%")
    print(f"    -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
