# Slipstream Wasm prototype evidence

These top-level reports preserve the **original sibling-based integration**.
For the current repo-owned bootstrap and changed direct-ABI findings, see
[self-contained/](self-contained/README.md). Historical failures below are not
claims that the current consistently generated toolchain still fails those calls.

Small retained reports and one vision-inspected screenshot. Generated runtime,
boots, logs and additional screenshots remain under ignored `.cache/wasm/`.
All passing browser reports use HTTP automation, Chromium 152 and SwiftShader.
`environment.json` records pins, tools, font hash and unchanged desktop-source
hashes. `SHA256SUMS` covers this evidence set.

| Report | Scope |
| --- | --- |
| `abi.json` | Jolt creates/reads real Slipstream geometry through pointer adapters; direct mixed-call failures remain visible in messages. |
| `direct-abi-failure.json` | Original measured scale=0 instead of 1.0; not erased by adapters. |
| `parity.json`, `feedback.png` | 65 ticks, 434 float32 values exactly match native fixture. Screenshot inspected: colored projective rectangle/crosshair trails and readable vector title. |
| `controls-and-tail-bounds.json` | Pause, three drags, wheel, +/- variants 8–78, clamp/reset/blur/resize. |
| `dpr2.json` | Input and resize at DPR=2, smaller CSS viewport; screenshot also inspected during execution. |
| `lifecycle.json` | Background-tab return, actual WebGL loss/restore events, explicit full-module reload recovery. |
| `context-loss-before-guard.json` | Original Emscripten uniform-query failure before native lost-context guard. |
| `stress600.json` | 600+ Jolt frames at reduced viewport; not a full-resolution performance claim. |
| `capture-comparison.json` | Tolerant desktop/WebGL feedback ROI comparison; different HUD intentionally excluded. |
| `final-smoke.json` | Final instrumented module; one startup/frame/capacity observation, not a distribution. |
| `bundle-size.json` | Exact final runtime bytes, hashes and per-file gzip-9 proxy. Boot/font are already in `.data`. |

Tests were executed incrementally; earlier successful JSON reports predate the
final metrics/packaging additions. Failed reports are deliberately retained and
are not counted as passes. For exact commands and remaining scope see
[../wasm-plan.md](../wasm-plan.md) and [../../web/README.md](../../web/README.md).

## Measurement boundaries

The final single local run reached readiness in about 4.72 seconds (navigation
through three rendered frames, fresh browser profile, local HTTP). Its sampled
frame spent 137.8 ms in Jolt/model + FFI/instrumentation and 736.8 ms in render
submission/driver work; this is **not** isolated GPU timing or a median. Wasm
linear-memory **capacity** was 104,529,920 bytes, not live allocations or peak
process RSS. No hardware-GPU, mobile, Firefox/Safari or long-duration leak claim.

The central feedback ROI normalized RGB MAE is 0.01173 after desktop downsampling,
against a 0.02 acceptance threshold. Only +/-1 vertical pixel registration is
permitted for CSS screenshot rounding. Exact shader payload parity is stronger
than this tolerant raster comparison; neither establishes complete HUD parity.
