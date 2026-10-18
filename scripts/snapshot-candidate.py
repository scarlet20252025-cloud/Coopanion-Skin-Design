"""Make the candidate pack versioned and verifiable.

copyfs a snapshot from the current scratch candidate into `scratch/candidates/<name>-<n>`,
writes `VERSION.md` in it (what it is, from which commit, and the texture hashes), and refreshes the
`node` import check. --ref the pack into `scratch/versions/registry.json` so the preview can list it.
"""
from pathlib import Path
import hashlib, json, shutil, subprocess, sys

ROOT = Path(r"D:\Codex\Coopanion-Skin-Design")
CAND = ROOT / "scratch/candidates"
SRC = CAND / "atri-pure-components-01"
REG = ROOT / "scratch/versions"

def sha(p):
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()

def head():
    return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                          capture_output=True, text=True).stdout.strip()

def create(name, note):
    base = CAND / name
    index = 2
    while (base.parent / f"{name}-{index}").exists():
        index += 1
    dest = base.parent / f"{name}-{index}"
    shutil.copytree(SRC, dest)
    tex = {}
    for p in sorted((dest / "tex").iterdir()):
        if p.is_file():
            tex[p.name] = sha(p)[:16]
    model = dest / "model.json"
    master = "?"
    if model.exists():
        master = json.loads(model.read_text(encoding="utf-8")).get("master_sha256", "?")
    (dest / "VERSION.md").write_text(
        f"# {dest.name}\n\n"
        f"- created from the live candidate while HEAD was `{head()}`\n"
        f"- source pack: `scratch/candidates/{SRC.name}`\n"
        f"- master sha256: `{master}`\n"
        f"- note: {note}\n\n"
        f"## textures ({len(tex)})\n\n" + "".join(f"- `{k}` `{v}`\n" for k, v in tex.items()),
        encoding="utf-8")
    REG.mkdir(parents=True, exist_ok=True)
    reg = REG / "registry.json"
    data = json.loads(reg.read_text(encoding="utf-8")) if reg.exists() else {"versions": []}
    entry = {
        "name": dest.name,
        "pack": f"scratch/candidates/{dest.name}",
        "created_from_commit": head(),
        "note": note,
        "master_sha256": master,
        "textures": tex,
    }
    # a snapshot of an identical pack adds nothing: replace the newest entry instead of stacking
    if data["versions"] and data["versions"][0].get("textures") == tex and \
            data["versions"][0].get("pack") == entry["pack"].replace(dest.name, SRC.name):
        data["versions"][0] = entry
    else:
        data["versions"].insert(0, entry)
    reg.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"created {dest.relative_to(ROOT)}  ({len(tex)} textures)")
    print(f"registry -> {reg.relative_to(ROOT)}  ({len(data['versions'])} versions)")
    return dest

if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "atri-pure-components-01"
    note = sys.argv[2] if len(sys.argv) > 2 else "snapshot"
    create(name, note)
