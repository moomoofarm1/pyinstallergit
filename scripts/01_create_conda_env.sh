#!/usr/bin/env bash

# R-Python Bridge Environment Setup Script
# Creates a conda environment with R and sets up Python integration via reticulate

set -euo pipefail

# Configuration
readonly ENV_NAME="rbridge"
readonly PYTHON_ENV="talkrpp_condaenv"
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
    
    # Export environment variable for R script
    export PYTHON_ENV
    export CRAN_MIRROR
    
    # Create R script content
    local r_script
    read -r -d '' r_script <<'EOF' || true
# R package installation and Python environment setup

# Get configuration from environment
cran_mirror <- Sys.getenv("CRAN_MIRROR", "https://cloud.r-project.org")
python_env <- Sys.getenv("PYTHON_ENV", "talkrpp_condaenv")
python_version <- Sys.getenv("PYTHON_VERSION", "3.9")

cat("Using CRAN mirror:", cran_mirror, "\n")
cat("Python environment name:", python_env, "\n")
cat("R version:", R.version.string, "\n")

# Install required R packages
r_packages <- c("reticulate", "devtools", "tidyverse")
cat("Installing required R packages:", paste(r_packages, collapse = ", "), "\n")

# Use multiple cores for faster installation
ncores <- max(1, parallel::detectCores() - 1)
cat("Using", ncores, "cores for installation\n")

install.packages(
    r_packages, 
    repos = cran_mirror, 
    Ncpus = ncores,
    dependencies = TRUE
)

# Try to install optional packages (don't fail if unavailable)
optional_packages <- c("talk")
for (pkg in optional_packages) {
    cat("Attempting to install optional package:", pkg, "\n")
    tryCatch({
        install.packages(pkg, repos = cran_mirror, Ncpus = ncores)
        cat("Successfully installed:", pkg, "\n")
    }, error = function(e) {
        cat("Warning: Could not install optional package '", pkg, "': ", e$message, "\n", sep = "")
    })
}

# Load reticulate to create Python environment
library(reticulate)

# Check if Python environment already exists
existing_envs <- conda_list()
if (python_env %in% existing_envs$name) {
    cat("Python environment '", python_env, "' already exists\n", sep = "")
} else {
    cat("Creating Python environment '", python_env, "'\n", sep = "")
    conda_create(envname = python_env, python_version = python_version)
}

# Optional: Install common Python packages
python_packages <- c("numpy", "pandas")
if (length(python_packages) > 0) {
    cat("Installing Python packages:", paste(python_packages, collapse = ", "), "\n")
    tryCatch({
        conda_install(envname = python_env, packages = python_packages)
    }, error = function(e) {
        cat("Warning: Could not install Python packages:", e$message, "\n")
    })
}

cat("Setup completed successfully!\n")
EOF

    # Run R script in the conda environment
    if conda run -n "$ENV_NAME" Rscript -e "$r_script"; then
        log_success "R packages and Python environment setup completed"
    else
        log_error "Failed to install R packages or create Python environment"
        return 1
    fi
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
