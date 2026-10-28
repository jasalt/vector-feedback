#!/usr/bin/env python3
"""Apply explicit web-only adaptations to a disposable pinned source copy."""
from pathlib import Path
import sys

native = Path(sys.argv[1]) / "native"

def replace(file, old, new, count=1):
    path = native / file
    text = path.read_text()
    actual = text.count(old)
    if actual != count:
        raise SystemExit(f"{path}: expected {count} occurrences, got {actual}: {old!r}")
    path.write_text(text.replace(old, new))

for file in ("reactive_renderer.hpp", "compositor.hpp"):
    replace(file, "#include <glad/glad.h>", "#include <GLES3/gl3.h>")
for file, count in (("advanced_shaders.cpp", 2), ("compositor.cpp", 3)):
    replace(file, "\n#version 330 core", "#version 300 es\nprecision highp float;\nprecision highp int;\nprecision highp sampler2D;\nprecision highp usampler2D;", count)
replace("reactive_renderer.cpp", '#include "reactive_renderer.hpp"', '#include "reactive_renderer.hpp"\n#include <emscripten/html5.h>\n#include <cmath>')
replace("reactive_renderer.cpp", '  glfwSwapInterval(0);', '  // Browser requestAnimationFrame owns timing.')
replace("reactive_renderer.cpp", '''  if(!gladLoadGLLoader(reinterpret_cast<GLADloadproc>(glfwGetProcAddress)))
    throw std::runtime_error("gladLoadGLLoader failed");''', '''  // GLES3 functions are linked directly by Emscripten.
  if(!emscripten_webgl_enable_extension(emscripten_webgl_get_current_context(), "EXT_color_buffer_float"))
    throw std::runtime_error("WebGL2 EXT_color_buffer_float required by compositor");''')
# Web-only mutable uniform payload: keep one effect/resource instead of caching
# a new immutable effect for every animation frame.
with (native / 'reactive_renderer.cpp').open('a') as out:
    out.write('''
extern "C" int ss_web_update_effect(void* owner, void* handle, const float* values, int32_t count) noexcept {
  ss_try(1,
    auto* effect = require_effect(require_context(owner), handle);
    if(!values || count != 434) throw std::invalid_argument("invalid web effect payload");
    for(int32_t i = 0; i < count; ++i)
      if(!std::isfinite(values[i])) throw std::invalid_argument("nonfinite web effect value");
    size_t components = 0;
    for(const auto& uniform : effect->uniforms) components += uniform.components;
    if(components != static_cast<size_t>(count))
      throw std::invalid_argument("web effect uniform count mismatch");
    size_t cursor = 0;
    for(auto& uniform : effect->uniforms) {
      std::copy(values + cursor, values + cursor + uniform.components, uniform.values.begin());
      cursor += uniform.components;
    }
    return 0;
  );
}
''')
replace("reactive_renderer.cpp", '''      glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 3);
      glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);''', '''      glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 0);
      glfwWindowHint(GLFW_CLIENT_API, GLFW_OPENGL_ES_API);''')
