#!/usr/bin/env python3
"""Validate Pages-style static hosting, deliberately without isolation headers."""
import functools
import hashlib
import http.server
import json
import os
from pathlib import Path
import shutil
import threading
import urllib.request
from playwright.sync_api import sync_playwright

root = Path(__file__).resolve().parent
output = root / '.validation'
output.mkdir(exist_ok=True)
host = output / 'host'
host.mkdir(exist_ok=True)
mount = host / 'vector-feedback'
if not mount.exists():
    mount.symlink_to(root, target_is_directory=True)
handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(host))
server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
threading.Thread(target=server.serve_forever, daemon=True).start()
url = f'http://127.0.0.1:{server.server_port}/vector-feedback/'
report = {'pageErrors':[], 'consoleErrors':[], 'requestFailures':[], 'responses404':[],
          'nestedProjectPath':'/vector-feedback/', 'serverAddsIsolationHeaders':False}
try:
    with urllib.request.urlopen(url) as response:
        assert response.headers.get('Cross-Origin-Opener-Policy') is None
        assert response.headers.get('Cross-Origin-Embedder-Policy') is None
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=os.environ.get('CHROMIUM') or shutil.which('chromium'),
            headless=True, args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
        page = browser.new_page(viewport={'width':700,'height':850})
        page.on('pageerror', lambda e: report['pageErrors'].append(getattr(e,'stack',None) or str(e)))
        page.on('console', lambda m: report['consoleErrors'].append(m.text) if m.type == 'error' else None)
        page.on('requestfailed', lambda r: report['requestFailures'].append({'url':r.url,'failure':r.failure}))
        def response_seen(response):
            if response.status == 404:
                report['responses404'].append(response.url)
            if response.url.endswith('/runtime/scheme.html'):
                report['runtimeFromServiceWorker'] = response.from_service_worker
                report['runtimeCOOP'] = response.headers.get('cross-origin-opener-policy')
                report['runtimeCOEP'] = response.headers.get('cross-origin-embedder-policy')
        page.on('response', response_seen)
        try:
            page.goto(url, wait_until='commit')
            page.wait_for_url('**/runtime/scheme.html', timeout=120000)
            page.wait_for_function('crossOriginIsolated && typeof SharedArrayBuffer !== "undefined" && window.witnessReady === true', timeout=120000)
            report['state'] = page.evaluate('({isolated:crossOriginIsolated,sab:typeof SharedArrayBuffer!=="undefined",scope:navigator.serviceWorker.controller.scriptURL,model:window.modelState})')
            assert report['state']['scope'].endswith('/vector-feedback/coi-serviceworker.js')
            assert report.get('runtimeFromServiceWorker')
            assert report['runtimeCOOP'] == 'same-origin' and report['runtimeCOEP'] == 'require-corp'
            page.locator('canvas').focus()
            page.keyboard.down('Space')
            page.wait_for_function('window.modelState.paused', timeout=30000)
            page.keyboard.up('Space')
            report['pauseInputConsumed'] = True
            report['ready'] = True
        finally:
            page.evaluate('window.webCapturePaused = true')
            report['status'] = page.locator('#status').inner_text()
            page.screenshot(path=str(output/'page.png'), full_page=True, timeout=30000)
            page.screenshot(path=str(output/'canvas.png'), clip=page.locator('canvas').bounding_box(), timeout=30000)
            report['browser'] = browser.version
            browser.close()
    assert report.get('ready'), report
    assert not any(report[k] for k in ['pageErrors','consoleErrors','requestFailures','responses404']), report
    print('PASS: static Pages-style launch, scoped isolation worker and live Jolt input')
finally:
    server.shutdown()
    for name in ['page.png','canvas.png']:
        if (output/name).exists():
            report[name+'_sha256'] = hashlib.sha256((output/name).read_bytes()).hexdigest()
    (output/'browser.json').write_text(json.dumps(report,indent=2)+'\n')
