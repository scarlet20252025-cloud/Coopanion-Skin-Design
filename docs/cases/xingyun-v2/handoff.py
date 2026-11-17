"""Archive the Xingyun 0.1.9 engineering tree and replay its release build."""
import argparse
from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
from uuid import uuid4
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile


PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT.parent
RELEASE = "xingyun-v2-0.1.9.zip"
ENGINEERING = "xingyun-v2-0.1.9-engineering.zip"
SUMS = "SHA256SUMS.txt"
PROJECTS = (
    "xingyun-v2", "xingyun-prep", "xingyun-arm-pass", "xingyun-right-pass",
    "xingyun-head-pass", "xingyun-rig", "xingyun-chibi", "xingyun-handoff-20261116",
)
STAR = "official03-rebuild"
WHALE = "whale-kit/whale-coopanion-repro-kit/assets/shipped/preview-pkg/web/whale"
REFERENCES = (
    f"{STAR}/handoff-20261106/00-README-文件地图与日常操作.md",
    f"{STAR}/handoff-20261106/01-经验总结与避坑.md",
    f"{STAR}/handoff-20261106/02-figure.js-changes.diff",
    f"{STAR}/parts/check/stool-r02-sit-composite.png",
    f"{STAR}/preview/web/whale/figure.js",
    f"{STAR}/preview/web/whale/expreface/face_drag.png",
    f"{STAR}/preview/web/whale/feat/drag_eyeL.png",
    f"{STAR}/preview/web/whale/feat/drag_eyeR.png",
    f"{STAR}/preview/web/whale/feat/drag_mouth.png",
    f"{STAR}/preview/web/whale/tex/sit_body.png",
    f"{WHALE}/figure.js",
    f"{WHALE}/figure.json",
    f"{WHALE}/model.json",
)
SKIP_DIRS = {".git", "__pycache__", "review-generated", "preview-export", "reproduced"}
SKIP_SUFFIXES = {".log", ".pyc", ".pending", ".expression-pending"}
COMPRESSED = {".png", ".gif", ".jpg", ".jpeg", ".webp", ".zip"}
LANDING = """# 星云 0.1.9 工程交接

先看[解压与复现步骤](xingyun-v2/交接包复现说明.md)和[完整制作手册](xingyun-v2/星云桌宠工程全流程手册.md)。

[Coopanion 正式导入包](xingyun-v2/xingyun-v2-0.1.9.zip)和 [SHA256SUMS.txt](SHA256SUMS.txt) 也在交接包内。
"""


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


@contextmanager
def staging_dir(parent, prefix):
    base = parent.resolve(strict=True)
    staging = base / (prefix + uuid4().hex)
    staging.mkdir()
    try:
        yield staging
    finally:
        resolved = staging.resolve()
        if resolved != staging or resolved.parent != base:
            raise ValueError(f"Staging path changed: {staging}")
        shutil.rmtree(resolved)


def inputs():
    for project in PROJECTS:
        source = ROOT / project
        if not source.is_dir():
            raise FileNotFoundError(source)
        for folder, dirs, files in os.walk(source):
            dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not d.startswith("."))
            for name in sorted(files):
                path = Path(folder) / name
                if name.startswith(".") or name == "Thumbs.db" or path.suffix.lower() in SKIP_SUFFIXES:
                    continue
                yield path
    for name in REFERENCES:
        yield ROOT / name


def archive(target):
    target = target.resolve()
    checksum = target.with_suffix(".zip.sha256")
    if target.exists() or checksum.exists():
        raise FileExistsError(target if target.exists() else checksum)
    if any(target.is_relative_to(ROOT / name) for name in PROJECTS):
        raise ValueError("Use an output path outside the project folders.")
    target.parent.mkdir(parents=True, exist_ok=True)
    records = {"00-先读这里.md": hashlib.sha256(LANDING.encode()).hexdigest()}
    with staging_dir(target.parent, "xingyun-handoff-") as temp:
        staged = temp / target.name
        with ZipFile(staged, "w", ZIP_DEFLATED, compresslevel=6) as pack:
            pack.writestr("00-先读这里.md", LANDING)
            for path in inputs():
                name = path.relative_to(ROOT).as_posix()
                method = ZIP_STORED if path.suffix.lower() in COMPRESSED else ZIP_DEFLATED
                pack.write(path, name, compress_type=method)
                records[name] = digest(path)
            pack.writestr(SUMS, "".join(f"{sha}  {name}\n" for name, sha in records.items()))
        with ZipFile(staged) as pack:
            if set(pack.namelist()) != {*records, SUMS} or pack.testzip() is not None:
                raise ValueError("Archive contents or CRC check failed.")
            for name, sha in records.items():
                with pack.open(name) as stream:
                    if hashlib.file_digest(stream, "sha256").hexdigest() != sha:
                        raise ValueError(f"Archive entry differs from its source: {name}")
        staged.rename(target)
    checksum.write_text(f"{digest(target)}  {target.name}\n", encoding="utf-8")
    print(f"{target}: {len(records)} files plus {SUMS}; {target.stat().st_size:,} bytes")


def verify():
    lines = (ROOT / SUMS).read_text(encoding="utf-8").splitlines()
    for line in lines:
        expected, name = line.split("  ", 1)
        path = (ROOT / name).resolve()
        if not path.is_relative_to(ROOT) or not path.is_file() or digest(path) != expected:
            raise ValueError(f"Missing, changed or invalid archive entry: {name}")
    print(f"{len(lines)} extracted files match {SUMS}.")


def compare_release(reference, rebuilt):
    with ZipFile(reference) as original, ZipFile(rebuilt) as generated:
        names = original.namelist()
        if set(names) != set(generated.namelist()) or len(names) != len(generated.namelist()):
            raise ValueError("Release file list differs.")
        if original.testzip() is not None or generated.testzip() is not None:
            raise ValueError("Release CRC check failed.")
        different = [name for name in names if original.read(name) != generated.read(name)]
        if different:
            raise ValueError("Release contents differ: " + ", ".join(different))
    return len(names)


def rebuild(out_dir):
    target = out_dir.resolve() / RELEASE
    if target.exists():
        raise FileExistsError(target)
    reference = PROJECT / RELEASE
    target.parent.mkdir(parents=True, exist_ok=True)
    with staging_dir(target.parent, "xingyun-rebuild-") as work:
        shutil.copytree(PROJECT / "parts", work / "parts", ignore=shutil.ignore_patterns(".*", "*.expression-pending"))
        seeds = (
            "build.py", "assemble.py", "face_registration.py", "work/pre-brows-face.png",
            "pack/xingyun-v2/figure.js", "pack/xingyun-v2/figure.json",
        )
        for seed in seeds:
            destination = work / seed
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(PROJECT / seed, destination)
        subprocess.run([sys.executable, "-X", "utf8", "build.py", "--pack"], cwd=work, check=True)
        rebuilt = work / RELEASE
        count = compare_release(reference, rebuilt)
        rebuilt.rename(target)
    print(f"{count} release entries match the included reference byte for byte.")
    print(target)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    pack = commands.add_parser("archive", help="Collect the engineering archive.")
    pack.add_argument("--out", type=Path, default=ROOT / ENGINEERING)
    commands.add_parser("verify", help="Check an extracted engineering archive.")
    replay = commands.add_parser("rebuild", help="Rebuild and byte-compare the release in a clean directory.")
    replay.add_argument("--out-dir", type=Path, default=ROOT / "reproduced")
    args = parser.parse_args()
    if args.command == "archive":
        archive(args.out)
    elif args.command == "verify":
        verify()
    else:
        rebuild(args.out_dir)


if __name__ == "__main__":
    main()
