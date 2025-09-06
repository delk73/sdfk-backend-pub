#!/usr/bin/env bash
set -euo pipefail

# Create GitHub issues from markdown files in meta/issues/*.md
# Requires: GitHub CLI (gh) authenticated for this repo.
# Usage:
#   ./scripts/create_issues.sh          # creates issues
#   DRY_RUN=1 ./scripts/create_issues.sh # print intended actions only

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ISSUE_DIR="$ROOT/meta/issues"

if ! command -v gh >/dev/null 2>&1; then
  echo "❌ GitHub CLI (gh) not found. Install from https://cli.github.com/" >&2
  exit 2
fi

# Check auth status (non-fatal; gh will still prompt on create if needed)
gh auth status -h github.com || true

shopt -s nullglob
mapfile -t FILES < <(ls -1 "$ISSUE_DIR"/*.md | sort)
if (( ${#FILES[@]} == 0 )); then
  echo "No issue files found in $ISSUE_DIR" >&2
  exit 0
fi

for f in "${FILES[@]}"; do
  title="$(sed -n '1s/^#\s\{0,1\}//p' "$f" | sed -n '1p')"
  if [[ -z "$title" ]]; then
    echo "⚠️  Skipping $f (missing H1 title line)" >&2
    continue
  fi

  bodyfile="$(mktemp)"
  trap 'rm -f "$bodyfile"' EXIT
  # Body is everything after the first line
  tail -n +2 "$f" > "$bodyfile"

  if [[ "${DRY_RUN:-}" == "1" ]]; then
    echo "[DRY] gh issue create --title \"$title\" --body-file $f"
    continue
  fi

  echo "Creating: $title"
  gh issue create --title "$title" --body-file "$bodyfile" || {
    echo "❌ Failed to create issue for $f" >&2
  }
done

echo "Done."

