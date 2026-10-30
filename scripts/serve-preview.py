# -*- coding: utf-8 -*-
"""Local preview server with no-cache headers.

Why this exists: `python -m http.server` sends no Cache-Control at all, so browsers fall back to
heuristic caching and keep serving a stale PNG after the file on disk changed. That is exactly what
happened when the left ponytail was redrawn - the file was correct on disk and over HTTP, but the
browser showed the old image. Every response here is marked no-store so a plain refresh (or even no
refresh, for images) always picks up the current file.

Usage:
    .venv/Scripts/python.exe scripts/serve-preview.py            # port 8765
    .venv/Scripts/python.exe scripts/serve-preview.py 8770       # custom port
"""
import functools
import http.server
import socketserver
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def log_message(self, fmt, *args):
        # keep the console readable during long screenshot runs
        if "?" in str(args[0]) if args else False:
            return
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    handler = functools.partial(NoCacheHandler, directory=str(ROOT))
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("127.0.0.1", port), handler) as httpd:
        print(f"serving {ROOT} on http://127.0.0.1:{port}/  (Cache-Control: no-store)", flush=True)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nstopped")


if __name__ == "__main__":
    main()
