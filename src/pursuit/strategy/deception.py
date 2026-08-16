"""D-36: the ALGORITHM decides what to claim and whether it is true.

This is the module that makes rule 25 / STRAT-07 structural rather than
aspirational. It returns a `DeceptionPlan` -- an intent flag and a claim,
both chosen from the board and the belief map -- and plan 04-10 turns that
into fifteen English tokens with no say in either field. The proof is not
this docstring: `scripts/check_no_llm_in_strategy.py` fails CI if anything
under `strategy/` imports a model client, and it is run as a gate.

Book Sec6.2 Figure 7 places this stage AFTER the move choice and BEFORE the
outgoing text, which is what lets a claim reference the move already
committed to -- a lie that contradicts our own action is not deception, it is
noise. LANG-03's ordering is enforced by the type: `DeceptionPlan` exists
before any phrasing does, and Phase 6 seals the flag alongside the move.

`plan_deception` never returns None. A turn always carries a hint (LANG-01),
so a policy that cannot think of a worthwhile lie returns a truthful claim
instead of nothing.

WHERE THE BARRIER AND CAPTURE DECLARATIONS ACTUALLY LIVE (05-15, G10) --
written down here so the question is not re-opened by the next reader.
This module used to export `declare_truthfully(kind)`, whose docstring
called it "the one constructor for a barrier or capture declaration" for
rules 15/16 and 21/22. It had ZERO production callers for its whole life
(measured: `grep -rn declare_truthfully src/` returned only its own
definition and its own error string), and that docstring MISDESCRIBED the
design badly enough that a reviewer read a rules violation into it. It is
deleted. Neither rule is unmet, and neither is met by this module:

- Rule 15, quoted from docs/RULES.md: MUST "Declare every barrier placement
  openly", sanction "Board forgery and automatic loss at audit". Rule 16:
  FORBIDDEN "Lie about where a barrier was placed", sanction "Severe
  disqualification cause". Both are satisfied by the COMMITTED ACTION, not
  by an utterance: `docs/PRD_commit_reveal.md` Sec2.2 (D-66/SEC-07) puts the
  barrier inside the composite `{move, barrier}` dict that crosses the wire
  in REVEAL, is hashed into `H_commit`, and is cross-checked at audit
  (D-67). Rule 15's own sanction is audit-shaped, which is the shape that
  design answers.
- Rule 21, quoted: MUST "Declare the truth **only** at the moment of
  capturing a thief", sanction "Immediate disqualification for denying
  reality". Rule 22: FORBIDDEN "Make a false capture declaration", sanction
  "**Immediate disqualification**, zero score, technical loss, no appeal".
  The capture declaration is a PROTOCOL message driven by the resolved
  outcome (`network/capture_declaration.py`, 05-15) -- never a sentence a
  policy or a model composes, because rule 22's sanction is the reason it
  must not be composable by anything that could choose.

What binds in THIS package is `DeceptionPlan.__post_init__`
(`shared/deception_types.py`, docs/PRD_deception.md Sec2): it refuses an
`Intent.LIE` plan on either always-true kind, and `dataclasses.replace`
re-runs it, so there is no construction path -- helper, replace, or test
double -- that can produce a lying declaration. Deleting a convenience
constructor cannot weaken that, because the constructor was never the gate.
No name here can even mention an always-true kind any more: `ClaimKind`,
`ALWAYS_TRUE_KINDS` and `Intent` are no longer imported by this module.
"""

from __future__ import annotations

import random

from pursuit.shared.config import GameParams
from pursuit.shared.deception_config import DeceptionParams
from pursuit.shared.deception_types import DeceptionPlan
from pursuit.shared.state import GameState
from pursuit.strategy.belief import BeliefMap
from pursuit.strategy.deception_cop import plan_cop_claim
from pursuit.strategy.deception_thief import plan_thief_claim

#: The two seats, matching GameState's own field names (belief_motion.ROLES).
ROLES = ("cop", "thief")


def plan_deception(
    role: str,
    state: GameState,
    params: GameParams,
    belief: BeliefMap,
    rng: random.Random,
    config: DeceptionParams,
    *,
    scent=None,
    weights: tuple | None = None,
) -> DeceptionPlan:
    """Build this turn's claim for `role`.

    Dispatches to the role policy -- the thief's danger-adaptive lying
    (D-37), the cop's herding (D-38) -- and returns whatever it produced. The
    always-true carve-outs of rules 15/16 and 21/22 need no check here:
    neither policy can generate those kinds at all, and `DeceptionPlan`'s own
    constructor refuses to build one as a lie regardless of which code path
    tries.

    `scent` (the thief's own trail, for the Sec4.4 self-contradiction check)
    and `weights` (the cop's evaluation vector) are keyword-only and optional
    -- each policy degrades sensibly without its own, and 04-12 supplies both.
    """
    if role == "thief":
        return plan_thief_claim(state, params, belief, rng, config, scent=scent)
    if role == "cop":
        return plan_cop_claim(state, params, belief, rng, config, weights=weights)
    raise ValueError(f"plan_deception: role must be one of {ROLES}, got {role!r}")
