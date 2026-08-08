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
"""

from __future__ import annotations

import random

from pursuit.shared.config import GameParams
from pursuit.shared.deception_config import DeceptionParams
from pursuit.shared.deception_types import (
    ALWAYS_TRUE_KINDS,
    ClaimKind,
    DeceptionPlan,
    Intent,
)
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


def declare_truthfully(kind: ClaimKind) -> DeceptionPlan:
    """The one constructor for a barrier or capture declaration.

    Rules 15/16 and 21/22 make these always truthful, and a false capture
    claim is immediate disqualification with zero score and no appeal. There
    is deliberately no `intent` argument: the caller cannot pass the wrong
    one because there is nowhere to pass it.

    Raises
    ------
    ValueError
        If `kind` is not one of the always-true kinds -- a location or
        heading claim carries a sector or a heading and must come from a
        policy, never from this shortcut.
    """
    if kind not in ALWAYS_TRUE_KINDS:
        raise ValueError(
            f"declare_truthfully is only for {sorted(k.value for k in ALWAYS_TRUE_KINDS)}, "
            f"got {kind.value!r} -- build a {kind.value} claim through plan_deception"
        )
    return DeceptionPlan(intent=Intent.TRUTH, kind=kind)
