"""Read-only inventory; GUI tools may be installed outside PATH."""
import importlib.metadata
import importlib.util
import json
import shutil
import sys


def main():
    packages = {}
    for module, distribution in (
        ("PIL", "Pillow"), ("cv2", "opencv-python-headless"),
        ("numpy", "numpy"), ("psd_tools", "psd-tools"),
    ):
        found = importlib.util.find_spec(module) is not None
        version = None
        if found:
            try:
                version = importlib.metadata.version(distribution)
            except importlib.metadata.PackageNotFoundError:
                version = "available via another distribution"
        packages[module] = {"available": found, "version": version}
    print(json.dumps({
        "python": sys.executable,
        "python_version": sys.version.split()[0],
        "commands_on_path": {name: shutil.which(name) for name in
                             ("git", "node", "npm", "krita", "aseprite", "ffmpeg")},
        "packages": packages,
        "note": "Inventory only; no rendering or GUI launch validation performed.",
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
