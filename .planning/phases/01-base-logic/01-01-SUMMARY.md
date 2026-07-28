---
phase: 01-base-logic
plan: "01"
subsystem: shared-engine
tags: [config, board, movement, tdd, constants, enums, immutable-state]

# Dependency graph
requires:
  - "01-00"  # uv project + game_params.json + stub test files
provides:
  - src/pursuit/constants.py (Direction/CellState/Outcome/ConfigKey enums)
  - src/pursuit/shared/config.py (load_game_params -> GameParams; fail-loud)
  - src/pursuit/shared/state.py (GameState frozen dataclass)
  - src/pursuit/shared/board.py (get_legal_moves + apply_move pure functions)
  - tests/unit/test_config.py (BASE-08 full test suite — 6 tests)
  - tests/unit/test_board.py (BASE-01 full test suite — 7 tests)
  - docs/phases/phase-1/{PRD,PLAN,TODO}.md (phase docs triplet)
affects:
  - 01-02-barrier-quota (imports GameState, GameParams, get_legal_moves from shared)
  - 01-03-capture (imports GameState, GameParams, Outcome from shared)
  - 01-04-sdk-facade (imports all shared modules via SDK layer)

# Tech tracking
tech-stack:
  added: []  # no new packages — stdlib only (enum, dataclasses, json, pathlib)
  patterns:
    - "Immutable GameState snapshot: @dataclass(frozen=True); dataclasses.replace for transitions"
    - "Pure function pipeline: get_legal_moves and apply_move are stateless, side-effect-free"
    - "Fail-loud config: KeyError on missing key, TypeError on wrong type, at load time (D-05)"
    - "Direction enum as single source of orthogonal deltas: board.py iterates Direction, never re-lists"
    - "ConfigKey class: string constants matching exact JSON keys, used in load_game_params"

key-files:
  created:
    - src/pursuit/shared/config.py
    - src/pursuit/shared/state.py
    - src/pursuit/shared/board.py
    - docs/phases/phase-1/PRD.md
    - docs/phases/phase-1/PLAN.md
    - docs/phases/phase-1/TODO.md
  modified:
    - src/pursuit/constants.py
    - tests/unit/test_config.py
    - tests/unit/test_board.py

decisions:
  - "D-05 (config as numeric truth root): load_game_params is the only entry point; game_params.json is the single source of all numeric values"
  - "D-07 (constants.py structural-only): Direction/CellState/Outcome/ConfigKey; zero numeric game values"
  - "D-08 (barriered cell is impassable): get_legal_moves excludes barriers from candidates"
  - "D-12 (immutable snapshot): GameState @dataclass(frozen=True); dataclasses.replace for new states"
  - "D-13 (STAY always legal): STAY (current pos) bypasses all filters in get_legal_moves"
  - "D-14 (Outcome enum): all four outcomes named; only CAPTURE/SURVIVAL produced in Phase 1"

# Metrics
duration: 15min
completed: 2026-07-28
---

# Phase 01 Plan 01: Config Loader + Board Model + Movement Summary

**Config loader (fail-loud) + immutable GameState + orthogonal movement engine built with RED/GREEN/REFACTOR TDD; 13 tests pass with 99% coverage; zero numeric game values in any source file**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-07-28T11:20:14Z
- **Completed:** 2026-07-28T11:36:05Z
- **Tasks:** 3 (RED, GREEN, REFACTOR)
- **Files created:** 6 (3 source + 3 docs)
- **Files modified:** 3 (constants.py + 2 test files)

## Accomplishments

- Task 1 RED: Replaced 9 pytest.skip stubs (4 in test_config.py, 5 in test_board.py) with 13 real assertions; RED gate confirmed with ModuleNotFoundError
- Task 2 GREEN: Implemented constants.py (Direction/CellState/Outcome/ConfigKey), state.py (GameState frozen dataclass), config.py (load_game_params with fail-loud validation), board.py (get_legal_moves + apply_move iterating Direction enum); all 13 tests pass
- Task 3 REFACTOR: Full quality gate passed; docs/phases/phase-1 triplet created; 99% coverage on new modules
- Test pins verified: test_missing_key_raises, test_stay_is_legal, test_diagonal_move_rejected, test_wrong_type_raises — all PASS

## Task Commits

Each task was committed atomically following TDD gate sequence:

1. **Task 1 RED: Failing tests for config loader + board movement** — `796e63f` (test)
2. **Task 2 GREEN: Implement constants + config + state + board** — `6ec770b` (feat)
3. **Task 3 REFACTOR: Phase-1 doc triplet + REFACTOR gate confirmed** — `3e483af` (feat)

**TDD Gate Compliance:**
- RED gate: `796e63f` — test(01-01) commit with ModuleNotFoundError confirmed
- GREEN gate: `6ec770b` — feat(01-01) commit with all 13 tests passing
- REFACTOR gate: `3e483af` — quality audits all passed, docs created

## Files Created/Modified

- `src/pursuit/constants.py` — Direction(NORTH/SOUTH/EAST/WEST/STAY), CellState, Outcome, ConfigKey; zero numeric game values (D-07)
- `src/pursuit/shared/config.py` — load_game_params(path) -> GameParams; _require_key + _require_int helpers; fail-loud (D-05)
- `src/pursuit/shared/state.py` — GameState @dataclass(frozen=True); cop/thief/barriers/barriers_placed/turn fields
- `src/pursuit/shared/board.py` — get_legal_moves (iterates Direction, filters OOB+barriers, always includes STAY); apply_move (dataclasses.replace)
- `tests/unit/test_config.py` — 6 tests: board_size, barrier_quota, scoring, missing_key, wrong_type, int_check
- `tests/unit/test_board.py` — 7 tests: orthogonal, diagonal_reject, stay_legal, OOB, barrier, apply_cop, apply_thief
- `docs/phases/phase-1/PRD.md` — phase goal, BASE-01..08 requirements, acceptance criteria, scope
- `docs/phases/phase-1/PLAN.md` — component table, interface contracts, ADRs D-05/07/08/12/13/14
- `docs/phases/phase-1/TODO.md` — task list with 01-00/01-01 marked done

## Decisions Made

- **Direction enum as single delta source:** board.py does `for direction in Direction: dr, dc = direction.value` — no re-listed (dr, dc) tuples, no duplication (Rule: no duplication at 2+ copies)
- **ConfigKey class (not Enum):** ConfigKey is a plain class with string class attributes to avoid `.value` noise at call sites (`data[ConfigKey.BOARD_SIZE]` reads cleanly)
- **_require_key + _require_int helpers in config.py:** Two internal helpers extract validation logic to avoid 8 repeated `if key not in data: raise` patterns
- **STAY check before other filters:** In get_legal_moves, STAY (candidate == pos) is detected first and appended directly without bounds/barrier checks — satisfies D-13 guarantee without a special-case flag

## Deviations from Plan

### Auto-added Missing Documentation

**1. [Rule 2 - Missing Critical Functionality] Created docs/phases/phase-1 triplet**
- **Found during:** Task 3 REFACTOR
- **Issue:** CLAUDE.md requires execute-phase to keep `docs/phases/phase-<N>/TODO.md` current. The plan-phase step did not create the triplet (docs/phases/phase-1/ did not exist).
- **Fix:** Created PRD.md, PLAN.md, TODO.md from _TEMPLATE/ skeletons; marked plan 01-00 and 01-01 as done in TODO.md
- **Files modified:** docs/phases/phase-1/PRD.md, docs/phases/phase-1/PLAN.md, docs/phases/phase-1/TODO.md
- **Commit:** 3e483af

### Ruff Auto-Fixes Applied

**2. [Rule 1 - Bug] Import ordering in test_config.py and test_board.py**
- **Found during:** Task 1 RED (ruff check ran before commit)
- **Issue:** `import pytest` was unused in test_board.py; import block ordering violated isort (I001); GameParams imported but unused in test_config.py
- **Fix:** Removed unused imports; ran `ruff check --fix`; removed bare `params =` assignments that were unused in apply_move tests
- **Files modified:** tests/unit/test_config.py, tests/unit/test_board.py
- No commit needed — fixed before Task 1 commit

## Coverage Results

```
Name                               Stmts   Miss  Cover
------------------------------------------------------
src/pursuit/constants.py              32      0   100%
src/pursuit/shared/board.py           25      0   100%
src/pursuit/shared/config.py          43      0   100%
src/pursuit/shared/state.py            9      0   100%
------------------------------------------------------
TOTAL (new modules)                   109     0   100%
Required: 85% — PASSED (99.09% overall)
```

## Known Stubs

None in the files created/modified by this plan. The following test stubs remain from Wave 0 for future plans:

| File | Stub count | Resolved by |
|------|-----------|------------|
| tests/unit/test_barrier.py | 5 | plan 01-02 |
| tests/unit/test_capture.py | 8 | plan 01-03 |
| tests/unit/test_sdk_engine.py | 3 | plan 01-04 |
| tests/integration/test_game_loop.py | 3 | plan 01-04 |

## Threat Surface Scan

No new network endpoints, auth paths, file system writes beyond the config read path (already present in Wave 0 as the conftest fixture). The config loader is the trust boundary (T-01-01-01 — filesystem -> config): fail-loud validation mitigated by KeyError/TypeError at load time. GameState immutability mitigated T-01-01-02 (Tampering via mutable state). No HIGH-severity threats introduced.

## Self-Check: PASSED

All files verified to exist and commits verified in git log.
