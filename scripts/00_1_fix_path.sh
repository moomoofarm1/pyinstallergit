#!/usr/bin/env bash
set -euo pipefail

INSTALL_BIN="$HOME/.local/bin"
mkdir -p "$INSTALL_BIN"

# Conda candidates
CONDA_CANDIDATES=(
  "/root/miniconda3/bin/conda"
  "$HOME/miniconda3/bin/conda"
  "/opt/conda/bin/conda"
  "/usr/local/miniconda3/bin/conda"
)

# UV candidates  
UV_CANDIDATES=(
  "/root/.local/bin/uv"
  "$HOME/.local/bin/uv"
  "$HOME/.cargo/bin/uv"
  "/usr/local/bin/uv"
)

# Find and link conda
CONDA_FOUND=""
for f in "${CONDA_CANDIDATES[@]}"; do
  if [ -x "$f" ]; then
    CONDA_FOUND="$f"
    ln -sf "$f" "$INSTALL_BIN/conda"
    echo "[INFO] Found conda at: $f"
    break
  fi
done

# Find and link uv
UV_FOUND=""
for f in "${UV_CANDIDATES[@]}"; do
  if [ -x "$f" ]; then
    UV_FOUND="$f"
    ln -sf "$f" "$INSTALL_BIN/uv"
    echo "[INFO] Found uv at: $f"
    break
  fi
done

# Update PATH for current session
export PATH="$INSTALL_BIN:$HOME/miniconda3/bin:$PATH"
hash -r

# Persist for future shells
LINE='export PATH="$HOME/.local/bin:$HOME/miniconda3/bin:$PATH"'
for rc in "$HOME/.bashrc" "$HOME/.profile" "$HOME/.zshrc"; do
  if [ -f "$rc" ]; then
    if ! grep -qxF "$LINE" "$rc"; then
      echo "$LINE" >> "$rc"
      echo "[INFO] Added PATH to $rc"
    fi
  fi
done

# Initialize conda if available
if [ -n "$CONDA_FOUND" ] && [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
  source "$HOME/miniconda3/etc/profile.d/conda.sh"
fi

# If this script is *executed*, tell user to source or restart shell
if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  echo "[INFO] PATH updated for this session."
  echo "For new shells, run: source ~/.bashrc or exec \$SHELL -l"
fi

# Test commands
echo "[INFO] Testing commands..."
if command -v conda >/dev/null 2>&1; then
  conda --version
else
  echo "[WARNING] conda not found in PATH"
  [ -n "$CONDA_FOUND" ] && echo "  Found conda binary at: $CONDA_FOUND"
fi

if command -v uv >/dev/null 2>&1; then
  uv --version
else
  echo "[WARNING] uv not found in PATH"
  [ -n "$UV_FOUND" ] && echo "  Found uv binary at: $UV_FOUND"
fi

# Try to install to system locations if we have sudo access
if [ -n "$CONDA_FOUND" ] && command -v sudo >/dev/null 2>&1; then
  if sudo -n true 2>/dev/null; then
    echo "[INFO] Installing conda to /usr/local/bin"
    sudo install -m 755 "$CONDA_FOUND" /usr/local/bin/conda 2>/dev/null || true
  fi
fi

if [ -n "$UV_FOUND" ] && command -v sudo >/dev/null 2>&1; then
  if sudo -n true 2>/dev/null; then
    echo "[INFO] Installing uv to /usr/local/bin"
    sudo install -m 755 "$UV_FOUND" /usr/local/bin/uv 2>/dev/null || true
  fi
fi
