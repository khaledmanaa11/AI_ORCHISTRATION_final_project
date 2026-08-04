---
phase: 03-blind-strategy-module-rl-policy
plan: "12"
subsystem: strategy
tags: [thief-safety, d-31, fallback, bfs, regression-guard]

# Dependency graph
requires:
  - phase: 03-blind-strategy-module-rl-policy plan 03-11
    provides: pursuit.strategy.graph package (not consumed directly by this
      plan, but wave 1's sibling establishing the same measurement-layer
      discipline this plan follows for safety.py)
provides:
  - "src/pursuit/strategy/safety.py: closed_neighbourhood()/safe_moves(), the
    D-31 thief-side N[cop] filter, pure and never-empty"
  - "fallback.py::_evade wired to filter-then-rank: safe_moves() strips
    N[cop] before the unchanged (unreachable?, distance, onward) ranking key"
  - "tests/integration/test_thief_safety.py: a non-vacuous 160-game
    regression guard (20 committed GATE-4 scenarios + 60 seeded random
    starts x 2 arms) that cannot pass with a no-op filter"
affects: [03-19 (wires safe_moves into SearchBrain's thief movegen)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Filter-then-rank composition in a fallback movement function: strip
      unsafe candidates first, then apply the existing ranking key unchanged
      -- keeps 03-04's tie-break semantics intact without a second key"
    - "Monkeypatch-based two-arm regression test: patch the production call
      site (fallback.safe_moves) to a spy or a no-op inside
      monkeypatch.context() blocks, rather than adding a production-code
      toggle parameter just for testing"

key-files:
  created:
    - src/pursuit/strategy/safety.py
    - tests/unit/strategy/test_safety.py
    - tests/integration/test_thief_safety.py
  modified:
    - src/pursuit/strategy/fallback.py

key-decisions:
  - "safety.py's module docstring carries the full D-31 provenance (296/300
    = 0.987 vs 283/300 = 0.943) AND the unsoftened caveat ('provably
    unbeatable' did not fully reproduce, 3/20 losses, flawed control) in one
    place, matching the objective's exact wording -- nothing calling or
    testing this module may say 'provably safe'"
  - "The regression test's two arms differ ONLY by monkeypatching
    fallback.safe_moves (real spy vs a no-op identity function) inside
    monkeypatch.context() blocks -- no production toggle parameter was added
    to _evade or pick() just to make the arms comparable"
  - "tests/unit/strategy/test_fallback.py needed zero changes: verified by
    running it before and after wiring the filter, all 6 existing assertions
    are generic distance/reachability inequalities that hold under the
    filtered behaviour too, so none was rewritten (the plan's own
    conditional instruction to rewrite only genuinely-changed cases applied
    to zero cases here)"
  - "The plan's own context-section estimate of ~100ms/game did not
    reproduce: measured ~34-38s for the 160-game suite (~215-240ms/game),
    cProfile-traced to 03-07's pre-existing choose_barrier BFS-per-candidate
    scan (~80% of per-game cost), not this plan's own code. Recorded
    honestly in the test module's own docstring rather than cutting n=60 or
    disabling barrier placement to hit the stale <=30s target"

patterns-established:
  - "A pure filter module (safety.py) sits between the movegen oracle
    (get_legal_moves) and the ranking function (fallback._evade) without
    either function needing to know about the other's internals -- the same
    'filter, then rank' shape 03-19's SearchBrain will reuse for the
    thief's search-time movegen"

# Metrics
duration: ~21min
completed: 2026-08-04
---

# Phase 03 Plan 12: Thief safety rule -- never step into N[cop] Summary

**D-31's measured 296/300=0.987 vs 283/300=0.943 free win is now live in the thief's STRAT-02 fallback, filter-then-rank, guarded by a 160-game regression test that cannot pass with a no-op filter.**

## Performance

- **Duration:** ~21 min
- **Started:** 2026-08-04T12:38:00+03:00 (approx, immediately after 03-11's completion commit)
- **Completed:** 2026-08-04T12:59:00+03:00
- **Tasks:** 2 (both `type="auto"`, no checkpoints)
- **Files modified:** 4 (1 modified, 3 created)

## Accomplishments

- `src/pursuit/strategy/safety.py`: `closed_neighbourhood(state, params)` (N[cop] via one
  `get_legal_moves(state, "cop", params)` call) and `safe_moves(candidates, state, params)`
  (strips N[cop] cells, order-preserving, never returns `[]`). Pure, no module-level state
  (D-03). Docstring carries the full 296/300=0.987 vs 283/300=0.943 provenance and the
  unsoftened D-31 caveat.
- `fallback.py::_evade` filters legal moves through `safe_moves` before ranking survivors
  with the unchanged `(unreachable?, distance, onward)` key -- filter-then-rank, not a new
  key. `_pursue` and the cop path are byte-for-byte untouched.
- `tests/integration/test_thief_safety.py`: a bounded, non-vacuous regression guard --
  two arms (real filtered `safe_moves` vs a monkeypatched no-op) replayed over the 20
  committed GATE-4 scenarios plus 60 seeded random starts (`n=60`,
  `REGRESSION_TOLERANCE=0.05`, `seed=314159`, all named test-local constants per D-19).
  Asserts: the grid's filtered survival count is never below the unfiltered count; the
  random-start filtered rate never falls more than one noise band below the unfiltered
  rate; the filter actually strips a candidate at least once across the 160 games
  (non-vacuity); and the per-turn N[cop] invariant holds on every one of those 160 games'
  every thief turn (the assertion with real power, checked per turn via a spy wrapper
  around the real `safe_moves`, not just per game).

## Task Commits

Each task was committed atomically:

1. **Task 1: safety.py -- the N[cop] filter** - `71b201d` (feat)
2. **Task 2: Wire into _evade and prove the gain did not regress** - `20d87f6` (feat)

**Plan metadata:** (this commit) `docs(03-12): complete thief safety plan`

_Note: Task 1 was written test-first (`test_safety.py` confirmed red against a
`ModuleNotFoundError` before `safety.py` existed, then green after) per the plan's own
"Tests first" instruction; not a formal TDD-flagged task, so it is one commit, not three._

## Files Created/Modified

- `src/pursuit/strategy/safety.py` - N[cop] filter: `closed_neighbourhood()`, `safe_moves()`
- `tests/unit/strategy/test_safety.py` - 7 unit tests: removal, survival, never-empty,
  ordering, purity, barrier/off-board exclusion, cop's-own-cell membership
- `src/pursuit/strategy/fallback.py` - `_evade` now filters via `safe_moves` before ranking
- `tests/integration/test_thief_safety.py` - the 160-game non-vacuous regression guard

## Decisions Made

See `key-decisions` in the frontmatter above. In brief: the docstring provenance-plus-caveat
requirement was honored verbatim; the two-arm comparison uses `monkeypatch.context()` against
the real `fallback.safe_moves` call site rather than a new production toggle; no existing
`test_fallback.py` case needed rewriting (verified, not assumed); and the plan's own ~100ms/game
timing estimate was found not to reproduce and was corrected in the test module's own docstring
with the real measured number and its cause, rather than silently shrinking `n` or the tolerance
to hit the stale `<=30s` target.

## Deviations from Plan

### Auto-fixed Issues

**1. [Documentation correction, not a code fix -- closest to Rule 1] The plan's own ~100ms/game
budget assumption did not reproduce**
- **Found during:** Task 2, first full run of `test_thief_safety.py` (34.36s, then 37.97s on a
  second run alongside the unit suite -- both over the plan's stated `<=30s` target)
- **Issue:** The plan's context section stated "one head-to-head game costs ~100 ms" (sourced
  from a prior planning-session measurement of `training/eval_arms.py`); at that rate 160 games
  should take ~16s. The real measured cost is ~215-240ms/game, ~34-38s total.
- **Root cause (via `cProfile` on 10 real games):** `barriers.py::choose_barrier` (03-07,
  pre-existing, cop-side, entirely out of this plan's scope) is ~80% of per-game cost -- a
  BFS-distance-to-anchor scan over every free-cell barrier candidate, run every cop turn,
  regardless of which arm or filter is active.
- **Fix:** None applied to test design -- `n=60` was kept (it is load-bearing for the stated
  `REGRESSION_TOLERANCE=0.05` derivation) and barrier placement was kept enabled (disabling it
  would repeat D-31's own flawed disabled-barrier control, which this module explicitly does
  not reproduce). The test module's own docstring was corrected to state the real measured
  number, the real cause, and why neither `n` nor the tolerance nor barrier placement was
  changed to chase the stale target.
- **Files modified:** `tests/integration/test_thief_safety.py` (docstring only; no assertion,
  constant, or production code changed)
- **Verification:** `uv run pytest tests/integration/test_thief_safety.py -q --durations=5`
  passes with the honest number visible in `--durations` output; no test weakened.
- **Committed in:** `20d87f6` (Task 2 commit)

---

**Total deviations:** 1 (a documentation correction to a plan-provided timing assumption that
did not reproduce; no source-code behavior, tolerance, or sample size was altered).
**Impact on plan:** None on correctness or the regression bar itself -- only the test module's
own stated performance budget was corrected to match reality, per the standing project rule
against overstating a measured result.

## Issues Encountered

The full-repo `uv run pytest --cov` run took 7m47s (467.76s) on this Windows machine --
consistent with this project's known slow-full-suite pattern on this box, not specific to this
plan's changes (`--durations=5` on the scoped run isolates the actual cost to
`test_thief_safety.py`'s own ~34-38s, not the full-suite wall time). Confirmed the background
process was genuinely CPU-bound throughout (via `Get-Process ... CPU`), not the known Windows
stdio-hang pattern noted elsewhere in project memory for interactive subagents.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- D-31's measured thief-safety gain is live in `HeuristicBrain`'s thief path (both as the
  `QLearningBrain` fallback and as `HeuristicBrain` itself, since both route through
  `fallback.pick`/`_evade`) -- independent of the alpha-beta rewrite in waves 2-4.
- 03-19 (`SearchBrain`'s thief movegen) is the next consumer of `safety.safe_moves` per this
  plan's own scope boundary; nothing in 03-19's search code was touched here.
- Full repo gates green: `ruff check .` 0 violations, line-limit clean (new files 50/11/76/157
  code lines respectively -- `safety.py` well under its budget, `fallback.py` still well inside
  its own 150-line ceiling), 464 passed / 2 skipped (the same 2 pre-existing skips as 03-11:
  the GATE-4 smoke subset awaiting a trained table, and the 03-08 reference-clone test),
  coverage 97.95% (>=85% floor); `safety.py` and `fallback.py` both individually 100% covered.
- Graphify rebuilt (3523 nodes / 6406 edges / 233 communities) and `GRAPH_REPORT.md` refreshed
  and committed; `graph.json`/`graph.html` remain gitignored build artifacts per CLAUDE.md.
- `docs/phases/phase-3/TODO.md` deliberately not touched -- same rationale as 03-11: its row
  numbering predates the 15-plan wave breakdown and reconciling it is 03-24's explicit job.

---
*Phase: 03-blind-strategy-module-rl-policy*
*Completed: 2026-08-04*

## Self-Check: PASSED

All claimed files verified present on disk; both task commits (`71b201d`, `20d87f6`) verified
present in `git log --oneline --all`. No missing items.
