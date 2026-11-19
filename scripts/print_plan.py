#!/usr/bin/env python3
"""Print phase order & missing files, without executing Snowflake SQL."""
import argparse
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--manifest', type=Path, default=root/'deploy/deployment_manifest.json')
args = parser.parse_args()
manifest_path = args.manifest.resolve()
manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
base = manifest_path.parent if manifest_path.name == 'deployment_manifest.configured.json' else root
for phase in manifest['phases']:
    print(f"{phase['phase']}: {phase['title']}")
    for name in phase['files']:
        exists = (base/name).is_file()
        print(('  READY   ' if exists else '  MISSING ')+name)
print('Source DDL completeness is evaluated by: python scripts/release_gate.py')
