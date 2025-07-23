#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# If you used lib_common.sh for PATH helpers, source it; otherwise remove this line
# source "$SCRIPT_DIR/lib_common.sh"

ENV_NAME="rbridge"
PYTHON_ENV="talkrpp_condaenv"

# --- ensure conda is available ---
if ! command -v conda >/dev/null 2>&1; then
  echo "conda not found. Run scripts/00_bootstrap.sh first." >&2
  exit 1
fi

# load conda functions into this shell
CONDA_BASE="$(conda info --base)"
# shellcheck source=/dev/null
source "$CONDA_BASE/etc/profile.d/conda.sh"

###############################################################################
# OPTION A: use only conda-forge (skip ToS entirely)
###############################################################################
conda config --set channel_priority strict
conda config --remove channels defaults || true
conda config --add channels conda-forge

# (If you prefer Option B, comment the three lines above and uncomment below)
# conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main --yes || true
# conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r    --yes || true

###############################################################################
# Create env if missing
###############################################################################
if conda env list | grep -q "^$ENV_NAME "; then
  echo "[INFO] Env '$ENV_NAME' already exists."
else
  conda create -y -n "$ENV_NAME" --override-channels -c conda-forge python=3.9 r-base r-reticulate
  echo "[INFO] Env '$ENV_NAME' created."
fi

###############################################################################
# Install R pkgs & create reticulate Python env from inside R
###############################################################################
# export the python env name so R can read it
export PYTHON_ENV

conda run -n "$ENV_NAME" Rscript - <<'EOF'
repos <- if (nzchar(Sys.getenv("CRAN"))) Sys.getenv("CRAN") else "https://cloud.r-project.org"
pkgs  <- c("reticulate", "devtools", "tidyverse", "talk")

install.packages(pkgs, repos = repos, Ncpus = max(1, parallel::detectCores() - 1))

pyenv <- Sys.getenv("PYTHON_ENV", "talkrpp_condaenv")

# Create a separate Python env for reticulate (inside the same Conda installation)
reticulate::conda_create(envname = pyenv, python_version = "3.9")
EOF

echo "[SUCCESS] R packages installed and conda env '$PYTHON_ENV' created."
echo "Use it with:"
echo "  conda activate $ENV_NAME"
