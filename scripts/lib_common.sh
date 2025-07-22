#!/usr/bin/env bash
set -euo pipefail

ensure_in_path() {
  # Add ~/.local/bin to PATH for this session
  export PATH="$HOME/.local/bin:$PATH"
  # Persist for future shells
  if ! grep -q 'HOME/.local/bin' "$HOME/.bashrc" 2>/dev/null; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
  fi
}

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
    none)    echo "No package manager found. Install: $*" >&2; exit 1 ;;
  esac
}
