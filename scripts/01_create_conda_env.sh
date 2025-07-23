#!/usr/bin/env bash
set -euo pipefail

ENV_NAME="rbridge"
PYTHON_ENV="talkrpp_condaenv"

# 1) Ensure conda is available
if ! command -v conda >/dev/null 2>&1; then
  echo "conda not found. Run scripts/00_bootstrap.sh first." >&2
  exit 1
fi

CONDA_BASE="$(conda info --base)"
# shellcheck source=/dev/null
source "$CONDA_BASE/etc/profile.d/conda.sh"

# 2) Avoid Anaconda ToS by using only conda-forge
conda config --set channel_priority strict
conda config --remove channels defaults   || true
conda config --add    channels conda-forge || true

# 3) Create R env if missing
if conda env list | grep -qw "$ENV_NAME"; then
  echo "[INFO] Env '$ENV_NAME' already exists."
else
  conda create -y -n "$ENV_NAME" --override-channels -c conda-forge python=3.9 r-base r-reticulate
  echo "[INFO] Env '$ENV_NAME' created."
fi

# 4) Install R pkgs & create reticulate Python env
export PYTHON_ENV   # picked up inside R via Sys.getenv()
conda run -n "$ENV_NAME" Rscript - <<'EOF'
set -e
repos <- if (nzchar(Sys.getenv("CRAN"))) Sys.getenv("CRAN") else "https://cloud.r-project.org"
pkgs  <- c("reticulate", "devtools", "tidyverse", "talk")

install.packages(pkgs, repos = repos, Ncpus = max(1, parallel::detectCores() - 1))

pyenv <- Sys.getenv("PYTHON_ENV", "talkrpp_condaenv")
reticulate::conda_create(envname = pyenv, python_version = "3.9")

# Optional: preinstall Python libs you'll need
# reticulate::conda_install(envname = pyenv, packages = c("numpy", "pandas"))

message("R packages installed and python env '", pyenv, "' created.")
EOF

echo "[SUCCESS] Done."
echo "Use it with:"
echo "  conda activate $ENV_NAME"
echo "  R -q"
echo "  reticulate::use_condaenv('$PYTHON_ENV', required = TRUE)"
