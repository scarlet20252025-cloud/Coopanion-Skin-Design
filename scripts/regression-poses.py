# -*- coding: utf-8 -*-
"""全表情 x 双姿态回归截图（改坐姿/站姿表情后必跑）。

用法（仓库根目录，先确保 8765 预览服务在跑，见 scripts/start-preview.ps1）:

    .\.venv\Scripts\python.exe scriptsegression-poses.py

产物在 scratch/fx-probe/full-regression/:
    stand-*.png / sit-*.png   每个表情每姿态一张
    report.txt               每张图的虹膜/唇色像素计数，有 NO-IRIS? / MISSING 就是要查的
    full-regression.png      20 行 x 2 列的对照总表（另有 -1 / -2 两半）

为什么需要它：2026-10-24 那次修坐姿时，偏移量被当成绝对坐标，导致所有嘴画到画布原点。
站立时偏移全为 0 完全看不出来，只有坐下才暴露。所以**双姿态必须各跑一遍**。

判据（report.txt）:
    iris > 200   虹膜在（眼睛至少有一张图片在显示）
    lip  > 0     有唇色像素（嘴没被画到画布外）
"""

每个表情在站立与坐姿各截一张，用虹膜定位裁出脸部，拼成对照表，并顺手做两项机器检查：
  * 嘴的位置是否落在脸内（防止再次出现「嘴画到画布原点」那类坐标 bug）；
  * 眼睛图像是否至少有一张在显示（防止某表情整体不显示眼睛）。
检查结果同时写进 report.txt，便于 grep。
"""
import subprocess
import urllib.parse
import pathlib
import sys
import time

import numpy as np
from PIL import Image, ImageDraw

sys.stdout.reconfigure(encoding="utf-8")

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
ROOT = pathlib.Path(r"D:\Codex\Coopanion-Skin-Design")
OUT = ROOT / "scratch/fx-probe/full-regression"
OUT.mkdir(parents=True, exist_ok=True)
PACK = "scratch/candidates/atri-pure-components-01"

FACES = [
    ("pingjing", "平静"), ("kaixin", "开心"), ("zhayan", "眨眼"), ("xihuan", "喜欢"),
    ("haixiu", "害羞"), ("jingya", "惊讶"), ("shengqi", "生气"), ("nanguo", "难过"),
    ("deyi", "得意"), ("danxin", "担心"), ("huangzhang", "慌张"), ("haipa", "害怕"),
    ("qidai", "期待"), ("yihuo", "疑惑"), ("fankun", "犯困"), ("sikao", "思考"),
    ("dzu", "嘟嘴"), ("renzhen", "认真"), ("daku", "大哭"), ("yunhu", "晕乎"),
]

# 每个姿势的脸部取景框（已在前几轮实测确认）
FACE_BOX = {"stand": (395, 395, 705, 625), "sit": (395, 535, 705, 765)}


def shoot(pose, zh, tag):
    w = urllib.parse.quote(zh)
    url = (f"http://127.0.0.1:8765/preview/pose-check.html?pack={PACK}"
           f"&pose={pose}&word={w}&faceonly=1&cb={pose}-{tag}-{int(time.time()*1000)}")
    out = OUT / f"{pose}-{tag}.png"
    out.unlink(missing_ok=True)
    for _ in range(3):
        subprocess.run([EDGE, "--headless", "--disable-gpu", "--window-size=1000,1000",
                        "--virtual-time-budget=13000", f"--screenshot={out}", url],
                       capture_output=True, timeout=180)
        if out.exists() and out.stat().st_size > 20000:
            return out
        time.sleep(2)
    return out


def probe(p):
    """粗检查：画面里是否有偏红的虹膜像素、是否有偏红的唇色像素。"""
    a = np.asarray(Image.open(p).convert("RGB")).astype(int)
    iris = ((a[..., 0] > 115) & (a[..., 0] < 215) & (a[..., 0] - a[..., 1] > 40)
            & (a[..., 2] < 140) & (a[..., 2] > 60))
    lip = ((a[..., 0] > 130) & (a[..., 0] < 210) & (a[..., 1] > 60) & (a[..., 1] < 135)
           & (a[..., 2] > 60) & (a[..., 2] < 140) & (a[..., 0] - a[..., 1] > 28))
    return int(iris.sum()), int(lip.sum())


rows, report = [], []
for tag, zh in FACES:
    pair = {}
    for pose in ("stand", "sit"):
        p = shoot(pose, zh, tag)
        if not p.exists():
            report.append(f"MISSING {zh} {pose}")
            pair[pose] = None
            continue
        iris, lip = probe(p)
        pair[pose] = p
        report.append(f"{zh:4s} {pose:5s} iris={iris:5d} lip={lip:5d} {'OK' if iris > 200 else 'NO-IRIS?'}")
    if pair.get("stand") and pair.get("sit"):
        row = []
        for pose in ("stand", "sit"):
            im = Image.open(pair[pose]).convert("RGB")
            c = im.crop(FACE_BOX[pose])
            row.append(c.resize((c.width*3, c.height*3), Image.LANCZOS))
        rows.append((zh, row))

(OUT / "report.txt").write_text("\n".join(report) + "\n", encoding="utf-8")

if not rows:
    sys.exit("no rows")

w = max(r[1][0].width for r in rows)
h = max(r[1][0].height for r in rows)
label_w = 92
cols = 2
sheet = Image.new("RGB", (label_w + w*cols, (h+22)*len(rows)), (252, 250, 254))
d = ImageDraw.Draw(sheet)
for i, (zh, imgs) in enumerate(rows):
    y = i*(h+22)
    d.rectangle([0, y, label_w-1, y+h+21], fill=(40, 36, 52))
    d.text((14, y+h//2), zh, fill=(255, 255, 255))
    for k, im in enumerate(imgs):
        sheet.paste(im, (label_w + k*w, y+22))
    d.rectangle([label_w, y, label_w+w*cols-1, y+20], fill=(120, 112, 140))
    d.text((label_w+8, y+5), "STANDING", fill=(255, 255, 255))
    d.text((label_w+w+8, y+5), "SEATED", fill=(255, 255, 255))

dest = OUT / "full-regression.png"
sheet.save(dest)
print("saved", dest, sheet.size)
half = (len(rows)+1)//2
for k in range(2):
    sheet.crop((0, k*half*(h+22), sheet.width, min(sheet.height, (k+1)*half*(h+22)))).save(
        OUT / f"full-regression-{k+1}.png")
    print(f"part {k+1} written")
