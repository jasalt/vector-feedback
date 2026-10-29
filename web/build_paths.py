"""Shared generated-build location for CLI tools (no sibling discovery)."""
import os
from pathlib import Path

def cache_root():
    default = Path(__file__).resolve().parent.parent / '.cache/wasm'
    return Path(os.environ.get('WASM_BUILD_ROOT', str(default))).expanduser().resolve()
