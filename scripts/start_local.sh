#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
trap 'kill 0' EXIT
(cd "$ROOT/backend" && PYTHONPATH=. uvicorn app.main:app --host 0.0.0.0 --port 8000) &
(cd "$ROOT/frontend" && python -m http.server 5500 --bind 0.0.0.0) &
echo "TraceIT API: http://localhost:8000/docs"
echo "TraceIT UI : http://localhost:5500"
wait
