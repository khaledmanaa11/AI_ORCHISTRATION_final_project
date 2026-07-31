#!/usr/bin/env bash
# SessionStart hook — report knowledge-graph presence and freshness.
#
# Wired in .claude/settings.json. Stdout is injected into every agent's context
# at session start, so this must stay short, cheap, and silent about detail.
# The graph itself is a manual navigation aid; this hook only makes sure no
# agent has to discover it exists. See CLAUDE.md "Knowledge graph (graphify)".
set -uo pipefail

REPORT=".planning/graphs/GRAPH_REPORT.md"
BUILD_CMD='graphify update . && cp graphify-out/{graph.json,graph.html,GRAPH_REPORT.md} .planning/graphs/'

if [ ! -f "$REPORT" ]; then
  echo "[graph] NONE — no knowledge graph in .planning/graphs/."
  echo "[graph] Build it: $BUILD_CMD"
  exit 0
fi

# Both facts come from the report header that graphify writes at build time.
summary=$(grep -m1 -E '^- [0-9]+ nodes' "$REPORT" | sed 's/^- //')
built=$(grep -m1 'Built from commit:' "$REPORT" | sed -E 's/.*`([0-9a-f]+)`.*/\1/')
head_sha=$(git rev-parse --short=8 HEAD 2>/dev/null || true)

if [ -z "$built" ] || [ -z "$head_sha" ]; then
  echo "[graph] PRESENT (freshness unknown) — $summary"
elif [ "$built" = "$head_sha" ]; then
  echo "[graph] FRESH at $head_sha — $summary"
else
  behind=$(git rev-list --count "$built..HEAD" 2>/dev/null || echo '?')
  echo "[graph] STALE — built at $built, HEAD is $head_sha ($behind commits behind)."
  echo "[graph] Refresh: $BUILD_CMD"
fi

echo "[graph] Query it, never read graph.json whole (~2 MB):"
echo "[graph]   graphify explain \"Name\"  |  graphify path \"A\" \"B\"  |  $REPORT"
