#!/usr/bin/env bash
# 00_bootstrap.sh
# Installs required system tools, micromamba (ARM/x86), and uv, then fixes PATH.
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

# 2) micromamba (lightweight conda)
if ! command -v micromamba >/dev/null 2>&1; then
  echo "[INFO] Installing micromamba for $ARCH"
  case "$ARCH" in
    aarch64) MM_URL="https://micro.mamba.pm/api/micromamba/linux-aarch64/latest" ;;
    x86_64|amd64)  MM_URL="https://micro.mamba.pm/api/micromamba/linux-64/latest" ;;
    *) echo "[ERROR] Unsupported arch $ARCH. Install micromamba manually." >&2; exit 1 ;;
  esac

  TMPDIR="$(mktemp -d)"
  trap 'rm -rf "$TMPDIR"' EXIT

  curl -Ls "$MM_URL" -o "$TMPDIR/mm.tar"
  tar -xf "$TMPDIR/mm.tar" -C "$TMPDIR"

  MM_PATH="$(find "$TMPDIR" -type f -name micromamba | head -n1)"
  if [ -z "$MM_PATH" ]; then
    echo "[ERROR] micromamba binary not found in archive." >&2
    exit 1
  fi

  install -m 755 "$MM_PATH" "$INSTALL_BIN/micromamba"
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
command -v micromamba >/dev/null 2>&1 || { echo "[ERROR] micromamba still not on PATH"; exit 1; }
command -v uv >/dev/null 2>&1 || { echo "[ERROR] uv still not on PATH"; exit 1; }

echo "[INFO] Bootstrap complete."


# Run scripts for the sys to detect the micromamba and uv

# 1. See where they actually got installed
ls -l ~/.local/bin /root/.local/bin 2>/dev/null
which -a micromamba uv 2>/dev/null || true
echo "$PATH"

# 2. If binaries are in /root/.local/bin, copy/symlink them to a global dir:
sudo install -m 755 /root/.local/bin/micromamba /usr/local/bin/micromamba 2>/dev/null || true
sudo install -m 755 /root/.local/bin/uv          /usr/local/bin/uv          2>/dev/null || true

# 3. Or, if they are in YOUR home:
export PATH="$HOME/.local/bin:$PATH"
hash -r  # refresh the command hash table

# 4. Persist it for future sessions:
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
# if you’re not using bash, add to ~/.profile or /etc/profile.d/localbin.sh
