#!/usr/bin/env bash
set -euo pipefail

INSTALL_BIN="$HOME/.local/bin"
mkdir -p "$INSTALL_BIN"

CANDIDATES=(
  "/root/miniconda3/bin/conda"
  "$HOME/miniconda3/bin/conda"
  "/root/.local/bin/uv"
  "$HOME/.local/bin/uv"
)

for f in "${CANDIDATES[@]}"; do
  [ -x "$f" ] || continue
  cp -f "$f" "$INSTALL_BIN/$(basename "$f")"
done

export PATH="$INSTALL_BIN:$PATH"
hash -r

# Persist for future shells
LINE='export PATH="$HOME/.local/bin:$PATH"'
for rc in "$HOME/.bashrc" "$HOME/.profile" "$HOME/.zshrc"; do
  [ -f "$rc" ] || continue
  grep -qxF "$LINE" "$rc" || echo "$LINE" >> "$rc"
done

# If this script is *executed*, tell user to source or restart shell
if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  echo "[INFO] PATH updated for this subshell only."
  echo "Run:  source ~/.bashrc    or    exec \$SHELL -l"
fi

command -v conda >/dev/null && conda --version || echo "conda still not found"
command -v uv    >/dev/null && uv --version    || echo "uv still not found"
