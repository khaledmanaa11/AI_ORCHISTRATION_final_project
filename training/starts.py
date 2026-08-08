"""Randomised start-state distribution -- the fix run 1 most needed.

Run 1 played all 300,000 episodes from the single board cop=(0,0), thief=(3,3),
then measured the policy somewhere it had never been. Its cop finished training
beating the heuristic thief 90% of the time and scored 25% at the gate.

This is not merely a generalisation nicety, it is a rules requirement. Book Sec3.3
p.19 marks BOTH start cells *negotiated*, not fixed: "the start points are not
random but strategic, and are not fixed in advance -- they are decided in the
negotiation stage between the two teams, and any legal agreed deployment is
permitted." A policy trained on one opening is trained for a board we may never
be given.

Mid-game states matter as much as openings. Sampling a turn index, a partial
barrier set and a spent quota puts the learner in the endgame positions that
decide games, instead of only the opening tube a single start produces.
"""

from __future__ import annotations

import random

from pursuit.shared.config import GameParams
from pursuit.shared.state import GameState

#: Share of episodes that start from the negotiated opening. Kept deliberately
#: non-zero: it is the one board we know we might actually be given, and the
#: league game is played from an agreed start, not a random one.
BOOK_START_SHARE = 0.30

#: Closest and furthest BFS-free Manhattan separation a sampled start may use.
#: Distance 1 is excluded because it is a forced capture for the cop under rule
#: 46, so it would flood the data with states that have no decision in them.
MIN_SEPARATION = 2


def sample_start(params: GameParams, rng: random.Random) -> GameState:
    """Return a start state: the negotiated opening, or a sampled position."""
    if rng.random() < BOOK_START_SHARE:
        return GameState(
            cop=params.cop_start,
            thief=params.thief_start,
            barriers=frozenset(),
            barriers_placed=0,
            turn=0,
        )
    return _sample_position(params, rng)


def _sample_position(params: GameParams, rng: random.Random) -> GameState:
    """Sample a legal mid-game position with partial barriers and a spent clock."""
    size = params.board_size
    cells = [(row, col) for row in range(size) for col in range(size)]

    turn = rng.randrange(0, max(1, params.survival_threshold - MIN_SEPARATION))
    # Barriers accumulate over the game, so tie the count to how far in we are.
    progress = turn / params.survival_threshold
    placed = min(params.barrier_quota, int(rng.random() * progress * params.barrier_quota))
    barriers = frozenset(rng.sample(cells, placed)) if placed else frozenset()

    free = [cell for cell in cells if cell not in barriers]
    cop, thief = _draw_pair(free, rng)
    return GameState(
        cop=cop, thief=thief, barriers=barriers, barriers_placed=placed, turn=turn
    )


def _draw_pair(free: list, rng: random.Random) -> tuple:
    """Draw two distinct free cells at least MIN_SEPARATION apart.

    Falls back to any distinct pair after a bounded number of attempts so a
    heavily barriered board can never spin here forever.
    """
    for _ in range(32):
        cop, thief = rng.sample(free, 2)
        if abs(cop[0] - thief[0]) + abs(cop[1] - thief[1]) >= MIN_SEPARATION:
            return cop, thief
    return tuple(rng.sample(free, 2))


def distinct_start_count(states) -> int:
    """How many distinct openings a run actually visited.

    Reported as a training gate: a run whose start distribution collapsed is the
    failure that produced run 1's result, and it is invisible in the win curve.
    """
    return len({(state.cop, state.thief, state.barriers, state.turn) for state in states})
