"""Render the ATRI promotional film from this repository's isolated SVG page.

同一套管线，只换了来源页与默认输出：逐帧截图 -> FFmpeg 编码 -> 全片解码校验。
只操作本地 127.0.0.1 的离线电影页，不驱动用户真实浏览器会话。

用法:
    python promo/render-atri.py --ffmpeg "C:/Program Files/Virtual Desktop Streamer/ffmpeg.exe" \
        --browser "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe" \
        --samples 1.5,6,12,16,23,28
    python promo/render-atri.py ... --music promo/assets/atri-music.wav --out "promo/assets/亚托利宣传片.mp4"
"""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DEFAULT_URL = "http://127.0.0.1:4319/promo/assets/src/02-atri/atri-film.html"
DEFAULT_OUT = "promo/assets/亚托利宣传片.mp4"


def main():
    from playwright.sync_api import sync_playwright

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--browser", help="Existing browser executable; otherwise installed Chromium")
    parser.add_argument("--ffmpeg", default=shutil.which("ffmpeg"))
    parser.add_argument("--out", default=DEFAULT_OUT)
    parser.add_argument("--music", help="Authorized optional WAV/music file")
    parser.add_argument("--duration", type=float, default=36)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--samples", help="Comma-separated key-frame times; no encoding")
    args = parser.parse_args()

    if urlparse(args.url).hostname not in ["127.0.0.1", "localhost"]:
        parser.error("Only an isolated localhost movie page is supported")
    if not 0 < args.duration <= 60 or not 1 <= args.fps <= 60:
        parser.error("Use duration (0,60] and fps [1,60]")
    out = (ROOT / args.out).resolve()
    if not out.is_relative_to(ROOT):
        parser.error("Output must stay in this repository")
    if not args.samples and not args.ffmpeg:
        parser.error("Supply --ffmpeg or add it to PATH")

    out.parent.mkdir(parents=True, exist_ok=True)
    qa = out.parent / "qa"
    qa.mkdir(exist_ok=True)

    times = (
        [float(t) for t in args.samples.split(",")]
        if args.samples
        else [i / args.fps for i in range(round(args.duration * args.fps))]
    )
    if not times or any(not 0 <= t < args.duration for t in times):
        parser.error(f"Frame times must be in [0,{args.duration})")

    with tempfile.TemporaryDirectory(prefix=".render-atri-", dir=out.parent) as temporary:
        frames = Path(temporary)
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=args.browser)
            page = browser.new_page(viewport={"width": 1920, "height": 1080})
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.goto(args.url)
            page.wait_for_function("window.promoReady === true", timeout=90000)
            page.evaluate("document.fonts.ready")
            page.evaluate("() => {for(const a of document.getAnimations())a.pause()}")
            states = []
            for i, t in enumerate(times):
                page.evaluate(
                    "async t => {for(const a of document.getAnimations())a.currentTime=t*1000;"
                    "await window.renderAt(t)}",
                    t,
                )
                # 2026-10-31: 必须先让合成器刷两帧再截图。
                # 只改 setAttribute 是同步的 DOM 更新，但图层（filter / foreignObject / 渐变）
                # 要等一次 rAF 才重新合成；直接 screenshot 会拿到半合成甚至上一帧的画面，
                # 表现为"DOM 里文字明明可见、PNG 里却几乎没有像素"(t=35s 端帧 ink 0.0003)。
                page.evaluate(
                    "() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))"
                )
                target = qa / f"atri-sample-{t:05.2f}.png" if args.samples else frames / f"frame_{i:05d}.png"
                page.screenshot(path=str(target))
                if args.samples:
                    states.append(page.evaluate("window.promoState"))
                if (i + 1) % 30 == 0 or i + 1 == len(times):
                    print(f"frame {i+1}/{len(times)}", flush=True)
            final = page.evaluate("window.promoState")
            browser.close()

        if errors:
            raise RuntimeError("Movie page errors: " + " | ".join(errors))
        rejected = [c for c in final["checks"] if c["accepted"] is False]
        if rejected:
            raise RuntimeError(f"Movie action rejected: {rejected}")

        (qa / "atri-render-state.json").write_text(
            json.dumps(final, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        if args.samples:
            (qa / "atri-states.json").write_text(
                json.dumps(states, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            print("Samples ready; review character and text before encoding")
            return

        silent = frames / "silent.mp4"
        subprocess.run(
            [args.ffmpeg, "-y", "-v", "error", "-framerate", str(args.fps),
             "-i", str(frames / "frame_%05d.png"),
             "-c:v", "libx264", "-preset", "slow", "-crf", "16",
             "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(silent)],
            check=True,
        )
        if args.music:
            music = Path(args.music).resolve()
            subprocess.run(
                [args.ffmpeg, "-y", "-v", "error", "-i", str(silent), "-i", str(music),
                 "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
                 "-c:a", "aac", "-b:a", "160k",
                 "-af", "loudnorm=I=-24:TP=-3:LRA=7", "-ar", "48000",
                 "-t", str(args.duration), "-movflags", "+faststart",
                 "-metadata", "artist=Asryto", str(out)],
                check=True,
            )
        else:
            shutil.copy2(silent, out)

        subprocess.run([args.ffmpeg, "-v", "error", "-i", str(out), "-f", "null", "-"],
                       check=True, stdout=subprocess.DEVNULL)

        report = {
            "duration_seconds": args.duration,
            "frames": len(times),
            "fps": args.fps,
            "resolution": [1920, 1080],
            "bytes": out.stat().st_size,
            "sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
            "full_decode": "passed",
            "page_errors": errors,
            "visual_review": "required",
            "music": bool(args.music),
            "actions_checked": len(final["checks"]),
            "actions_accepted": sum(1 for c in final["checks"] if c["accepted"]),
            "source_pack": "packs/atri-v011",
        }
        (qa / "atri-video-validation.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(str(out))


if __name__ == "__main__":
    main()
