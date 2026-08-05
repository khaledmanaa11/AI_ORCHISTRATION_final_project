"""Cop barrier sub-policy (STRAT-05) -- the second stage after `_pick_move` (D-12).

`choose_barrier` never becomes a 6th Q action (D-12): the Q-policy already picked a
movement, and this pure function decides only whether/where to spend one of the
cop's `barrier_quota` placements this turn. It never reimplements board legality --
every candidate is checked by calling `pursuit.shared.barrier.place_barrier` itself
and testing identity on rejection (QUAL-02) -- and it never invents a second
distance metric: every score comes from `pathfind.bfs()` (D-09).

Scoring model (documented engineering decision, the plan leaves the exact metric
open): the game rules define no explicit "escape zone", so this module anchors
"the thief's best escape" at the board corner diagonally farthest from the cop's
own cell -- a deterministic, board-geometry-only reference point requiring no extra
game concept and no per-candidate cost beyond the one required `bfs()` call. A
candidate is scored by how much it lengthens (or outright severs) the believed
thief cell's BFS route to that corner; the best-scoring candidate is proposed only
if its gain clears `min_gain` (`strategy.barrier_min_gain`, an engineering default,
D-18 -- NOT a PARAMETERS.md game value, so it lives in StrategyParams, not
GameParams) -- spending a finite barrier for a gain of zero is strictly worse than
holding it in reserve. `game_params.barrier_quota` IS a book value (D-05) and is
read from `GameParams` alone, matching `place_barrier`'s own signature.

Pure function of (state, game_params, believed_thief_cell, min_gain) only -- no
counters, no caches, no module-level mutable state (D-03, project rule 2).
`state.thief` is never read; only `state.cop` (the cop's own true position --
self-knowledge, not cheating) and `believed_thief_cell` (the Phase-3 known-target /
Phase-4 belief-map seam, D-11) locate the two agents.
"""

from __future__ import annotations

import dataclasses

from pursuit.constants import Direction
from pursuit.shared.barrier import place_barrier
from pursuit.shared.config import GameParams
from pursuit.shared.state import GameState
from pursuit.strategy.base import Decision
from pursuit.strategy.pathfind import UNREACHABLE, Coord, bfs


def cop_decision(
    movement: Decision,
    state: GameState,
    game_params: GameParams,
    believed_thief_cell: Coord,
    min_gain: int,
) -> Decision:
    """Resolve the cop's move-XOR-barrier turn (D-12), shared by every brain.

    Placing forgoes movement, so `choose_barrier` is asked about the cop's
    CURRENT cell -- never a post-move one -- and a proposed cell comes back
    alongside `move=state.cop` (stay), so declared == applied (rules 16/22).

    PLACEHOLDER POLICY -- deliberately not a settled design. Place whenever a
    candidate clears `min_gain`, move otherwise. Under the one-step rule a
    barrier costs the whole turn, so the real move-vs-place trade-off is an
    open strategy question and is NOT decided here.
    """
    barrier = choose_barrier(state, game_params, believed_thief_cell, min_gain)
    if barrier is None:
        return Decision(move=movement.move, source=movement.source)
    return Decision(move=state.cop, source=movement.source, barrier=barrier)


def choose_barrier(
    state: GameState,
    game_params: GameParams,
    believed_thief_cell: Coord,
    min_gain: int,
) -> Coord | None:
    """Whether and where the cop should place a barrier this turn.

    `state` must reflect the cop's current position before it acts. Under the
    D-12 move-XOR-barrier rule, a returned cell means the caller must forgo
    movement and pass this same state to the engine for placement, guaranteeing
    declared == applied (AI-SPEC E9, rules 16/22).

    Returns `None` at quota, when no legal candidate exists, or when the best
    candidate's gain does not clear `min_gain` (`StrategyParams.barrier_min_gain`).
    """
    if state.barriers_placed >= game_params.barrier_quota:
        return None

    anchor = _escape_anchor(state.cop, game_params.board_size)
    baseline = _bfs_distance(state, believed_thief_cell, anchor, game_params)

    best_cell: Coord | None = None
    best_gain: int | None = None
    for candidate in sorted(_legal_candidates(state, believed_thief_cell, game_params)):
        if candidate == anchor:
            # Barrier-on-the-anchor trivially makes the anchor itself
            # UNREACHABLE regardless of the thief's real position -- the
            # anchor is a scoring reference point, not a real escape target,
            # so this degenerate "win" is excluded on purpose.
            continue
        probed = dataclasses.replace(state, barriers=state.barriers | frozenset({candidate}))
        new_distance = _bfs_distance(probed, believed_thief_cell, anchor, game_params)
        gain = _gain(baseline, new_distance, game_params)
        if gain < min_gain:
            continue
        if best_gain is None or gain > best_gain:
            best_gain, best_cell = gain, candidate
    return best_cell


def _legal_candidates(
    state: GameState, believed_thief_cell: Coord, params: GameParams
) -> list[Coord]:
    """One-step cells `place_barrier` would accept, minus the believed thief cell."""
    candidates = []
    for direction in Direction:
        row_delta, col_delta = direction.value
        cell = (state.cop[0] + row_delta, state.cop[1] + col_delta)
        if cell == believed_thief_cell:
            continue
        if place_barrier(state, cell, params) is state:
            continue
        candidates.append(cell)
    return candidates


def _escape_anchor(cop_cell: Coord, board_size: int) -> Coord:
    """The board corner diagonally farthest from the cop -- see module docstring."""
    row, col = cop_cell
    return (board_size - 1 - row, board_size - 1 - col)


def _bfs_distance(state: GameState, start: Coord, goal: Coord, params: GameParams) -> int:
    distance, _ = bfs(state, start, goal, "thief", params)
    return distance


def _gain(baseline: int, new: int, params: GameParams) -> int:
    """Non-negative BFS-distance increase caused by one extra barrier.

    Barriers only remove edges, so a distance can only grow or stay the same.
    UNREACHABLE-after scores as the largest possible gain (the anchor is cut off
    entirely); an already-UNREACHABLE baseline yields zero -- there is nothing
    further to gain once the anchor was already unreachable.
    """
    if baseline == UNREACHABLE:
        return 0
    if new == UNREACHABLE:
        return params.board_size * params.board_size
    return new - baseline
