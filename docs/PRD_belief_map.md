# PRD — the belief map (Bayesian position inference)

**Mechanism:** how each agent maintains a probability distribution over the opponent's cell from
scent and hint evidence, and how that distribution reaches the mover.
**Status:** implemented (plans 04-05, 04-09, 04-11) · **Segal §2.3:** every algorithm or central
mechanism carries its own PRD. This is that document.
**Rules note:** [`docs/phases/phase-4/RULES-RESOLUTION-LANG.md`](phases/phase-4/RULES-RESOLUTION-LANG.md)
D-48 records the reveal-vs-blindness contradiction this mechanism resolves; D-51 in this
document's §5 is cross-referenced there.

---

## 1. The problem this mechanism solves

§6.4 (book p.47, PDF 63) requires that *"neither side sees the opponent's real location"* and
that each side instead build its own `[board size]×[board size]` grid `b(s) = P(opponent in cell
s)`, fed by scent evidence and a verbal hint that "may be false," fused by Bayes' rule with a
reliability coefficient on the hint. D-48 (see the rules note) resolves this against the book's
own per-turn Reveal requirement by making the belief map the **one-turn-ahead predictive**
distribution: the opponent's pre-turn cell is known exactly one turn behind (Regime A) or not at
all (Regime B), and the belief map's job is to turn that plus scent and hints into a usable
target for the mover.

## 2. The object: `BeliefMap`

`strategy/belief.py`'s `BeliefMap(board_size, role)` is a dense probability grid
(`list[list[float]]`, every cell always present — unlike `ScentField`'s sparse dict trails) with
five operations, all defended by invariants checked in code, not merely assumed:

| Operation | What it does | Invariant |
|---|---|---|
| `observe_exact(cell)` | collapse to a delta at a known cell | raises on an off-board cell |
| `predict(state, params)` | one joint turn of legal-motion diffusion | barrier-safe; never deposits mass on a barriered cell |
| `update(likelihood)` | pointwise multiply + renormalise against a `Grid` | an all-zero-product likelihood is an exact no-op (see §4) |
| `posterior()` | immutable snapshot | non-negative, sums to 1, always |
| `sample(rng)` | proportional draw from an injected `random.Random` | never touches the module RNG or `secrets` (D-43, §6) |

Constructed uniform; every one of `observe_exact`/`predict`/`update` is proven, by a seeded
random sequence of calls (not just each operation in isolation), to leave the grid a valid
distribution at every step.

## 3. The motion model and the scent likelihood

**Motion.** `strategy/belief_motion.py::spread(prior, role, state, params)` diffuses mass through
the *same* legal-action sets `sdk/actions.py` uses to play the engine — an interior thief spreads
to exactly 5 cells at 0.2 each; a cop's 5 barrier placements collapse onto its own cell alongside
the move-to-self (6/10 stay, 1/10 each neighbour). This is the one function both `predict()` and
the scent-projection step below share, so "how mass moves" is defined exactly once.

**Scent likelihood (D-42).** `strategy/belief_scent.py::scent_likelihood()` inverts a measured
scent strength into an age (via `expected_strength_after`'s closed form — see
[`docs/PRD_scent_map.md`](PRD_scent_map.md) §2), then projects that age forward through `spread()`
to estimate where the opponent is **now**. Two properties are load-bearing, and both were found
by numerical verification before any test was written, not assumed from the spec text:

1. **Read the trail through its single freshest cell**, not every cell above the epsilon floor
   independently — an earlier per-cell-bucket design left a symmetric deposit's `argmax` pinned
   at the deposit cell forever, because `spread()`'s legal-action set always includes STAY and a
   symmetric random walk's own highest-probability cell never leaves its origin (a textbook, not
   incidental, property).
2. **Drop the deposit cell's own projected weight once its age ≥ 1.** A fresh reading (age 0) is
   exempt — the opponent may genuinely still be there — but a stale reading is itself evidence
   against "never moved": had the opponent stayed, its own continued emission would have kept the
   reading at full strength.

Both fixes were verified against the board's exact centre `(3,3)` — the thief's real starting
cell, and the worst-case symmetry point for this class of bug — at every step count from 1 to 10,
not merely the more forgiving off-centre cases.

## 4. The hint likelihood (D-40) and `NO_EVIDENCE`

`strategy/belief_hint.py::hint_likelihood(inference, reliability, board_size, config)` implements
the book's mixing formula:

```
L(c) = w · [r · q(c) + (1 − r) · u(c)] + (1 − w) · u(c)
```

`w` is `hint_likelihood.weight` — the fixed config mixing weight, validated at load to be strictly
below `scent_likelihood.weight` by name (shipped: `w = 0.3` against scent's `4.0`) — the book's
own instruction that a hint is weighted below scent because "scent cannot lie, words can" (D-40).
`r` is the adaptive reliability coefficient (§5). `q(c)` concentrates on the claimed
region/cells; `u(c)` is uniform. A confidence-0 inference (`NO_EVIDENCE`, or any decoded hint the
decoder could not read) produces an **all-zero** grid — deliberately different from
`scent_likelihood`'s neutral-1.0 convention — so `BeliefMap.update()`'s own zero-product guard
turns it into an **exact, bit-for-bit** no-op posterior, not merely an approximately-unchanged
one. A confident hint never zeroes any cell outside the claimed region either, since
`(1 − w)·u(c) > 0` always (the config enforces `r_max < 1` strictly) — a lie can shift mass, it
cannot erase a possibility.

A heading riding **alongside** a region or cell claim tilts the distribution within that claimed
set toward cells further in that direction, without ever zeroing a cell in the set. A standalone
heading with nothing to anchor it (the decoder's own convention: a bare heading decodes at
confidence 0, `04-07-SUMMARY.md` Interface note 2) produces a flat, unshifted distribution.

## 5. Reliability and the §4.4 lie detector — D-51, a disclosed revision of D-40

**`04-CONTEXT.md`'s locked decision (D-40) reads "hint trust: fixed discount weight."** The
shipped code has **both** a fixed weight `w` (§4 above, unchanged, still fixed, still below
scent's weight) **and** a second, independent, adaptive coefficient `r`
(`strategy/reliability.py::Reliability`) — the book's own §4.4 mechanism, which D-40's "fixed"
framing did not anticipate. **This is stated here as a revision, not smoothed into an extension**,
because a reader comparing `04-CONTEXT.md` to the shipped code would otherwise see a locked
decision walked back with no explanation — exactly what rule 38 (never misreport what actually
ran) exists to punish, even though rule 38 itself is about game-count declarations rather than
design documents; the standard it sets is the one this disclosure honours.

**Why the revision was necessary.** §4.4 (book p.30, PDF 46) gives a fully worked example: a
thief declares "I moved north," the field's expected strength there (from
`expected_strength_after`, §2 above) is `(1−ρ)·0.9 ≈ 0.81`, the measured strength is `0.00`, and
the book's own text concludes: *"The cop concludes with high confidence that the thief is lying.
It lowers the trust coefficient it assigns to that opponent's verbal declarations."* A constant
coefficient would leave the book's single most concrete worked mechanism entirely unimplemented.
Taken under the autonomy directive (`[[autonomy-directive-phase-3-onward]]`), the mandate is: the
book's own mechanism outranks a config label written before this session's book-reading pass.

**`strategy/scent_check.py::contradicts()`** reproduces the worked example exactly: a field
holding `0.81` (computed from the real shipped `scent.json` numbers via
`expected_strength_after(model, 1)`, never retyped as a literal) at the claimed cell and `0.00`
elsewhere scores `1.0` for a claim naming the empty direction and `0.0` for a claim naming the
loaded one. `contradicts()`'s expected value always uses one turn of projection
(`expected_strength_after(model, 1)`) — a location claim is read as "I was here **this** turn,"
matching the book's own example, not a variable recency inferred from the sentence.

**`strategy/reliability.py::Reliability`** is one bounded coefficient
`r ∈ [r_min, r_max]`, per opponent, per game (never persisted, never shared — rule 2), seeded at
a configured prior and moved by `observe(contradiction_score)`: a positive score pulls `r` down
toward `r_min` at `contradiction_step`; an exact-zero score (fully consistent) pulls it back up
toward the prior at `recovery_rate`. Measured (not merely bounded): 1000 maximal-contradiction
observations settle `r` **exactly** at `r_min`; 1000 fully-consistent observations settle it
**exactly** at the prior.

**The reliability trajectory, reproduced end to end** (10 joint turns, opponent truly at `(6,6)`
throughout, shipped config `prior=0.5, r_min=0.05, r_max=0.95, contradiction_step=0.3,
recovery_rate=0.05`):

| Opponent | Reliability trajectory (turn 0 = prior, turns 1–10) | Final belief `argmax` |
|---|---|---|
| **Fully truthful** (claims south-east every turn) | `0.5` for all 11 values | `(6, 6)` — the truth |
| **Fully lying** (claims north-west every turn) | `0.5, 0.2, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05` | `(6, 6)` — the truth |

The lying opponent's trust collapses to the floor within two contradictory observations and stays
there; the truthful opponent's trust never moves. **In both cases the fused posterior's `argmax`
tracks the real scent trail, never the claim** — the book's closing line under §6.4, that the
scent map cannot lie, holds numerically on this codebase's own locked numbers, not just as prose.
Reproduced by `tests/unit/strategy/test_belief_fusion_e2e.py`.

`hint_likelihood.weight` (fixed, §4) and `reliability.prior` (adaptive, this section) are **two
independent `belief.json` fields**, not one number reused twice — D-40's mechanical content
(a fixed mixing weight below scent's) survives unchanged; what D-40's *label* called "hint trust"
is the thing that became adaptive.

## 6. The two regimes, and what the belief map contributes in each

| Regime | Opponent's pre-turn cell | What the belief map does |
|---|---|---|
| **A** (Reveal integrable) | known exactly, one turn stale | `observe_exact` then `predict`: a genuine one-turn-ahead posterior over legal successor cells, refined by any hint that arrived |
| **B** (Reveal missing/opaque) | unknown | `predict` alone, fed only by `scent_likelihood`/`hint_likelihood`: a full diffusing posterior with no exact anchor |

**The honesty clause — stated in plain words, not smoothed over.** In Regime A, the mover
(`strategy/valuebrain.py::ValueSearchBrain`, Phase 3, unchanged by this phase) builds its payoff
matrix from `GameState`, which under Option A (§7) already carries the **believed** opponent cell
substituted in. In Regime A that believed cell is one legal-motion step from a position the
opponent's own last Reveal already told us exactly — so the belief map's *scoring* contribution
in Regime A is real but bounded: it supplies the opponent-action prior and the sampled target,
not a correction to information we did not already have. **The belief map's value in Regime A is
not primarily about move quality.** It is, in order:

1. **LANG-05 compliance** — a Bayesian belief map genuinely runs from scent + hints every turn,
   satisfying the requirement on its own terms even when Regime A makes its scoring contribution
   modest.
2. **The opponent-action prior and the sampled target** the mover actually consumes (§7) — a real,
   if narrow, input.
3. **The deception channel** — the belief map is the surface our own hints are designed to shape
   in the **opponent's** mirrored instance of this same mechanism (see
   [`docs/PRD_deception.md`](PRD_deception.md)).
4. **Regime B survival** — the same object, unmodified, is what carries the whole burden of
   position estimation the moment a peer's Reveal becomes missing or opaque. This is where the
   mechanism's real work is visible.

Overclaiming Regime A's contribution to move *scoring* would be the kind of overstatement rule 38
exists to punish in a different context; this document states the honest, narrower claim instead.

## 7. From belief to move — `BeliefAdapter`, Option A, and D-43 (sample, not `argmax`)

`docs/phases/phase-3/PRD.md` §8 left Phase 4 an open design question: how does a belief
distribution reach a mover (`ValueSearchBrain`) that was built to read a single true `GameState`?
Two options were on the table:

| Option | What it means | Cost |
|---|---|---|
| **A — believed state** (shipped) | substitute the belief-sampled cell for the opponent's true cell in a `GameState`, via `dataclasses.replace`; the unmodified mover reasons over it | cheap; discards the belief's uncertainty at the point of use |
| **B — expectation over the belief** | build the payoff matrix as a belief-weighted expectation over every candidate opponent cell | correct under partial observability; multiplies the per-decision matrix expansion by the candidate-cell count |

**Option A shipped**, per Phase 3's own cost argument, now measured rather than merely asserted:
belief-enabled per-turn decision time is **cop max 4.99ms, thief max ~3.7–4.99ms**, against the
`strategy.max_decision_ms = 50ms` budget — comfortably inside it with the belief pipeline's own
predict/update×2/sample cost included on top of the matrix mover's own ~2–5ms (Phase 3, AC-6). The
substitution is proven correct in **both** regimes: in Regime A, a boxed-in opponent (only STAY
legal) reproduces the identity exactly, for any RNG draw — a structural guarantee, not a lucky
seed; in Regime B, the substituted state is proven to differ from the true state in the opponent's
coordinate **only** — cop, barriers, quota and turn all pass through untouched.

**`strategy/valuebrain.py`, `matrix.py`, `features.py`, and `equilibrium.py` are unmodified by
this phase** (`git diff --stat` empty across every commit that built `BeliefAdapter`) — the mover
Phase 3 shipped reasons over the substituted state exactly as it always reasoned over the true
one.

**D-43 — we sample from the belief, `BeliefMap.sample(rng)`, where §6.4's own worked figure shows
`argmax_s b(s)` as the displayed target.** This is a deliberate departure from the book's literal
figure, taken under the autonomy directive, for a reason specific to this league's format: a
deterministic `argmax` target makes our own pursuit fully predictable to an opponent capable of
modelling our belief state, and rule 52 gives each opponent exactly **one** counted game — there
is no adaptation window in which exploitable determinism could be corrected mid-series. Sampling
is seeded (`random.Random`, never the module RNG or `secrets`) so a replay reproduces
byte-identically (rule 20); two independently constructed `BeliefAdapter`s with the same seed
produce byte-identical decision sequences over a scripted game.

## 8. Compliance

- **LANG-05** — the belief map updates via Bayes from scent + hint evidence, in both regimes.
- **Rule 2** — `BeliefMap`/`Reliability`/`BeliefAdapter` are all constructed fresh per process,
  per game; never a shared or persisted object across the cop/thief boundary.
- **Rule 25 / STRAT-07** — the belief pipeline lives entirely under `strategy/`, which
  `scripts/check_no_llm_in_strategy.py` proves imports no LLM/network module; the LLM never
  chooses the move, it only produces the text the belief map's hint-likelihood step reads.
- **Segal Table 5** — every belief-related module ≤150 code lines (four `belief.json`-owning
  modules were split at the ceiling as the config grew across plans 04-05/04-09/04-11, never
  compressed); zero hardcoded values (every threshold is a named `belief.json` field, labelled an
  engineering default where it is not traced to `docs/PARAMETERS.md`).

## 9. Acceptance criteria and links to the plans that built it

| Criterion | Measured by |
|---|---|
| `BeliefMap` stays a valid distribution through any operation sequence | `tests/unit/strategy/test_belief.py` |
| Scent likelihood does not chase the strongest cell directly (D-42) | `tests/unit/strategy/test_belief_scent.py`, 4 starting cells × 10 turns |
| §4.4 worked example reproduced exactly (0.9 → 0.81) | `tests/unit/strategy/test_scent_check.py` |
| Reliability settles exactly at its bounds under extremes | `tests/unit/strategy/test_reliability.py` |
| Fused posterior tracks scent, not the claim, in both a lying and a truthful run | `tests/unit/strategy/test_belief_fusion_e2e.py` |
| Believed-state substitution is exact in Regime A, coordinate-only in Regime B | `tests/unit/strategy/test_beliefadapter.py` |
| Belief-enabled decision time inside the 50ms budget | `tests/integration/test_belief_policy.py` |

**Built by:** plan 04-05 (`BeliefMap`, motion model, scent likelihood), plan 04-09 (reliability,
scent-contradiction detector, hint likelihood), plan 04-11 (`BeliefAdapter`, Option A, D-43,
registry wiring), plan 04-12 (live wiring into the turn loop, the regime decision computed once
per turn).

**Requirements covered:** LANG-05 (Bayesian belief map from scent + hints).

---

*Phase: 04-language-and-scent · Numbers traced to 04-05-SUMMARY.md, 04-09-SUMMARY.md,
04-11-SUMMARY.md.*
