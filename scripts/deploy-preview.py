# -*- coding: utf-8 -*-
"""Publish the ATRI preview site to the `gh-pages` branch.

Why a separate branch instead of `/docs`: the repository is public and already 186 MB. GitHub Pages
rejects sites over 1 GB and serves everything under the chosen directory, so pointing Pages at the
repo root or /docs would publish the whole project (all packs, all iteration art). `gh-pages` carries
only what the preview page actually needs:

    index.html                 landing page -> engineering.html?pack=packs/<id>
    preview/engineering.html   the stage
    preview/engineering.js
    preview/pose-check.html    single-expression / single-pose viewer used for审查
    preview/vendor/            the kit the page imports
    packs/<id>/                one candidate pack (manifest + model + figure.js + tex)

Usage (from the repo root):

    .venv/Scripts/python.exe scripts/deploy-preview.py              # publish packs/atri-v011
    .venv/Scripts/python.exe scripts/deploy-preview.py atri-v012    # publish another pack

The pack must already exist under packs/. The script writes to a temporary worktree of the
`gh-pages` branch, commits, and pushes. It never touches the working tree of `main`.
"""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
BRANCH = "gh-pages"
DEFAULT_PACK = "atri-v011"

# Files the preview page needs, relative to the repo root.
PREVIEW_FILES = [
    "preview/engineering.html",
    "preview/engineering.js",
    "preview/pose-check.html",
]
PREVIEW_DIRS = ["preview/vendor"]

INDEX = """<!doctype html><meta charset="utf-8">
<title>ATRI 桌宠 · 预览</title>
<style>
 body{{margin:0;background:#f3f0f8;color:#4c415c;font:15px/1.7 system-ui,'Microsoft YaHei'}}
 main{{max-width:760px;padding:28px;margin:auto}}
 h1{{font-size:22px;margin:0 0 6px}}
 p.sub{{color:#6b5f7d;margin:0 0 22px}}
 a.card{{display:block;padding:16px 18px;margin:10px 0;border:1px solid #c7b5dc;border-radius:10px;
   background:#fcfaff;text-decoration:none;color:inherit}}
 a.card:hover{{border-color:#9b7fc4;background:#f7f2ff}}
 .t{{font-weight:600}}
 .d{{color:#6b5f7d;font-size:13px}}
 code{{background:#efe9f7;padding:1px 5px;border-radius:4px;font-size:13px}}
</style>
<main>
 <h1>ATRI 桌宠 · 预览</h1>
 <p class="sub">包 <code>{pack}</code> · 由 <code>scripts/deploy-preview.py</code> 发布</p>

 <a class="card" href="preview/engineering.html?pack=packs/{pack}">
   <div class="t">工程预览（站姿 / 坐姿 / 动作 / 表情）</div>
   <div class="d">按钮点表情，鼠标移入画面触发动作；「复位」「切换朝向」「深浅背景」可切换显示</div>
 </a>

 <a class="card" href="preview/pose-check.html?pack=packs/{pack}">
   <div class="t">表情核查（单表情定格）</div>
   <div class="d">加 <code>&amp;pose=sit</code> 看坐姿，<code>&amp;word=害羞</code> 锁定某个表情</div>
 </a>

 <a class="card" href="preview/pose-check.html?pack=packs/{pack}&amp;pose=sit&amp;word=害羞">
   <div class="t">坐姿 · 害羞（直达）</div>
   <div class="d">当前版本已修好：半睁眼 + 腮红加深 + 歪头 2°，坐姿五官与脸对齐</div>
 </a>
</main>
"""


def git(*args, cwd=None, check=True):
    r = subprocess.run(["git", *args], cwd=cwd or ROOT, capture_output=True, text=True)
    if check and r.returncode != 0:
        sys.exit(f"git {' '.join(args)} failed:\n{r.stdout}\n{r.stderr}")
    return r.stdout.strip()


def branch_exists(name):
    return bool(git("ls-remote", "--heads", "origin", name))


def main():
    pack = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PACK
    src = ROOT / "packs" / pack
    if not src.is_dir():
        sys.exit(f"pack not found: {src}\nCopy the candidate into packs/ first.")

    missing = [f for f in PREVIEW_FILES if not (ROOT / f).exists()]
    missing += [d for d in PREVIEW_DIRS if not (ROOT / d).is_dir()]
    if missing:
        sys.exit("missing preview sources: " + ", ".join(missing))

    work = Path(tempfile.mkdtemp(prefix="atri-pages-"))
    try:
        has = branch_exists(BRANCH)
        if has:
            git("worktree", "add", "-f", str(work), BRANCH)
            git("fetch", "origin", BRANCH, cwd=work)
            git("reset", "--hard", f"origin/{BRANCH}", cwd=work)
        else:
            git("worktree", "add", "-f", "--orphan", "-b", BRANCH, str(work))

        # clean the tracked content of the worktree, keep .git plumbing
        for item in work.iterdir():
            if item.name == ".git":
                continue
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()

        for f in PREVIEW_FILES:
            dst = work / f
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / f, dst)
        for d in PREVIEW_DIRS:
            shutil.copytree(ROOT / d, work / d)

        dst_pack = work / "packs" / pack
        shutil.copytree(src, dst_pack)
        # the pack README/VERSION notes are fine to publish; drop nothing.

        (work / "index.html").write_text(INDEX.format(pack=pack), encoding="utf-8")
        # GitHub Pages runs Jekyll by default; skip it so paths with dots parse verbatim
        (work / ".nojekyll").write_text("", encoding="utf-8")

        total = sum(f.stat().st_size for f in work.rglob("*") if f.is_file())
        print(f"staged {len(list(work.rglob('*')))} entries, {total/1024/1024:.1f} MB")

        git("add", "-A", cwd=work)
        msg = f"Publish ATRI preview: {pack}"
        r = subprocess.run(["git", "commit", "-q", "-m", msg], cwd=work, capture_output=True, text=True)
        if r.returncode != 0 and "nothing to commit" not in (r.stdout + r.stderr):
            sys.exit(f"commit failed:\n{r.stdout}\n{r.stderr}")
        git("-c", "http.version=HTTP/1.1", "push", "-f", "origin", BRANCH, cwd=work)
        print(f"pushed {BRANCH}")
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", str(work)],
                       cwd=ROOT, capture_output=True)
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
