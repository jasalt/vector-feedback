# Optional Jolt + Slipstream WebGL2 target

**Working experimental browser target. Desktop remains primary:** normal
`scripts/setup.sh` and `jolt -M:run` are unchanged. The browser runs the shared
Jolt model and effect shader inside threaded Chez Wasm, with actual Slipstream/
Slughorn vector graphics and FreeType text. No Raylib renderer is used.

Progress and evidence: [../docs/wasm-plan.md](../docs/wasm-plan.md).

## Build and run in this workspace

Requires the sibling `../jolt-wasm-raylib` locked development environment and
its **prepared** EXP-018 native Chez host/target pack, EXP-014 Emscripten libffi,
EXP-017 Chez tree and pinned Jolt archive. Follow that project's EXP-018 prepare
instructions first. These prerequisites are substantial: this integration is
**not yet a clean-room bootstrap or a supported upstream Jolt Wasm release**.
`WASM_REFERENCE` overrides the sibling path; scripts only read it.

```sh
# C++ platform witness, dependencies and shared shader fixture:
nix develop ../jolt-wasm-raylib -c bash scripts/wasm-build.sh
# Live Jolt model + Slipstream:
nix develop ../jolt-wasm-raylib -c env WASM_MODE=live bash scripts/wasm-abi-build.sh
python3 web/serve.py
# Open http://127.0.0.1:8000/scheme.html
```

The first script needs Emscripten, CMake, Git, Python, native Jolt and a font.
It pins Slipstream/Slughorn/MSDFgen and applies fail-fast web adaptations to a
**disposable source copy** under `.cache/wasm/`. It never patches desktop source
or dependency caches. `JOLT` overrides native fixture emission only; cross-builds
use the sibling's explicitly revision-matched Jolt/host/target pack.

Set `WEB_FONT` and `WEB_FONT_LICENSE` for a different redistributable TTF.
Default: installed Adwaita Mono and its system license. The font is preloaded
inside `.data`; the license and a font hash are copied beside browser artifacts.
Before publishing, include licenses/notices for all bundled dependencies too.

Controls: left drag pan; right drag yaw/pitch; middle drag roll; wheel dolly;
Space pause; R reset; +/- adjust tail (8–78). Canvas focus and a three-button
mouse are recommended. Context loss stops submissions; use the reload button
to rebuild resources. In-place restoration is **not** implemented.

## Tests

Host `uv` plus Chromium are needed. Avoid running host Playwright inside the
Nix shell if its Python extensions cannot find host `libstdc++`.

```sh
export CHROMIUM="$(nix develop ../jolt-wasm-raylib -c bash -c 'command -v chromium')"
uv run --with-requirements web/requirements.txt web/browser_smoke.py --scene live
uv run --with-requirements web/requirements.txt web/browser_smoke.py --scene live --deterministic
uv run --with-requirements web/requirements.txt web/browser_smoke.py --scene live --exercise --tail-bounds
uv run --with-requirements web/requirements.txt web/browser_smoke.py --scene live --exercise --dpr 2
uv run --with-requirements web/requirements.txt web/browser_smoke.py --scene live --lifecycle
uv run --with-requirements web/requirements.txt web/browser_smoke.py --scene live --frames 600
```

The last gate uses a narrower viewport to bound SwiftShader fragment workload.
Full-resolution software rendering is slow and can exceed several-minute test
budgets. Screenshots pause submissions before capture; readiness/error checks
alone are not visual correctness proof. Diagnostics, screenshots and hashes go
to `.cache/wasm/*evidence*/`. Inspect screenshots as well as JSON results.

Native desktop regression and tolerant feedback-region image comparison:

```sh
jolt -M:test
xvfb-run -a jolt -M:run --frames 65 --capture .cache/wasm/desktop.ppm
uv run --with-requirements web/requirements.txt web/compare_capture.py \
  .cache/wasm/desktop.ppm .cache/wasm/live-parity-evidence/canvas.png
python3 web/measure.py
```

`--deterministic` runs 65 exact ticks and compares all 434 float32 uniforms to
native Jolt emission. Image comparison excludes the different HUD, downsamples
the desktop capture and permits at most one vertical pixel of registration.
It is not byte-identical pixel parity.

## Isolated witnesses

```sh
# Reduced direct ABI failures + successful pointer adapters:
nix develop ../jolt-wasm-raylib -c bash scripts/wasm-abi-build.sh
uv run --with-requirements web/requirements.txt web/browser_smoke.py --scene abi
# C++ only geometry/font and a native-Jolt-authored static feedback fixture:
uv run --with-requirements web/requirements.txt web/browser_smoke.py --scene geometry
uv run --with-requirements web/requirements.txt web/browser_smoke.py --scene feedback
```

## Architecture and limitations

- Browser callbacks own Chez/Jolt and GL on the same owner thread. C retains no
  Scheme objects. A bounded foreign float buffer carries matrices and metadata.
- The pinned target mis-marshals the tested mixed uint64 and float direct calls.
  Small count/float-memory adapters avoid that ABI boundary. Unchanged desktop
  Slipstream FFI/Glimmer bindings are **not** advertised as browser compatible.
- `visuals/effect` and `feedback.model` are shared unchanged. C++ adapts the one
  quad and font scene; the HUD is HTML. This is not a general Glimmer web backend.
- A web-only mutable uniform extension reuses effects; tail variants are cached
  by tail length. Large tails depend on available fragment-uniform capacity.
- Requires WebGL2 + `EXT_color_buffer_float`, workers, SharedArrayBuffer and
  cross-origin isolation. `serve.py` binds loopback and sends COOP/COEP. Deployment
  needs HTTPS (or localhost), suitable headers for HTML/workers/assets, and all
  generated `.html`, `.js`, `.wasm`, `.data` files. Plain GitHub Pages without an
  isolation mechanism is insufficient; none is installed automatically here.
- Pinned experimental runtime is Jolt 0.8.21 / Chez `tpb32l`, not a claim that
  current desktop Jolt releases have supported browser builds. Generated Wasm is
  the Chez bytecode interpreter and native renderer, not direct Wasm compilation
  of Jolt functions. Hardware/browser portability and production performance
  remain open; see the measured limitations in the plan.
