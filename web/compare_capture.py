#!/usr/bin/env python3
"""Compare the feedback region, not the deliberately different desktop/web HUD.

Run: uv run --with pillow web/compare_capture.py desktop.ppm browser-canvas.png
The browser screenshot can include one extra pixel from fractional CSS placement.
Only +/-1 pixel vertical registration is allowed; this is not byte parity.
"""
import argparse
import json
from pathlib import Path
from PIL import Image, ImageChops, ImageStat

parser = argparse.ArgumentParser()
parser.add_argument('desktop', type=Path)
parser.add_argument('browser', type=Path)
parser.add_argument('--output', type=Path, default=Path('.cache/wasm/capture-parity.json'))
args = parser.parse_args()
native = Image.open(args.desktop).convert('RGB').resize((960, 600), Image.Resampling.LANCZOS)
web = Image.open(args.browser).convert('RGB')
assert web.width == 960 and web.height in (600, 601), web.size
region = (0, 120, 960, 480)
results = []
for shift in (-1, 0, 1):
    difference = ImageChops.difference(native.crop(region), web.crop((0,120+shift,960,480+shift)))
    means = ImageStat.Stat(difference).mean
    results.append({'verticalShift': shift, 'meanAbsoluteRGB': means,
                    'normalizedMAE': sum(means) / (3*255)})
best = min(results, key=lambda x: x['normalizedMAE'])
report = {'region':region, 'resampling':'desktop LANCZOS to 960x600',
          'hudCompared':False, 'registrationLimitPixels':1, 'thresholdNormalizedMAE':0.02,
          'best':best, 'candidates':results, 'pass':best['normalizedMAE'] < 0.02}
args.output.write_text(json.dumps(report, indent=2) + '\n')
assert report['pass'], report
print(f"PASS: feedback-region normalized MAE {best['normalizedMAE']:.5f}, vertical offset {best['verticalShift']}")
