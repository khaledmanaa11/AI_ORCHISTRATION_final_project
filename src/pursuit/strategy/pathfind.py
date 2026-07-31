"""Barrier-aware BFS distance oracle over the Phase-1 board (STRAT-04, D-09, QUAL-02).

bfs() is the single distance oracle for Phase 3: the Bayes+BFS fallback (03-04) and
the cop's barrier sub-policy (03-07) both call it rather than each computing distance
themselves. It never reimplements adjacency or barrier-blocking -- every neighbour
comes from `pursuit.shared.board.get_legal_moves`, the same function the Phase-1
engine uses to validate a real move (QUAL-02). Barriers occupy cells, not edges
(`GameState.barriers` is a frozenset of cells), so a barrier is impassable exactly
where the engine already says it is.

Sentinel: UNREACHABLE (a plain int, not math.inf) is returned as the distance when
no path exists. The cop can legally spend its whole barrier quota walling the target
off, so an unreachable goal is a normal, tested outcome -- bfs() never raises and
never returns an arbitrary neighbour a caller could walk into.

Tie-breaking: neighbours of every expanded cell are sorted by their (row, col) tuple
before being enqueued, so two equal-distance first steps always resolve to the same
one on every call and a replayed game reproduces the same move.
"""

from __future__ import annotations

import dataclasses
from collections import deque

from pursuit.shared.board import get_legal_moves
from pursuit.shared.config import GameParams
from pursuit.shared.state import GameState

Coord = tuple[int, int]

UNREACHABLE: int = -1


def bfs(
    state: GameState,
    start: Coord,
    goal: Coord,
    agent: str,
    params: GameParams,
) -> tuple[int, Coord | None]:
    """Shortest-path distance and first step from `start` to `goal`.

    Parameters
    ----------
    state:
        Current immutable snapshot; only its `barriers` field is fixed for the
        whole search -- `start`/`goal` need not equal `state.cop`/`state.thief`,
        the search explores the grid around `agent`'s hypothetical position.
    start, goal:
        Cells to search between.
    agent:
        "cop" or "thief" -- selects which state field `get_legal_moves` treats
        as the mover, so the search inherits exactly the movement rule a real
        move would be checked against.
    params:
        GameParams. Board bounds are enforced inside `get_legal_moves`; nothing
        here reads `params.board_size` directly.

    Returns
    -------
    tuple[int, Coord | None]
        `(distance, next_step)`. `distance` is the length of an optimal path
        (0 when `start == goal`). `next_step` is the first cell along one such
        path, or `None` when `start == goal` or `goal` is unreachable. Never
        raises and never returns an arbitrary neighbour.
    """
    if start == goal:
        return 0, None

    distances: dict[Coord, int] = {start: 0}
    came_from: dict[Coord, Coord] = {}
    frontier: deque[Coord] = deque([start])

    while frontier:
        current = frontier.popleft()
        if current == goal:
            return distances[current], _reconstruct_first_step(came_from, start, goal)
        for neighbor in _sorted_neighbors(state, current, agent, params):
            if neighbor == current or neighbor in distances:
                continue
            distances[neighbor] = distances[current] + 1
            came_from[neighbor] = current
            frontier.append(neighbor)

    return UNREACHABLE, None


def _sorted_neighbors(
    state: GameState, cell: Coord, agent: str, params: GameParams
) -> list[Coord]:
    """Legal destinations from `cell`, sorted for deterministic tie-breaking.

    `state` is probed with `agent`'s position temporarily replaced by `cell` via
    `dataclasses.replace` -- barriers and board bounds still come from
    `get_legal_moves` unchanged; this never reimplements "orthogonal, in-bounds,
    not a barrier" (QUAL-02).
    """
    probe = (
        dataclasses.replace(state, cop=cell)
        if agent == "cop"
        else dataclasses.replace(state, thief=cell)
    )
    return sorted(get_legal_moves(probe, agent, params))


def _reconstruct_first_step(
    came_from: dict[Coord, Coord], start: Coord, goal: Coord
) -> Coord:
    """Walk the parent chain from `goal` back to the cell reached directly from `start`."""
    cell = goal
    while came_from[cell] != start:
        cell = came_from[cell]
    return cell
