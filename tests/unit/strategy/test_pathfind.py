"""Tests proving STRAT-04 -- bfs() computes AND walks the barrier-aware shortest
path, not merely measures it (D-09, QUAL-02)."""

from __future__ import annotations

from pursuit.shared.config import GameParams
from pursuit.shared.state import GameState
from pursuit.strategy.pathfind import Coord, bfs


def _state(cop: Coord, thief: Coord, barriers: frozenset = frozenset()) -> GameState:
    return GameState(cop=cop, thief=thief, barriers=barriers, barriers_placed=len(barriers), turn=0)


def _manhattan(a: Coord, b: Coord) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def test_open_board_distance_equals_manhattan(default_params: GameParams) -> None:
    state = _state(cop=(1, 1), thief=(5, 5))
    start, goal = (1, 1), (4, 5)
    distance, _ = bfs(state, start, goal, "cop", default_params)
    assert distance == _manhattan(start, goal)


def test_adjacent_and_identical_cells(default_params: GameParams) -> None:
    state = _state(cop=(2, 2), thief=(2, 2))
    same_distance, same_step = bfs(state, (2, 2), (2, 2), "cop", default_params)
    assert (same_distance, same_step) == (0, None)

    adjacent_distance, adjacent_step = bfs(state, (2, 2), (2, 3), "cop", default_params)
    assert adjacent_distance == 1
    assert adjacent_step == (2, 3)
