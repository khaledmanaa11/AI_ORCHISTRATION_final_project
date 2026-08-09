---
phase: 04-language-and-scent
plan: "11"
subsystem: strategy
tags: [belief-map, bayesian-inference, belief-adapter, sampling, option-a, registry-wiring, d-43, d-48]

# Dependency graph
requires:
  - phase: 04-language-and-scent (plan 04-09)
    provides: >
      strategy/belief_hint.py's hint_likelihood(inference, reliability, board_size, config),
      strategy/reliability.py's Reliability(config), strategy/scent_check.py's contradicts()
      (not called by this plan -- reserved for 04-12), and strategy/belief.py's BeliefMap
      (observe_exact/predict/update/posterior/argmax/sample) from 04-05
provides:
  - "strategy/beliefadapter.py: BeliefAdapter -- wraps a BrainBase, owns a fresh BeliefMap +
    Reliability per game, and runs Figure 7's order every turn: observe -> predict ->
    update(scent) -> update(hint) -> sample -> decide, then substitutes the belief-sampled
    cell into a believed GameState (Option A) before calling the wrapped brain"
  - "strategy/registry.py: build_brain(role, params, game_params, *, belief_config=None,
    scent_model=None) -- returns a BeliefAdapter-wrapped brain when belief.enabled, the raw
    brain otherwise; existing 3-positional-argument callers are unaffected"
  - "shared/belief_toggle_config.py: BeliefToggleParams (enabled, seed) -- belief.json's new
    'belief' group; a null seed is not an error, registry.py derives and logs a fallback"
  - "Observation.target_cell is no longer vestigial: it is filled by a belief SAMPLE (D-43,
    not the Phase-3 docstring's 'argmax' guess) and, via the believed-state substitution,
    demonstrably changes the mover's Decision"
affects: [04-12-turn-pipeline-integration, 04-13-docs-and-rules-resolution, 04-14-gate-4-measurement]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "BeliefAdapter is composition, not inheritance: decide()'s inputs (Inference, ScentField,
      an explicit Regime-A/B known_cell signal) exceed BrainBase._decide_move(obs, state)'s
      contract, so it is a distinct public entry point, never a BrainBase subclass"
    - "Reliability is constructed INSIDE BeliefAdapter.__init__ (not by 04-12 as 04-09's carry-over
      F anticipated) and exposed as a public self.reliability attribute -- 04-12 calls
      .observe(score) on that SAME instance between decide() calls rather than building its own"
    - "known_cell: Coord | None is an explicit Regime-A/B signal, not inferred from state: state
      keeps carrying the engine's true joint position regardless of regime (rule 3's 'local
      truth' is a display-layer concern), so the regime has to be told, not derived"
    - "build_brain() extended with belief_config/scent_model as OPTIONAL keyword-only params
      (never required) -- the same function, not a second build_brain_with_belief() path, per
      the plan's own literal 'build_brain returns the adapter-wrapped brain' wording"

key-files:
  created:
    - src/pursuit/strategy/beliefadapter.py
    - src/pursuit/shared/belief_toggle_config.py
    - tests/unit/strategy/test_beliefadapter.py
    - tests/unit/test_belief_toggle_config.py
    - tests/integration/test_belief_policy.py
    - tests/integration/test_belief_policy_replay.py
  modified:
    - src/pursuit/strategy/base.py
    - src/pursuit/strategy/registry.py
    - src/pursuit/shared/belief_config.py
    - config/police/belief.json
    - config/thief/belief.json
    - tests/integration/conftest.py
    - tests/unit/strategy/test_registry.py

key-decisions:
  - "Option A (docs/phases/phase-3/PRD.md Sec8) shipped, not Option B: the belief-sampled cell
    substitutes the opponent's coordinate in a believed GameState via dataclasses.replace, so
    the UNCHANGED matrix mover (valuebrain.py/matrix.py/features.py/equilibrium.py -- git diff
    --stat on all four is empty) reasons over it exactly as it always has. Option B (expectation
    over the belief's whole support) was rejected because it multiplies the payoff-matrix
    expansion by the candidate-cell count against the same strategy.max_decision_ms=50ms budget
    Phase 3 measured as the per-turn cost driver (AC-6: 3.62ms cold / 2.14ms warm for a single
    matrix build) -- Option A stays cheap by construction, measured at max 4.99ms (cop) / 3.68ms
    (thief) per decision with belief fully enabled, comfortably inside the 50ms budget with the
    belief pipeline's own cost included"
  - "D-43 (sample, not argmax) is a DELIBERATE deviation from book Sec6.4's literal
    '(x_target,y_target) = argmax_s b(s)' -- the user's own prior decision, implemented here: a
    deterministic argmax target makes pursuit fully predictable to an opponent modelling our
    belief, and a one-counted-game league (rule 52) punishes exploitable determinism"
  - "known_cell: Coord | None added to decide()'s signature beyond the plan's literal prose
    (which showed decide(state, inference, opponent_field, rules) with no explicit regime
    signal): Regime A/B cannot be derived from state alone since state always carries the
    engine's true joint position (needed for resolve_turn regardless of blindness), so the
    'was this turn's Reveal integrable' question has to be told to the adapter explicitly, not
    inferred. rules is accepted but NOT read inside decide() -- the wrapped brain already
    carries its own negotiated ResolutionRules from construction, and this module may not touch
    valuebrain.py to thread a second copy through it; kept in the signature so a caller is
    never left guessing which rules governed a Decision"
  - "Reliability is constructed inside BeliefAdapter.__init__, not by 04-12 as 04-09's own
    carry-over F literally proposed ('04-12 is the intended owner of building one Reliability
    per opponent at handshake time') -- reconciled by 04-12 calling BeliefAdapter's own
    constructor (itself the natural 'handshake time' moment) rather than building Reliability
    separately; self.reliability is exposed publicly so 04-12 can still drive
    .observe(contradiction_score) on the SAME instance decide() reads from"
  - "Regime-A identity is proven with a boxed-in fixture (opponent surrounded by barriers on
    every orthogonal neighbour, only STAY legal), not a lucky RNG seed: spread() from a pure
    delta at a cell with one legal action returns another pure delta at the SAME cell for ANY
    draw, so equality holds deterministically rather than 'usually'"
  - "build_brain() gained belief_config/scent_model as OPTIONAL keyword-only parameters on the
    SAME function rather than a new build_brain_with_belief() -- existing 3-positional callers
    (test_strategy_pluggable.py) are unaffected by construction, not by convention"

patterns-established:
  - "A missing (null) seed in an engineering-default config group is never silently
    non-deterministic: the caller derives a documented fallback constant AND logs a warning
    (registry.py::_resolve_belief_seed) -- the replay viewer (rule 20) still needs the actual
    seed used to be discoverable, not merely 'some seed was used'"

requirements-completed: [LANG-05, STRAT-07]

# Metrics
duration: ~65min
completed: 2026-08-09
---

# Phase 4 Plan 11: BeliefAdapter Summary

**`BeliefAdapter` runs the book's Figure-7 belief order every turn and substitutes a belief-SAMPLED opponent cell (D-43, not argmax) into a believed `GameState` via `dataclasses.replace` (Option A) so the Phase-3 matrix mover reasons over it unchanged; `registry.build_brain()` wires it in behind a `belief.enabled` config flag, closing `Observation.target_cell`'s vestigial status with a measured decision time of 4.99ms (cop) / 3.68ms (thief) against the 50ms budget.**

## Performance

- **Duration:** ~65 min (approximate -- no precise session-start timestamp was captured;
  estimated from the reading, design and implementation performed)
- **Completed:** 2026-08-09T04:51:22+03:00 (final Task 3 commit)
- **Tasks:** 3 planned tasks, 3 commits (one per task)
- **Files modified:** 13 (6 created, 7 modified)

## Accomplishments

- `strategy/beliefadapter.py`'s `BeliefAdapter.decide()` runs the exact six/seven-step Figure 7
  order every turn -- `observe_exact` (Regime A) or a posterior-weighted `emit_opponent` sweep
  (Regime B) -> `predict` -> `scent_likelihood`+`update` -> `hint_likelihood`+`update` ->
  `sample` -- asserted by a spy across TWO consecutive turns, not just one.
- Two independently constructed `BeliefAdapter`s with the same seed reproduce byte-identical
  `Decision` sequences across a two-turn scripted game; a confident regional hint measurably
  changes the posterior versus `NO_EVIDENCE`'s exact all-zero no-op (belief_hint.py's own D-33
  guarantee), proving the hint-update step is not dead weight in the adapter's own pipeline.
- Option A's believed-state substitution (`dataclasses.replace(state, **{opponent_role:
  sampled_cell})`) is proven correct in BOTH regimes: Regime A's identity holds EXACTLY (not
  approximately) for a boxed-in opponent under any RNG draw; Regime B's substitution is proven
  to differ from the true state in the opponent's coordinate ONLY -- cop, barriers, quota and
  turn all pass through untouched.
- `registry.build_brain()` gained optional `belief_config`/`scent_model` keyword parameters:
  supplying both with `belief.enabled=true` wraps the constructed brain in a `BeliefAdapter`
  with a seeded `random.Random`; omitting either, or `enabled=false`, returns the identical raw
  brain Phase 3 shipped -- proven by type identity AND a byte-for-byte-identical scripted game
  against the truly-unwired path.
- `Observation.target_cell` is demonstrably no longer vestigial: the SAME true `GameState` with
  a DIFFERENT believed opponent cell produces a DIFFERENT `Decision` from `ValueSearchBrain` --
  closing the exact gap `docs/phases/phase-3/PRD.md` Sec8 flagged.
- Per-turn decision time with the full belief pipeline enabled, measured over a real 35-turn
  game: **cop max 4.99ms / mean ~1.9ms, thief max 4.99ms (typically ~3.5-4.6ms) / mean ~1.7ms**,
  against a `strategy.max_decision_ms=50ms` budget per role -- the belief layer's own cost
  (predict/update x2/sample plus two `ScentField` emissions) stays a small fraction of the
  budget even stacked on top of the matrix mover's own ~2-5ms.
- Two full seeded games (belief enabled) are byte-for-byte identical end to end -- outcome,
  final state AND the entire recorded action sequence.
- The recorded action sequence from a belief-driven game, replayed through `resolve_turn` alone
  (bypassing both brains entirely), reaches the identical outcome, state and
  `score_outcome()` result -- the belief layer decides moves, it never touches resolution.
- `git diff --stat` confirms zero changes to `valuebrain.py`, `matrix.py`, `features.py` and
  `equilibrium.py` across all three commits.
- Full repo suite: **1020 passed, 94.94% coverage** (floor 85%, up from the pre-plan baseline of
  1001 passed / 94.81%); `ruff check .` 0 violations; `scripts/check_line_limit.sh` and
  `scripts/check_no_llm_in_strategy.py` both clean. 100% coverage on every new/modified
  belief-related module (`beliefadapter.py`, `belief_toggle_config.py`, `registry.py`,
  `belief_config.py`).

## Task Commits

Each task was committed atomically:

1. **Task 1: the adapter and the per-turn order** - `34c1846` (feat) -- `beliefadapter.py`
   ships the full order pipeline but Task 1's own commit still calls the wrapped brain with the
   TRUE state (no substitution yet), matching the plan's own `<files>` tags showing
   `beliefadapter.py` touched by BOTH Task 1 and Task 2
2. **Task 2: believed-state substitution -- Option A, identity in Regime A** - `1bc293f` (feat)
   -- adds the `dataclasses.replace` substitution, updates `base.py`'s `Observation.target_cell`
   docstring (D-43), adds the Regime-A/B substitution tests
3. **Task 3: registry wiring and the seed** - `083206a` (feat) -- `belief.json`'s new `belief`
   group, `registry.build_brain()`'s optional belief kwargs, the integration test suite
   (`test_belief_policy.py` + `test_belief_policy_replay.py`), and coverage-closing unit tests

**Plan metadata:** commit follows this SUMMARY.

## Files Created/Modified

- `src/pursuit/strategy/beliefadapter.py` -- `BeliefAdapter(brain, role, game_params,
  belief_config, scent_model, rng)`, `.decide(state, inference, opponent_field, rules, *,
  known_cell=None) -> Decision`
- `src/pursuit/shared/belief_toggle_config.py` -- `BeliefToggleParams(enabled, seed)`,
  `require_bool`, `require_optional_int`
- `src/pursuit/strategy/base.py` -- `Observation.target_cell`'s docstring corrected: D-43
  overrides the Phase-3 "argmax" guess with a posterior sample
- `src/pursuit/strategy/registry.py` -- `build_brain(..., *, belief_config=None,
  scent_model=None)`, `_resolve_belief_seed(seed) -> int`
- `src/pursuit/shared/belief_config.py` -- new `belief` group (`enabled`, `seed`) parsed into
  `BeliefParams.belief`
- `config/police/belief.json`, `config/thief/belief.json` -- new byte-identical `belief` group
  (`enabled: true`, `seed: 20260809`)
- `tests/unit/strategy/test_beliefadapter.py` -- Figure-7 order spy, seeded reproducibility,
  hint-matters, Regime A/B substitution, invalid-role guard (6 tests)
- `tests/unit/test_belief_toggle_config.py` -- 6 tests for the new config group's error/derive
  paths
- `tests/unit/strategy/test_registry.py` -- 2 tests for `_resolve_belief_seed`
- `tests/integration/test_belief_policy.py` + `test_belief_policy_replay.py` -- registry-level
  proof: disabled reproduces Phase 3, target_cell non-vestigial, timing budget, seeded
  byte-identity, action-replay scoring (5 tests total)
- `tests/integration/conftest.py` -- new shared `belief_cfg`/`scent_model` fixtures (QUAL-02)

## Decisions Made

See `key-decisions` in the frontmatter for the full list with rationale. The two decisions worth
restating in prose:

1. **Option A, not Option B**, per `docs/phases/phase-3/PRD.md` Sec8's own cost argument,
   confirmed by measurement here (belief-enabled decisions stay under 5ms against the 50ms
   budget) rather than merely asserted.
2. **`decide()`'s signature gained an explicit `known_cell: Coord | None` keyword** beyond the
   plan's literal prose text, because Regime A/B cannot be read off `state` alone -- `state`
   always carries the engine's true joint position (needed for `resolve_turn` regardless of
   blindness), so "was this turn's Reveal integrable" has to be told to the adapter, not
   inferred from it.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `belief_config.py` extended, then trimmed back under 150 lines**
- **Found during:** Task 3, after adding the fourth (`belief`) config group on top of the
  existing three.
- **Issue:** The straightforward addition pushed `belief_config.py` to 153 code lines against
  the 150 ceiling.
- **Fix:** Split `BeliefToggleParams` + its two loader helpers (`require_bool`,
  `require_optional_int`) into a new `shared/belief_toggle_config.py`, mirroring the SAME
  precedent 04-09 already set with `reliability_config.py`/`hint_likelihood_config.py`. Trimmed
  two more docstring lines in `belief_config.py` for margin (149 lines final).
- **Files modified:** `src/pursuit/shared/belief_config.py`,
  `src/pursuit/shared/belief_toggle_config.py` (new)
- **Verification:** `scripts/check_line_limit.sh` clean; 100% coverage on both files.
- **Committed in:** `083206a` (Task 3 commit)

**2. [Rule 3 - Blocking] `tests/integration/test_belief_policy.py` split at the 150-line ceiling**
- **Found during:** Task 3, after writing all five integration tests in one file (170 code
  lines).
- **Issue:** Same ceiling as above.
- **Fix:** Split reproducibility (`test_two_seeded_games_are_byte_identical`) and action-replay
  scoring (`test_replaying_the_recorded_actions_scores_identically`) into a new
  `test_belief_policy_replay.py`, which imports `test_belief_policy.py`'s `play()` helper (a
  plain function, not a fixture) rather than duplicating the game loop. Also moved the shared
  `belief_cfg`/`scent_model` fixtures into `tests/integration/conftest.py` (QUAL-02: one shared
  fixture per §10.4 gate module) instead of redefining them per file, which incidentally
  resolved a `ruff F811` fixture-redefinition error the first cross-file-import attempt hit.
- **Files modified:** `tests/integration/test_belief_policy.py`,
  `tests/integration/test_belief_policy_replay.py` (new), `tests/integration/conftest.py`
- **Verification:** `scripts/check_line_limit.sh` clean (120/58/125 lines respectively); all 5
  tests pass; `ruff check` clean.
- **Committed in:** `083206a` (Task 3 commit)

**3. [Rule 2 - Missing coverage] Closed three new-code coverage gaps**
- **Found during:** Task 3, final `--cov --cov-report=term-missing` pass after Tasks 1-3 landed.
- **Issue:** `belief_toggle_config.py`'s error/derive paths (77%), `registry.py`'s
  `_resolve_belief_seed` null-seed branch (93%), and `BeliefAdapter`'s invalid-role guard (98%)
  had no direct test.
- **Fix:** Added `tests/unit/test_belief_toggle_config.py` (6 tests: missing group/key, wrong
  type for `enabled`/`seed`, and the `seed: null` accept-path), two tests in
  `tests/unit/strategy/test_registry.py` (`_resolve_belief_seed` given vs. derived-and-logged),
  and one test in `tests/unit/strategy/test_beliefadapter.py` (invalid role raises).
- **Files modified:** `tests/unit/test_belief_toggle_config.py` (new),
  `tests/unit/strategy/test_registry.py`, `tests/unit/strategy/test_beliefadapter.py`
- **Verification:** All three modules now 100% covered; full suite 1020 passed, 94.94% overall.
- **Committed in:** `083206a` (Task 3 commit)

---

**Total deviations:** 3 auto-fixed (2 line-limit splits, 1 missing-coverage close). All three
are mechanical consequences of the 150-line gate and a post-implementation coverage pass; none
changed a shipped function's signature, contract or behaviour. No scope creep.
**Impact on plan:** None on the shipped contracts (`BeliefAdapter.decide()`,
`build_brain(..., belief_config=, scent_model=)`, `BeliefToggleParams` all match the plan's
`must_haves` intent); only file organization and test coverage improved, always toward smaller,
single-purpose files and toward better error-path coverage.

## Issues Encountered

- **`tests/integration/test_beats_baseline.py`, which environment rule 4 and the plan's own
  verification item 4 both name as a file that "must still pass with belief.enabled=false,
  unmodified", does not exist anywhere in this codebase.** `git log --all` confirms it was
  deleted in commit `f3d9847` ("feat(03-21..24): the matrix-game mover replaces tabular
  Q-learning") during Phase 3's run-2 rebuild, before this session started, and has not existed
  since. This is a stale reference in the plan/environment text, not a regression this plan
  caused -- there is nothing to run or preserve. `tests/integration/test_strategy_pluggable.py`,
  the OTHER file verification item 4 names, is confirmed present, passing (7/7), and
  byte-for-byte unmodified by this plan (`git diff` against the commit before this session's
  first commit is empty for that file; its own git log's most recent touch is commit `589772a`,
  from a prior session).
- No other issues. The Regime-A "sample must equal the true cell" claim in the plan's own prose
  (Task 2) does not hold for an ARBITRARY position after one `predict()` spread (mass generally
  fans out across every legal destination); it holds EXACTLY for a position whose only legal
  action is STAY. The test fixture (`_boxed_state`, a corner cell walled in on both in-bounds
  neighbours) was constructed specifically to make the identity a structural guarantee under any
  RNG draw rather than a coincidence of one lucky seed -- documented in the test's own docstring
  and in `key-decisions` above so a future reader does not mistake the general case for the
  identity case.

## User Setup Required

None -- no external service configuration required.

## Next Phase Readiness

- **Plan 04-12** (turn-pipeline integration, wave 6) is the intended owner of: (a) calling
  `scent_check.contradicts()` then `reliability.observe(score)` on the SAME `BeliefAdapter
  .reliability` instance between `decide()` calls (04-09's carry-over F, now closed by
  construction rather than by a separate 04-12-owned `Reliability`); (b) reading
  `language_params.model["hint_word_limit"]` once and passing it into both `DecodeContext` and
  `BluffContext` (wave-3/4 carry-overs A/J, still open); (c) deciding what `known_cell` is each
  turn from the ACTUAL reveal machinery (this plan always passed the true opponent cell in its
  own tests, simulating "reveal always succeeds" -- 04-12 is where a genuinely missing/opaque
  reveal becomes `known_cell=None` for real); (d) constructing one `BeliefAdapter` per role per
  game at wiring/handshake time via `registry.build_brain(role, params, game_params,
  belief_config=..., scent_model=...)`, and one `ScentField` per role, both held for the game's
  duration and passed into `decide()` every turn.
- `docs/phases/phase-3/PRD.md` Sec8's design question is now closed in code, not just in docs:
  Option A shipped, measured, and its cost (well under the 50ms budget) is on record for 04-13's
  `PRD_belief_map.md` and 04-14's GATE-4 report to cite directly.
- No blockers identified for wave 6.

## Known Stubs

None -- every function shipped in this plan is fully wired (real belief math, real registry
wiring, real seeded RNG); nothing renders empty/placeholder data. `BeliefAdapter` never calls a
language model and imports nothing from `pursuit.services`/`pursuit.network` (confirmed by
`scripts/check_no_llm_in_strategy.py` and the existing `test_strategy_package_imports_no_networking`
structural test in `test_registry.py`).

---
*Phase: 04-language-and-scent*
*Completed: 2026-08-09*

## Self-Check: PASSED

- All 6 created files confirmed present on disk (`[ -f ]`): `beliefadapter.py`,
  `belief_toggle_config.py`, `test_beliefadapter.py`, `test_belief_toggle_config.py`,
  `test_belief_policy.py`, `test_belief_policy_replay.py`.
- All 7 modified files confirmed present: `base.py`, `registry.py`, `belief_config.py`, both
  `belief.json` role files, `tests/integration/conftest.py`, `tests/unit/strategy/test_registry.py`.
- All 3 task commit hashes (`34c1846`, `1bc293f`, `083206a`) confirmed present in
  `git log --oneline --all`.
- Full repo suite re-run clean at SUMMARY time: 1020 passed, 94.94% coverage (gate >= 85%);
  `uv run ruff check .`, `bash scripts/check_line_limit.sh` (repo-wide), and
  `uv run python scripts/check_no_llm_in_strategy.py` all exit clean.
- `git diff --stat` on `valuebrain.py`/`matrix.py`/`features.py`/`equilibrium.py` confirmed
  empty across all three task commits.
- 100% line coverage confirmed individually on all new/modified belief-related modules
  (`beliefadapter.py`, `belief_toggle_config.py`, `registry.py`, `belief_config.py`).
