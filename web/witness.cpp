// Actual Slipstream C ABI scene. No replacement vector renderer and no Jolt yet.
#include "slipstream_shim.h"
#include <GLES3/gl3.h>
#include <emscripten.h>
#include <cstdio>
#include <cstdlib>
#include <vector>

namespace {
void* context;
std::vector<SSGLDrawCommand> commands;
int frames = 0;
void check(int result) {
  if(result != 0) { std::fprintf(stderr, "Slipstream: %s\n", ss_last_error()); std::abort(); }
}
void* owned(void* result) {
  if(!result) { std::fprintf(stderr, "Slipstream: %s\n", ss_last_error()); std::abort(); }
  return result;
}
void add(void* atlas, const SSLayer& layer) {
  SSGLDrawCommand command{};
  command.handle = owned(ss_gl_upload(context, atlas, &layer));
  // Layout stores translation in ems; draw commands use world coordinates.
  command.transform = {layer.transform.x * layer.scale,
                       layer.transform.y * layer.scale,
                       layer.transform.z * layer.scale};
  command.color = layer.color;
  command.scale = layer.scale;
  command.visible = 1;
  command.mask_type = 255;
  commands.push_back(command);
}
void frame() {
  check(ss_gl_poll(context));
  check(ss_gl_render(context, commands.data(), commands.size()));
  GLenum error = glGetError();
  if(error != GL_NO_ERROR) {
    std::fprintf(stderr, "GL error: 0x%x\n", error);
    std::abort();
  }
  check(ss_gl_swap(context));
  if(++frames == 3) {
    EM_ASM({document.getElementById('status').textContent = 'READY: Slipstream WebGL2 geometry + font'; window.witnessReady = true;});
  }
}
}
int main() {
  SSGLContextOptions options{};
  options.title = "Slipstream WebGL2";
  options.width = 960; options.height = 600;
  options.bounds[0] = -1.6f; options.bounds[1] = 1.6f;
  options.bounds[2] = -1; options.bounds[3] = 1;
  options.has_bounds = 1; options.visible = 1;
  context = owned(ss_gl_context_create(&options));
  std::printf("GL: %s\n", glGetString(GL_VERSION));
  auto* atlas = owned(ss_atlas_new(1024, 32));
  auto* canvas = owned(ss_canvas_new(atlas, 1000));
  auto* path = owned(ss_path_new());
  float rect[] = {-1.18f, -0.68f, 2.36f, 1.36f};
  check(ss_path_command(path, 14, rect, 4));
  SSLayer rectangle{};
  SSKey key{1, 0, "rectangle"};
  check(ss_canvas_stroke(canvas, path, &key, 0.012f, {0.2f, 0.95f, 0.65f, 1},
    1, 0, 0, 0, 0, 0, 4, 0, 0, &rectangle));
  SSFontLoadResult font{};
  check(ss_font_load(atlas, "/font.ttf", nullptr, 0, 1, false, 0, &font));
  check(ss_atlas_build(atlas));
  add(atlas, rectangle);
  const char* title = "SLIPSTREAM / WEBGL2";
  std::vector<uint32_t> text;
  for(const char* p = title; *p; ++p) text.push_back(*p);
  uint64_t count = 0;
  SSColor color{0.8f, 0.9f, 1, 1};
  check(ss_text_layout(atlas, text.data(), text.size(), 0.12f, -1.1f, 0.8f,
    &color, &font.metrics, 0, 0, 0, nullptr, 0, &count));
  std::vector<SSLayer> layers(count);
  check(ss_text_layout(atlas, text.data(), text.size(), 0.12f, -1.1f, 0.8f,
    &color, &font.metrics, 0, 0, 0, layers.data(), count, &count));
  for(const auto& layer : layers) add(atlas, layer);
  check(ss_path_destroy(path));
  check(ss_canvas_destroy(canvas));
  check(ss_atlas_destroy(atlas));
  emscripten_set_main_loop(frame, 0, true);
}
