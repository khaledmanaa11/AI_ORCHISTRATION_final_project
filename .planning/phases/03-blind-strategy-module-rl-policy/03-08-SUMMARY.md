---
phase: 03-blind-strategy-module-rl-policy
plan: "08"
subsystem: training
tags: [offline-training, q-learning, sparring-pool, resumable-checkpoint, strat-06, d-16, d-21, d-22, d-24, d-25, d-19]

# Dependency graph
requires:
  - phase: 03-05
    provides: QTable (get/set/visits/best_action/copy, JSON save/load) -- the table run_training checkpoints and admits into the sparring pool
  - phase: 03-06
    provides: QLearningBrain(role, params, game_params, rng, table) -- the learner run_training drives; mutable .epsilon/.alpha reassigned per episode from the decay schedules
  - phase: 03-07
    provides: choose_barrier wired into both brains' _decide_move -- run_episode exercises the full movement+barrier decision on every cop turn
provides:
  - training/harness.py -- run_episode(learner, opponent, params, rng) -> EpisodeResult, the inner per-episode game loop over sdk.engine
  - training/curves.py -- open_curve/append/close/truncate_after, the D-16 CSV learning-curve writer
  - training/loop.py + loop_setup.py + progress.py + run_config.py -- run_training(TrainingRunConfig) -> RunResult, the outer resumable run driver (resume, opponent sampling, role alternation, schedules, cadenced checkpoint/curve/pool-snapshot, Windows keep-awake/final-checkpoint)
  - training/runstate.py -- + combined_config_hash(cop_params, thief_params)
affects: [03-09, 03-10]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "One shared random.Random(seed) instance for the whole run -- opponent sampling AND both brains' own epsilon-greedy exploration draws from the SAME instance (each QLearningBrain constructed with it directly), matching docs/PRD_rl_strategy.md Sec5's D-19 wording verbatim ('ε-greedy action selection and opponent sampling use A seeded random.Random(training.seed) instance') and runstate.py's own single-field RunState.rng_state design -- not a per-brain sub-seed"
    - "Artifact-path separation (D-22): training checkpoints Q-tables under StrategyParams.artifacts_dir (LOCALAPPDATA by default) using the SAME basename as the role's configured qtable_path, never at that repo-relative config path itself -- the config path names the FINAL BLESSED table a later plan copies in at run end, and rewriting a multi-MB table there every checkpoint_every episodes would churn OneDrive on every interval"
    - "Single curve CSV for both roles, not two -- the schema's own `role` column (D-25) already keeps cop/thief separable, and RunState's single `csv_row_count` field only makes sense against one file"
    - "150-line-gate split pattern repeated a fourth time (03-05/06/07's precedent): the outer driver split into loop.py (episode-loop orchestration), loop_setup.py (once-per-run resume/checkpoint/pool-build/Windows-guard helpers), progress.py (pure mutable bookkeeping dataclasses), run_config.py (shared TrainingRunConfig/RunResult, breaking a would-be import cycle between loop.py and loop_setup.py)"

key-files:
  created:
    - training/harness.py
    - training/curves.py
    - training/loop.py
    - training/loop_setup.py
    - training/progress.py
    - training/run_config.py
    - training/artifacts.py
    - tests/unit/training/test_harness.py
    - tests/unit/training/test_loop.py
    - tests/unit/training/test_curves.py
  modified:
    - training/runstate.py
    - docs/phases/phase-3/TODO.md
    - .planning/graphs/{graph.json,graph.html,GRAPH_REPORT.md}

key-decisions:
  - "run_training(config: TrainingRunConfig) takes ONE bundled object (game_params + cop_params + thief_params), matching the plan's literal single-argument run_training(params) signature while still giving each role its own StrategyParams (brain_class/qtable_path/reward_* legitimately differ per role)"
  - "Run-level scalars (seed, episodes, checkpoint_every, pool_snapshot_every, artifacts_dir) must agree between cop.json and thief.json -- validated up front (require_shared_run_fields, raises ValueError naming the mismatched fields) rather than silently picking one side, since a resumed run reading a different seed than the one its own checkpoint was produced under would desync reproducibility"
  - "winrate_vs_baseline is tracked specifically against opponent_kind == 'heuristic' draws (the pool's literal baseline member), not every sampled opponent -- so the column means what its name says rather than blending in past-self/reference results"
  - "checkpoint_every and pool_snapshot_every read as GLOBAL (both-roles-combined) episode cadences; curve_log_every reads as a PER-ROLE cadence (role_episodes % curve_log_every) -- matches RESEARCH's framing of checkpoint/pool-snapshot as whole-run crash-recovery/anti-collapse mechanics, while the curve's own `role` column and separate epsilon/alpha schedules make per-role logging the only cadence that produces an evenly-spaced curve per role"
  - "Role alternation is strict global-episode parity (cop learns on even progress.episode, thief on odd) -- the simplest schedule satisfying D-25's 'alternate which role learns' with no other tie-breaking rule specified anywhere in the plan or PRD"
  - "config_hash mismatch on resume (e.g. episodes bumped between runs) logs a warning, not a hard failure -- the plan requires the hash be RECORDED for provenance, not that a resume be blocked on any config drift; RNG state and episode counters are what actually gate correctness, and those are restored/validated independently"

patterns-established:
  - "Offline single-process training may share a random.Random instance and Q-table access across simulated cop/thief roles for reproducibility -- this is a training-pipeline determinism choice, not a violation of project rule 2 (no shared runtime state), which governs the two DEPLOYED agent processes at match time, not this offline harness. Documented explicitly in training/loop.py's own module docstring to preempt future doubt."

# Metrics
duration: ~50min (this session's remaining work: Task 4 only -- Tasks 1-3 were already committed from a prior session)
completed: 2026-08-01
---

# Phase 3 Plan 08: Offline Training Harness Summary

**`run_training(config)` -- a resumable, single-seed, whole-run-checkpointed Q-learning trainer that alternates which of cop/thief learns per episode against a delta-uniform sparring pool, appending a shared learning-curve CSV from episode 1 and surviving a Windows `KeyboardInterrupt` with at most one checkpoint interval lost.**

## Performance

- **Duration:** ~50 min for this session's actual work (Task 4 only -- Tasks 1-3 of this plan
  were already implemented and committed in a prior, interrupted session: commits `8891f64`
  durable run-state checkpointing, `7482bea` sparring pool, `3eed329` reference adapter).
- **Started:** picked up mid-plan; `training/curves.py` + its tests and `training/harness.py`'s
  `run_episode` inner loop were already written (uncommitted) at session start.
- **Completed:** 2026-08-01
- **Tasks:** 1 remaining task completed (Task 4 of 4)
- **Files modified:** 7 created, 1 modified in the code commit; 3 test files created

## Accomplishments

- **`training/curves.py`** (inherited from the interrupted session, verified still correct and
  committed here): `open_curve`/`append`/`close`/`truncate_after` over the exact
  `episode,epsilon,alpha,mean_reward,winrate_vs_baseline,fallback_rate,role` schema (AI-SPEC E6),
  header written once with `seed`+`config_hash`, `csv` stdlib only.
- **`training/harness.py`'s `run_episode`** (inherited, verified correct): drives `sdk.engine`
  cop-then-thief per turn, builds `Observation`s, calls `_decide_move`, applies the result, computes
  the PRD Sec4 reward, and calls `learner.update(...)` -- only ever on the learner's own brain.
  Added one direct unit test for its previously-uncovered `_role_won(role, None)` defensive branch,
  closing the module to 100% coverage.
- **`training/loop.py` + `loop_setup.py` + `progress.py` + `run_config.py` (new, this session):**
  `run_training(config: TrainingRunConfig) -> RunResult`, the outer driver:
  - Resumes from `run_state.json` if present (`loop_setup.load_or_init`): restores both Q-tables,
    the shared RNG's exact state (`runstate.restore_rng_state`), each role's own episode counter,
    and calls `curves.truncate_after(curve_path, checkpoint_episode)` so a resumed run never leaves
    a duplicated rewound curve segment (D-24). A config-hash mismatch (e.g. `episodes` changed
    between runs) logs a warning rather than blocking the resume.
  - Samples one frozen opponent per episode from the appropriate `SparringPool` (`training.sparring`,
    already built in Tasks 1-3), alternates which role learns by global-episode parity (D-25), and
    reassigns the learner's `epsilon`/`alpha` from `runstate.epsilon_at`/`alpha_at` before every
    episode -- never resetting the schedule on resume, since it reads off the persisted per-role
    episode counter.
  - Admits a Q-table snapshot into each role's own pool on `pool_snapshot_every`, checkpoints both
    tables plus the run manifest on `checkpoint_every` (both read as whole-run, both-roles-combined
    cadences -- validated equal between `cop.json`/`thief.json` up front), and appends one curve
    row per role on that role's own `curve_log_every` (a per-role cadence, since epsilon/alpha and
    the curve's own `role` column are already per-role).
  - `winrate_vs_baseline` is computed only over episodes where the sampled opponent's
    `kind == "heuristic"` -- the pool's literal baseline member -- so the column is not diluted by
    past-self/reference results.
  - Windows long-run handling per RESEARCH Sec3: `win32_keep_awake`/`win32_release`
    (`SetThreadExecutionState`, guarded by `sys.platform == "win32"`), and a `try/finally` final
    checkpoint plus an `atexit` backstop (unregistered on clean exit to avoid a redundant double
    write) so a `KeyboardInterrupt` -- the realistic stop signal on Windows, which delivers no
    SIGTERM -- still leaves a durable checkpoint. Verified directly: a simulated `KeyboardInterrupt`
    mid-run propagates to the caller AND leaves a valid, loadable checkpoint on disk.
  - A single, shared `random.Random(config.cop_params.seed)` instance drives opponent sampling and
    BOTH brains' own exploration -- constructed once and passed to both `QLearningBrain`s and the
    pool sampler -- so `RunState.rng_state`'s one `getstate()` reproduces the entire run exactly.
    This matches `docs/PRD_rl_strategy.md` Sec5's D-19 wording precisely ("ε-greedy action
    selection **and** opponent sampling use **a** seeded `random.Random(training.seed)` instance").
- **`training/runstate.py`:** added `combined_config_hash(cop_params, thief_params)`, reusing the
  same canonicalisation as the existing single-role `config_hash` (QUAL-02) -- one run trains two
  roles under two, potentially different, `StrategyParams` objects, so the checkpoint/curve header
  needs one hash spanning both.
- **`tests/unit/training/test_harness.py`** (new): `run_episode` reaches a terminal outcome and
  writes only to the learner's table; a structural proof that the opponent's `update` is never
  called (`HeuristicBrain` has no such method -- reaching for it would raise `AttributeError`
  before the episode could finish); determinism under a fixed seed; the D-17 no-network-import
  structural test extended to BOTH directions (`training/**` imports nothing from
  `pursuit.network`, and nothing under `src/pursuit/**` imports `training`), reusing the exact
  AST-walk pattern `tests/unit/strategy/test_registry.py` already established for STRAT-03/07.
- **`tests/unit/training/test_loop.py`** (new): a short (30-episode) seeded run completes with
  nonzero visit counts on both tables; the same seed from a fresh start reproduces byte-identical
  curve rows and identical Q-tables; resume continuity of epsilon/alpha across a checkpoint
  boundary (verified against `runstate.epsilon_at`/`alpha_at` computed independently); a stray
  curve row planted past the last checkpoint is truncated on resume; a real `KeyboardInterrupt`
  mid-run still leaves a loadable, non-empty checkpoint; `require_shared_run_fields` rejects a
  seed mismatch between the two role configs.
- Full repo gates green: `uv run ruff check .` -> 0 violations; `bash scripts/check_line_limit.sh`
  -> clean on every touched file (largest new file `harness.py` at 132 code lines, well under 150);
  `uv run pytest --cov=pursuit --cov=training -q` -> 346 passed, 1 skipped (the reference-clone
  integration test, correctly skipped without the clone), 97.04% overall coverage. Every new
  `training/` module in this plan is at 100% coverage except the pre-existing
  `sparring_reference.py` (50%, expected -- the guarded import path is only exercised when a local
  clone is present, matching D-21's own established, documented exemption from Task 3).
- Graphify graph rebuilt after this plan's new code (2897 nodes / 5089 edges / 189 communities,
  built from commit `9aaf8295`); `.planning/graphs/{graph.json,graph.html,GRAPH_REPORT.md}`
  refreshed. `docs/phases/phase-3/TODO.md` row 03-08 marked done.

## Task Commits

Tasks 1-3 were committed in a prior session (see `.planning/STATE.md`'s Session Continuity for
context): `8891f64` (Task 1: durable checkpoint + run state), `7482bea` (Task 2: sparring pool),
`3eed329` (Task 3: reference adapter). This session completed and committed the remainder:

4. **Task 4: Curve logging, episode loop, and the training entry point** - `9aaf829` (feat)

**Plan metadata:** (this commit, following SUMMARY/STATE update)

## Files Created/Modified

- `training/harness.py` -- `run_episode`, `Player`/`EpisodeConfig`/`EpisodeResult`, `_turn`,
  `_observation`, `_reward`, `_update_learner`, `_accumulate`, `_role_won`
- `training/curves.py` -- `open_curve`, `append`, `close`, `truncate_after`, `CurveWriter`
- `training/loop.py` -- `TrainingRunConfig`/`RunResult` re-export, `run_training`, `_build_brains`,
  `_run_episodes`, `_maybe_log_curve`
- `training/loop_setup.py` -- `require_shared_run_fields`, `build_pool`, `load_or_init`,
  `build_run_state`, `write_checkpoint`, `win32_keep_awake`, `win32_release`
- `training/progress.py` -- `RunProgress`, `RoleAccumulator`
- `training/run_config.py` -- `TrainingRunConfig`, `RunResult`
- `training/artifacts.py` -- `table_checkpoint_path`, `run_state_path`, `curve_path`,
  `load_or_new_table`
- `training/runstate.py` -- `+ combined_config_hash`
- `tests/unit/training/{test_harness,test_loop,test_curves}.py`
- `docs/phases/phase-3/TODO.md` -- row 03-08 marked done
- `.planning/graphs/{graph.json,graph.html,GRAPH_REPORT.md}` -- rebuilt

## Decisions Made Autonomously

No user was available for this unattended run. See `key-decisions` in frontmatter for the full
list with rationale; in brief:

- `run_training(config: TrainingRunConfig)` bundles `game_params`/`cop_params`/`thief_params` into
  one object, satisfying the plan's literal single-argument signature while keeping each role's
  own `StrategyParams` distinct (their `brain_class`/`qtable_path`/`reward_*` legitimately differ).
- A single shared `random.Random` instance drives every nondeterministic draw in the run (opponent
  sampling, both brains' own exploration) -- not a design invented for this plan, but the literal
  reading of `docs/PRD_rl_strategy.md` Sec5's D-19, discovered and confirmed while implementing.
- Q-table checkpoints during training live under `artifacts_dir` using the qtable_path's basename,
  never at the repo-relative `qtable_path` itself -- that path is reserved for the FINAL BLESSED
  table a later plan copies in at run end (RESEARCH Sec3); copying it is out of this plan's scope.
- `checkpoint_every`/`pool_snapshot_every` read as global (combined) cadences; `curve_log_every`
  reads as per-role -- validated consistent between the two role configs up front so a drift
  between `cop.json`/`thief.json` fails loud instead of silently picking one side.
- `winrate_vs_baseline` is scoped to `opponent_kind == "heuristic"` episodes specifically, matching
  what the column name says rather than blending in past-self/reference results.
- 150-line-gate split into four files (`loop.py`/`loop_setup.py`/`progress.py`/`run_config.py`),
  repeating the exact pattern 03-05/03-06/03-07 already established for this repo -- `run_config.py`
  exists specifically to break a would-be import cycle between `loop.py` and `loop_setup.py`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] `harness.py`'s `_role_won(role, None)` branch had no direct test**
- **Found during:** Task 4, reviewing coverage after the first full-suite run (99% on `harness.py`,
  one line: the `outcome is None` fallthrough).
- **Issue:** `run_episode` itself never returns with `outcome is None` (the loop always terminates
  by `move_ceiling + 1`), so no integration test exercised this defensive branch; sibling
  Phase-3 modules (`barriers.py`/`heuristic.py`/`qlearning.py`) are all at 100%.
- **Fix:** Added `test_role_won_is_false_for_neither_role_when_the_game_has_no_outcome_yet`,
  calling `_role_won` directly with `outcome=None` for both roles.
- **Files modified:** `tests/unit/training/test_harness.py`.
- **Verification:** `uv run pytest tests/unit/training/ --cov=training` -> `harness.py` 100%.
- **Committed in:** `9aaf829` (Task 4 commit).

**2. [Rule 3 - Blocking, repeat of the 03-05/06/07 pattern] `run_training` plus its setup logic would have exceeded 150 code lines in one file**
- **Found during:** Task 4, drafting the outer driver -- the orchestrator's own briefing flagged
  this as likely before implementation began (a stray docstring in the inherited `harness.py`
  already anticipated a `training/loop.py` split from the interrupted prior session).
- **Issue:** Resume/init, pool-building, checkpoint-writing, Windows guards, per-episode
  orchestration, and curve-logging cadence logic combined would run well past 150 code lines.
- **Fix:** Split into `training/loop.py` (episode-loop orchestration only), `training/loop_setup.py`
  (once-per-run resume/checkpoint/pool-build/Windows-guard helpers), `training/progress.py` (pure
  mutable bookkeeping: `RunProgress`, `RoleAccumulator`), and `training/run_config.py` (the shared
  `TrainingRunConfig`/`RunResult` dataclasses, needed to avoid a circular import between `loop.py`
  and `loop_setup.py`). The inherited `harness.py` docstring's mention of `training/loop.py` needed
  no correction -- it already named the file this split produces.
- **Files modified:** `training/loop.py`, `training/loop_setup.py`, `training/progress.py`,
  `training/run_config.py` (all new).
- **Verification:** `bash scripts/check_line_limit.sh` clean on every file (largest, `harness.py`,
  at 132 code lines).
- **Committed in:** `9aaf829` (Task 4 commit).

---

**Total deviations:** 2 auto-fixed (1 Rule 2 -- closing a coverage gap on a genuinely-reachable
defensive branch; 1 Rule 3 -- a repeat of this repo's now four-times-established 150-line-gate
split pattern). No scope or behavior change beyond what the plan's own Task 4 action text and
`<verify>` block require.
**Impact on plan:** None beyond organizational file splitting and one additional unit test.

## Issues Encountered

- The plan's literal `run_training(params)` signature (singular `params`) needed to become
  `run_training(config: TrainingRunConfig)` bundling three objects (`game_params`, `cop_params`,
  `thief_params`), since a single `StrategyParams` cannot describe a run that trains BOTH roles'
  tables together under two configs that legitimately differ in `brain_class`/`qtable_path`/
  `reward_*`. Resolved by treating `params` as "the run's config, as one object" rather than
  literally one `StrategyParams` instance -- consistent with the codebase's existing
  `EpisodeConfig` pattern (03-08's own inherited `harness.py`, which already bundles
  `game_params`+`learner_params` the same way).
- Manually verified (outside the test suite, via ad-hoc scripts against tiny episode counts) before
  writing the formal tests: exact curve/table reproducibility across two independent fresh runs
  with the same seed; resume continuity of epsilon/alpha across a checkpoint boundary; truncation
  of a manually-planted stray curve row on resume; and a real `KeyboardInterrupt` mid-run leaving a
  valid checkpoint. All four became the corresponding `tests/unit/training/test_loop.py` cases.
- No authentication gates, no architectural questions requiring a stop, no blockers.

## User Setup Required

None -- no external service configuration required. A real overnight run (300,000 episodes per
`config/{police,thief}/strategy.json`) is an operator task, not something this plan or its tests
execute; per `docs/phases/phase-3/PLAN.md`'s test plan, "no test trains a real policy."

## Next Phase Readiness

- `training.loop.run_training` and `training.loop.TrainingRunConfig` are the entry point 03-09
  (learning curves + plotting + README section) and 03-10 (gate tests + coverage audit) build on;
  `RunResult` hands back both final `QTable`s plus the `RunState` manifest without needing to
  re-read them off disk.
- The blessed-table copy step (training checkpoint -> `config/{police,thief}/strategy.json`'s
  `qtable_path`, i.e. the repo) is explicitly NOT part of this plan (RESEARCH Sec3) and remains
  open for 03-09/03-10 to own.
- `training/curves.py`'s CSV is the direct input `training/plot_curves.py` (03-09) reads; the
  `role` column is what lets it render two separate curves per the rule-42 README section.
- No blockers. Every Phase-3 hyperparameter `run_training` reads (`episodes`, `checkpoint_every`,
  `curve_log_every`, `pool_snapshot_every`, `pool_size`, `selfplay_delta`, `seed`, `artifacts_dir`,
  `reference_impl_path`, `reward_*`, `epsilon_*`, `alpha_*`) already existed in `StrategyParams`
  from 03-00's config scaffold -- no new config keys were required for this plan.

---
*Phase: 03-blind-strategy-module-rl-policy*
*Completed: 2026-08-01*

## Self-Check: PASSED

All 16 claimed files confirmed present on disk (`training/{harness,curves,loop,loop_setup,
progress,run_config,artifacts,runstate}.py`, `tests/unit/training/{test_harness,test_loop,
test_curves}.py`, `docs/phases/phase-3/TODO.md`, `.planning/graphs/{graph.json,graph.html,
GRAPH_REPORT.md}`, this SUMMARY). All 4 referenced commit hashes (`8891f64`, `7482bea`,
`3eed329`, `9aaf829`) confirmed present in `git log --oneline --all`.
