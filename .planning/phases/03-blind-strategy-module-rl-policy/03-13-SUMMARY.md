---
phase: 03-blind-strategy-module-rl-policy
plan: "13"
subsystem: strategy-config
tags: [q-learning, state-encoding, config-schema, strategy-json, run-2]

# Dependency graph
requires:
  - phase: 03-blind-strategy-module-rl-policy (03-11, 03-12)
    provides: graph primitives package and the thief safety filter, both landed
      earlier in wave 1 with no coupling to this plan's files
provides:
  - "encode_state key field 5 is exact turns_remaining (move_ceiling - turn_index,
    clamped at 0), turn_bucket deleted entirely (D-06 superseded)"
  - "The complete run-2 config surface declared once in StrategyKey/TrainingKey +
    strategy_schema.py + both config/{police,thief}/strategy.json files -- 15 new
    fields, 1 removed (turn_bucket_fractions)"
  - "QTable.load() rejects any payload whose schema version differs from the
    current one (bumped 1 -> 2), so a stale run-1-format artifact fails loud
    instead of loading silently against a wrong time field"
affects: [03-14, 03-15, 03-16, 03-17, 03-18, 03-19, 03-20, 03-21, 03-23]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "150-line-gate split by extracting a dataclass + its schema table into a
      sibling module (strategy_schema.py), re-exported via __all__ so ~20
      existing import sites need zero changes"
    - "Config schema rows carry a group NAME (string) instead of a resolved
      dict, so the dataclass/schema module has no load-time dependency on the
      loader's own local variables"

key-files:
  created:
    - src/pursuit/shared/strategy_schema.py
    - tests/unit/strategy/test_strategy_config_run2.py
  modified:
    - src/pursuit/strategy/encoding.py
    - src/pursuit/config_keys.py
    - src/pursuit/shared/strategy_config.py
    - src/pursuit/strategy/qtable.py
    - config/police/strategy.json
    - config/thief/strategy.json
    - tests/unit/strategy/test_encoding.py
    - tests/unit/strategy/test_strategy_config.py
    - tests/unit/strategy/test_qtable.py
    - tests/unit/strategy/test_qtable_durability.py

key-decisions:
  - "search_depth_cap seeded at 5 (MEASURED, D-26's own real-engine figure with a
    useful eval), never ALG-COMPARISON's unverified 11-12 plies"
  - "min_distinct_starts=200, terminal_spread_min=0.1, terminal_spread_ratio_max=3.0,
    floor_episode_fraction_max=0.15 seeded verbatim from
    docs/research/TRAINING-METHODOLOGY.md SF.3 (SOURCED)"
  - "pfsp_exponent=1.0 follows f_var(x)=x(1-x) (AlphaStar); flagged in this SUMMARY,
    not just the research doc, that the exact AlphaStar exponent itself reaches us
    through secondary sources only (TRAINING-METHODOLOGY.md 'No source found' #6)"
  - "weak_opponent_floor=2 derived from SF.3's literal '>=1 scripted weak + 1
    random-walk' requirement (SOURCED principle, engineering-default count)"
  - "barrier_candidate_min_degree=3 and the four barrier_weight_* values
    (cycle_rank=4.0 > component_size=3.0 > territory=2.0 > distance=1.0) are
    ENGINEERING DEFAULTS with no literature source for their magnitudes -- only
    the strict ordering is fixed here; 03-17 sets the real filter threshold and
    03-21 sets the real magnitudes"
  - "learner_rule seeded per role (police=q_learning, thief=expected_sarsa),
    anticipating the outline's stated direction for 03-20 (on-policy Expected
    SARSA for the thief per S&B SS11.3's deadly-triad argument); 03-20 owns the
    actual semantics and may revise the string"
  - "feature_scale_divisor=1.0 (identity) -- no source, 03-16's own feature
    definitions already scale to ~[0,1] via BFS distance ratios"
  - "docs/PRD_rl_strategy.md Sec2 was NOT updated to match the new key format --
    it is 03-22's file (D-27 deviation-defence deliverable), out of this plan's
    file-ownership scope. The affected test was adapted with an explicit note
    rather than silently left inconsistent"
  - "training/harness.py's stale 'turn_bucket_fractions' docstring mention was
    left untouched -- that file is 03-14's this same wave per outline SS7's
    file-ownership table (sequential by wave, never parallel edits)"

patterns-established:
  - "Config schema split: dataclass + validator-schema table in one module,
    loader logic in another, group dicts resolved and looked up by name string
    at load time rather than baked into the schema table"

# Metrics
duration: ~45min
completed: 2026-08-04
---

# Phase 03 Plan 13: State key `turns_remaining` + the whole run-2 config surface Summary

**Q-table key field 5 becomes exact `turns_remaining` (turn_bucket deleted, not joined); every
numeric knob plans 03-14..03-25 need is declared once across `StrategyKey`/`TrainingKey` +
`strategy_schema.py` + both role `strategy.json` files; a run-1-format Q-table now fails loud
on load instead of silently playing against a wrong time field.**

## Performance

- **Duration:** ~45 min (start time not captured via `date` at session start; estimated from
  session length — see Issues Encountered)
- **Completed:** 2026-08-04T10:20:33Z
- **Tasks:** 3 (all `type="auto"`, no checkpoints)
- **Files modified:** 10 modified, 2 created

## Accomplishments

- `encode_state`'s key field 5 is now exact `turns_remaining = move_ceiling - turn_index`
  (clamped at 0), replacing the deleted `turn_bucket` phase-bucketer entirely — D-06 superseded,
  citing Puterman 1994 ch.4 and Pardo et al. ICML 2018. `encode_state`'s 3-argument signature is
  unchanged, so `training/harness.py` and `qlearning.py` (03-14's this same wave) needed no edits.
- The complete run-2 config surface is declared in one pass: 9 new `StrategyKey` members (live
  per-turn decision path: search depth, feature scaling, weights path, learner rule, barrier
  candidate filter + 4 objective weights) and 6 new `TrainingKey` members (PFSP exponent, weak-
  opponent floor, pre-flight-gate thresholds), all loadable and type-checked through
  `load_strategy_config`. `TURN_BUCKET_FRACTIONS` removed. Both `config/{police,thief}/strategy.json`
  carry the identical new key set — no later plan (03-15..03-25) needs to open a config file except
  03-19 (two class-name values) and 03-21 (final numeric values), per the outline's file-ownership
  contract.
- The measured 150-line-gate split landed: `StrategyParams` and its schema table moved to a new
  `src/pursuit/shared/strategy_schema.py`; `strategy_config.py` kept only the loader functions and
  re-exports `StrategyParams` via `__all__`, so none of the ~20 existing
  `from pursuit.shared.strategy_config import StrategyParams` import sites across `training/` and
  `tests/` needed to change.
- `QTable.SCHEMA_VERSION` bumped 1 → 2; `_validate_top_level` now rejects any payload whose
  `version` differs from the current constant, naming both the found and expected values. No
  migration path was written (none was needed or safe to write — no table was ever promoted).

## Task Commits

Each task was committed atomically:

1. **Task 1: turns_remaining replaces turn_bucket in the state key** - `da27684` (feat)
2. **Task 2: declare the whole run-2 config surface, once** - `050d95d` (feat)
3. **Task 3: a run-1 Q-table fails loud instead of loading wrong** - `dd7384e` (feat)

**Plan metadata:** (this commit, docs)

## Files Created/Modified

- `src/pursuit/strategy/encoding.py` - `turn_bucket` deleted; `turns_remaining(turn_index,
  game_params)` added; `decode_state` returns `"turns_remaining"`; docstring rewritten with the
  D-06-superseded rationale and citations
- `src/pursuit/config_keys.py` - `TURN_BUCKET_FRACTIONS` removed; 9 new `StrategyKey` + 6 new
  `TrainingKey` members added, all structural (no numeric values)
- `src/pursuit/shared/strategy_schema.py` **(new)** - `StrategyParams` (53 fields) + the
  `(field_name, group_name, key, requirer, unit_interval)` schema table, group dicts referenced by
  name string
- `src/pursuit/shared/strategy_config.py` - now only `load_strategy_config` + its three private
  helpers; consumes `strategy_schema.SCHEMA` via a `{group_name: dict}` lookup; re-exports
  `StrategyParams`
- `src/pursuit/strategy/qtable.py` - `SCHEMA_VERSION = 2`; `_validate_top_level` rejects a
  version mismatch; docstring documents the no-migration rationale
- `config/police/strategy.json`, `config/thief/strategy.json` - `turn_bucket_fractions` removed;
  15 new keys added identically to both, per-role values differing only where `qtable_path`
  already differed (`weights_path`, `learner_rule`)
- `tests/unit/strategy/test_encoding.py` - bucket-boundary tests replaced with the
  `turns_remaining` contract (interior turn, clamp at/past ceiling, round trip, differing
  `turn_index` gives differing key); worked-example test adapted with an explicit note that
  `docs/PRD_rl_strategy.md` itself is not yet updated (03-22's job)
- `tests/unit/strategy/test_strategy_config.py` - unchanged in final content (net zero diff — new
  tests were added then relocated to satisfy the line-count gate)
- `tests/unit/strategy/test_strategy_config_run2.py` **(new)** - every new key's type across both
  role files, barrier-weight ordering contract, missing/wrong-typed-key fail-loud,
  `floor_episode_fraction_max`'s [0,1] range check, identical role key sets,
  `turn_bucket_fractions`' absence from both files
- `tests/unit/strategy/test_qtable.py`, `tests/unit/strategy/test_qtable_durability.py` - literal
  `"version": 1` payloads replaced with the imported `SCHEMA_VERSION` constant;
  `test_load_stale_schema_version_raises` added

## Decisions Made

See frontmatter `key-decisions` for the full, labelled list of every seeded value (measured /
sourced / engineering default). None is claimed as a `docs/PARAMETERS.md` value (project rule 1,
D-18).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - blocking, repeat of the established 03-05/06/07/08 pattern] `test_strategy_config.py`
split at the 150-line gate**
- **Found during:** Task 2
- **Issue:** Adding the run-2 key coverage directly to `test_strategy_config.py` pushed it to 162
  code lines against the 150 gate.
- **Fix:** New `tests/unit/strategy/test_strategy_config_run2.py` holds every run-2-specific test
  (new-key types, barrier-weight ordering, missing/wrong-typed-key, range check, identical role key
  sets, bucket-key absence); `test_strategy_config.py` reverted to its original content (net zero
  diff against the pre-plan file).
- **Files modified:** `tests/unit/strategy/test_strategy_config_run2.py` (new)
- **Verification:** `bash scripts/check_line_limit.sh` → 0 violations repo-wide; both files' tests
  pass (17 total).
- **Committed in:** `050d95d` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 3, line-limit split — the same contingency the plan's own
context section flagged in advance: "the 150-line gate counts CODE lines... task 2 nets +28, so
the split fires").
**Impact on plan:** Purely mechanical; no test weakened, removed, or moved without a corresponding
verification pass.

## Issues Encountered

- **Start timestamp not captured.** The `PLAN_START_TIME`/`PLAN_START_EPOCH` bash step in the
  execution workflow was not run before beginning file reads. Duration above is an estimate from
  session length, not a measured `epoch` delta. No functional impact — recorded honestly rather
  than fabricating a precise number.
- **The plan's own literal `grep -rn "turn_bucket" src/ training/ tests/` verification step
  returns 7 hits, not 0.** Inspected individually, all are benign and none is a functional
  dependency on the deleted symbol:
  - 2 hits are historical-rationale prose in `src/pursuit/config_keys.py` and
    `src/pursuit/strategy/qtable.py` docstrings, explaining *why* the field/version changed (same
    style as this project's own `D-06 superseded` documentation convention elsewhere).
  - 1 hit is a **pre-existing** stale docstring line in `training/harness.py` (`EpisodeConfig`'s
    docstring still says "turn_bucket_fractions encode_state needs"). Left untouched deliberately
    — `harness.py` is 03-14's file this same wave (outline SS7 file-ownership: sequential by wave,
    never parallel), and `encode_state`'s signature is unchanged so nothing there is functionally
    broken, only the prose is stale. Flagged here for 03-14 to correct in passing.
  - 4 hits are in the new `test_strategy_config_run2.py`, in a test function whose entire purpose
    is asserting `"turn_bucket_fractions"` is **absent** from both config files — the literal
    string is unavoidable in an absence assertion.
  - Confirmed separately: `Task 1`'s own narrower `<done>` criterion ("no `turn_bucket` symbol,
    string or dict field remains in `src/`") holds for the functional artifact — no callable, enum
    member, dataclass field, or dict key named `turn_bucket*` remains reachable from any code path.

## Next Phase Readiness

- 03-14 (terminal signal, R2+R4) can proceed: it inherits `encode_state`'s unchanged signature and
  `training/harness.py` untouched by this plan.
- 03-15/03-16/03-17/03-18/03-19/03-20/03-21/03-23 each have every config key they need already
  declared and loadable; per the outline's file-ownership table, none of them should open
  `config/{police,thief}/strategy.json` except 03-19 (class names) and 03-21 (final numbers).
- Wave 1's fourth and final plan is 03-14. No blockers identified.

---
*Phase: 03-blind-strategy-module-rl-policy*
*Completed: 2026-08-04*

## Self-Check: PASSED

All 13 claimed files confirmed present on disk; all 3 task commit hashes (`da27684`, `050d95d`,
`dd7384e`) confirmed present in `git log --oneline --all`.
