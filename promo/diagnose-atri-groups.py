"""Probe every scene group's real paint state at the sample times.

DOM 说 opacity=1、截图说没有像素，这类矛盾不能靠推理，只能取证：
对每个采样时刻，把每个场景组的 style.opacity / 计算样式 / getBBox / 屏幕矩形
一起打出来，看是谁在撒谎。

用法:
    python promo/diagnose-atri-groups.py                 # 默认 6 个时间点
    python promo/diagnose-atri-groups.py --times 20,31.5,35
"""
from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

URL = "http://127.0.0.1:4319/promo/assets/src/02-atri/atri-film.html"
GROUPS = ["intro", "talk", "touch", "actions", "radish", "seated", "outro"]


def main():
    from playwright.sync_api import sync_playwright

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--url", default=URL)
    ap.add_argument("--browser", default=r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
    ap.add_argument("--times", default="2,16,20,25,31.5,35")
    ap.add_argument("--shot-dir", default="scratch/diag")
    args = ap.parse_args()

    times = [float(t) for t in args.times.split(",")]
    shot_dir = (ROOT / args.shot_dir)
    shot_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=args.browser)
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        page.goto(args.url)
        page.wait_for_function("window.promoReady === true", timeout=90000)
        page.evaluate("document.fonts.ready")
        page.evaluate("() => {for(const a of document.getAnimations())a.pause()}")

        report = {}
        for t in times:
            page.evaluate("async t => {await window.renderAt(t)}", t)
            info = page.evaluate(
                """(groups) => {
                  const out = {};
                  for (const id of groups) {
                    const e = document.getElementById(id);
                    if (!e) { out[id] = {missing: true}; continue; }
                    const cs = getComputedStyle(e);
                    let bb = null;
                    try { const b = e.getBBox(); bb = [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)]; } catch (err) { bb = 'getBBox failed'; }
                    const r = e.getBoundingClientRect();
                    out[id] = {
                      attrOp: e.getAttribute('opacity'),
                      styleOp: e.style.opacity,
                      compOp: cs.opacity,
                      display: cs.display,
                      vis: cs.visibility,
                      transform: e.getAttribute('transform'),
                      bbox: bb,
                      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
                      childCount: e.children.length,
                    };
                  }
                  // 画布根部的实际可见范围
                  const svg = document.getElementById('film');
                  const sb = svg.getBoundingClientRect();
                  const lastChild = svg.lastElementChild;
                  return {
                    groups: out,
                    svgRect: [Math.round(sb.x), Math.round(sb.y), Math.round(sb.width), Math.round(sb.height)],
                    lastChildTag: lastChild ? lastChild.tagName + '#' + (lastChild.id || '') : null,
                    outroTitleBox: (() => {
                      const o = document.getElementById('outro');
                      const tt = o && o.querySelector('text.title');
                      if (!tt) return null;
                      const b = tt.getBoundingClientRect();
                      const el = document.elementFromPoint(b.x + b.width / 2, b.y + b.height / 2);
                      return {
                        box: [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)],
                        topElement: el ? el.tagName + '#' + (el.id || '') + '.' + (el.getAttribute('class') || '') : 'none',
                        fill: getComputedStyle(tt).fill,
                      };
                    })(),
                  };
                }""",
                GROUPS,
            )
            page.screenshot(path=str(shot_dir / f"diag-{t:05.2f}.png"))
            report[f"{t:.2f}"] = info

            print(f"\n===== t={t} =====")
            for gid, g in info["groups"].items():
                if g.get("missing"):
                    print(f"  {gid:8s} MISSING")
                    continue
                print(f"  {gid:8s} styleOp={g['styleOp'] or '-':>6s} compOp={g['compOp']:>5s} "
                      f"bbox={g['bbox']} rect={g['rect']} kids={g['childCount']}")
            ot = info.get("outroTitleBox")
            if ot:
                print(f"  outro .title box={ot['box']} top={ot['topElement']} fill={ot['fill']}")
            print(f"  svg lastChild={info['lastChildTag']}")

        browser.close()

    out = ROOT / "promo/assets/qa/atri-group-diag.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\nwritten {out}")


if __name__ == "__main__":
    main()
