#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
JOLT="${JOLT:-jolt}"
command -v "$JOLT" >/dev/null || { echo 'Set JOLT to your jolt executable (0.8.23+).' >&2; exit 1; }
# `path` resolves sources without loading the not-yet-built native library.
paths="$("$JOLT" path)"
IFS=: read -ra roots <<< "$paths"
slipstream=''
for root in "${roots[@]}"; do
  if [[ -f "$root/slipstream/ffi.clj" ]]; then
    slipstream="$(dirname "$root")"
    break
  fi
done
[[ -n "$slipstream" ]] || { echo 'Cannot locate resolved Slipstream dependency.' >&2; exit 1; }
if [[ -z "${SLUGHORN_HOME:-}" ]]; then
  SLUGHORN_HOME="$PWD/.cache/slughorn"
  if [[ ! -d "$SLUGHORN_HOME/.git" ]]; then
    git clone https://github.com/AlphaPixel/slughorn.git "$SLUGHORN_HOME"
  fi
  git -C "$SLUGHORN_HOME" checkout --detach 3ad0529d59a87bc29bb56ea91c02eae073ce6e97
  git -C "$SLUGHORN_HOME" submodule update --init ext/json
fi
cmake -S "$slipstream/native" -B "$PWD/.cache/native-build" \
  -DCMAKE_BUILD_TYPE=Release -DSLUGHORN_HOME="$SLUGHORN_HOME"
cmake --build "$PWD/.cache/native-build" --parallel "${JOBS:-4}"
mkdir -p native
case "$(uname -s)" in
  Darwin) lib=libslipstream.dylib ;;
  Linux) lib=libslipstream.so ;;
  *) echo 'Supported platforms: Linux and macOS.' >&2; exit 1 ;;
esac
cp "$slipstream/native/$lib" "native/$lib"
printf '\nReady. Run: %s -M:run\n' "$JOLT"
