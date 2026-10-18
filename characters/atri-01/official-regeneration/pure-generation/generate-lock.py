"""Generate one missing lock component through the configured GPT Image 2.5 image endpoint.

The only input is the locked master template, as required by the pure-generation rules. The raw
output is stored under characters/atri-01/official-regeneration/raw/ with its request record; it is
not used until it passes the same-uniform-similarity fit against the master and a visual check.

Usage:
  set OPENAI_BASE_URL          (optional; defaults to the endpoint below)
  set OPENAI_API_KEY           (never written to disk)
  python generate-lock.py --side right --out-name ponytail-far-complete-07.png
"""
from pathlib import Path
import argparse, base64, json, os, sys, time, urllib.error, urllib.request, uuid

ROOT = Path(__file__).resolve().parents[4]
MASTER = ROOT/'characters/atri-01/master.png'
PROMPT = ROOT/'characters/atri-01/prompts/image25-far-lock.txt'
RAW = ROOT/'characters/atri-01/official-regeneration/raw'
DEFAULT_BASE = 'https://edge.lingsuan.org/v1'
MODEL = 'gpt-image-2.5-sunburst'
UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36')


def multipart(fields, files):
    boundary = '----codex' + uuid.uuid4().hex
    body = bytearray()
    for name, value in fields.items():
        body += f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode()
    for name, (filename, payload, ctype) in files.items():
        body += (f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"; '
                 f'filename="{filename}"\r\nContent-Type: {ctype}\r\n\r\n').encode()
        body += payload + b'\r\n'
    body += f'--{boundary}--\r\n'.encode()
    return bytes(body), f'multipart/form-data; boundary={boundary}'


def call(fields, files, base, key, timeout=600):
    body, ctype = multipart(fields, files)
    req = urllib.request.Request(base + '/images/edits', data=body, method='POST',
                                 headers={'Authorization': 'Bearer ' + key, 'Content-Type': ctype,
                                          'User-Agent': UA, 'Accept': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise SystemExit(f'image endpoint HTTP {e.code}: {e.read()[:400]!r}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--side', default='right', choices=['left', 'right'])
    ap.add_argument('--out-name', required=True)
    ap.add_argument('--size', default='auto')
    ap.add_argument('--quality', default='high')
    ap.add_argument('--prompt', default=str(PROMPT))
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    key = os.environ.get('OPENAI_API_KEY')
    base = os.environ.get('OPENAI_BASE_URL', DEFAULT_BASE).rstrip('/')
    prompt = Path(args.prompt).read_text(encoding='utf8')
    fields = {'model': MODEL, 'prompt': prompt, 'n': '1', 'size': args.size,
              'quality': args.quality, 'background': 'transparent', 'output_format': 'png'}
    if args.dry_run:
        print(json.dumps({'endpoint': base + '/images/edits', 'model': MODEL,
                          'fields': {k: v for k, v in fields.items() if k != 'prompt'},
                          'prompt_file': str(Path(args.prompt).relative_to(ROOT)),
                          'input': str(MASTER.relative_to(ROOT)), 'key_present': bool(key)}, indent=2))
        return 0
    if not key:
        raise SystemExit('OPENAI_API_KEY is not set in this shell')
    started = time.time()
    data = call(fields, {'image': (MASTER.name, MASTER.read_bytes(), 'image/png')}, base, key)
    item = (data.get('data') or [{}])[0]
    if 'b64_json' not in item:
        raise SystemExit('no image in response: ' + json.dumps(data)[:400])
    out = RAW/args.out_name
    out.write_bytes(base64.b64decode(item['b64_json']))
    record = {'model': MODEL, 'endpoint': base + '/images/edits', 'input': str(MASTER.relative_to(ROOT)),
              'prompt_file': str(Path(args.prompt).relative_to(ROOT)), 'size': args.size,
              'quality': args.quality, 'background': 'transparent',
              'output': str(out.relative_to(ROOT)), 'seconds': round(time.time() - started, 1),
              'usage': data.get('usage')}
    (RAW/(out.stem + '-request.json')).write_text(json.dumps(record, indent=2) + '\n', encoding='utf8')
    print(json.dumps(record, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
