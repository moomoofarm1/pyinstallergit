#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/lib_common.sh"

# Use uv to create Python virtual environment for pyinstaller project
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"

PY_VENV=".venv"
python3 -m venv "$PY_VENV"
source "$PY_VENV/bin/activate"

# Install Python packages listed in py_packages.txt using uv
if [ -f py_packages.txt ]; then
  uv pip install -r py_packages.txt
fi

# Ensure pyinstaller is installed
uv pip install pyinstaller

deactivate

cat <<EOM
[INFO] Python virtual environment created at $PY_VENV
Activate with:
  source $PY_VENV/bin/activate
EOM
