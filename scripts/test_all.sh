#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/backend"
rm -f tests/test_traceit.db
PYTHONPATH=. python -m pytest -q tests
cd "$ROOT"
for f in frontend/site.js frontend/auth.js frontend/dashboard.js frontend/config.js; do node --check "$f"; done
python - <<'PY'
from pathlib import Path
for name, scripts in {
    'index.html':['config.js','site.js'],
    'auth.html':['config.js','auth.js'],
    'dashboard.html':['config.js','dashboard.js'],
}.items():
    s=Path('frontend/'+name).read_text()
    assert '<html' in s and '</html>' in s
    for src in scripts: assert f'src="{src}"' in s
print('HTML structure check: PASS')
PY
