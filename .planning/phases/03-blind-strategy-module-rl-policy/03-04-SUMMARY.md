---
phase: 03-blind-strategy-module-rl-policy
plan: "04"
subsystem: strategy
tags: [bayes-prior, bfs-fallback, heuristic-brain, strat-02, d-09, d-10, d-11, d-03]

# Dependency graph
requires:
  - phase: 03-02
    provides: BrainBase ABC, frozen Observation/Decision, MoveSource, build_brain registry mechanism
  - phase: 03-03
    provides: bfs(state, start, goal, agent, params) -> (distance, next_step), UNREACHABLE sentinel
provides:
  - src/pursuit/strategy/prior.py -- uniform()/spread()/argmax_cell(): Bayes PREDICTION step only, no evidence term (Phase-4 seam)
  - src/pursuit/strategy/fallback.py -- pick(obs, state, agent, params, prior=None) -> Decision, BFS-only distance (never Manhattan)
  - src/pursuit/strategy/heuristic.py -- HeuristicBrain(BrainBase), fully playable for both roles, no Q-table
  - registry.py's build_brain() now threads a required GameParams through to every brain constructor
affects: [03-05, 03-06, 03-07, 03-08, 03-10, "every later Phase-3 plan constructing or calling a brain"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Candidate-scoring fallback: enumerate sorted(get_legal_moves(...)) once, score each destination's BFS distance to the believed target via a (bool, int[, int]) tuple key, pick strict min/max -- ties always resolve to the first (smallest row,col) candidate, matching bfs()'s and prior.argmax_cell's own tie-break convention"
    - "Unreachable-as-best-for-the-evader: the thief's ranking key treats UNREACHABLE as strictly better than any finite distance (the cop can never arrive), while the cop's key treats it as strictly worse than any finite distance -- both derived from the same (distance == UNREACHABLE, distance[, onward]) tuple shape"
    - "GameParams injected once at brain-construction time (via build_brain), not per _pick_move call -- keeps BrainBase's frozen 03-02 ABC signature untouched while still giving every brain's internal fallback/BFS machinery the board_size it needs"

key-files:
  created:
    - src/pursuit/strategy/prior.py
    - src/pursuit/strategy/fallback.py
    - src/pursuit/strategy/heuristic.py
    - tests/unit/strategy/test_prior.py
    - tests/unit/strategy/test_fallback.py
    - tests/unit/strategy/test_heuristic.py
  modified:
    - src/pursuit/strategy/registry.py
    - tests/unit/strategy/test_registry.py
    - docs/phases/phase-3/PLAN.md
    - docs/phases/phase-3/TODO.md
    - .planning/graphs/GRAPH_REPORT.md

key-decisions:
  - "build_brain(role, params, game_params) now REQUIRES a GameParams argument (Rule 2/3 deviation, not optional/defaulted): every real brain's fallback/BFS machinery needs board_size for legal-move generation, BrainBase._pick_move/_decide_move (03-02) deliberately carry no GameParams, and orchestrator.py's already-frozen ChooseMove type confirms GameParams is meant to reach a brain per-turn -- injected once at construction instead of widening the tested ABC signature. _StubBrain and its 3 call sites in test_registry.py updated mechanically to match; no assertion changed"
  - "HeuristicBrain's own registration line lives in registry.py (imports HEURISTIC_BRAIN_NAME/HeuristicBrain and assigns _BRAIN_REGISTRY[...] there), not via heuristic.py reaching into registry's private dict from outside -- matches 03-02's own stated intent ('later plans add entries by editing this file directly') and avoids a needless cross-module mutation of a name prefixed private"
  - "Coord type alias for prior.py/fallback.py imported from pathfind.py (the module that first declared it) rather than redeclared, so there is exactly one canonical (row, col) alias across the phase"
  - "_MASS_TOLERANCE = 1e-9 is a module-level float in prior.py, categorized as a numerical-precision structural constant (like pathfind.py's UNREACHABLE=-1 sentinel), not a game value or RL hyperparameter under D-05/D-18 -- it never appears in a config file and is not a game/training number"
  - "spread() asserts the sum-to-1.0 invariant on BOTH entry and exit, not only exit, as a defensive guard against a caller-supplied prior that has already drifted -- the plan's own wording ('asserted as an invariant... after every update') requires the exit check; the entry check is an additional, low-risk safety net given the fallback runs every turn for up to 35 turns"
  - "HeuristicBrain's test build uses config/{police,thief}/strategy.json's REAL values with only brain_class swapped via dataclasses.replace (StrategyParams is frozen) to HEURISTIC_BRAIN_NAME -- config/police/strategy.json still names QLearningBrain (03-06 not landed), so this is the closest literal reading of the plan's 'builds via build_brain from config for both roles' available right now"

patterns-established:
  - "AST structural test for 'no class-level mutable state': walks the target class's ast.ClassDef.body and asserts no Assign/AnnAssign node exists directly in it -- reusable by 03-06's QLearningBrain to prove the same D-03 guarantee, following test_registry.py's existing AST-walk precedent rather than a runtime mutation probe (which cannot actually detect a shared class attribute, only reassignment)"

# Metrics
duration: ~35min (approximate -- PLAN_START_TIME was not captured at session start, see Issues Encountered)
completed: 2026-08-01
---

# Phase 3 Plan 04: Bayes Motion Prior + BFS Fallback + HeuristicBrain Summary

**A Bayes prediction-only prior (`prior.py`), a BFS-distance pursue/evade fallback (`fallback.py`) that never touches raw Manhattan, and `HeuristicBrain` -- a fully playable, Q-table-free baseline that plays a complete cop-vs-thief game to a terminal outcome and is registered as GATE-4's opponent.**

## Performance

- **Duration:** ~35 min (approximate)
- **Tasks:** 3 completed
- **Files modified:** 6 created, 5 modified

## Accomplishments
- `src/pursuit/strategy/prior.py` (56 code lines core logic + docstrings, well under 150): `uniform()`, `spread()` (the Bayes PREDICTION step only -- no evidence term, explicit Phase-4 seam in the module docstring), `argmax_cell()` with deterministic tie-breaking. Mass redistribution goes exclusively through `pursuit.shared.board.get_legal_moves` (QUAL-02) so barriers/bounds are honoured for free; the sum-to-1.0 invariant is asserted inside the function on both entry and exit, not spot-checked only in tests (D-10).
- `src/pursuit/strategy/fallback.py`: `pick(obs, state, agent, params, prior=None) -> Decision`, `source` always `MoveSource.FALLBACK`. Cop minimizes BFS distance to the believed target; thief maximizes it, tie-breaking toward more onward legal moves so cornering never looks like escaping. Distance never comes from anywhere but `pathfind.bfs()` (D-09) -- verified by re-using 03-03's exact barrier-pocket wall layout and asserting the fallback's chosen step equals `bfs()`'s own optimal next step for the cop, and differs from a naive Manhattan-greedy stepper for both roles. Unreachable targets always resolve to a legal move without raising (ranked worst for the cop, best for the thief).
- `src/pursuit/strategy/heuristic.py`: `HeuristicBrain(BrainBase)`, fully playable for both roles from turn 1 -- `_pick_move` delegates entirely to `fallback.pick()` (exactly one heuristic implementation in the codebase), `_decide_move` returns `barrier=None` with a `# 03-07` marker, every `Decision.source` is truthfully `MoveSource.HEURISTIC`. Instance attributes only (`_role`/`_params`/`_game_params`), no class-level or module-level mutable state, verified by an AST structural test (D-03, project rule 2). A full cop-vs-thief `HeuristicBrain` game through `sdk.engine` reaches a terminal outcome within `move_ceiling` turns (test-proven, not asserted by inspection).
- **Deviation, applied and documented (Rule 2/3):** `registry.build_brain()` now requires a `GameParams` argument, threaded to every brain constructor. `BrainBase._pick_move`/`_decide_move` (03-02) deliberately take no `GameParams`, but `HeuristicBrain`'s fallback/BFS internals need `board_size` for legal-move generation, and this project's own `ChooseMove` type in `orchestrator.py` (`Callable[[GameState, str, GameParams], tuple[int, int]]`) already establishes that `GameParams` reaches move-selection per turn -- so it is injected once at brain construction instead of widening the already-tested ABC call signature. `test_registry.py`'s `_StubBrain` and its 3 `build_brain` call sites were updated mechanically to match (no assertion changed, all 3 tests still pass green).
- Full repo gates green: `uv run ruff check .` -> 0 violations; `bash scripts/check_line_limit.sh` -> clean (all new/modified files, including `heuristic.py` at 20 statements and `prior.py`/`fallback.py` comfortably under 150 lines); `uv run pytest --cov=pursuit --cov=training -q` -> 235 passed, 97.31% coverage (`fallback.py`/`heuristic.py`/`registry.py` each 100%, `prior.py` 98%).
- Graphify graph rebuilt after this plan's new code (2349 nodes / 3543 edges / 181 communities); `.planning/graphs/GRAPH_REPORT.md` refreshed and staged for the metadata commit. `docs/phases/phase-3/PLAN.md`'s `build_brain` interface line and `docs/phases/phase-3/TODO.md` row 03-04 updated to reflect this plan's actual shipped contract.

## Task Commits

Each task was committed atomically:

1. **Task 1: Bayes motion-model prior** - `8c7ffd0` (feat)
2. **Task 2: Fallback policy -- BFS toward the believed target** - `1675772` (feat)
3. **Task 3: HeuristicBrain -- the playable baseline (+ registry GameParams deviation)** - `9e081db` (feat)

**Plan metadata:** (this commit, following SUMMARY/STATE update)

## Files Created/Modified
- `src/pursuit/strategy/prior.py` - `uniform`, `spread`, `argmax_cell`, `_probe_state`, `_normalize`, `_assert_normalized`
- `src/pursuit/strategy/fallback.py` - `pick`, `_pursue`, `_evade`, `_probe`, `_distance_from`
- `src/pursuit/strategy/heuristic.py` - `HeuristicBrain`, `HEURISTIC_BRAIN_NAME`
- `src/pursuit/strategy/registry.py` - `build_brain` gains a required `game_params` parameter; `_BRAIN_REGISTRY` now seeded with `HeuristicBrain`
- `tests/unit/strategy/test_prior.py` - 10 tests
- `tests/unit/strategy/test_fallback.py` - 8 tests
- `tests/unit/strategy/test_heuristic.py` - 5 tests
- `tests/unit/strategy/test_registry.py` - `_StubBrain` + 3 call sites updated for the new `game_params` argument
- `docs/phases/phase-3/PLAN.md` - `build_brain` interface line updated to the 3-argument signature
- `docs/phases/phase-3/TODO.md` - row 03-04 marked ☑
- `.planning/graphs/GRAPH_REPORT.md` - refreshed after this plan's new code

## Decisions Made
See `key-decisions` in frontmatter. In brief: `build_brain` gained a required `game_params` parameter (the plan's most significant deviation, fully documented above and in the frontmatter); `HeuristicBrain`'s registry entry lives in `registry.py` itself, not injected from `heuristic.py`; `Coord` is imported from `pathfind.py` everywhere rather than redeclared; `_MASS_TOLERANCE` is a structural float constant, not a game value; `spread()` checks the mass invariant on both entry and exit; the `HeuristicBrain` config-build test swaps `brain_class` on the real per-role `strategy.json` rather than fabricating a config file, since 03-06 has not registered `QLearningBrain` yet.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2/3 -- Missing critical functionality / blocking issue] `build_brain()` did not thread `GameParams` to brain constructors**
- **Found during:** Task 3 (`HeuristicBrain` -- the first plan to actually construct a brain that calls real board logic)
- **Issue:** `fallback.pick()` (and therefore `HeuristicBrain`) needs `GameParams.board_size` to call `get_legal_moves`/`bfs`, but `BrainBase._pick_move(self, obs, state)` (03-02, frozen and tested) takes no `GameParams`, and `registry.build_brain(role, params)` (03-02) only ever passed `role`/`params: StrategyParams` to a brain's constructor. Without a fix, `HeuristicBrain` could not be constructed with the board configuration it needs to function at all -- it is not a stub-able gap, it blocks Task 3 outright.
- **Fix:** Added a required `game_params: GameParams` parameter to `registry.build_brain()`, passed through as `brain_cls(role=role, params=params, game_params=game_params)`. Chose construction-time injection (not a per-call `_pick_move(obs, state, game_params)` signature change) so the already-tested 03-02 ABC contract stays untouched; this mirrors `orchestrator.py`'s own `ChooseMove` type, which already carries `GameParams` as a per-call argument at the network-integration seam, confirming `GameParams` availability at that boundary was always the intended design.
- **Files modified:** `src/pursuit/strategy/registry.py` (signature + `_BRAIN_REGISTRY` seeded with `HeuristicBrain`), `tests/unit/strategy/test_registry.py` (`_StubBrain.__init__` gained the same parameter; its 3 `build_brain` call sites pass the `default_params` fixture through) -- purely mechanical, no assertion changed.
- **Verification:** All 3 pre-existing `test_registry.py` tests still pass; full suite green (235 passed, 97.31% coverage); `docs/phases/phase-3/PLAN.md`'s interface table updated so the documented contract matches what shipped.
- **Committed in:** `9e081db` (Task 3 commit)

---

**Total deviations:** 1 auto-fixed (Rule 2/3 -- a genuine interface gap between two already-committed plans, not a matter of taste). No architectural change was made to `BrainBase` itself; the fix is additive and localized to `registry.py` plus a mechanical test update.
**Impact on plan:** `QLearningBrain` (03-06) must accept the same `role`/`params`/`game_params` keyword-only constructor shape `HeuristicBrain` now uses -- this is now the fixed calling convention for every brain in the registry, documented in `registry.py`'s own docstring and in `docs/phases/phase-3/PLAN.md`.

## Issues Encountered
- `PLAN_START_TIME` was not captured via a bash timestamp at the very start of this session (a process gap on my part, not a plan issue); duration above is an approximation based on commit clustering and elapsed wall-clock context, not a precise measurement. No functional impact.
- One `ruff` violation (`C420`, unnecessary dict comprehension in `prior.uniform()`) surfaced on the first `ruff check .` pass and was fixed immediately (`dict.fromkeys(unique_cells, mass)` instead of a comprehension) before any commit -- not a deviation requiring documentation under the Rule taxonomy (caught and fixed pre-commit, zero behavior change).

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- 03-05 (state encoding + Q-table JSON persistence) and 03-06 (`QLearningBrain`) can now import `fallback.pick()` directly for the `min_visits` fallback trigger, and must construct via the same `brain_cls(role=role, params=params, game_params=game_params)` convention `HeuristicBrain` establishes.
- 03-07 (cop barrier sub-policy) has a clear, marked seam: `HeuristicBrain._decide_move`'s `# 03-07` comment is the literal attachment point, and `fallback.py`'s per-candidate BFS-scoring pattern is directly reusable for scoring barrier placements.
- 03-08's training harness and 03-10's GATE-4 eval can use `HeuristicBrain` immediately as the baseline opponent -- it is proven to play a complete game to termination for both roles, not a stub.
- No blockers. The one open interface note: `config/{police,thief}/strategy.json` still name `pursuit.strategy.qlearning:QLearningBrain` (03-06 has not landed that class yet), so `HeuristicBrain` is not yet reachable through the *default* config-driven path -- only through an explicit `brain_class` override, exactly as this plan's own tests do. This is expected, not a gap: 03-06 is what finally makes both registry entries reachable by real config, and GATE-3 (03-10) will need to build against `HeuristicBrain` as an explicit `[strategy]` override to prove config-only swapping actually works between two *real* brains.

---
*Phase: 03-blind-strategy-module-rl-policy*
*Completed: 2026-08-01*

## Self-Check: PASSED

All 12 claimed files confirmed present on disk (`src/pursuit/strategy/{prior,fallback,heuristic,registry}.py`,
`tests/unit/strategy/{test_prior,test_fallback,test_heuristic,test_registry}.py`,
`docs/phases/phase-3/{PLAN,TODO}.md`, `.planning/graphs/GRAPH_REPORT.md`, this SUMMARY).
All 3 task commit hashes (`8c7ffd0`, `1675772`, `9e081db`) confirmed present in `git log --oneline --all`.
