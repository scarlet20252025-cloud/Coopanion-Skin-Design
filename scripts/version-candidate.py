"""Give the ATRI candidate a version number, and make rollback a first-class operation.

`scripts/snapshot-candidate.py` already copies the live candidate into
`scratch/candidates/<name>-<n>` with a `VERSION.md` and a `registry.json` entry. What it does
NOT do is give that copy a stable version number, or make "go back to version X" a single
reversible command. This script adds both:

  * a monotonic version id `atri-pure-components-<NNN>` (not `-<n>` by directory index),
    recorded in the registry as `version` and in the pack's `VERSION.md`;
  * a git tag `atri-pack-v<NNN>` on the commit the snapshot was taken from, so the *code*
    half of a version is recoverable too (textures live in gitignored scratch/, the
    renderer does not);
  * `list`   – show every registered version with its fingerprint and note;
  * `rollback <version>` – restore a registered version into the live candidate path,
    after saving the current state as its own version so the rollback itself is undoable.

Usage (from the repo root):

    python scripts/version-candidate.py list
    python scripts/version-candidate.py snapshot "<note>"
    python scripts/version-candidate.py rollback atri-pure-components-011

Design notes:

  * The version counter is derived from the registry, not from directory names, so deleting
    a directory never reuses a number.
  * `snapshot` refuses to stack two versions with identical texture fingerprints: it
    relabels the newest entry instead. Same protection the original script had, now
    version-aware.
  * `rollback` never deletes the outgoing state. It snapshots it first (with the note
    "auto-saved before rollback to <target>"), then copies the target textures/JSON back
    into `scratch/candidates/atri-pure-components-01`. That keeps `build-diagnostic.py`
    working unchanged, because it always reads the live path.
  * After any rollback, run the build + node import check before trusting the preview.
  * **IMPORTANT**: `rollback` restores the candidate pack, but `build-diagnostic.py` regenerates
    `figure.js` from the repository sources. So to actually go back in time you ALSO need the
    sources at that version. The git tag `atri-pack-vNNN` is the anchor:
        git checkout atri-pack-vNNN -- characters/atri-01/official-regeneration/pure-generation
    then rebuild. Without that step, rolling back the pack alone is undone by the next build.
"""
from pathlib import Path
import hashlib, json, shutil, subprocess, sys

ROOT = Path(r"D:\Codex\Coopanion-Skin-Design")
LIVE = ROOT / "scratch/candidates/atri-pure-components-01"
REG = ROOT / "scratch/versions"
BASE = "atri-pure-components"


def say(*a):
    print(*a)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def git(*args) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def load_registry() -> dict:
    reg = REG / "registry.json"
    if reg.exists():
        return json.loads(reg.read_text(encoding="utf-8"))
    return {"versions": []}


def save_registry(data: dict) -> None:
    REG.mkdir(parents=True, exist_ok=True)
    (REG / "registry.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def textures_of(pack: Path) -> dict:
    out = {}
    tex = pack / "tex"
    if tex.is_dir():
        for p in sorted(tex.iterdir()):
            if p.is_file():
                out[p.name] = sha(p)[:16]
    return out


def state_of(pack: Path) -> dict:
    """Version identity = textures + the runtime that consumes them.

    Textures alone are not enough: the seated-reuse fix (004) changed no texture at all, only
    figure.js / renderer-template.js, and a texture-only fingerprint would have called it
    "no change" and silently relabelled the previous version instead of making a new one.
    """
    out = textures_of(pack)
    # VERSION.md is written BY the snapshot, so it must not take part in its own identity
    for name in ("figure.js", "figure.json", "model.json", "part-registration.json",
                 "SOURCE.json", "EXPRESSION-PRESERVATION.json"):
        f = pack / name
        if f.is_file():
            out["@" + name] = sha(f)[:16]
    return out


def next_version(data: dict) -> tuple[str, int]:
    """Monotonic version number from the registry, independent of directory names."""
    n = 0
    for v in data.get("versions", []):
        name = v.get("name", "")
        if name.startswith(BASE + "-"):
            tail = name[len(BASE) + 1:]
            if tail.isdigit():
                n = max(n, int(tail))
    return f"{BASE}-{n + 1:03d}", n + 1


def write_version_md(pack: Path, version: str, commit: str, master: str, note: str, tex: dict) -> None:
    (pack / "VERSION.md").write_text(
        f"# {pack.name}\n\n"
        f"- **version**: `{version}`\n"
        f"- **git tag**: `atri-pack-v{version.rsplit('-', 1)[1]}`\n"
        f"- created from the live candidate while HEAD was `{commit}`\n"
        f"- source pack: `scratch/candidates/{LIVE.name}`\n"
        f"- master sha256: `{master}`\n"
        f"- note: {note}\n\n"
        f"## textures ({len(tex)})\n\n" + "".join(f"- `{k}` `{v}`\n" for k, v in tex.items()),
        encoding="utf-8")


def register(data: dict, version: str, pack: Path, commit: str, note: str,
             tex: dict, master: str) -> None:
    entry = {
        "version": version,
        "name": pack.name,
        "pack": f"scratch/candidates/{pack.name}",
        "created_from_commit": commit,
        "note": note,
        "master_sha256": master,
        "textures": tex,
    }
    # identical textures add nothing: relabel the newest entry instead of stacking
    if data["versions"] and data["versions"][0].get("textures") == tex:
        data["versions"][0] = entry
    else:
        data["versions"].insert(0, entry)
    save_registry(data)


def master_sha() -> str:
    m = LIVE / "model.json"
    if m.exists():
        try:
            return json.loads(m.read_text(encoding="utf-8")).get("master_sha256", "?")
        except Exception:
            return "?"
    return "?"


def snapshot(note: str) -> Path:
    data = load_registry()
    tex = state_of(LIVE)
    if data["versions"] and data["versions"][0].get("textures") == tex:
        v = data["versions"][0]
        say(f"no change since {v['name']} ({v.get('version')}); relabelling instead of stacking")
        version = v.get("version") or next_version(data)[0]
        pack = ROOT / v["pack"]
        commit = v.get("created_from_commit", "?")
    else:
        version, num = next_version(data)
        pack = ROOT / f"scratch/candidates/{version}"
        if pack.exists():
            sys.exit(f"refusing to overwrite existing {pack}")
        shutil.copytree(LIVE, pack)
        commit = git("rev-parse", "--short", "HEAD")
    write_version_md(pack, version, commit, master_sha(), note, tex)
    register(data, version, pack, commit, note, tex, master_sha())
    tag = f"atri-pack-v{version.rsplit('-', 1)[1]}"
    if git("rev-parse", "-q", "--verify", f"refs/tags/{tag}") == "":
        git("tag", "-a", tag, "-m", f"ATRI candidate pack {version}: {note}")
        say(f"git tag {tag} -> {git('rev-parse', '--short', tag)}")
    say(f"version {version}  ->  {pack.relative_to(ROOT)}  ({len(tex)} textures)")
    return pack


def rollback(version: str) -> None:
    data = load_registry()
    target = None
    for v in data["versions"]:
        if v.get("version") == version or v.get("name") == version:
            target = v
            break
    if target is None:
        say(f"unknown version: {version}")
        say("known versions:")
        for v in data["versions"]:
            say(f"  {v.get('version') or v.get('name')}  {v.get('note', '')[:60]}")
        sys.exit(2)

    src = ROOT / target["pack"]
    if not src.is_dir():
        sys.exit(f"registered pack missing on disk: {src}")

    # never lose the outgoing state: it becomes its own version first
    auto = snapshot(f"auto-saved before rollback to {target.get('version')}")
    say(f"saved current state as {auto.name}")

    # copy the target back over the live path
    for rel in ("tex", "figure.js", "figure.json", "model.json", "part-registration.json",
                "SOURCE.json", "EDGE-EXPORT.json", "EXPRESSION-PRESERVATION.json"):
        s, d = src / rel, LIVE / rel
        if s.is_dir():
            if d.exists():
                shutil.rmtree(d)
            shutil.copytree(s, d)
        elif s.is_file():
            shutil.copy2(s, d)
    shutil.copy2(src / "VERSION.md", LIVE / "VERSION.md")
    say(f"rolled back {LIVE.name} to {target.get('version')}")
    say("now rebuild: .venv\\Scripts\\python.exe characters\\atri-01\\official-regeneration\\"
        "pure-generation\\build-diagnostic.py")


def listing() -> None:
    data = load_registry()
    if not data["versions"]:
        say("no versions registered yet")
        return
    live = state_of(LIVE)
    say(f"live {LIVE.name}: {len(live)} textures, fingerprint "
        f"{hashlib.sha256(json.dumps(live, sort_keys=True).encode()).hexdigest()[:16]}")
    say("")
    for v in data["versions"]:
        tex = v.get("textures", {})
        mark = " <-- live" if tex == live else ""
        say(f"{v.get('version') or v.get('name'):<28} {v.get('created_from_commit','?'):<10} "
            f"{len(tex):>3} tex  {v.get('note', '')[:64]}{mark}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
    if cmd == "list":
        listing()
    elif cmd == "snapshot":
        snapshot(sys.argv[2] if len(sys.argv) > 2 else "snapshot")
    elif cmd == "rollback":
        if len(sys.argv) < 3:
            sys.exit("usage: version-candidate.py rollback <version>")
        rollback(sys.argv[2])
    else:
        sys.exit(f"unknown command: {cmd}")
