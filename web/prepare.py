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
replace("reactive_renderer.cpp", '#include "reactive_renderer.hpp"', '#include "reactive_renderer.hpp"\n#include <emscripten/html5.h>')
replace("reactive_renderer.cpp", '  glfwSwapInterval(0);', '  // Browser requestAnimationFrame owns timing.')
replace("reactive_renderer.cpp", '''  if(!gladLoadGLLoader(reinterpret_cast<GLADloadproc>(glfwGetProcAddress)))
    throw std::runtime_error("gladLoadGLLoader failed");''', '''  // GLES3 functions are linked directly by Emscripten.
  if(!emscripten_webgl_enable_extension(emscripten_webgl_get_current_context(), "EXT_color_buffer_float"))
    throw std::runtime_error("WebGL2 EXT_color_buffer_float required by compositor");''')
replace("reactive_renderer.cpp", '''      glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 3);
      glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);''', '''      glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 0);
      glfwWindowHint(GLFW_CLIENT_API, GLFW_OPENGL_ES_API);''')
