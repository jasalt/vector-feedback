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
- [x] P4 — Connect Jolt model + Slipstream scene to owner-thread browser frames;
  retain shared shader/model and native desktop adapter. Bundle a redistributable
  font and isolate browser dependencies from native shared-library loading.
- [x] P5 — Input/lifecycle and parity: deterministic 65-frame capture, numerical
  model parity, all controls, 600 frames, resize/DPR/blur/background behavior,
  error and context-loss handling; desktop regression tests and capture.
- [x] P6 — Document reproducible build/serve commands, deployment isolation,
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

### P4 — live Jolt-owned feedback (PASS prototype, not full Glimmer port)

- `WASM_MODE=live` with `scripts/wasm-abi-build.sh` builds a separate
  `chez-live` module. A named owner-thread Scheme callback resolves the live
  Jolt `feedback.web/frame!` Var. No evaluator worker draws and C holds no
  Scheme object pointers.
- Jolt runs the unchanged shared model, input update and `visuals/effect` each
  frame, writing a bounded foreign float buffer. The same actual Slipstream
  scene/effect/atlas/FreeType code from P2 renders it. A web-only uniform-update
  extension reuses one effect instead of leaking a cached effect per frame.
- `web/browser_smoke.py --scene live` passes with isolation, boot token, model
  frame progression and no browser errors. Observed frame 5/time 0.5, later
  frame 9/time 0.88 (elapsed-time catch-up on software rendering).
- Inspected `.cache/wasm/live-evidence/canvas.png`: colored projective rectangle
  trails/crosshair and readable vector text. This time the model executes inside
  the Wasm module, not only during native fixture emission.
- Prototype fixes tail at 48; the newly added desktop +/- tail controls and
  full Glimmer scene/HUD reconciliation are not ported. Core drag/wheel/pause/
  reset input is wired but awaits P5 automation. Font is preloaded; publishing
  still needs its license. Toolchain remains pinned Jolt 0.8.21 experimentally,
  not the desktop application's supported-release requirement.

### P5a — deterministic parity and core controls (PASS; lifecycle still partial)

- Deterministic Wasm run stops after 65 rendered frames. All **434 float32
  uniform components match native Jolt's fixture exactly** (max absolute error
  0), including inverse matrices, decay and time. Report/screenshots:
  `.cache/wasm/live-parity-evidence/`.
- Automated pause (simulation time remains fixed), left/right/middle drag,
  wheel, R reset, blur while dragging, and resize pass. A 600-frame gate reaches
  601 frames, with zero page/console/request errors. Report:
  `.cache/wasm/live-controls-evidence/`. Observed changed pan/yaw/pitch/roll/zoom
  while paused; reset restores defaults. Canvas resizes to 684×428.
- Full desktop tests now pass: 7 tests, 33 assertions, 0 failures/errors.
  Running Nix Jolt outside its shell with host `LD_LIBRARY_PATH=/usr/lib64`
  resolves the existing native dependency. The loader emits a harmless ncurses
  version-info warning. Desktop 65-frame capture also exits 0 under Xvfb;
  `.cache/wasm/desktop.ppm`. No desktop source changes were needed.
- Added browser pointer capture, focus/wheel behavior, blur clearing,
  device-pixel-sized canvas resize, and explicit context-loss/reload handling.
  DPR/context-loss/background behavior and new desktop +/- tail controls still
  need dedicated gates; P5 is not marked complete yet.

### P5b — tail range, DPR and lifecycle (PASS prototype scope)

- +/- now selects shaders generated by the same shared `visuals/effect` and
  updates a bounded cache (one effect per reachable tail), not a second shader
  implementation. Automated 8/18/28/38/48/58/68/78 variants, endpoint clamping,
  reset and controls pass on Chromium/SwiftShader.
- DPR=2 controls and resize pass: 534×334 CSS pixels map to 1068×668 backing
  pixels. Readable vector text and colored trails visually inspected. Early
  high-DPR attempts timed out; CSS/backing-store separation was fixed and
  screenshot capture now pauses submissions, avoiding an overloaded software
  GPU queue. DPR tests use a narrower viewport to bound fragment workload.
- Background-tab return and synthetic WebGL context loss pass with **explicit
  reload recovery**, not in-place resource resurrection. An initial loss race
  caused Emscripten `glGetUniformfv` to dereference null; check native context
  loss before invoking Jolt/GL, not just the later DOM loss event. The failed
  stack is retained in `.cache/wasm/context-loss-uniform-failure.json`.
- Latest deterministic rerun still has exact 434-component float32 parity.
  Desktop-vs-browser central feedback ROI, excluding the intentionally different
  HUD, has normalized RGB MAE 0.01173 after desktop downsampling (threshold
  0.02). Comparison permits at most +/-1 vertical pixel for fractional CSS
  screenshot placement; latest capture needs offset 0. This is tolerant visual
  agreement, not byte-identical screenshots. `web/compare_capture.py` reproduces.
- Final 600-frame rerun passes at a 500-pixel viewport, no browser errors.
  Full-size software runs hit tool timeouts; progress showed continuing frames,
  not a deadlock (about 14 frames/10 seconds at 960×600). Smaller runs reach
  about 48 frames/10 seconds. This is a **slow software-rendered prototype**,
  not a 60 fps claim. `.cache/wasm/live-stress-evidence/` retains the passing
  600-frame report; tail/DPR/lifecycle reports are in separately named folders.

### P6 — build/serve, measurements and handoff (PASS experimental scope)

- [../web/README.md](../web/README.md) contains build, isolated serving,
  automation, ABI probes, capture comparison and measurement commands. Desktop
  remains the documented default. `web/serve.py` is loopback-only and sends
  COOP/COEP; runtime and copied font license serving were verified over HTTP.
- Font data is preloaded; its hash and license are copied beside artifacts.
  Python test dependencies are pinned in `web/requirements.txt`. Generated
  binaries, boots, profiles and caches stay ignored. Bash syntax, Python compile
  checks and `git diff --check` pass.
- Final runtime: HTML 2,509 B; JS 408,685 B; Wasm 2,283,465 B; data 17,261,795 B.
  Total 19,956,454 B; per-file gzip-9 total 10,232,275 B (not measured transfer).
  Boot/font are already inside data. Assertions, pthreads and C++ exceptions
  remain enabled; this is not a minimal-size release build.
- One final 960×600 SwiftShader run: navigation-to-ready 4,716.5 ms (includes
  first three frames). Sample model/FFI/instrumentation 137.8 ms, render/driver
  736.8 ms. These are **single samples**, not medians or isolated GPU timings.
  Wasm linear-memory capacity 104,529,920 B; live allocation count/peak RSS and
  long-run leak behavior are not measured. No hardware-GPU/60 fps claim.
- Small reports, source/tool pins, original reduced failures, hashes and a
  vision-inspected feedback screenshot retained in
  [wasm-evidence/](wasm-evidence/README.md). Earlier passing gates predate final
  observability/packaging changes; final instrumented smoke also passes cleanly.
- All planned prototype stages are executed. The original `deps.edn`, desktop
  source and native setup are unchanged. No sibling repository/cache was edited
  and no upstream patch or push was made. Work is split into atomic commits.

## Final status / follow-ups (not advertised as completed)

**Working optional Jolt + actual Slipstream Wasm prototype**, with shared model
and shader, browser controls and parity evidence. It is not a general Slipstream
or Glimmer browser release. Follow-ups before production/upstreaming:

- Replace prepared sibling build-tree prerequisites with a clean pinned bootstrap.
- Upgrade/validate the cross toolchain against the desktop's supported Jolt
  version; reduce/report the mixed float/uint64 ABI failures upstream.
- Generalize the platform/FFI boundary if full Glimmer scene reuse is required.
- Profile model allocation/bytecode execution, FFI writes and driver waits;
  remove test instrumentation from a future performance build and test hardware
  GPUs, uniform limits, other browsers and mobile input.
- Measure startup distributions, peak/live memory and longer GC/leak stress.
- Implement in-place context restoration if needed; current recovery reloads.
- Ship all dependency notices and validate isolation on the intended public host.
