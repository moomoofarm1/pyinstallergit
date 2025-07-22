#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/lib_common.sh"

# Create micromamba environment with reticulate
ENV_NAME="reticulate_env"

micromamba create -y -n "$ENV_NAME" -c conda-forge python=3.10 r-reticulate

cat <<EOM
[INFO] Created conda environment '$ENV_NAME'.
Activate with:
  micromamba activate $ENV_NAME
EOM
