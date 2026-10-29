# Optional self-contained Jolt + Slipstream WebGL2 build

**Working experimental browser target; desktop remains primary.** No sibling
checkout, prepared target pack or copied compiler executable is required. This
repo fetches pinned upstream sources and builds its own Chez host/cross toolchain,
libffi and Slipstream renderer. Normal desktop setup and `jolt -M:run` are unchanged.

Progress/evidence: [../docs/wasm-plan.md](../docs/wasm-plan.md).
Toolchain boundary/patch provenance: [toolchain/README.md](toolchain/README.md).

## Build and run

Currently supported build host: **Linux x86_64 with Nix flakes enabled**.
The locked development shell supplies compilers, Emscripten, native Jolt,
Chromium and a redistributable DejaVu Sans Mono font/license. First build needs
network access, several minutes and a few GB of cache/disk space. Builds are not
claimed bit-reproducible, and this is not an upstream-supported Jolt Wasm release.

```sh
# From this repository's root; builds all prerequisites on the first run:
nix develop -c bash scripts/wasm-live-build.sh
python3 web/serve.py
# Open http://127.0.0.1:8000/scheme.html
```

Output: **`.cache/wasm/chez-live/em-tpb32l/bin/tpb32l/`**. The isolated server
binds loopback and sends COOP/COEP. SharedArrayBuffer requires those headers;
plain HTTP serving alone is insufficient for the raw runtime.

For development the stages can also be run separately:

```sh
nix develop -c bash scripts/wasm-bootstrap.sh  # host, cross pack, libffi
nix develop -c bash scripts/wasm-build.sh      # C++ witness + shared shader fixture
nix develop -c bash scripts/wasm-abi-build.sh  # optional direct ABI/adapters gate
# wasm-live-build.sh runs all required stages, then the live app.
```

App/toolchain output is local and ignored (Nix and Emscripten also use their
normal package/port caches). `WASM_BUILD_ROOT` selects a separate cache, and is
honored by the build scripts, server, browser gates and measurements:

```sh
export WASM_BUILD_ROOT="$PWD/.cache/wasm-fresh"
nix develop -c bash scripts/wasm-live-build.sh
python3 web/serve.py
```

Keep that variable exported for subsequent tests/serving. Unset it to return to
the default cache. **Migration:** app trees made by the old sibling-dependent
scripts have no owned-toolchain fingerprint and are rejected. Use a fresh cache,
or remove only the old generated `.cache/wasm/chez-abi` and `chez-live` directories.
Do not delete the repository or `.cache/pages-site` Git worktree.

Bootstrap stage stamps resume completed stages; fingerprints reject changes to
lock/pins/patch inputs with cleanup guidance instead of silently mixing packs.
See `<cache>/toolchain/logs/` for native-host, target-pack and libffi logs.
The first native target link uses a real 32-bit Linux kernel; a separate
pthread-enabled Wasm kernel is built for the browser. Host, xpatch and target
boots are generated together from one patched Chez source tree.

Set `WEB_FONT` and `WEB_FONT_LICENSE` to override the pinned default. The font is
preloaded into `.data`; its hash and license are copied beside browser artifacts.
Before public distribution, include all dependency notices and confirm the
pinned Slipstream license/permission (no explicit declaration was found earlier).

## Controls and tests

Left drag pans; right drag adjusts yaw/pitch; middle drag rolls; wheel dollies;
Space pauses; R resets; +/- changes the tail (8–78). Focus the canvas. Context
loss stops submissions; reload to rebuild resources (no in-place restoration).

Use host `uv` for Playwright; running host Python extensions inside a Nix shell
may fail to find host `libstdc++`. Obtain Chromium from this repo's locked shell:

```sh
export CHROMIUM="$(nix develop -c bash -c 'command -v chromium')"
python3 web/test_build_tools.py
uv run --with-requirements web/requirements.txt web/browser_smoke.py --scene abi
uv run --with-requirements web/requirements.txt web/browser_smoke.py --scene live
uv run --with-requirements web/requirements.txt web/browser_smoke.py --scene live --deterministic
uv run --with-requirements web/requirements.txt web/browser_smoke.py --scene live --exercise --tail-bounds
uv run --with-requirements web/requirements.txt web/browser_smoke.py --scene live --exercise --dpr 2
uv run --with-requirements web/requirements.txt web/browser_smoke.py --scene live --lifecycle
uv run --with-requirements web/requirements.txt web/browser_smoke.py --scene live --frames 600
```

Run the separate ABI build stage before its gate. Isolated C++ witnesses use
`--scene geometry` and `--scene feedback`. Diagnostics/screenshots/hashes go to
`<cache>/*evidence*/`; inspect images as well as readiness/error JSON. The stress
and DPR gates use narrower viewports to bound SwiftShader fragment workload.
Full-resolution software rendering is slow, not a 60 fps claim.

`--deterministic` runs 65 exact ticks and checks all 434 float32 uniforms against
native Jolt emission. It is separate from interactive tests. Desktop regression
and tolerant feedback-region image comparison:

```sh
jolt -M:test
xvfb-run -a jolt -M:run --frames 65 --capture desktop.ppm
uv run --with-requirements web/requirements.txt web/compare_capture.py \
  desktop.ppm "${WASM_BUILD_ROOT:-.cache/wasm}/live-parity-evidence/canvas.png"
python3 web/measure.py
```

Image comparison excludes the different HUD, downsamples desktop and permits
at most one vertical pixel of registration; it is not byte-identical raster parity.
The historical reports in `docs/wasm-evidence/` describe the original toolchain;
`docs/wasm-evidence/self-contained/` records fresh-cache validation of this build.

## Architecture and remaining limits

- Shared `feedback.model` and `visuals/effect` execute in Chez Wasm. C++ uses
  actual Slipstream/Slughorn atlas/effect rendering and FreeType text; no Raylib.
  Browser frames own Chez/Jolt and GL. C retains no Scheme objects.
- `web/chez_host.c.inc` is our static-symbol/frame host, inserted into **pristine**
  pinned Chez main.c. `web/prepare.py` adapts a disposable Slipstream copy to GLES3.
  Neither upstream checkouts nor the desktop native dependency are patched.
- A bounded float buffer transports matrices/metadata; a mutable uniform extension
  reuses effects and caches variants by tail. Larger tails require sufficient
  fragment uniforms. This is not a general Glimmer web backend or full HUD port.
- The fresh consistent toolchain now passes the tested **direct mixed uint64 and
  float calls** as well as adapters. The earlier mismatched host/xpatch/target
  failures are preserved as historical evidence, not a current unsupported-ABI
  claim. The entire Slipstream FFI/closure surface is still not validated.
- Jolt remains pinned at experimental 0.8.21; the desktop release requirement is
  not changed. Wasm contains Chez's bytecode interpreter/native renderer, not
  direct Wasm compilation of Jolt functions. Other hosts, browsers, hardware
  GPU performance, peak/live memory and long leak/GC stress remain open.
- Requires WebGL2 + EXT_color_buffer_float, workers and cross-origin isolation.
  Public hosting needs HTTPS and COOP/COEP for runtime/assets/workers, or a scoped
  isolation service-worker bootstrap such as the separate `pages` branch. That
  branch is a static snapshot and is not automatically replaced by source builds.
