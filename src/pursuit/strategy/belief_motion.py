"""Legal-motion model for the belief map (D-48 Sec1, Task 2): spreads
probability mass through the SAME legal action sets the engine plays with --
`sdk/actions.py` -- never a private copy of the movement rules.

The default action prior is uniform over each hypothesised cell's legal set:
deliberately weak and deliberately honest, since nothing here yet models HOW
the opponent chooses. `action_weights` is a documented, unused seam -- a
future phase can drop a per-action weighting callable through this exact
call site without reshaping it. Today it is never invoked in production: an
unjustified prior is worse than a uniform one (Task 2 action note).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace

from pursuit.sdk.actions import cop_actions, thief_actions
from pursuit.shared.config import GameParams
from pursuit.shared.state import GameState

Coord = tuple[int, int]
Grid = list[list[float]]
ActionWeights = Callable[[list[Coord], float], list[float]]

#: The two roles a BeliefMap or spread() call may track -- matching
#: GameState's own field names exactly (state.cop / state.thief), so
#: dataclasses.replace(state, **{role: cell}) substitutes the right field.
ROLES = ("cop", "thief")


def spread(
    prior: Grid,
    role: str,
    state: GameState,
    params: GameParams,
    action_weights: ActionWeights | None = None,
) -> Grid:
    """Return one joint turn of `prior` advanced through role's legal actions.

    For every cell holding mass, hypothesise `role` standing there --
    keeping every other field of `state` (barriers, the other agent's cell)
    unchanged -- and enumerate its legal actions via sdk/actions.py. Mass
    divides across the resulting destinations, uniformly unless a caller
    supplies `action_weights` (see module docstring).

    Mass is conserved to within float precision: STAY is always legal, so
    every credited cell has at least one destination, and the returned
    grid's total equals `prior`'s.
    """
    if role not in ROLES:
        raise ValueError(f"spread: role must be one of {ROLES}, got {role!r}")
    size = params.board_size
    result: Grid = [[0.0] * size for _ in range(size)]
    for row in range(size):
        for col in range(size):
            mass = prior[row][col]
            if mass <= 0.0:
                continue
            hypothetical = replace(state, **{role: (row, col)})
            destinations = _destinations(hypothetical, role, params)
            for (dest_row, dest_col), share in zip(
                destinations, _shares(mass, destinations, action_weights), strict=True
            ):
                result[dest_row][dest_col] += share
    return result


def _destinations(state: GameState, role: str, params: GameParams) -> list[Coord]:
    """Every resulting position for role's legal actions.

    A cop's barrier action leaves its own cell unchanged -- it changes the
    board, not the cop's position -- so it contributes to the STAY branch
    alongside a move-to-self, via CopAction.destination().
    """
    if role == "thief":
        return thief_actions(state, params)
    return [action.destination(state.cop) for action in cop_actions(state, params)]


def _shares(mass: float, destinations: list[Coord], action_weights: ActionWeights | None) -> list:
    """One share of `mass` per destination -- uniform unless `action_weights`
    is supplied (unused in production today; see module docstring)."""
    if action_weights is not None:
        return action_weights(destinations, mass)
    even = mass / len(destinations)
    return [even for _ in destinations]
