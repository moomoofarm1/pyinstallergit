#!/usr/bin/env bash
# Run only the LLM backend pytest file.
set -e
cd "$(dirname "$0")/.."
pytest test/test_llm_backend.py "$@"

