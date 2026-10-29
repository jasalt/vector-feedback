#!/usr/bin/env bash
# Convenience entry point; prerequisites are built by the repo-owned bootstrap.
set -euo pipefail
export WASM_MODE=live
exec bash "$(dirname "$0")/wasm-abi-build.sh" "$@"
