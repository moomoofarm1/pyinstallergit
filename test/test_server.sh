#!/usr/bin/env bash
# Run only the server pytest file.
set -e
cd "$(dirname "$0")/.."
pytest test/test_server.py "$@"

