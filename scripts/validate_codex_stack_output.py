#!/usr/bin/env python3
import re, sys, pathlib

text = pathlib.Path(sys.argv[1]).read_text() if len(sys.argv) > 1 else sys.stdin.read()

required_sections = [
    "=== PREVIEW REPORT BEGIN ===",
    "=== PREVIEW REPORT END ===",
]
aborted_preview = "=== ABORTED: PREVIEW ERRORS DETECTED ===" in text
aborted_links  = "=== ABORTED: LINK CHECK ERRORS DETECTED ===" in text

has_apply   = "=== APPLY DIFFS BEGIN ===" in text and "=== APPLY DIFFS END ===" in text
has_cleanup = "=== CLEANUP DIFFS BEGIN ===" in text and "=== CLEANUP DIFFS END ===" in text
has_linkchk = "=== LINK CHECK REPORT BEGIN ===" in text and "=== LINK CHECK REPORT END ===" in text

# 1) required preview markers
for m in required_sections:
    if m not in text:
        print(f"ERROR: missing section marker: {m}")
        sys.exit(2)

# 2) abort logic
if aborted_preview:
    print("FAIL: Aborted due to PREVIEW errors.")
    sys.exit(3)

# 3) after preview must have apply/cleanup/link sections (even if empty)
missing = []
if not has_apply:   missing.append("APPLY DIFFS")
if not has_cleanup: missing.append("CLEANUP DIFFS")
if not has_linkchk: missing.append("LINK CHECK REPORT")
if missing:
    print("ERROR: missing sections after PREVIEW:", ", ".join(missing))
    sys.exit(4)

if aborted_links:
    print("FAIL: Aborted due to LINK CHECK errors.")
    sys.exit(5)

# 4) sanity: ensure apply/cleanup blocks look like unified diffs (or are empty)
def block(name):
    return re.search(rf"=== {name} BEGIN ===\n(.*?)\n=== {name} END ===", text, re.S)

def looks_like_diff(s):
    s = s.strip()
    if not s:
        return True  # empty allowed
    # Allow standard unified diff lines
    ok = all(line.startswith(('--- ', '+++ ', '@@ ', 'diff --git ', 'index ', 'new file mode ', 'deleted file mode ')) 
             or not line.strip()  # blank
             for line in s.splitlines())
    return ok

for name in ["APPLY DIFFS", "CLEANUP DIFFS"]:
    m = block(name)
    if not m:
        print(f"ERROR: cannot extract block: {name}")
        sys.exit(6)
    if not looks_like_diff(m.group(1)):
        print(f"ERROR: {name} does not look like unified diffs.")
        sys.exit(7)

print("OK: stack output passes structural checks.")
