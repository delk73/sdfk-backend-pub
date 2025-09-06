#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUNDLE_DIR="$ROOT/typescript/tmp/bundled"
OUT="$ROOT/python/src/synesthetic_schemas"

# 1) Bundle all schemas (no network; uses our custom resolver)
node "$ROOT/codegen/ts_bundle.mjs"

# 2) Clean python package dir and make it importable
rm -rf "$OUT"
mkdir -p "$OUT"
: > "$OUT/__init__.py"
: > "$OUT/py.typed"

# 3) Decide if the CLI supports the pydantic v2 flag
EXTRA_FLAGS=()
# Use the direct python -m call here for consistency
if python -m datamodel_code_generator --help 2>&1 | grep -q -- '--use-pydantic-v2'; then
  EXTRA_FLAGS+=(--use-pydantic-v2)
fi

COMMON_ARGS=(
  --input-file-type jsonschema
  --target-python-version 3.11
  --use-standard-collections
  --disable-timestamp
)

# 4) Generate one .py per bundled schema (hyphens → underscores)
for schema in "$BUNDLE_DIR"/*.schema.json; do
  base="$(basename "$schema")"
  mod="${base%.schema.json}"
  mod="${mod//-/_}"
  out_py="$OUT/$mod.py"

  # THIS IS THE FIX:
  # We call the tool directly as a Python module. This forces the use of the
  # correct Nix Python interpreter from the current shell, bypassing the
  # broken executable script with the wrong shebang.
  python -m datamodel_code_generator "${COMMON_ARGS[@]}" "${EXTRA_FLAGS[@]}" --input "$schema" --output "$out_py"
  
  echo "generated: $(basename "$out_py")"
done

# Ensure py.typed exists for typed package distribution (keep deterministic)
: > "$OUT/py.typed"