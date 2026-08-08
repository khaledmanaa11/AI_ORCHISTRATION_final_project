---
phase: 04-language-and-scent
plan: "05"
subsystem: strategy
tags: [belief-map, bayesian-inference, scent-likelihood, probability-grid, dec-pomdp, random-walk, config-loader]

# Dependency graph
requires:
  - phase: 04-language-and-scent (plan 04-01)
    provides: >
      strategy/scent.py's expected_strength_after() (the decay law's closed form, D-42's
      inversion target), strategy/scentfield.py's ScentField (opponent trail reader), and
      shared/scent_config.py's ScentModel (source/decay/window)
provides:
  - "strategy/belief.py: BeliefMap -- a dense board_size x board_size posterior over one
    role's cell, with observe_exact/predict/update/posterior/argmax/sample(rng), three
    invariants defended in code (non-negative + sums to 1, degenerate update leaves the
    prior unchanged, barrier cells never carry mass)"
  - "strategy/belief_motion.py: spread(prior, role, state, params, action_weights=None) --
    the legal-motion model both predict() and belief_scent.py's projection step share"
  - "strategy/belief_scent.py: scent_likelihood(opponent_field, role, state, params, model,
    config) -> Grid -- the D-42 scent-evidence likelihood, never chasing the strongest cell"
  - "shared/belief_config.py + config/{police,thief}/belief.json: the scent_likelihood
    engineering-default group (weight, epsilon, age_cap, freshness_decay)"
affects: [04-09-belief-fusion, 04-11-belief-adapter, any later plan reading a BeliefMap or a scent_likelihood Grid]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "BeliefMap is a MUTABLE @dataclass (like ScentField), not a frozen one: predict/
      update/observe_exact advance state in place across a live game"
    - "Grid = list[list[float]] is dense and boring by design (Task 1 instruction) --
      board_size**2 floats, no sparse dict, unlike ScentField's dict-backed trails"
    - "belief_config.py follows the ScentKey/LanguageKey precedent: BeliefKey lives beside
      its own loader, not in pursuit.config_keys (already at its 150-line ceiling)"
    - "sample(rng) reuses strategy/equilibrium.py's sample(strategy, draw) over a flattened
      grid rather than re-implementing cumulative-distribution sampling a second time"

key-files:
  created:
    - src/pursuit/strategy/belief.py
    - src/pursuit/strategy/belief_motion.py
    - src/pursuit/strategy/belief_scent.py
    - src/pursuit/shared/belief_config.py
    - config/police/belief.json
    - config/thief/belief.json
    - tests/unit/strategy/test_belief.py
    - tests/unit/strategy/test_belief_motion.py
    - tests/unit/strategy/test_belief_scent.py
    - tests/unit/test_belief_config.py
  modified: []

key-decisions:
  - "scent_likelihood() reads the trail's SINGLE freshest cell (ScentField.freshest), not
    every cell above epsilon independently -- an initial per-cell multi-bucket design was
    built first, found (via interactive numerical verification, before any test was
    written) to leave a symmetric interior deposit's argmax AT the deposit forever, for
    every k >= 1, because spread()'s legal action set always includes STAY and a lazy
    symmetric random walk keeps its mode at the origin indefinitely -- see Deviations"
  - "age >= 1 drops the deposit cell's own projected weight before it enters the
    likelihood -- the same symmetric-random-walk property applies to a single projected
    point too, so without this the single-peak redesign alone still failed the decisive
    test at the board's exact centre; a stale reading is itself evidence against 'stayed
    put', since continued occupancy would keep re-emitting at full strength"
  - "predict()'s second parameter is typed GameParams (named params), not a literal `rules:
    ResolutionRules` -- the plan's prose says predict(state, rules) but
    thief_actions/cop_actions/barrier_cells only ever need GameParams; naming it `rules`
    would collide with this codebase's own strict params=GameParams / rules=ResolutionRules
    convention (resolve.py, matrix.py, valuebrain.py) for no real benefit"
  - "Task 2 (belief_motion.py) committed before Task 1 (belief.py) -- belief.py imports
    spread()/Grid/Coord/ROLES from belief_motion.py, so committing Task 1 first would leave
    an intermediate commit whose tests cannot even import. Both tasks' CONTENT matches the
    plan; only the commit sequence changed"

requirements-completed: [LANG-05]

# Metrics
duration: ~50min
completed: 2026-08-08
---

# Phase 4 Plan 05: Belief Map Core Summary

**BeliefMap (predict/update/observe_exact/argmax/sample over a dense probability grid) plus a shared legal-motion model and a D-42 scent-likelihood that reads a trail's single freshest cell, inverts its age, and projects it forward while explicitly discounting the walk's own self-renewal bias -- fixing a symmetric-random-walk property that would otherwise keep the belief pinned to the deposit cell forever.**

## Performance

- **Duration:** ~50 min
- **Completed:** 2026-08-08T22:33Z
- **Tasks:** 3 planned tasks, 3 commits (one per task; see Decisions for the execution-order note)
- **Files modified:** 10 (10 created, 0 modified)

## Accomplishments

- `BeliefMap` (`src/pursuit/strategy/belief.py`) is a proper probability distribution end to
  end: constructor seeds uniform, and `observe_exact`/`predict`/`update` each leave the grid
  non-negative and summing to 1 (verified by a seeded random predict/update sequence, not just
  the individual operations in isolation).
- `spread()` (`src/pursuit/strategy/belief_motion.py`) advances mass through the SAME
  `sdk/actions.py` legal-action sets the engine plays with -- verified exactly: an interior
  thief spreads to exactly 5 cells at 0.2 each, a cop's 5 barrier placements collapse onto its
  own cell alongside the move-to-self (6/10 stay, 1/10 each neighbour), and a documented
  `action_weights` seam is wired and tested without being used in production.
- `scent_likelihood()` (`src/pursuit/strategy/belief_scent.py`) passes the decisive D-42 test
  --argmax(posterior) != the deposit cell after a stale reading -- for **all four** tested
  starting cells: the board's exact centre, a corner, an edge-adjacent cell, and an interior
  off-centre cell, at k = 1..10 turns. The first (per-cell bucket) design passed only the
  off-centre cases; see Deviations for why and how it was fixed.
- Both regimes are exercised on the SAME `BeliefMap` object: Regime A
  (`observe_exact` then `predict` reproduces exactly the legal successor set) and Regime B (10
  joint turns with zero `observe_exact` calls, fed only by scent, staying a valid distribution
  throughout, diffusing without evidence, and re-concentrating when a fresh trail appears).
- `belief.json`'s four numbers (scent weight, epsilon, age cap, freshness decay) are fail-loud
  validated engineering defaults, explicitly documented as NOT `docs/PARAMETERS.md` values
  (`age_cap >= 1` is enforced specifically because `age_cap = 0` would degenerate back into
  chasing the strongest cell directly -- the exact D-42 failure mode).
- 100% line coverage on all four new source modules; repo-wide suite: 571 passed, 93.22%
  coverage (gate: >= 85%); `ruff check .`, `check_line_limit.sh` (repo-wide), and
  `check_no_llm_in_strategy.py` all clean; `grep -rn "pursuit.network" src/pursuit/strategy/belief*.py`
  empty.

## Task Commits

Each task was committed atomically. Commit ORDER differs from task-number order (Task 2
before Task 1) because `belief.py` imports from `belief_motion.py` -- see Decisions.

1. **Task 2: the motion model** - `b3773ac` (feat) -- `strategy/belief_motion.py`, `tests/unit/strategy/test_belief_motion.py`
2. **Task 1: the BeliefMap object and its invariants** - `f6ced38` (feat) -- `strategy/belief.py`, `tests/unit/strategy/test_belief.py`
3. **Task 3: the scent likelihood (D-42)** - `2163b29` (feat) -- `strategy/belief_scent.py`, `shared/belief_config.py`, `config/{police,thief}/belief.json`, `tests/unit/strategy/test_belief_scent.py`, `tests/unit/test_belief_config.py`

## Files Created/Modified

- `src/pursuit/strategy/belief.py` -- `BeliefMap`: `observe_exact(cell)`, `predict(state, params)`, `update(likelihood)`, `posterior()`, `argmax()`, `sample(rng)`
- `src/pursuit/strategy/belief_motion.py` -- `spread(prior, role, state, params, action_weights=None) -> Grid`, `Coord`, `Grid`, `ROLES`
- `src/pursuit/strategy/belief_scent.py` -- `scent_likelihood(opponent_field, role, state, params, model, config) -> Grid`, `inverted_age(strength, model, age_cap) -> int`
- `src/pursuit/shared/belief_config.py` -- `BeliefKey`, `BeliefParams`, `load_belief_config(path)`
- `config/police/belief.json`, `config/thief/belief.json` -- byte-identical `scent_likelihood` engineering defaults
- `tests/unit/strategy/test_belief.py`, `test_belief_motion.py`, `test_belief_scent.py`, `tests/unit/test_belief_config.py` -- 67 new tests total

## The API contract 04-09 and 04-11 code against

**`BeliefMap(board_size: int, role: str)`** -- `role` is `"cop"` or `"thief"` (whichever the
*opponent* is, from the caller's own seat): matches `GameState`'s own field names, since
`predict()` hypothesises `role` at each credited cell via `dataclasses.replace(state, **{role: cell})`.

- `observe_exact(cell: tuple[int, int]) -> None` -- collapse to a delta; raises `ValueError` if `cell` is off-board.
- `predict(state: GameState, params: GameParams) -> None` -- one joint turn of legal-motion diffusion; barrier-safe.
- `update(likelihood: Grid) -> None` -- pointwise multiply + renormalise; an all-zero-product likelihood is a no-op.
- `posterior() -> tuple[tuple[float, ...], ...]` -- immutable snapshot, `board_size` rows.
- `argmax() -> tuple[int, int]` -- row-major tie-break.
- `sample(rng: random.Random) -> tuple[int, int]` -- proportional draw; never touches the module RNG or `secrets`.

**`scent_likelihood(opponent_field: ScentField, role: str, state: GameState, params: GameParams, model: ScentModel, config: BeliefParams) -> Grid`**
-- every cell defaults to **1.0** (neutral: "explains nothing", not zero). Callers pass this
straight into `BeliefMap.update()`. A `Grid` is `list[list[float]]`, `board_size` rows of
`board_size` floats, dense (every cell always present, never a sparse dict like `ScentField`'s
own trails).

## Decisions Made

**The scent-likelihood algorithm was redesigned once, before any test was written, after
interactive numerical verification exposed a real correctness gap in the first reading of
Task 3's prose.** Task 3's `<action>` describes inverting "a measured strength τ at a cell"
into an age and projecting it forward. Read literally per-cell, the first implementation built
one age-bucket per cell whose strength was >= epsilon (the whole kernel footprint around a
deposit, since `emission()` writes a 5x5 neighbourhood, not a single point) and spread each
bucket forward independently. Manually verifying the plan's own "decisive test" against this
implementation (`python -c` probes, not yet pytest) showed the posterior's argmax stayed AT
the deposit cell **indefinitely** for the board's exact centre `(3,3)` -- at k=1 through k=15,
never moving away. Root cause, confirmed by an isolated probe script: `spread()`'s legal action
set always includes STAY, so a symmetric point mass diffusing through repeated `spread()` calls
is a "lazy random walk" whose single highest-probability cell remains the origin forever (a
textbook, not incidental, property of symmetric random walks -- confirmed to hold even for a
"must-move" variant with STAY excluded, just at even step-counts instead of every step). Since
`(3,3)` is literally the thief's actual starting position (`game_params.json`), this was not a
theoretical corner case.

Two changes fixed it, verified numerically across four starting cells (centre, corner, edge,
off-centre interior) and k=1..10 before being written into any test:

1. **Read the trail through its single freshest cell** (`ScentField.freshest`), not every
   cell above epsilon independently -- matching the book's own "the opponent was HERE (singular)
   N turns ago" framing more literally, and avoiding a ring of same-capped-age cells whose
   independently-projected contributions were reconverging on the centre by symmetry.
2. **Drop the deposit cell's own projected weight once age >= 1.** Even with a single peak,
   projecting a point mass through `spread()` keeps that same point as the highest-weighted
   cell (the identical lazy-walk property, now applied to one point instead of a ring). Age 0
   is exempt: a fresh trail legitimately IS still there. This is well-motivated, not an
   arbitrary patch: a genuinely stale reading is itself evidence against "never moved" -- if
   the opponent had stayed, continued occupancy would keep re-emitting at full strength
   (`ScentField.emit_opponent`), and the reading would not have decayed at all.

**A barrier-mass-leak bug in `BeliefMap.predict()` was found and fixed the same way** (manual
verification before tests): the initial `_clip_barriers` fell back to the generic, barrier-
*unaware* `_uniform()` helper when every credited cell had just been barriered, which then let
`spread()`'s unconditional STAY branch (`board.py` trusts the precondition that an agent's own
cell is never a barrier, so it does not defend against a hypothesised position that violates
it) redeposit a small residual mass back onto the barrier cell. `_clip_barriers`'s degenerate
fallback is now barrier-aware: uniform over the cells that remain legal, never the barriers
themselves.

**`predict()`'s parameter is `params: GameParams`, not a literal `rules` argument.** The plan's
prose names it `predict(state, rules)`, but the only function it needs to call
(`sdk/actions.py`'s `thief_actions`/`cop_actions`/`barrier_cells`) takes `GameParams`, never
`ResolutionRules`. This codebase uses `params`/`rules` as a strict, consistent pair naming
`GameParams`/`ResolutionRules` respectively throughout (`resolve.py`, `matrix.py`,
`valuebrain.py`); naming an unrelated `GameParams` argument `rules` would silently break that
convention for every future reader. The real, tested signature is documented above for 04-09
and 04-11.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Split the Task 3 test file at the 150-code-line ceiling**
- **Found during:** Task 3, first line-limit check after writing `tests/unit/strategy/test_belief_scent.py` with both the `belief_config.py` loader tests and the `belief_scent.py` algorithm tests in one file (153 lines; a later addition for a coverage gap pushed a redraft to 155).
- **Issue:** The plan's `files_modified` names only `tests/unit/strategy/test_belief_scent.py` for Task 3, but CLAUDE.md's line-limit rule "OVERRIDES any default behavior" and takes precedence over plan instructions (the same situation 04-01 documented for `scent_config.py`/`scent_kernel.py`).
- **Fix:** Moved the `belief_config.py` loader tests to a new `tests/unit/test_belief_config.py`, matching this repo's own existing convention that config loaders under `shared/` get their tests in `tests/unit/`, not `tests/unit/strategy/` (`test_language_config.py` and `test_scent_config.py` already do exactly this, and `test_language_config.py`'s own docstring documents the identical "added beyond the plan's files_modified list" precedent). `test_belief_scent.py` kept only the `belief_scent.py`-specific tests.
- **Files modified:** `tests/unit/strategy/test_belief_scent.py`, `tests/unit/test_belief_config.py` (new)
- **Verification:** Both files pass `scripts/check_line_limit.sh`; all 27 tests across the two files pass; 100% coverage on both `belief_scent.py` and `belief_config.py`.
- **Committed in:** `2163b29` (Task 3 commit)

**2. [Rule 2 - Missing test coverage] Removed an unused `BeliefKey.__str__` override**
- **Found during:** Task 3, post-implementation coverage pass.
- **Issue:** `BeliefKey.__str__` was added out of habit, copying `ScentKey`'s pattern, but `belief.json` is never canonically re-serialised or hashed (unlike `scent.json`'s `scent_digest()`), so the override had zero callers and showed as uncovered.
- **Fix:** Removed the override; a plain `str, Enum` member already compares equal to its own value for every dict-key lookup this loader performs (matching `LanguageKey`, which never defined `__str__` either).
- **Files modified:** `src/pursuit/shared/belief_config.py`
- **Verification:** 100% coverage on `belief_config.py`; `ruff check` clean.
- **Committed in:** `2163b29` (Task 3 commit)

---

**Total deviations:** 2 auto-fixed (1 blocking/line-limit, 1 dead-code-from-coverage-gap). The
scent-likelihood algorithm redesign and the barrier-mass-leak fix (see Decisions Made) are not
listed here because neither was ever committed in a broken state -- both were found and fixed
during interactive verification before Task 1/Task 3's commits were made, which is why they
are documented as design decisions with full rationale rather than as post-commit deviations.
**Impact on plan:** No scope creep. The algorithm redesign changed `scent_likelihood()`'s
internal method, not its signature or its contract (still `(opponent_field, role, state,
params, model, config) -> Grid`, still callable exactly where 04-09 expects it).

## Issues Encountered

- **The board's exact centre is a worst-case symmetry point for any diffusion-based
  likelihood, and it is also the thief's real starting cell.** Documented at length under
  Decisions Made; resolved before any commit, and specifically tested for (not just the more
  forgiving off-centre/corner cases) so this cannot silently regress.
- `core.hooksPath` is not configured in this worktree's git config (same observation 04-01
  recorded) -- `scripts/check_line_limit.sh`, `uv run ruff check`, and the full test suite were
  run manually before every commit rather than relying on an inactive pre-commit hook.

## User Setup Required

None -- no external service configuration required.

## Next Phase Readiness

- **Plan 04-09** (belief fusion: hint likelihood, adaptive reliability, scent-contradiction
  detection) can call `scent_likelihood()` and `BeliefMap.update()` directly; the "Grid is
  dense, neutral = 1.0" contract is stable and documented above.
- **Plan 04-11** (`BeliefAdapter`, sample-from-belief) has `BeliefMap.sample(rng)` ready,
  taking an injected `random.Random` exactly as D-43 requires for reproducible seeded
  selection.
- No blockers identified for the next wave. Both `04-02` (handshake scent digest) and this
  plan depend only on `04-01`, already merged.

## Known Stubs

None -- every function shipped in this plan is fully wired (pure computation and a fail-loud
config loader); nothing renders empty/placeholder data.

---
*Phase: 04-language-and-scent*
*Completed: 2026-08-08*

## Self-Check: PASSED

- All 10 created files confirmed present via `git show --stat` across the three task
  commits: `belief.py`, `belief_motion.py`, `belief_scent.py`, `belief_config.py`, both
  `belief.json` configs, and all four test files.
- All 3 referenced commit hashes (`b3773ac`, `f6ced38`, `2163b29`) confirmed present in
  `git log --oneline -3`.
- Full repo suite re-run clean at SUMMARY time: 571 passed, 93.22% coverage (gate >= 85%);
  `uv run ruff check .`, `bash scripts/check_line_limit.sh` (repo-wide), and
  `uv run python scripts/check_no_llm_in_strategy.py` all exit clean.
- 100% line coverage confirmed individually on all four new source modules
  (`belief.py`, `belief_motion.py`, `belief_scent.py`, `belief_config.py`).
