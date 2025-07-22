#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/lib_common.sh"

ENV_NAME="rbridge"
ensure_in_path

if ! command -v micromamba >/dev/null 2>&1; then
  echo "micromamba not found. Run scripts/00_bootstrap.sh first." >&2
  exit 1
fi

export MAMBA_ROOT_PREFIX="$HOME/micromamba"
mkdir -p "$MAMBA_ROOT_PREFIX"

eval "$(micromamba shell hook --shell bash -p "$MAMBA_ROOT_PREFIX")"

if micromamba env list | grep -q "^$ENV_NAME "; then
  echo "[INFO] Env '$ENV_NAME' already exists."
  exit 0
fi

micromamba create -y -n "$ENV_NAME" -c conda-forge python=3.11 r-base r-reticulate
echo "[INFO] Env '$ENV_NAME' created."
echo "To use it: micromamba activate $ENV_NAME"
