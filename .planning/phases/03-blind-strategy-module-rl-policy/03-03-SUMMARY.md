---
phase: 03-blind-strategy-module-rl-policy
plan: "03"
subsystem: strategy
tags: [bfs, pathfinding, distance-oracle, barrier-aware, strat-04, d-09]

# Dependency graph
requires:
  - phase: 03-00
    provides: StrategyParams (move_ceiling not used directly here, board bounds via GameParams)
  - phase: 01-04
    provides: pursuit.shared.board.get_legal_moves (the single adjacency/barrier rule reused, QUAL-02)
provides:
  - src/pursuit/strategy/pathfind.py -- bfs(state, start, goal, agent, params) -> (distance, next_step), the single barrier-aware distance oracle for the phase
  - UNREACHABLE sentinel constant (int, -1) for goals walled off by barriers
affects: [03-04, 03-07, "every later Phase-3 plan needing a barrier-aware distance"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "BFS adjacency delegated entirely to board.get_legal_moves via a per-cell probe state (dataclasses.replace(state, cop=cell) or thief=cell) rather than reimplementing in-bounds/barrier checks -- QUAL-02's single source of movement truth extends to pathfinding"
    - "Deterministic tie-break: neighbours sorted ascending (row, col) before every expansion, so BFS's FIFO level-order processing always resolves an equal-distance first-step tie to the same cell on every call"
    - "Sentinel int (-1) rather than math.inf for UNREACHABLE, documented at the module level, so callers get a plain, type-stable int in both the reachable and unreachable cases"

key-files:
  created:
    - src/pursuit/strategy/pathfind.py
    - tests/unit/strategy/test_pathfind.py
  modified:
    - docs/phases/phase-3/TODO.md
    - .planning/graphs/GRAPH_REPORT.md

key-decisions:
  - "bfs() takes explicit start/goal cells plus an agent role string, not just state -- the search explores hypothetical positions the real state doesn't hold, so every BFS expansion step builds a fresh probe state via dataclasses.replace and re-queries get_legal_moves on it, never re-deriving adjacency by hand"
  - "UNREACHABLE = -1 (a plain int), not math.inf -- keeps the return type a single, non-mixed numeric type across both branches and avoids a float/int comparison surprise at call sites in 03-04/03-07"
  - "No walk() convenience added to pathfind.py -- gameplay calls bfs() fresh every turn with the updated live state (the real turn loop), so a multi-step walk is purely a test-time simulation concern; keeping the module to a single public function left ample headroom under the 150-line gate (86 code lines)"
  - "Test-file split across the plan's two tasks: Task 1's commit carries pathfind.py plus the two simplest sanity tests (open-board Manhattan equivalence, adjacent/identical-cell edge cases) that would naturally drive bfs()'s initial TDD pass; Task 2's commit adds the five tests that specifically prove STRAT-04's actual wording (walk-proof, barrier-pocket, fully-walled-off, determinism/tie-break, termination-bound)"

patterns-established:
  - "Distance-oracle test pattern: build a `_walk()` test helper that repeatedly re-calls the production function (never a separate walk implementation) with a move_ceiling-derived budget, so 'the agent walks' is asserted as behavior, not inferred from the returned integer alone"

# Metrics
duration: 18min
completed: 2026-07-31
---

# Phase 3 Plan 03: Barrier-Aware BFS Distance Oracle Summary

**`bfs()` -- a single barrier-aware BFS distance oracle with deterministic tie-breaking, reusing the Phase-1 engine's `get_legal_moves` for every step, that both the Bayes fallback (03-04) and the barrier sub-policy (03-07) will consume rather than reimplementing distance twice.**

## Performance

- **Duration:** 18 min
- **Started:** 2026-07-31T16:45:21Z
- **Completed:** 2026-07-31T17:03:18Z
- **Tasks:** 2 completed
- **Files modified:** 2 created, 2 modified (docs TODO row, graph report)

## Accomplishments
- `src/pursuit/strategy/pathfind.py` (86 code lines): `bfs(state, start, goal, agent, params) -> tuple[int, Coord | None]`, breadth-first over cells reached via `board.get_legal_moves` on a per-step probe state -- zero reimplemented adjacency or barrier-membership logic (QUAL-02, verified by inspection: the module contains no in-bounds or `in state.barriers` check of its own).
- `UNREACHABLE: int = -1` module-level sentinel returned with `None` when a goal is walled off; never raises, matching the real constraint that a cop can legally spend its whole 14-barrier quota enclosing the thief.
- Deterministic tie-breaking: neighbours sorted ascending `(row, col)` before every BFS expansion, so two equal-distance first steps resolve to the same cell on every call -- documented in the module docstring for 03-04/03-07 and Phase 6/7 replay-reproducibility to rely on.
- `tests/unit/strategy/test_pathfind.py`: 7 named tests covering open-board Manhattan equivalence, the walk-proof (repeated `next_step` application reaches goal in exactly the reported distance, budget-capped by `move_ceiling`), a named barrier-pocket case (wall with gaps only at the two far edges -- the Manhattan-nearest neighbour stalls at the wall forever, `bfs()` detours through a gap), fully-walled-off goal (sentinel + `None`), adjacent/identical-cell edge cases, determinism + tie-break stability, and a second termination-bound test on a corner-to-corner board traversal.
- Deviation-rule QA performed live and reverted: `bfs()`'s body was temporarily replaced with a one-step Manhattan-greedy stepper; re-running the suite confirmed the walk-proof and barrier-pocket tests fail against it (`3 failed, 4 passed`), then the real BFS was restored and the full suite re-confirmed green (`git diff` on `pathfind.py` empty afterward).
- Full repo gates green: `uv run ruff check .` → 0 violations; `bash scripts/check_line_limit.sh` → clean; `uv run pytest --cov=pursuit --cov=training -q` → 214 passed, 97.14% coverage (`pathfind.py` itself at 100%).
- Graphify graph rebuilt (2244 nodes / 3179 edges / 177 communities); `.planning/graphs/GRAPH_REPORT.md` refreshed and committed.

## Task Commits

Each task was committed atomically:

1. **Task 1: Barrier-aware BFS returning distance and next step** - `1523bbc` (feat)
2. **Task 2: The tests that actually prove STRAT-04** - `61b9240` (test)

**Plan metadata:** (this commit, following SUMMARY/STATE update)

## Files Created/Modified
- `src/pursuit/strategy/pathfind.py` - `bfs()`, `UNREACHABLE`, `Coord`, and two private helpers (`_sorted_neighbors`, `_reconstruct_first_step`)
- `tests/unit/strategy/test_pathfind.py` - 7 tests + `_state`/`_manhattan`/`_greedy_first_step`/`_walk` helpers
- `docs/phases/phase-3/TODO.md` - row 03-03 marked ☑
- `.planning/graphs/GRAPH_REPORT.md` - refreshed after this plan's new code

## Decisions Made
See `key-decisions` in frontmatter. In brief: `bfs()` accepts explicit `start`/`goal` cells rather than reading only `state.cop`/`state.thief`, since the search must explore hypothetical positions the live state doesn't hold, each expansion step probes `get_legal_moves` via a `dataclasses.replace`d state; `UNREACHABLE` is a plain `int` (`-1`), not `math.inf`, for return-type stability; no `walk()` helper was added to the module since gameplay calls `bfs()` fresh every turn and a full walk is only ever a test-time simulation concern; the two plan tasks were kept on separate commits by splitting the test file's content (matching the pattern already established in 03-02).

## Deviations from Plan

### Auto-fixed Issues

None required — the plan's own literal `<verify>` instruction for Task 2 (deliberately corrupt BFS to a Manhattan-greedy stepper, confirm the relevant tests fail, then revert) was carried out exactly as written, with one adaptation documented below since it is a test-design choice, not a bug fix.

**1. [Design adaptation, not a deviation from scope] The "walk" test needed an on-path barrier to actually fail under the plan's corruption check**

- **Found during:** Task 2's own verification step (deliberately replacing `bfs()`'s body with a Manhattan-greedy stepper and confirming the plan's referenced "tests 2 and 3" fail)
- **Issue:** My first draft of the walk-proof test used a barrier-free board (to keep it a pure "does it walk" check, independent of barrier logic already covered by the pocket test). Under the corruption, an open board still lets a one-step Manhattan-greedy stepper walk correctly to the goal (no obstruction to stall on), so that test did not fail — only the barrier-pocket and fully-walled-off tests failed, not matching the plan's literal expectation that the walk-proof test itself also fails against a naive corruption.
- **Fix:** Added a single barrier directly on the straight line between start and goal in the walk-proof test (a minimal obstruction, not the elaborate pocket-wall the dedicated pocket test uses). A one-step Manhattan-greedy stepper provably stalls at any on-axis barrier (moving off-axis always increases raw Manhattan distance, so "stay" is locally optimal), while `bfs()`'s real detour still completes. Re-ran the corruption check: walk-proof and barrier-pocket tests both failed as the plan specifies; reverted to the real `bfs()`, both green again.
- **Files modified:** `tests/unit/strategy/test_pathfind.py` (test scenario only; no change to `pathfind.py`)
- **Verification:** Corruption re-applied and re-reverted a second time; final state confirmed via `git diff` (empty) on `pathfind.py` and `uv run pytest tests/unit/strategy/test_pathfind.py -q` → 7 passed.
- **Committed in:** `61b9240` (Task 2 commit — the final, correct test scenario is what landed; the intermediate barrier-free draft was never committed)

---

**Total deviations:** 0 auto-fixed bug/blocking fixes (Rules 1-3 did not trigger); 1 test-design adaptation made while carrying out the plan's own explicit verification instruction, so that instruction's literal wording ("tests 2 and 3 fail") would actually hold for whichever two tests occupy those roles in this plan's own numbering.
**Impact on plan:** None on scope, `must_haves`, or `pathfind.py` itself — the adaptation only sharpened one test's board layout so the plan's demonstrate-then-revert QA step is genuinely evidentiary rather than incidentally true.

## Issues Encountered
None beyond the design adaptation above. `pathfind.py` landed at 86 code lines, well under the 150-line gate, with ample headroom.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- 03-04 (Bayes motion prior + fallback + `HeuristicBrain`) can import `bfs`/`UNREACHABLE` directly from `pursuit.strategy.pathfind` and use it as the fallback's distance metric with no further oracle work.
- 03-07 (cop barrier sub-policy) consumes the same `bfs()` to evaluate whether a candidate barrier placement increases the thief's escape distance — no second distance implementation needs to exist anywhere in the phase (QUAL-02 upheld).
- No blockers. The sentinel contract (`UNREACHABLE`, `None`) is stable and tested; both later consumers must branch on it rather than assume a numeric distance is always present.

---
*Phase: 03-blind-strategy-module-rl-policy*
*Completed: 2026-07-31*

## Self-Check: PASSED

All 4 claimed files confirmed present on disk (`src/pursuit/strategy/pathfind.py`,
`tests/unit/strategy/test_pathfind.py`, `docs/phases/phase-3/TODO.md`,
`.planning/graphs/GRAPH_REPORT.md`).
Both task commit hashes (`1523bbc`, `61b9240`) confirmed present in `git log --oneline --all`.
