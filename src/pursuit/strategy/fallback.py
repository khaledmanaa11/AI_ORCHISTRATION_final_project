"""STRAT-02 fallback: BFS-distance pursue/evade toward the believed target.

Used whenever the Q-table has not sufficiently visited the current state
(`min_visits`, D-08), and used directly by `HeuristicBrain` (03-04), which
has no Q-table at all. Distance never comes from anywhere but
`pathfind.bfs()` (D-09, QUAL-02) -- raw Manhattan is never computed here,
not even as a tie-break.
"""

from __future__ import annotations

import dataclasses

from pursuit.constants import MoveSource
from pursuit.shared.board import get_legal_moves
from pursuit.shared.config import GameParams
from pursuit.shared.state import GameState
from pursuit.strategy.base import Decision, Observation
from pursuit.strategy.pathfind import UNREACHABLE, Coord, bfs
from pursuit.strategy.prior import argmax_cell
from pursuit.strategy.safety import safe_moves


def pick(
    obs: Observation,
    state: GameState,
    agent: str,
    params: GameParams,
    prior: dict[Coord, float] | None = None,
) -> Decision:
    """Choose a fallback move for `agent` ("cop" or "thief").

    The believed target is `argmax_cell(prior)` when a prior is supplied
    (Phase 4's belief-map path); otherwise it is `obs.target_cell` directly
    (Phase 3's known-target path). Both paths exist because D-11 fixes the
    *contract* at "a believed cell" while Phase 3 already knows it exactly.
    Always returns a legal move, even when the target is unreachable --
    walling the thief off is a legitimate cop strategy, not an error state.
    """
    target = argmax_cell(prior) if prior is not None else obs.target_cell
    move = (
        _pursue(state, agent, target, params)
        if agent == "cop"
        else _evade(state, agent, target, params)
    )
    return Decision(move=move, source=MoveSource.FALLBACK)


def _probe(state: GameState, agent: str, cell: Coord) -> GameState:
    return (
        dataclasses.replace(state, cop=cell)
        if agent == "cop"
        else dataclasses.replace(state, thief=cell)
    )


def _distance_from(
    state: GameState, agent: str, dest: Coord, target: Coord, params: GameParams
) -> int:
    probe = _probe(state, agent, dest)
    distance, _ = bfs(probe, dest, target, agent, params)
    return distance


def _pursue(state: GameState, agent: str, target: Coord, params: GameParams) -> Coord:
    """The cop's step: minimize BFS distance to `target`.

    Ranking key is `(unreachable?, distance)` so any reachable candidate
    beats every unreachable one; candidates iterate in sorted (row, col)
    order so a genuine tie -- including "every candidate is unreachable",
    the walled-off case -- always resolves to the same legal move.
    """
    candidates = sorted(get_legal_moves(state, agent, params))
    best_cell = candidates[0]
    best_key: tuple[bool, int] | None = None
    for dest in candidates:
        distance = _distance_from(state, agent, dest, target, params)
        key = (distance == UNREACHABLE, distance)
        if best_key is None or key < best_key:
            best_key, best_cell = key, dest
    return best_cell


def _evade(state: GameState, agent: str, target: Coord, params: GameParams) -> Coord:
    """The thief's step: filter first, then rank the survivors.

    Legal destinations pass through the D-31 safety filter
    (`safety.safe_moves` -- never steps into the cop's closed neighbourhood
    N[cop] while a cell outside it is offered; see `safety.py` for the
    measured gain and its caveat) before ranking. Ranking is unchanged:
    maximize BFS distance from `target`, tie-breaking toward the destination
    with more onward legal moves -- walking into a pocket to gain one square
    of distance is how an evader loses. Being unreachable from `target`
    ranks as the *best* outcome (the cop can never arrive), never the worst.
    """
    legal = sorted(get_legal_moves(state, agent, params))
    candidates = safe_moves(legal, state, params)
    best_cell = candidates[0]
    best_key: tuple[bool, int, int] | None = None
    for dest in candidates:
        distance = _distance_from(state, agent, dest, target, params)
        onward = len(get_legal_moves(_probe(state, agent, dest), agent, params))
        key = (distance == UNREACHABLE, distance, onward)
        if best_key is None or key > best_key:
            best_key, best_cell = key, dest
    return best_cell
