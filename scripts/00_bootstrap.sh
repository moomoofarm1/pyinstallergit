#!/usr/bin/env bash
# 00_bootstrap.sh
# Idempotent bootstrap for: system deps, Miniconda (ARM/x86) for independent R installation, uv of python program manager before the pyinstaller .
# Ensures PATH works immediately (no need to reopen shell).

set -euo pipefail

#######################################
# Helpers
#######################################
detect_pkg_manager() {
  for pm in apt-get yum dnf apk zypper pacman; do
    command -v "$pm" >/dev/null 2>&1 && { echo "$pm"; return; }
  done
  echo "none"
}

install_pkgs() {
  local PM="$1"; shift
  case "$PM" in
    apt-get) sudo apt-get update && sudo apt-get install -y "$@" ;;
    yum)     sudo yum install -y "$@" ;;
    dnf)     sudo dnf install -y "$@" ;;
    apk)     sudo apk add --no-cache "$@" ;;
    zypper)  sudo zypper install -y "$@" ;;
    pacman)  sudo pacman -Sy --noconfirm "$@" ;;
    none)    echo "[ERROR] No supported package manager. Install: $*" >&2; exit 1 ;;
  esac
}

ensure_path_now() {
  export PATH="$HOME/.local/bin:$HOME/miniconda3/bin:$PATH"
  hash -r 2>/dev/null || true
}

persist_path() {
  local line='export PATH="$HOME/.local/bin:$HOME/miniconda3/bin:$PATH"'
  for rc in "$HOME/.bashrc" "$HOME/.profile" "$HOME/.zshrc"; do
    [ -f "$rc" ] || continue
    grep -qxF "$line" "$rc" || echo "$line" >> "$rc"
  done
}

#######################################
# Start
#######################################
OS="$(uname -s)"
ARCH="$(uname -m)"
PM="$(detect_pkg_manager)"
echo "[INFO] OS=$OS ARCH=$ARCH PM=$PM"

INSTALL_BIN="${XDG_BIN_HOME:-$HOME/.local/bin}"
mkdir -p "$INSTALL_BIN"

# 1) System deps
BASE_PKGS=(curl wget tar bzip2 git)
case "$PM" in
  apt-get) BASE_PKGS+=(xz-utils build-essential) ;;
  apk)     BASE_PKGS+=(xz build-base) ;;
  pacman)  BASE_PKGS+=(xz base-devel) ;;
  yum|dnf) BASE_PKGS+=(xz) ;;
  *)       BASE_PKGS+=(xz-utils build-essential) ;;
esac

NEED_INSTALL=0
for t in curl wget tar bzip2 xz git; do
  command -v "$t" >/dev/null 2>&1 || NEED_INSTALL=1
done
[ "$NEED_INSTALL" -eq 1 ] && install_pkgs "$PM" "${BASE_PKGS[@]}"

# 2) Miniconda (only if conda missing)
if ! command -v conda >/dev/null 2>&1; then
  echo "[INFO] Installing Miniconda for $ARCH"
  case "$ARCH" in
    aarch64)      MC_URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-aarch64.sh" ;;
    x86_64|amd64) MC_URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh" ;;
    *) echo "[ERROR] Unsupported arch $ARCH. Install Miniconda manually." >&2; exit 1 ;;
  esac

  TMPDIR="$(mktemp -d)"
  trap 'rm -rf "$TMPDIR"' EXIT

  curl -Ls "$MC_URL" -o "$TMPDIR/miniconda.sh"
  bash "$TMPDIR/miniconda.sh" -b -p "$HOME/miniconda3"
  
  # Initialize conda for bash
  "$HOME/miniconda3/bin/conda" init bash
  
  # Create symlink in .local/bin
  ln -sf "$HOME/miniconda3/bin/conda" "$INSTALL_BIN/conda"
fi

# 3) uv (Python package manager)
if ! command -v uv >/dev/null 2>&1; then
  echo "[INFO] Installing uv"
  curl -LsSf https://astral.sh/uv/install.sh | sh
  # Ensure uv is in the right place
  if [ -f "$HOME/.cargo/bin/uv" ]; then
    ln -sf "$HOME/.cargo/bin/uv" "$INSTALL_BIN/uv"
  fi
fi

# Update PATH and persist
ensure_path_now
persist_path

# Source conda environment if it exists
if [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
  source "$HOME/miniconda3/etc/profile.d/conda.sh"
fi

# 4) Sanity checks
echo "[INFO] Checking versions..."
if command -v conda >/dev/null 2>&1; then
  conda --version
else
  echo "[ERROR] conda still not on PATH" >&2
  exit 1
fi

if command -v uv >/dev/null 2>&1; then
  uv --version
else
  echo "[ERROR] uv still not on PATH" >&2
  exit 1
fi

echo "[SUCCESS] Bootstrap complete!"
# echo "Note: In new shells, run 'source ~/.bashrc' or restart your shell to use these tools."

echo "Copy and run command in the terminal: source ~/.bashrc"
