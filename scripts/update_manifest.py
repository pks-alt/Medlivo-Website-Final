"""Refresh checksums only after intentionally approved source changes."""
import argparse
import hashlib
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--build-id', required=True, help='A unique identifier for this approved build')
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
path = root / 'BUILD.json'
manifest = json.loads(path.read_text(encoding='utf-8'))
files = [root / name for name in manifest['pages']]
files += [p for p in (root / 'assets').rglob('*') if p.is_file()]
missing = [str(p) for p in files if not p.is_file()]
if missing:
    raise SystemExit('Missing page files: ' + ', '.join(missing))
manifest['files'] = {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}
for name in manifest['pages']:
    manifest['pages'][name]['sha256'] = manifest['files'][name]
manifest['build_id'] = args.build_id
path.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
print('Checksums updated. Run the source and browser checks before committing.')
