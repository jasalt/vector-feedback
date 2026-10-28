// Actual Slipstream C ABI scene. No replacement vector renderer and no Jolt yet.
#include "slipstream_shim.h"
#include <GLES3/gl3.h>
#include <emscripten.h>
#include <cstdio>
#include <cstdlib>
#include <vector>
#include <iterator>
#include <algorithm>
#include <cmath>
#include "feedback_fixture.hpp"

namespace {
void* context;
std::vector<SSGLDrawCommand> commands;
int frames = 0;
#ifdef WEB_JOLT_HOST
bool deterministic = false;
#endif
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
  ++frames;
#ifdef WEB_JOLT_HOST
  if(deterministic && frames == 65) {
    EM_ASM({window.fixtureDone = true;});
    emscripten_pause_main_loop();
  }
#endif
  if(frames == 3) {
#ifdef WEB_JOLT_HOST
    EM_ASM({window.witnessReady = true;});
#else
    EM_ASM({document.getElementById('status').textContent = 'READY: Slipstream WebGL2 geometry + font'; window.witnessReady = true;});
#endif
  }
}
}
#ifdef WEB_JOLT_HOST
extern "C" int web_scene_init() {
#else
int main() {
#endif
  SSGLContextOptions options{};
  options.title = "Slipstream WebGL2";
  options.width = 960; options.height = 600;
  options.bounds[0] = -1.6f; options.bounds[1] = 1.6f;
  options.bounds[2] = -1; options.bounds[3] = 1;
  options.has_bounds = 1; options.visible = 1;
  context = owned(ss_gl_context_create(&options));
  std::printf("GL: %s\n", glGetString(GL_VERSION));
#ifdef WEB_JOLT_HOST
  bool feedback = true;
  deterministic = EM_ASM_INT({return new URLSearchParams(location.search).has('deterministic');});
  std::vector<float> expected;
  for(const auto& uniform : feedback_uniforms)
    expected.insert(expected.end(), uniform.values, uniform.values + uniform.components);
  EM_ASM({
    document.querySelector('h1').textContent = 'Picture Plane — Jolt + Slipstream WebGL2';
    window.expectedPayload = Array.from(HEAPF32.subarray($0 >> 2, ($0 >> 2) + $1));
  }, expected.data(), expected.size());
#else
  bool feedback = EM_ASM_INT({return new URLSearchParams(location.search).get('scene') === 'feedback';});
#endif
  auto* atlas = owned(ss_atlas_new(1024, 32));
  auto* canvas = owned(ss_canvas_new(atlas, 1000));
  auto* path = owned(ss_path_new());
  float rect[] = {-1.18f, -0.68f, 2.36f, 1.36f};
  check(ss_path_command(path, 14, rect, 4));
  SSLayer rectangle{};
  SSKey key{1, 0, "rectangle"};
  check(ss_canvas_stroke(canvas, path, &key, 0.012f, {0.2f, 0.95f, 0.65f, 1},
    1, 0, 0, 0, 0, 0, 4, 0, 0, &rectangle));
  SSLayer plane{};
  if(feedback) {
    check(ss_path_command(path, 0, nullptr, 0));
    float quad[] = {0, 0, 3.2f, 2.0f};
    check(ss_path_command(path, 14, quad, 4));
    SSKey plane_key{1, 0, "picture-plane"};
    check(ss_canvas_fill(canvas, path, &plane_key, {1, 1, 1, 1},
                        1, 0, 0, 0, 0, 0, &plane));
    plane.transform = {-1.6f, -1.0f, 0};
  }
  SSFontLoadResult font{};
  check(ss_font_load(atlas, "/font.ttf", nullptr, 0, 1, false, 0, &font));
  check(ss_atlas_build(atlas));
  if(feedback) {
    add(atlas, plane);
    commands.back().effect = owned(ss_gl_effect_program(context, "feedback-48", "fixture-65",
      feedback_declarations, "", feedback_hook, 0, feedback_uniforms, std::size(feedback_uniforms)));
    commands.back().effect_id = 1;
  } else {
    add(atlas, rectangle);
  }
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
#ifdef WEB_JOLT_HOST
  return 0;
#else
  emscripten_set_main_loop(frame, 0, true);
#endif
}

#ifdef WEB_JOLT_HOST
extern "C" int ss_web_update_effect(void*, void*, const float*, int32_t) noexcept;
extern "C" void web_scene_render() { frame(); }
extern "C" int web_scene_input(float* out) {
  if(!out) return 1;
  check(ss_gl_poll(context));
  SSGLInput input{};
  check(ss_gl_input_snapshot(context, &input));
  if(EM_ASM_INT({const clear = !!window.clearWebInput; window.clearWebInput = false; return clear;})) {
    const double x = input.x, y = input.y;
    input = {}; input.x = x; input.y = y;
    check(ss_gl_test_set_input(context, &input));
  }
  SSGLFrameState dimensions{};
  check(ss_gl_test_frame_state(context, &dimensions));
  int desired_width = EM_ASM_INT({return Math.round(Module.canvas.getBoundingClientRect().width * devicePixelRatio);});
  int desired_height = EM_ASM_INT({return Math.round(Module.canvas.getBoundingClientRect().height * devicePixelRatio);});
  if(desired_width > 0 && desired_height > 0 &&
     (desired_width != dimensions.window_size[0] || desired_height != dimensions.window_size[1])) {
    check(ss_gl_test_resize(context, desired_width, desired_height));
    check(ss_gl_test_frame_state(context, &dimensions));
  }
  const int width = dimensions.window_size[0], height = dimensions.window_size[1];
  out[0] = width > 0 ? -1.6f + 3.2f * input.x / width : 0;
  out[1] = height > 0 ? 1.0f - 2.0f * input.y / height : 0;
  out[2] = input.scroll_y;
  out[3] = input.left; out[4] = input.right; out[5] = input.middle;
  out[6] = input.space; out[7] = input.r;
  static double previous = emscripten_get_now();
  const double now = emscripten_get_now();
  out[8] = deterministic ? 1.0 / 60.0 : std::clamp((now - previous) / 1000.0, 0.0, 0.1);
  previous = now;
  return 0;
}
extern "C" int web_scene_submit(const float* values) {
  if(!values) return 1;
  if(deterministic && frames == 64)
    EM_ASM({window.actualPayload = Array.from(HEAPF32.subarray($0 >> 2, ($0 >> 2) + 434));}, values);
  int result = ss_web_update_effect(context, commands[0].effect, values, 434);
  if(result) return result;
  EM_ASM({
    const status = document.getElementById('status');
    status.textContent = `Jolt + Slipstream WebGL2 / ${$1 ? 'PAUSED' : 'LIVE'} / frame ${$0} / time ${$2.toFixed(2)} / zoom ${$3.toFixed(3)}`;
    window.modelState = ({frames:$0, paused:!!$1, time:$2, zoom:$3, panX:$4, panY:$5, yaw:$6, pitch:$7, roll:$8});
  }, frames, values[434], values[435], values[436], values[437], values[438], values[439], values[440], values[441]);
  return 0;
}
#endif
