#!/usr/bin/env bash
set -euo pipefail

# This script runs pre-commit style checks.
# We use 'poetry run' before each 'make' command to ensure that the Makefile
# and all scripts it calls are executed within the project's Python virtual
# environment (.venv), giving them access to the installed dependencies.

echo "◼︎ normalize --check"
poetry run make normalize-check

echo "◼︎ schema-lint"
poetry run make schema-lint

echo "◼︎ ensure codegen clean"
if [[ -n "${SKIP_CODEGEN_CHECK:-}" ]]; then
  echo "(skipped by CI paths filter)"
else
  poetry run make codegen-check
fi

echo "◼︎ validate examples"
poetry run make validate

echo "✅ preflight OK"

# Record last successful preflight timestamp for quick visibility
mkdir -p .cache
date -u +"%Y-%m-%dT%H:%M:%SZ" > .cache/last_preflight.txt
echo "Stamped: $(cat .cache/last_preflight.txt) -> .cache/last_preflight.txt"