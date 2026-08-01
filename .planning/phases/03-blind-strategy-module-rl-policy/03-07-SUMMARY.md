---
phase: 03-blind-strategy-module-rl-policy
plan: "07"
subsystem: strategy
tags: [barrier-placement, bfs, cop-only, strat-05, d-09, d-12, ai-spec-e9, config-split]

# Dependency graph
requires:
  - phase: 03-03
    provides: bfs(state, start, goal, agent, params) -> (distance, next_step), UNREACHABLE sentinel -- the single distance oracle
  - phase: 03-04
    provides: HeuristicBrain(BrainBase), the `# 03-07` attachment marker in its cop-side _decide_move
  - phase: 03-06
    provides: QLearningBrain(BrainBase), the matching `# 03-07` attachment marker in its own _decide_move
provides:
  - src/pursuit/strategy/barriers.py -- choose_barrier(state, game_params, believed_thief_cell, min_gain) -> Coord | None, the cop-only second decision stage (D-12)
  - src/pursuit/config_keys.py -- ConfigKey/NetworkConfigKey/StrategyKey/TrainingKey, split out of constants.py at the 150-code-line ceiling
  - strategy.barrier_min_gain in StrategyParams/config/{police,thief}/strategy.json -- the engineering-default improvement threshold the plan required but did not source
  - Both HeuristicBrain._decide_move and QLearningBrain._decide_move now attach a real, engine-validated cop barrier; thief's is unconditionally None
affects: [03-08, 03-09, 03-10, "training's reward_barrier_gain shaping term (PRD Sec4) can reuse this module's BFS-to-anchor gain concept if it needs one"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Legality-by-delegation: choose_barrier never re-derives place_barrier's rejection rules -- every candidate is checked by calling place_barrier itself and testing identity (`place_barrier(state, cell, params) is state`) on rejection (QUAL-02), so a rule change in barrier.py can never silently desync from the sub-policy's candidate filter"
    - "Post-move probe before scoring: both brains build `dataclasses.replace(state, cop=movement.move)` before calling choose_barrier, so every legality/anchor computation matches the exact state sdk.engine.apply_cop_action will validate against (move-then-barrier order) -- this is what makes declared == applied a structural guarantee rather than a coincidence"
    - "Anchor-cell exclusion: the scoring reference point (the board corner diagonally farthest from the cop) is itself excluded from the candidate set, closing a trivial 'wall off my own scoring reference point regardless of the thief's position' degenerate solution found during manual verification before any test was written"

key-files:
  created:
    - src/pursuit/strategy/barriers.py
    - src/pursuit/config_keys.py
    - tests/unit/strategy/test_barriers.py
    - tests/unit/strategy/test_barriers_integration.py
  modified:
    - src/pursuit/strategy/heuristic.py
    - src/pursuit/strategy/qlearning.py
    - src/pursuit/constants.py
    - src/pursuit/shared/config.py
    - src/pursuit/shared/network_config.py
    - src/pursuit/shared/strategy_config.py
    - config/police/strategy.json
    - config/thief/strategy.json
    - tests/unit/strategy/test_strategy_config.py
    - tests/unit/test_network_config.py
    - tests/unit/strategy/test_heuristic.py
    - tests/unit/strategy/test_qlearning.py
    - docs/phases/phase-3/PLAN.md
    - docs/phases/phase-3/TODO.md
    - .planning/graphs/GRAPH_REPORT.md

key-decisions:
  - "Scoring metric for 'the thief's best escape' (autonomous decision, the plan's own wording left this open): anchors at the board corner diagonally farthest from the cop's own (post-move) cell, scores each candidate by how much it lengthens (or severs) the believed thief cell's BFS route to that anchor, requiring exactly one bfs() call per candidate. Chosen because bfs(cop, thief) is provably symmetric in this codebase (get_legal_moves never special-cases the agent argument beyond which GameState field it reads), so 'increase the cop-thief distance' cannot discriminate a cop-favoring placement from a self-defeating one -- a fixed, board-geometry-only third point was required to make the metric asymmetric and genuinely useful, and no other 'escape zone' concept exists anywhere in the game rules"
  - "choose_barrier takes min_gain as an explicit 4th parameter (not the plan's literal 3-parameter sketch) because game_params.barrier_quota (a PARAMETERS.md value, D-05) and strategy.barrier_min_gain (an engineering default, D-18) live in two different config objects (GameParams vs StrategyParams) in this codebase's established architecture -- conflating them into one params object, or worse, inventing a barrier threshold inside game_params.json, would have violated D-05's 'every number traces to PARAMETERS.md' rule for GameParams"
  - "Both _decide_move implementations build the post-move probe state (dataclasses.replace(state, cop=movement.move)) before calling choose_barrier, matching sdk.engine.apply_cop_action's real move-then-barrier order exactly -- this is what makes 'declared == applied' hold by construction; validating against the pre-move state instead was considered and rejected because it can silently diverge from the engine's own decision the moment a movement destination coincides with a barrier candidate"
  - "strategy.barrier_min_gain = 1 (both role configs, byte-for-byte identical value, matching the existing [strategy] group's cross-role-consistency convention) -- the smallest BFS-distance increase that is still a real, measurable lengthening of the thief's route; 0 was rejected because it would let the sub-policy spend a finite barrier for provably zero gain, which the plan's own action text calls 'strictly worse than keeping it'"

patterns-established:
  - "Config-key module split: when constants.py or any file at the 150-line ceiling needs one more member, extract the least-central class/group first (here: the four *Key classes moved wholesale to config_keys.py) rather than trimming docstrings -- preserves every existing docstring's content, only import paths change"

# Metrics
duration: ~70min
completed: 2026-08-01
---

# Phase 3 Plan 07: Cop Barrier Sub-Policy Summary

**`choose_barrier` -- a pure, BFS-scored, quota-aware cop-only barrier sub-policy wired as the second decision stage in both `HeuristicBrain` and `QLearningBrain`, with declared-equals-applied honesty proven against the real engine over full games.**

## Performance

- **Duration:** ~70 min
- **Tasks:** 2 completed
- **Files modified:** 4 created, 15 modified

## Accomplishments

- `src/pursuit/strategy/barriers.py`: `choose_barrier(state, game_params, believed_thief_cell, min_gain) -> Coord | None` -- the cop's second decision stage after `_pick_move` (D-12), keeping the Q action space at exactly 5. Legality is never re-derived: every candidate cell is filtered by calling `pursuit.shared.barrier.place_barrier` itself and checking identity on rejection (QUAL-02). Every score comes from `pathfind.bfs()` alone (D-09) -- candidates are scored by how much they lengthen (or sever) the believed thief cell's BFS route to a fixed anchor (the board corner diagonally farthest from the cop's own cell), with the anchor cell itself excluded from candidates to close a trivial exploit found during manual verification (placing a barrier directly on the anchor always "wins" regardless of the thief's real position). Returns `None` at quota, when no candidate exists, or when the best gain doesn't clear `min_gain`. Pure function of its inputs only (D-03) -- `state.thief` is never read.
- Both `HeuristicBrain._decide_move` and `QLearningBrain._decide_move` (replacing their `# 03-07` markers) now build a post-move probe state (`dataclasses.replace(state, cop=movement.move)`) matching `sdk.engine.apply_cop_action`'s real move-then-barrier order, then call the one shared `choose_barrier` (QUAL-02 -- neither brain reimplements any part of the decision). The thief branch is `barrier = None` unconditionally, never routed through `choose_barrier` at all.
- **Deviation (Rule 2/3 -- blocking):** the plan's own action text requires "a configured improvement threshold," which did not exist. Added `strategy.barrier_min_gain` (engineering default, D-18, value `1`) to `StrategyParams`/`load_strategy_config`/both `config/{police,thief}/strategy.json`. Adding its key to `StrategyKey` required first splitting `src/pursuit/constants.py`, which was already at the exact 150-code-line ceiling per this session's own briefing: `ConfigKey`/`NetworkConfigKey`/`StrategyKey`/`TrainingKey` moved wholesale to a new `src/pursuit/config_keys.py`; `constants.py` keeps only the game-domain enums and `Action`<->`Direction` helpers. Five import sites updated mechanically (`shared/config.py`, `shared/network_config.py`, `shared/strategy_config.py`, `tests/unit/test_network_config.py`, `tests/unit/strategy/test_strategy_config.py`) -- no assertion changed, all pre-existing tests still pass.
- `tests/unit/strategy/test_barriers.py` (Task 1, pure unit tests, 100% coverage on `barriers.py`): quota-exhausted-returns-None, open-board-no-candidate-above-threshold (also the anchor-exploit regression case), chokepoint-placement-that-lengthens-the-escape-is-chosen, returned-cell-is-always-engine-legal, already-unreachable-baseline-yields-no-further-gain, determinism.
- `tests/unit/strategy/test_barriers_integration.py` (Task 2, new file, Rule 3 split -- see Deviations): a full `HeuristicBrain`-vs-`HeuristicBrain` game through `sdk.engine`, asserting on every cop turn that declares a barrier that the engine's applied result matches exactly (`AI-SPEC E9`, rules 16/22) and that `barriers_placed` never exceeds `barrier_quota`; the same honesty/quota proof repeated end-to-end for `QLearningBrain`'s own, separately-implemented `_decide_move`; and the thief-never-barriers guarantee proven directly for `QLearningBrain` across several decisions.
- Two now-stale `# 03-07 not landed yet` comments/test names (left by 03-04/03-06) were corrected in `tests/unit/strategy/test_heuristic.py` and `tests/unit/strategy/test_qlearning.py` -- both underlying assertions still held (the exact scenarios they use happen to be open-board, no-chokepoint cases), but the comments were now factually wrong after this plan landed.
- Full repo gates green: `uv run ruff check .` -> 0 violations; `bash scripts/check_line_limit.sh` -> clean (`barriers.py` 93 code lines, well within `[40, 150]`); `uv run pytest --cov=pursuit --cov=training -q` -> 305 passed, 97.78% coverage overall, `barriers.py`/`heuristic.py`/`qlearning.py` each 100%.
- Graphify graph rebuilt after this plan's new code (2624 nodes / 4264 edges / 187 communities); `.planning/graphs/GRAPH_REPORT.md` refreshed and committed. `docs/phases/phase-3/{PLAN,TODO}.md` updated: row 03-07 marked done; the Components table and interface block document `choose_barrier`'s real 4-argument signature and the new `config_keys.py` split.

## Task Commits

Each task was committed atomically:

1. **Task 1: Barrier sub-policy** - `b91c08a` (feat)
2. **Task 2: Wire into both brains and prove declared == applied** - `738eba9` (feat)

**Plan metadata:** (this commit, following SUMMARY/STATE update)

## Files Created/Modified

- `src/pursuit/strategy/barriers.py` -- `choose_barrier`, `_legal_candidates`, `_escape_anchor`, `_bfs_distance`, `_gain`
- `src/pursuit/config_keys.py` -- `ConfigKey`, `NetworkConfigKey`, `StrategyKey` (+`BARRIER_MIN_GAIN`), `TrainingKey`
- `src/pursuit/constants.py` -- trimmed to game-domain enums + `Action`/`Direction` helpers only
- `src/pursuit/shared/{config,network_config,strategy_config}.py` -- import path updated to `pursuit.config_keys`; `strategy_config.py` also gains the `barrier_min_gain` field/schema row
- `config/{police,thief}/strategy.json` -- `strategy.barrier_min_gain: 1` added
- `src/pursuit/strategy/heuristic.py`, `src/pursuit/strategy/qlearning.py` -- `_decide_move` wired to `choose_barrier`
- `tests/unit/strategy/test_barriers.py` -- 6 tests, `choose_barrier` unit coverage
- `tests/unit/strategy/test_barriers_integration.py` -- 3 tests, brain-level honesty/quota/thief-never-barriers proofs
- `tests/unit/{test_network_config,strategy/test_strategy_config,strategy/test_heuristic,strategy/test_qlearning}.py` -- import path fix + two stale-comment corrections
- `docs/phases/phase-3/{PLAN,TODO}.md`, `.planning/graphs/GRAPH_REPORT.md` -- doc triplet and graph refresh

## Decisions Made Autonomously

See `key-decisions` in frontmatter. In brief, since the user was unavailable for this unattended run:

- The scoring metric for "the thief's best escape" was left open by the plan's own wording. Chose a fixed board-geometry anchor (the corner diagonally farthest from the cop) because the codebase's `bfs()` is provably symmetric between cop and thief (adjacency depends only on `state.barriers`, never on which `agent` string is passed), so a direct "increase cop-thief distance" metric cannot distinguish a cop-favoring barrier from a self-defeating one. No other "escape zone" concept exists anywhere in the game rules, so this is a documented engineering choice, not a derived one -- and it was verified by hand (via `uv run python -c ...` probes) against three scenarios (open board -> None, chokepoint -> the correct seal cell, quota exhausted -> None) before any test was written, catching the anchor-cell trivial-exploit case in the process.
- `choose_barrier` gained a 4th parameter (`min_gain`) rather than folding the threshold into the plan's literal 3-parameter sketch, because the threshold (`StrategyParams.barrier_min_gain`, an engineering default) and the quota (`GameParams.barrier_quota`, a PARAMETERS.md value) live in two different config objects by this codebase's own established architecture, and merging them or inventing a threshold inside `game_params.json` would have violated D-05.
- Both brains build the post-move probe state before calling `choose_barrier`, rather than validating against the pre-move `state` the plan's signature sketch implies -- this was necessary for correctness (not just a preference), since `sdk.engine.apply_cop_action` applies the move before validating the barrier, and validating against the wrong state risks a declared placement the engine later rejects.
- `barrier_min_gain = 1` was chosen as the smallest value that still requires a *real* measurable lengthening (0 would let the sub-policy spend a barrier for proven zero gain, which the plan's own text calls strictly worse than not spending it).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2/3 -- Missing critical functionality / blocking issue] No config threshold existed for "a configured improvement threshold"**
- **Found during:** Task 1, while implementing `choose_barrier`'s selection rule.
- **Issue:** The plan's `<action>` text requires "the best-scoring candidate above a configured improvement threshold," but no such field existed in `StrategyParams` or either `strategy.json`.
- **Fix:** Added `strategy.barrier_min_gain` (engineering default, D-18, value `1`) to `StrategyKey`, `StrategyParams`, `load_strategy_config`'s schema, and both `config/{police,thief}/strategy.json`. This required first splitting `src/pursuit/constants.py` (already at the exact 150-code-line ceiling): `ConfigKey`/`NetworkConfigKey`/`StrategyKey`/`TrainingKey` moved to a new `src/pursuit/config_keys.py`.
- **Files modified:** `src/pursuit/constants.py`, `src/pursuit/config_keys.py` (new), `src/pursuit/shared/{config,network_config,strategy_config}.py`, `config/{police,thief}/strategy.json`, `tests/unit/test_network_config.py`, `tests/unit/strategy/test_strategy_config.py`.
- **Verification:** `bash scripts/check_line_limit.sh` clean on all touched files; `uv run pytest -q` -> 302 passed (before Task 2's additions) with zero pre-existing assertions changed.
- **Committed in:** `b91c08a` (Task 1 commit).

**2. [Rule 3 -- Blocking] `tests/unit/strategy/test_barriers.py` would have exceeded 150 code lines with Task 2's honesty/integration tests added**
- **Found during:** Task 2, after drafting the full-game declared-equals-applied test alongside Task 1's 6 pure unit tests in the same file.
- **Issue:** Combining both would have pushed the file well past the 150-line gate.
- **Fix:** Split along the same seam 03-05/03-06 already established: `test_barriers.py` keeps the pure `choose_barrier` unit tests; `tests/unit/strategy/test_barriers_integration.py` (new) holds the full-game, brain-level honesty/quota/thief-never-barriers tests.
- **Files modified:** `tests/unit/strategy/test_barriers_integration.py` (new).
- **Verification:** `bash scripts/check_line_limit.sh` clean on both files; `uv run pytest tests/unit/strategy/ -q` -> all pass.
- **Committed in:** `738eba9` (Task 2 commit).

**3. [Rule 1 -- Bug, documentation accuracy] Two stale "03-07 not landed yet" comments/test names left by 03-04/03-06**
- **Found during:** Task 2, running the full suite after wiring both brains.
- **Issue:** `test_heuristic.py::test_every_decision_carries_heuristic_source` and `test_qlearning.py::test_decide_move_attaches_no_barrier_yet` both asserted `decision.barrier is None` with comments explaining this was because the barrier sub-policy wasn't wired yet. Both assertions still passed after wiring (the exact scenarios they use are open-board, no-chokepoint cases where `choose_barrier` legitimately returns `None`), but the comments were now factually wrong and misleading about *why*.
- **Fix:** Reworded both comments (and renamed the qlearning test) to explain the real, still-correct reason the assertion holds, with a pointer to `test_barriers.py`/`test_barriers_integration.py` for the wired, non-None case.
- **Files modified:** `tests/unit/strategy/test_heuristic.py`, `tests/unit/strategy/test_qlearning.py`.
- **Verification:** `uv run pytest tests/unit/strategy/ -q` -> all 126 strategy tests still pass; no assertion changed, only prose.
- **Committed in:** `738eba9` (Task 2 commit).

---

**Total deviations:** 3 auto-fixed (1 Rule 2/3 -- a genuine interface gap the plan's own text required but didn't source; 1 Rule 3 -- a repeat of the now-established 150-line-gate test-file split pattern; 1 Rule 1 -- stale-comment correction with zero behavior change).
**Impact on plan:** No scope or behavior change beyond the required threshold field. Every one of the plan's own itemized test cases exists and passes; the two file splits (constants.py -> +config_keys.py, test_barriers.py -> +test_barriers_integration.py) are organizational, not scope creep.

## Issues Encountered

- The plan's own wording for the barrier-scoring metric ("how much placing it increases the thief's BFS distance to its best escape (equivalently, shrinks its reachable region)") does not correspond to any concrete, pre-existing "escape zone" concept in the game rules or prior Phase-3 code -- multiple candidate readings were considered (cop-thief distance directly, a flood-fill-derived farthest-reachable-cell, a fixed board corner) before settling on the fixed-corner anchor, specifically because `bfs()` was proven symmetric between the two agents in this codebase (ruling out the direct cop-thief-distance reading, which cannot discriminate a cop-favoring placement). This is recorded in `key-decisions` so 03-08's `reward_barrier_gain` shaping term (which needs a similar "did this barrier help" signal) doesn't have to re-derive the same reasoning.
- A real, non-hypothetical exploit was found and fixed before any test existed: the first working version of `choose_barrier`, run against a bare open-board scenario, returned the anchor cell itself as the "best" barrier -- because placing a barrier directly on the scoring reference point trivially makes it UNREACHABLE regardless of the thief's actual position. Caught via manual `uv run python -c ...` verification, fixed by excluding the anchor cell from candidates, and turned into a permanent regression test (`test_open_board_has_no_candidate_above_threshold`) before proceeding.
- No authentication gates, no architectural questions requiring a stop, no blockers.

## User Setup Required

None -- no external service configuration required.

## Next Phase Readiness

- 03-08 (offline training harness) can call `choose_barrier` directly if it wants a "did this placement help" signal for `training.reward_barrier_gain` shaping, reusing the same anchor/gain concept documented here rather than inventing a second one (QUAL-02).
- Both brains are now fully feature-complete for Phase 3's blind-play contract: movement (Q-table or fallback) plus a truthful, quota-respecting, engine-validated barrier decision, with zero LLM or network import reachable from the decision path (STRAT-07, unchanged from 03-02's structural guarantee).
- `src/pursuit/config_keys.py` is now the import path for `ConfigKey`/`NetworkConfigKey`/`StrategyKey`/`TrainingKey` for any future plan -- `pursuit.constants` no longer exports them.
- No blockers. `strategy.barrier_min_gain` is now a required key in `strategy.json`; any future hand-edited or generated config file missing it will fail loud via `load_strategy_config`, matching this project's fail-loud convention for every other hyperparameter.

---
*Phase: 03-blind-strategy-module-rl-policy*
*Completed: 2026-08-01*

## Self-Check: PASSED

All 20 claimed files confirmed present on disk (`src/pursuit/strategy/{barriers,heuristic,qlearning}.py`,
`src/pursuit/config_keys.py`, `src/pursuit/constants.py`, `src/pursuit/shared/{config,network_config,strategy_config}.py`,
`config/{police,thief}/strategy.json`, `tests/unit/strategy/{test_barriers,test_barriers_integration,test_strategy_config,test_heuristic,test_qlearning}.py`,
`tests/unit/test_network_config.py`, `docs/phases/phase-3/{PLAN,TODO}.md`, `.planning/graphs/GRAPH_REPORT.md`, this SUMMARY).
Both task commit hashes (`b91c08a`, `738eba9`) confirmed present in `git log --oneline --all`.
