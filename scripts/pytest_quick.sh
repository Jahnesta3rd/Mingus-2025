#!/usr/bin/env bash
set -euo pipefail

# Lightweight, fast pytest run with minimal plugins and no parallelism/coverage/html
cd "$(dirname "$0")/.."

if [[ -x ./venv/bin/python ]]; then PY=./venv/bin/python; else PY=$(command -v python3 || command -v python); fi

exec "$PY" -m pytest -q -o addopts="-ra --maxfail=1" "$@"


