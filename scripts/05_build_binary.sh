#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/lib_common.sh"

ensure_in_path

PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# PyInstaller needs objdump -> binutils (handled in bootstrap)
uv run pyinstaller --name roberta_active --onefile src/__main__.py

echo "[INFO] Binary built at dist/roberta_active"
