"""The joint turn resolver -- the single place a turn is applied (D-12 superseded).

Replaces apply_cop_action + apply_thief_move. Those could not be reordered into
simultaneity: a joint turn was inexpressible because no function accepted both
actions, and every turn passed through an intermediate state in which exactly one
agent had moved -- destroying the pre-turn positions a swap detector needs.

This module also closes three defects the sequential engine carried:
  * apply_move validated nothing (board.py was a bare dataclasses.replace), so a
    thief could be placed on a barrier. Both actions are validated here.
  * the thief could step onto the cop and not be captured, because capture was
    only ever tested on the cop's half-turn.
  * a rejected barrier was signalled by returning the same object, making an
    invalid placement indistinguishable from a deliberately wasted turn.
"""

from __future__ import annotations

from pursuit.constants import Outcome
from pursuit.sdk.actions import CopAction, barrier_cells, thief_actions
from pursuit.sdk.terminal import terminal_outcome
from pursuit.shared.board import get_legal_moves
from pursuit.shared.config import GameParams
from pursuit.shared.resolution import ResolutionRules
from pursuit.shared.state import GameState

Coord = tuple[int, int]


def resolve_turn(
    state: GameState,
    cop_action: CopAction,
    thief_move: Coord,
    params: GameParams,
    rules: ResolutionRules,
) -> tuple:
    """Apply both actions to *state* at once and return (new_state, outcome).

    Both actions were chosen from *state* without either agent seeing the other's
    choice -- the Commit-Reveal protocol (book Sec5.3) guarantees exactly this.

    Parameters
    ----------
    state:
        The shared pre-turn snapshot.
    cop_action:
        Move XOR barrier, already validated for shape by CopAction itself.
    thief_move:
        The thief's chosen destination cell.
    params:
        Game parameters.
    rules:
        Negotiated terminal predicates; BOOK_ONLY when nothing was agreed.

    Returns
    -------
    tuple[GameState, Outcome | None]
        The resolved snapshot with the turn counter advanced by exactly one, and
        the outcome, or None when play continues.

    Raises
    ------
    ValueError
        If either action is illegal from *state*. Illegal actions are rejected,
        never silently applied -- rules 13/14 make an illegal move a technical
        loss, so it must be detectable rather than absorbed.
    """
    _validate(state, cop_action, thief_move, params)

    barrier = cop_action.barrier
    barriers = state.barriers | {barrier} if barrier is not None else state.barriers
    placed = state.barriers_placed + (1 if barrier is not None else 0)

    # The barrier race: the thief chose the very cell the cop sealed this turn.
    # The move was legal when chosen -- the barrier did not exist yet -- so the
    # thief is held at its pre-turn cell rather than being placed on a wall.
    # Whether that is a capture is the negotiated predicate, decided downstream.
    raced = barrier is not None and barrier == thief_move and thief_move != state.thief

    post = GameState(
        cop=cop_action.destination(state.cop),
        thief=state.thief if raced else thief_move,
        barriers=barriers,
        barriers_placed=placed,
        turn=state.turn + 1,
    )
    outcome = terminal_outcome(state, post, barrier, raced, params, rules)
    return post, outcome


def make_state(params: GameParams) -> GameState:
    """Create the canonical opening state from the negotiated start positions.

    Book Sec3.3 p.19 marks both start cells *negotiated*, not fixed: "the start
    points are not random but strategic, and are not fixed in advance." Training
    that only ever sees this one state is training for a board we may not be
    given -- which is why the self-play start distribution samples far wider.
    """
    return GameState(
        cop=params.cop_start,
        thief=params.thief_start,
        barriers=frozenset(),
        barriers_placed=0,
        turn=0,
    )


def is_terminal(outcome: Outcome | None) -> bool:
    """True when *outcome* ends the game. Kept as a named predicate so callers
    never re-derive `outcome is not None` and drift on the TIE/TECHNICAL_LOSS
    cases that arrive in later phases."""
    return outcome is not None


def _validate(
    state: GameState, cop_action: CopAction, thief_move: Coord, params: GameParams
) -> None:
    """Raise ValueError if either action is illegal from the pre-turn state."""
    if thief_move not in thief_actions(state, params):
        raise ValueError(f"illegal thief move {thief_move} from {state.thief}")

    if cop_action.is_barrier:
        if cop_action.barrier not in barrier_cells(state, params):
            raise ValueError(
                f"illegal barrier {cop_action.barrier} from cop at {state.cop} "
                f"({state.barriers_placed}/{params.barrier_quota} placed)"
            )
        return

    if cop_action.move not in get_legal_moves(state, "cop", params):
        raise ValueError(f"illegal cop move {cop_action.move} from {state.cop}")
