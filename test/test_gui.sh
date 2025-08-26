#!/usr/bin/env bash
# Run only the GUI-related pytest file.
set -e
cd "$(dirname "$0")/.."
pytest test/test_gui.py "$@"

