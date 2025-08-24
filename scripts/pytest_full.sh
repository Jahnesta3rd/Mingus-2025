#!/usr/bin/env bash
set -euo pipefail

# Full pytest run with reports, coverage, and xdist when available
cd "$(dirname "$0")/.."

mkdir -p reports

if [[ -x ./venv/bin/python ]]; then PY=./venv/bin/python; else PY=$(command -v python3 || command -v python); fi

EXTRA_OPTS=("--html=reports/pytest_report.html" "--self-contained-html" "--cov=backend" "--cov-report=term-missing")

# Use xdist if installed
if "$PY" -c "import pytest_xdist" >/dev/null 2>&1; then
  EXTRA_OPTS+=("-n" "auto")
fi

exec "$PY" -m pytest -q -o addopts="-ra --maxfail=1" "${EXTRA_OPTS[@]}" "$@"


