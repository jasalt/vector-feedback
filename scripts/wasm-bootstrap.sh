#!/usr/bin/env bash
# Build all runtime/cross-compiler prerequisites from locked upstream sources.
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/wasm-common.sh
[[ "$(uname -s):$(uname -m)" == Linux:x86_64 ]] || {
  echo 'The self-contained Wasm bootstrap currently supports Linux x86_64 only.' >&2; exit 1;
}
: "${CHEZ_SOURCE:?Run nix develop -c bash scripts/wasm-bootstrap.sh}"
: "${JOLT_SOURCE:?Run in this repository\'s nix develop shell}"
for tool in nix cc make patch curl sha256sum tar emconfigure emmake emcc python3; do
  command -v "$tool" >/dev/null || { echo "Missing bootstrap tool: $tool" >&2; exit 1; }
done
# Validate the declared pins against the locked flake environment. Include the
# patch and lock in the cache identity so incompatible packs are never reused.
fingerprint="$(python3 - <<'PY'
import hashlib,json,os
from pathlib import Path
pins=json.loads(Path('web/toolchain/pins.json').read_text())
assert pins['jolt']==os.environ.get('JOLT_UPSTREAM_REVISION'), 'Jolt flake/pins mismatch'
assert pins['chez']==os.environ.get('CHEZ_UPSTREAM_REVISION'), 'Chez flake/pins mismatch'
h=hashlib.sha256(b'picture-plane-bootstrap-schema-1\n')
for name in ['flake.lock','web/toolchain/pins.json','web/toolchain/patches/chez-emscripten-libffi.patch']:
 h.update(Path(name).read_bytes())
print(h.hexdigest())
PY
)"
mkdir -p "$toolchain/logs"
if [[ -f "$toolchain/fingerprint" ]]; then
  [[ "$(<"$toolchain/fingerprint")" == "$fingerprint" ]] || {
    echo "Toolchain inputs changed. Remove $toolchain and rerun bootstrap (do not mix packs)." >&2; exit 1;
  }
else
  printf '%s\n' "$fingerprint" > "$toolchain/fingerprint"
fi
host="$toolchain/chez"
jolt="$toolchain/jolt"
ffi="$toolchain/libffi"
pack="$toolchain/pack"
run_stage() {
  local stage="$1"; shift
  echo "== Wasm bootstrap: $stage =="
  "$@" 2>&1 | tee "$toolchain/logs/$stage.log"
}
if [[ ! -f "$toolchain/source-ready" ]]; then
  [[ ! -e "$host" && ! -e "$jolt" ]] || {
    echo "Incomplete source setup in $toolchain; remove it and rerun." >&2; exit 1;
  }
  cp -RL "$CHEZ_SOURCE" "$host"
  cp -RL "$JOLT_SOURCE" "$jolt"
  chmod -R u+w "$host" "$jolt"
  patch --batch --forward -d "$host" -p1 < web/toolchain/patches/chez-emscripten-libffi.patch
  printf '%s\n' "$JOLT_UPSTREAM_REVISION" > "$jolt/UPSTREAM_REVISION"
  touch "$toolchain/source-ready"
fi
if [[ ! -f "$toolchain/native-ready" ]]; then
  run_stage native-host bash -c '
    set -euo pipefail
    cd "$1"
    ./configure --threads --disable-x11 --disable-curses
    make -j"${JOBS:-4}"
    make bootquick XM=tpb32l
  ' _ "$host"
  touch "$toolchain/native-ready"
fi
if [[ ! -f "$toolchain/pack-ready" ]]; then
  # A real 32-bit Linux kernel is needed for Jolt build step 4's temporary
  # executable link. It is NOT the eventual Wasm kernel.
  run_stage target-pack nix shell "$wasm_repo#i686-cc" -c bash -c '
    set -euo pipefail
    cd "$1"
    ./configure --cross --force --threads --pbarch --32 --disable-x11 --disable-curses CC_FOR_BUILD=cc
    make -j"${JOBS:-4}"
    CHEZ_SRC="$1" bash "$2/tools/cross-compile/make-pack.sh" tpb32l "$3"
  ' _ "$host" "$jolt" "$pack"
  touch "$toolchain/pack-ready"
fi
if [[ ! -f "$toolchain/libffi-ready" ]]; then
  mkdir -p "$ffi"
  url="$(python3 -c 'import json; print(json.load(open("web/toolchain/pins.json"))["libffi"]["url"])')"
  digest="$(python3 -c 'import json; print(json.load(open("web/toolchain/pins.json"))["libffi"]["sha256"])')"
  [[ -f "$ffi/source.tar.gz" ]] || curl --fail --location --retry 3 "$url" -o "$ffi/source.tar.gz"
  printf '%s  %s\n' "$digest" "$ffi/source.tar.gz" | sha256sum -c -
  if [[ ! -d "$ffi/src" ]]; then
    mkdir "$ffi/src"
    tar -xf "$ffi/source.tar.gz" -C "$ffi/src" --strip-components=1
  fi
  mkdir -p "$ffi/src/build"
  run_stage libffi bash -c '
    set -euo pipefail
    cd "$1/src/build"
    flags="-pthread -Wcast-function-type"
    CFLAGS="$flags" CPPFLAGS="$flags" LDFLAGS="$flags" \
      emconfigure ../configure --host=wasm32-unknown-emscripten \
        --prefix="$1/install" --enable-static --disable-shared \
        --disable-docs --disable-multi-os-directory
    emmake make -j"${JOBS:-4}"
    make install
  ' _ "$ffi"
  touch "$toolchain/libffi-ready"
fi
for file in "$host/ta6le/bin/ta6le/scheme" "$pack/xpatch" "$pack/petite.boot" \
  "$pack/scheme.boot" "$pack/libkernel.a" "$ffi/install/lib/libffi.a" "$jolt/bin/jolt"; do
  [[ -f "$file" ]] || { echo "Missing bootstrap output: $file. Remove corresponding stage stamp and rerun." >&2; exit 1; }
done
printf '%s\n' "$fingerprint" > "$toolchain/complete"
printf 'Ready: self-contained toolchain at %s\n' "$toolchain"
