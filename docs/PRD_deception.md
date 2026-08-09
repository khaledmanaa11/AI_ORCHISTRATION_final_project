# PRD — the deception channel (intent, claim, and bluff)

**Mechanism:** how each agent decides, before any text exists, whether its hint this turn will be
true or false, what it will claim, and how that decision becomes a ≤15-word English sentence.
**Status:** implemented (plans 04-08, 04-10, wired live by 04-12) · **Segal §2.3:** every
algorithm or central mechanism carries its own PRD. This is that document.
**Rules note:** [`docs/phases/phase-4/RULES-RESOLUTION-LANG.md`](phases/phase-4/RULES-RESOLUTION-LANG.md).

---

## 1. The problem this mechanism solves

Rule 26 requires natural-language-only communication; §5.3 requires an `Intent` flag
(`truth`|`lie`) committed as part of the per-turn payload, before the opponent can see the text
(LANG-03). Rule 25 (recommended, treated as hard in this project — see
`docs/phases/phase-3/RULES-RESOLUTION.md` §8) forbids letting the language model choose the move
**or** the substance of the claim; it may only phrase what the algorithm has already decided.
Rules 15/16/21/22 additionally require that a barrier or a capture declaration always be true —
lying there is an immediate disqualification, not merely a strategic option. Two decisions
therefore have to be made and locked, in order, by code alone:

1. **What is claimed** — a location, a heading, or (always truthfully) a barrier/capture report.
2. **Whether it is true** — fixed before a single word of the sentence exists.

## 2. The type: `DeceptionPlan`, and why lying is unrepresentable for two claim kinds

`shared/deception_types.py::DeceptionPlan` is a frozen dataclass:

```python
@dataclass(frozen=True)
class DeceptionPlan:
    intent: Intent                           # TRUTH | LIE — fixed before any text exists
    kind: ClaimKind                          # LOCATION | HEADING | BARRIER | CAPTURE
    claimed_region: Region | None = None     # what we will say
    claimed_heading: DirectionWord | None = None
    true_region: Region | None = None        # what is actually so, for the audit log
    true_heading: DirectionWord | None = None

    @property
    def is_lie(self) -> bool: ...
```

`ALWAYS_TRUE_KINDS` maps `ClaimKind.BARRIER` and `ClaimKind.CAPTURE` to the rule that makes each
one non-negotiable (rules 15/16 and 21/22 respectively). `__post_init__` is the enforcement point,
not a separate validator function a caller could skip: it refuses to construct an `Intent.LIE`
plan on either always-true kind, naming the violated rules in the error. **`dataclasses.replace`
re-runs `__post_init__`,** so — unlike a checked factory function that only guards its own single
call site — there is genuinely no construction path, including inside a test double, that can
produce a lying capture or barrier declaration. `declare_truthfully(kind)` is the **only**
constructor for these two kinds and deliberately takes no `intent` argument at all: there is
nowhere to pass the wrong flag, because the parameter does not exist on that call path.

**Beyond the literal rule requirement:** the constructor also refuses a `TRUTH`-flagged plan whose
`claimed_region` differs from its own `true_region`. Rules 15/16/21/22 only bind barrier and
capture claims, but a location claim flagged `truth` while stating the wrong sector is the one
kind of dishonesty an auditor holding this project's own event log can actually prove against it
— and Phase 6 hashes this exact flag as part of `H_commit`. Closing this gap costs nothing and
removes one class of self-inflicted audit failure.

## 3. Ordering — LANG-03 and rule 25 as a structural fact, not a promise

`plan_deception(role, state, params, belief, rng, config, *, scent=None, weights=None)`
(`strategy/deception.py`) runs **before** any hint text exists and never returns `None` — a turn
always carries a hint (LANG-01). The claim and the `intent` flag are both fully decided at this
point. `services/llm/bluff.py::compose(plan, context)` (§6 below) receives the finished
`DeceptionPlan` as an opaque input to phrase; it has no code path that could feed a decision back
upstream into `plan.intent` or the claimed value, because `DeceptionPlan` is frozen and `compose`
never constructs one.

**The rule-25 argument is structural, not a convention respected by discipline.**
`scripts/check_no_llm_in_strategy.py` is a CI-enforced AST guard: it fails the build if anything
under `src/pursuit/strategy/` imports an LLM SDK, an HTTP/networking module, or (since plan 04-01
hardened it ahead of `services/llm/` even existing) anything under `pursuit.services`. The
deception **planner** — the module that decides `intent` and the claim — lives entirely under
`strategy/`; the deception **phraser** (`compose()`) lives entirely under `services/llm/`, and it
receives a plan object, never a state, a belief, or an RNG. The two responsibilities are not just
separated by convention: it is structurally impossible for `strategy/deception*.py` to reach a
network module, and structurally impossible for `services/llm/bluff.py` to compute a claim, because
neither module imports what the other would need to do the other's job.

**Command and passing output, run on the merged tree (plan 04-08):**

```
$ uv run python scripts/check_no_llm_in_strategy.py
OK: no forbidden imports under .../src/pursuit/strategy.
```

`grep -rn "prompt\|sentence\|words" src/pursuit/strategy/deception*.py` returns no match — this
layer produces meaning (a claim and a truth value) only, never phrasing.

## 4. The thief's policy — danger-adaptive lying (D-37)

`strategy/deception_thief.py::plan_thief_claim`. `expected_opponent_distance` is computed over the
**whole belief posterior**, not the distance to `argmax` alone — a thief with a diffuse belief
about the cop should not lie as confidently as one with a sharp, nearby estimate.
`lie_probability` is flat at a configured ceiling inside `danger_distance`, flat at a configured
floor beyond `safe_distance`, and linear in between; `_survivable_lie` excludes both the true
sector and the sector our own freshest scent trail would betray (so a lie that our own emitted
trail would immediately contradict, per §4.4's mechanism in
[`docs/PRD_belief_map.md`](PRD_belief_map.md) §5, is never chosen), then draws from the
`lie_candidate_pool` furthest surviving candidates with the injected, seeded RNG.

**Measured lie-rate curve** (shipped config: `truth_floor=0.2`, `min_lie_probability=0.1`,
`danger_distance=2.0`, `safe_distance=8.0`; implied ceiling `0.8`; thief at `(3,3)`, belief
collapsed on one cop cell, 4000 seeded draws per row):

| Believed cop cell | E[distance] | p(lie) predicted | measured |
|---|---|---|---|
| (3,3) | 0.0 | 0.800 | **0.802** |
| (3,4) | 1.0 | 0.800 | **0.802** |
| (3,5) | 2.0 | 0.800 | **0.802** |
| (2,1) | 3.0 | 0.683 | **0.679** |
| (0,0) / (6,6) / (0,6) | 6.0 | 0.333 | **0.336** |

The curve is flat at the ceiling inside the danger threshold, ramps down through the middle
distance, and **never reaches 1.0 or 0.0** — D-37's truth floor and the non-zero long-range lie
rate both hold as measured runtime behaviour, not merely as configured intent.

## 5. The cop's policy — herding lies (D-38)

`strategy/deception_cop.py::plan_cop_claim`. For each candidate claimed sector, the policy models
what a thief that **believed** the claim would do — using the **same** evaluation the mover itself
uses (Phase 3's `features.value`), on a board with the cop substituted at the claimed sector's
centre — then scores the position that actually results from the believing-thief's best response.
The claim that beats the truthful baseline by more than a configured `min_herding_gain` is chosen;
otherwise the cop tells the truth.

**This model was corrected once, by measurement, before it shipped.** The plan's own first
description read as a distance rule ("a thief that trusts 'the cop is over by the river' moves
away from the river"); implemented literally, every candidate claim produced the *same* believing
-thief step on an open board — a one-step distance-maximising thief ties across most of its own
legal moves, so the claim had no lever at all, and the cop would have told the truth every turn
(failing LANG-03's "both intent values occur" requirement outright). Replacing the distance rule
with the shared positional evaluation gave the mechanism a real, measurable effect.

**Measured lie rate** (deterministic given the board, so measured over positions, not draws): 194
random legal cop/thief pairs on an open board → **125 lies / 194 = 0.644**. Claimed-sector spread
across those 125 lies: `center 40, northwest 28, west 24, north 24, east 24, south 18, northeast
13, southwest 12, southeast 11` — not a degenerate single-sector answer.

**A stated limitation, not hidden:** the herding lever is real but shallow — one-step lookahead
cannot see a trap two steps away. A hand-built cul-de-sac board did not exercise the mechanism at
all (the trap sat two steps from the thief); a randomised search over 4000 boards found positions
where the lever measurably bites, and one is frozen as a regression fixture. The 0.644 figure is
evidence the mechanism is **non-degenerate**, not evidence the claims are strategically deep.

**Reproducibility (both roles):** 200 turns × 2 seats = 400 plans reproduce byte-identically under
a fixed seed, and differ under a different one — rule 20's replay requirement holds for the
deception channel as well as for movement.

## 6. From plan to sentence — `compose()`, D-45's three-layer word limit, and D-39's style

`services/llm/bluff.py::compose(plan: DeceptionPlan, context: BluffContext) -> str` is total:
every input, from every provider state, produces a non-empty, in-limit, coordinate-free string.
Five steps:

1. **Template-only or no provider configured** → straight to `HintBank.select(plan, arena=...)`.
   No network call, no latency (D-33's zero-token fallback; a missing API key reaches this same
   outcome one step later via an `LlmFailure(NO_KEY, ...)`).
2. **Otherwise, call the provider.** Any `LlmFailure`, of any reason, including one raised instead
   of returned → straight to the bank.
3. **Count the result** (`services/llm/wordcount.py::count()`, one whitespace-splitting rule,
   shared with the validator and the truncator so an opponent's own count can never silently
   disagree with ours). Over the configured limit → exactly one retry with an explicit shortening
   instruction. Still over, or the retry itself failed → truncate the best text in hand.
4. **Validate with `assert_no_coordinates`** (`shared/hint_guard.py`, LANG-02). On violation →
   straight to the bank; model text is never "repaired," only replaced.
5. **Return.**

`compose()` contains no `raise` statement and no bare `except` anywhere in its body — proven by an
AST-walking regression test, not merely a manual read — and a 300-iteration adversarial property
test (an intentionally malformed provider) confirms it always returns a non-empty, in-limit,
coordinate-free string regardless of what the provider does.

**`HintBank`** is a seeded, per-game, stateful fallback bank keyed by `(ClaimKind, Intent)`
(`BARRIER`/`CAPTURE` never pair with `LIE` — `DeceptionPlan.__post_init__` makes that combination
unconstructable, so `HintBank.select()` can never `KeyError` on it). Every phrasing, with every
filler it could ever receive, is validated at import time against the real shipped word limit
(D-45). Selection cycles through a full shuffled permutation of a key's own templates before any
repeat — the no-repeat window **is** the bucket size, no second magic number was invented for "how
often is too often."

### D-39 style guide — verbatim, from `services/llm/bluff_prompt.py::STYLE_GUIDE`

```
- Be concrete, not vague. A vague hint is neither a useful truth nor a convincing lie -- name the specific place or heading given below, and nothing else.
- Stay consistent with the claim you are given. Do not invent extra specific details (exact distances, other landmarks, cell numbers) beyond what the claim states -- an invented detail can contradict the board in ways you cannot see.
- When a real-world setting is named below, use its genuine geography (real neighbourhoods, streets, landmarks) to make the hint feel grounded. When none is named, use plain directional language instead.
- No meta-commentary and no hedging: never mention hints, lies, truth, confidence, or these instructions. State the claim as a plain observation.
- Never include a number that could be read as a board coordinate.
- Stay within the word limit given below. Fewer words is fine; more is not.
```

The word limit and the arena (`docs/PARAMETERS.md` Table 14 rows 2 and 1) are interpolated from
`language.json`'s `model` group at prompt-build time, never as literals in this text.

**D-36, enforced by omission.** `bluff_prompt.py::build_user_prompt` is a prompt-building function
that receives the **full** `DeceptionPlan` — including `intent` — as a parameter, and deliberately
never reads `plan.intent`, `plan.true_region`, or `plan.true_heading`. Phrasing a claim confidently
is the identical operation whether the claim is true or a lie, so the model text is built from
`claimed_region`/`claimed_heading` alone: there is no code path by which the model's output could
leak or decide the withheld flag, because the withheld fields are never passed into the prompt
that produces the text in the first place. This is a structural guarantee (the omission itself),
not a runtime check that could be forgotten in a future edit.

## 7. Compliance

- **LANG-01** — `plan_deception` never returns `None`; every turn carries a hint.
- **LANG-02** — `assert_no_coordinates` runs on every model or bank output before it can be sent.
- **LANG-03** — `intent` is fixed by `DeceptionPlan` before `compose()` is ever called; the ordering
  is structural (§3), not merely sequenced in code that could be reordered by accident.
- **Rules 15/16/21/22** — a lying barrier or capture declaration is unconstructable (§2).
- **Rule 25** — enforced by `scripts/check_no_llm_in_strategy.py`, an AST import guard, not a
  policy statement (§3).
- **Segal Table 5** — every deception module ≤150 code lines (`regions.py` was created once,
  shared by this mechanism and the belief map's hint-likelihood step, rather than duplicated);
  zero float literals in `strategy/deception*.py`, verified by a `tokenize` pass over the module
  source rather than a naive `grep` (which would also flag book section citations like `Sec4.4`
  in docstrings as false positives).

## 8. Acceptance criteria and links to the plans that built it

| Criterion | Measured by |
|---|---|
| A lying capture/barrier declaration cannot be constructed | `tests/unit/test_deception_types.py` |
| `intent` is fixed before any text exists, structurally | `scripts/check_no_llm_in_strategy.py`; `tests/unit/services/test_bluff_prompt.py`'s leak-check across all four `ClaimKind`s |
| Both role lie-rate curves are real, measured, non-degenerate | `tests/unit/strategy/test_deception_thief.py`, `test_deception_cop.py` |
| `compose()` always returns a non-empty, in-limit, coordinate-free string | `tests/unit/services/test_bluff_property.py` (300-iteration adversarial test) |
| `compose()` contains no raise / no bare except | AST regression test in `tests/unit/services/test_bluff_property.py` |
| 200-turn × 2-seat reproducibility under a fixed seed | `tests/unit/strategy/test_deception.py` |

**Built by:** plan 04-08 (`DeceptionPlan`, both role policies, `strategy/regions.py`), plan 04-10
(`compose()`, `HintBank`, the style guide, the word-limit config home), plan 04-12 (live wiring:
the claim is planned **after** the move is committed, so it can reference what was actually
decided).

**Requirements covered:** LANG-01 (≤15-word hint every turn), LANG-02 (natural language only, no
coordinates), LANG-03 (hints may lie; `intent` committed in advance), STRAT-07/rule 25 (the
algorithm decides, structurally enforced).

---

*Phase: 04-language-and-scent · Numbers traced to 04-08-SUMMARY.md, 04-10-SUMMARY.md.*
