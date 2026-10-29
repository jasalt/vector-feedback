/* Project-owned glue included only by the private Emscripten Chez main.c.
 * Chez/Jolt and Slipstream GL calls execute on this browser frame owner.
 * No Scheme object is retained by C. */
#include <emscripten/emscripten.h>
#include <emscripten/html5.h>
#include "slipstream_shim.h"

static int32_t web_u64_low(uint64_t count) { return (int32_t)count; }
static int32_t web_u64_high(uint64_t count) { return (int32_t)(count >> 32); }
static int32_t web_path_command(void* path, uint32_t command, const float* values, uint32_t count) {
  return ss_path_command(path, command, values, count);
}
static int32_t web_define_shape(void* canvas, const void* path, const SSKey* key,
                                float scale, uint32_t origin, float x, float y) {
  printf("DEFINE-SHAPE-OBSERVED scale=%g origin=%u x=%g y=%g\n", scale, origin, x, y);
  return ss_canvas_define_shape(canvas, path, key, scale, origin, x, y);
}
static int32_t web_define_shape_p(void* canvas, const void* path, const SSKey* key, const float* values) {
  return ss_canvas_define_shape(canvas, path, key, values[0], 0, values[1], values[2]);
}
static int32_t web_shape_quad_p(const SSShape* shape, const SSTransform* transform, const float* scale, SSQuad* quad) {
  return ss_shape_quad(shape, transform, *scale, quad);
}
static int32_t web_read_float(const float* value) { return (int32_t)(1000 * *value); }

#ifdef WEB_JOLT_LIVE
extern int web_scene_init(void);
extern int web_scene_input(float*);
extern int web_scene_submit(const float*);
extern int web_scene_set_tail(int32_t, const char*, const char*, const float*);
extern void web_scene_render(void);
static void picture_plane_frame(void) {
  if(EM_ASM_INT({return !!window.webContextLost || !!window.webCapturePaused;})) return;
  if(emscripten_is_webgl_context_lost(emscripten_webgl_get_current_context())) return;
  double begin = emscripten_get_now();
  Scall0(Stop_level_value(Sstring_to_symbol("picture-plane-frame")));
  double submitted = emscripten_get_now();
  web_scene_render();
  double rendered = emscripten_get_now();
  EM_ASM({window.frameMetrics = ({modelAndFFIMs:$0, renderAndDriverMs:$1, wasmCapacityBytes:HEAPU8.length});},
         submitted-begin, rendered-submitted);
}
#endif

static void picture_plane_start(void) {
#ifdef WEB_JOLT_LIVE
  if(web_scene_init() != 0) abort();
  emscripten_set_main_loop(picture_plane_frame, 0, 1);
#else
  EM_ASM({
    window.witnessReady = true;
    document.getElementById('status').textContent = 'READY: Slipstream ABI host returned';
  });
  emscripten_exit_with_live_runtime();
#endif
}

static void picture_plane_init(void) {
#define REGISTER(name) Sforeign_symbol(#name, (void *)name)
  REGISTER(web_define_shape_p);
  REGISTER(web_shape_quad_p);
  REGISTER(web_define_shape);
  REGISTER(web_read_float);
  REGISTER(web_u64_low);
  REGISTER(web_u64_high);
  REGISTER(web_path_command);
  REGISTER(ss_atlas_new);
  REGISTER(ss_atlas_destroy);
  REGISTER(ss_atlas_build);
  REGISTER(ss_atlas_is_built);
  REGISTER(ss_path_new);
  REGISTER(ss_path_destroy);
  REGISTER(ss_path_command);
  REGISTER(ss_canvas_new);
  REGISTER(ss_canvas_destroy);
  REGISTER(ss_canvas_define_shape);
  REGISTER(ss_atlas_get_shape);
  REGISTER(ss_shape_quad);
  REGISTER(ss_last_error);
#ifdef WEB_JOLT_LIVE
  REGISTER(web_scene_input);
  REGISTER(web_scene_submit);
  REGISTER(web_scene_set_tail);
#endif
#undef REGISTER
}
