"""Collect the pure-generation review page QA with a real browser and bind it to the candidate pack.

The review page already drives the genuine Coopanion renderer for the candidate pack. This script
only opens it, presses the existing QA button and writes the returned frames plus metadata, so the
candidate keeps re-derivable evidence after any art change.
"""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import base64, hashlib, json, sys, threading

Q = Path(__file__).resolve().parent
ROOT = Q.parents[3]
PACK = ROOT/'scratch/candidates/atri-pure-components-01'
PAGE = 'characters/atri-01/official-regeneration/pure-generation/review.html'
OUT = Q/'qa/current'


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def fingerprint(pack):
    files = {str(f.relative_to(pack)).replace('\\', '/'): hashlib.sha256(f.read_bytes()).hexdigest()
             for f in sorted(pack.rglob('*')) if f.is_file()}
    return hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()


def main(browser=None):
    from playwright.sync_api import sync_playwright
    before = fingerprint(PACK)
    OUT.mkdir(parents=True, exist_ok=True)
    for stale in OUT.glob('*.png'):
        stale.unlink()
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Quiet, directory=str(ROOT)))
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    errors = []
    try:
        with sync_playwright() as p:
            with p.chromium.launch(executable_path=browser) as b:
                page = b.new_page(viewport={'width': 1900, 'height': 1200})
                page.on('pageerror', lambda e: errors.append(str(e)))
                page.goto(f'http://127.0.0.1:{server.server_port}/{PAGE}')
                page.wait_for_function('document.body.dataset.ready === "true"', timeout=90000)
                page.click('#qa')
                page.wait_for_function("document.getElementById('status').textContent.includes('采样完成')", timeout=600000)
                payload = page.evaluate("""() => ({
                  results: document.getElementById('results').textContent,
                  shots: [...document.querySelectorAll('#shots img')].map(i => i.src),
                  status: document.getElementById('status').textContent,
                })""")
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=2)
    if errors:
        raise SystemExit('page errors: ' + json.dumps(errors, ensure_ascii=False))
    meta = json.loads(payload['results'])
    shots = payload['shots']
    samples = meta['samples']
    if len(samples) != len(shots):
        raise SystemExit(f'frame mismatch: {len(samples)} metadata vs {len(shots)} images')
    for i, src in enumerate(shots):
        head, _, data = src.partition(',')
        if not head.startswith('data:image/png'):
            raise SystemExit(f'frame {i} is not a PNG data URL')
        (OUT/f'{i:03}.png').write_bytes(base64.b64decode(data))
    meta['schema'] = 3
    meta['pack_fingerprint'] = fingerprint(PACK)
    if meta['pack_fingerprint'] != before:
        raise SystemExit('candidate changed while capturing; rerun after edits stop')
    meta['review_page'] = PAGE
    (OUT/'samples.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    print(json.dumps({'frames': len(samples), 'checks': len(meta['checks']),
                      'rejects': sum(1 for c in meta['checks'] if not c['accepted']),
                      'fingerprint': meta['pack_fingerprint'], 'status': payload['status']},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else None))
