---
phase: 03-blind-strategy-module-rl-policy
plan: "06"
subsystem: strategy
tags: [q-learning, epsilon-greedy, min-visits-trigger, decision-provenance, strat-01, strat-02, strat-07, d-08, d-19, d-03]

# Dependency graph
requires:
  - phase: 03-02
    provides: BrainBase ABC, frozen Observation/Decision, MoveSource, build_brain(role, params, game_params) registry convention
  - phase: 03-04
    provides: fallback.pick(obs, state, agent, game_params) -> Decision (BFS-only, never Manhattan)
  - phase: 03-05
    provides: encode_state(obs, params, game_params) -> str, QTable.get/set/bump_visit/visits/best_action/save/load
provides:
  - src/pursuit/strategy/qlearning.py -- QLearningBrain(BrainBase): table-loaded-once construction, min_visits routing (STRAT-02), e-greedy selection over legal actions (D-19), truthful Decision.source (E2/E3), update() applying the PRD Sec5 Q-rule
  - registry.py's _BRAIN_REGISTRY now carries both playable brains -- QLearningBrain reachable by the default config brain_class string with zero code changes
affects: [03-07, 03-08, 03-10, "every later Phase-3 plan constructing or training a QLearningBrain"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "epsilon as a mutable per-instance attribute (not a constructor arg): __init__ sets self.epsilon = params.epsilon_eval so registry.build_brain's fixed 3-argument call still produces a correctly-greedy match/eval brain; 03-08's training loop reassigns brain.epsilon per episode from its own decaying schedule without touching the constructor signature every other brain in the registry shares"
    - "rng is an optional keyword-only constructor arg defaulting to an unseeded random.Random() -- keeps QLearningBrain constructible through build_brain(role, params, game_params) unchanged, while 03-08's training harness (or a test) injects random.Random(seed) directly for reproducibility (D-19)"
    - "Exploration is restricted to the currently legal action set (PRD Sec5's literal wording); the greedy/argmax branch is NOT masked by legality -- a deliberate asymmetry matching the PRD verbatim, since the state key already conditions on blocked_mask and any legal-move guardrail belongs to the AI-SPEC Sec6 online-guardrail table, which no plan in this outline (03-06..03-10) currently owns"
    - "Shared, non-collected test helper module (tests/unit/strategy/_qlearning_fixtures.py) reused across two split test files, following the tests/unit/_fakes_agent.py precedent, instead of a conftest.py fixture (helpers are called directly with per-test arguments, not injected)"

key-files:
  created:
    - src/pursuit/strategy/qlearning.py
    - tests/unit/strategy/_qlearning_fixtures.py
    - tests/unit/strategy/test_qlearning.py
    - tests/unit/strategy/test_qlearning_learning.py
  modified:
    - src/pursuit/strategy/registry.py
    - docs/phases/phase-3/TODO.md
    - .planning/graphs/GRAPH_REPORT.md

key-decisions:
  - "QLearningBrain.__init__(*, role, params, game_params, rng=None) -- rng is optional and keyword-only so build_brain(role, params, game_params) (the fixed 03-04 convention) constructs a working, unseeded-but-functional brain without modification; 03-08's harness supplies a seeded random.Random(training.seed) by constructing QLearningBrain directly rather than through the registry"
  - "self.epsilon is set from params.epsilon_eval at construction and left as a plain mutable instance attribute (not read from config on every decision) -- 03-08 reassigns it once per episode from its own alpha/epsilon decay schedule; this keeps _pick_move's signature untouched and keeps the decaying-schedule arithmetic entirely inside the training harness, not the brain"
  - "The QTable is loaded exactly once, in __init__, via QTable.load() -- which already fails loud (FileNotFoundError / ValueError) on a missing or corrupt table via 03-05's load_json_with_fallback; no additional try/except was added here, since silently catching that error would be exactly the failure mode (a shipped agent quietly playing random) the plan explicitly forbids"
  - "Exploration draws uniformly from get_legal_moves(state, role, game_params) (PRD Sec5: 'a uniformly random legal action'); the greedy table.best_action(key) branch is used as-is with no additional legal-move filter, matching the PRD's literal asymmetry -- masking the greedy branch is an AI-SPEC Sec6 online guardrail ('Legal-move filter'), a distinct future concern with its own guard_flags telemetry that no plan in 03-06..03-10 currently owns; adding it here would be scope creation beyond this plan's own <task> text"
  - "Both exploring and exploiting inside the visited region set Decision.source = MoveSource.QTABLE (per the plan's own literal task description) -- exploration is the policy trying an alternative inside its own trained region, not a delegation to the heuristic fallback, which is why it is provenance-distinct from FALLBACK"

patterns-established:
  - "AST structural test for 'no class-level mutable state' reused verbatim from 03-04's HeuristicBrain precedent, applied to QLearningBrain -- the same technique is available to 03-07's barrier sub-policy brain code"

# Metrics
duration: ~20min
completed: 2026-08-01
---

# Phase 3 Plan 06: QLearningBrain Summary

**The phase's headline brain: a table-backed epsilon-greedy Q-policy that loads its per-role Q-table once at construction, routes on a visit-count threshold rather than key presence (closing AI-SPEC failure mode 2), and tags every decision with truthful provenance for E2/E3.**

## Performance

- **Duration:** ~20 min
- **Tasks:** 2 completed
- **Files modified:** 4 created, 3 modified

## Accomplishments

- `src/pursuit/strategy/qlearning.py`: `QLearningBrain(BrainBase)` -- `_pick_move` encodes the observation via 03-05's `encode_state`, routes to `fallback.pick()` (`source=FALLBACK`) whenever `table.visits(key) < params.min_visits` (D-08, STRAT-02's real trigger, not mere key presence), otherwise either explores a uniformly random **legal** action via an injected seeded `random.Random` or takes `table.best_action(key)` -- both tagged `source=QTABLE`, matching the PRD's own asymmetry (exploration is legality-filtered per PRD Sec5's literal wording; the greedy branch is not, by design). `update(prev_key, action, reward, next_key)` applies `Q += alpha * (r + gamma * max_a' Q[s',a'] - Q)` exactly and bumps the visit count, as a plain method 03-08's training loop can call directly. The table loads exactly once, in `__init__`; `_pick_move` performs zero file I/O, verified by poisoning `builtins.open` after construction and confirming the decision still succeeds (E11).
- `registry.py`: `QLEARNING_BRAIN_NAME` (`"pursuit.strategy.qlearning:QLearningBrain"`) registered in `_BRAIN_REGISTRY` -- this string already matches `config/{police,thief}/strategy.json`'s `police_class`/`thief_class` values from 03-00, so both roles are now reachable through the *default*, unmodified config path with zero code changes (closing the gap 03-04's SUMMARY flagged as "expected, not a gap").
- The `min_visits` trigger boundary is swept explicitly from 0 through `min_visits + 2` (23 parametrized cases against the real config value of 20), each asserting the exact expected `Decision.source`. A falsification check was run and reverted per the plan's own `<verify>` instruction: temporarily weakening the trigger from `visits < min_visits` to a constant `< 0` (equivalent to "always trust the table") made 23 of the boundary/threshold tests fail immediately, proving the test suite actually discriminates the correct trigger from the naive one before the change was reverted (`git diff` confirms zero net change to `qlearning.py`).
- Exploration reproducibility is proven directly: two brains built with `random.Random(7)` produce an identical 20-decision move sequence; a third with `random.Random(99)` diverges (D-19). `epsilon_eval = 0.0` from the real per-role config is proven never to explore across 200 decisions (deterministic, greedy shipped play). Two `QLearningBrain` instances (one cop, one thief, each loading its own tmp-file table) are proven to hold disjoint `QTable` objects -- mutating one never touches the other (D-03, project rule 2), reinforced by an AST structural test (no `Assign`/`AnnAssign` in the class body) reusing 03-04's exact `HeuristicBrain` technique.
- Full repo gates green: `uv run ruff check .` -> 0 violations; `bash scripts/check_line_limit.sh` -> clean across all touched files (the 150-line gate forced one deliberate split, see Deviations); `uv run pytest --cov=pursuit --cov=training -q` -> 296 passed, 97.69% coverage overall, `qlearning.py` itself at **100%** coverage.
- Graphify graph rebuilt after this plan's new code (2551 nodes / 4087 edges / 187 communities); `.planning/graphs/GRAPH_REPORT.md` refreshed and staged for the metadata commit. `docs/phases/phase-3/TODO.md` row 03-06 marked done.

## Task Commits

Each task was committed atomically:

1. **Task 1: QLearningBrain -- selection, trigger, and provenance** - `6ac63f8` (feat)
2. **Task 2: The tests that make E2 and E3 real** - `846eeae` (test)

**Plan metadata:** (this commit, following SUMMARY/STATE update)

## Files Created/Modified

- `src/pursuit/strategy/qlearning.py` -- `QLearningBrain`, `QLEARNING_BRAIN_NAME`
- `src/pursuit/strategy/registry.py` -- `_BRAIN_REGISTRY` now seeded with `QLearningBrain` alongside `HeuristicBrain`
- `tests/unit/strategy/_qlearning_fixtures.py` -- shared, non-collected helper module (`params_for`, `make_obs`, `make_state`, `seeded_table`, `MIN_VISITS`)
- `tests/unit/strategy/test_qlearning.py` -- config wiring, the `min_visits` trigger boundary (0..min_visits+2), decision provenance, `_decide_move`'s `barrier=None` marker (9 tests)
- `tests/unit/strategy/test_qlearning_learning.py` -- exploration seeding/divergence, greedy-at-eval, the Q-update rule, no-I/O-on-decision-path, role isolation, AST no-mutable-state (7 tests)
- `docs/phases/phase-3/TODO.md` -- row 03-06 marked ☑
- `.planning/graphs/GRAPH_REPORT.md` -- refreshed after this plan's new code

## Decisions Made Autonomously

See `key-decisions` in frontmatter. In brief, since the user was unavailable for this unattended run:

- `rng` is an optional keyword-only constructor argument defaulting to an unseeded `random.Random()`, so `build_brain(role, params, game_params)` -- the fixed 3-argument convention every brain in the registry shares -- still constructs a working `QLearningBrain` unmodified; 03-08's training harness is expected to construct `QLearningBrain` directly (not through the registry) when it needs a seeded RNG.
- `epsilon` is a plain mutable instance attribute initialized from `params.epsilon_eval`, not re-read from config per decision -- 03-08 reassigns it once per episode from its own decaying schedule, keeping the decay arithmetic out of the brain entirely.
- The greedy/argmax branch is **not** filtered by current legal-move status, matching the PRD's own literal asymmetry (only exploration is explicitly "a uniformly random **legal** action" in PRD Sec5); a legal-move guardrail on the greedy branch is AI-SPEC Sec6's distinct "Legal-move filter" online guardrail, which carries its own `guard_flags` telemetry contract that no plan from 03-06 through 03-10 currently owns -- adding it here would be scope creation beyond this plan's literal task text, and until 03-08 trains a real table the greedy branch is rarely exercised (an empty/undertrained table almost always routes through the always-legal fallback).
- Both the explore and exploit paths inside the visited region tag `Decision.source = MoveSource.QTABLE`, per the plan's own literal task description -- exploration is the policy trying an alternative inside its own trained region, not a delegation to the heuristic.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `tests/unit/strategy/test_qlearning.py` hit 174 code lines against the 150-line gate**
- **Found during:** Task 2, after writing the full set of tests the plan's own `<action>`/`<verify>` list requires (9 itemized cases plus the config-build and `_decide_move` provenance tests).
- **Issue:** `bash scripts/check_line_limit.sh` failed on the single combined file.
- **Fix:** Split along the same conceptual seam 03-05 already used for `test_qtable.py`/`test_qtable_durability.py`: `test_qlearning.py` keeps config wiring + the `min_visits` trigger/provenance tests; `test_qlearning_learning.py` keeps exploration, the update rule, I/O isolation, and role isolation. A third, non-collected helper module (`_qlearning_fixtures.py`, no `test_` prefix, following the existing `tests/unit/_fakes_agent.py` precedent) was extracted so neither test file duplicates the same `params_for`/`make_obs`/`make_state`/`seeded_table` construction code (QUAL-02). No test was weakened, removed, or compressed.
- **Files modified:** `tests/unit/strategy/test_qlearning.py` (trimmed), `tests/unit/strategy/test_qlearning_learning.py` (new), `tests/unit/strategy/_qlearning_fixtures.py` (new).
- **Verification:** `bash scripts/check_line_limit.sh` -> clean across all four touched files; `uv run pytest tests/unit/strategy/test_qlearning.py tests/unit/strategy/test_qlearning_learning.py -q` -> 34 passed; full repo suite 296 passed, coverage 97.69%.
- **Committed in:** `6ac63f8` (Task 1 commit carries `test_qlearning.py` + the fixtures module; `846eeae` (Task 2 commit) carries `test_qlearning_learning.py`) -- the split happened before either commit, so both files landed as the intended shape from the start.

**2. [Rule 2 - Missing critical functionality] `_decide_move`'s `barrier=None` marker line was uncovered (93% on qlearning.py)**
- **Found during:** Task 2, running `--cov-report=term-missing` on the new module after the plan's own 9 itemized tests all passed.
- **Issue:** `BrainBase._decide_move` is an abstract method every brain must implement, and `HeuristicBrain` has a dedicated test proving its own `barrier=None` marker (`test_every_decision_carries_heuristic_source`); `QLearningBrain`'s equivalent was implemented but never directly exercised, leaving the 03-07 attachment seam untested.
- **Fix:** Added `test_decide_move_attaches_no_barrier_yet` to `test_qlearning.py`, mirroring `HeuristicBrain`'s own coverage of the identical D-12 placeholder.
- **Files modified:** `tests/unit/strategy/test_qlearning.py`.
- **Verification:** `qlearning.py` reaches 100% coverage; `bash scripts/check_line_limit.sh` still clean after the addition (71 code lines, well under 150).
- **Committed in:** `6ac63f8` (Task 1 commit -- the test was added before that commit was made, so it landed as part of the intended shape).

---

**Total deviations:** 2 auto-fixed (1 Rule 3 -- a repeat of an already-established blocking pattern from 03-05; 1 Rule 2 -- a genuine coverage gap on a required ABC method, closed the same way `HeuristicBrain` already closes it).
**Impact on plan:** No scope or behavior change. The plan named one test file; the split is a file-organization deviation, and every one of the plan's own 9 itemized test cases (plus the config-build test) still exists and passes. The added `_decide_move` test closes a coverage gap without touching `qlearning.py`'s implementation.

## Issues Encountered

- The plan's `<read_first>` for Task 1 lists `docs/PRD_rl_strategy.md` as authoritative for the update rule and fallback trigger; that document also documents an intentional PRD-level asymmetry (exploration is legality-filtered, the greedy argmax branch is not) that is easy to over-correct in code. Resolved by implementing the PRD's literal wording exactly rather than adding an unrequested legal-move guard on the greedy branch, and recording the reasoning in `key-decisions` so 03-07/03-08 don't have to re-derive it.
- No authentication gates, no architectural questions, no blockers.

## User Setup Required

None -- no external service configuration required.

## Next Phase Readiness

- 03-07 (cop barrier sub-policy) attaches at the `# 03-07` marker inside `QLearningBrain._decide_move`, exactly where `HeuristicBrain`'s own marker already sits -- the two brains now share an identical two-stage decision shape.
- 03-08 (offline training harness) can construct `QLearningBrain` directly with an injected `random.Random(training.seed)`, drive `update(prev_key, action, reward, next_key)` per environment step, and reassign `brain.epsilon`/read `brain._params.alpha` per its own decaying schedule -- no constructor or method signature changes are anticipated.
- Both roles are now reachable through the **default**, unmodified `config/{police,thief}/strategy.json` (`police_class`/`thief_class` already named `pursuit.strategy.qlearning:QLearningBrain` since 03-00) -- 03-10's GATE-3 config-only-swap test can now toggle between two *real* brains without any override, closing the note 03-04's SUMMARY left open.
- No blockers. `artifacts/qtable_{police,thief}.json` do not exist yet -- constructing `QLearningBrain` via the real config as-is will fail loud (by design, per this plan's own requirement) until 03-08 trains and ships a table; every test in this plan builds its own tmp-path table via `dataclasses.replace(qtable_path=...)`, matching the pattern 03-04 established for `HeuristicBrain`'s config-driven test.

---
*Phase: 03-blind-strategy-module-rl-policy*
*Completed: 2026-08-01*

## Self-Check: PASSED

All 7 claimed files confirmed present on disk (`src/pursuit/strategy/{qlearning,registry}.py`,
`tests/unit/strategy/{_qlearning_fixtures,test_qlearning,test_qlearning_learning}.py`,
`docs/phases/phase-3/TODO.md`, `.planning/graphs/GRAPH_REPORT.md`, this SUMMARY).
Both task commit hashes (`6ac63f8`, `846eeae`) confirmed present in `git log --oneline --all`.
