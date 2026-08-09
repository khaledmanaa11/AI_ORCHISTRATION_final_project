"""D-37: the thief lies more as the cop closes in, and never stops telling
the truth entirely.

Two properties matter more than the exact shape of the curve between them:

**A truth floor.** Even at maximum danger some turns are honest. D-37 calls
this sprinkling truths so the lies stay credible; mechanically it stops the
opponent's own reliability coefficient (the mirror of our D-51) from
collapsing to its lower bound, after which every claim we make is discounted
to nothing and the channel is worthless. An always-lying agent is exactly as
readable as an always-truthful one.

**The lie has to survive a scent check.** Book Sec4.4 works the attack
through in the opponent's voice: a declared heading, an expected trail
strength there, a measured strength of nothing, and the conclusion that the
speaker is lying. Our claims are chosen knowing the opponent may run that
same test, so a claim landing on our own freshest trail is not a lie, it is a
confession. Candidates are scored by how far they sit from the sector our
trail betrays, and one is drawn from the best few.

Every threshold is an engineering default in `deception.json` (D-18), and
nothing here builds any text -- this module decides MEANING and hands it to
04-10 to phrase.
"""

from __future__ import annotations

import random

from pursuit.shared.config import GameParams
from pursuit.shared.deception_config import DeceptionParams
from pursuit.shared.deception_types import ClaimKind, DeceptionPlan, Intent
from pursuit.shared.inference import Region
from pursuit.shared.state import GameState
from pursuit.strategy.belief import BeliefMap
from pursuit.strategy.regions import region_distance, region_of


def expected_opponent_distance(belief: BeliefMap, own_cell: tuple, board_size: int) -> float:
    """Expected Manhattan distance to the opponent, over the WHOLE posterior.

    Deliberately not the distance to `belief.argmax()`. A bimodal belief with
    one close mode is precisely the situation where the argmax misleads: it
    names the single likeliest cell and says nothing about the mass sitting
    two steps away, so an agent trusting it feels safe at the exact moment it
    should be lying hardest.
    """
    posterior = belief.posterior()
    return sum(
        posterior[row][col] * (abs(row - own_cell[0]) + abs(col - own_cell[1]))
        for row in range(board_size)
        for col in range(board_size)
    )


def lie_probability(distance: float, config: DeceptionParams) -> float:
    """How likely we are to lie at `distance`, falling monotonically as the
    estimated cop distance grows.

    Flat at the ceiling inside `danger_distance`, flat at the floor beyond
    `safe_distance`, linear between. The ceiling is derived from
    `truth_floor` rather than configured separately, so the floor cannot be
    contradicted by a second number.
    """
    if distance <= config.danger_distance:
        return config.max_lie_probability
    if distance >= config.safe_distance:
        return config.min_lie_probability
    span = config.safe_distance - config.danger_distance
    travelled = (distance - config.danger_distance) / span
    return config.max_lie_probability - travelled * (
        config.max_lie_probability - config.min_lie_probability
    )


def plan_thief_claim(
    state: GameState,
    params: GameParams,
    belief: BeliefMap,
    rng: random.Random,
    config: DeceptionParams,
    *,
    scent=None,
) -> DeceptionPlan:
    """The thief's claim for this turn: a sector, and whether it is true.

    `scent` is this peer's own `ScentField` and is optional: without it the
    contradiction check is skipped and the lie is merely chosen away from the
    true sector. 04-12 supplies the real field. Skipping degrades the quality
    of the lie; it never blocks the turn, because LANG-01 requires a hint
    every turn regardless.
    """
    board = params.board_size
    true_region = region_of(state.thief, board)
    distance = expected_opponent_distance(belief, state.thief, board)
    if rng.random() >= lie_probability(distance, config):
        return DeceptionPlan(
            intent=Intent.TRUTH,
            kind=ClaimKind.LOCATION,
            claimed_region=true_region,
            true_region=true_region,
        )
    return DeceptionPlan(
        intent=Intent.LIE,
        kind=ClaimKind.LOCATION,
        claimed_region=_survivable_lie(true_region, board, rng, config, scent),
        true_region=true_region,
    )


def _betrayed_region(scent, board_size: int) -> Region | None:
    """The sector our own freshest trail points at, or None when we have no
    trail yet (turn zero) or no field was supplied."""
    if scent is None:
        return None
    freshest = scent.freshest("own")
    return None if freshest is None else region_of(freshest, board_size)


def _survivable_lie(
    true_region: Region,
    board_size: int,
    rng: random.Random,
    config: DeceptionParams,
    scent,
) -> Region:
    """A claimed sector that is neither where we are nor where our trail says
    we are, drawn from the `lie_candidate_pool` sectors furthest from the
    betraying one.

    Drawing from a pool rather than taking the single furthest sector keeps
    the claims from becoming a readable pattern -- always naming the opposite
    corner is itself information. The draw uses the injected RNG (D-43's
    discipline), so a seeded game replays identically.
    """
    betrayed = _betrayed_region(scent, board_size)
    if betrayed is None:
        betrayed = true_region
    # Never empty, and deliberately without a fallback branch: the two
    # exclusions remove at most two of the nine sectors, so seven candidates
    # always remain. A defensive `if not candidates` here would be
    # unreachable code that no test could honestly cover.
    candidates = [r for r in Region if r is not true_region and r is not betrayed]
    ranked = sorted(
        candidates, key=lambda r: (-region_distance(betrayed, r, board_size), r.value)
    )
    return rng.choice(ranked[: config.lie_candidate_pool])
