#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d -t syn-schema-XXXX)"
trap 'rm -rf "$TMP"' EXIT

# --- generate PY into temp ---
PY_OUT="$TMP/python/src/synesthetic_schemas"
mkdir -p "$PY_OUT"
python -m datamodel_code_generator \
  --input "$ROOT/jsonschema/synesthetic-asset.schema.json" \
  --input-file-type jsonschema \
  --output "$PY_OUT/asset.py" \
  --target-python-version 3.11 \
  --use-standard-collections
for S in shader tone haptic control modulation rule-bundle rule; do
  [ -f "$ROOT/jsonschema/$S.schema.json" ] || continue
  python -m datamodel_code_generator \
    --input "$ROOT/jsonschema/$S.schema.json" \
    --input-file-type jsonschema \
    --output "$PY_OUT/${S//-/_}.py" \
    --target-python-version 3.11 \
    --use-standard-collections
done
: > "$PY_OUT/__init__.py"

# --- generate TS into temp ---
TS_OUT="$TMP/typescript/src"
mkdir -p "$TS_OUT"
GEN="json-schema-to-typescript@15.0.0"
npx --yes "$GEN" "$ROOT/jsonschema/synesthetic-asset.schema.json" > "$TS_OUT/asset.d.ts"
for S in shader tone haptic control modulation rule-bundle rule; do
  [ -f "$ROOT/jsonschema/$S.schema.json" ] || continue
  npx --yes "$GEN" "$ROOT/jsonschema/$S.schema.json" > "$TS_OUT/${S//-/_}.d.ts"
done
cat > "$TS_OUT/index.d.ts" <<'TS'
export * from "./asset";
export * from "./shader";
export * from "./tone";
export * from "./haptic";
export * from "./control";
export * from "./modulation";
export * from "./rule_bundle";
export * from "./rule";
TS

# --- diff temp vs repo without touching repo ---
IGNORE_PY='^\s*#\s*timestamp:'
IGNORE_TS='^\s*\*\s*Generated on:'

PY_DIFF=0
TS_DIFF=0

git diff --no-index -I "$IGNORE_PY" -- "$PY_OUT" "$ROOT/python/src/synesthetic_schemas" >/dev/null || PY_DIFF=1
git diff --no-index -I "$IGNORE_TS" -- "$TS_OUT" "$ROOT/typescript/src" >/dev/null || TS_DIFF=1

if (( PY_DIFF || TS_DIFF )); then
  echo "❌ Codegen differs (ignoring timestamps)."
  echo "–– Python diff ––"
  git --no-pager diff --no-index -I "$IGNORE_PY" -- "$PY_OUT" "$ROOT/python/src/synesthetic_schemas" || true
  echo "–– TypeScript diff ––"
  git --no-pager diff --no-index -I "$IGNORE_TS" -- "$TS_OUT" "$ROOT/typescript/src" || true
  exit 1
fi

echo "✅ Codegen matches (ignoring timestamps)."
