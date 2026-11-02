#!/usr/bin/env python3
"""Build the Star Sleep Coopanion API 2 image-pack ZIP with integrity checks."""
from __future__ import annotations
import argparse, hashlib, json, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACK = ROOT / "packs" / "star-sleep-01-v001"

def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    manifest = json.loads((PACK / "figure.json").read_text(encoding="utf-8"))
    model = json.loads((PACK / "model.json").read_text(encoding="utf-8"))
    source = json.loads((PACK / "SOURCE.json").read_text(encoding="utf-8"))
    if manifest.get("api") != 2 or manifest.get("id") != "star-sleep-01":
        raise SystemExit("Unexpected figure manifest API or id")
    if manifest.get("model") != "model.json" or manifest.get("entry") != "figure.js":
        raise SystemExit("Manifest entry/model path mismatch")
    word_ids = {word["id"] for word in manifest.get("vocab", [])}
    if not word_ids or set(model.get("words", [])) != word_ids:
        raise SystemExit("figure.json vocab and model.words differ")
    if model.get("canvas") != [1086, 1448]:
        raise SystemExit("Unexpected master canvas")
    texture = PACK / "tex" / "star-sleep.png"
    if sha256(texture) != source["master_sha256"]:
        raise SystemExit("Master texture hash does not match SOURCE.json")
    try:
        from PIL import Image
    except ImportError as exc:
        raise SystemExit("Pillow is required: python -m pip install Pillow") from exc
    with Image.open(texture) as image:
        if image.format != "PNG" or image.mode != "RGBA" or list(image.size) != model["canvas"]:
            raise SystemExit("Master texture must be RGBA PNG with the declared canvas")
        if image.getchannel("A").getextrema()[0] != 0:
            raise SystemExit("Master texture must preserve transparent background")
    args.out.mkdir(parents=True, exist_ok=True)
    archive = args.out / f"star-sleep-{manifest['version']}.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for file in sorted(PACK.rglob("*")):
            if file.is_file():
                bundle.write(file, file.relative_to(PACK).as_posix())
    checksum = sha256(archive)
    archive.with_suffix(".zip.sha256").write_text(f"{checksum}  {archive.name}\n", encoding="utf-8")
    print(f"Built {archive}")
    print(f"SHA-256 {checksum}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
