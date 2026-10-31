"""Where is the character, really, at each sample time.

pet 区的 ink 在部分时刻只有 0.015，正常时刻是 0.15。要么角色被移出构图，
要么被嵌套 svg 的 viewBox 裁掉了。这个脚本同时给出 layout 和真实 bbox。

用法:
    python promo/diagnose-atri-pet.py
    python promo/diagnose-atri-pet.py --times 6,20,25,31.5
"""
from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

URL = "http://127.0.0.1:4319/promo/assets/src/02-atri/atri-film.html"


def main():
    from playwright.sync_api import sync_playwright

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--url", default=URL)
    ap.add_argument("--browser", default=r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
    ap.add_argument("--times", default="6,16,20,22.5,25,28,31.5,35")
    ap.add_argument("--out", default="promo/assets/qa/atri-pet-diag.json")
    args = ap.parse_args()

    times = [float(t) for t in args.times.split(",")]
    report = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=args.browser)
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        page.goto(args.url)
        page.wait_for_function("window.promoReady === true", timeout=90000)
        page.evaluate("document.fonts.ready")
        page.evaluate("() => {for(const a of document.getAnimations())a.pause()}")

        for t in times:
            page.evaluate("async t => {await window.renderAt(t)}", t)
            info = page.evaluate(
                """() => {
                  const st = window.promoState || {};
                  const mount = document.getElementById('petMount');
                  const frame = document.getElementById('petFrame');
                  const g = mount.querySelector('g');
                  let innerBBox = null;
                  try { const b = mount.getBBox(); innerBBox = [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)]; } catch(e) { innerBBox = 'fail'; }
                  let gBox = null;
                  if (g) { const b = g.getBoundingClientRect(); gBox = [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)]; }
                  const mr = mount.getBoundingClientRect();
                  const fr = frame.getBoundingClientRect();
                  return {
                    layout: st.layout ? {x: st.layout.x, facing: st.layout.facing, mode: st.layout.mode, box: st.layout.box} : null,
                    visual: st.visual || null,
                    mountRect: [Math.round(mr.x), Math.round(mr.y), Math.round(mr.width), Math.round(mr.height)],
                    frameRect: [Math.round(fr.x), Math.round(fr.y), Math.round(fr.width), Math.round(fr.height)],
                    innerBBox, gBox,
                    mountOverflow: getComputedStyle(mount).overflow,
                    frameTransform: frame.getAttribute('transform'),
                    childCount: mount.children.length,
                  };
                }"""
            )
            report[f"{t:.2f}"] = info
            lay = info["layout"] or {}
            print(f"t={t:5.1f} mode={str(lay.get('mode')):10s} x={lay.get('x')} box={lay.get('box')}")
            print(f"        mountRect={info['mountRect']} frameRect={info['frameRect']}")
            print(f"        innerBBox={info['innerBBox']} gBox={info['gBox']} overflow={info['mountOverflow']} kids={info['childCount']}")

        browser.close()

    out = ROOT / args.out
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\nwritten {out}")


if __name__ == "__main__":
    main()
