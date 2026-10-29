# Optional Wasm target: initial feasibility research

> Superseded by execution: the actual Slipstream renderer now runs in an optional
> Jolt/Chez Wasm prototype, including controls, tail variants and parity gates.
> See [wasm-plan.md](wasm-plan.md) and [../web/README.md](../web/README.md).
> The assessment below preserves the initial, pre-build research; its proposed
> separate-renderer preference was not adopted. WebGL platform glue proved
> tractable; the measured ABI issues were handled by small pointer adapters.

## Verdict

**Feasible as a separate experimental target; not runnable unchanged today.**
Keep Jolt + Slipstream/OpenGL as the primary desktop implementation. The lowest
risk browser route is the sibling project's Chez `tpb32l` Wasm runtime plus a
small WebGL2 renderer for this application's existing analytic shader. A full
Slipstream browser port is a separate, much larger library project.

This is a source/evidence audit, not a successful Wasm build of Picture Plane.
No browser execution, performance, or visual parity is claimed here. Existing
application sources, dependencies, setup, and desktop entry point are unchanged.

## Evidence and version boundaries

Inspected this project's current working-tree sources (including local model and
visual changes), Slipstream pin `d2f7f3d87a37ffcf25e66c27b88e91d4480ea308`,
and sibling `../jolt-wasm-raylib` at `c85ca23`.

Important: the sibling's top-level `REPORT.md` and `docs/ARCHITECTURE.md` predate
its latest successes. Prefer the later experiment evidence:

- [EXP-015](../../jolt-wasm-raylib/experiments/EXP-015-jolt-raylib-static/README.md):
  Jolt calls statically registered signed-int32 C functions; browser mouse/key
  input reaches the C-owned render loop.
- [EXP-017](../../jolt-wasm-raylib/experiments/EXP-017-jolt-flappy/README.md):
  an owner-thread Scheme wrapper calls the Jolt `frame!` Var each frame. Jolt
  owns persistent gameplay state; C renders bounded commands. Chromium reports
  39 Jolt-driven frames and consumed Space/click input. This is not merely a
  standalone Chez or C rendering witness.
- [EXP-018](../../jolt-wasm-raylib/experiments/EXP-018-jolt-size/README.md):
  that app passes again with Jolt 0.8.21 (`5b46858a`), matched Chez
  `7fadeee45fcc0135b17f5c1a926157004f898339`, patched threaded `tpb32l`, libffi,
  and browser isolation. Scripts depend on prerequisite build trees, not a
  standalone clean bootstrap. Its uncompressed Wasm + JS + data total is
  17,282,493 bytes, mostly boot/data; this is context, not this app's size.

This app documents Jolt 0.8.23+. Upgrading the sibling toolchain to that version
must be validated rather than assuming the 0.8.21 result transfers. The local
`../jolt` checkout is older (`6cb7d2ec`). Cross-build host, xpatch, target boots,
and kernel must be revision/machine matched; EXP-018 records failures otherwise.

## What transfers, and what does not

| Component | Assessment |
| --- | --- |
| `feedback.model` | Strong reuse candidate: pure maps/vectors, homographies, bounded 60 Hz stepping, input state. No native graphics dependency. Prove numeric/test parity on `tpb32l`. |
| `feedback.visuals/fragment` | Strong reuse candidate: analytic rectangle/crosshair coverage, `mat3` transforms, derivatives, decay and coloring. Requires a standalone shader wrapper. |
| `column-major`, hidden matrices, inverse-frame values | Reuse through a small pure render-payload function; currently mixed into Slipstream effect descriptions. |
| `visuals/scene` | Slipstream hiccup, font paths and scene effects are renderer-specific; not directly consumable by WebGL or Raylib. |
| `feedback.main` | Desktop-specific Glimmer lifecycle, native input, filesystem font detection, and PPM output. Leave it desktop-only. |
| `native/libslipstream.so` | A Linux binary cannot be loaded into the browser. Recompile selected C/C++ code and statically register symbols, or avoid it for the browser target. |

This is especially tractable because the feedback is **not framebuffer recursion**:
there is one quad and 48 projective vector histories. A browser can evaluate the
same analytic coverage without Slughorn tessellation, font atlases, or feedback
textures. Do not replace it with a superficially similar raster-feedback effect.

## Why compiling Slipstream unchanged is insufficient

At the pinned dependency, inspected `native/CMakeLists.txt`,
`native/reactive_renderer.cpp`, `native/{advanced_shaders,compositor}.cpp`,
`src/slipstream/{ffi,glimmer_renderer}.clj`, and the app entry point:

1. CMake builds a **shared** C++20 library, fetches desktop GLFW/GLAD, and finds
   host FreeType with pkg-config. A web build needs separate Emscripten static
   targets, GLES headers/context creation, and cross-built dependencies/assets.
2. Renderer shaders use `#version 330 core`; the context requests OpenGL 3.3.
   WebGL2 uses GLSL ES 3.00, with explicit precision and a platform shader wrapper.
   Shader text/version replacement alone is not a complete backend port.
3. Atlas upload formats include floating-point and integer textures, including
   RGB32F. Validate WebGL2 format/type/filter support and pixel unpack alignment;
   compositor RGBA16F render targets require capability/extension checks.
4. `slipstream.ffi` exposes pointers, strings, floats, booleans, structs and
   uint64 counts. The sibling's successful app boundary is signed int32 scalar
   calls, not proof of all these ABI shapes. Direct bindings need separate
   memory-layout, lifetime, string and float tests on 32-bit Wasm.
5. Glimmer's `run-loop!` is a synchronous loop. Browser frames must return to the
   event loop, with Jolt callbacks on the proven Chez/graphics owner thread.
   The sibling's frame-host integration is the useful precedent, not the desktop
   blocking loop. Do not move rendering to an arbitrary evaluator worker.
6. Fonts must be bundled/preloaded, not discovered in host `/usr/share/fonts`.
   Native capture paths also need a browser-specific download/capture adapter.

A complete port could eventually preserve Slipstream scenes across platforms,
but is disproportionate to this application's one-quad feedback renderer.

## Recommended architecture: additive, desktop-first

```text
                     feedback.model (shared Jolt)
                       /                  \
 desktop main + visuals                    web main + pure render payload
 Glimmer / Slipstream                      Chez tpb32l Wasm
 OpenGL 3.3                                owner-thread C facade
                                           WebGL2 quad shader + HTML HUD
```

- Keep `jolt -M:run`, `scripts/setup.sh`, native library pins, and captures as-is.
- Add an opt-in web entry/build script and dependency configuration that does
  **not resolve or load desktop Slipstream FFI**. A separate `web/deps.edn` or
  alias with replacement dependencies can isolate it; compiler source paths
  must still include the shared model.
- Only when implementing, extract the analytic hook and matrix payload into a
  pure shared namespace. Keep the Slipstream effect/scene adapter in `visuals`.
  Generate shader source from that shared definition rather than hand-copying it.
- Browser renderer: a fullscreen quad with a GLSL ES 3.00 wrapper implementing
  the same `[-1.6,1.6] × [-1,1]` coordinate mapping and shader-local offset.
  Use HTML for the HUD initially (explicitly not a Slipstream text parity claim).
- Reuse the sibling's owner-thread callback and static-symbol mechanism. Raylib
  can host the quad if that simplifies reuse, but is not required by the effect.
  Existing rectangle/circle commands alone cannot render this shader.

### Data boundary to prove early

Each frame needs 48 column-major inverse mat3 values (432 components), decay,
and time. Float32 GPU matrix data alone is 1,728 bytes/frame, about 104 KB/s at
60 Hz; bandwidth is small, but hundreds of FFI calls and Jolt allocation may not
be. This says nothing about measured frame time.

Do not assume float/pointer FFI works because integer commands do. First prove
float arguments and bounded bulk upload on the actual target. An initial
int32-only prototype can transport float32 **bit patterns** through signed words
and reconstruct them in C with `memcpy`, with explicit packing tests; that
packing path itself still needs implementation/proof. Avoid arbitrary fixed-point
quantization of inverse homographies, especially near small denominators.

Use a bounded staging buffer and commit only complete frames. C retains no Jolt
object pointers. Validate indices, lengths, non-finite values, and ownership.
Query fragment uniform limits and shader compile/link logs: 48 mat3 uniforms
consume substantial capacity, and the unrolled coverage shader is comparatively
large. WebGL2 is the sensible initial baseline; WebGL1 adds avoidable constraints.

Input must match `model/update-input`: Y-up model-space mouse coordinates,
left/right/middle buttons, wheel delta, Space and R. Handle device pixel ratio,
resize, canvas focus, context-menu suppression, wheel prevention, pointer capture,
and clearing held inputs on blur. Drive `advance` with monotonic elapsed time;
retain its bounded catch-up and deterministic one-tick-per-render capture mode.

## Proposed proof order / acceptance gates

1. **Runtime/model:** build only the shared model on a version-matched Wasm
   toolchain. Run deterministic native/Node/browser traces (initial state,
   history depth, project/inverse tolerances, pause/reset, drag and scroll).
2. **GPU without Jolt:** compile the shared 48-frame shader in WebGL2; render
   known identity/tilted histories and hidden matrices. Inspect screenshots and
   compile logs before adding the runtime/FFI boundary.
3. **Boundary:** round-trip matrix components, commit one complete payload, and
   render a deterministic 65-frame fixture. Compare with desktop capture using
   numerical/pixel tolerances, not necessarily byte equality across GPUs.
4. **Interaction/lifecycle:** Jolt-driven input and 600+ frames; pause/resume,
   R reset, all drags, wheel, resizing/DPR, blur, background-tab return, context
   loss and error reporting. Keep the existing desktop tests/capture green.
5. **Practicality:** measure startup/download sizes, CPU/GPU frame times,
   allocations and longer-running memory behavior on actual browsers/devices.
   The 48-history derivative-heavy fragment shader may be the bottleneck.

Threaded Chez requires SharedArrayBuffer/cross-origin isolation (normally COOP
and COEP headers), appropriate worker/asset serving, and HTTPS or localhost.
The sibling has isolated serving and a scoped service-worker deployment example;
copy its deployment constraints as well as its compiler commands.

## Alternatives

- **Full Slipstream WebGL2 port:** best eventual renderer/API reuse, highest
  scope; needs upstream platform separation plus ABI and rendering conformance.
- **Gambit → JavaScript + WebGL:** Jolt's documented demo-grade browser backend,
  not Wasm and not compatible with the existing native FFI. Could share the pure
  model with a new JS bridge, but does not follow the requested Chez/Wasm path.
- **Rewrite the model in JavaScript:** easy browser packaging, but loses shared
  Jolt behavior and is unnecessary given the sibling's demonstrated runtime.

References: [Jolt backends](https://jolt-lang.net/docs/scheme-backends.html),
[Jolt libraries](https://jolt-lang.net/docs/libraries.html), and the experiment
links above. These establish available building blocks, not completed support
for this application's renderer.
