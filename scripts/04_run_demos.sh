#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/lib_common.sh"

ensure_in_path

PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Run the active learning demo using uncertainty sampling
uv run python -m src.__main__ active-learn \
  --iterations 2 \
  --query_k 3 \
  --output_dir "checkpoints/active_learning_demo"

