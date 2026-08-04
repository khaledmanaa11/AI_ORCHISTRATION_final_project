"""D-31: the thief-side N[cop] safety filter.

Measured against this repo, random starts, no training, real engine
(2026-08-02 literature-review session): a thief that never steps into the
cop's closed neighbourhood N[cop] -- the cop's own cell plus every cell it
could legally reach this turn -- scored 296/300 = 0.987 over 300 random-start
games against the current BFS thief's 283/300 = 0.943.

CAVEAT -- part of the deliverable, not a footnote: "provably unbeatable" did
NOT fully reproduce. The safe thief still lost 3/20 with new barrier
placement disabled, and that control was itself flawed, because the
scenarios carry pre-placed barriers so the board was never truly open. This
is a real, bounded gain -- not a solved thief. Nothing that calls this
module, tests it, or describes it in a summary may say "provably safe".

N[cop] comes from `get_legal_moves(state, "cop", params)` -- the cop's own
cell (STAY is always legal) plus its legal destinations, one call,
barrier- and board-aware for free (QUAL-02). No second neighbourhood walk is
written here. Both functions are pure: no module-level mutable state, no
cache, no role object, no I/O (D-03) -- candidates and state always come
from the caller, so this module never asks who is moving and no cop path
can reach it.
"""

from __future__ import annotations

from pursuit.shared.board import get_legal_moves
from pursuit.shared.config import GameParams
from pursuit.shared.state import GameState
from pursuit.strategy.pathfind import Coord


def closed_neighbourhood(state: GameState, params: GameParams) -> frozenset[Coord]:
    """N[cop]: the cop's own cell plus every cell it could legally move to
    this turn, in one call to the shared movegen oracle."""
    return frozenset(get_legal_moves(state, "cop", params))


def safe_moves(
    candidates: list[Coord], state: GameState, params: GameParams
) -> list[Coord]:
    """Return the members of `candidates` that lie outside N[cop], in the
    caller's original order.

    When every candidate lies inside N[cop], returns `candidates` unchanged
    -- never `[]`. A thief with no candidate set is a crash, not a strategy.
    """
    forbidden = closed_neighbourhood(state, params)
    survivors = [cell for cell in candidates if cell not in forbidden]
    return survivors if survivors else candidates
