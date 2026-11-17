"""Package the verified runtime and a self-contained editable project."""

import argparse
import hashlib
import json
import re
from pathlib import Path, PurePosixPath
from shutil import copy2
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from PIL import Image, ImageChops


ROOT = Path(__file__).resolve().parent
RUNTIME = ROOT / "pack" / "star-witch"
EXAMPLE_FILES = {
    "angry-seam-before.png", "angry-seam-compare.jpg", "blink-atlases.png",
    "body-unified-source.png", "complexion-compare.jpg", "eye-registration.json",
    "full-motion-check.jpg", "left-arm-audit.json",
    "left-arm-motion.png", "left-arm-reassembled.png", "matched-blink-art.jpg",
    "portrait-qa.json", "portraits-runtime-verified.jpg", "portraits-verified.jpg",
    "preview-listen.png", "preview-qa.json", "preview-walk.png", "preview-walk-left.png",
    "standing-reassembled.png", "talk-atlas-check.jpg",
}


def local_path(folder, name):
    relative = PurePosixPath(name)
    file = (folder / relative).resolve()
    if relative.is_absolute() or ".." in relative.parts or not file.is_relative_to(folder):
        raise ValueError(f"Path escapes {folder.name}: {name}")
    if not file.is_file():
        raise ValueError(f"Missing file: {name}")
    return file


def runtime_files():
    manifest = json.loads((RUNTIME / "figure.json").read_text(encoding="utf-8"))
    if (manifest["manifest"], manifest["api"], manifest["id"]) != (2, 2, "star-witch"):
        raise ValueError("Unexpected manifest, API or character ID")
    if not re.fullmatch(r"\d+\.\d+\.\d+", manifest["version"]):
        raise ValueError("Expected a numeric three-part version")
    model = json.loads(local_path(RUNTIME, manifest["model"]).read_text(encoding="utf-8"))
    if model["canvas"] != [1163, 1352]:
        raise ValueError("The model is not on the locked master canvas")
    paths = {
        "figure.json", manifest["entry"], manifest["model"], manifest["thumb"],
        "effects.js", "LICENSE", "NOTICE.md",
    }

    for name, part in model["parts"].items():
        x, y, width, height = part["box"]
        count = part.get("count", 1)
        cols = part.get("columns", 1)
        if min(x, y) < 0 or min(width, height, count, cols) <= 0:
            raise ValueError(f"Invalid texture layout for {name}")
        if x + width > 1163 or y + height > 1352 or cols > count:
            raise ValueError(f"Texture outside its artboard or atlas for {name}")
        path = local_path(RUNTIME, part["file"])
        with Image.open(path) as raster:
            if raster.mode != "RGBA" or raster.size != (width * cols, height * ((count + cols - 1) // cols)):
                raise ValueError(f"Texture dimensions or RGBA differ for {name}")
            if "count" not in part:
                source = local_path(ROOT / "parts", name + ".png")
                with Image.open(source) as full:
                    if full.mode != "RGBA" or list(full.size) != model["canvas"]:
                        raise ValueError(f"Expected full-canvas RGBA for {name}")
                    cropped = full.crop((x, y, x + width, y + height))
                    if ImageChops.difference(cropped, raster).getbbox(alpha_only=False) is not None:
                        raise ValueError(f"Runtime texture of {name} differs from its editable PNG")
        paths.add(part["file"])

    with Image.open(local_path(RUNTIME, manifest["thumb"])) as thumb:
        if thumb.width != thumb.height:
            raise ValueError("Expected a square thumbnail")

    for name, index in model["expressions"].items():
        if not isinstance(index, int) or not 0 <= index < model["parts"]["moodPortrait"]["count"]:
            raise ValueError(f"Mood points to a non-existent frame: {name}")
    return manifest["version"], model["parts"], {local_path(RUNTIME, name) for name in paths}


def verify_master():
    with Image.open(ROOT / "source/master-selected.png") as selected, Image.open(ROOT / "source/master-right.png") as right:
        for art in (selected, right):
            if art.mode != "RGBA" or art.size != (1163, 1352):
                raise ValueError("Expected both master PNGs to use 1163×1352 RGBA")
        mirrored = selected.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        if ImageChops.difference(mirrored, right).getbbox(alpha_only=False) is not None:
            raise ValueError("The working master does not match the mirrored original")


def project_files(parts, runtime):
    """Current inputs and outputs only. Rejected exports and logs stay local."""
    root_sources = {file for file in ROOT.iterdir()
                    if file.is_file() and (file.suffix in {".py", ".mjs", ".md"}
                                           or file.name in {
                                               "LICENSE", "preview.html", "preview.js", "requirements.txt", ".gitignore",
                                           })}
    current_parts = {ROOT / "parts" / (name + ".png") for name, part in parts.items() if "count" not in part}
    current_parts.update(ROOT / "parts" / n for n in ("arm-viewer-left.png", "body-left-pass.png"))
    inputs = set()
    for path in ("docs", "source", "masks", "vendor"):
        inputs.update(file for file in (ROOT / path).rglob("*") if file.is_file())
    inputs.update((ROOT / "masters").glob("*.md"))
    inputs.update(file for file in (ROOT / "work").iterdir() if file.is_file() and file.suffix in {".png", ".md"})
    repair = ROOT / "work" / "face-repair"
    inputs.update(repair.glob("*.md"))
    inputs.update(repair.glob("mood-*.png"))
    inputs.update(repair.glob("blink-*-matched.png"))
    inputs.update(repair / name for name in (
        "eyeLeft-extraction.png", "eyeRight-extraction.png", "face-extraction.png",
        "eyeLeft-painted.png", "eyeRight-painted.png", "face-opaque-painted.png", "master-face-reference.png",
    ))
    review = ROOT / "review"
    outputs = {review / name for name in EXAMPLE_FILES if (review / name).is_file()}
    outputs.update(review.glob("*-qa.json"))
    outputs.update(review.glob("palette-*"))
    outputs.update(review.glob("motion-*"))
    outputs.update(review.glob("walk-*-verified.*"))
    outputs.update(review.glob("listen-*-verified.*"))
    return set(root_sources | inputs | current_parts | runtime | outputs)


def archive(path, files, base, prefix=""):
    temp = path.with_suffix(".zip.tmp")
    try:
        with ZipFile(temp, "w", compression=ZIP_DEFLATED, compresslevel=6) as out:
            for file in sorted(files, key=lambda file: file.relative_to(base).as_posix()):
                name = prefix + file.relative_to(base).as_posix()
                info = ZipInfo(name)
                info.external_attr = 0o100644 << 16
                out.writestr(info, file.read_bytes(), compress_type=ZIP_DEFLATED, compresslevel=6)
        with ZipFile(temp) as check:
            corrupt = check.testzip()
            if corrupt or set(check.namelist()) != {prefix + p.relative_to(base).as_posix() for p in files}:
                raise ValueError(f"ZIP verification failed: {corrupt}")
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    path.with_suffix(".zip.sha256").write_text(f"{digest}  {path.name}\n", encoding="utf-8")
    print(f"{path} ({len(files)} files, SHA-256 {digest})")


def stage(files, target):
    if target == ROOT or target.is_relative_to(ROOT) or ROOT.is_relative_to(target):
        raise ValueError("The staged copy must be outside the editable project")
    if target.exists() and any(child.name != ".git" for child in target.iterdir()):
        raise ValueError(f"Stage requires an empty directory or a bare working tree: {target}")
    target.mkdir(parents=True, exist_ok=True)
    for file in files:
        staged = target / file.relative_to(ROOT)
        staged.parent.mkdir(parents=True, exist_ok=True)
        copy2(file, staged)
    print(f"Staged {len(files)} project files in {target}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "dist", help="ZIP output directory")
    parser.add_argument("--stage", type=Path, help="Also stage the current source tree in an empty directory")
    args = parser.parse_args()
    verify_master()
    version, parts, runtime = runtime_files()
    source = project_files(parts, runtime)
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    archive(out / f"star-witch-{version}.zip", runtime, RUNTIME)
    archive(out / f"star-witch-{version}-engineering.zip", source, ROOT, "star-witch/")
    if args.stage:
        stage(source, args.stage.resolve())


if __name__ == "__main__":
    main()
