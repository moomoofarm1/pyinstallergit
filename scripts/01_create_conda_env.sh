#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/lib_common.sh"

ENV_NAME="rbridge"
PYTHON_ENV="textrpp_condaenv"
ensure_in_path

if ! command -v conda >/dev/null 2>&1; then
  echo "conda not found. Run scripts/00_bootstrap.sh first." >&2
  exit 1
fi

source "$HOME/miniconda3/etc/profile.d/conda.sh"

if conda env list | grep -q "^$ENV_NAME "; then
  echo "[INFO] Env '$ENV_NAME' already exists."
else
  conda create -y -n "$ENV_NAME" -c conda-forge python=3.11 r-base
  echo "[INFO] Env '$ENV_NAME' created."
fi

# Install required R packages and create Python env via reticulate
conda run -n "$ENV_NAME" Rscript - <<EOF
repos <- if (nzchar(Sys.getenv("CRAN"))) Sys.getenv("CRAN") else "https://cloud.r-project.org"
install.packages(c("reticulate", "devtools", "tidyverse"), repos = repos)
reticulate::conda_create("$PYTHON_ENV")
install.packages("talk", repos = repos)
EOF

echo "[SUCCESS] R packages installed and conda env '$PYTHON_ENV' created."
echo "To use it: conda activate $ENV_NAME"
