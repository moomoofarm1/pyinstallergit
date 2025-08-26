#!/usr/bin/env bash

# Run all pytest-based tests in this directory.
set -e
pytest "$(dirname "$0")"
