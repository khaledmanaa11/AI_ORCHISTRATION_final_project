"""Tests for the D-31 thief-side N[cop] safety filter (STRAT-02, D-03)."""

from __future__ import annotations

from pursuit.shared.config import GameParams
from pursuit.shared.state import GameState
from pursuit.strategy.pathfind import Coord
from pursuit.strategy.safety import closed_neighbourhood, safe_moves


def _state(cop: Coord, thief: Coord, barriers: frozenset = frozenset()) -> GameState:
    return GameState(cop=cop, thief=thief, barriers=barriers, barriers_placed=len(barriers), turn=0)


def test_closed_neighbourhood_contains_cops_own_cell(default_params: GameParams) -> None:
    state = _state(cop=(3, 3), thief=(0, 0))
    n_cop = closed_neighbourhood(state, default_params)
    assert (3, 3) in n_cop


def test_closed_neighbourhood_excludes_barriered_and_off_board_cells(
    default_params: GameParams,
) -> None:
    cop = (0, 0)
    barriers = frozenset({(0, 1), (1, 0)})
    state = _state(cop=cop, thief=(5, 5), barriers=barriers)
    n_cop = closed_neighbourhood(state, default_params)
    assert (0, 1) not in n_cop
    assert (1, 0) not in n_cop
    assert (-1, 0) not in n_cop
    assert n_cop == {(0, 0)}


def test_safe_moves_removes_candidate_inside_n_cop(default_params: GameParams) -> None:
    state = _state(cop=(3, 3), thief=(0, 0))
    candidates = [(3, 3), (0, 0)]
    result = safe_moves(candidates, state, default_params)
    assert (3, 3) not in result


def test_safe_moves_keeps_candidate_outside_n_cop(default_params: GameParams) -> None:
    state = _state(cop=(3, 3), thief=(0, 0))
    candidates = [(3, 3), (0, 0)]
    result = safe_moves(candidates, state, default_params)
    assert (0, 0) in result


def test_safe_moves_never_empty_when_every_candidate_is_inside_n_cop(
    default_params: GameParams,
) -> None:
    """The fully-surrounded case: every offered candidate lies inside N[cop]
    (constructed here as N[cop] itself) -- must return the unfiltered list,
    never []."""
    state = _state(cop=(3, 3), thief=(3, 4))
    candidates = list(closed_neighbourhood(state, default_params))
    result = safe_moves(candidates, state, default_params)
    assert result == candidates
    assert result != []


def test_safe_moves_preserves_caller_ordering(default_params: GameParams) -> None:
    state = _state(cop=(3, 3), thief=(0, 0))
    candidates = [(0, 0), (6, 6), (0, 1), (5, 5)]
    result = safe_moves(candidates, state, default_params)
    forbidden = closed_neighbourhood(state, default_params)
    assert result == [cell for cell in candidates if cell not in forbidden]


def test_safe_moves_is_pure_repeated_calls_identical(default_params: GameParams) -> None:
    state = _state(cop=(3, 3), thief=(0, 0))
    candidates = [(3, 3), (0, 0), (6, 6)]
    first = safe_moves(candidates, state, default_params)
    second = safe_moves(candidates, state, default_params)
    assert first == second
    # the input list itself must never be mutated by a call (purity, D-03)
    assert candidates == [(3, 3), (0, 0), (6, 6)]
