#!/usr/bin/env bash
# 00_bootstrap.sh
# Idempotent bootstrap for: system deps, Miniconda (ARM/x86), uv.
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
  export PATH="$HOME/.local/bin:$PATH"
  hash -r 2>/dev/null || true
}

persist_path() {
  local line='export PATH="$HOME/.local/bin:$PATH"'
  for rc in "$HOME/.bashrc" "$HOME/.profile" "$HOME/.zshrc"; do
    [ -f "$rc" ] || continue
    grep -qxF "$line" "$rc" || echo "$line" >> "$rc"
  done
}

symlink_or_wrapper() {
  # $1 = target, $2 = link path (in INSTALL_BIN)
  local target="$1" link="$2"
  if [ -x "$target" ]; then
    ln -sf "$target" "$link" 2>/dev/null || {
      # fallback: small wrapper script
      cat >"$link" <<EOF
#!/usr/bin/env bash
exec "$target" "\$@"
EOF
      chmod +x "$link"
    }
  fi
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
BASE_PKGS=(curl wget tar bzip2 xz-utils git binutils)
case "$PM" in
  apk)    BASE_PKGS+=(build-base) ;;
  pacman) BASE_PKGS+=(base-devel) ;;
  *)      BASE_PKGS+=(build-essential) ;;
esac

NEED_INSTALL=0
for t in curl wget tar bzip2 xz git objdump; do
  command -v "$t" >/dev/null 2>&1 || NEED_INSTALL=1
done
[ "$NEED_INSTALL" -eq 1 ] && install_pkgs "$PM" "${BASE_PKGS[@]}"

ensure_path_now
persist_path

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

  # Put a stable shim in INSTALL_BIN
  symlink_or_wrapper "$HOME/miniconda3/bin/conda" "$INSTALL_BIN/conda"
fi

# 3) uv (Python package manager)
if ! command -v uv >/dev/null 2>&1; then
  echo "[INFO] Installing uv"
  curl -LsSf https://astral.sh/uv/install.sh | sh
  # installer drops 'uv' into ~/.local/bin
fi

ensure_path_now
persist_path

# 4) Sanity checks
echo "[INFO] Checking versions..."
if ! command -v conda >/dev/null 2>&1; then
  echo "[ERROR] conda still not on PATH. Try: export PATH=\"$HOME/.local/bin:\$PATH\"" >&2
  exit 1
fi
if ! command -v uv >/dev/null 2>&1; then
  echo "[ERROR] uv still not on PATH. Try: export PATH=\"$HOME/.local/bin:\$PATH\"" >&2
  exit 1
fi

conda --version
uv --version

echo "[INFO] Bootstrap complete."
