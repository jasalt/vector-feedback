#!/usr/bin/env python3
"""Exact local bundle bytes/hashes; gzip is a proxy, not network measurement."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
from build_paths import cache_root

parser = argparse.ArgumentParser()
parser.add_argument('--directory', type=Path,
    default=cache_root() / 'chez-live/em-tpb32l/bin/tpb32l')
parser.add_argument('--output', type=Path, default=cache_root() / 'bundle-size.json')
args = parser.parse_args()
files = {}
for name in ('scheme.html', 'scheme.js', 'scheme.wasm', 'scheme.data'):
    data = (args.directory / name).read_bytes()
    files[name] = {'bytes':len(data), 'gzip9Bytes':len(gzip.compress(data, compresslevel=9, mtime=0)),
                   'sha256':hashlib.sha256(data).hexdigest()}
report = {'files':files, 'totalBytes':sum(x['bytes'] for x in files.values()),
          'totalGzip9Bytes':sum(x['gzip9Bytes'] for x in files.values()),
          'notes':['Boot and preloaded font are already inside scheme.data.',
                   'Excludes source/licenses; gzip is per-file, not measured transfer.',
                   'Assertions, pthreads and C++ exception handling are enabled.']}
args.output.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
