# Third-party notices

This package contains a Chez portable-bytecode interpreter and native renderer
compiled to WebAssembly, plus a preloaded Jolt application and font. Source
revision/tool records are in `build-environment.json`; runtime hashes are in
`build-size.json` and `SHA256SUMS`.

- Jolt: EPL-2.0, [pinned source](https://github.com/jolt-lang/jolt/tree/5b46858a171f30949f5b09eb484bc6c5ff93c6ea).
  Original notices and component licenses are in `licenses/Jolt-*` and
  `licenses/jolt-components/`. Some listed components may be unused by this app.
- Chez Scheme: Apache-2.0 and bundled notices. Its upstream revision is
  `7fadeee45fcc0135b17f5c1a926157004f898339`; runtime build/patch lineage is the
  [Jolt Wasm experiment](https://github.com/jasalt/jolt-wasm-raylib-experiment),
  EXP-014/017/018. The app's platform adaptations and build instructions are in
  [the source commit](https://github.com/jasalt/vector-feedback/tree/d8963ae4056caa7565566a92509d67f1a90114c4).
- Slughorn: MIT, copyright 2026 AlphaPixel LLC.
- MSDFgen and nlohmann/json: MIT; see included notices.
- FreeType: distributed under the FreeType License (FTL), not the alternative
  GPL option. Portions of this software are copyright © 2026 The FreeType
  Project (www.freetype.org). All rights reserved. See `licenses/FreeType-*`.
- Adwaita Mono: see `runtime/font-LICENSE.txt`; the exact font hash is in
  `runtime/font-info.json`.
- libffi, Emscripten, LLVM C++/compiler runtime, musl, GLFW API support, lz4,
  and zlib: notices/license texts are preserved under `licenses/`.

## Redistribution clarification still needed

The pinned Slipstream checkout
`d2f7f3d87a37ffcf25e66c27b88e91d4480ea308` contains no explicit license file or
license declaration found during packaging. This package does **not** invent or
assign one. Confirm the applicable permission with the copyright holder before
public redistribution. Including the other notices does not resolve this gap.
