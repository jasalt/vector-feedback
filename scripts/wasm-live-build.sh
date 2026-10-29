#!/usr/bin/env bash
# Full opt-in browser build, including all owned prerequisites and shader emission.
set -euo pipefail
cd "$(dirname "$0")/.."
bash scripts/wasm-bootstrap.sh
bash scripts/wasm-build.sh
export WASM_MODE=live
exec bash scripts/wasm-abi-build.sh "$@"
