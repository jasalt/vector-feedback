# Slipstream Wasm execution plan

## Goal and constraints

Add an opt-in browser target using Slipstream itself, keeping the desktop
renderer, `jolt -M:run`, dependencies and setup primary and unchanged. Do not
substitute Raylib or a separately reimplemented feedback renderer. Reuse the
sibling Chez/Wasm experiment only after proving Slipstream's graphics layer.

Use small atomic commits. Track observations here, including failed gates;
build success is not browser/render success. Keep generated artifacts ignored.
Do not modify dependency caches or sibling repositories: apply reproducible
platform patches to build-local copies of pinned sources.

## Stages

- [x] P0 — Record scope, proof order and baseline.
- [x] P1 — Reproducible Emscripten build of pinned Slipstream and its dependencies;
  conditional GLES3 shader/context glue; compile an actual Slipstream C++ scene.
- [x] P2 — Serve and automate Chromium; record errors/readiness and inspect a
  screenshot proving Slipstream vector geometry and text in WebGL2. Exercise
  typed effect uniforms (especially mat3) and the application's full shader.
- [x] P3 — Validate the broader Slipstream ABI on the sibling's threaded Chez
  Wasm target: pointers, float arguments, structs, strings, counts and errors.
  Keep toolchain/Jolt revisions explicit; do not infer ABI support from build.
- [ ] P4 — Connect Jolt model + Slipstream scene to owner-thread browser frames;
  retain shared shader/model and native desktop adapter. Bundle a redistributable
  font and isolate browser dependencies from native shared-library loading.
- [ ] P5 — Input/lifecycle and parity: deterministic 65-frame capture, numerical
  model parity, all controls, 600 frames, resize/DPR/blur/background behavior,
  error and context-loss handling; desktop regression tests and capture.
- [ ] P6 — Document reproducible build/serve commands, deployment isolation,
  measured size/startup/frame-time/memory limitations; final status and handoff.

Stages may stop at an observed blocker, recorded with the exact failed command
and next action. Partial witnesses must not be labeled a working Jolt port.

## Validation and ownership

1. C++/WebGL2 witness first, without Chez, to isolate platform glue.
2. Actual Slipstream resources, atlas, shader compilation, submission and capture;
   not just a canvas clear or custom standalone shader.
3. HTTP browser automation with page/console/request diagnostics and screenshots.
4. Chez/Jolt calls and GL stay on the proven frame owner. No retained unrooted
   Scheme objects and no evaluator-worker graphics calls.
5. Baseline `jolt -M:test` and desktop smoke capture remain independent gates.

## Progress / evidence

### P0 — baseline and planning

- Initial source working tree is clean; only the prior research document is
  untracked. Include that document with this planning commit.
- Desktop dependencies: Slipstream `d2f7f3d87a37ffcf25e66c27b88e91d4480ea308`,
  Slughorn `3ad0529d59a87bc29bb56ea91c02eae073ce6e97` (verify against setup
  script before building; script is authoritative).
- Environment: Fedora Lima (`HOSTNAME=lima-default`), Nix available, `emcc` not
  on default PATH. Sibling has a locked Emscripten/Chromium development shell.
- Research correction: WebGL-capable dependencies make the graphics work a
  platform integration task; its difficulty is not established until tested.
  The broad Slipstream FFI is unvalidated, not known to be unsupported.

### P1 — C++ platform build (PASS compilation only)

- `nix develop ../jolt-wasm-raylib -c bash scripts/wasm-build.sh` exited 0.
  Emscripten 6.0.8, C++20, pinned Slipstream/Slughorn/MSDFgen, Emscripten
  FreeType port. Generated log: `.cache/wasm/build.log`.
- Added a separate static target, GLES3 headers/direct symbols, GLSL ES 3.00
  precision qualifiers, GLES context hints and explicit compositor extension
  requirement. Only a disposable source copy is changed.
- Witness builds a stroked rectangle and FreeType text through the real C ABI;
  browser rendering is still unverified until P2. No Chez/Jolt integration yet.
- Baseline attempt `nix develop ../jolt-wasm-raylib -c jolt -M:test` failed
  before tests: native `libslipstream.so` cannot find `libfreetype.so.6` in that
  isolated Nix environment. This is not a test failure in model logic; retry
  with a suitable desktop environment separately.
- Concurrent user changes appeared in `README.md`; leave them out of commits.

### P2a — real vector geometry and font (PASS; P2 still in progress)

- HTTP + Chromium 152/SwiftShader automation passes with zero page, console,
  or request errors. Report and screenshots: `.cache/wasm/evidence/`.
- Visually inspected `canvas.png`: a crisp green rectangular outline and readable
  pale-blue `SLIPSTREAM / WEBGL2` above it, on a dark background. This proves
  actual atlas/FreeType/vector rendering, not just context initialization.
- First browser run exposed GLFW extension-query and pre-main-loop swap timing
  issues. Enable `EXT_color_buffer_float` through Emscripten and let RAF own
  timing. Next run exposed leading-newline GLSL ES version rejection; remove
  that newline. A witness argument used invalid curve precision 0; corrected
  to 32. Original failed JSON reports retained in `.cache/wasm/`.
- Initial readiness-only gate missed invisible text (em-space translation was
  passed directly as world-space). Screenshot inspection caught it; scale the
  layout translation and rerun. Font is now visibly verified.
- Automation environment: running uv/Playwright inside Nix could not load host
  `libstdc++`; run host uv with `CHROMIUM` pointing to the shell's Chromium.
  A 35-second tool timeout interrupted one run; a 100-second retry passed.
- Command: `CHROMIUM=<chromium executable> uv run --with playwright
  web/browser_smoke.py`. Full 48-matrix application shader is the next gate.

### P2b — full application effect (PASS)

- Native Jolt emits the **current** `visuals/effect` shader and uniforms after
  65 deterministic steps with `:tail 48`. No shader or homography reimplementation
  in C++; only a generated header under `.cache/wasm/`.
- Current desktop sources changed during this task (fragment is now generated
  per tail length). The fixture follows the public effect result, not the
  earlier removed `visuals/fragment` Var. Desktop files remain untouched.
- Rebuilt and ran `web/browser_smoke.py --scene feedback`: exit 0, no browser
  diagnostics. Screenshot `.cache/wasm/feedback-evidence/canvas.png` inspected:
  many colored shrinking/rotated/projectively tilted rectangle outlines and
  central crosshair trails, with readable Slipstream title. All 48 mat3 uniforms
  compile/link and render through the real Slipstream effect interface.
- This is a static Jolt-authored fixture rendered by C++, **not** Jolt executing
  in Wasm or interactive model execution. Those are P3/P4.

### P3 — real Jolt/Slipstream ABI (PARTIAL direct; PASS pointer adaptation)

- Built a private copy of the sibling's matched threaded Chez/libffi runtime,
  linked pthread-compiled Slipstream/MSDFgen/FreeType and registered real C ABI
  symbols. No sibling or dependency-cache edits. Script:
  `nix develop ../jolt-wasm-raylib -c bash scripts/wasm-abi-build.sh`.
- Chromium under COOP/COEP reaches `SLIPSTREAM-WASM-ABI-PASS`, with zero page,
  console or request errors. Report: `.cache/wasm/abi-evidence/browser.json`.
- Direct mixed `ss_path_command(pointer,uint32,pointer,uint64)` fails argument
  count validation, although a single-argument uint64 probe sees `4` correctly.
  Direct mixed float define-shape probe receives scale `0`, not `1.0`.
  Float memory probe correctly reads `-1.18`. These are measured target ABI
  problems, not missing WebGL support. No upstream runtime patch is applied.
- Small web-only adapters widen bounded uint32 counts in C and read float
  arguments from pointers. Through these adapters Jolt creates/builds an atlas,
  defines a rectangle, reads real shape structs/floats, scales its output quad,
  checks bool return, gets a borrowed error string and releases foreign memory.
- Initial test erroneously wrote nil to a pointer field; use `ffi/null`.
  Initial C linker selected nonexception C++ libraries; use
  `-sDEFAULT_TO_CXX=1 -fexceptions`. Failure logs/JSON retained in cache.
- This **does not** validate all direct Slipstream bindings or its full Glimmer
  integration. P4 will use the measured pointer/scalar adapter boundary rather
  than claim that unchanged desktop FFI works on this toolchain.
