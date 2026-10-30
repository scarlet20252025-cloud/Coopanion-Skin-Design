"""Pixel-level sanity checks for the ATRI film when no human eye is reviewing frames.

这台机器上的模型无法直接看图，所以用可量化的指标代替目视：
每帧是否非空白、角色区域是否真的有像素、文字区域是否有字形、各场景色调是否真的不同。

用法:
    python promo/check-atri-frames.py                     # 检查 assets/qa 下所有 atri-sample-*.png
    python promo/check-atri-frames.py --dir promo/assets/qa
    python promo/check-atri-frames.py --video "promo/assets/亚托利宣传片.mp4" --ffmpeg <ffmpeg>
"""
from pathlib import Path
import argparse
import json
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow required: pip install pillow")

# 场景判定区域（1920x1080）：左侧文案区、右侧角色区、底部进度区
ZONES = {
    "title": (100, 240, 900, 560),
    "body": (100, 560, 900, 760),
    "pet": (980, 120, 1760, 960),
    "footer": (100, 940, 1800, 1060),
}

# 画面必须达到的最小"有内容"比例（非背景色像素占比）
MIN_INK = {
    "title": 0.010,
    "body": 0.004,
    "pet": 0.060,
    "footer": 0.001,
}


def zone_stats(im, box):
    """返回该区域的信息量指标：均值亮度、标准差、与纯色的偏离度、边缘强度。"""
    crop = im.crop(box).convert("RGB")
    px = list(crop.getdata())
    n = len(px)
    if n == 0:
        return {"mean": 0.0, "std": 0.0, "ink": 0.0, "edge": 0.0}
    lum = [(r * 299 + g * 587 + b * 114) / 1000 for r, g, b in px]
    mean = sum(lum) / n
    var = sum((v - mean) ** 2 for v in lum) / n
    std = var ** 0.5
    # "ink" = 明显亮于或暗于背景的像素占比，背景是深海蓝（亮度约 20-40）
    ink = sum(1 for v in lum if v > 70 or v < 8) / n
    # 边缘强度：相邻像素亮度差的平均值，用来判断有没有字形/轮廓而不是一片纯色
    w, h = crop.size
    edge = 0.0
    if w > 1 and h > 1:
        tot = 0.0
        cnt = 0
        for y in range(0, h, 3):
            row = lum[y * w:(y + 1) * w]
            for x in range(1, w, 3):
                tot += abs(row[x] - row[x - 1])
                cnt += 1
        edge = tot / max(1, cnt)
    return {"mean": round(mean, 2), "std": round(std, 2), "ink": round(ink, 4), "edge": round(edge, 2)}


def check_file(path):
    im = Image.open(path)
    if im.size != (1920, 1080):
        return {"file": path.name, "ok": False, "reason": f"size {im.size}"}, {}
    results = {}
    failures = []
    for name, box in ZONES.items():
        st = zone_stats(im, box)
        results[name] = st
        if st["ink"] < MIN_INK[name]:
            failures.append(f"{name} ink={st['ink']} < {MIN_INK[name]}")
    # 整体不能是纯色（防止白屏/黑屏）
    whole = zone_stats(im, (0, 0, 1920, 1080))
    results["whole"] = whole
    if whole["std"] < 3.0:
        failures.append(f"frame looks flat (std={whole['std']})")
    return {"file": path.name, "ok": not failures, "reason": "; ".join(failures)}, results


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dir", default="promo/assets/qa")
    ap.add_argument("--pattern", default="atri-sample-*.png")
    ap.add_argument("--video")
    ap.add_argument("--ffmpeg")
    ap.add_argument("--times", default="1.5,6,12,16,23,28")
    ap.add_argument("--out", default="promo/assets/qa/atri-frame-checks.json")
    args = ap.parse_args()

    d = (ROOT / args.dir).resolve()
    files = sorted(d.glob(args.pattern))

    tmpdir = None
    if args.video:
        if not args.ffmpeg:
            sys.exit("--video needs --ffmpeg")
        tmpdir = tempfile.TemporaryDirectory(prefix=".frames-check-")
        for t in args.times.split(","):
            out = Path(tmpdir.name) / f"atri-sample-{float(t):05.2f}.png"
            subprocess.run(
                [args.ffmpeg, "-y", "-v", "error", "-ss", t,
                 "-i", str((ROOT / args.video).resolve()), "-frames:v", "1", str(out)],
                check=True,
            )
        files = sorted(Path(tmpdir.name).glob("atri-sample-*.png"))

    if not files:
        sys.exit(f"no frames matched {d / args.pattern}")

    report = []
    for f in files:
        res, zones = check_file(f)
        res["zones"] = zones
        report.append(res)
        mark = "OK  " if res["ok"] else "FAIL"
        print(f"{mark} {res['file']}  " + ("" if res["ok"] else res["reason"]))
        if zones:
            t = zones.get("title", {})
            p = zones.get("pet", {})
            print(f"       title ink={t.get('ink')} edge={t.get('edge')}  "
                  f"pet ink={p.get('ink')} edge={p.get('edge')}  whole std={zones.get('whole', {}).get('std')}")

    # 场景差异性：任意两帧的角色区与标题区不应完全一致，否则说明场景没切换
    print("\n--- 场景差异（相邻采样帧的 pet 区 ink 差值应 >0.002 或 mean 差值 >1.5）---")
    diffs = []
    for a, b in zip(report, report[1:]):
        pa = a["zones"].get("pet", {})
        pb = b["zones"].get("pet", {})
        da = abs(pa.get("ink", 0) - pb.get("ink", 0))
        dm = abs(pa.get("mean", 0) - pb.get("mean", 0))
        changed = da > 0.002 or dm > 1.5
        diffs.append({"a": a["file"], "b": b["file"], "ink_delta": round(da, 4), "mean_delta": round(dm, 2), "changed": changed})
        print(f"{'OK  ' if changed else 'WARN'} {a['file']} -> {b['file']}  inkΔ={da:.4f} meanΔ={dm:.2f}")

    ok = all(r["ok"] for r in report) and all(dd["changed"] for dd in diffs if dd)
    out = (ROOT / args.out)
    out.write_text(json.dumps({"frames": report, "scene_diffs": diffs, "all_ok": ok},
                              ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\n{'ALL OK' if ok else 'PROBLEMS FOUND'}  ->  {out}")
    if tmpdir:
        tmpdir.cleanup()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
