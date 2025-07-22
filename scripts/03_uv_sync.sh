#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/lib_common.sh"

ensure_in_path

PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Add additional packages from config/extra-packages.txt (ignore comments/blank lines)
if [ -f config/extra-packages.txt ]; then
  grep -v '^\s*#' config/extra-packages.txt | grep -v '^\s*$' | while read -r pkg; do
    uv add "$pkg"
  done
fi

uv sync
