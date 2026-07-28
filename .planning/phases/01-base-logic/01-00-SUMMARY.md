---
phase: 01-base-logic
plan: "00"
subsystem: infra
tags: [uv, ruff, pytest, pytest-cov, python, config]

# Dependency graph
requires: []
provides:
  - uv project with pyproject.toml (ruff config + coverage fail_under=85)
  - uv.lock locked dependency tree
  - src/pursuit package layout (sdk, services, shared sub-packages)
  - src/pursuit/shared/version.py with VERSION="1.00"
  - config/police/game_params.json and config/thief/game_params.json (byte-for-byte identical, all values from PARAMETERS.md)
  - config/police/role.json and config/thief/role.json (only legitimate difference between sides)
  - tests/conftest.py with default_params and start_state fixtures
  - 7 stub test files covering BASE-01..BASE-08, QUAL-01, §10.4 gate criteria (all skipped, pytest exits 0)
affects:
  - 01-01-board-movement (imports pursuit.constants, uses conftest fixtures)
  - 01-02-barrier-quota (uses conftest fixtures, extends test_barrier.py)
  - 01-03-capture (uses conftest fixtures, extends test_capture.py)
  - 01-04-sdk-facade (fills test_sdk_engine.py stubs)

# Tech tracking
tech-stack:
  added:
    - uv 0.11.19 (package manager and virtualenv)
    - pytest 9.1.1
    - pytest-cov 7.1.0
    - ruff 0.16.0
  patterns:
    - All game numerics in game_params.json only — zero hardcoded values in src/
    - uv-only workflow (uv add, uv run, uv sync — never pip/python directly)
    - src/pursuit layout with sdk/services/shared sub-packages (QUAL-01 SDK layer)
    - Stub test files with pytest.skip() bodies — Wave 0 green suite for TDD bootstrapping
    - Fixture chain: default_params (session) → start_state (function), no hardcoded numbers

key-files:
  created:
    - pyproject.toml
    - uv.lock
    - .env-example
    - src/pursuit/__init__.py
    - src/pursuit/constants.py
    - src/pursuit/sdk/__init__.py
    - src/pursuit/services/__init__.py
    - src/pursuit/shared/__init__.py
    - src/pursuit/shared/version.py
    - config/police/game_params.json
    - config/thief/game_params.json
    - config/police/role.json
    - config/thief/role.json
    - tests/__init__.py
    - tests/unit/__init__.py
    - tests/integration/__init__.py
    - tests/conftest.py
    - tests/unit/test_config.py
    - tests/unit/test_board.py
    - tests/unit/test_barrier.py
    - tests/unit/test_capture.py
    - tests/unit/test_sdk_engine.py
    - tests/integration/test_game_loop.py
  modified: []

key-decisions:
  - "D-01: ruff config line-length=100, py310, select=E,F,W,I,N,UP,B,C4,SIM, ignore=E501"
  - "D-02: src/pursuit layout with sdk/services/shared; version.py=1.00"
  - "D-04: package name pursuit (neutral, usable by both sides in Phase 8)"
  - "D-05: all game numerics in game_params.json, zero in src/ code"
  - "D-06: game_params.json duplicated byte-for-byte in config/police/ and config/thief/"

patterns-established:
  - "Wave-0 stub pattern: pytest.skip() inside each test body; suite stays green while stubs exist"
  - "Fixture chain: default_params loads JSON, start_state derives from default_params with no literals"
  - "Config separation: game_params.json is the numeric trust root; constants.py is structural-only"

requirements-completed:
  - QUAL-01
  - QUAL-06

# Metrics
duration: 9min
completed: 2026-07-28
---

# Phase 01 Plan 00: Project Scaffold Summary

**uv project skeleton with ruff/coverage config, src/pursuit package layout, dual-side game_params.json (all values from PARAMETERS.md), and 7 skipped stub test files providing a green Wave-0 pytest baseline**

## Performance

- **Duration:** ~9 min
- **Started:** 2026-07-28T11:05:13Z
- **Completed:** 2026-07-28T11:13:52Z
- **Tasks:** 3
- **Files created:** 23

## Accomplishments

- uv project configured with ruff lint (E,F,W,I,N,UP,B,C4,SIM), coverage fail_under=85, pytest testpaths
- Canonical game_params.json written identically to both config/police/ and config/thief/ with all values sourced strictly from docs/PARAMETERS.md Tables 13, 15, 17 — no invented numbers
- 7 stub test files (28 tests total) all skipped; `uv run pytest -q` exits 0; `ruff check .` exits 0; `bash scripts/check_line_limit.sh` passes all new files

## Task Commits

Each task was committed atomically:

1. **Task 1: uv project init + pyproject.toml + directory layout** — `bdb9fd7` (chore)
2. **Task 2: Config files — game_params.json + role.json (both sides)** — `8731a0f` (feat)
3. **Task 3: Test infrastructure — conftest.py + unit/integration stubs** — `4def96f` (test)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `pyproject.toml` — uv project definition, ruff config, coverage config, pytest config
- `uv.lock` — locked dependency tree (pytest, pytest-cov, ruff + transitive)
- `.env-example` — dummy placeholder values only (SOME_API_KEY, SOME_SECRET, SOME_TOKEN)
- `src/pursuit/__init__.py` — package root (docstring only)
- `src/pursuit/constants.py` — module docstring + comment; awaits plan 01-01 for enums
- `src/pursuit/sdk/__init__.py` — SDK sub-package (docstring only)
- `src/pursuit/services/__init__.py` — services sub-package (docstring only)
- `src/pursuit/shared/__init__.py` — shared library sub-package (docstring only)
- `src/pursuit/shared/version.py` — `VERSION = "1.00"` (string sentinel)
- `config/police/game_params.json` — trust root for numeric parameters
- `config/thief/game_params.json` — byte-for-byte identical copy
- `config/police/role.json` — `{"role": "police"}`
- `config/thief/role.json` — `{"role": "thief"}`
- `tests/conftest.py` — default_params and start_state fixtures (no hardcoded numbers)
- `tests/unit/test_config.py` — 4 stubs for BASE-08
- `tests/unit/test_board.py` — 5 stubs for BASE-01
- `tests/unit/test_barrier.py` — 5 stubs for BASE-02
- `tests/unit/test_capture.py` — 8 stubs for BASE-03..BASE-07
- `tests/unit/test_sdk_engine.py` — 3 stubs for QUAL-01
- `tests/integration/test_game_loop.py` — 3 stubs for §10.4 gate criteria
- `tests/__init__.py`, `tests/unit/__init__.py`, `tests/integration/__init__.py` — empty package markers

## Decisions Made

- Package name is `pursuit` (D-04): short, neutral, usable by both cop and thief repos at Phase 8 split
- All numeric game values live in `game_params.json` only (D-05): required by Appendix F §2 rule 1 (config file attachment + cryptographic lock in Phase 6)
- `game_params.json` duplicated byte-for-byte in both config dirs (D-06): Phase 2 NET-09 byte-for-byte identity check needs two files to compare
- Stub tests use `pytest.skip()` inside body (not `@pytest.mark.xfail`): simpler green-suite guarantee while Wave 1 fills in implementations

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## Known Stubs

The following test files contain intentional stubs (all test bodies call `pytest.skip()`):

| File | Stub count | Resolved by |
|------|-----------|------------|
| tests/unit/test_config.py | 4 | plan 01-01 |
| tests/unit/test_board.py | 5 | plan 01-01 |
| tests/unit/test_barrier.py | 5 | plan 01-02 |
| tests/unit/test_capture.py | 8 | plan 01-03 |
| tests/unit/test_sdk_engine.py | 3 | plan 01-04 |
| tests/integration/test_game_loop.py | 3 | plan 01-04 |

These stubs are intentional: they declare the test function names so Wave 1 plans can implement bodies without structural conflict. They do not prevent this plan's goal (Wave-0 green baseline) from being achieved.

## Threat Surface Scan

No new network endpoints, auth paths, or schema changes. Only filesystem reads (config/police/game_params.json via conftest). T-01-00-01 (byte-for-byte config identity) mitigated by verified `diff` producing no output. T-01-00-02 (.env-example) accepted — only dummy values committed.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Wave 0 complete: uv project, config, version sentinel, green stub suite all in place
- Plan 01-01 (board + movement) can now import `pursuit` and write real implementations against the test stubs in `tests/unit/test_board.py` and `tests/unit/test_config.py`
- `config/police/game_params.json` is the numeric trust root for all subsequent plans

## Self-Check: PASSED

All 24 expected files found on disk. All 3 task commits verified in git log (bdb9fd7, 8731a0f, 4def96f).

---
*Phase: 01-base-logic*
*Completed: 2026-07-28*
