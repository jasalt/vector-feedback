# Opt-in Slipstream WebGL2 platform witness

This target builds the pinned Slipstream C++ renderer and its Slughorn/MSDFgen/
FreeType dependencies. It is **not yet a Jolt browser application**. Desktop
setup and `jolt -M:run` are unchanged. Progress: [../docs/wasm-plan.md](../docs/wasm-plan.md).

With Emscripten, CMake, Git, Python and a TTF font available:

```sh
bash scripts/wasm-build.sh
python3 -m http.server 8000 --bind 127.0.0.1 --directory .cache/wasm/build
# Visit http://127.0.0.1:8000/witness.html
```

In this workspace the existing locked sibling shell can supply the tools:

```sh
nix develop ../jolt-wasm-raylib -c bash scripts/wasm-build.sh
```

The build also requires native Jolt (`JOLT` override). It emits the current
application effect and a deterministic 65-tick/48-history fixture without loading
the desktop native dependency. `?scene=feedback` renders that fixture through
Slipstream's mat3 effect interface; it is not yet live Jolt execution in Wasm.

Set `WEB_FONT` if Adwaita Mono is not installed. The font is preloaded at build
time, not resolved from browser host paths. Before publishing, supply and ship
its license. This witness requires WebGL2 and EXT_color_buffer_float for
Slipstream's compositor; capability failure is explicit. Chez's later pthread
integration will additionally need cross-origin isolation.

`prepare.py` applies fail-fast platform adaptations to a disposable pinned
source copy under `.cache/wasm/`. The original desktop source is never patched.
Browser gate (host `uv`, with Chromium on PATH or `CHROMIUM` set):

```sh
uv run --with playwright web/browser_smoke.py
uv run --with playwright web/browser_smoke.py --scene feedback
```

Diagnostics and screenshots go to `.cache/wasm/evidence/`. The gate checks
readiness and browser errors; screenshots must also be inspected for semantic
content. A ready canvas alone does not prove correct geometry or text.

## Experimental Jolt ABI gate

Requires the sibling's prepared EXP-018 native host/target pack, EXP-014 libffi,
EXP-017 Chez tree and pinned Jolt archive (see that project's EXP-018 commands).
This is currently an integration experiment, **not a clean-room bootstrap**.
`WASM_REFERENCE` overrides the sibling path. It is read-only; all changes/builds
are in this project's `.cache/wasm/`.

```sh
nix develop ../jolt-wasm-raylib -c bash scripts/wasm-abi-build.sh
uv run --with playwright web/browser_smoke.py --scene abi
```

## Live Jolt-owned feedback prototype

```sh
nix develop ../jolt-wasm-raylib -c env WASM_MODE=live bash scripts/wasm-abi-build.sh
uv run --with playwright web/browser_smoke.py --scene live
```

Serve `.cache/wasm/chez-live/em-tpb32l/bin/tpb32l/` with COOP/COEP headers and
open `scheme.html`. This runs shared `feedback.model` and `visuals/effect` inside
Chez Wasm each frame, with actual Slipstream C++ graphics and a preloaded font.
The browser prototype has a fixed 48-frame tail and a simplified HUD, not a
complete Glimmer browser backend. See the plan for validation and limitations.

The test records direct mixed uint64/float ABI failures and validates small
pointer-based adapters. It does not claim unchanged desktop FFI compatibility.

The legacy blocking GLFW example runner is deliberately not linked; the actual
reactive renderer is driven through its existing C ABI by browser frames.
