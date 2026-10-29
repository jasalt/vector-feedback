#!/usr/bin/env bash
# Shared cache layout. Source this file; it never enters a sibling repository.
wasm_repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
build="$(python3 -c 'import pathlib,sys; print(pathlib.Path(sys.argv[1]).expanduser().resolve())' "${WASM_BUILD_ROOT:-$wasm_repo/.cache/wasm}")"
[[ "$build" != / && "$build" != "$wasm_repo" && "$build" != "$HOME" ]] || {
  echo 'WASM_BUILD_ROOT must name a disposable build-cache directory.' >&2; return 1;
}
export WASM_BUILD_ROOT="$build"
toolchain="$build/toolchain"
