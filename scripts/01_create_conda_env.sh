#!/usr/bin/env bash

# R-Python Bridge Environment Setup Script
# Creates a conda environment with R and sets up Python integration via reticulate

set -euo pipefail

# Configuration
readonly ENV_NAME="r-reticulate" # for reticulate itself
readonly PYTHON_ENV="talkrpp_condaenv" # to run inside the R.
readonly PYTHON_VERSION="3.9"
readonly R_VERSION="4.3"  # Specify R version
readonly R_PACKAGES=("reticulate" "devtools" "tidyverse")  # Removed 'talk' as it may not be available
readonly R_PACKAGES_OPTIONAL=("talk")  # Optional packages that might not be available
readonly PYTHON_PACKAGES=("numpy" "pandas")  # Optional packages
readonly CRAN_MIRROR="${CRAN:-https://cloud.r-project.org}"

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

# Check if conda is available
check_conda() {
    if ! command -v conda >/dev/null 2>&1; then
        log_error "conda not found. Please install conda or run scripts/00_bootstrap.sh first."
        exit 1
    fi
    
    local conda_base
    conda_base="$(conda info --base)"
    # shellcheck source=/dev/null
    source "$conda_base/etc/profile.d/conda.sh"
    log_info "Using conda from: $conda_base"
}

# Configure conda channels to avoid Anaconda ToS
configure_conda_channels() {
    log_info "Configuring conda channels..."
    
    conda config --set channel_priority strict
    
    # Remove defaults channel if present (ignore errors)
    if conda config --show channels | grep -q "defaults"; then
        conda config --remove channels defaults || log_warning "Could not remove defaults channel"
    fi
    
    # Add conda-forge if not already present
    if ! conda config --show channels | grep -q "conda-forge"; then
        conda config --add channels conda-forge
    fi
    
    log_info "Conda channels configured to use only conda-forge"
}

# Create or verify R environment
setup_r_environment() {
    log_info "Setting up R environment: $ENV_NAME"
    
    if conda env list | grep -qw "$ENV_NAME"; then
        log_info "Environment '$ENV_NAME' already exists"
        return 0
    fi
    
    log_info "Creating new environment '$ENV_NAME'..."
    conda create -y -n "$ENV_NAME" \
        --override-channels -c conda-forge \
        "python=$PYTHON_VERSION" \
        "r-base=$R_VERSION" \
        r-reticulate
    
    log_success "Environment '$ENV_NAME' created successfully"
}

# Install R packages and create Python environment
install_r_packages_and_python_env() {
    log_info "Installing R packages and setting up Python environment..."

    export PYTHON_ENV CRAN_MIRROR PYTHON_VERSION

    # Create a temp R script
    TMP_R="$(mktemp -t rsetup.XXXXXX.R)"

    cat >"$TMP_R" <<'RSCRIPT'
options(warn=1)           # flush warnings immediately
flush.console <- function() {}  # on some platforms this is a no-op, but keep it.

cran_mirror   <- Sys.getenv("CRAN_MIRROR", "https://cloud.r-project.org")
python_env    <- Sys.getenv("PYTHON_ENV", "talkrpp_condaenv")
python_version<- Sys.getenv("PYTHON_VERSION", "3.9")

message("Using CRAN mirror: ", cran_mirror)
message("Python env name: ", python_env)
message("R version: ", R.version.string)

req_pkgs <- c("reticulate", "devtools", "tidyverse")
opt_pkgs <- c("talk")

ncores <- max(1, parallel::detectCores() - 1)
message("Installing required R packages: ", paste(req_pkgs, collapse=", "))
install.packages(req_pkgs, repos = cran_mirror, Ncpus = ncores, dependencies = TRUE)

for (pkg in opt_pkgs) {
  message("Attempting optional package: ", pkg)
  tryCatch(
    install.packages(pkg, repos = cran_mirror, Ncpus = ncores),
    error = function(e) message("Optional '", pkg, "' failed: ", e$message)
  )
}

library(reticulate)

envs <- conda_list()
if (python_env %in% envs$name) {
  message("Python env '", python_env, "' already exists.")
} else {
  message("Creating Python env '", python_env, "' with Python ", python_version)
  conda_create(envname = python_env, python_version = python_version)
}

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

    # Run it with no capture and line-buffering
    # stdbuf is in coreutils (apt-get install coreutils if missing; on mac use 'script -q /dev/null ...')
    if command -v stdbuf >/dev/null 2>&1; then
        STD_BUF="stdbuf -oL -eL"
    else
        STD_BUF=""
    fi

    if conda run --no-capture-output -n "$ENV_NAME" $STD_BUF Rscript "$TMP_R"; then
        log_success "R packages and Python environment setup completed"
    else
        log_error "Failed to install R packages or create Python environment"
        rm -f "$TMP_R"
        return 1
    fi

    rm -f "$TMP_R"
}


# Display usage instructions
show_usage_instructions() {
    log_success "Setup completed successfully!"
    echo
    echo "To use the R-Python bridge environment:"
    echo "  1. Activate the conda environment:"
    echo "     conda activate $ENV_NAME"
    echo
    echo "  2. Start R:"
    echo "     R -q"
    echo
    echo "  3. In R, configure the Python environment:"
    echo "     reticulate::use_condaenv('$PYTHON_ENV', required = TRUE)"
    echo
    echo "  4. Test the setup:"
    echo "     py_config()  # Should show Python configuration"
    echo "     py_run_string('print(\"Hello from Python!\")')"
}

# Main execution
main() {
    log_info "Starting R-Python bridge environment setup..."
    
    check_conda
    configure_conda_channels
    setup_r_environment
    install_r_packages_and_python_env
    show_usage_instructions
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
