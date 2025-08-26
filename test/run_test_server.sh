#!/usr/bin/env bash
set -e
pytest "$(dirname "$0")/test_server.py"

