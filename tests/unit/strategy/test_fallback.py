"""Tests for the STRAT-02 fallback: BFS-distance pursue/evade toward the
believed target (D-08, D-09, D-11)."""

from __future__ import annotations

from pursuit.constants import MoveSource
from pursuit.shared.board import get_legal_moves
from pursuit.shared.config import GameParams
from pursuit.shared.state import GameState
from pursuit.strategy.base import Observation
from pursuit.strategy.fallback import pick
from pursuit.strategy.pathfind import Coord, bfs
from pursuit.strategy.prior import uniform


def _state(cop: Coord, thief: Coord, barriers: frozenset = frozenset()) -> GameState:
    return GameState(cop=cop, thief=thief, barriers=barriers, barriers_placed=len(barriers), turn=0)


def _obs(own_cell: Coord, target_cell: Coord) -> Observation:
    return Observation(
        own_cell=own_cell, target_cell=target_cell, blocked_mask=0, barriers_used=0, turn_index=0
    )


def _manhattan(a: Coord, b: Coord) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _greedy_first_step(
    state: GameState, target: Coord, agent: str, params: GameParams
) -> Coord:
    """Naive one-step Manhattan-greedy stepper -- exactly what D-09 rejects."""
    candidates = sorted(get_legal_moves(state, agent, params))
    return min(candidates, key=lambda c: _manhattan(c, target))


def test_cop_closes_distance_to_target(default_params: GameParams) -> None:
    state = _state(cop=(1, 1), thief=(5, 5))
    obs = _obs(own_cell=(1, 1), target_cell=(5, 5))
    decision = pick(obs, state, "cop", default_params)
    assert decision.source is MoveSource.FALLBACK
    assert _manhattan(decision.move, (5, 5)) < _manhattan((1, 1), (5, 5))


def test_thief_opens_distance_from_target(default_params: GameParams) -> None:
    state = _state(cop=(1, 1), thief=(2, 2))
    obs = _obs(own_cell=(2, 2), target_cell=(1, 1))
    decision = pick(obs, state, "thief", default_params)
    assert decision.source is MoveSource.FALLBACK
    assert _manhattan(decision.move, (1, 1)) > _manhattan((2, 2), (1, 1))


def test_barrier_pocket_first_step_non_greedy_for_cop(default_params: GameParams) -> None:
    """Same wall-with-gaps layout as 03-03's pocket test: a raw-Manhattan step
    walks into the wall; the fallback must detour through a gap instead, and
    must match bfs()'s own optimal next step exactly."""
    size = default_params.board_size
    mid = size // 2
    wall = frozenset((row, mid) for row in range(1, size - 1))
    own_cell, target = (mid, mid - 2), (mid, mid + 2)
    state = _state(cop=own_cell, thief=target, barriers=wall)
    obs = _obs(own_cell=own_cell, target_cell=target)

    decision = pick(obs, state, "cop", default_params)
    _, bfs_next_step = bfs(state, own_cell, target, "cop", default_params)
    greedy_next_step = _greedy_first_step(state, target, "cop", default_params)

    assert decision.move == bfs_next_step
    assert decision.move != greedy_next_step


def test_barrier_pocket_thief_never_walks_toward_cop(default_params: GameParams) -> None:
    """The thief evades AWAY from the believed cop cell across the same wall
    layout -- its chosen step must not be the naive Manhattan-toward step,
    and must never reduce distance to the cop."""
    size = default_params.board_size
    mid = size // 2
    wall = frozenset((row, mid) for row in range(1, size - 1))
    own_cell, cop_cell = (mid, mid + 2), (mid, mid - 2)
    state = _state(cop=cop_cell, thief=own_cell, barriers=wall)
    obs = _obs(own_cell=own_cell, target_cell=cop_cell)

    decision = pick(obs, state, "thief", default_params)
    assert decision.source is MoveSource.FALLBACK
    assert _manhattan(decision.move, cop_cell) >= _manhattan(own_cell, cop_cell)


def test_unreachable_target_returns_legal_move_without_raising(default_params: GameParams) -> None:
    size = default_params.board_size
    mid = size // 2
    target = (mid, mid)
    walls = frozenset({(mid - 1, mid), (mid + 1, mid), (mid, mid - 1), (mid, mid + 1)})
    own_cell = (0, 0)
    state = _state(cop=own_cell, thief=target, barriers=walls)
    obs = _obs(own_cell=own_cell, target_cell=target)

    decision = pick(obs, state, "cop", default_params)
    assert decision.move in get_legal_moves(state, "cop", default_params)
    assert decision.source is MoveSource.FALLBACK


def test_prior_argmax_used_as_believed_target_when_supplied(default_params: GameParams) -> None:
    state = _state(cop=(0, 0), thief=(6, 6))
    obs = _obs(own_cell=(0, 0), target_cell=(1, 1))  # must be ignored in favour of the prior
    prior = uniform([(6, 6)])
    decision = pick(obs, state, "cop", default_params, prior=prior)
    assert _manhattan(decision.move, (6, 6)) < _manhattan((0, 0), (6, 6))
