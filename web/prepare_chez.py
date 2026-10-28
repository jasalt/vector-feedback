#!/usr/bin/env python3
"""Replace the sibling's Raylib witness glue in a private Chez build copy."""
from pathlib import Path
import sys

mode = sys.argv[2] if len(sys.argv) > 2 else 'abi'
source = Path(sys.argv[1]) / 'c/main.c'
text = source.read_text()
start = text.index('#ifdef __EMSCRIPTEN__')
end = text.index('/****\n  CUSTOM_INIT', start)
text = text[:start] + '''#ifdef __EMSCRIPTEN__
#include <emscripten/emscripten.h>
#include "slipstream_shim.h"
static int32_t web_u64_low(uint64_t count) { return (int32_t)count; }
static int32_t web_u64_high(uint64_t count) { return (int32_t)(count >> 32); }
static int32_t web_path_command(void* path, uint32_t command, const float* values, uint32_t count) {
  return ss_path_command(path, command, values, count);
}
static int32_t web_define_shape(void* canvas, const void* path, const SSKey* key,
                                float scale, uint32_t origin, float x, float y) {
  printf("DEFINE-SHAPE-OBSERVED scale=%g origin=%u x=%g y=%g\\n", scale, origin, x, y);
  return ss_canvas_define_shape(canvas, path, key, scale, origin, x, y);
}
static int32_t web_define_shape_p(void* canvas, const void* path, const SSKey* key, const float* values) {
  return ss_canvas_define_shape(canvas, path, key, values[0], 0, values[1], values[2]);
}
static int32_t web_shape_quad_p(const SSShape* shape, const SSTransform* transform, const float* scale, SSQuad* quad) {
  return ss_shape_quad(shape, transform, *scale, quad);
}
static int32_t web_read_float(const float* value) { return (int32_t)(1000 * *value); }
static void project_start_raylib(void) {
  EM_ASM({
    window.witnessReady = true;
    document.getElementById('status').textContent = 'READY: Slipstream ABI host returned';
  });
  emscripten_exit_with_live_runtime();
}
#endif

''' + text[end:]
start = text.index('static void project_init(void)')
end = text.index('#define CUSTOM_INIT project_init', start)
names = ['web_define_shape_p', 'web_shape_quad_p', 'web_define_shape', 'web_read_float', 'web_u64_low', 'web_u64_high', 'web_path_command', 'ss_atlas_new', 'ss_atlas_destroy', 'ss_atlas_build', 'ss_atlas_is_built',
         'ss_path_new', 'ss_path_destroy', 'ss_path_command', 'ss_canvas_new',
         'ss_canvas_destroy', 'ss_canvas_define_shape', 'ss_atlas_get_shape',
         'ss_shape_quad', 'ss_last_error']
text = text[:start] + 'static void project_init(void) {\n' + ''.join(
    f'  Sforeign_symbol("{name}", (void *){name});\n' for name in names) + '}\n' + text[end:]
if mode == 'live':
    start = text.index('static void project_start_raylib(void)')
    end = text.index('\n#endif', start)
    text = text[:start] + '''extern int web_scene_init(void);
extern int web_scene_input(float*);
extern int web_scene_submit(const float*);
extern void web_scene_render(void);
static void project_live_frame(void) {
  if(EM_ASM_INT({return !!window.webContextLost;})) return;
  Scall0(Stop_level_value(Sstring_to_symbol("picture-plane-frame")));
  web_scene_render();
}
static void project_start_raylib(void) {
  if(web_scene_init() != 0) abort();
  emscripten_set_main_loop(project_live_frame, 0, 1);
}
''' + text[end:]
    marker = 'static void project_init(void) {\n'
    text = text.replace(marker, marker + '''  Sforeign_symbol("web_scene_input", (void *)web_scene_input);
  Sforeign_symbol("web_scene_submit", (void *)web_scene_submit);
''')
source.write_text(text)
