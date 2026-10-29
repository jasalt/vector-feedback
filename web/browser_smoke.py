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
import time

from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser()
parser.add_argument('--scene', choices=['geometry', 'feedback', 'abi', 'live'], default='geometry')
parser.add_argument('--deterministic', action='store_true')
parser.add_argument('--exercise', action='store_true')
parser.add_argument('--frames', type=int, default=0)
parser.add_argument('--dpr', type=float, default=1)
parser.add_argument('--lifecycle', action='store_true')
parser.add_argument('--tail-bounds', action='store_true')
args = parser.parse_args()
if args.frames < 0 or args.dpr <= 0:
    parser.error('frames must be nonnegative and DPR must be positive')
if args.scene != 'live' and any((args.deterministic, args.exercise, args.frames, args.lifecycle, args.tail_bounds)):
    parser.error('extended validation flags require --scene live')
if args.tail_bounds and not args.exercise:
    parser.error('--tail-bounds requires --exercise')
if args.deterministic and any((args.exercise, args.frames, args.lifecycle)):
    parser.error('deterministic parity is a separate gate from interactive validation')
root = Path(__file__).resolve().parent.parent
output = root / '.cache/wasm' / ('evidence' if args.scene == 'geometry' else args.scene + '-evidence')
if args.deterministic:
    output = output.with_name(output.name.replace('-evidence', '-parity-evidence'))
elif args.exercise:
    output = output.with_name(output.name.replace('-evidence', '-controls-evidence'))
elif args.frames:
    output = output.with_name(output.name.replace('-evidence', '-stress-evidence'))
if args.dpr != 1:
    output = output.with_name(output.name + '-dpr' + str(args.dpr))
if args.lifecycle:
    output = output.with_name(output.name + '-lifecycle')
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
        page = browser.new_page(viewport={"width": 500 if args.dpr > 1 or args.tail_bounds or args.frames else 1100, "height": 850}, device_scale_factor=args.dpr)
        page.on("pageerror", lambda e: report["pageErrors"].append(getattr(e, 'stack', None) or str(e)))
        def console_message(message):
            report['consoleErrors' if message.type == 'error' else 'messages'].append(message.text)
            if message.text.startswith('stress progress:'):
                print(message.text, flush=True)
        page.on('console', console_message)
        page.on("requestfailed", lambda r: report["requestFailures"].append({"url": r.url, "failure": r.failure}))
        try:
            entry = 'scheme.html' if args.scene in ('abi', 'live') else 'witness.html'
            query = f'scene={args.scene}' + ('&deterministic=1' if args.deterministic else '')
            navigation_start = time.monotonic()
            page.goto(f"http://127.0.0.1:{server.server_port}/{entry}?{query}")
            condition = "window.witnessReady === true"
            if args.scene == 'abi':
                condition += " && document.querySelector('#log').textContent.includes('SLIPSTREAM-WASM-ABI-PASS')"
            page.wait_for_function('(' + condition + ") || document.querySelector('#log').textContent.includes('Unhandled exception')", timeout=45000)
            assert page.evaluate(condition), page.locator('#log').inner_text()
            report['navigationToReadyMs'] = (time.monotonic()-navigation_start)*1000
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
                    print('controls: pause', flush=True)
                    page.locator('canvas').focus()
                    page.keyboard.down('Space')
                    page.wait_for_function('window.modelState.paused', timeout=15000)
                    page.keyboard.up('Space')
                    advance_frames()
                    paused_time = model()['time']
                    advance_frames()
                    assert model()['time'] == paused_time
                    box = page.locator('canvas').bounding_box()
                    print('controls: drags', flush=True)
                    for button, field in [('left','panX'), ('right','yaw'), ('middle','roll')]:
                        print('drag: ' + button, flush=True)
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
                    print('controls: tail', flush=True)
                    page.keyboard.down('Equal')
                    page.wait_for_function('window.modelState.tail === 58', timeout=30000)
                    page.keyboard.up('Equal')
                    advance_frames()
                    page.keyboard.down('Minus')
                    page.wait_for_function('window.modelState.tail === 48', timeout=30000)
                    page.keyboard.up('Minus')
                    advance_frames()
                    if args.tail_bounds:
                        for key, targets in [('Equal', [58,68,78,78]), ('Minus', [68,58,48,38,28,18,8,8])]:
                            for target in targets:
                                print('tail target: ' + str(target), flush=True)
                                page.keyboard.down(key)
                                page.wait_for_function('(t)=>window.modelState.tail===t', arg=target, timeout=30000)
                                page.keyboard.up(key)
                                advance_frames()
                        report['tailBounds'] = [8,78]
                    report['afterControls'] = model()
                    page.keyboard.down('r')
                    page.wait_for_function('!window.modelState.paused && window.modelState.tail===48 && Math.abs(window.modelState.zoom-0.965)<0.00001', timeout=15000)
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
                    print('controls: resize', flush=True)
                    page.set_viewport_size({'width':550 if args.dpr > 1 else 700,'height':720})
                    advance_frames()
                    report['resizedCanvas'] = page.locator('canvas').evaluate('(c)=>({width:c.width,height:c.height,cssWidth:c.clientWidth,dpr:devicePixelRatio})')
                    assert abs(report['resizedCanvas']['width'] - report['resizedCanvas']['cssWidth']*args.dpr) <= 2
                    report['controls'] = 'pause, left/right/middle drag, wheel, +/- tail, reset, blur, resize'
                (output / 'progress.json').write_text(json.dumps(report, indent=2) + '\n')
                if args.frames:
                    print('stress target: ' + str(args.frames), flush=True)
                    page.set_viewport_size({'width':500, 'height':720})
                    page.evaluate("window.stressTimer = setInterval(()=>console.log('stress progress: ' + JSON.stringify({model:window.modelState,lost:!!window.webContextLost})),10000)")
                    page.wait_for_function('(n) => window.modelState.frames >= n', arg=args.frames, timeout=300000)
                    page.evaluate('clearInterval(window.stressTimer)')
                    report['stressFrames'] = model()['frames'] if args.exercise else page.evaluate('window.modelState.frames')
                report['modelState'] = page.evaluate('window.modelState')
                if args.lifecycle:
                    print('lifecycle: background tab', flush=True)
                    tab = browser.new_page()
                    tab.bring_to_front()
                    page.wait_for_timeout(500)
                    page.bring_to_front()
                    tab.close()
                    before = page.evaluate('window.modelState.frames')
                    page.wait_for_function('(f)=>window.modelState.frames>f', arg=before, timeout=30000)
                    print('lifecycle: context loss', flush=True)
                    page.evaluate("window.loss = document.querySelector('canvas').getContext('webgl2').getExtension('WEBGL_lose_context'); window.loss.loseContext()")
                    page.wait_for_function('window.webContextLost === true', timeout=10000)
                    assert 'context lost' in page.locator('#status').inner_text()
                    page.wait_for_timeout(300)
                    page.evaluate('window.loss.restoreContext()')
                    page.wait_for_function("document.querySelector('#status').textContent.includes('reload to rebuild')", timeout=15000)
                    page.get_by_role('button', name='Reload / recover graphics context').click()
                    page.wait_for_function('window.witnessReady === true', timeout=45000)
                    report['lifecycle'] = 'background tab return, context loss with explicit reload recovery'
            page.wait_for_timeout(1000)
            report["ready"] = True
        finally:
            if args.scene == 'live':
                page.evaluate('window.webCapturePaused = true')
            report["status"] = page.locator("#status").inner_text()
            if args.scene == 'live':
                report['lastFrameMetrics'] = page.evaluate('window.frameMetrics')
            report['canvasDimensions'] = page.locator('canvas').evaluate('(c)=>({width:c.width,height:c.height,css:c.style.cssText,box:c.getBoundingClientRect().toJSON()})')
            page.screenshot(path=str(output / "page.png"), full_page=True, timeout=15000)
            box = page.locator('canvas').bounding_box()
            page.screenshot(path=str(output / 'canvas.png'), clip=box, timeout=15000)
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
