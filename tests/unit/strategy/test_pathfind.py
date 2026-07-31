"""Tests proving STRAT-04 -- bfs() computes AND walks the barrier-aware shortest
path, not merely measures it (D-09, QUAL-02)."""

from __future__ import annotations

import dataclasses

import pytest

from pursuit.shared.board import get_legal_moves
from pursuit.shared.config import GameParams
from pursuit.shared.state import GameState
from pursuit.strategy.pathfind import UNREACHABLE, Coord, bfs


def _state(cop: Coord, thief: Coord, barriers: frozenset = frozenset()) -> GameState:
    return GameState(cop=cop, thief=thief, barriers=barriers, barriers_placed=len(barriers), turn=0)


def _manhattan(a: Coord, b: Coord) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _greedy_first_step(
    state: GameState, start: Coord, goal: Coord, agent: str, params: GameParams
) -> Coord:
    """A naive one-step-lookahead fallback: the legal neighbour minimizing raw
    Manhattan distance to goal, blind to anything beyond the immediate step --
    exactly what D-09 rejects in favour of bfs()'s barrier-aware search."""
    probe = (
        dataclasses.replace(state, cop=start)
        if agent == "cop"
        else dataclasses.replace(state, thief=start)
    )
    candidates = sorted(get_legal_moves(probe, agent, params))
    return min(candidates, key=lambda c: _manhattan(c, goal))


def _walk(
    state: GameState, start: Coord, goal: Coord, agent: str, params: GameParams, budget: int
) -> int:
    """Repeatedly follow bfs()'s next_step until goal is reached or `budget`
    (always move_ceiling-derived at the call site) is exhausted -- an oscillating
    implementation fails this loudly instead of hanging the suite."""
    current = start
    for steps in range(budget + 1):
        if current == goal:
            return steps
        _, next_step = bfs(state, current, goal, agent, params)
        assert next_step is not None, "walk stalled before reaching goal"
        current = next_step
    pytest.fail(f"walk did not reach goal within budget={budget}")
    return -1


def test_open_board_distance_equals_manhattan(default_params: GameParams) -> None:
    state = _state(cop=(1, 1), thief=(5, 5))
    start, goal = (1, 1), (4, 5)
    distance, _ = bfs(state, start, goal, "cop", default_params)
    assert distance == _manhattan(start, goal)


def test_walk_reaches_goal_in_reported_distance(default_params: GameParams) -> None:
    """A single barrier directly on the straight line forces a real detour -- a
    one-step Manhattan-greedy stepper stalls right at the obstruction (its own
    "stay" always beats stepping off-axis), while bfs()'s walk still arrives."""
    state = _state(cop=(1, 1), thief=(6, 6), barriers=frozenset({(1, 2)}))
    start, goal = (1, 1), (1, 4)
    distance, _ = bfs(state, start, goal, "cop", default_params)
    steps_taken = _walk(state, start, goal, "cop", default_params, budget=default_params.move_ceiling)
    assert steps_taken == distance


def test_barrier_pocket_first_step_differs_from_manhattan_greedy(default_params: GameParams) -> None:
    """A wall with gaps only at the two far board edges: the Manhattan-nearest
    neighbour walks straight into the wall and stalls there forever, while bfs()
    detours through a gap and actually reaches the goal (D-09) -- this is the case
    a naive fallback passes review on and fails in a real game."""
    size = default_params.board_size
    mid = size // 2
    wall = frozenset((row, mid) for row in range(1, size - 1))
    state = _state(cop=(0, 0), thief=(size - 1, size - 1), barriers=wall)
    start, goal = (mid, mid - 2), (mid, mid + 2)

    distance, bfs_first_step = bfs(state, start, goal, "cop", default_params)
    greedy_first_step = _greedy_first_step(state, start, goal, "cop", default_params)
    assert bfs_first_step != greedy_first_step

    steps_taken = _walk(state, start, goal, "cop", default_params, budget=default_params.move_ceiling)
    assert steps_taken == distance


def test_fully_walled_off_goal_returns_sentinel_and_none(default_params: GameParams) -> None:
    size = default_params.board_size
    mid = size // 2
    goal = (mid, mid)
    walls = frozenset({(mid - 1, mid), (mid + 1, mid), (mid, mid - 1), (mid, mid + 1)})
    state = _state(cop=(0, 0), thief=(size - 1, size - 1), barriers=walls)
    distance, next_step = bfs(state, (0, 0), goal, "cop", default_params)
    assert distance == UNREACHABLE
    assert next_step is None


def test_adjacent_and_identical_cells(default_params: GameParams) -> None:
    state = _state(cop=(2, 2), thief=(2, 2))
    same_distance, same_step = bfs(state, (2, 2), (2, 2), "cop", default_params)
    assert (same_distance, same_step) == (0, None)

    adjacent_distance, adjacent_step = bfs(state, (2, 2), (2, 3), "cop", default_params)
    assert adjacent_distance == 1
    assert adjacent_step == (2, 3)


def test_determinism_and_tie_break_is_stable(default_params: GameParams) -> None:
    """Two neighbours of start (3,3)@offset tie for distance-2 to a diagonal goal;
    repeated calls must agree, and the documented sort rule (ascending (row, col))
    must pick the same first step every time."""
    state = _state(cop=(3, 3), thief=(0, 6))
    start, goal = (3, 3), (4, 4)
    first = bfs(state, start, goal, "cop", default_params)
    second = bfs(state, start, goal, "cop", default_params)
    assert first == second
    distance, next_step = first
    assert distance == 2
    assert next_step == (3, 4)


def test_walk_terminates_within_move_ceiling_budget(default_params: GameParams) -> None:
    """The walk's step budget is derived from move_ceiling, not an arbitrary cap."""
    state = _state(cop=(0, 0), thief=(6, 6))
    size = default_params.board_size
    start, goal = (0, 0), (size - 1, size - 1)
    distance, _ = bfs(state, start, goal, "cop", default_params)
    assert distance <= default_params.move_ceiling
    steps_taken = _walk(state, start, goal, "cop", default_params, budget=default_params.move_ceiling)
    assert steps_taken == distance
