# Fresh-cache self-contained build validation

These reports supersede the earlier sibling-artifact prerequisites and direct
ABI findings, not the preserved historical observations in the parent folder.

Built from an initially empty `.cache/wasm-selfcontained` using **this repo's**
`flake.nix`/`flake.lock`, upstream source pins and owned Chez compatibility patch.
No prepared sibling host, pack, libffi or modified main.c was copied. Nix's normal
package/source cache is allowed; source builds are not claimed bit-reproducible.

Commands (all exited 0):

```sh
export WASM_BUILD_ROOT="$PWD/.cache/wasm-selfcontained"
nix develop -c bash scripts/wasm-bootstrap.sh
nix develop -c bash scripts/wasm-build.sh
nix develop -c bash scripts/wasm-abi-build.sh
nix develop -c bash scripts/wasm-live-build.sh
export CHROMIUM="$(nix develop -c bash -c 'command -v chromium')"
uv run --with-requirements web/requirements.txt web/browser_smoke.py --scene abi
uv run --with-requirements web/requirements.txt web/browser_smoke.py --scene live --deterministic
uv run --with-requirements web/requirements.txt web/browser_smoke.py --scene live --exercise --tail-bounds
python3 web/test_build_tools.py
```

- `environment.json`: pins, lock/patch fingerprint, native host/target-kernel
  architecture, generated pack/library hashes, pinned font/license and cache
  reuse/stale-input rejection results.
- `abi.json`: real Slipstream pointer/struct/memory/error operations and **direct
  mixed pointer/uint64 and pointer/float calls pass**. Observed count 4, scale 1.
  The bootstrap regenerates the host, patched xpatch and target together. The
  old mixed-call failures no longer reproduce; no universal FFI claim follows.
- `parity.json`: 65 deterministic ticks, all 434 float32 uniforms exactly match
  native emission (max error 0), with no browser diagnostics.
- `controls.json`: pause, drags, wheel, tail variants/clamps 8–78, reset, blur and
  resize pass. The longer/DPR/context-loss gates remain available but were not
  all rerun for this build-containment change; see historical reports for them.
- `feedback.png`: visually inspected; readable DejaVu vector text and expected
  colored projective rectangle/crosshair trails rendered by actual Slipstream.
- `bundle-size.json`: this newly generated runtime, not the old Pages snapshot.

Four stdlib-only tooling tests pass. Re-running bootstrap reuses completed
stages; a deliberately stale fingerprint is rejected before source setup. The
full desktop suite also still passes (7 tests, 33 assertions, no failures/errors).
The isolated server was checked against this cache and serves the correct font
license. Generated build logs stay under the cache; runtime/boots are not added
to the source branch. The separately committed `pages` branch remains unchanged.
