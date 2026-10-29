#!/usr/bin/env bash
# Build the ABI witness or live app using only this repo's owned toolchain.
set -euo pipefail
cd "$(dirname "$0")/.."
root="$PWD"
source scripts/wasm-common.sh
mode="${WASM_MODE:-abi}"
[[ "$mode" == abi || "$mode" == live ]] || { echo 'WASM_MODE must be abi or live' >&2; exit 1; }
bash scripts/wasm-bootstrap.sh
host="$toolchain/chez/ta6le"
jolt="$toolchain/jolt"
pack="$toolchain/pack"
ffi="$toolchain/libffi/install"
work="$build/chez-$mode"
main=witness
mode_flags=''
if [[ "$mode" == live ]]; then main=feedback.web; mode_flags=-DWEB_JOLT_LIVE; fi
for file in "$build/feedback_fixture.hpp" "$build/slipstream-web/native/reactive_renderer.cpp"; do
  [[ -f "$file" ]] || { echo "Missing $file; run scripts/wasm-build.sh first." >&2; exit 1; }
done
emcmake cmake -S web -B "$build/build-threaded" -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_CXX_FLAGS=-pthread -DSLIPSTREAM_SOURCE="$build/slipstream-web" \
  -DSLUGHORN_SOURCE="$build/sources/slughorn" \
  -DWEB_FONT="${WEB_FONT:-/usr/share/fonts/adwaita-mono-fonts/AdwaitaMono-Regular.ttf}"
cmake --build "$build/build-threaded" --target slipstream_web_scene --parallel "${JOBS:-4}"
if [[ -d "$work" ]]; then
  [[ -f "$work/picture-plane-toolchain" && "$(<"$work/picture-plane-toolchain")" == "$(<"$toolchain/complete")" ]] || {
    echo "Stale app tree: $work. Remove that generated directory or select a fresh WASM_BUILD_ROOT." >&2; exit 1;
  }
else
  cp -a --reflink=auto "$toolchain/chez" "$work"
  cp "$toolchain/complete" "$work/picture-plane-toolchain"
fi
# Regenerate from pristine pinned Chez, not from another app's modified main.c.
cp "$toolchain/chez/c/main.c" "$work/c/main.c"
python3 web/prepare_chez.py "$work"
(
  cd "web/$mode"
  export JOLT_NARROW_HASH=1 JOLT_CHEZ="$host/bin/ta6le/scheme"
  export JOLT_CHEZ_CSV="$host/boot/ta6le" JOLT_TARGET_CC=gcc
  nix shell "$root#i686-cc" -c "$jolt/bin/jolt" build -m "$main" \
    -o "$build/$mode-app" --target tpb32l --target-pack "$pack"
)
if [[ "$mode" == live ]]; then
  printf '\n(define (picture-plane-frame) (jolt-invoke0 (var-cell-deref (jolt-var "feedback.web" "frame!"))))\n' >> "$build/$mode-app.build/flat.ss"
  rm -f "$build/$mode-app.build/flat.so" "$build/$mode-app.build/jolt.boot"
  JOLT_NARROW_HASH=1 nix shell "$root#i686-cc" -c \
    "$host/bin/ta6le/scheme" --script "$build/$mode-app.build/compile.ss"
fi
(
  cd "$work"
  CFLAGS="-DDISABLE_CURSES -fexceptions $mode_flags" \
  CPPFLAGS="-I$build/slipstream-web/native -I$ffi/include" \
  LDFLAGS="$build/build-threaded/libslipstream_web_scene.a $build/build-threaded/libslipstream_web.a $build/build-threaded/_deps/msdfgen-build/libmsdfgen-core.a -sDEFAULT_TO_CXX=1 -fexceptions -sUSE_FREETYPE=1 -sUSE_GLFW=3 -sMIN_WEBGL_VERSION=2 -sMAX_WEBGL_VERSION=2 -sASSERTIONS=1 -L$ffi/lib -sPTHREAD_POOL_SIZE=1 --shell-file $root/web/shell.html --preload-file ${WEB_FONT:-/usr/share/fonts/adwaita-mono-fonts/AdwaitaMono-Regular.ttf}@/font.ttf" \
  ./configure --emscripten --threads --pbarch --enable-libffi \
    --emboot="$build/$mode-app.build/jolt.boot" --disable-x11 --disable-curses
  make -j"${JOBS:-4}"
)
python3 web/font_assets.py "$work/em-tpb32l/bin/tpb32l"
printf 'Built Slipstream/Jolt %s witness: %s/em-tpb32l/bin/tpb32l/scheme.html\n' "$mode" "$work"
