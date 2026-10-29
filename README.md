# Picture Plane — GitHub Pages package

Static package of the Jolt + Slipstream Wasm prototype, built from source commit
`d8963ae4056caa7565566a92509d67f1a90114c4` on the repository's `master` branch.
It uses actual Slipstream/Slughorn WebGL2 rendering, not Raylib. Desktop remains
the primary implementation. Runtime binaries are copied unchanged from the
current local live build and freshly validated as a package; `build-size.json`
contains the packaged hashes. `build-provenance.json` records differences from
the earlier retained measurement; bit-reproducible builds are not claimed.

## Hosting

After confirming the outstanding Slipstream license/permission in
[THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md), push the `pages` branch and
select **Settings → Pages → Deploy from a branch → pages → / (root)**.
Expected project URL: <https://jasalt.github.io/vector-feedback/>.
No custom Actions workflow or compilation on GitHub is required.

The `index.html` bootstrap registers a service worker scoped to this project,
reloads once to obtain cross-origin isolation and only then loads
`runtime/scheme.html`. The worker adds COOP/COEP headers missing from GitHub
Pages. It does not cache assets. All paths are relative to support project URLs.
Use the package entry point, not a direct first visit to `runtime/scheme.html`.

Test locally with an ordinary server (no special headers required):

```sh
python3 -m http.server 8000 --bind 127.0.0.1
# Open http://127.0.0.1:8000/
```

Requires HTTPS or localhost, service workers, SharedArrayBuffer, WebGL2 and
EXT_color_buffer_float. Browser policies that disable isolation/service workers
prevent launch. Clear this site's service workers/site data if an old worker
from another demo is interfering.

## Runtime

Left/right/middle drags adjust pan/yaw-pitch/roll. Wheel dollies; Space pauses;
R resets; +/- adjusts the feedback tail. Context-loss recovery reloads the
module. This remains an experimental Jolt 0.8.21 / Chez tpb32l build, with a
simplified HUD and slow software-rendered performance. Approximately 20 MB of
uncompressed runtime assets; no mobile/other-browser or 60 fps claim.

## Validation

`test-pages.py` validates this package under a nested project path, with **no
server-supplied isolation headers**, using a fresh Chromium profile. It checks
worker-created isolation, runtime readiness/input, missing requests and captures
screenshots. Run with Chromium on PATH or `CHROMIUM` set:

```sh
uv run --with playwright==1.64.1 test-pages.py
```

Generated local validation files live in `.validation/` and are ignored. Retained
report and inspected screenshot are under `evidence/`. `SHA256SUMS` covers the
published runtime and licensing files. This branch has not itself been publicly
deployed or verified on the live GitHub Pages URL merely by creating it locally.
