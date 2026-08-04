---
phase: 03-blind-strategy-module-rl-policy
plan: "11"
subsystem: strategy
tags: [graph-theory, cycle-rank, articulation-points, voronoi, run-2]

# Dependency graph
requires:
  - phase: 03 (wave 1, plan 03-10 post-mortem)
    provides: "D-09 superseded finding (distance is the wrong objective), the cited
      E-V+1/d-1 identities and 7x7 oracle from docs/research/PURSUIT-AND-EVASION-STRATEGY.md"
provides:
  - "pursuit.strategy.graph: free_cells/neighbors/component_of/degree/edge_count/articulation_points"
  - "cycle_rank/is_forest/reduction_value -- the cop-win-iff-forest measurement"
  - "voronoi_split/territory_diff -- two-source BFS territory split"
affects: [03-16 (features), 03-17 (barrier rewrite), 03-18 (alpha-beta search)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Iterative Hopcroft-Tarjan articulation points (explicit index-stack frames, no recursion)"
    - "free_cells() as the sole (GameState, GameParams) entry point; every other function
      takes the derived frozenset so callers pay the derivation once per search node (D-26)"
    - "Two-source BFS advanced in lockstep (one layer per source per round) rather than
      two independently-timed searches, to make ties well-defined"

key-files:
  created:
    - src/pursuit/strategy/graph/__init__.py
    - src/pursuit/strategy/graph/components.py
    - src/pursuit/strategy/graph/cycles.py
    - src/pursuit/strategy/graph/territory.py
    - tests/unit/strategy/graph/__init__.py
    - tests/unit/strategy/graph/test_components.py
    - tests/unit/strategy/graph/test_cycles.py
    - tests/unit/strategy/graph/test_territory.py
  modified: []

key-decisions:
  - "None new -- this plan implements already-settled contracts (D-26, D-09 superseded,
    D-03, QUAL-02) with no ambiguity requiring a fresh decision"

patterns-established:
  - "Pattern: cycle_rank's connected-set precondition is documented, not runtime-guarded
    -- a component-count check would cost a full traversal per alpha-beta node (D-26)"

# Metrics
duration: ~20min
completed: 2026-08-04
---

# Phase 03 Plan 11: Graph Primitives Summary

**Pure-library `pursuit.strategy.graph` package (components/cycles/territory) measuring the run-2 objective directly: cop-win iff the thief's free component is a forest, via cycle rank = E-V+1, iterative Hopcroft-Tarjan articulation points, and a two-source Voronoi territory split.**

## Performance

- **Duration:** ~20 min
- **Started:** 2026-08-04T09:10:00Z
- **Completed:** 2026-08-04T09:32:00Z
- **Tasks:** 3 (all `type="auto"`, autonomous)
- **Files modified:** 8 (all new)

## Accomplishments

- `components.py`: `free_cells`/`neighbors`/`component_of`/`degree`/`edge_count`/
  `articulation_points` — the package's one adjacency implementation, pinned equal to
  `board.get_legal_moves` minus `STAY` by an exhaustive per-cell equivalence test
  (QUAL-02). `articulation_points` is iterative Hopcroft-Tarjan with an explicit
  `(node, sorted_neighbors, next_index)` stack — no recursion anywhere in the package.
- `cycles.py`: `cycle_rank` (`E - V + 1`), `is_forest` (`cycle_rank == 0`), and
  `reduction_value` (`degree - 1`, the 03-17 greedy barrier score). Pinned against the
  cited 7x7 oracle: `V=49, E=84, cycle_rank=36`.
- `territory.py`: `voronoi_split` (two sources advanced one BFS layer per round in the
  same loop; ties and unreachable cells belong to neither side) and `territory_diff`
  (reuses `components.edge_count`, no second edge counter).
- `__init__.py` re-exports the full public surface so 03-16/03-17/03-18 import from
  `pursuit.strategy.graph`, never a submodule.
- Zero role knowledge in code (grep for `cop|thief` under the package hits docstrings
  only — every function is pure, takes no role, and branches on nothing but the cell
  set and coordinates it is given, D-03).

## Task Commits

Each task was committed atomically, TDD (tests written and confirmed red before the
implementation went green):

1. **Task 1: components.py — free-cell graph, degree, iterative articulation points** -
   `12be2e4` (feat)
2. **Task 2: cycles.py — cycle rank, reduction value, is_forest** - `52c85f2` (feat)
3. **Task 3: territory.py — two-source Voronoi split and its differences** - `b4b06fa`
   (feat)

Plus one post-task deviation-fix commit (see below): `af5f0de` (test).

## Files Created/Modified

- `src/pursuit/strategy/graph/components.py` (100 code lines) — free-cell graph,
  adjacency, components, degree, edge count, articulation points
- `src/pursuit/strategy/graph/cycles.py` (37 code lines) — cycle rank, is_forest,
  reduction value
- `src/pursuit/strategy/graph/territory.py` (55 code lines) — Voronoi split, territory
  diff
- `src/pursuit/strategy/graph/__init__.py` (32 code lines) — public re-exports
- `tests/unit/strategy/graph/{test_components,test_cycles,test_territory}.py` — 19
  tests total, 100% coverage of the new package

## Decisions Made

None new. Every contract in this plan (adjacency-equivalence proof, the never-raise
convention for out-of-set cells, the connected-only precondition on `cycle_rank`, the
neither-side tie rule in `voronoi_split`) was already fully specified by the plan text
and the cited research doc; no ambiguity required an autonomous call. The one
implementation choice worth naming for future readers: `voronoi_split` advances both
source frontiers one BFS layer per round inside a single loop (rather than running two
independently-timed BFS passes and comparing distances afterward) so that "reached on
the same round" is the literal, obvious definition of a tie.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - missing coverage] Two documented contract branches had no direct test**

- **Found during:** final verification pass, after all three tasks were committed
- **Issue:** `pytest --cov` showed `components.py` at 99% and `cycles.py` at 90%.
  The misses were (a) `articulation_points`'s root-specific `root_child_count >= 2`
  branch — the DFS-root-is-itself-a-cut-vertex case, a genuinely distinct code path
  from the non-root case the barrier-corridor test already covered — and (b)
  `cycle_rank(frozenset())`'s documented "empty input is 0" contract, never exercised
  directly.
- **Fix:** Added `test_dfs_root_itself_is_reported_as_a_cut_vertex_when_it_has_two_children`
  (a root with two direct leaf neighbours: `{(0,0),(0,1),(1,0)}`, where `(0,0)` sorts
  first and gets exactly two DFS children) and
  `test_empty_cell_set_has_cycle_rank_zero_and_is_a_forest`.
- **Files modified:** `tests/unit/strategy/graph/test_components.py`,
  `tests/unit/strategy/graph/test_cycles.py`
- **Verification:** `uv run pytest tests/unit/strategy/graph/ --cov=pursuit.strategy.graph
  --cov-report=term-missing` → 100% on all four package files, 19 passed
- **Committed in:** `af5f0de`

---

**Total deviations:** 1 auto-fixed (missing coverage on two documented-but-untested
branches)
**Impact on plan:** No scope creep — both additions are tests only, proving contracts
the plan itself specified in prose (never-raise / empty-input-is-0) but that the
plan's own listed test cases didn't happen to trigger.

## Issues Encountered

None. All three tasks went red -> green on the first implementation attempt; no bugs,
no blocking issues, no architectural questions.

## User Setup Required

None — pure library, no external service configuration, no config keys added (the
plan is explicit: "No tunable knob exists in this package").

## Verification Evidence

- `uv run pytest tests/unit/strategy/graph/ -q` → 19 passed (17 from the plan's own
  test cases + 2 coverage-gap fixes)
- `uv run pytest tests/unit/strategy/graph/ --cov=pursuit.strategy.graph
  --cov-report=term-missing` → 100% (109/109 statements)
- Full repo suite: `uv run pytest --cov=pursuit --cov=training -q` → 456 passed, 2
  skipped (pre-existing GATE-4 skip), repo-wide coverage 97.0%+ (>= 85% floor)
- `uv run ruff check .` → 0 violations
- `bash scripts/check_line_limit.sh` → clean repo-wide (new files: `components.py` 100,
  `cycles.py` 37, `territory.py` 55, `__init__.py` 32 code lines — all under budget)
- `uv run python scripts/check_no_llm_in_strategy.py` → OK (new subpackage covered
  automatically, no forbidden imports)
- `grep -rn "cop\|thief" src/pursuit/strategy/graph/` → matches only inside docstrings
  (D-03: no role knowledge in code)
- Manual AST/grep check: no numeric literal beyond the cited `E - V + 1` / `d - 1`
  identities and ordinary loop arithmetic (`0`, `1`, `2`, `// 2`); board bounds come
  from `params.board_size`, deltas from `Direction`
- `graphify update .` re-run after the code landed: 3457 nodes / 6273 edges / 234
  communities; `.planning/graphs/GRAPH_REPORT.md` refreshed and committed alongside
  this summary (CLAUDE.md graphify lifecycle)

## Next Phase Readiness

`pursuit.strategy.graph` is a complete, tested, pure-library API ready for:

- **03-16** (feature vector `phi` + linear evaluation) — reads `cycle_rank`,
  `is_forest`, `reduction_value`, `territory_diff`, `articulation_points` as features
- **03-17** (barrier placement rewrite) — filters candidates by `reduction_value` and
  connectivity via `component_of`/`articulation_points`
- **03-18** (alpha-beta search) — the whole point of hoisting `free_cells()` to a
  single call per node (D-26): every other function in the package takes the already-
  derived cell set, so the inner loop never re-derives it

No blockers. `docs/phases/phase-3/TODO.md`'s row list for 03-11..03-16 still reflects
the pre-breakdown numbering from the post-mortem session (it describes "03-11 Thief
safety rule", which is now plan 03-12) — deliberately left untouched here, since
STATE.md's wave plan assigns the phase-triplet reconciliation to plan **03-24
("triplet refresh")**, not to each of the 15 individual run-2 plans. Next plan per
wave 1 is **03-12** (thief safety rule — never step into `N[cop]`).

---

## Self-Check: PASSED

Files confirmed present on disk:
- FOUND: `src/pursuit/strategy/graph/__init__.py`
- FOUND: `src/pursuit/strategy/graph/components.py`
- FOUND: `src/pursuit/strategy/graph/cycles.py`
- FOUND: `src/pursuit/strategy/graph/territory.py`
- FOUND: `tests/unit/strategy/graph/__init__.py`
- FOUND: `tests/unit/strategy/graph/test_components.py`
- FOUND: `tests/unit/strategy/graph/test_cycles.py`
- FOUND: `tests/unit/strategy/graph/test_territory.py`

Commits confirmed in `git log`:
- FOUND: `12be2e4` (Task 1: components.py)
- FOUND: `52c85f2` (Task 2: cycles.py)
- FOUND: `b4b06fa` (Task 3: territory.py)
- FOUND: `af5f0de` (deviation fix: coverage gaps)

Final full-suite confirmation (post-deviation-fix): `uv run pytest --cov=pursuit
--cov=training -q` → **456 passed, 2 skipped in 459.96s**, `Total coverage: 97.05%`.

---

*Phase: 03-blind-strategy-module-rl-policy*
*Completed: 2026-08-04*
