#!/usr/bin/env python3
"""Loopback-only isolated server for the optional pthread Wasm target."""
import argparse
import functools
import http.server
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--port', type=int, default=8000)
parser.add_argument('--directory', type=Path,
                    default=Path('.cache/wasm/chez-live/em-tpb32l/bin/tpb32l'))
args = parser.parse_args()
if not (args.directory / 'scheme.html').is_file():
    parser.error('Build the live target first, or set --directory to its runtime directory')

class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cross-Origin-Opener-Policy', 'same-origin')
        self.send_header('Cross-Origin-Embedder-Policy', 'require-corp')
        super().end_headers()

server = http.server.ThreadingHTTPServer(('127.0.0.1', args.port),
    functools.partial(Handler, directory=str(args.directory.resolve())))
print(f'http://127.0.0.1:{server.server_port}/scheme.html', flush=True)
try:
    server.serve_forever()
except KeyboardInterrupt:
    pass
finally:
    server.server_close()
