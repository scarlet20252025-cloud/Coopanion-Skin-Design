"""Verify every packaged file against the running local pet server, without changing it."""
from pathlib import Path
from urllib.request import urlopen
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / 'packs/gpt-dragon-v005-r06'
OUT = ROOT / 'characters/original-01/rig-v005-r06'
manifest = json.loads((PACK / 'figure.json').read_text(encoding='utf-8'))
files = []
for path in sorted(PACK.rglob('*')):
    if not path.is_file():
        continue
    relative = path.relative_to(PACK).as_posix()
    with urlopen('http://127.0.0.1:7797/packs/gpt-dragon-v005-r06/' + relative, timeout=15) as response:
        installed = response.read()
    local_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    installed_hash = hashlib.sha256(installed).hexdigest()
    if local_hash != installed_hash:
        raise SystemExit('Installed/local mismatch: ' + relative)
    files.append({'path': relative, 'sha256': local_hash})
report = {'version': manifest['version'], 'all_files_match': True, 'files': files}
(OUT / 'installed-files-v066.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(f"PASS: {len(files)} installed files match {manifest['version']} byte for byte")
