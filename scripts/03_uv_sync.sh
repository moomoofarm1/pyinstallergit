#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# If you have ensure_in_path in lib_common.sh, keep the source; otherwise remove.
source "$SCRIPT_DIR/lib_common.sh" 2>/dev/null || true
ensure_in_path 2>/dev/null || true

PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo "[INFO] Project root: $PROJECT_ROOT"

# 1. Ensure uv is available
if ! command -v uv >/dev/null 2>&1; then
  echo "[ERROR] uv not found. Install it first." >&2
  exit 1
fi

# 2. Ensure pyproject.toml exists
if [ ! -f pyproject.toml ]; then
  echo "[WARN] No pyproject.toml found. Creating a minimal one..."
  cat > pyproject.toml <<'EOF'
[project]
name = "pyinstaller-roberta-demo"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = []
EOF
fi

# 3. Add extra packages from config/extra-packages.txt
if [ -f config/extra-packages.txt ]; then
  echo "[INFO] Adding packages from config/extra-packages.txt"
  while IFS= read -r pkg; do
    [[ -z "$pkg" || "$pkg" =~ ^[[:space:]]*# ]] && continue
    echo "  -> uv add $pkg"
    uv add "$pkg"
  done < config/extra-packages.txt
else
  echo "[INFO] No config/extra-packages.txt found (skipping)."
fi

# 4. Sync
echo "[INFO] Running uv sync..."
uv sync

echo "[SUCCESS] uv sync complete."
