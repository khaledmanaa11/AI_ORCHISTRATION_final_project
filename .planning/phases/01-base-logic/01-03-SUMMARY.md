---
phase: 01-base-logic
plan: "03"
subsystem: shared-engine
tags: [capture, outcome, scoring, tdd, pure-function, immutable-state, base-03, base-04, base-05, base-06, base-07]

# Dependency graph
requires:
  - "01-01"  # GameState frozen dataclass, GameParams, Outcome enum, get_legal_moves
  - "01-02"  # place_barrier (barrier-on-thief states produced here, capture detected here)
provides:
  - src/pursuit/shared/capture.py (detect_capture + evaluate_turn_end pure functions)
  - src/pursuit/shared/outcome.py (score_outcome pure function)
  - tests/unit/test_capture.py (BASE-03..07 full test suite — 11 tests)
affects:
  - 01-04-sdk-facade (SDK turn engine calls detect_capture + evaluate_turn_end between cop and thief actions)

# Tech tracking
tech-stack:
  added: []  # no new packages; stdlib only
  patterns:
    - "D-12 check order: cop==thief (BASE-03) -> thief in barriers (BASE-04) -> no legal moves (BASE-05) -> None"
    - "D-13 note: BASE-05 independent trigger geometrically impossible (STAY always legal unless BASE-04)"
    - "D-16: evaluate_turn_end uses params.survival_threshold — no hardcoded value"
    - "D-15: Phase 1 produces only CAPTURE/SURVIVAL — TIE/TECHNICAL_LOSS unreachable but scored for completeness"
    - "AST scan discipline: zero numeric literals in capture.py; only literal 0 permitted in outcome.py"

key-files:
  created:
    - src/pursuit/shared/capture.py
    - src/pursuit/shared/outcome.py
  modified:
    - tests/unit/test_capture.py
    - docs/phases/phase-1/TODO.md

decisions:
  - "D-10 (boundary ownership): barrier-on-thief capture detected in detect_capture, not place_barrier"
  - "D-12 (D-12 check order enforced): BASE-03 -> BASE-04 -> BASE-05 in detect_capture; early-return on first match"
  - "D-13 (STAY always legal): BASE-05 never independently triggered; check included for future-proofing"
  - "D-14 (scoring from params): score_outcome reads exclusively from params.score_* fields; only literal 0 for TECHNICAL_LOSS"
  - "D-15 (Phase 1 outcomes): only CAPTURE and SURVIVAL produced; TIE/TECHNICAL_LOSS scored but unreachable"
  - "D-16 (survival threshold): evaluate_turn_end uses params.survival_threshold; zero hardcoded values"

# Metrics
duration: 5min
completed: 2026-07-28
---

# Phase 01 Plan 03: Capture Detection + Outcome Scoring Summary

**Three capture types (cop-on-thief, barrier-on-thief, no-legal-move) + turn-end survival detection + config-driven scoring; RED/GREEN/REFACTOR TDD; 11 tests at 97% coverage; zero numeric literals in capture.py; only literal 0 in outcome.py**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-07-28T11:56:29Z
- **Completed:** 2026-07-28T12:01:58Z
- **Tasks:** 3 (RED, GREEN, REFACTOR)
- **Files created:** 2 (capture.py, outcome.py)
- **Files modified:** 2 (test_capture.py, docs/phases/phase-1/TODO.md)

## Accomplishments

- Task 1 RED: Replaced 8 pytest.skip stubs in test_capture.py with 8 real BASE-03..07 assertions; RED gate confirmed with ModuleNotFoundError on pursuit.shared.capture
- Task 2 GREEN: Implemented capture.py (detect_capture + evaluate_turn_end) and outcome.py (score_outcome); all 8 tests pass; AST scan: zero numeric literals in capture.py, zero non-zero literals in outcome.py
- Task 3 REFACTOR: Full quality gate passed; added 3 coverage tests (TIE, TECHNICAL_LOSS, ValueError paths); total 11 tests at 97% coverage; full unit suite 32 passed (no regressions)

## Task Commits

Each task was committed atomically following TDD gate sequence:

1. **Task 1 RED: Failing capture/outcome tests** — `fc158eb` (test)
2. **Task 2 GREEN: Implement capture.py + outcome.py** — `48f15d0` (feat)
3. **Task 3 REFACTOR: Coverage completers + quality gate** — `b34edd6` (feat)

**TDD Gate Compliance:**
- RED gate: `fc158eb` — test(01-03) commit with ModuleNotFoundError confirmed
- GREEN gate: `48f15d0` — feat(01-03) commit with all 8 original tests passing
- REFACTOR gate: `b34edd6` — quality audits all passed, 11 tests, 97% coverage

## Files Created/Modified

- `src/pursuit/shared/capture.py` — detect_capture (BASE-03/04/05 D-12 check order) + evaluate_turn_end (BASE-06 D-16); module + function docstrings with D-12 timing contract; zero numeric literals (AST verified)
- `src/pursuit/shared/outcome.py` — score_outcome maps Outcome -> (cop_score, thief_score) from params; only literal 0 for TECHNICAL_LOSS; ValueError for unrecognised Outcome; 100% coverage
- `tests/unit/test_capture.py` — 11 tests: 8 BASE-03..07 assertions + 3 coverage completers (TIE score, TECHNICAL_LOSS score, ValueError guard)
- `docs/phases/phase-1/TODO.md` — 01-03 row marked ☑ done with commit hashes

## Decisions Made

- **D-12 check order enforced by code structure:** Three sequential early-return guards in detect_capture implement the canonical BASE-03 -> BASE-04 -> BASE-05 order; frozen GameState prevents any mutation between checks.
- **BASE-05 geometrically dependent on BASE-04:** As documented in the plan analysis, STAY is always legal unless the thief's own cell is a barrier (BASE-04). Therefore BASE-05 cannot trigger independently with current get_legal_moves semantics. The check is included for future-proofing. Coverage tool correctly marks line 65 (return Outcome.CAPTURE in BASE-05) as uncovered — this is by design.
- **TECHNICAL_LOSS uses literal 0:** No `score_technical_loss` field in GameParams (PARAMETERS Table 17 lists 0/0 as fixed). Using the literal 0 in outcome.py is correct and preferred over adding a spurious config field.
- **3 additional coverage tests added in REFACTOR:** TIE, TECHNICAL_LOSS, and ValueError paths were uncovered after GREEN. Added tests are named `test_tie_score`, `test_technical_loss_score`, `test_score_outcome_invalid_raises` — all pass.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical Functionality] Added coverage tests for TIE, TECHNICAL_LOSS, ValueError**
- **Found during:** Task 3 REFACTOR (coverage run showed outcome.py at 62%)
- **Issue:** Plan's 8 original tests only covered CAPTURE and SURVIVAL paths; TIE/TECHNICAL_LOSS/ValueError branches were uncovered. Total coverage was 81% (below 85% threshold).
- **Fix:** Added 3 tests (`test_tie_score`, `test_technical_loss_score`, `test_score_outcome_invalid_raises`) to test_capture.py. The plan's Task 3 explicitly calls for adding a ValueError test if not covered.
- **Files modified:** tests/unit/test_capture.py
- **Commit:** b34edd6

**2. [Rule 1 - Bug] Import ordering in test_capture.py violated ruff isort**
- **Found during:** Task 1 RED (ruff check ran before commit)
- **Issue:** `import pytest` was unused and import block ordering violated I001
- **Fix:** Removed `import pytest` at module level; reordered imports alphabetically; moved `import pytest` to local scope in `test_score_outcome_invalid_raises`
- **Files modified:** tests/unit/test_capture.py
- Fixed before RED commit

## Coverage Results

```
Name                            Stmts   Miss  Cover   Missing
-------------------------------------------------------------
src\pursuit\shared\capture.py      18      1    94%   65
src\pursuit\shared\outcome.py      13      0   100%
-------------------------------------------------------------
TOTAL                              31      1    97%
Required: 85% — PASSED (96.77% total)
```

Line 65 of capture.py (BASE-05 `return Outcome.CAPTURE`) is geometrically unreachable
given current `get_legal_moves` semantics — STAY is always legal unless the thief's own
cell is a barrier, which is caught by BASE-04 first. Documented in plan as by design.

## Named Test Pins Verified

| Test | Result |
|------|--------|
| test_cop_on_thief_capture | PASS |
| test_barrier_on_thief_capture | PASS |
| test_no_legal_move_capture | PASS |
| test_one_move_available_no_capture | PASS |
| test_survival_at_threshold | PASS |
| test_game_continues_below_threshold | PASS |
| test_capture_score | PASS |
| test_survival_score | PASS |

## Static Audit

| Check | Result |
|-------|--------|
| `uv run ruff check .` | 0 violations |
| `bash scripts/check_line_limit.sh` | all files pass |
| AST numeric literal scan on capture.py | `[]` (empty — zero literals) |
| AST non-zero literal scan on outcome.py | `[]` (empty — only literal 0 permitted) |
| `grep -c "detect_capture" src/pursuit/shared/capture.py` | 2 (def + docstring) |
| `grep -c "score_outcome" src/pursuit/shared/outcome.py` | 2 (def + docstring) |
| `grep -c "frozen=True" src/pursuit/shared/state.py` | 1 (inherited from 01-01) |

## Self-Check: PASSED

All files verified to exist and commits verified in git log.
