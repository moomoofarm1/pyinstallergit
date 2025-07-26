#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

PROJECT_ROOT="$(cd "$(dirname "$0")"/.. && pwd)"
PYPROJECT="$PROJECT_ROOT/pyproject.toml"
EXTRA_PKGS_FILE="$PROJECT_ROOT/config/extra-packages.txt"

# choose your uv-managed python
PY_VER="${UV_PY_VER:-3.11.9}"

err()  { echo "[ERROR] $*" >&2; exit 1; }
info() { echo "[INFO] $*"; }

cd "$PROJECT_ROOT" || err "Cannot cd to $PROJECT_ROOT"
info "Project root: $PROJECT_ROOT"

# 0. Make sure uv exists
command -v uv >/dev/null 2>&1 || err "uv not found. Install via: curl -LsSf https://astral.sh/uv/install.sh | sh"

# 1. Ensure we’re not using conda’s python
conda deactivate 2>/dev/null || true
export PATH="$(echo "$PATH" | tr ':' '\n' | grep -v 'miniconda' | paste -sd: -)"
hash -r

# 2. Make sure uv has the Python version we want
if ! uv python list | grep -q "$PY_VER"; then
  info "Installing uv-managed Python $PY_VER"
  uv python install "$PY_VER"
fi

# Pin it (creates .python-version/.uv-python)
uv python pin "$PY_VER"

# 3. Ensure pyproject.toml exists
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

# 4. Add core deps if missing
CORE_PKGS=(
  numpy scipy torch transformers datasets accelerate evaluate scikit-learn
  noisereduce label-studio-sdk pyinstaller rich requests
)
for pkg in "${CORE_PKGS[@]}"; do
  if ! grep -qiE "^[[:space:]]*\"?$pkg(==|>=|\"|$)" "$PYPROJECT"; then
    info "Adding core dep: $pkg"
    uv add "$pkg"
  fi
done

# 5. Extras from file
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

# 6. Remove old env if linked to wrong python
if [ -d .venv ]; then
  VENV_PY="$(readlink -f .venv/bin/python || true)"
  if [ -n "$VENV_PY" ] && [[ "$VENV_PY" == *miniconda* ]]; then
    info "Removing old .venv tied to conda python"
    rm -rf .venv
  fi
fi

# 7. Sync using pinned python
info "Running uv sync with Python $PY_VER..."
uv sync --python "$PY_VER"

info "[SUCCESS] uv sync complete."
