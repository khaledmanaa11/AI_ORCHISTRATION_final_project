---
phase: 01-base-logic
plan: "04"
subsystem: sdk-facade
tags: [sdk, facade, integration-tests, tdd, documentation]
dependency_graph:
  requires:
    - 01-01: GameState, GameParams, get_legal_moves, apply_move
    - 01-02: place_barrier
    - 01-03: detect_capture, evaluate_turn_end, score_outcome, increment_turn
  provides:
    - engine.make_state
    - engine.legal_moves
    - engine.apply_cop_action
    - engine.apply_thief_move
    - engine.check_capture
    - engine.score
  affects:
    - Phase 2: sole entry point via pursuit.sdk.engine
tech_stack:
  added: []
  patterns:
    - Thin facade delegating to owning shared modules (QUAL-01)
    - Immutable state chain (frozen dataclass + dataclasses.replace)
    - D-12 turn wiring: apply_cop_action -> apply_thief_move
    - increment_turn helper in state.py to avoid numeric literal in facade
key_files:
  created:
    - src/pursuit/sdk/engine.py
    - docs/phases/phase-1/PRD.md
    - docs/phases/phase-1/PLAN.md
    - docs/phases/phase-1/TODO.md
  modified:
    - tests/unit/test_sdk_engine.py
    - tests/integration/test_game_loop.py
    - src/pursuit/shared/state.py
    - docs/TODO.md
decisions:
  - "D-09: engine.apply_cop_action wires cop move + barrier placement as one cop action (D-09)"
  - "D-12: engine.apply_cop_action does cop-acts + capture-check; apply_thief_move does thief-move + turn-increment + survival-check"
  - "increment_turn() helper added to state.py so engine.py has zero non-zero numeric literals (AST-clean)"
metrics:
  duration: 9min
  completed: 2026-07-28
  tasks_completed: 4
  files_modified: 8
---

# Phase 01 Plan 04: SDK Facade + Integration Gate Summary

**One-liner:** SDK facade `engine.py` wires D-12 turn pipeline over existing shared modules; three §10.4 gate tests confirm GATE-1/2/3 pass end-to-end.

## What Was Built

### src/pursuit/sdk/engine.py (new)

Thin facade over all Phase 1 shared modules. Six public functions, zero business logic duplicated:

- `make_state(params)` — factory from config start positions
- `legal_moves(state, agent, params)` — delegates to `get_legal_moves`
- `apply_cop_action(state, move_to, barrier_at, params)` — D-12 steps 1–2: move + barrier + capture check
- `apply_thief_move(state, move_to, params)` — D-12 steps 3–4: move + turn increment + survival check
- `check_capture(state, params)` — delegates to `detect_capture`
- `score(outcome, params)` — delegates to `score_outcome`

No numeric literals except `0` in `make_state`; AST scan confirms zero non-zero literals.
100% test coverage; all 10 tests (7 unit + 3 gate integration) pass.

### tests/unit/test_sdk_engine.py (replaced Wave 0 stubs)

Seven real delegation tests covering each SDK method. All values from `default_params` fixture — no hardcoded game numbers.

### tests/integration/test_game_loop.py (replaced Wave 0 stubs)

Three §10.4 gate tests:
- `test_legal_turn_sequence` — GATE-1: legal cop+thief turn, game continues
- `test_barrier_quota_gate` — GATE-2: over-quota barrier rejected, state unchanged
- `test_all_capture_types` — GATE-3: BASE-03/04/05 each yield `Outcome.CAPTURE`

### docs/phases/phase-1/{PRD,PLAN,TODO}.md (new)

Phase 1 documentation triplet per CLAUDE.md per-phase requirement:
- **PRD.md:** BASE-01..BASE-08 + QUAL-01/06; GATE-1/2/3 as §10.4 acceptance criteria
- **PLAN.md:** Components table, interfaces, ADRs P1-1/P1-2, TDD test plan
- **TODO.md:** Rows 1-00..1-04 + 1-99, definitions of done, §10.4 gate checklist

### docs/TODO.md (updated)

Row `01-04` added to Phase 1 section; per-phase triplet table updated to ◐ (in-progress) for Phase 1.

## TDD Discipline

| Phase | Commit | Verification |
|-------|--------|-------------|
| RED | d8a7d67 | ImportError confirmed — engine.py did not exist |
| GREEN | 3117176 | All 10 tests pass; ruff 0; line limit passes; AST scan clean |
| REFACTOR | — | Full 42-test suite green; 100% coverage; no source changes needed |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Non-zero literal `1` in engine.py failed AST scan**

- **Found during:** Task 2 GREEN (AST spot-check)
- **Issue:** The prescribed `turn=after_move.turn + 1` placed a literal `1` in `engine.py`, causing the scan `n.value not in (0,)` to return `[1]`
- **Fix:** Added `increment_turn(state) -> GameState` helper to `src/pursuit/shared/state.py`; engine.py delegates to it (`after_tick = increment_turn(after_move)`)
- **Files modified:** `src/pursuit/shared/state.py` (added helper), `src/pursuit/sdk/engine.py` (removed `import dataclasses`, replaced inline replace with `increment_turn`)
- **Commit:** 3117176

**2. [Rule 3 - Ruff] Unused `pytest` import and unsorted imports in test files**

- **Found during:** Task 1 RED (ruff check)
- **Issue:** Both test files had `import pytest` (unused — fixtures injected by conftest) and unsorted imports
- **Fix:** Removed `pytest` import; sorted import blocks per ruff I001
- **Commit:** d8a7d67

## Self-Check

### Files created/modified — existence check

- [x] `src/pursuit/sdk/engine.py` — created
- [x] `tests/unit/test_sdk_engine.py` — 7 real tests
- [x] `tests/integration/test_game_loop.py` — 3 gate tests
- [x] `docs/phases/phase-1/PRD.md` — contains "Acceptance criteria" and BASE-01
- [x] `docs/phases/phase-1/PLAN.md` — contains "Components" and engine.py
- [x] `docs/phases/phase-1/TODO.md` — contains "1-04" and "Phase gate"
- [x] `docs/TODO.md` — contains "01-04" row
- [x] `src/pursuit/shared/state.py` — contains `increment_turn`

### Commits

- d8a7d67 — `test(01-04): add failing tests for SDK facade + integration gates (RED)`
- 3117176 — `feat(01-04): implement SDK facade engine.py (GREEN — QUAL-01)`
- fac6cec — `docs(01-04): per-phase doc triplet + root TODO update`

## Self-Check: PASSED
