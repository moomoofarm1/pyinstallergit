#!/usr/bin/env bash
# ==============================================================================
# R–Python Bridge Environment Setup Script (Ubuntu/conda)
# ------------------------------------------------------------------------------
# - Creates a conda env with R (r-base) + reticulate
# - Installs needed R packages (reticulate, tidyverse, etc.)
# - Installs GitHub package "talk" (theharmonylab/talk) via remotes
# - Creates a separate Python env for reticulate: $PYTHON_ENV
# - Installs common Python pkgs (numpy, pandas) into that env
# - Streams R installation logs to your terminal
# ------------------------------------------------------------------------------
# Safe to re-run (idempotent).
# ==============================================================================

set -euo pipefail

# ----------------------------- Configuration ---------------------------------
readonly ENV_NAME="r-reticulate"           # conda env containing R + reticulate
readonly PYTHON_ENV="talkrpp_condaenv"     # reticulate-managed Python env name
readonly PYTHON_VERSION="3.9"              # Python version for PYTHON_ENV
readonly R_VERSION="4.4"                   # R version in ENV_NAME
readonly CRAN_MIRROR="${CRAN:-https://cloud.r-project.org}"

# R packages installed **via conda** (avoid compile hassles)
# Add more here if you want them preinstalled at the conda level.
readonly CONDA_R_PACKAGES=(
  r-reticulate r-remotes r-devtools r-tidyverse git
)

# Python packages to drop into PYTHON_ENV (optional)
readonly PY_PKGS=(numpy pandas)

# ------------------------------ Color output ---------------------------------
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m'

log_info()    { echo -e "${BLUE}[INFO]${NC} $*"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $*"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $*"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; }

# ------------------------------ Helpers --------------------------------------
check_conda() {
  if ! command -v conda >/dev/null 2>&1; then
    log_error "conda not found. Install conda or run your bootstrap script first."
    exit 1
  fi
  CONDA_BASE="$(conda info --base)"
  # shellcheck source=/dev/null
  source "$CONDA_BASE/etc/profile.d/conda.sh"
  log_info "Using conda from: $CONDA_BASE"
}

configure_conda_channels() {
  log_info "Configuring conda channels (use conda-forge only)…"
  conda config --set channel_priority strict
  conda config --remove channels defaults   || true
  conda config --add    channels conda-forge || true
}

setup_r_environment() {
  log_info "Setting up conda env: $ENV_NAME"
  if conda env list | grep -qw "$ENV_NAME"; then
    log_info "Env '$ENV_NAME' already exists."
  else
    conda create -y -n "$ENV_NAME" \
      --override-channels -c conda-forge \
      "python=$PYTHON_VERSION" "r-base=$R_VERSION" r-reticulate
    log_success "Env '$ENV_NAME' created."
  fi

  # Ensure extra R pkgs + git are available via conda (faster than compiling in R)
  log_info "Installing base R pkgs via conda: ${CONDA_R_PACKAGES[*]}"
  conda install -y -n "$ENV_NAME" -c conda-forge "${CONDA_R_PACKAGES[@]}"
}

install_r_packages_and_python_env() {
  log_info "Installing R packages (talk from GitHub) and configuring reticulate Python env…"

  export PYTHON_ENV PYTHON_VERSION CRAN_MIRROR

  local TMP_R
  TMP_R="$(mktemp -t rsetup.XXXXXX.R)"

  cat >"$TMP_R" <<'RSCRIPT'
options(warn=1)

cran_mirror    <- Sys.getenv("CRAN_MIRROR", "https://cloud.r-project.org")
python_env     <- Sys.getenv("PYTHON_ENV", "talkrpp_condaenv")
python_version <- Sys.getenv("PYTHON_VERSION", "3.9")

message("Using CRAN mirror: ", cran_mirror)
message("Python env name: ", python_env)
message("R version: ", R.version.string)

# remotes/devtools/reticulate/tidyverse installed by conda already, but verify
for (pkg in c("remotes", "reticulate")) {
  if (!requireNamespace(pkg, quietly = TRUE))
    stop(pkg, " not installed; please ensure conda installed it.")
}

# Install 'talk' from GitHub if missing
if (!requireNamespace("talk", quietly = TRUE)) {
  message("Installing 'talk' from GitHub (theharmonylab/talk)…")
  remotes::install_github("theharmonylab/talk", upgrade = "never")
}

library(talk)
# these are package-specific functions you mentioned
try(talkrpp_install(), silent = TRUE)
try(talkrpp_initialize(save_profile = TRUE), silent = TRUE)

# Now manage Python env via reticulate
library(reticulate)

envs <- tryCatch(conda_list(), error = function(e) data.frame())
if (!(python_env %in% envs$name)) {
  message("Creating Python env '", python_env, "' with Python ", python_version)
  conda_create(envname = python_env, python_version = python_version)
}

# Install Python packages into that env
py_pkgs <- c("numpy", "pandas")
if (length(py_pkgs)) {
  message("Installing Python packages into '", python_env, "': ", paste(py_pkgs, collapse=", "))
  tryCatch(
    conda_install(envname = python_env, packages = py_pkgs),
    error = function(e) message("Warning: could not install Python packages: ", e$message)
  )
}

message("Setup completed successfully!")
RSCRIPT

  # Stream output live (use stdbuf if available); conda >=4.14 supports --no-capture-output
  local STD_BUF=""
  if command -v stdbuf >/dev/null 2>&1; then
    STD_BUF="stdbuf -oL -eL"
  fi

  if conda run --help | grep -q -- "no-capture-output"; then
    CONDA_RUN_OPTS="--no-capture-output"
  else
    CONDA_RUN_OPTS=""
  fi

  if conda run $CONDA_RUN_OPTS -n "$ENV_NAME" $STD_BUF Rscript "$TMP_R"; then
    log_success "R packages and Python environment setup completed."
  else
    log_error "R script failed. Check logs above."
    rm -f "$TMP_R"
    return 1
  fi

  rm -f "$TMP_R"
}

show_usage_instructions() {
  log_success "All done!"
  cat <<EOF

To use the R–Python bridge:
  1. Activate the env:
     conda activate $ENV_NAME

  2. Start R and select the Python env:
     R -q
     reticulate::use_condaenv('$PYTHON_ENV', required = TRUE)
     py_config()                      # verify
     py_run_string('print("Hello from Python!")')

  3. If you need to add more Python pkgs later:
     reticulate::conda_install(envname = '$PYTHON_ENV', packages = c('scikit-learn'))

EOF
}

main() {
  log_info "Starting setup…"
  check_conda
  configure_conda_channels
  setup_r_environment
  install_r_packages_and_python_env
  show_usage_instructions
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  main "$@"
fi
