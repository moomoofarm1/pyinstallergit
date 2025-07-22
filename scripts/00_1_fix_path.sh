#!/usr/bin/env bash
set -euo pipefail

INSTALL_BIN="$HOME/.local/bin"
mkdir -p "$INSTALL_BIN"

# try to locate conda/uv
CANDIDATES=(
  "/root/miniconda3/bin/conda"
  "$HOME/miniconda3/bin/conda"
  "/root/.local/bin/uv"
  "$HOME/.local/bin/uv"
)

for f in "${CANDIDATES[@]}"; do
  [ -x "$f" ] || continue
  base="$(basename "$f")"
  cp "$f" "$INSTALL_BIN/$base" 2>/dev/null || true
done

export PATH="$INSTALL_BIN:$PATH"
hash -r

echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"

command -v conda >/dev/null && conda --version || echo "conda still not found"
command -v uv    >/dev/null && uv --version    || echo "uv still not found"
