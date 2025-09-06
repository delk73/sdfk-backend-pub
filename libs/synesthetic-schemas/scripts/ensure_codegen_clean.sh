#!/usr/bin/env bash
set -euo pipefail

bash codegen/gen_py.sh
bash codegen/gen_ts.sh

IGNORE_PY='^\s*#\s*timestamp:'
IGNORE_TS='^\s*\*\s*Generated on:'

# detect any real diffs
if ! git diff --exit-code -I "$IGNORE_PY" -I "$IGNORE_TS" -- python/src typescript/src >/dev/null; then
  echo "❌ Generated code is stale (excluding timestamp-only changes)."
  git --no-pager diff -I "$IGNORE_PY" -I "$IGNORE_TS" -- python/src typescript/src
  exit 1
fi

# at this point, only timestamp lines differ; clean them out of the index
if ! git diff --quiet -- python/src typescript/src; then
  echo "ℹ️ Only timestamp lines changed — discarding them."
  git restore --source=HEAD --worktree -- python/src typescript/src
fi

echo "✅ Codegen is clean (ignoring timestamps)."
