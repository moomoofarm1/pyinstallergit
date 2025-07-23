# In progress
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/lib_common.sh"

ENV_NAME="rbridge"
ensure_in_path

if ! command -v conda >/dev/null 2>&1; then
  echo "conda not found. Run scripts/00_bootstrap.sh first." >&2
  exit 1
fi

source "$HOME/miniconda3/etc/profile.d/conda.sh"

if conda env list | grep -q "^$ENV_NAME "; then
  echo "[INFO] Env '$ENV_NAME' already exists."
  exit 0
fi

conda create -y -n "$ENV_NAME" -c conda-forge python=3.11 r-base r-reticulate
echo "[INFO] Env '$ENV_NAME' created."
echo "To use it: conda activate $ENV_NAME"
