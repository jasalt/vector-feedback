#!/usr/bin/env python3
"""Small stdlib-only tests for generated-source and cache-path tooling."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from build_paths import cache_root

WEB = Path(__file__).resolve().parent
PRISTINE = '''#include "config.h"
#ifndef CUSTOM_INIT
#define CUSTOM_INIT ((void (*)(void))0)
#endif
void f(void) {
  Sbuild_heap(execpath, CUSTOM_INIT);
#endif /* FunCRepl */

#ifdef SAVEDHEAPS
#endif
}
'''

class BuildToolsTest(unittest.TestCase):
    def test_default_cache_is_repository_local(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(cache_root(), WEB.parent / '.cache/wasm')

    def test_explicit_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {'WASM_BUILD_ROOT':directory}):
                self.assertEqual(cache_root(), Path(directory).resolve())

    def test_pristine_chez_injection_is_owned_and_fail_fast(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'c/main.c'
            source.parent.mkdir()
            source.write_text(PRISTINE)
            command = [sys.executable, str(WEB/'prepare_chez.py'), directory]
            subprocess.run(command, check=True)
            result = source.read_text()
            self.assertIn('#define CUSTOM_INIT picture_plane_init', result)
            self.assertIn('if(status == 0) picture_plane_start();', result)
            self.assertEqual(result.count('picture_plane_init();'), 1)
            self.assertEqual(source.with_name('picture_plane_host.inc').read_bytes(),
                             (WEB/'chez_host.c.inc').read_bytes())
            second = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(second.returncode, 0)
            self.assertIn('pristine marker', second.stderr)

    def test_toolchain_pins_are_locked_by_flake(self):
        pins = json.loads((WEB/'toolchain/pins.json').read_text())
        lock = json.loads((WEB.parent/'flake.lock').read_text())
        self.assertEqual(pins['jolt'], lock['nodes']['jolt']['locked']['rev'])
        self.assertEqual(pins['chez'], lock['nodes']['chezScheme']['locked']['rev'])
        self.assertNotIn('raylib', lock['nodes'])

if __name__ == '__main__':
    unittest.main()
