# -*- coding: utf-8 -*-
"""Zip a Coopanion figure pack for import, without touching its manifest.

Two scripts, two jobs, on purpose:

    write-atri-manifest.py   owns figure.json - the only place the manifest is written
    package-atri-pack.py     owns the zip   - reads figure.json and validates it, never rewrites it

They used to overlap: both wrote name/about, so running package after write-atri-manifest silently
put the old generic `about` back and the ATRI identity line never reached the app. Packaging now
only validates, and the validation is the same contract Coopanion enforces in
src/packs.ts readManifest(), so a bad word fails here instead of costing a whole-pack rejection.

Usage:
    .venv/Scripts/python.exe scripts/package-atri-pack.py [pack-dir-name]
"""
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACK_NAME = sys.argv[1] if len(sys.argv) > 1 else "atri-v011"
PACK = ROOT / "packs" / PACK_NAME
OUT_ZIP = ROOT / "delivery" / f"{PACK_NAME}-coopanion.zip"

# what readManifest() insists on; about/name are Names objects, entry/model/thumb are pack-relative paths
REQUIRED = ("manifest", "api", "id", "version", "name", "about", "entry", "export")


def die(msg):
    sys.exit(f"[pack] {msg}")


def main():
    if not PACK.is_dir():
        die(f"pack not found: {PACK}")

    mf = PACK / "figure.json"
    if not mf.is_file():
        die(f"missing {mf.name}")
    try:
        d = json.loads(mf.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        die(f"{mf.name} is not valid JSON: {e}")

    missing = [k for k in REQUIRED if k not in d]
    if missing:
        die("manifest is missing required fields "
            f"{missing} - run write-atri-manifest.py first")
    if d["manifest"] != 2 or d["api"] != 2:
        die(f"manifest/api must be 2, got {d['manifest']}/{d['api']}")
    if d["id"] == "coo":
        die("id 'coo' is reserved for the built-in pack")

    for key in ("name", "about"):
        v = d[key]
        if not isinstance(v, dict) or not any(isinstance(s, str) and s.strip() for s in v.values()):
            die(f"{key} needs at least one non-empty language string")

    for key in ("entry", "model", "thumb"):
        v = d.get(key)
        if v is None:
            continue
        if not isinstance(v, str) or v.startswith("/") or ".." in v.split("/"):
            die(f"{key} is not a pack-relative path: {v!r}")
        if not (PACK / v).exists():
            die(f"{key} points at a file that is not in the pack: {v}")

    vocab = d.get("vocab")
    if not isinstance(vocab, list) or not vocab:
        die("vocab must be a non-empty array")
    bad = []
    for w in vocab:
        wid = w.get("id")
        if w.get("kind") not in ("expression", "motion"):
            bad.append((wid, f"kind={w.get('kind')!r}"))
        names = w.get("names") or {}
        if not any(isinstance(v, list) and any(isinstance(s, str) and s.strip() for s in v)
                   for v in names.values()):
            bad.append((wid, "no usable name"))
        sec = w.get("seconds")
        if not isinstance(sec, (int, float)) or isinstance(sec, bool) or sec <= 0:
            bad.append((wid, f"seconds={sec!r}"))
    if bad:
        die("vocab violates the manifest contract: " + repr(bad[:10]))

    # the entry module must actually export the factory the manifest names
    entry_src = (PACK / d["entry"]).read_text(encoding="utf-8", errors="replace")
    if f"export async function {d['export']}" not in entry_src and f"export function {d['export']}" not in entry_src:
        die(f"{d['entry']} does not export {d['export']}")

    OUT_ZIP.parent.mkdir(parents=True, exist_ok=True)
    OUT_ZIP.unlink(missing_ok=True)
    files = sorted(p for p in PACK.rglob("*") if p.is_file())
    with zipfile.ZipFile(OUT_ZIP, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for f in files:
            z.write(f, f"{PACK.name}/{f.relative_to(PACK).as_posix()}")

    print(f"[pack] {PACK.name}: manifest OK "
          f"({len(vocab)} words, id={d['id']}, version={d['version']})")
    print(f"[pack] name  = {d['name'].get('zh') or next(iter(d['name'].values()))}")
    print(f"[pack] about = {(d['about'].get('zh') or next(iter(d['about'].values())))[:60]}…")
    print(f"[pack] wrote {OUT_ZIP.relative_to(ROOT)} "
          f"({len(files)} files, {OUT_ZIP.stat().st_size/1024/1024:.1f} MB)")


if __name__ == "__main__":
    main()
