#!/usr/bin/env bash
set -euo pipefail

# This script builds and validates the project artifacts.
# It MUST be run after 'poetry install' has created the .venv.

# 1. Ensure we are in the correct Nix environment.
# Corrected variable: IN_NIX_SHELL (all caps)
if [ -z "${IN_NIX_SHELL:-}" ]; then
  echo "Error: This script must be run inside the Nix shell." >&2
  echo "Please run 'nix develop' first." >&2
  exit 1
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

# 2. Validate that the Poetry venv exists and is active.
# This ensures 'poetry install' has been run.
if ! poetry env info --path &> /dev/null; then
    echo "Error: Poetry environment not found." >&2
    echo "Please run 'poetry install' to create the .venv and install dependencies first." >&2
    exit 1
fi

# 3. Run code generation.
echo "--> Generating code from schemas..."
# We use 'poetry run' to ensure we use the tools from the .venv.
poetry run bash "$ROOT/codegen/gen_py.sh"
bash "$ROOT/codegen/gen_ts.sh" # Node is provided directly by Nix.

# 4. Run validation and quality control.
echo "--> Validating generated artifacts..."
poetry run python "$ROOT/scripts/validate_examples.py"

echo "--> Running quality control checks..."
poetry run python "$ROOT/scripts/examples_qc.py" --ci || true

echo ""
echo "Build and validation complete."