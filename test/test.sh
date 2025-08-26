#!/usr/bin/env bash
# Run all pytest-based tests in this repository.

set -e

# Change to repository root (one level above this script's directory).
cd "$(dirname "$0")/.."

# Execute pytest for all test files.
pytest test "$@"
