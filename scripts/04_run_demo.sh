#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/lib_common.sh"

ensure_in_path

PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

DEMO_DIR="$SCRIPT_DIR/src"

if [ ! -d "$DEMO_DIR" ]; then
  echo "[WARN] Demo directory '$DEMO_DIR' not found." >&2
  exit 0
fi

shopt -s nullglob
DEMO_FILES=("$DEMO_DIR"/*.py)
shopt -u nullglob

if [ ${#DEMO_FILES[@]} -eq 0 ]; then
  echo "[WARN] No demo python files found in '$DEMO_DIR'." >&2
  exit 0
fi

for demo_file in "${DEMO_FILES[@]}"; do
  echo "[INFO] Running demo $(basename "$demo_file")"
  uv run python -m src.__main__ "$demo_file"
done
