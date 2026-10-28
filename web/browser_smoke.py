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
parser.add_argument('--scene', choices=['geometry', 'feedback', 'abi', 'live'], default='geometry')
parser.add_argument('--deterministic', action='store_true')
parser.add_argument('--exercise', action='store_true')
parser.add_argument('--frames', type=int, default=0)
parser.add_argument('--dpr', type=float, default=1)
args = parser.parse_args()
root = Path(__file__).resolve().parent.parent
output = root / '.cache/wasm' / ('evidence' if args.scene == 'geometry' else args.scene + '-evidence')
if args.deterministic:
    output = output.with_name(output.name.replace('-evidence', '-parity-evidence'))
elif args.exercise:
    output = output.with_name(output.name.replace('-evidence', '-controls-evidence'))
output.mkdir(parents=True, exist_ok=True)
class IsolatedHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cross-Origin-Opener-Policy', 'same-origin')
        self.send_header('Cross-Origin-Embedder-Policy', 'require-corp')
        super().end_headers()

build = root / '.cache/wasm' / (f'chez-{args.scene}/em-tpb32l/bin/tpb32l' if args.scene in ('abi', 'live') else 'build')
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
        page = browser.new_page(viewport={"width": 1100, "height": 850}, device_scale_factor=args.dpr)
        page.on("pageerror", lambda e: report["pageErrors"].append(str(e)))
        page.on("console", lambda m: report["consoleErrors" if m.type == "error" else "messages"].append(m.text))
        page.on("requestfailed", lambda r: report["requestFailures"].append({"url": r.url, "failure": r.failure}))
        try:
            entry = 'scheme.html' if args.scene in ('abi', 'live') else 'witness.html'
            query = f'scene={args.scene}' + ('&deterministic=1' if args.deterministic else '')
            page.goto(f"http://127.0.0.1:{server.server_port}/{entry}?{query}")
            condition = "window.witnessReady === true"
            if args.scene == 'abi':
                condition += " && document.querySelector('#log').textContent.includes('SLIPSTREAM-WASM-ABI-PASS')"
            page.wait_for_function('(' + condition + ") || document.querySelector('#log').textContent.includes('Unhandled exception')", timeout=45000)
            assert page.evaluate(condition), page.locator('#log').inner_text()
            report['isolated'] = page.evaluate('crossOriginIsolated')
            if args.scene == 'live':
                report['modelState'] = page.evaluate('window.modelState')
                assert report['modelState']['frames'] >= 2, report
                if args.deterministic:
                    page.wait_for_function('window.fixtureDone === true', timeout=180000)
                    parity = page.evaluate('({expected:window.expectedPayload, actual:window.actualPayload})')
                    assert len(parity['expected']) == len(parity['actual']) == 434, parity
                    differences = [abs(a-b) for a,b in zip(parity['expected'], parity['actual'])]
                    assert all(d <= max(0.00002, abs(e)*0.00002) for d,e in zip(differences, parity['expected'])), max(differences)
                    report['fixtureParity'] = {'components':434, 'ticks':65, 'maxAbsError':max(differences)}
                if args.exercise:
                    assert not args.deterministic, 'interactive and deterministic modes are separate gates'
                    def model():
                        return page.evaluate('window.modelState')
                    def advance_frames(n=2):
                        start = model()['frames']
                        page.wait_for_function('(start) => window.modelState.frames >= start + ' + str(n), arg=start, timeout=30000)
                    page.locator('canvas').focus()
                    page.keyboard.down('Space')
                    page.wait_for_function('window.modelState.paused', timeout=15000)
                    page.keyboard.up('Space')
                    advance_frames()
                    paused_time = model()['time']
                    advance_frames()
                    assert model()['time'] == paused_time
                    box = page.locator('canvas').bounding_box()
                    for button, field in [('left','panX'), ('right','yaw'), ('middle','roll')]:
                        before = model()[field]
                        page.mouse.move(box['x']+300, box['y']+250)
                        advance_frames()
                        page.mouse.down(button=button)
                        advance_frames()
                        page.mouse.move(box['x']+350, box['y']+270)
                        advance_frames()
                        page.mouse.up(button=button)
                        advance_frames()
                        assert abs(model()[field]-before) > 0.00001, (button, before, model())
                    zoom = model()['zoom']
                    page.mouse.wheel(0, -100)
                    page.wait_for_function('(z) => Math.abs(window.modelState.zoom-z) > 0.00001', arg=zoom, timeout=15000)
                    report['afterControls'] = model()
                    page.keyboard.down('r')
                    page.wait_for_function('!window.modelState.paused && Math.abs(window.modelState.zoom-0.965)<0.00001', timeout=15000)
                    page.keyboard.up('r')
                    advance_frames()
                    # Clear held inputs on blur and verify a later move cannot drag.
                    page.mouse.down(button='left')
                    advance_frames()
                    page.evaluate("window.dispatchEvent(new Event('blur'))")
                    advance_frames()
                    pan = model()['panX']
                    page.mouse.move(box['x']+400, box['y']+300)
                    advance_frames()
                    assert model()['panX'] == pan
                    page.mouse.up(button='left')
                    page.set_viewport_size({'width':700,'height':720})
                    advance_frames()
                    report['resizedCanvas'] = page.locator('canvas').evaluate('(c)=>({width:c.width,height:c.height,cssWidth:c.clientWidth,dpr:devicePixelRatio})')
                    assert abs(report['resizedCanvas']['width'] - report['resizedCanvas']['cssWidth']*args.dpr) <= 2
                    report['controls'] = 'pause, left/right/middle drag, wheel, reset, blur, resize'
                if args.frames:
                    page.wait_for_function('(n) => window.modelState.frames >= n', arg=args.frames, timeout=300000)
                    report['stressFrames'] = model()['frames'] if args.exercise else page.evaluate('window.modelState.frames')
                report['modelState'] = page.evaluate('window.modelState')
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
    print('PASS: ' + ('Jolt/Slipstream pointer-adapted ABI' if args.scene == 'abi' else 'Jolt-driven Slipstream WebGL2' if args.scene == 'live' else 'actual Slipstream WebGL2 C++ scene'))
finally:
    server.shutdown()
    for name in ("page.png", "canvas.png"):
        path = output / name
        if path.exists():
            report[name + "_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    (output / "browser.json").write_text(json.dumps(report, indent=2) + "\n")
