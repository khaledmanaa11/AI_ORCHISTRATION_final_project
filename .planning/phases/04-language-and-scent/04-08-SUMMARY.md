---
phase: 04-language-and-scent
plan: "08"
subsystem: strategy
tags: [deception, intent-flag, herding, danger-adaptive, rule-25, d-36, d-37, d-38, lang-03, strat-07]

# Dependency graph
requires:
  - "04-05: BeliefMap.posterior()/argmax() (strategy/belief.py) -- the cop-distance estimate's source"
  - "04-07: Region + REGION_NAMES (shared/inference.py) -- the claim vocabulary, shared with the decoder"
  - "04-07: DirectionWord/Origin/axis_signs (shared/directions.py)"
  - "04-01: ScentField.freshest('own') (strategy/scentfield.py) -- the Sec4.4 self-contradiction check"
  - "Phase 3: features.value + weights.PRIOR -- the existing evaluation the cop scores claims with"
provides:
  - "DeceptionPlan + ClaimKind + ALWAYS_TRUE_KINDS + Intent (shared/deception_types.py)"
  - "plan_deception(role, state, params, belief, rng, config, *, scent, weights) -> DeceptionPlan (strategy/deception.py)"
  - "declare_truthfully(kind) -> DeceptionPlan -- the one constructor for barrier/capture declarations"
  - "plan_thief_claim / lie_probability / expected_opponent_distance (strategy/deception_thief.py)"
  - "plan_cop_claim (strategy/deception_cop.py)"
  - "DeceptionParams/load_deception_config/DeceptionKey (shared/deception_config.py) + config/{police,thief}/deception.json"
  - "region_of / region_cells / region_center / region_distance (strategy/regions.py) -- the ONE Region-to-cells translation"
affects: [04-10-bluff-generator, 04-09-belief-fusion, 04-12-turn-pipeline, 04-14-gate-4-measurement, phase-6-commit-reveal]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Illegal-state-unrepresentable via __post_init__ on a frozen dataclass rather than via a checked factory function. dataclasses.replace re-runs __post_init__, so unlike a helper there is genuinely no construction path -- including in a test double -- that produces a lying capture or barrier declaration."
    - "Model the opponent with the SAME evaluation we use, on a board with the opponent's BELIEF substituted, then score the position that actually results. The gap between the believed board and the real one is precisely the value of a lie, and it needs no second heuristic."
    - "Derive a config ceiling from its floor (max_lie_probability = 1 - truth_floor) instead of configuring both, so the two can never be set inconsistently and the floor cannot become a fiction."
    - "Zero float literals in a policy module, verified by tokenize rather than by grep, so book section references in prose (Sec4.4) do not mask a real hardcoded threshold."

key-files:
  created:
    - src/pursuit/shared/deception_types.py
    - src/pursuit/shared/deception_config.py
    - src/pursuit/strategy/deception.py
    - src/pursuit/strategy/deception_thief.py
    - src/pursuit/strategy/deception_cop.py
    - src/pursuit/strategy/regions.py
    - config/police/deception.json
    - config/thief/deception.json
    - tests/unit/test_deception_types.py
    - tests/unit/test_deception_config.py
    - tests/unit/strategy/test_deception.py
    - tests/unit/strategy/test_deception_thief.py
    - tests/unit/strategy/test_deception_cop.py
    - tests/unit/strategy/test_regions.py
  modified:
    - src/pursuit/network/hint_payload.py
    - src/pursuit/network/move_payload.py
    - src/pursuit/shared/directions.py

key-decisions:
  - "The cop's believing-thief model uses features.value against a board with the cop substituted at the claimed sector's centre, NOT a 'run away from the believed cell' distance rule. Measured, not assumed: with the distance heuristic every claim produced the SAME step on an open board (gain +0.0000 across all nine sectors), leaving the deception channel with no lever at all. See Issues."
  - "Intent moved from network/hint_payload.py to shared/deception_types.py (re-exported there). The planner DECIDES the flag and lives under strategy/, which may not import pursuit.network (STRAT-03)."
  - "Origin/DEFAULT_ORIGIN/axis_signs moved from network/move_payload.py to shared/directions.py so the nine sectors honour a negotiated non-default axis origin (Table 13 row 3) instead of assuming top-left in a brand-new module."
  - "DeceptionPlan also rejects a TRUTH plan whose claim differs from the recorded truth -- beyond the plan's literal requirement. A flag marked 'truth' over a false claim is the one dishonesty an auditor can actually catch, and rules 15/16/21/22 only cover the two always-true kinds."
  - "strategy/regions.py created here rather than in 04-09: both this plan and 04-09 need Region -> cells, and 04-09 depends on 04-05/04-07, not on this plan, so leaving it uncreated would have produced two sector grids."

patterns-established:
  - "A frozen-dataclass constructor as a rules gate, with dataclasses.replace explicitly tested as a non-bypass."
  - "Finding a regression-test position by randomised search over boards, then freezing it, when a hand-constructed board fails to exercise the mechanism."

requirements-completed: [LANG-03, STRAT-07]

# Metrics
duration: single session, 1 commit (215458b)
completed: 2026-08-08
---

# Phase 4 Plan 08: Deception Planner Summary

**The intent flag and the claim are chosen by code, from the board and the belief map, before any text exists. A capture or barrier claim cannot be marked a lie by any code path.**

## Accomplishments

- **`shared/deception_types.py`** — `Intent` (moved here), `ClaimKind` (`LOCATION`, `HEADING`, plus the always-true `BARRIER` and `CAPTURE`), `ALWAYS_TRUE_KINDS` mapping each to the rule that makes it truthful, and the frozen `DeceptionPlan`. `__post_init__` is the gate: it refuses `Intent.LIE` on an always-true kind with a message naming the rules **and** refuses a `TRUTH` plan that does not state the recorded truth.
- **`strategy/deception.py`** — `plan_deception` dispatches to the role policy and never returns `None` (LANG-01: a turn always carries a hint). `declare_truthfully(kind)` is the single constructor for barrier and capture declarations, and deliberately **takes no `intent` argument** — the caller cannot pass the wrong flag because there is nowhere to pass it.
- **`strategy/deception_thief.py`** (D-37) — `expected_opponent_distance` over the **whole posterior**, not the distance to `argmax`; `lie_probability` flat at the ceiling inside `danger_distance`, flat at the floor beyond `safe_distance`, linear between; and `_survivable_lie`, which excludes both the true sector and the sector our own freshest trail betrays, then draws from the `lie_candidate_pool` furthest candidates with the injected RNG.
- **`strategy/deception_cop.py`** (D-38) — for each candidate sector, model what a thief believing it would do using `features.value` on a board with the cop substituted at that sector's centre, then score the position that **actually** results. Lie only when the best claim beats the truthful one by more than `min_herding_gain`.
- **`strategy/regions.py`** — `region_of`, `region_cells`, `region_center`, `region_distance`. `region_cells` is derived by asking `region_of` about each cell, so the two cannot drift apart.
- **`config/{police,thief}/deception.json`** — byte-identical, every number labelled an engineering default in the file itself.

## The `DeceptionPlan` shape (for 04-10 and Phase 6)

```python
from pursuit.shared.deception_types import ClaimKind, DeceptionPlan, Intent
from pursuit.strategy.deception import declare_truthfully, plan_deception

@dataclass(frozen=True)
class DeceptionPlan:
    intent: Intent                          # TRUTH | LIE -- fixed before any text exists
    kind: ClaimKind                          # LOCATION | HEADING | BARRIER | CAPTURE
    claimed_region: Region | None = None     # what we will say
    claimed_heading: DirectionWord | None = None
    true_region: Region | None = None        # what is actually so, for the audit log
    true_heading: DirectionWord | None = None

    @property
    def is_lie(self) -> bool

plan = plan_deception("thief", state, params, belief, rng, config, scent=field)
plan = plan_deception("cop",   state, params, belief, rng, config, weights=trained)
plan = declare_truthfully(ClaimKind.CAPTURE)   # rules 21/22; no intent argument exists
```

**04-10 phrases `claimed_region`/`claimed_heading` and must not read or alter `intent`.** There is no text field on this type, which is what keeps the ordering LANG-03 requires.

## Measured lie-rate curves

Config as shipped: `truth_floor=0.2`, `min_lie_probability=0.1`, `danger_distance=2.0`, `safe_distance=8.0`, `lie_candidate_pool=3` ⇒ implied ceiling **0.8**.

**Thief (D-37)** — thief at `(3,3)`, belief collapsed on one cop cell, 4000 seeded draws each:

| Believed cop cell | E[distance] | p(lie) predicted | measured |
|---|---|---|---|
| (3,3) | 0.0 | 0.800 | **0.802** |
| (3,4) | 1.0 | 0.800 | **0.802** |
| (3,5) | 2.0 | 0.800 | **0.802** |
| (2,1) | 3.0 | 0.683 | **0.679** |
| (0,0) / (6,6) / (0,6) | 6.0 | 0.333 | **0.336** |

The curve is flat at the ceiling inside the danger threshold, falls through the ramp, and **never reaches 1.0 or 0.0** — D-37's truth floor and the non-zero long-range lie rate both hold as measured behaviour, not just as config values.

**Cop (D-38)** — deterministic given the board, so the rate is over positions rather than draws. 194 random legal cop/thief pairs on an open board: **125 lies / 194 = 0.644**. Claimed-sector spread: `center 40, northwest 28, west 24, north 24, east 24, south 18, northeast 13, southwest 12, southeast 11` — no degenerate single-sector answer.

**Reproducibility:** 200 turns × 2 seats = 400 plans reproduce byte-identically under a fixed seed, and differ under a different one.

## Gates measured on the merged tree

| Check | Result |
|---|---|
| `uv run pytest tests/ --cov` | **850 passed, 94.31%** (floor 85) |
| `uv run ruff check .` | 0 violations |
| `bash scripts/check_line_limit.sh` | clean repo-wide |
| `uv run python scripts/check_no_llm_in_strategy.py` | `OK: no forbidden imports under .../src/pursuit/strategy.` |
| `grep -rn "prompt\|sentence\|words" src/pursuit/strategy/deception*.py` | no match — this layer produces meaning only |
| Float literals in `strategy/deception*.py` (tokenize) | **0** — every threshold from `deception.json` |
| Seeded 200-turn × 2-seat replay | byte-identical |
| Coverage of the 6 new source modules | **100% each** |

## Deviations from Plan

### 1. [Rule 3 — Blocking] The believing-thief model uses the evaluation, not a distance rule

- **Found during:** Task 3, probing the policy on constructed boards before writing assertions.
- **Issue:** The plan's own phrasing — *"a thief that trusts 'the cop is over by the river' moves away from the river"* — reads as a distance rule, and that is how it was implemented first. **Measured, it does not work:** on an open board with the cop at `(3,0)`, all nine candidate claims produced the same believing-thief step and a herding gain of `+0.0000`. A one-step distance-maximising thief ties across most of its legal set, so the claim had no lever at all and the cop would have told the truth in every position — LANG-03's *"both intent values occur"* would have failed at 04-14.
- **Fix:** `_believing_step` now evaluates each legal destination with `features.value` on a board where the cop is substituted at the claimed sector's centre, and picks the destination the thief prefers (lowest cop-perspective value, ties to the lowest cell). This follows the plan's *other*, stronger instruction — *"using the existing evaluation rather than a new heuristic"* — and the belief enters exactly where it should. After the change the same board yields distinct steps and a real gain (`+0.0551` for the best claim).
- **Verification:** `test_the_believing_thief_responds_to_the_believed_position`, `test_the_chosen_lie_is_the_best_scoring_claim`, and the frozen `herding_board` regression.
- **Lookahead is still one step**, exactly as the plan requires. Its power is genuinely limited — see Issues.

### 2. [Rule 3 — Blocking] `plan_deception` takes `params`, and two optional keyword arguments

- **Issue:** The plan's signature is `plan_deception(role, state, belief, rng, config)`, but `GameState` carries no `board_size` and every sector computation needs it.
- **Fix:** `plan_deception(role, state, params, belief, rng, config, *, scent=None, weights=None)`. `scent` gives the thief the Sec4.4 self-contradiction check; `weights` lets a **trained** cop herd on its own evaluation rather than silently on `PRIOR`. Both are keyword-only, both degrade sensibly when absent, and 04-12 supplies both.
- **Note for 04-12:** passing `scent` is what makes the thief's lies survivable, and passing `weights` is what makes the cop's herding use the artefact it was trained with. Omitting either is a silent quality loss, not an error.

### 3. [Rule 3 — Blocking] `Intent`, `Origin`, `DEFAULT_ORIGIN` and `axis_signs` moved into `shared/`

- **Issue:** `Intent` lived in `network/hint_payload.py`; the planner that decides it lives under `strategy/`, which may not import `pursuit.network` (STRAT-03). The axis origin had the same problem: sectors that assumed top-left would silently disagree with the wire under a negotiated `bottom-left` agreement.
- **Fix:** moved to `shared/deception_types.py` and `shared/directions.py`; both network modules re-export, so every existing call site resolves unchanged.
- **Verification:** `test_intent_is_the_same_object_the_wire_serialises`; `test_a_bottom_left_origin_flips_the_row_axis`; all 20 pre-existing `test_move_payload.py` tests green.

### 4. [Rule 3 — Blocking] `strategy/regions.py` created here

- **Issue:** Not in this plan's `files_modified`, but both this plan and 04-09 need `Region` → cells, and 04-09 does not depend on this plan. Leaving it out would have produced two independent sector grids that could disagree.
- **Fix:** one module, with `region_cells` derived from `region_of` so they cannot drift.

### 5. [Rule 2 — Missing functionality] Three test files beyond the plan's list

- `tests/unit/test_deception_types.py` (14), `tests/unit/test_deception_config.py` (22), `tests/unit/strategy/test_regions.py` (17) — CLAUDE.md's per-module rule, same precedent as 04-03/04-06.

### 6. [Beyond the plan, deliberate] `DeceptionPlan` also rejects a dishonest `TRUTH` flag

The plan requires refusing `LIE` on the always-true kinds. The constructor additionally refuses a `TRUTH` plan whose claim differs from the recorded truth. Rules 15/16/21/22 only cover barrier and capture declarations, but a location claim flagged `truth` while stating the wrong sector is the one dishonesty an auditor holding our event log can actually prove — and Phase 6 will hash that flag.

---

**Total deviations:** 6 — four Rule-3 blocking structural fixes (one of them a measured correction to the plan's own herding model), one Rule-2 test addition, one deliberate strengthening of a rules gate. No scope creep; no plan requirement relaxed.

## Issues Encountered

- **The distance-based herding model was inert, and only a measurement showed it.** Recorded in full as Deviation 1 because the failure was invisible to type checks, to lint, and to any test that did not compare gains across all nine candidate claims — the code ran, returned plans, and would have quietly told the truth every turn.
- **One-step lookahead is genuinely weak, and the tests say so honestly.** A hand-built cul-de-sac board did not exercise the mechanism at all: the trap sat two steps from the thief, and one ply cannot see it. Rather than tune a board until a test passed, a randomised search over 4000 boards found positions where the lever measurably bites; one is frozen as `herding_board` (`test_the_lie_drives_the_thief_somewhere_less_connected`). The plan's deliberate one-step ceiling is respected, and its cost is now documented rather than implied.
- **`grep -nE "[0-9]\.[0-9]"` (the plan's verification 5) matches book section references** such as `Sec4.4` and `Sec6.2` in docstrings, and would do so for pre-existing files like `strategy/belief.py` too. The check was run in the stricter form the gate intends — a `tokenize` pass for NUMBER tokens containing `.` — which reports **zero float literals** across all three modules. The prose references were left intact; mangling a book citation to satisfy a naive regex would trade a real reference for a cosmetic pass.

## Next Phase Readiness

- **04-10** consumes `DeceptionPlan`, extends `deception.json`, and must not read `intent` when phrasing. `Region` and `DirectionWord` are the shared claim vocabulary with 04-07's decoder, so a claim we emit decodes into the same enum on the opponent's side.
- **04-09** should import `strategy/regions.py` for its hint likelihood rather than deriving sectors again.
- **04-12** should pass `scent=` and `weights=` (Deviation 2) and use `declare_truthfully` for capture and barrier declarations.
- **Phase 6** hashes `Intent` from `pursuit.shared.deception_types`; the plan object already exists before any text does, which is the ordering `State || Move || Intent || Nonce` depends on.
- No blockers.

---
*Phase: 04-language-and-scent · Commit: `215458b`*
