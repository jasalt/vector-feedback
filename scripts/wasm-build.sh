#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
for tool in emcmake emcc cmake python3 git "${JOLT:-jolt}"; do
  command -v "$tool" >/dev/null || { echo "Missing $tool: enter an Emscripten shell (see web/README.md)." >&2; exit 1; }
done
build="$PWD/.cache/wasm"
mkdir -p "$build/sources"
fetch() {
  local name="$1" url="$2" revision="$3"
  local dest="$build/sources/$name"
  if [[ ! -d "$dest/.git" ]]; then git clone "$url" "$dest"; fi
  git -C "$dest" checkout --detach "$revision"
  [[ "$(git -C "$dest" rev-parse HEAD)" == "$revision" ]]
}
fetch slipstream https://github.com/jlt-commons/slipstream.git d2f7f3d87a37ffcf25e66c27b88e91d4480ea308
fetch slughorn https://github.com/AlphaPixel/slughorn.git 3ad0529d59a87bc29bb56ea91c02eae073ce6e97
git -C "$build/sources/slughorn" submodule update --init ext/json
# Do not modify dependency caches or checkouts; always regenerate this copy.
rm -rf "$build/slipstream-web"
mkdir "$build/slipstream-web"
git -C "$build/sources/slipstream" archive HEAD | tar -x -C "$build/slipstream-web"
python3 web/prepare.py "$build/slipstream-web"
font="${WEB_FONT:-/usr/share/fonts/adwaita-mono-fonts/AdwaitaMono-Regular.ttf}"
[[ -f "$font" ]] || { echo 'Set WEB_FONT to a redistributable TTF font.' >&2; exit 1; }
# Emit from the shared application with native Jolt, outside the desktop project
# so deps.edn cannot try to load its native shared library in the build shell.
root="$PWD"
(cd "$build" && "${JOLT:-jolt}" -Scp "$root/src:$root/web" \
  -m feedback-fixture "$build/feedback_fixture.hpp")
emcmake cmake -S web -B "$build/build" -DCMAKE_BUILD_TYPE=Release \
  -DSLIPSTREAM_SOURCE="$build/slipstream-web" \
  -DSLUGHORN_SOURCE="$build/sources/slughorn" -DWEB_FONT="$font"
cmake --build "$build/build" --parallel "${JOBS:-4}"
printf 'Built C++ Slipstream witness (not Jolt): %s/witness.html\n' "$build/build"
