---
phase: 02-fastmcp-infrastructure
plan: "00"
subsystem: infra
tags: [fastmcp, pytest-asyncio, uv, network-config, constants, test-stubs]

# Dependency graph
requires:
  - phase: 01-base-logic
    provides: "pursuit package skeleton, ConfigKey convention, tests/conftest.py fixtures, check_line_limit.sh gate"
provides:
  - "fastmcp 3.4.5 + pytest-asyncio 1.4.0 as locked uv dependencies"
  - "asyncio_mode = \"auto\" enabling bare async def test_... in Waves 2 and 5"
  - "config/{police,thief}/network.json — the single source of every Phase-2 network number"
  - "NetworkConfigKey structural constants in src/pursuit/constants.py"
  - "src/pursuit/network/ empty package root for Waves 1-5"
  - ".env-example PURSUIT_* override placeholders"
  - "tests/conftest.py police_network_config + network_params fixtures (lazy import)"
  - "13 named, skipped test stub files — one per Phase-2 module plan 02-01 through 02-10"
affects: [02-01, 02-02, 02-03, 02-04, 02-05, 02-06, 02-07, 02-08, 02-09, 02-10]

# Tech tracking
tech-stack:
  added: ["fastmcp==3.4.5", "pytest-asyncio==1.4.0"]
  patterns:
    - "network.json per-agent config: identical schema, only port + opponent_url differ (D-04)"
    - "lazy import inside a fixture body to keep collection green before the module it needs exists"
    - "stub test convention: pytest.skip(\"stub — implemented in plan 02-XX\") in the body, never @pytest.mark.xfail"

key-files:
  created:
    - config/police/network.json
    - config/thief/network.json
    - src/pursuit/network/__init__.py
    - tests/unit/test_network_config.py
    - tests/unit/test_envelope.py
    - tests/unit/test_config_hash.py
    - tests/unit/test_state_machine.py
    - tests/unit/test_event_log.py
    - tests/unit/test_watchdog.py
    - tests/unit/test_tools.py
    - tests/unit/test_peer_runtime.py
    - tests/unit/test_deadline.py
    - tests/unit/test_handshake.py
    - tests/unit/test_orchestrator.py
    - tests/integration/test_peer_roundtrip.py
    - tests/integration/test_turn_lifecycle.py
  modified:
    - pyproject.toml
    - uv.lock
    - .env-example
    - src/pursuit/constants.py
    - tests/conftest.py

key-decisions:
  - "fastmcp resolved to exactly 3.4.5, matching RESEARCH.md's verified API surface — no divergence to flag for Wave 2"
  - "pytest-asyncio resolved to 1.4.0 with zero conflict against pytest>=9.1.1 — no downgrade needed"
  - "NetworkConfigKey does not redeclare VERSION; reuses existing ConfigKey.VERSION (QUAL-02)"

patterns-established:
  - "Pattern: per-agent JSON config with byte-identical schema, only endpoint fields differ — reusable for any future per-side config"
  - "Pattern: fixture-body lazy import to let a stub-first test suite collect before its target module exists"

# Metrics
duration: 12min
completed: 2026-07-28
---

# Phase 2 Plan 00: FastMCP Foundation Summary

**Installed fastmcp 3.4.5 + pytest-asyncio as locked uv dependencies, created the per-agent `network.json` config (D-04/D-16/D-17/D-18) as the single source of every Phase-2 network number, added `NetworkConfigKey` structural constants, and dropped 13 named-and-skipped test stubs so Waves 1-5 start with zero collection risk.**

## Performance

- **Duration:** ~12 min
- **Completed:** 2026-07-28
- **Tasks:** 3/3 completed
- **Files modified:** 20 (2 created config files, 1 created package root, 13 created test stubs, 4 modified: pyproject.toml, uv.lock, .env-example, constants.py, conftest.py)

## Accomplishments
- `fastmcp` (3.4.5) and `pytest-asyncio` (1.4.0) installed via `uv add` / `uv add --dev` only — no `pip`, no `requirements.txt`; `uv.lock` regenerated
- `asyncio_mode = "auto"` added to `[tool.pytest.ini_options]` without touching `testpaths`/`addopts`
- `config/police/network.json` and `config/thief/network.json` created, differing in exactly `port` + `opponent_url`; every other number traced to PARAMETERS.md Table 19 (30/60/3/5) or to D-16/D-18 engineering defaults (8001/8002/1) — `config/{police,thief}/game_params.json` verified byte-identical and untouched
- `NetworkConfigKey` appended to `src/pursuit/constants.py` — structural strings only, no numeric literal, no duplicate of `ConfigKey.VERSION`
- `.env-example` gained three `PURSUIT_*` placeholder lines, no real port or secret
- `tests/conftest.py` gained `police_network_config` and `network_params` fixtures, with the `pursuit.shared.network_config` import kept inside the `network_params` body (module doesn't exist until 02-01)
- 13 test stub files created (11 unit + 2 integration) with all named test functions from the plan's Task 3 spec, each skipping via `pytest.skip("stub — implemented in plan 02-XX")`

## Task Commits

Each task was committed atomically:

1. **Task 1: Dependencies, async test mode, and the network package root** - `f382d3b` (chore)
2. **Task 2: Per-agent network.json, NetworkConfigKey, and .env-example overrides** - `0a9aec6` (feat)
3. **Task 3: conftest network fixtures + all 13 Phase-2 test stubs** - `670310a` (test)

**Plan metadata:** committed alongside this SUMMARY (see final commit below)

## Files Created/Modified
- `pyproject.toml` - fastmcp dependency, asyncio_mode = "auto"
- `uv.lock` - regenerated lock covering fastmcp + pytest-asyncio and their transitive trees
- `src/pursuit/network/__init__.py` - empty Phase-2 network package root (docstring only, zero executable statements)
- `config/police/network.json` - police endpoint (8001) + resilience parameters
- `config/thief/network.json` - thief endpoint (8002) + resilience parameters, otherwise identical
- `src/pursuit/constants.py` - `NetworkConfigKey` class (8 field keys + 3 ENV_* names)
- `.env-example` - `PURSUIT_HOST`/`PURSUIT_PORT`/`PURSUIT_OPPONENT_URL` placeholder overrides
- `tests/conftest.py` - `police_network_config` + `network_params` fixtures (lazy import)
- `tests/unit/test_network_config.py` ... `tests/unit/test_orchestrator.py`, `tests/integration/test_peer_roundtrip.py`, `tests/integration/test_turn_lifecycle.py` - 13 named, skipped stubs for plans 02-01 through 02-10

## Decisions Made
- fastmcp resolved to exactly **3.4.5** — matches RESEARCH.md's verified version; no divergence to record for Wave 2
- pytest-asyncio resolved to **1.4.0** with no resolution conflict against the pinned `pytest>=9.1.1` — no downgrade was needed, so the STOP-and-report branch in Task 1 did not trigger
- Confirmed `config/{police,thief}/game_params.json` remain byte-for-byte identical after this plan (NET-09 precondition intact)

## Deviations from Plan

None — plan executed exactly as written. All three tasks completed with no auto-fixes, no architectural questions, and no authentication gates.

**Observation (not a deviation, no code change made):** The plan's own `<verification>` block, item 11, states the literal command `grep -rn 'PURSUIT_' src/ config/` "must return nothing," but its own parenthetical in the same line says the env-var names "live only in `constants.py` as `ENV_*` values" — and `constants.py` sits under `src/`. Running the grep as literally written does return 3 matches, all three in `src/pursuit/constants.py` (the `ENV_HOST`/`ENV_PORT`/`ENV_OPPONENT_URL` string values), exactly where Task 2's own action block places them. Isolating `config/` alone (`grep -rn 'PURSUIT_' config/`) returns nothing, which is the actually-meaningful invariant (no env-var name leaks into JSON config). Recorded here for the plan-checker/verifier rather than silently "fixed" — the code matches the plan's Task 2 spec and success criteria exactly; only the verification item's own wording is internally inconsistent.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required. `fastmcp`/`pytest-asyncio` installed automatically via `uv`.

## Next Phase Readiness

- Wave 1 (02-01 loader, 02-02 envelope+digest, 02-03 state machine, 02-04 event-log+watchdog) can start immediately: `network.json`, `NetworkConfigKey`, and the lazy `network_params` fixture are all in place.
- Waves 2-5 (02-05 through 02-10) have their named stub files ready to convert to real tests without any intra-wave file-creation collision.
- `uv run pytest -q` baseline for 02-01 onward: **43 passed, 62 skipped**, 0 collection errors.
- Coverage unaffected: 99.01% (Phase-1 level), well above the 85% gate — this plan added zero executable source statements.
- No blockers carried into Wave 1.

---
*Phase: 02-fastmcp-infrastructure*
*Completed: 2026-07-28*

## Self-Check: PASSED

All 12 claimed files verified present on disk (config/police/network.json,
config/thief/network.json, src/pursuit/network/__init__.py, src/pursuit/constants.py,
.env-example, tests/conftest.py, tests/unit/test_network_config.py,
tests/unit/test_orchestrator.py, tests/integration/test_peer_roundtrip.py,
tests/integration/test_turn_lifecycle.py, pyproject.toml, uv.lock). All 3 task commit
hashes (f382d3b, 0a9aec6, 670310a) verified present in `git log --oneline --all`.
