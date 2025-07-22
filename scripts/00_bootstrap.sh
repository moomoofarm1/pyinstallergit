#!/usr/bin/env bash
# 00_bootstrap.sh
# Installs required system tools, Miniconda (ARM/x86), and uv, then fixes PATH.
# Safe to re-run (idempotent).

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

add_to_shell_rc() {
  local line='export PATH="$HOME/.local/bin:$PATH"'
  for rc in "$HOME/.bashrc" "$HOME/.profile" "$HOME/.zshrc"; do
    [ -f "$rc" ] || continue
    grep -qxF "$line" "$rc" || echo "$line" >> "$rc"
  done
}

ensure_path_now() {
  export PATH="$HOME/.local/bin:$PATH"
  hash -r 2>/dev/null || true
}

#######################################
# Start
#######################################
OS="$(uname -s)"
ARCH="$(uname -m)"
PM="$(detect_pkg_manager)"
echo "[INFO] OS=$OS ARCH=$ARCH PM=$PM"

# Decide install dir for user binaries
INSTALL_BIN="${XDG_BIN_HOME:-$HOME/.local/bin}"
mkdir -p "$INSTALL_BIN"

# 1) Ensure base tools
# use compact names; map build tools per distro in one go
BASE_PKGS=(curl wget tar bzip2 xz-utils git binutils)
# compiler/toolchain packages
case "$PM" in
  apk)   BASE_PKGS+=(build-base) ;;
  pacman) BASE_PKGS+=(base-devel) ;;
  *)     BASE_PKGS+=(build-essential) ;;
esac

NEED_INSTALL=0
for t in curl wget tar bzip2 xz git objdump; do
  command -v "$t" >/dev/null 2>&1 || NEED_INSTALL=1
done
if [ "$NEED_INSTALL" -eq 1 ]; then
  install_pkgs "$PM" "${BASE_PKGS[@]}"
fi

ensure_path_now
add_to_shell_rc

# 2) Miniconda
if ! command -v conda >/dev/null 2>&1; then
  echo "[INFO] Installing Miniconda for $ARCH"
  case "$ARCH" in
    aarch64) MC_URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-aarch64.sh" ;;
    x86_64|amd64)  MC_URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh" ;;
    *) echo "[ERROR] Unsupported arch $ARCH. Install Miniconda manually." >&2; exit 1 ;;
  esac

  TMPDIR="$(mktemp -d)"
  trap 'rm -rf "$TMPDIR"' EXIT

  curl -Ls "$MC_URL" -o "$TMPDIR/miniconda.sh"
  bash "$TMPDIR/miniconda.sh" -b -p "$HOME/miniconda3"
  ln -s "$HOME/miniconda3/bin/conda" "$INSTALL_BIN/conda" 2>/dev/null || true
fi

# 3) uv (Python package manager)
if ! command -v uv >/dev/null 2>&1; then
  echo "[INFO] Installing uv"
  curl -LsSf https://astral.sh/uv/install.sh | sh
  # uv installer also drops binaries in ~/.local/bin
fi

ensure_path_now
add_to_shell_rc

# 4) Sanity checks
command -v conda >/dev/null 2>&1 || { echo "[ERROR] conda still not on PATH"; exit 1; }
command -v uv >/dev/null 2>&1 || { echo "[ERROR] uv still not on PATH"; exit 1; }

echo "[INFO] Bootstrap complete."
