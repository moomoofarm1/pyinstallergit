#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/lib_common.sh"

OS="$(uname -s)"
ARCH="$(uname -m)"
PM="$(detect_pkg_manager)"
echo "[INFO] OS=$OS ARCH=$ARCH PM=$PM"

# 1) Ensure base tools
NEEDED=(curl wget tar bzip2 xz-utils git binutils build-essential)
for t in "${NEEDED[@]}"; do
  command -v "${t%% *}" >/dev/null 2>&1 || NEED_INSTALL=1
done

if [ "${NEED_INSTALL:-0}" -eq 1 ]; then
  install_pkgs "$PM" "${NEEDED[@]}"
fi

ensure_in_path

# 2) micromamba (lightweight conda)
if ! command -v micromamba >/dev/null 2>&1; then
  echo "[INFO] Installing micromamba for $ARCH"
  case "$ARCH" in
    aarch64) MM_URL="https://micro.mamba.pm/api/micromamba/linux-aarch64/latest" ;;
    x86_64)  MM_URL="https://micro.mamba.pm/api/micromamba/linux-64/latest" ;;
    *) echo "Unsupported arch $ARCH. Install micromamba manually." >&2; exit 1 ;;
  esac
  curl -Ls "$MM_URL" | tar -xvj bin/micromamba
  mkdir -p "$HOME/.local/bin"
  mv bin/micromamba "$HOME/.local/bin/"
fi

# 3) uv (Python package manager)
if ! command -v uv >/dev/null 2>&1; then
  echo "[INFO] Installing uv"
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi

ensure_in_path
echo "[INFO] Bootstrap complete."
