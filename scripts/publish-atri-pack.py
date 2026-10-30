# -*- coding: utf-8 -*-
"""Publish the built candidate into the shippable pack, then make it a valid Coopanion pack.

The pipeline has two directories and they must not drift apart:

    scratch/candidates/atri-pure-components-01     build-diagnostic.py writes here (gitignored)
    packs/atri-v011                               what gets installed / zipped

`packs/` is a copy, so a rebuild in scratch does NOT reach it on its own - that is how the pack
ended up shipping the old logo_scale while the preview showed the new one. This script is the only
supported way to move a build across, and it preserves the two files `packs/` owns:

    figure.json   hand-authored: name/about/axes/presets/sounds/can/vocab-about
    tex/thumb.png derived from the master, not from the candidate

Order matters: copy the build, then re-apply the manifest, then the vocab descriptions, then the
thumb, then validate and zip. Any other order silently loses one of them.

Usage:
    .venv/Scripts/python.exe scripts/publish-atri-pack.py [pack-dir-name]
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACK_NAME = sys.argv[1] if len(sys.argv) > 1 else "atri-v011"
PACK = ROOT / "packs" / PACK_NAME
BUILT = ROOT / "scratch/candidates/atri-pure-components-01"
PY = sys.executable

# what build-diagnostic.py produces; tex/ is merged rather than replaced so thumb.png survives
COPY_FILES = ["figure.js", "model.json", "part-registration.json", "EDGE-EXPORT.json",
              "EXPRESSION-PRESERVATION.json", "SOURCE.json", "figure.json", "README.md",
              "VERSION.md", "LICENSE", "UPSTREAM.json"]


def run(script, *args):
    # utf-8 explicitly: these scripts print Chinese and the console default here is GBK, which
    # raised UnicodeDecodeError on the first run
    r = subprocess.run([PY, str(ROOT / "scripts" / script), *args],
                       cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace",
                       env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    out = ((r.stdout or "") + (r.stderr or "")).strip()
    if r.returncode != 0:
        sys.exit(f"{script} failed:\n{out}")
    return out


def main():
    if not BUILT.is_dir():
        sys.exit(f"no build to publish: {BUILT}\nrun build-diagnostic.py first")
    PACK.mkdir(parents=True, exist_ok=True)

    # 1. copy the build (figure.json is overwritten here, then rewritten below - that is intended,
    #    the built one only carries preview fields)
    for name in COPY_FILES:
        src = BUILT / name
        if src.is_file():
            shutil.copy2(src, PACK / name)
    (PACK / "tex").mkdir(exist_ok=True)

    # 2026-10-31: textures the person edited by hand must survive a publish. The first version of
    # this script copied every scratch/tex/*.png over packs/tex/, which silently reverted the
    # hand-repaired left ponytail (md5 6ab6bf6a...) back to the old build output (ef57a84d...). build
    # output is authoritative only for textures nobody touched, so hand-edited names are listed here
    # and skipped, with the reason printed.
    HAND_EDITED = {
        "tail-left.png": "hand-repaired left ponytail (2026-10-30)",
    }
    n, kept = 0, []
    for f in sorted((BUILT / "tex").glob("*.png")):
        dst = PACK / "tex" / f.name
        if f.name in HAND_EDITED and dst.exists():
            kept.append(f.name)
            continue
        shutil.copy2(f, dst)
        n += 1
    # stale textures from an older build would still load by name and confuse a diff
    live = {f.name for f in (BUILT / "tex").glob("*.png")} | {"thumb.png"}
    removed = []
    for f in (PACK / "tex").glob("*.png"):
        if f.name not in live:
            f.unlink()
            removed.append(f.name)
    print(f"[publish] copied {n} textures" + (f", removed stale {removed}" if removed else ""))
    if kept:
        print("[publish] kept hand-edited: " + ", ".join(f"{k} ({HAND_EDITED[k]})" for k in kept))

    # 2-4. re-author the parts packs/ owns, in dependency order
    print("[publish] " + run("write-atri-manifest.py", PACK_NAME).splitlines()[-1])
    print("[publish] " + run("add-atri-vocab-about.py", PACK_NAME).splitlines()[-1])
    # --bust: the 装扮 card gets a portrait (head/bows/ponytail roots), not the whole body
    print("[publish] " + run("make-atri-thumb.py", PACK_NAME, "--size=512", "--bust").splitlines()[-1])

    # 5. validate + zip (this step never writes the manifest)
    for line in run("package-atri-pack.py", PACK_NAME).splitlines():
        print("[publish] " + line)

    # 6. state the two numbers that were wrong before, so the next run can see them change
    model = json.loads((PACK / "model.json").read_text(encoding="utf-8"))
    fig = json.loads((PACK / "figure.json").read_text(encoding="utf-8"))
    b = model["bounds"]
    print(f"[publish] logo_scale={model['logo_scale']:.6f} -> "
          f"{(b[3]-b[1])*model['logo_scale']/256*100:.1f}% of stage height")
    print(f"[publish] thumb={fig['thumb']}")


if __name__ == "__main__":
    main()
