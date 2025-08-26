#!/usr/bin/env bash
set -euo pipefail
pytest "$(dirname "$0")" "$@"
