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
- [ ] P2 — Serve and automate Chromium; record errors/readiness and inspect a
  screenshot proving Slipstream vector geometry and text in WebGL2. Exercise
  typed effect uniforms (especially mat3) and the application's full shader.
- [ ] P3 — Validate the broader Slipstream ABI on the sibling's threaded Chez
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
