"""D-38: the cop's claims herd, they do not hide.

The cop's objective is different in kind from the thief's. The cop's own
position is the less valuable secret -- the thief's next step is the prize --
so a claim is chosen for the movement it CAUSES, not for the concealment it
buys. A thief that believes *"the cop is over by the river"* walks away from
the river, and if the cop has walled the other side, the claim did work the
cop's legs could not do in one turn.

The scoring reuses the Phase-3 evaluation rather than inventing a second
notion of control: `features.value` already knows that the cop wins by
driving the thief's region toward a forest, and that territory and
chokepoints are how that happens. A fresh heuristic here would be a second,
unvalidated opinion about the same question.

**The lookahead is deliberately one step.** Modelling how the thief's belief
map actually updates is a research project whose assumptions would be
unverifiable in a league game where we never see the opponent's internals.
One step is a claim we can defend.
"""

from __future__ import annotations

import random
from dataclasses import replace

from pursuit.sdk.actions import thief_actions
from pursuit.shared.config import GameParams
from pursuit.shared.deception_config import DeceptionParams
from pursuit.shared.deception_types import ClaimKind, DeceptionPlan, Intent
from pursuit.shared.inference import Region
from pursuit.shared.state import GameState
from pursuit.strategy.belief import BeliefMap
from pursuit.strategy.features import value
from pursuit.strategy.regions import region_center, region_of
from pursuit.strategy.weights import PRIOR


def plan_cop_claim(
    state: GameState,
    params: GameParams,
    belief: BeliefMap,
    rng: random.Random,
    config: DeceptionParams,
    *,
    weights: tuple | None = None,
) -> DeceptionPlan:
    """The cop's claim for this turn: the sector that, if believed, drives the
    thief somewhere the cop would rather it went.

    Falls back to the truth when no claim beats it by `min_herding_gain` --
    a lie that buys nothing still spends credibility, and credibility is the
    resource that makes the NEXT lie work.

    `rng` is accepted and unused: the cop's choice is fully determined by the
    board, and a tie breaks on sector name rather than on a draw. It stays in
    the signature so both role policies remain interchangeable behind
    `plan_deception`, and so a future stochastic variant is a change of body
    rather than of interface. `belief` is likewise unused today -- the thief's
    believed position enters only through the evaluation of the successor
    state, which reads the true board.
    """
    board = params.board_size
    scoring = weights if weights is not None else PRIOR
    true_region = region_of(state.cop, board)
    baseline = _herded_value(true_region, state, params, scoring)

    # Negated score first so `min` picks the BEST claim, with the sector name
    # as the tie-break -- an alphabetical tie-break is arbitrary but stable,
    # and a stable choice is what makes a seeded game replay byte-identically.
    best_negated, _, best_region = min(
        (-_herded_value(candidate, state, params, scoring), candidate.value, candidate)
        for candidate in Region
        if candidate is not true_region
    )
    if -best_negated - baseline <= config.min_herding_gain:
        return DeceptionPlan(
            intent=Intent.TRUTH,
            kind=ClaimKind.LOCATION,
            claimed_region=true_region,
            true_region=true_region,
        )
    return DeceptionPlan(
        intent=Intent.LIE,
        kind=ClaimKind.LOCATION,
        claimed_region=best_region,
        true_region=true_region,
    )


def _herded_value(
    believed_region: Region, state: GameState, params: GameParams, weights: tuple
) -> float:
    """The cop-perspective value of the position a thief believing
    `believed_region` would step into.

    Note the two different boards. The thief chooses against the board it
    BELIEVES -- cop substituted at the claimed sector's centre -- and the cop
    scores the position that actually results, with itself where it really is.
    That gap between the two boards is the entire value of a lie.

    Higher is better for the cop: `features.value` is always evaluated from
    the cop's seat and the thief's value is its negation, so no second sign
    convention is introduced here.
    """
    believed_cop = region_center(believed_region, params.board_size)
    step = _believing_step(state, params, believed_cop, weights)
    return value(weights, replace(state, thief=step), params)


def _believing_step(
    state: GameState, params: GameParams, believed_cop: tuple, weights: tuple
) -> tuple:
    """Where a thief that trusts the claim steps.

    Modelled with the SAME evaluation the cop uses rather than with a "run
    away from the believed cell" rule of thumb: a distance heuristic ties
    across most of the legal set on an open board, which would leave the
    claim with no lever at all, and it also ignores the structural facts
    (territory, chokepoints, cycle rank) that decide this game. The thief
    minimises the cop-perspective value because the game is zero-sum.

    Ties break toward the lowest cell in row-major order -- the same
    deterministic-ordering convention `belief.argmax` and `sdk/actions.py`
    already use -- so a replay reproduces the same choice.
    """
    believed = replace(state, cop=believed_cop)
    return min(
        thief_actions(state, params),
        key=lambda cell: (value(weights, replace(believed, thief=cell), params), cell),
    )
