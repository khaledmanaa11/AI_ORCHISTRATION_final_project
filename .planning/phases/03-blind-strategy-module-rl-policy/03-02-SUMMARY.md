---
phase: 03-blind-strategy-module-rl-policy
plan: "02"
subsystem: strategy
tags: [abc, dataclass, enum, ast-structural-test, config-registry, strat-03, strat-07]

# Dependency graph
requires:
  - phase: 03-00
    provides: StrategyKey/TrainingKey enums, StrategyParams.brain_class (already per-role resolved), load_strategy_config()
provides:
  - src/pursuit/strategy/{__init__,base,registry}.py — BrainBase ABC + frozen Observation/Decision + build_brain
  - Action IntEnum (frozen 5-action order) + MoveSource str Enum + cell_for/action_for in constants.py
  - AST-based structural gates (no pursuit.network import, no LLM/HTTP/subprocess/socket import) proven to fail on introduction
affects: [03-03, 03-04, 03-05, 03-06, 03-07, "every later Phase-3 plan implementing a concrete brain or a strategy submodule"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Action/Direction share member names (NORTH/SOUTH/EAST/WEST/STAY) so cell_for/action_for reuse Direction's deltas via Direction[action.name] instead of a second literal-delta table — zero duplication, no module-level dict"
    - "Explicit name-to-class dict registry (never eval/exec/importlib on a config string) as the only brain-construction path; concrete brains land in it by editing registry.py in 03-04/03-06, not by a runtime self-registration call"
    - "Package-wide AST import-walk test (walks src/pursuit/strategy/**/*.py via pathlib.rglob, not an enumerated file list) so 03-03..03-07 adding new modules stay covered automatically"

key-files:
  created:
    - src/pursuit/strategy/__init__.py
    - src/pursuit/strategy/base.py
    - src/pursuit/strategy/registry.py
    - tests/unit/strategy/test_base.py
    - tests/unit/strategy/test_registry.py
  modified:
    - src/pursuit/constants.py
    - docs/phases/phase-3/TODO.md
    - .planning/graphs/GRAPH_REPORT.md

key-decisions:
  - "build_brain(role, params) passes role through to the brain constructor (brain_cls(role=role, params=params)) even though params.brain_class is already role-resolved by load_strategy_config — role lets a two-stage brain (movement then barrier) know which role it plays without a second config read; this fixes the constructor calling convention 03-04/03-06 must match, since docs/phases/phase-3/PLAN.md's interface table names build_brain's signature but not a concrete brain's __init__"
  - "cell_for/action_for reuse Direction's existing (row_delta, col_delta) tuples via Direction[action.name] rather than a second hardcoded delta table, because Action and Direction were deliberately given identical member names — avoids duplicating the movement deltas Table 15 already fixes once in Direction"
  - "_BRAIN_REGISTRY is a private module-level dict in registry.py, not a runtime-registration function — later plans add entries by editing this file directly (a source change), which is not project-rule-2 shared *game* state: it is a process-local, read-only-at-runtime class lookup table, identical in kind to Direction/Action already living at module scope in constants.py"
  - "Forbidden-import deny-list in the STRAT-07 structural test names concrete libraries (socket, subprocess, http, requests, httpx, aiohttp, urllib3, openai, anthropic, google.generativeai, cohere) rather than a vaguer pattern match, so the test is auditable and was demonstrated to actually fail (temporarily added `import socket` to base.py, confirmed RED, reverted, confirmed GREEN)"

patterns-established:
  - "Two-commit split for a single plan-declared file: Task 2 and Task 3 both list tests/unit/strategy/test_registry.py as their file, so the file was drafted in full then re-split into two Write calls (Task-2-only content, committed; then an Edit appending Task-3 content, committed) so each task keeps its own atomic commit"

# Metrics
duration: 12min
completed: 2026-07-31
---

# Phase 3 Plan 02: BrainBase Seam + Config-Driven Brain Registry Summary

**`BrainBase` ABC with frozen `Observation`/`Decision` contracts, a frozen 5-action `Action` IntEnum pinned by test, and `build_brain()` resolving `[strategy]` class names through an explicit dict — no `eval`/`exec`/importlib, and an AST-walk test that provably fails when the strategy package imports networking or an LLM/HTTP/subprocess/socket facility.**

## Performance

- **Duration:** 12 min
- **Started:** 2026-07-31T16:33:18Z
- **Completed:** 2026-07-31T16:45:21Z
- **Tasks:** 3 completed
- **Files modified:** 5 created, 3 modified

## Accomplishments
- `src/pursuit/strategy/base.py`: frozen `Observation` (own_cell/target_cell/blocked_mask/barriers_used/turn_index, with the D-11 believed-target contract stated verbatim in its docstring) and frozen `Decision` (move/source/barrier=None default); `BrainBase(ABC)` with abstract `_pick_move`/`_decide_move`, both taking `GameState` explicitly as a second argument per D-05/STRAT-07.
- `src/pursuit/constants.py`: `MoveSource` str Enum (QTABLE/FALLBACK/HEURISTIC) and the canonical, order-frozen `Action` IntEnum (NORTH=0/SOUTH=1/EAST=2/WEST=3/STAY=4) plus `cell_for`/`action_for`, round-trip tested from an interior cell for every action; file lands at exactly 150 code lines (the gate's own ceiling, confirmed via `scripts/check_line_limit.sh`).
- `src/pursuit/strategy/registry.py`: `build_brain(role, params)` resolves `params.brain_class` through an explicit, empty-for-now `_BRAIN_REGISTRY` dict; unknown names raise `ValueError` naming the offending value and every known name; zero `eval`/`exec` calls (AST-verified, not string-matched).
- `tests/unit/strategy/test_registry.py`: package-wide AST-walk structural tests for STRAT-03 (no `pursuit.network` import anywhere under `src/pursuit/strategy/`) and STRAT-07 (no import from a named socket/subprocess/HTTP/LLM deny-list) — both demonstrated to actually fail when a forbidden import was temporarily introduced into `base.py`, then reverted clean (`git diff` empty).
- Full repo gates green: `uv run ruff check .` → 0 violations; `bash scripts/check_line_limit.sh` → clean; `uv run pytest --cov=pursuit --cov=training -q` → 207 passed, 97.06% coverage (`training/` still unimported — expected, 03-08 creates it).
- Graphify graph rebuilt after the new code landed (2188 nodes / 3069 edges / 178 communities); `.planning/graphs/GRAPH_REPORT.md` refreshed and committed, `graph.json`/`graph.html` regenerated as gitignored artifacts.

## Task Commits

Each task was committed atomically:

1. **Task 1: BrainBase + Observation/Decision contracts** - `022f42f` (feat)
2. **Task 2: Config-driven brain registry with fail-loud resolution** - `b948f5a` (feat)
3. **Task 3: Structural isolation tests (STRAT-03 and STRAT-07)** - `a0389c6` (test)

**Plan metadata:** (this commit, following SUMMARY/STATE update)

## Files Created/Modified
- `src/pursuit/strategy/__init__.py` - exports BrainBase/Decision/Observation only, no brain re-exports
- `src/pursuit/strategy/base.py` - Observation, Decision, BrainBase
- `src/pursuit/strategy/registry.py` - build_brain, `_BRAIN_REGISTRY`
- `src/pursuit/constants.py` - MoveSource, Action, cell_for, action_for
- `tests/unit/strategy/test_base.py` - 12 tests (ABC enforcement, frozen contracts, Action pin, round-trip)
- `tests/unit/strategy/test_registry.py` - 16 tests (resolution/fail-loud/no-eval-exec + 2 package-wide structural gates)
- `docs/phases/phase-3/TODO.md` - row 03-02 marked ☑
- `.planning/graphs/GRAPH_REPORT.md` - refreshed after this plan's new code

## Decisions Made
See `key-decisions` in frontmatter. In brief: `build_brain` passes `role` through to the brain constructor for later plans to consume; `cell_for`/`action_for` reuse `Direction`'s existing deltas via name-matching rather than duplicating them; `_BRAIN_REGISTRY` is a private, source-edited dict (not a runtime self-registration API); the STRAT-07 deny-list names concrete libraries and was verified to actually fail when triggered.

## Deviations from Plan

None — plan executed exactly as written. The one procedural adjustment (splitting `tests/unit/strategy/test_registry.py`'s content into two Write/Edit passes so Task 2 and Task 3 each got their own atomic commit despite naming the same file) is a commit-mechanics choice, not a deviation from scope, behavior, or the plan's `must_haves`.

## Issues Encountered
- `constants.py` had only 23 code lines of headroom before the 150-line gate (127 pre-existing). `MoveSource`/`Action`/`cell_for`/`action_for` were written with terse one-line docstrings to land at exactly 150 code lines, confirmed via the gate script itself rather than a manual line count — no logic was compressed, only comment verbosity was trimmed.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- 03-03 (BFS pathfinding) can now depend on `Observation`/`Decision`/`GameState` and the frozen `Action` order without any risk of renumbering.
- 03-04 and 03-06 register `HeuristicBrain`/`QLearningBrain` into `_BRAIN_REGISTRY` and must match the `brain_cls(role=role, params=params)` constructor calling convention fixed by this plan's `build_brain`.
- No blockers. The registry's `ValueError` fail-loud path and the two AST structural tests are stable contracts every later strategy module automatically inherits (the import-walk tests scan the package directory, not an enumerated file list).

---
*Phase: 03-blind-strategy-module-rl-policy*
*Completed: 2026-07-31*

## Self-Check: PASSED

All 9 claimed files confirmed present on disk (`src/pursuit/strategy/{__init__,base,registry}.py`,
`tests/unit/strategy/{test_base,test_registry}.py`, `src/pursuit/constants.py`,
`docs/phases/phase-3/TODO.md`, `.planning/graphs/GRAPH_REPORT.md`, this SUMMARY).
All 3 task commit hashes (`022f42f`, `b948f5a`, `a0389c6`) confirmed present in
`git log --oneline --all`.
