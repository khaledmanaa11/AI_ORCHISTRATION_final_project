#!/usr/bin/env sh
# Enforce Segal §3 / §19.1 Table 5: every Python source/test file must be
# <= MAX code lines, EXCLUDING blank lines and comment lines. The limit is a
# fixed rule value (docs/SEGAL_GUIDELINES.md); split files, never compress.
#
# Usage:
#   scripts/check_line_limit.sh                # scan tracked src/ + tests/ *.py
#   scripts/check_line_limit.sh path/a.py ...  # scan explicit files (CI/tests)
#   MAX_LINES=150 scripts/check_line_limit.sh  # override limit (never below 150)
set -eu

MAX="${MAX_LINES:-150}"
status=0

if [ "$#" -gt 0 ]; then
  files="$*"
else
  files=$(git ls-files 'src/**/*.py' 'tests/**/*.py' 2>/dev/null || true)
  [ -z "$files" ] && files=$(git ls-files '*.py' 2>/dev/null || true)
fi

for f in $files; do
  [ -f "$f" ] || continue
  n=$(awk '
    {
      line = $0
      sub(/\r$/, "", line)          # tolerate CRLF (Windows)
      sub(/^[ \t]+/, "", line)      # strip leading whitespace
      if (line == "") next          # skip blank lines
      if (substr(line, 1, 1) == "#") next  # skip comment lines
      c++
    }
    END { print c + 0 }
  ' "$f")
  if [ "$n" -gt "$MAX" ]; then
    echo "VIOLATION: $f has $n code lines (limit $MAX)"
    status=1
  fi
done

if [ "$status" -ne 0 ]; then
  echo ""
  echo "Line-limit gate FAILED. Split the file(s) above; never compress code to fit."
  echo "Rule: Segal §3 / Table 5 — <= $MAX code lines (blanks/comments excluded)."
fi
exit "$status"
