#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

# --- config ---
PROJECT_ROOT="$(cd "$(dirname "$0")"/.. && pwd)"
PYPROJECT="$PROJECT_ROOT/pyproject.toml"
EXTRA_PKGS_FILE="$PROJECT_ROOT/config/extra-packages.txt"

# --- helpers ---
err() { echo "[ERROR] $*" >&2; exit 1; }
info(){ echo "[INFO] $*"; }

# ensure uv is on PATH
if ! command -v uv >/dev/null 2>&1; then
  err "uv not found. Install it first (curl -LsSf https://astral.sh/uv/install.sh | sh)."
fi

cd "$PROJECT_ROOT" || err "Cannot cd to $PROJECT_ROOT"

info "Project root: $PROJECT_ROOT"

# 1. Ensure pyproject.toml exists
if [ ! -f "$PYPROJECT" ]; then
  info "No pyproject.toml found. Creating a minimal one..."
  cat > "$PYPROJECT" <<'EOF'
[project]
name = "uv-app"
version = "0.0.1"
requires-python = ">=3.10"
dependencies = []
EOF
fi

# 2. Add core packages if pyproject doesn't already mention them
CORE_PKGS=(
  numpy scipy torch transformers datasets accelerate scikit-learn
  noisereduce label-studio-sdk pyinstaller rich requests
)
for pkg in "${CORE_PKGS[@]}"; do
  if ! grep -qiE "^[[:space:]]*\"?$pkg(==|>=|\"|$)" "$PYPROJECT"; then
    info "Adding core dep: $pkg"
    uv add "$pkg"
  fi
done

# 3. Extra packages file
if [ -f "$EXTRA_PKGS_FILE" ]; then
  info "Adding extras from $EXTRA_PKGS_FILE"
  while IFS= read -r pkg; do
    [[ -z "$pkg" || "$pkg" =~ ^[[:space:]]*# ]] && continue
    info "  -> uv add $pkg"
    uv add "$pkg"
  done < "$EXTRA_PKGS_FILE"
else
  info "No extra-packages file found."
fi

# 4. Sync env (creates/updates .venv)
info "Running uv sync..."
uv sync

info "[SUCCESS] uv sync complete."
