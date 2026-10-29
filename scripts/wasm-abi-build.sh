#!/usr/bin/env bash
# Experimental integration with the sibling's already-proven, matched Chez pack.
set -euo pipefail
cd "$(dirname "$0")/.."
root="$PWD"
sibling="${WASM_REFERENCE:-$root/../jolt-wasm-raylib}"
base="$sibling/build/EXP-014-jolt-tpb32l-emscripten"
host="$sibling/build/EXP-018-chez-native/ta6le"
jolt="$sibling/build/EXP-017-jolt-upstream"
pack="$sibling/build/EXP-018-pack"
build="$root/.cache/wasm"
mode="${WASM_MODE:-abi}"
[[ "$mode" == abi || "$mode" == live ]] || { echo 'WASM_MODE must be abi or live' >&2; exit 1; }
work="$build/chez-$mode"
main=witness
[[ "$mode" != live ]] || main=feedback.web
for file in "$host/bin/ta6le/scheme" "$pack/xpatch" "$jolt/UPSTREAM_REVISION" \
  "$sibling/build/EXP-017-flappy/c/main.c" "$build/feedback_fixture.hpp"; do
  [[ -f "$file" ]] || { echo "Missing prerequisite: $file (see web/README.md)" >&2; exit 1; }
done
[[ "$(<"$jolt/UPSTREAM_REVISION")" == 5b46858a171f30949f5b09eb484bc6c5ff93c6ea ]]
emcmake cmake -S web -B "$build/build-threaded" -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_CXX_FLAGS=-pthread -DSLIPSTREAM_SOURCE="$build/slipstream-web" \
  -DSLUGHORN_SOURCE="$build/sources/slughorn" \
  -DWEB_FONT="${WEB_FONT:-/usr/share/fonts/adwaita-mono-fonts/AdwaitaMono-Regular.ttf}"
cmake --build "$build/build-threaded" --target slipstream_web_scene --parallel "${JOBS:-4}"
# Do not rebuild or patch the reference project itself.
if [[ ! -d "$work" ]]; then
  cp -a --reflink=auto "$sibling/build/EXP-017-flappy" "$work"
fi
# Always regenerate the integration file, making this script repeatable.
cp "$sibling/build/EXP-017-flappy/c/main.c" "$work/c/main.c"
python3 web/prepare_chez.py "$work" "$mode"
(
  cd "web/$mode"
  export JOLT_NARROW_HASH=1 JOLT_CHEZ="$host/bin/ta6le/scheme"
  export JOLT_CHEZ_CSV="$host/boot/ta6le" JOLT_TARGET_CC=gcc
  nix shell "$sibling#i686-cc" -c "$jolt/bin/jolt" build -m "$main" \
    -o "$build/$mode-app" --target tpb32l --target-pack "$pack"
)
if [[ "$mode" == live ]]; then
  printf '\n(define (picture-plane-frame) (jolt-invoke0 (var-cell-deref (jolt-var "feedback.web" "frame!"))))\n' >> "$build/$mode-app.build/flat.ss"
  rm -f "$build/$mode-app.build/flat.so" "$build/$mode-app.build/jolt.boot"
  JOLT_NARROW_HASH=1 nix shell "$sibling#i686-cc" -c \
    "$host/bin/ta6le/scheme" --script "$build/$mode-app.build/compile.ss"
fi
(
  cd "$work"
  CFLAGS="-DDISABLE_CURSES -fexceptions" \
  CPPFLAGS="-I$build/slipstream-web/native -I$base/libffi-em/install/include" \
  LDFLAGS="$build/build-threaded/libslipstream_web_scene.a $build/build-threaded/libslipstream_web.a $build/build-threaded/_deps/msdfgen-build/libmsdfgen-core.a -sDEFAULT_TO_CXX=1 -fexceptions -sUSE_FREETYPE=1 -sUSE_GLFW=3 -sMIN_WEBGL_VERSION=2 -sMAX_WEBGL_VERSION=2 -sASSERTIONS=1 -L$base/libffi-em/install/lib -sPTHREAD_POOL_SIZE=1 --shell-file $root/web/shell.html --preload-file ${WEB_FONT:-/usr/share/fonts/adwaita-mono-fonts/AdwaitaMono-Regular.ttf}@/font.ttf" \
  ./configure --emscripten --threads --pbarch --enable-libffi \
    --emboot="$build/$mode-app.build/jolt.boot" --disable-x11 --disable-curses
  make -j"${JOBS:-4}"
)
python3 web/font_assets.py "$work/em-tpb32l/bin/tpb32l"
printf 'Built Slipstream/Jolt %s witness: %s/em-tpb32l/bin/tpb32l/scheme.html\n' "$mode" "$work"
