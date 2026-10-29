#!/usr/bin/env python3
"""Add owned host glue to pristine, pinned Chez main.c (never a sibling tree)."""
from pathlib import Path
import shutil
import sys

source = Path(sys.argv[1]) / 'c/main.c'
text = source.read_text()
def replace(old, new):
    global text
    if text.count(old) != 1:
        raise SystemExit(f'{source}: expected one pristine marker: {old!r}')
    text = text.replace(old, new)

replace('#include "config.h"', '''#include "config.h"
#ifdef __EMSCRIPTEN__
#include "picture_plane_host.inc"
#define CUSTOM_INIT picture_plane_init
#endif''')
replace('  Sbuild_heap(execpath, CUSTOM_INIT);', '''  Sbuild_heap(execpath, CUSTOM_INIT);
#ifdef __EMSCRIPTEN__
  /* Preloaded Emscripten boots can bypass CUSTOM_INIT in Sbuild_heap. */
  picture_plane_init();
#endif''')
replace('#endif /* FunCRepl */\n\n#ifdef SAVEDHEAPS', '''#endif /* FunCRepl */

#ifdef __EMSCRIPTEN__
  if(status == 0) picture_plane_start();
#endif

#ifdef SAVEDHEAPS''')
source.write_text(text)
shutil.copyfile(Path(__file__).with_name('chez_host.c.inc'), source.with_name('picture_plane_host.inc'))
