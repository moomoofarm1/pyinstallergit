#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")"/.. && pwd)"
cd "$REPO_ROOT"

if [ -d .git ]; then
  echo "[INFO] Git repo already initialized."
else
  git init
  git add .
  git commit -m "Initial commit"
  echo "[INFO] Git repo initialized."
fi
