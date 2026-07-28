---
phase: 02-fastmcp-infrastructure
plan: "01"
subsystem: infra
tags: [config-loader, fail-loud-validation, network-config, qual-02, dataclass]

# Dependency graph
requires:
  - phase: 02-fastmcp-infrastructure (02-00)
    provides: "config/{police,thief}/network.json, NetworkConfigKey constants, network_params conftest fixture"
provides:
  - "src/pursuit/shared/loader_helpers.py — require_key/require_int/require_str, the single shared fail-loud validator for every JSON loader in the project"
  - "src/pursuit/shared/network_config.py — NetworkParams frozen dataclass + load_network_config(path) -> NetworkParams"
  - "config.py refactored onto the shared helpers, behaviour-preserving"
affects: [02-06, 02-07, 02-04, 02-09]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "keyword-only `source` parameter on fail-loud validators, so one implementation serves every config file's error messages"
    - "fresh-object-per-call loader (no module-level cache) as the mechanism that guarantees NET-02 (no shared runtime state across processes)"
    - "D-16 env override applied AFTER file validation, so a malformed env var still fails loud (ValueError) rather than silently reverting to the file value"

key-files:
  created:
    - src/pursuit/shared/loader_helpers.py
    - src/pursuit/shared/network_config.py
    - tests/unit/test_loader_helpers.py
  modified:
    - src/pursuit/shared/config.py
    - tests/unit/test_network_config.py
    - tests/unit/test_config.py

key-decisions:
  - "Reused 02-00's existing NetworkConfigKey.ENV_HOST/ENV_PORT/ENV_OPPONENT_URL instead of adding a second NetworkEnvVar class (QUAL-02) — plan's own instruction to reuse an equivalently-named class if 02-00 already added one"
  - "network.json already carried watchdog_poll_seconds=1 from 02-00, so Step D (add the D-18 field) was a no-op — no file change needed"
  - "GAME_PARAMS_SOURCE = \"game_params.json\" added as a module-level constant in config.py so the extraction is a pure move with no behaviour change"

patterns-established:
  - "Pattern: shared/loader_helpers.py as the one fail-loud JSON validator every future config loader in the project must import, never re-implement"

# Metrics
duration: 18min
completed: 2026-07-28
---

# Phase 2 Plan 01: Network Config Loader + Loader-Helper Extraction Summary

**Fail-loud `NetworkParams` loader for `network.json` with D-16 environment overrides, built on a `loader_helpers.py` extraction that pays off the `game_params.json`/`network.json` duplication debt in the same plan.**

## Performance

- **Duration:** ~18 min
- **Completed:** 2026-07-28
- **Tasks:** 3/3 completed (RED / GREEN / REFACTOR — no refactor changes were needed, all gates passed on the first GREEN pass)
- **Files modified:** 6 (3 created: loader_helpers.py, network_config.py, test_loader_helpers.py; 3 modified: config.py, test_network_config.py, test_config.py)

## Accomplishments
- `src/pursuit/shared/loader_helpers.py` — `require_key`/`require_int`/`require_str`, each taking a keyword-only `source` naming the file in its error message. Extracted verbatim from `config.py`'s private `_require_key`/`_require_int` pair (a pure move — no new validation semantics), plus a new `require_str`.
- `src/pursuit/shared/config.py` refactored to import and call the shared helpers; all five pre-existing `test_config.py` tests plus the new QUAL-02 guard test pass unchanged — the extraction is behaviour-preserving.
- `src/pursuit/shared/network_config.py` — frozen `NetworkParams` (host, port, opponent_url, response_timeout, watchdog_threshold, retry_count, backoff_seconds, watchdog_poll_seconds) + `load_network_config(path) -> NetworkParams`. Every field validated at load time; missing key -> `KeyError`, wrong type -> `TypeError`; zero numeric literals in the module (AST-verified).
- D-16 environment overrides (`PURSUIT_HOST`/`PURSUIT_PORT`/`PURSUIT_OPPONENT_URL`) applied after file validation; a non-integer `PURSUIT_PORT` raises `ValueError` rather than silently falling back.
- NET-02 verified two ways: a named test (`test_agents_get_independent_objects`) and a standalone identity check — `load_network_config` returns a fresh object every call, never a shared/cached instance.
- Full `tests/unit/` suite: 60 passed, 48 skipped, 0 regressions. Coverage of both new modules: 100% (loader_helpers.py 14/14, network_config.py 43/43 statements); project total 99.21%, well above the 85% gate.

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: loader-helper, network-config and no-duplication tests** - `4fc5e7b` (test)
2. **Task 2 GREEN: extract loader_helpers, re-point config.py, add network_config.py** - `ff87d45` (feat)
3. **Task 3 REFACTOR: full suite, numeric/secret audits, coverage** - no additional commit; all quality gates (tests, ruff, line-limit, coverage, AST numeric scan, QUAL-02/QUAL-12 grep audits) passed on the first attempt after Task 2, so no refactor changes were needed. Verified against `ff87d45`.

**Plan metadata:** committed alongside this SUMMARY (see final commit below)

## Files Created/Modified
- `src/pursuit/shared/loader_helpers.py` - `require_key`/`require_int`/`require_str`, the single shared fail-loud validator (QUAL-02)
- `src/pursuit/shared/network_config.py` - `NetworkParams` + `load_network_config`, NET-01/NET-02/QUAL-11 compliant
- `src/pursuit/shared/config.py` - private `_require_key`/`_require_int` removed, now imports `loader_helpers`; `GAME_PARAMS_SOURCE` constant added
- `tests/unit/test_loader_helpers.py` - new file, full happy-path + error-path coverage for all three helpers
- `tests/unit/test_network_config.py` - replaces the 02-00 skip stub with 12 real assertions (load, types, frozen, NET-02 independence, fixture cross-check, missing/wrong-type/missing-watchdog-poll errors, env overrides x3)
- `tests/unit/test_config.py` - one added QUAL-02 no-duplication regression guard (`test_config_uses_shared_loader_helpers`)

## Decisions Made
- Reused 02-00's `NetworkConfigKey.ENV_HOST`/`ENV_PORT`/`ENV_OPPONENT_URL` rather than introducing a new `NetworkEnvVar` class — the plan explicitly instructed reuse if 02-00 already added an equivalently-named class, and the three names match `.env-example` exactly.
- `config/{police,thief}/network.json` already carried `watchdog_poll_seconds: 1` from 02-00, so Task 2 Step D required no file edit.
- Kept `version = str(require_key(...))` coercion in `config.py` unchanged, per the plan's explicit "behaviour-preserving" instruction (not switched to `require_str`).

## Deviations from Plan

None requiring a fix. Two plan-anticipated conditionals both resolved to "no-op, already satisfied by 02-00":
1. **[Reuse, not a new class]** The plan's Step C offered a `NetworkEnvVar` class but explicitly said to reuse an equivalent if 02-00 had already added one — 02-00 had (`NetworkConfigKey.ENV_*`), so no new class was created. No `src/pursuit/constants.py` edit was needed for this plan.
2. **[Already present]** The plan's Step D asked to add `watchdog_poll_seconds` to both `network.json` files "if absent" — 02-00 already added it (D-18), so no config file edit was needed.

Both are documented here per the plan's own instruction to record them, not silently treated as no-ops.

## Issues Encountered

None. Ruff's import-sort auto-fix (`ruff check --fix`) was applied once to the two new test files to satisfy the repo's isort ordering (grouping `pursuit.*` imports with third-party rather than as a separate first-party block) — a formatting-only change, not a logic change.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `NetworkParams` is ready for 02-06 (`PeerRuntime` reads `host`/`port`/`opponent_url`/`response_timeout`), 02-07 (deadline tracker reads `response_timeout`/`retry_count`/`backoff_seconds`), and 02-04/02-09 (watchdog reads `watchdog_threshold`/`watchdog_poll_seconds`).
- `require_key`/`require_int`/`require_str` in `loader_helpers.py` are the standing shared validator — any future config loader in the project must import these, not re-implement them.
- No blockers carried into the rest of Wave 1 (02-02, 02-03, 02-04, 02-05 remain zero-file-overlap with this plan's touches).
- `uv run pytest tests/unit/ -x -q` baseline after this plan: **60 passed, 48 skipped**, 0 collection errors, 0 regressions.

---
*Phase: 02-fastmcp-infrastructure*
*Completed: 2026-07-28*

## Self-Check: PASSED

All 6 claimed files verified present on disk (src/pursuit/shared/loader_helpers.py,
src/pursuit/shared/network_config.py, src/pursuit/shared/config.py,
tests/unit/test_loader_helpers.py, tests/unit/test_network_config.py,
tests/unit/test_config.py). Both task commit hashes (4fc5e7b, ff87d45) verified
present in `git log --oneline --all`.
