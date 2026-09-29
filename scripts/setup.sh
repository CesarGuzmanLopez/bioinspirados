#!/usr/bin/env bash
# Entorno Ubuntu sin root: venv local, sin sudo, sin --break-system-packages.
# Puertos >1024 (web en 8030).
set -euo pipefail

python3 -m venv .venv --upgrade-deps
. .venv/bin/activate
pip install -U pip
pip install -e .

echo "OK entorno listo. Para la web estatica:"
echo "  cd web && python3 -m http.server 8030  # http://localhost:8030"
