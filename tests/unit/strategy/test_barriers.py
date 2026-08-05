"""Tests for the cop barrier sub-policy (STRAT-05, D-09, D-12, AI-SPEC E9)."""

from __future__ import annotations

from pursuit.constants import MoveSource
from pursuit.shared.barrier import place_barrier
from pursuit.shared.config import GameParams
from pursuit.shared.state import GameState
from pursuit.strategy.barriers import choose_barrier, cop_decision
from pursuit.strategy.base import Decision
from pursuit.strategy.pathfind import Coord

_CHOKEPOINT_COP = (0, 4)
_CHOKEPOINT_THIEF = (6, 6)
_CHOKEPOINT_WALL_COL = 3
_CHOKEPOINT_GAP_ROW = 0
# The wall's one open cell -- the cop's own WEST neighbour under this layout.
_CHOKEPOINT_EXPECTED_SEAL = (_CHOKEPOINT_GAP_ROW, _CHOKEPOINT_WALL_COL)


def _state(
    cop: Coord, thief: Coord, barriers: frozenset = frozenset(), barriers_placed: int | None = None
) -> GameState:
    return GameState(
        cop=cop,
        thief=thief,
        barriers=barriers,
        barriers_placed=len(barriers) if barriers_placed is None else barriers_placed,
        turn=0,
    )


def _wall_with_gap(board_size: int, col: int, gap_row: int) -> frozenset[Coord]:
    """Every cell in `col` except `gap_row` -- a one-cell-wide corridor.

    Splits the board into a side containing the cop (east of `col`) and a
    side containing the far escape anchor (west of `col`), joined only at
    `gap_row` -- orthogonally adjacent to a cop placed one column east of it,
    the one legal-candidate cell this scenario needs (D-09).
    """
    return frozenset({(row, col) for row in range(board_size) if row != gap_row})


def test_quota_exhausted_returns_none_immediately(default_params: GameParams) -> None:
    wall = _wall_with_gap(default_params.board_size, _CHOKEPOINT_WALL_COL, _CHOKEPOINT_GAP_ROW)
    state = _state(
        cop=_CHOKEPOINT_COP,
        thief=_CHOKEPOINT_THIEF,
        barriers=wall,
        barriers_placed=default_params.barrier_quota,
    )
    assert choose_barrier(state, default_params, _CHOKEPOINT_THIEF, 1) is None


def test_open_board_has_no_candidate_above_threshold(default_params: GameParams) -> None:
    """No single barrier lengthens an already-wide-open shortest path on a bare
    board -- the sub-policy must not spend a barrier for zero measurable gain.
    Regression coverage: before the anchor cell was excluded from candidates,
    this exact scenario returned the anchor corner itself (a trivial, thief-
    position-independent 'win') instead of None."""
    state = _state(cop=(0, 0), thief=(3, 3))
    assert choose_barrier(state, default_params, (3, 3), 1) is None


def test_chokepoint_placement_that_lengthens_escape_is_chosen(
    default_params: GameParams,
) -> None:
    """The wall's one gap is the cop's sole route-altering neighbour; the
    sub-policy must find and seal it, severing the far corner from the
    believed thief cell entirely (STRAT-05)."""
    wall = _wall_with_gap(default_params.board_size, _CHOKEPOINT_WALL_COL, _CHOKEPOINT_GAP_ROW)
    state = _state(cop=_CHOKEPOINT_COP, thief=_CHOKEPOINT_THIEF, barriers=wall)
    chosen = choose_barrier(state, default_params, _CHOKEPOINT_THIEF, 1)
    assert chosen == _CHOKEPOINT_EXPECTED_SEAL
    assert chosen != state.cop
    assert chosen != _CHOKEPOINT_THIEF


def test_returned_cell_is_always_engine_legal(default_params: GameParams) -> None:
    """Legality is never re-derived (QUAL-02) -- the returned cell must be one
    `place_barrier` itself actually accepts."""
    wall = _wall_with_gap(default_params.board_size, _CHOKEPOINT_WALL_COL, _CHOKEPOINT_GAP_ROW)
    state = _state(cop=_CHOKEPOINT_COP, thief=_CHOKEPOINT_THIEF, barriers=wall)
    chosen = choose_barrier(state, default_params, _CHOKEPOINT_THIEF, 1)
    assert chosen is not None
    after = place_barrier(state, chosen, default_params)
    assert after is not state
    assert chosen in after.barriers
    assert after.barriers_placed == state.barriers_placed + 1


def test_already_unreachable_anchor_yields_no_further_gain(
    default_params: GameParams,
) -> None:
    """Both of the wall's cells are already sealed -- baseline distance to
    the anchor is already UNREACHABLE, so no further candidate can register a
    gain and the sub-policy must not spend a barrier chasing zero."""
    wall = _wall_with_gap(default_params.board_size, _CHOKEPOINT_WALL_COL, _CHOKEPOINT_GAP_ROW)
    state = _state(
        cop=_CHOKEPOINT_COP,
        thief=_CHOKEPOINT_THIEF,
        barriers=wall | frozenset({_CHOKEPOINT_EXPECTED_SEAL}),
    )
    assert choose_barrier(state, default_params, _CHOKEPOINT_THIEF, 1) is None


def test_deterministic_repeated_calls(default_params: GameParams) -> None:
    """Pure function of its inputs (D-03) -- identical inputs, identical output."""
    wall = _wall_with_gap(default_params.board_size, _CHOKEPOINT_WALL_COL, _CHOKEPOINT_GAP_ROW)
    state = _state(cop=_CHOKEPOINT_COP, thief=_CHOKEPOINT_THIEF, barriers=wall)
    first = choose_barrier(state, default_params, _CHOKEPOINT_THIEF, 1)
    second = choose_barrier(state, default_params, _CHOKEPOINT_THIEF, 1)
    assert first == second == _CHOKEPOINT_EXPECTED_SEAL


def test_cop_decision_stays_when_barrier_chosen(default_params: GameParams) -> None:
    """cop_decision must report move=state.cop whenever it attaches a barrier
    (declared == applied, rules 16/22) -- overriding whatever move the
    movement policy actually picked, never just coinciding with it (D-12)."""
    wall = _wall_with_gap(default_params.board_size, _CHOKEPOINT_WALL_COL, _CHOKEPOINT_GAP_ROW)
    state = _state(cop=_CHOKEPOINT_COP, thief=_CHOKEPOINT_THIEF, barriers=wall)
    movement = Decision(move=(1, 4), source=MoveSource.HEURISTIC)
    decision = cop_decision(movement, state, default_params, _CHOKEPOINT_THIEF, 1)
    assert decision.barrier is not None
    assert decision.move == state.cop
