# -*- coding: utf-8 -*-
"""从 v2 脸部裁图里取出「一对眼睛」，写成整画布透明贴图。

用法（仓库根目录）:
    .venv/Scripts/python.exe scripts/extract-eye-pair.py eye-pair-shy <生成图.png>

然后用 build-diagnostic.py 把 new-art/<name>.png 注册成零件（看 eye-pair-shy 那段），
并在 expression-face.js 的 eyeArt 变体列表里加上同名变体。

为什么要用「虹膜配对」而不是墨色：这张脸的长发也是深褐，用墨色做种子会把整张图
（实测 172562px）都选中；腮红又偏红。所以先用严判据取饱和红虹膜块，再按
「面积相近 + 水平分开 + 高度接近」配成一对，才稳定。

这是既有的 v2 表情管线（half / late / rest / love / dizzy / pinch 都是这么来的）：
输入一张 520x520 的脸部裁图与它对应的参考图，只保留两只眼睛所在的区域，
输出与母版同尺寸（1145x1374）的透明 PNG，其余全透明。

关键点：
  * 参考图 `standing-expression-reference.png` 是 520x520，对应母版上的
    (CROP_X, CROP_Y) 起的一块；这个偏移从 expression-contours.json 的
    「裁图内坐标 + 370/195」换算关系得到（历史记录里已实测确认）。
  * 眼睛区域用「参考图里本来就有的红虹膜 + 睫毛墨色」的膨胀框来定，
    不是手画多边形 —— 贴图自带的刘海碎片也在框内，与已验收的 v2 贴图一致。
"""
from pathlib import Path
import json
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"D:\Codex\Coopanion-Skin-Design")
ARTSRC = ROOT / "characters/atri-01/art-source"
PACK = ROOT / "scratch/candidates/atri-pure-components-01"
W, H = 1145, 1374
CROP_X, CROP_Y = 370, 195          # 520x520 裁图在母版上的左上角


def eye_mask(ref: np.ndarray) -> np.ndarray:
    """两只眼睛的掩码：以「饱和红虹膜」为种子，再膨胀包住眼睑与睫毛。

    不能用深褐墨色做种子 —— 这张脸的长发也是深褐，会整张被选中（实测 172562px，
    眼睛区域本来就只占约 3 万）。腮红同样是偏红的，所以按「两个最大且尺寸相近、
    左右分布」的块来挑，而不是按面积取前 N。
    """
    a = ref.astype(int)
    iris = ((a[..., 0] > 120) & (a[..., 1] < 105) & (a[..., 0] - a[..., 1] > 60)
            & (a[..., 2] > 70) & (a[..., 2] < 160))
    lab, n = ndimage.label(iris)
    if n == 0:
        raise SystemExit("no iris pixels")
    sizes = ndimage.sum(iris, lab, range(1, n + 1))
    objs = ndimage.find_objects(lab)
    cands = []
    for i in range(n):
        if sizes[i] < 200:
            continue
        sl = objs[i]
        cy = (sl[0].start + sl[0].stop) / 2
        cx = (sl[1].start + sl[1].stop) / 2
        cands.append((sizes[i], cx, cy, i))
    if len(cands) < 2:
        raise SystemExit(f"need 2 iris blobs, found {len(cands)}")
    # 两只眼：面积相近、水平分开、y 接近；腮红是单个横向长条，会被这两条筛掉
    cands.sort(key=lambda c: -c[0])
    best = None
    for i in range(len(cands)):
        for j in range(i + 1, len(cands)):
            s1, x1, y1, _ = cands[i]
            s2, x2, y2, _ = cands[j]
            if abs(x1 - x2) < 60:
                continue          # 太近，是同一只眼的两半
            if abs(y1 - y2) > 60:
                continue          # 高度差太大，不是一对
            ratio = min(s1, s2) / max(s1, s2)
            if ratio < 0.4:
                continue          # 面积差太多
            score = ratio
            if best is None or score > best[0]:
                best = (score, cands[i], cands[j])
    if best is None:
        raise SystemExit("could not pair two iris blobs")
    _, c1, c2 = best
    keep = (lab == c1[3] + 1) | (lab == c2[3] + 1)
    # 膨胀：包住眼睑、眼白、睫毛与一点点自带刘海（与已验收的 v2 贴图同量级）
    grown = ndimage.binary_dilation(keep, iterations=26)
    grown = ndimage.binary_fill_holes(grown)
    print(f"  iris pair: ({c1[1]:.0f},{c1[2]:.0f}) size={int(c1[0])}  /  "
          f"({c2[1]:.0f},{c2[2]:.0f}) size={int(c2[0])}")
    return grown


def build(name: str, src_png: Path, compare: bool = True):
    ref = np.asarray(Image.open(ARTSRC / "standing-expression-reference.png").convert("RGB"))
    gen = Image.open(src_png).convert("RGB").resize((ref.shape[1], ref.shape[0]), Image.LANCZOS)
    g = np.asarray(gen)

    m = eye_mask(ref)
    ys, xs = np.nonzero(m)
    print(f"{name}: eye-region bbox in crop = ({xs.min()},{ys.min()})-({xs.max()},{ys.max()}), "
          f"{int(m.sum())} px")

    # 放到整画布
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    patch = Image.fromarray(g, "RGB").convert("RGBA")
    alpha = Image.fromarray((m * 255).astype(np.uint8), "L")
    patch.putalpha(alpha)
    canvas.paste(patch, (CROP_X, CROP_Y))

    out = PACK / "tex" / f"{name}.png"
    canvas.save(out)
    print(f"  wrote {out.relative_to(ROOT)}")

    # 校验：alpha 连通块应为 2（一对眼），不应有零散孤点
    a = np.asarray(canvas)
    lab, n = ndimage.label(a[..., 3] > 8)
    sizes = sorted(ndimage.sum(a[..., 3] > 8, lab, range(1, n + 1)), reverse=True)
    big = [int(s) for s in sizes if s > 200]
    print(f"  alpha blobs >200px: {len(big)} sizes={big[:4]}  (want 2)")
    return out


if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "eye-pair-shy"
    src = Path(sys.argv[2]) if len(sys.argv) > 2 else ARTSRC / "standing-eyes-shy-v2.png"
    build(name, src)
