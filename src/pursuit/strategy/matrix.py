"""Build the joint payoff matrix of one turn by one-ply expansion.

The transitions are deterministic, so the matrix is DERIVED on demand rather than
learned: M[i][j] is just the value of resolve_turn(state, cop_action_i,
thief_move_j). That single fact is what makes a sound simultaneous-move method
affordable here -- the usual objection to minimax-Q is that the joint table is
|A_c| x |A_t| times larger than a Q-table and needs that many more samples, but
nothing joint is ever stored. Only a 14-weight evaluation is learned, and the
matrix is rebuilt at the point of use.

Values are bounded to [-1, 1] so terminals and estimates share one scale and the
regret-matching solver stays well conditioned: a capture is exactly +1, a survival
exactly -1, and a non-terminal leaf is tanh(w . phi), which never reaches either.
Terminals therefore always dominate estimates, without a magic large constant.
"""

from __future__ import annotations

from math import tanh

from pursuit.constants import Outcome
from pursuit.sdk.actions import cop_actions, thief_actions
from pursuit.sdk.resolve import resolve_turn
from pursuit.shared.config import GameParams
from pursuit.shared.resolution import ResolutionRules
from pursuit.shared.state import GameState
from pursuit.strategy.features import value as linear_value

CAPTURE_VALUE = 1.0
SURVIVAL_VALUE = -1.0

#: Rule 46 makes distance 1 with quota remaining a capture ONE turn later (the
#: seal lands on the cell the thief is leaving). Kept strictly below
#: CAPTURE_VALUE so an immediate capture always outranks a forced one, and
#: above every tanh leaf so no estimate can outrank the forced win.
FORCED_CAPTURE_VALUE = 0.98


def leaf_value(
    state: GameState,
    outcome: Outcome | None,
    weights: tuple,
    params: GameParams,
    *,
    forced_capture: bool = False,
) -> float:
    """Value of a resolved successor, from the cop's point of view.

    A terminal outcome is worth its exact bound; anything else is the squashed
    linear evaluation. Squashing is not cosmetic -- an unbounded leaf could
    outrank a real capture and make the search prefer a position it merely likes
    to a win it can actually take.
    """
    if outcome is Outcome.CAPTURE:
        return CAPTURE_VALUE
    if outcome is Outcome.SURVIVAL:
        return SURVIVAL_VALUE
    if forced_capture and params.barrier_quota - state.barriers_placed > 0:
        gap = abs(state.cop[0] - state.thief[0]) + abs(state.cop[1] - state.thief[1])
        if gap == 1:
            return FORCED_CAPTURE_VALUE
    return tanh(linear_value(weights, state, params))


def payoff_matrix(
    state: GameState,
    weights: tuple,
    params: GameParams,
    rules: ResolutionRules,
    *,
    forced_capture: bool = False,
) -> tuple:
    """Return (cop_actions, thief_moves, matrix) for the joint turn at *state*.

    Both action lists are generated from the SAME pre-turn state -- neither agent
    sees the other's choice, which is the property the Commit-Reveal protocol
    exists to enforce (book Sec5.3.2).

    Returns
    -------
    tuple[list[CopAction], list[tuple], list[list[float]]]
        The row actions, the column moves, and the payoffs to the cop, indexed
        [row][col].
    """
    rows = cop_actions(state, params)
    columns = thief_actions(state, params)
    matrix = [
        [_entry(state, action, move, weights, params, rules, forced_capture) for move in columns]
        for action in rows
    ]
    return rows, columns, matrix


def _entry(
    state: GameState,
    cop_action,
    thief_move: tuple,
    weights: tuple,
    params: GameParams,
    rules: ResolutionRules,
    forced_capture: bool = False,
) -> float:
    """Value of one joint action pair."""
    successor, outcome = resolve_turn(state, cop_action, thief_move, params, rules)
    return leaf_value(successor, outcome, weights, params, forced_capture=forced_capture)
