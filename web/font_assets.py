#!/usr/bin/env python3
"""Record the preloaded font and copy its license beside browser artifacts."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

output = Path(sys.argv[1])
font = Path(os.environ.get('WEB_FONT', '/usr/share/fonts/adwaita-mono-fonts/AdwaitaMono-Regular.ttf'))
license_path = os.environ.get('WEB_FONT_LICENSE')
if not license_path and 'WEB_FONT' not in os.environ:
    license_path = '/usr/share/licenses/adwaita-mono-fonts/LICENSE'
info = {'name':font.name, 'sha256':hashlib.sha256(font.read_bytes()).hexdigest(), 'licenseIncluded':False}
if license_path and Path(license_path).is_file():
    shutil.copyfile(license_path, output / 'font-LICENSE.txt')
    info['licenseIncluded'] = True
else:
    # Never leave an old license that could misidentify a replacement font.
    (output / 'font-LICENSE.txt').unlink(missing_ok=True)
    print('WARNING: set WEB_FONT_LICENSE and rebuild before publishing this font.', file=sys.stderr)
(output / 'font-info.json').write_text(json.dumps(info, indent=2) + '\n')
