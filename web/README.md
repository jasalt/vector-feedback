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
```

Diagnostics and screenshots go to `.cache/wasm/evidence/`. The gate checks
readiness and browser errors; screenshots must also be inspected for semantic
content. A ready canvas alone does not prove correct geometry or text.

The legacy blocking GLFW example runner is deliberately not linked; the actual
reactive renderer is driven through its existing C ABI by browser frames.
