#!/usr/bin/env bash
# ==============================================================================
# R–Python Bridge Environment Setup Script (Ubuntu + conda) - FIXED VERSION
# ------------------------------------------------------------------------------
# • Creates a conda env with R (r-base) + reticulate (ENV_NAME)
# • Installs core R pkgs via conda (no compile): reticulate, remotes/devtools, tidyverse
# • Installs GitHub pkg "talk" (theharmonylab/talk) with remotes
# • Creates a separate Python env for reticulate (PYTHON_ENV) and installs numpy/pandas
# • Streams R output (progress) to your terminal
# • Properly removes Anaconda/defaults channels (avoids ToS prompts)
# • Idempotent: safe to rerun
# ==============================================================================

set -euo pipefail

# ----------------------------- Configuration ---------------------------------
readonly ENV_NAME="r-reticulate"            # conda env containing R + reticulate
readonly PYTHON_ENV="talkrpp_condaenv"      # reticulate-managed Python env name
readonly PYTHON_VERSION="3.9"               # Python version for PYTHON_ENV
readonly R_VERSION="4.4"                    # R version in ENV_NAME
readonly CRAN_MIRROR="${CRAN:-https://cloud.r-project.org}"

# R pkgs to install via conda (fewer compile issues)
readonly CONDA_R_PACKAGES=( 
  r-reticulate r-remotes r-devtools r-tidyverse git
)

# Python pkgs to install in PYTHON_ENV
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
  log_info "Configuring conda channels (conda-forge only)…"

  # First, get current channels and remove problematic ones more aggressively
  local current_channels
  current_channels="$(conda config --show channels 2>/dev/null | grep -E '^\s*-\s*' | sed 's/^\s*-\s*//' || true)"
  
  # Remove all default/anaconda channels
  local DROP_CHANNELS=(
    "defaults"
    "https://repo.anaconda.com/pkgs/main"
    "https://repo.anaconda.com/pkgs/r"
    "https://repo.anaconda.com/pkgs/free"
    "https://repo.anaconda.com/pkgs/pro"
  )
  
  for ch in "${DROP_CHANNELS[@]}"; do
    if echo "$current_channels" | grep -qF "$ch"; then
      log_info "Removing channel: $ch"
      conda config --remove channels "$ch" 2>/dev/null || true
    fi
  done
  
  # Force remove any remaining anaconda.com channels
  conda config --remove-key channels 2>/dev/null || true
  
  # Set conda-forge as the only channel
  conda config --add channels conda-forge
  conda config --set channel_priority strict
  
  # Verify channels are clean
  log_info "Final channels configuration:"
  conda config --show channels || log_warning "Could not show channels config"
}

setup_r_environment() {
  log_info "Setting up conda env: $ENV_NAME"
  if conda env list | grep -qw "$ENV_NAME"; then
    log_info "Env '$ENV_NAME' already exists."
  else
    log_info "Creating new environment with R $R_VERSION and Python $PYTHON_VERSION..."
    conda create -y -n "$ENV_NAME" \
      --override-channels -c conda-forge \
      "python=$PYTHON_VERSION" "r-base=$R_VERSION"
    log_success "Env '$ENV_NAME' created."
  fi

  # Install base R packages via conda
  log_info "Installing base R pkgs via conda: ${CONDA_R_PACKAGES[*]}"
  conda install -y -n "$ENV_NAME" \
    --override-channels -c conda-forge \
    "${CONDA_R_PACKAGES[@]}"
  log_success "Base R packages installed via conda."
}

create_python_environment() {
  log_info "Creating dedicated Python environment: $PYTHON_ENV"
  
  # Check if the Python environment already exists
  if conda env list | grep -qw "$PYTHON_ENV"; then
    log_info "Python env '$PYTHON_ENV' already exists."
  else
    log_info "Creating Python environment '$PYTHON_ENV' with Python $PYTHON_VERSION..."
    conda create -y -n "$PYTHON_ENV" \
      --override-channels -c conda-forge \
      "python=$PYTHON_VERSION"
    log_success "Python env '$PYTHON_ENV' created."
  fi
  
  # Install Python packages
  if [ ${#PY_PKGS[@]} -gt 0 ]; then
    log_info "Installing Python packages: ${PY_PKGS[*]}"
    conda install -y -n "$PYTHON_ENV" \
      --override-channels -c conda-forge \
      "${PY_PKGS[@]}"
    log_success "Python packages installed."
  fi
}

install_r_packages() {
  log_info "Installing R packages (talk) & configuring reticulate…"

  export PYTHON_ENV PYTHON_VERSION CRAN_MIRROR

  local TMP_R
  TMP_R="$(mktemp -t rsetup.XXXXXX.R)"

  cat >"$TMP_R" <<'RSCRIPT'
options(warn=1)

cran_mirror    <- Sys.getenv("CRAN_MIRROR", "https://cloud.r-project.org")
python_env     <- Sys.getenv("PYTHON_ENV", "talkrpp_condaenv")
python_version <- Sys.getenv("PYTHON_VERSION", "3.9")

message("=== R Package Installation ===")
message("Using CRAN mirror: ", cran_mirror)
message("Target Python env: ", python_env)
message("R version: ", R.version.string)

# Ensure remotes + reticulate available (installed by conda)
required_pkgs <- c("remotes", "reticulate")
for (pkg in required_pkgs) {
  if (!requireNamespace(pkg, quietly = TRUE)) {
    stop("Package '", pkg, "' not installed. Please ensure conda installed it.")
  } else {
    message("✓ Found package: ", pkg)
  }
}

# Install 'talk' from GitHub if missing
if (!requireNamespace("talk", quietly = TRUE)) {
  message("Installing 'talk' from GitHub (theharmonylab/talk)…")
  tryCatch({
    remotes::install_github("theharmonylab/talk", upgrade = "never")
    message("✓ Successfully installed 'talk' package")
  }, error = function(e) {
    message("Warning: Failed to install 'talk' package: ", e$message)
  })
} else {
  message("✓ Package 'talk' already installed")
}

# Load and test reticulate
library(reticulate)
message("✓ Loaded reticulate package")

# Verify the Python environment exists
message("=== Python Environment Verification ===")
envs <- tryCatch({
  conda_list()
}, error = function(e) {
  message("Warning: Could not list conda environments: ", e$message)
  data.frame(name = character(0), python = character(0))
})

message("Available conda environments:")
if (nrow(envs) > 0) {
  for (i in 1:nrow(envs)) {
    message("  - ", envs$name[i], " (", envs$python[i], ")")
  }
} else {
  message("  (no environments found)")
}

if (python_env %in% envs$name) {
  message("✓ Found target Python environment: ", python_env)
  
  # Try to use the environment
  tryCatch({
    use_condaenv(python_env, required = TRUE)
    message("✓ Successfully configured reticulate to use: ", python_env)
    
    # Test Python connection
    py_config_info <- py_config()
    message("Python executable: ", py_config_info$python)
    message("Python version: ", py_config_info$version)
    
  }, error = function(e) {
    message("Warning: Could not configure Python environment: ", e$message)
  })
} else {
  message("✗ Python environment '", python_env, "' not found!")
  message("Available environments: ", paste(envs$name, collapse = ", "))
}

# Try to run package-specific helpers if 'talk' is available
if (requireNamespace("talk", quietly = TRUE)) {
  message("=== Running talk package setup ===")
  library(talk)
  
  tryCatch({
    talkrpp_install()
    message("✓ talkrpp_install() completed")
  }, error = function(e) {
    message("Note: talkrpp_install() failed: ", e$message)
  })
  
  tryCatch({
    talkrpp_initialize(save_profile = TRUE)
    message("✓ talkrpp_initialize() completed")
  }, error = function(e) {
    message("Note: talkrpp_initialize() failed: ", e$message)
  })
}

message("=== Setup Summary ===")
message("R environment setup completed!")
RSCRIPT

  # Stream output live with better error handling
  local STD_BUF=""
  command -v stdbuf >/dev/null 2>&1 && STD_BUF="stdbuf -oL -eL"

  local CONDA_RUN_OPTS="--no-capture-output"
  if ! conda run --help 2>/dev/null | grep -q -- "no-capture-output"; then
    CONDA_RUN_OPTS=""
    log_warning "Your conda version doesn't support --no-capture-output, output may be buffered"
  fi

  log_info "Running R setup script..."
  if conda run $CONDA_RUN_OPTS -n "$ENV_NAME" $STD_BUF Rscript "$TMP_R"; then
    log_success "R packages & configuration completed."
  else
    log_error "R script failed. Check logs above."
    log_info "Temp R script saved at: $TMP_R (for debugging)"
    return 1
  fi

  rm -f "$TMP_R"
}

verify_setup() {
  log_info "Verifying installation..."
  
  # Check environments exist
  log_info "Conda environments:"
  conda env list
  
  # Verify both environments exist
  if ! conda env list | grep -qw "$ENV_NAME"; then
    log_error "R environment '$ENV_NAME' not found!"
    return 1
  fi
  
  if ! conda env list | grep -qw "$PYTHON_ENV"; then
    log_error "Python environment '$PYTHON_ENV' not found!"
    return 1
  fi
  
  log_success "Both environments verified!"
  
  # Quick R test
  log_info "Testing R installation..."
  if conda run -n "$ENV_NAME" R --slave -e "cat('R version:', R.version.string, '\n')"; then
    log_success "R installation verified!"
  else
    log_warning "R test failed"
  fi
}

show_usage_instructions() {
  log_success "All done!"
  cat <<EOF

🎉 Setup completed successfully!

Available environments:
  • $ENV_NAME     - R environment with reticulate
  • $PYTHON_ENV   - Python environment for reticulate

To use the R–Python bridge:

  1. Activate the R environment:
     conda activate $ENV_NAME

  2. Start R and configure Python:
     R
     library(reticulate)
     use_condaenv('$PYTHON_ENV', required = TRUE)
     py_config()  # verify configuration

  3. Test Python integration:
     py_run_string('import numpy as np; print("NumPy version:", np.__version__)')

  4. Install additional Python packages:
     conda install -n $PYTHON_ENV -c conda-forge scikit-learn matplotlib

  5. Or from within R:
     conda_install(envname = '$PYTHON_ENV', packages = c('scikit-learn'))

Troubleshooting:
  • If reticulate can't find Python: restart R and run use_condaenv() again
  • Check environments: conda env list
  • Verify Python packages: conda list -n $PYTHON_ENV

EOF
}

main() {
  log_info "Starting R-Python bridge setup (FIXED VERSION)..."
  
  check_conda
  configure_conda_channels
  setup_r_environment
  create_python_environment
  install_r_packages
  verify_setup
  show_usage_instructions
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  main "$@"
fi
