# Owned Wasm toolchain boundary

The repo's `flake.nix`/`flake.lock` pin upstream Jolt, Chez (including submodules),
Nixpkgs and thus Emscripten/compilers. `pins.json` records matching source revisions
and libffi 3.5.2's release URL/SHA-256. Bootstrap currently supports Linux x86_64.
No sibling checkout, target pack or copied compiler executable is an input.

`../../scripts/wasm-bootstrap.sh` builds, in the selected disposable cache:

1. A writable copy of the locked Chez source with the owned patch applied.
2. A native `ta6le` host, then `bootquick XM=tpb32l` boots and host-matched xpatch.
3. A native 32-bit `tpb32l` kernel and target pack for Jolt's intermediate link.
4. Static pthread-enabled Emscripten libffi 3.5.2, verified before extraction.

The final app script builds a separate Wasm Chez kernel and statically registers
our Slipstream adapter functions; the native pack is not shipped to browsers.
All host/xpatch/target artifacts come from the **same patched Chez tree**.
`JOLT_NARROW_HASH=1` is set during emission and target compilation. Jolt's old
word-size patch is already upstream in the pinned version and is not reapplied.

Stage stamps allow retries after build failures. Fingerprints cover the lock,
pins and Chez patch. A changed fingerprint fails with cleanup instructions;
never combine a stale pack with a new host. Bump the bootstrap schema when
changing build logic/flags in a way that affects boot/ABI compatibility.
`WASM_BUILD_ROOT` selects a fresh cache for clean-room validation; default is
`.cache/wasm/`. The full entry point is `nix develop -c bash scripts/wasm-live-build.sh`.

## Chez patch provenance and scope

`patches/chez-emscripten-libffi.patch` is retained from the Jolt Chez/Wasm
experiment's EXP-014, sibling source commit `c85ca23`; base Chez revision
`7fadeee45fcc0135b17f5c1a926157004f898339`. Source reference:
https://github.com/jasalt/jolt-wasm-raylib-experiment/tree/c85ca23/experiments/EXP-014-jolt-tpb32l-emscripten/patches

It aligns PB argument slots, represents Wasm closure table indices explicitly,
exports Emscripten libffi/table helpers, and adds static symbol lookup. Chez's
Apache-2.0 license applies to its source; Jolt's license/notices remain in its
fetched source. This is a project-local compatibility delta, not an upstream
supported Wasm release. Copying the reviewed patch once into this repo does not
make the sibling a build-time dependency.

When changing the patch, regenerate **both** the host/xpatch and target boots.
The previous integration mixed an unpatched native host with patched targets;
its direct mixed-call ABI failures must be retested, not assumed identical with
this newly consistent bootstrap. Fresh-cache validation now passes both direct
mixed calls (path count and float scale) and the bounded pointer adapter. The
adapter remains in use for bulk uploads; this is not full FFI/closure conformance.
