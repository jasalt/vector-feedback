#!/usr/bin/env python3
"""HTTP/Chromium gate. Run with: uv run --with playwright web/browser_smoke.py"""
import argparse
import functools
import hashlib
import http.server
import json
import os
from pathlib import Path
import shutil
import threading

from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser()
parser.add_argument('--scene', choices=['geometry', 'feedback', 'abi'], default='geometry')
args = parser.parse_args()
root = Path(__file__).resolve().parent.parent
output = root / '.cache/wasm' / ('evidence' if args.scene == 'geometry' else args.scene + '-evidence')
output.mkdir(parents=True, exist_ok=True)
class IsolatedHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cross-Origin-Opener-Policy', 'same-origin')
        self.send_header('Cross-Origin-Embedder-Policy', 'require-corp')
        super().end_headers()

build = root / '.cache/wasm' / ('chez-abi/em-tpb32l/bin/tpb32l' if args.scene == 'abi' else 'build')
handler = functools.partial(IsolatedHandler, directory=str(build))
server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
threading.Thread(target=server.serve_forever, daemon=True).start()
report = {"scene": args.scene, "pageErrors": [], "consoleErrors": [], "requestFailures": [], "messages": []}
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=os.environ.get("CHROMIUM") or shutil.which("chromium"),
            headless=True,
            args=["--no-sandbox", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        page = browser.new_page(viewport={"width": 1100, "height": 850})
        page.on("pageerror", lambda e: report["pageErrors"].append(str(e)))
        page.on("console", lambda m: report["consoleErrors" if m.type == "error" else "messages"].append(m.text))
        page.on("requestfailed", lambda r: report["requestFailures"].append({"url": r.url, "failure": r.failure}))
        try:
            entry = 'scheme.html' if args.scene == 'abi' else 'witness.html'
            page.goto(f"http://127.0.0.1:{server.server_port}/{entry}?scene={args.scene}")
            condition = "window.witnessReady === true"
            if args.scene == 'abi':
                condition += " && document.querySelector('#log').textContent.includes('SLIPSTREAM-WASM-ABI-PASS')"
            page.wait_for_function('(' + condition + ") || document.querySelector('#log').textContent.includes('Unhandled exception')", timeout=45000)
            assert page.evaluate(condition), page.locator('#log').inner_text()
            report['isolated'] = page.evaluate('crossOriginIsolated')
            page.wait_for_timeout(1000)
            report["ready"] = True
        finally:
            report["status"] = page.locator("#status").inner_text()
            page.screenshot(path=str(output / "page.png"), full_page=True)
            page.locator("canvas").screenshot(path=str(output / "canvas.png"))
            report["browser"] = browser.version
            browser.close()
    assert report.get("ready"), report
    assert not any(report[k] for k in ("pageErrors", "consoleErrors", "requestFailures")), report
    print('PASS: ' + ('Jolt/Slipstream pointer-adapted ABI' if args.scene == 'abi' else 'actual Slipstream WebGL2 C++ scene'))
finally:
    server.shutdown()
    for name in ("page.png", "canvas.png"):
        path = output / name
        if path.exists():
            report[name + "_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    (output / "browser.json").write_text(json.dumps(report, indent=2) + "\n")
