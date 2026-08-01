---
phase: 03-blind-strategy-module-rl-policy
plan: "05"
subsystem: strategy
tags: [state-encoding, json-persistence, atomic-write, windows, d-02, d-05, d-24]

# Dependency graph
requires:
  - phase: 03-00
    provides: StrategyParams.turn_bucket_fractions, GameParams.move_ceiling
  - phase: 03-02
    provides: Observation (own_cell/target_cell/blocked_mask/barriers_used/turn_index), Action IntEnum order
affects: [03-06, 03-08, "every later Phase-3 plan reading or writing a Q-table"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Crash-safe JSON write/read sequence (write temp in same dir -> flush+fsync -> rotate target to .prev -> os.replace with retry-with-backoff on PermissionError) factored into src/pursuit/shared/durable_write.py, the first module deliberately placed there for a Phase-3 consumer that training/ (03-08) will also import, since training/ must never be imported by src/"
    - "load_json_with_fallback falls back to .prev on BOTH a missing target (crash between rotate and final replace) and a corrupt one -- not just corruption alone"
    - "Per-key JSON schema keeps values and visit counts together ({table: {key: {values: {action: q}, visits: n}}}) so a save/load cycle can never desynchronize them"
    - "blocked_mask's bit order is deliberately pinned to Action's own IntEnum order (NORTH=bit0..WEST=bit3, STAY excluded) rather than inventing a second ordering -- reuses an already-frozen contract from 03-02"

key-files:
  created:
    - src/pursuit/strategy/encoding.py
    - src/pursuit/strategy/qtable.py
    - src/pursuit/shared/durable_write.py
    - tests/unit/strategy/test_encoding.py
    - tests/unit/strategy/test_qtable.py
    - tests/unit/strategy/test_qtable_durability.py
  modified:
    - docs/phases/phase-3/TODO.md
    - .planning/graphs/GRAPH_REPORT.md

key-decisions:
  - "encode_state/turn_bucket take StrategyParams AND GameParams as two explicit typed parameters (params, game_params) rather than one merged object -- matches the calling convention 03-04 already established for registry.build_brain(role, params, game_params), so 03-06's QLearningBrain sees one consistent pattern across the phase"
  - "blocked_mask(state, cell, agent, game_params) is a standalone utility, not called internally by encode_state -- Observation already carries a precomputed blocked_mask field (03-02's contract, D-05: no board in Observation), so encode_state only formats obs's existing fields plus the derived turn_bucket; blocked_mask exists for whichever caller populates Observation (03-06)"
  - "JSON schema is {version, table: {key: {values: {action_index_str: q}, visits: n}}} -- a nested per-key object rather than two parallel top-level dicts, so 'values and visit counts live together per key' is a structural JSON guarantee, not a convention two call sites could drift apart on"
  - "save()'s retries=3/backoff=0.1s are QTable-module-level structural constants (_SAVE_RETRIES/_SAVE_BACKOFF_SECONDS), not durable_write_json defaults -- durable_write_json's retries/backoff stay required keyword-only args per the plan's literal signature, so training/checkpoint.py (03-08) supplies its own values explicitly rather than inheriting QTable's choice implicitly"
  - "Split tests/unit/strategy/test_qtable.py into test_qtable.py (API + fail-loud load) and test_qtable_durability.py (crash/retry mechanics) -- see Deviations"

patterns-established:
  - "durable_write.py's crash-safety mechanics (write-temp -> fsync -> rotate-to-.prev -> retrying replace) is now the one write-sequence 03-08's training/checkpoint.py must reuse rather than reimplement, per the plan's own QUAL-02 instruction"

# Metrics
duration: ~25min
completed: 2026-08-01
---

# Phase 3 Plan 05: State Encoding + Q-Table JSON Persistence Summary

**Five-field canonical state-key string (own cell, believed target, agent-relative blocked-direction bitmask, barriers used, bucketed turn phase — never the barrier bitmap) plus a JSON `QTable` with per-key visit counts and a Windows-safe crash-recoverable save/load cycle shared with the future offline training harness.**

## Performance

- **Duration:** ~25 min
- **Tasks:** 2 completed
- **Files modified:** 6 created, 2 modified

## Accomplishments

- `src/pursuit/strategy/encoding.py`: `encode_state`/`decode_state` implement `docs/PRD_rl_strategy.md` §2 verbatim — the PRD's own worked example (`own=(2,3)`, `target=(5,5)`, `blocked_mask=9`, `barriers_used=6`, `turn=14`) encodes to exactly `"2,3|5,5|9|6|1"`, test-proven. `turn_bucket` derives both boundaries from `turn_bucket_fractions * move_ceiling`, no turn-index literal anywhere in the module (D-18). `blocked_mask` derives blocked-ness from `board.get_legal_moves` on a probed state, never a local barrier check (QUAL-02), with its bit order frozen to `Action`'s own order (NORTH=bit0…WEST=bit3) — proven via board-edge corner cases, including the PRD's own `{N,W} → 9` example, with no barriers needed to construct the test.
- Two dedicated tests prove D-05, the state-explosion guard the whole encoding exists to prevent: two states differing only in a barrier **far** from the agent's cell encode to the identical key (the bitmap genuinely never enters the key), while a barrier **adjacent** to the cell changes `blocked_mask` and therefore the key.
- `src/pursuit/strategy/qtable.py`: `QTable.get/set/bump_visit/visits/best_action/save/load` — visit counts are first-class and independent of Q-values (D-08), `best_action` ties break to the smallest action index deterministically, and `load()` is fail-loud on every malformed-input shape (non-object JSON, missing `version`, missing `table`, an entry missing `visits`, a non-integer or out-of-range action index, or a key `encoding.decode_state` cannot parse) — never a partially populated table.
- `src/pursuit/shared/durable_write.py`: the crash-safe write/read sequence (write to a same-directory temp file → `flush()` → `os.fsync(fd)` → rotate the existing target to `.prev` → `os.replace` retried with linear backoff on `PermissionError`) lives here specifically so `training/checkpoint.py` (03-08) can reuse it without `src/` ever importing `training/` (QUAL-02). `load_json_with_fallback` falls back to `.prev` on **both** a missing target (a crash landing between the rotate and the final replace leaves target briefly absent) and a corrupt one, logging a warning either way so one bad checkpoint costs one interval, never a whole overnight run (D-24).
- Both new persistence modules land at **100% test coverage**; full-repo coverage is 97.62% (262 tests, up from 235). `uv run ruff check .` and `bash scripts/check_line_limit.sh` are clean across the whole repository. Zero `pickle` import anywhere in the phase (only a docstring mention explaining why not).
- Graphify graph rebuilt (2471 nodes / 3802 edges / 189 communities); `.planning/graphs/GRAPH_REPORT.md` refreshed and committed.

## Task Commits

Each task was committed atomically:

1. **Task 1: Canonical state encoding** — `19172ea` (feat)
2. **Task 2: JSON Q-table with visit counts and atomic save** — `2dbdb83` (feat)

**Plan metadata:** (this commit, following SUMMARY/STATE update)

## Files Created/Modified

- `src/pursuit/strategy/encoding.py` — `encode_state`, `decode_state`, `turn_bucket`, `blocked_mask`
- `src/pursuit/strategy/qtable.py` — `QTable` class + fail-loud load validation helpers
- `src/pursuit/shared/durable_write.py` — `durable_write_json`, `load_json_with_fallback`
- `tests/unit/strategy/test_encoding.py` — 10 tests (worked example, round-trip, D-05 distant/adjacent barrier, bit-order pin, turn-bucket boundary pin, malformed-key cases)
- `tests/unit/strategy/test_qtable.py` — 15 tests (API, save/load round-trip, fail-loud load cases)
- `tests/unit/strategy/test_qtable_durability.py` — 4 tests (retries-exhausted, crash-before-rotate, corrupt-falls-back-to-.prev, PermissionError-retried-and-succeeds)
- `docs/phases/phase-3/TODO.md` — row 03-05 marked ☑
- `.planning/graphs/GRAPH_REPORT.md` — refreshed after this plan's new code

## Decisions Made Autonomously

See `key-decisions` in frontmatter. In brief, since the user was unavailable for this unattended run:

- `encode_state`/`turn_bucket` take `(obs, params: StrategyParams, game_params: GameParams)` as two explicit typed parameters, matching the `(role, params, game_params)` convention 03-04 already fixed for `registry.build_brain` — chosen over inventing a merged params object, so 03-06 sees one consistent calling pattern across the whole phase.
- The QTable JSON schema nests `values` and `visits` inside one per-key object (`{table: {key: {values: {...}, visits: n}}}`) rather than two parallel top-level dicts, making "values and visits live together" a structural JSON guarantee rather than a convention two code paths could let drift.
- `QTable.save()`'s `retries=3`/`backoff=0.1s` are module-level structural constants in `qtable.py` (same exemption category as `prior.py`'s `_MASS_TOLERANCE` and `pathfind.py`'s `UNREACHABLE` sentinel — engineering/mechanical constants, not game values or RL hyperparameters) rather than defaults baked into `durable_write_json` itself, since the plan's own literal signature (`durable_write_json(path, payload, *, retries, backoff)`) has no defaults — 03-08's `training/checkpoint.py` supplies its own values explicitly.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `tests/unit/strategy/test_qtable.py` split into two files to satisfy the hard 150-line gate**
- **Found during:** Task 2, after writing the full set of tests the plan's own `<verify>` list requires (unseen-defaults, round-trip, save→load fidelity, five distinct fail-loud-load cases, and four separate crash/retry-mechanics cases for `durable_write.py`).
- **Issue:** The single file reached 152 code lines (limit 150, blanks/comments excluded) — `bash scripts/check_line_limit.sh` failed.
- **Fix:** Split along an existing conceptual seam: `test_qtable.py` keeps the `QTable` API and fail-loud `load()` validation tests (15 tests); `test_qtable_durability.py` keeps the four tests that specifically exercise `durable_write.py`'s crash-safety and retry mechanics through `QTable.save()`/`load()` (4 tests). No test was weakened, removed, or compressed — CLAUDE.md's explicit instruction is "split files, never compress code to fit."
- **Files modified:** `tests/unit/strategy/test_qtable.py` (trimmed), `tests/unit/strategy/test_qtable_durability.py` (new).
- **Verification:** `bash scripts/check_line_limit.sh` → clean; `uv run pytest tests/unit/strategy/test_qtable.py tests/unit/strategy/test_qtable_durability.py -q` → 19 passed; full repo suite still 262 passed, coverage 97.62%.
- **Committed in:** `2dbdb83` (Task 2 commit — the split happened before the commit, so both files landed as the intended shape from the start).

---

**Total deviations:** 1 auto-fixed (Rule 3 — a blocking issue against this repo's hard-enforced, machine-checked 150-line pre-commit gate).
**Impact on plan:** No scope or behavior change — one plan-declared test file became two, both still exactly matching the plan's own `files_modified`-adjacent intent (the plan named one file; the split is a file-organization deviation, not a scope deviation, and every test the plan's `<verify>` section demands still exists and passes).

## Issues Encountered

None beyond the line-limit split above. No authentication gates, no architectural questions, no blockers.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- 03-06's `QLearningBrain` can now call `encoding.encode_state`/`turn_bucket`/`blocked_mask` to build its Q-key and consume `qtable.QTable.get/set/bump_visit/visits/best_action` directly — the STRAT-02 fallback trigger (`visits(key) < min_visits`) has real, independently-tracked visit counts to read, not a value list to infer them from.
- 03-08's `training/checkpoint.py` can import `pursuit.shared.durable_write.durable_write_json`/`load_json_with_fallback` directly rather than reimplementing the Windows-safe atomic-write sequence — the one place `src/` and `training/` share code without `training/` ever being imported by `src/`.
- No blockers. `QTable`/`encoding.py` do not yet know about `min_visits`-driven fallback selection or ε-greedy action choice — that logic is explicitly 03-06's, per this plan's own objective ("No policy logic lives here").

---
*Phase: 03-blind-strategy-module-rl-policy*
*Completed: 2026-08-01*

## Self-Check: PASSED

All 9 claimed files confirmed present on disk (`src/pursuit/strategy/{encoding,qtable}.py`,
`src/pursuit/shared/durable_write.py`, `tests/unit/strategy/{test_encoding,test_qtable,
test_qtable_durability}.py`, this SUMMARY, `docs/phases/phase-3/TODO.md`,
`.planning/graphs/GRAPH_REPORT.md`).
Both task commit hashes (`19172ea`, `2dbdb83`) confirmed present in `git log --oneline --all`.
