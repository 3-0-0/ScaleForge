#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="${APP_ROOT:-/root/ScaleForge}"
cd "$APP_ROOT"
PY=${PY:-"./.venv/bin/python3"}
[ -x "$PY" ] || PY=python3

echo "[preflight] Python:"
$PY -c "import sys,platform; print(sys.version.split()[0], platform.platform())"

echo "[preflight] CLI version/help:"
PYTHONPATH=src $PY -m scaleforge.cli --version
PYTHONPATH=src $PY -m scaleforge.cli --help >/dev/null

echo "[preflight] Dry-run smoke:"
mkdir -p /tmp/sf-in /tmp/sf-out
printf x >/tmp/sf-in/dummy.jpg
PYTHONPATH=src $PY -m scaleforge.cli run --dry-run -o /tmp/sf-out /tmp/sf-in >/dev/null
echo "[preflight ok]"
