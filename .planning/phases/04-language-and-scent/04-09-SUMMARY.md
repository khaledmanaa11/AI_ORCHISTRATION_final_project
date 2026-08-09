---
phase: 04-language-and-scent
plan: "09"
subsystem: strategy
tags: [belief-map, bayesian-inference, reliability, lie-detection, hint-likelihood, d-40, d-42, d-51]

# Dependency graph
requires:
  - phase: 04-language-and-scent (plan 04-05)
    provides: >
      strategy/belief.py's BeliefMap (update/predict/posterior/argmax) and
      its exact-no-op zero-guard; strategy/belief_scent.py's
      scent_likelihood() and the neutral-grid convention; shared/belief_config.py's
      BeliefKey/BeliefParams/load_belief_config()
  - phase: 04-language-and-scent (plan 04-07)
    provides: >
      shared/inference.py's Inference/NO_EVIDENCE/Region/is_evidence, the
      decoder's read-confidence contract; strategy/regions.py's region_cells
      (04-08); shared/directions.py's DirectionWord/DEFAULT_ORIGIN/axis_signs
provides:
  - "strategy/scent_check.py: contradicts(inference, opponent_field, model, config) -> float,
    the Sec4.4 expected-vs-measured lie detector, reading expected_strength_after(model, 1)
    against the opponent trail's own freshest cell"
  - "strategy/reliability.py: Reliability -- a bounded [r_min, r_max] adaptive coefficient,
    seeded at a configured prior, moved by observe(contradiction_score) (D-51)"
  - "strategy/belief_hint.py: hint_likelihood(inference, reliability, board_size, config) -> Grid,
    the D-40 Bayes mixing formula, weighted well below scent and never zeroing a cell"
  - "shared/reliability_config.py + shared/hint_likelihood_config.py: the two new belief.json
    groups' typed containers and validation, split out of shared/belief_config.py at the
    150-code-line ceiling"
  - "belief.json's reliability and hint_likelihood groups (both roles, byte-identical),
    engineering defaults labelled as such"
affects: [04-11-belief-adapter, 04-12-turn-pipeline-integration, 04-13-docs-and-rules-resolution, 04-14-gate-4-measurement]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Reliability's observe(score) is ONE entry point handling both directions: a positive
      contradiction score pulls the coefficient down proportionally; an exact zero pulls it up
      toward the prior at recovery_rate -- no separate on_lie/on_truth methods, no threshold
      config needed to decide which branch to take"
    - "confidence == 0 returns an ALL-ZERO grid in belief_hint.py, not a neutral-1.0 grid like
      belief_scent.py's convention -- deliberately different, because BeliefMap.update()'s own
      zero-product guard is what buys an EXACT (bit-for-bit) no-op, which the plan's own verify
      text demands under exact comparison, not approx"
    - "belief.json now has three config groups from three different owning plans in one file;
      each new group gets its own shared/<group>_config.py + its own tests/unit/test_<group>_config.py,
      exercised only through load_belief_config() -- BeliefKey stays the single centralized key
      enum across all three, per 04-05's own anticipated extension"

key-files:
  created:
    - src/pursuit/strategy/scent_check.py
    - src/pursuit/strategy/reliability.py
    - src/pursuit/strategy/belief_hint.py
    - src/pursuit/shared/reliability_config.py
    - src/pursuit/shared/hint_likelihood_config.py
    - tests/unit/strategy/test_scent_check.py
    - tests/unit/strategy/test_reliability.py
    - tests/unit/strategy/test_belief_hint.py
    - tests/unit/strategy/test_belief_fusion_e2e.py
    - tests/unit/test_reliability_config.py
    - tests/unit/test_hint_likelihood_config.py
  modified:
    - src/pursuit/shared/belief_config.py
    - config/police/belief.json
    - config/thief/belief.json
    - tests/unit/test_belief_config.py

key-decisions:
  - "D-51 is implemented literally as a DISCLOSED REVISION of D-40, not an extension: the fixed
    hint mixing weight w (belief_hint.py, belief.json's hint_likelihood.weight) is unchanged and
    still validated below scent's weight by name; the reliability coefficient r (reliability.py,
    belief.json's own separate reliability.prior) is what became adaptive -- two distinct config
    fields, not the same JSON number wearing two names"
  - "The heading-to-gradient translation (belief_hint.py's _implied_distribution/_tilted/_tilt)
    only activates when a direction rides ALONGSIDE a region or explicit cells -- never as a
    standalone anchor, matching the wave-3 carry-over and the decoder's own confidence=0
    convention for bare headings. It never needs 'the last believed position' as external state:
    the claimed region/cells set IS the anchor, and the direction only re-weights within it,
    keeping the function pure and self-contained"
  - "contradicts()'s expected value uses expected_strength_after(model, 1) unconditionally -- a
    hint claiming a location always implies 'just moved here this turn', matching the book's own
    worked example (0.9 -> 0.81) exactly, not a variable recency inferred from the sentence"
  - "belief_config.py's three-group growth was proactively split into shared/reliability_config.py
    and shared/hint_likelihood_config.py before the 150-line ceiling was hit for the SOURCE file,
    but the ceiling still hit test_belief_config.py and test_belief_hint.py during the work --
    both split the same way, mirroring the source-file split"

patterns-established:
  - "One new shared/<group>_config.py + one new tests/unit/test_<group>_config.py per belief.json
    group added by a later plan, all still funneled through the single load_belief_config()"

requirements-completed: [LANG-05]

# Metrics
duration: ~25min
completed: 2026-08-09
---

# Phase 4 Plan 09: Belief Fusion (Reliability + Hint Likelihood + Sec4.4 Lie Detection) Summary

**The Bayes loop closes: `contradicts()` reads the book's own worked example (0.9 -> 0.81) against the opponent's real scent trail, `Reliability` turns that disagreement into a bounded [0.05, 0.95] trust coefficient that drops on a caught lie and recovers on consistency, and `hint_likelihood()` mixes a decoded claim into the belief map at a fixed weight (0.3) permanently below scent's (4.0) -- never zeroing a cell, and reproducing an exact no-op for `NO_EVIDENCE`.**

## Performance

- **Duration:** ~25 min
- **Completed:** 2026-08-09T00:39Z
- **Tasks:** 3 planned tasks, 3 commits (one per task)
- **Files modified:** 15 (11 created, 4 modified)

## Accomplishments

- `strategy/scent_check.py::contradicts()` reproduces the book's Sec4.4 worked example on the
  nose: a field holding `0.81` (`expected_strength_after(model, 1)`, computed from the real
  `scent.json` numbers, never retyped) at a south-east deposit and `0.00` at north scores `1.0`
  for a "north" claim and `0.0` for a "south-east" claim; an all-zero field and a region-less
  inference both score `0.0` regardless of the claim.
- `strategy/reliability.py::Reliability` starts at the configured prior (`0.5`), and a thousand
  maximal-contradiction observations settle it EXACTLY at `r_min` (`0.05`) while a thousand
  consistent observations settle it EXACTLY at the prior -- both measured directly, not just
  bounded, and never escaping `[r_min, r_max]` under a mixed 200-observation sequence either.
- `strategy/belief_hint.py::hint_likelihood()` implements the full D-40 mixing formula
  `L(c) = w . [r . q(c) + (1 - r) . u(c)] + (1 - w) . u(c)`, times the decoder's own confidence.
  `NO_EVIDENCE` produces an all-zero grid that `BeliefMap.update()`'s own zero-guard turns into an
  **exact** (bit-for-bit tuple-equal) no-op posterior -- the plan's stricter-than-approx
  requirement, verified directly rather than with `pytest.approx`.
- A confident hint never zeroes any cell, even outside the claimed region (`(1 - w) . u(c) > 0`
  always, since `r_max < 1` is validated strictly). Lowering reliability provably shrinks a
  claimed cell's own likelihood value.
- A heading riding alongside a region or cell claim tilts the implied distribution within that
  set (favouring cells further "in that direction") without ever reducing any cell in the set to
  zero; a heading with nothing to anchor it produces a flat, unshifted distribution.
- **The end-to-end Sec4.4 reproduction** (`test_belief_fusion_e2e.py`) drives scent and a hint
  stream through the SAME `BeliefMap` for 10 joint turns with the opponent truly fixed at a
  south-east cell: a **fully-truthful** hint stream (claiming the true region every turn) holds
  reliability at the prior the entire time; a **fully-lying** stream (claiming the opposite
  corner every turn) drives it to `r_min` within two observations. In BOTH regimes the fused
  posterior's `argmax` tracks the real scent trail, never the claim -- the book's own closing
  line ("the scent map cannot lie") holds numerically, not just as prose.
- `belief.json` now carries three engineering-default groups from three different owning plans in
  one byte-identical-across-roles file; `hint_likelihood.weight` (`0.3`) is validated at load to
  be strictly below `scent_likelihood.weight` (`4.0`), naming both keys on failure.
- 100% line coverage on all six new/extended production modules; repo-wide suite: **903 passed,
  94.55% coverage** (floor 85%); `ruff check .` 0 violations; `scripts/check_line_limit.sh` and
  `scripts/check_no_llm_in_strategy.py` both clean.

## The reliability trajectory 04-14 quotes

Ten joint turns, opponent truly at `(6, 6)` (south-east) throughout, `prior=0.5`, `r_min=0.05`,
`r_max=0.95`, `contradiction_step=0.3`, `recovery_rate=0.05`:

| Opponent | Reliability trajectory (turn 0 = prior, turns 1-10 after each observation) | Final `argmax` |
|---|---|---|
| **Fully truthful** (claims south-east every turn) | `0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5` | `(6, 6)` -- the truth |
| **Fully lying** (claims north-west every turn) | `0.5, 0.2, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05` | `(6, 6)` -- the truth |

The lying opponent's trust collapses to `r_min` after just two contradictory observations and
stays there; the truthful opponent's trust never moves. In both cases the belief map's `argmax`
follows the scent trail, never the claim -- Sec4.4 reproduced end to end, on this codebase's own
locked scent numbers.

## Task Commits

Each task was committed atomically:

1. **Task 1: the scent-contradiction test (Sec4.4, literally)** - `6bf5d6e` (feat)
2. **Task 2: reliability -- bounded, adaptive, per-game** - `fe0bd7e` (feat)
3. **Task 3: the hint likelihood, weighted below scent** - `f2ffbc9` (feat)

**Plan metadata:** commit follows this SUMMARY.

## Files Created/Modified

- `src/pursuit/strategy/scent_check.py` - `contradicts(inference, opponent_field, model, config) -> float`
- `src/pursuit/strategy/reliability.py` - `Reliability`: `value`, `observe(contradiction_score)`
- `src/pursuit/strategy/belief_hint.py` - `hint_likelihood(inference, reliability, board_size, config) -> Grid`
- `src/pursuit/shared/reliability_config.py` - `ReliabilityParams`, `validate_reliability()`
- `src/pursuit/shared/hint_likelihood_config.py` - `HintLikelihoodParams`, `validate_hint_likelihood()`
- `src/pursuit/shared/belief_config.py` - extended with the `reliability`/`hint_likelihood` groups
- `config/police/belief.json`, `config/thief/belief.json` - two new byte-identical groups
- `tests/unit/strategy/test_scent_check.py`, `test_reliability.py`, `test_belief_hint.py`,
  `test_belief_fusion_e2e.py` - 8 + 8 + 12 + 5 tests respectively
- `tests/unit/test_reliability_config.py`, `test_hint_likelihood_config.py`, `test_belief_config.py`
  (extended) - loader-level validation tests for the two new groups

## Decisions Made

See `key-decisions` in the frontmatter. The two decisions worth restating in prose:

1. **D-51 keeps D-40's fixed weight `w` and adds an independent adaptive `r`.** These are two
   separate `belief.json` fields (`hint_likelihood.weight` and `reliability.prior`), not one
   number reused twice — the plan's own text ("D-40's fixed weight, unchanged" for the reliability
   prior, and a *separate* "add the hint weight to belief.json" for Task 3) reads ambiguously
   enough that a literal same-field reading was also possible; this executor chose the
   architecturally cleaner two-field reading (avoids a cross-task ordering dependency within the
   same plan, and keeps each config group self-contained per file-ownership convention).
2. **The heading-to-gradient translation never needs external "last believed position" state.**
   It re-weights cells ALREADY implicated by a region or explicit cell claim; a standalone heading
   (no region, no cells) has nothing to translate and falls through to flat uniform, which the
   real decoder never emits at positive confidence in the first place (04-07's `is_evidence`).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `shared/belief_config.py` split at the 150-code-line ceiling**
- **Found during:** Task 3, after adding the `hint_likelihood` group on top of Task 2's
  `reliability` group (04-05's original `scent_likelihood` group already occupied ~94 code lines).
- **Issue:** Three groups' worth of typed dataclasses, field parsing and validation in one file
  would have exceeded 150 code lines; CLAUDE.md's line-limit rule overrides plan instructions.
- **Fix:** `ReliabilityParams`/`validate_reliability` moved to a new `shared/reliability_config.py`
  (Task 2); `HintLikelihoodParams`/`validate_hint_likelihood` moved to a new
  `shared/hint_likelihood_config.py` (Task 3). `belief_config.py` stays the single
  `load_belief_config()` entry point and the single `BeliefKey` enum, per 04-05's own SUMMARY,
  which explicitly anticipated 04-09 extending this same file.
- **Files modified:** `src/pursuit/shared/belief_config.py`, `src/pursuit/shared/reliability_config.py`
  (new), `src/pursuit/shared/hint_likelihood_config.py` (new)
- **Verification:** `scripts/check_line_limit.sh` clean; 100% coverage on all three files.
- **Committed in:** `fe0bd7e` (reliability_config.py), `f2ffbc9` (hint_likelihood_config.py)

**2. [Rule 3 - Blocking] `tests/unit/test_belief_config.py` split at the 150-code-line ceiling**
- **Found during:** Task 3, after adding validation tests for both new groups on top of the
  existing `scent_likelihood`-group tests (98 lines pre-existing).
- **Issue:** Same ceiling, same reasoning, mirroring the source-file split.
- **Fix:** Reliability-group validation tests moved to a new `tests/unit/test_reliability_config.py`
  (Task 2); hint_likelihood-group validation tests moved to a new
  `tests/unit/test_hint_likelihood_config.py` (Task 3). `test_belief_config.py` keeps the
  original `scent_likelihood` tests, the loader's general mechanics tests, the new
  byte-identical-roles test, and one smoke test proving both new groups are wired into
  `BeliefParams` at all.
- **Files modified:** `tests/unit/test_belief_config.py`, `tests/unit/test_reliability_config.py`
  (new), `tests/unit/test_hint_likelihood_config.py` (new)
- **Verification:** `scripts/check_line_limit.sh` clean; all tests pass.
- **Committed in:** `fe0bd7e` (test_reliability_config.py), `f2ffbc9` (test_hint_likelihood_config.py)

**3. [Rule 3 - Blocking] `tests/unit/strategy/test_belief_hint.py` split at the 150-code-line ceiling**
- **Found during:** Task 3, final verification pass, after the directional-tilt coverage tests and
  the end-to-end Sec4.4 tests were both added to one file (183 code lines).
- **Issue:** Same ceiling. The pre-commit hook caught this on the first commit attempt for Task 3
  and blocked it, exactly as designed.
- **Fix:** The end-to-end Sec4.4 reproduction (`_run_ten_turns` and its two tests, plus the
  posterior-validity and D-40-asymmetry tests that also combine scent + hint on one `BeliefMap`)
  moved to a new `tests/unit/strategy/test_belief_fusion_e2e.py`. `test_belief_hint.py` keeps the
  `hint_likelihood()`-only unit tests (confidence handling, the mixing formula, the directional
  tilt).
- **Files modified:** `tests/unit/strategy/test_belief_hint.py`,
  `tests/unit/strategy/test_belief_fusion_e2e.py` (new)
- **Verification:** `scripts/check_line_limit.sh` clean; both files' tests pass; the split commit
  was verified before pushing (the blocked commit was never forced through with `--no-verify`).
- **Committed in:** `f2ffbc9`

**4. [Rule 2 - Missing critical] Added the missing byte-identical-roles test for belief.json**
- **Found during:** Task 2, reading the environment rules ("config/police/belief.json and
  config/thief/belief.json must stay byte-identical (a test asserts this)") and finding no such
  test actually existed in `test_belief_config.py`, unlike `scent.json`/`language.json`/`deception.json`'s
  own loader tests, which all have one.
- **Issue:** Missing regression coverage for a hard project invariant (both role configs, sourced
  independently, must never drift byte-for-byte).
- **Fix:** Added `test_role_files_are_byte_identical()` to `test_belief_config.py`, matching the
  sibling loaders' established pattern exactly.
- **Files modified:** `tests/unit/test_belief_config.py`
- **Verification:** Test passes on both role files as they now stand.
- **Committed in:** `fe0bd7e`

---

**Total deviations:** 4 auto-fixed (3 line-limit splits, 1 missing test coverage). All four are
mechanical consequences of the 150-line gate and one pre-existing coverage gap; none changed any
function's signature, contract, or behaviour. No scope creep.
**Impact on plan:** None on the shipped contracts (`contradicts`, `Reliability.observe`,
`hint_likelihood` all match the plan's `must_haves` signatures verbatim); only file organization
changed, always toward smaller, single-purpose files per CLAUDE.md's explicit instruction to
split rather than compress.

## Issues Encountered

- **The per-task atomic-commit protocol required reconstructing two intermediate states** of
  `shared/belief_config.py` and both `belief.json` files (a "Task 2 only, no hint_likelihood yet"
  version) so Task 2's commit would not silently include Task 3's `hint_likelihood` group. This
  is not a code defect — both intermediate and final states were independently verified (tests +
  ruff + line-limit) before each commit — but it added real executor overhead versus writing each
  task's files once, in order. Documented here as a process note for future same-file-across-tasks
  plans, not as a deviation from the shipped code.
- Two ambiguous phrases in the plan's own prose required an interpretive decision, both recorded
  above under Decisions Made: whether `reliability.prior` and `hint_likelihood.weight` are the
  same config field or two independent ones (chosen: independent), and what "a directional
  gradient from the last believed position" means operationally when no belief-map state is
  threaded into `hint_likelihood`'s signature (chosen: the claimed region/cells set itself is the
  anchor).

## User Setup Required

None -- no external service configuration required.

## Next Phase Readiness

- **Plan 04-11** (`BeliefAdapter`, sample-from-belief) can call `BeliefMap.update()` with either
  `scent_likelihood()` or `hint_likelihood()` output interchangeably -- both are dense `Grid`
  objects with the same contract.
- **Plan 04-12** (turn-pipeline integration) is the natural owner of constructing one
  `Reliability` instance per opponent at handshake time (never persisted across games, per this
  plan's docstring) and calling `scent_check.contradicts()` + `Reliability.observe()` once per
  incoming hint, in that order, each turn.
- **Plan 04-13** must state D-51 as a disclosed revision of D-40 in `PRD_belief_map.md` and
  `RULES-RESOLUTION-LANG.md` (already required by the outline's must_haves) -- this plan's
  `reliability.py`/`belief_hint.py` docstrings and this SUMMARY's Decisions Made section are the
  source material for that write-up.
- **Plan 04-14** should quote the reliability-trajectory table above directly; both regimes
  (fully-truthful and fully-lying) are already measured and reproduced by a committed,
  deterministic test (`test_belief_fusion_e2e.py`), not just this SUMMARY's prose.
- No blockers identified.

## Known Stubs

None -- every function shipped in this plan is fully wired (pure computation and fail-loud config
loaders); nothing renders empty/placeholder data.

---
*Phase: 04-language-and-scent*
*Completed: 2026-08-09*

## Self-Check: PASSED

- All 11 created files confirmed present on disk (`[ -f ]`): `scent_check.py`, `reliability.py`,
  `belief_hint.py`, `reliability_config.py`, `hint_likelihood_config.py`, and the six new test
  files.
- All 4 modified files confirmed present: `belief_config.py`, both `belief.json` role files,
  `test_belief_config.py`.
- All 3 task commit hashes (`6bf5d6e`, `fe0bd7e`, `f2ffbc9`) confirmed present in
  `git log --oneline --all`.
- Full repo suite re-run clean at SUMMARY time: 903 passed, 94.55% coverage (gate >= 85%);
  `uv run ruff check .`, `bash scripts/check_line_limit.sh` (repo-wide), and
  `uv run python scripts/check_no_llm_in_strategy.py` all exit clean.
- 100% line coverage confirmed individually on all six new/extended production modules
  (`scent_check.py`, `reliability.py`, `belief_hint.py`, `belief_config.py`,
  `reliability_config.py`, `hint_likelihood_config.py`).
