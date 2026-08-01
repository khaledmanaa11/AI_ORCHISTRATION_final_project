"""Bayes motion-model prior over the opponent's plausible cells (D-10, D-11).

`spread()` is the Bayes filter's PREDICTION step ONLY: each cell's mass moves
uniformly onto the legal moves the opponent could make from it, using
`pursuit.shared.board.get_legal_moves` so barriers and board bounds are
honoured for free (QUAL-02) -- there is no evidence term and no likelihood
multiply anywhere in this module. Phase 4 adds scent/hint evidence as a
second step layered on top of this one; this module must not need to be
restructured for that to work, only extended alongside it.

Not exercised by Phase 3 gameplay itself (Phase 3 plays with a known target,
D-11), but `fallback.pick()` accepts this module's output as an alternate
input so the Phase-4 seam is real and tested from day one, not promised.
"""

from __future__ import annotations

import dataclasses

from pursuit.shared.board import get_legal_moves
from pursuit.shared.config import GameParams
from pursuit.shared.state import GameState
from pursuit.strategy.pathfind import Coord

# Floating-point equality guard for the "mass sums to 1.0" invariant -- a
# numerical-precision constant, not a game value or RL hyperparameter (D-05/
# D-18 do not apply; it never appears in a config file). Same category as
# pathfind.py's UNREACHABLE sentinel: a structural constant, not a "value".
_MASS_TOLERANCE: float = 1e-9


def uniform(cells: list[Coord]) -> dict[Coord, float]:
    """A uniform probability distribution over `cells` (deduplicated, order-stable)."""
    if not cells:
        raise ValueError("cells must not be empty")
    unique_cells = list(dict.fromkeys(cells))
    mass = 1.0 / len(unique_cells)
    return dict.fromkeys(unique_cells, mass)


def spread(
    prior: dict[Coord, float],
    state: GameState,
    agent: str,
    params: GameParams,
) -> dict[Coord, float]:
    """Bayes PREDICTION step: redistribute each cell's mass over `agent`'s legal moves.

    `agent` names which state field ("cop" or "thief") this prior tracks --
    matching `pathfind.bfs()`'s own convention so a caller never special-cases
    which side it is predicting for. The normalized invariant is asserted
    both on entry and on the result: a prior that quietly stops summing to 1
    must fail loud here, not degrade the fallback silently (D-10).
    """
    _assert_normalized(prior)
    spread_mass: dict[Coord, float] = {}
    for cell, mass in prior.items():
        if mass <= 0.0:
            continue
        probe = _probe_state(state, agent, cell)
        destinations = get_legal_moves(probe, agent, params)
        share = mass / len(destinations)
        for dest in destinations:
            spread_mass[dest] = spread_mass.get(dest, 0.0) + share
    normalized = _normalize(spread_mass)
    _assert_normalized(normalized)
    return normalized


def argmax_cell(prior: dict[Coord, float]) -> Coord:
    """The most likely cell. Ties break toward the smallest (row, col) cell,
    deterministically, so a replayed game reproduces the same believed target."""
    if not prior:
        raise ValueError("prior must not be empty")
    best_cell: Coord = next(iter(sorted(prior)))
    best_mass = float("-inf")
    for cell in sorted(prior):
        mass = prior[cell]
        if mass > best_mass + _MASS_TOLERANCE:
            best_mass = mass
            best_cell = cell
    return best_cell


def _probe_state(state: GameState, agent: str, cell: Coord) -> GameState:
    """`state` with `agent`'s position replaced by `cell` -- never mutates `state`."""
    return (
        dataclasses.replace(state, cop=cell)
        if agent == "cop"
        else dataclasses.replace(state, thief=cell)
    )


def _normalize(mass: dict[Coord, float]) -> dict[Coord, float]:
    total = sum(mass.values())
    if total <= 0.0:
        raise ValueError("prior mass collapsed to zero during spread")
    return {cell: value / total for cell, value in mass.items()}


def _assert_normalized(prior: dict[Coord, float]) -> None:
    total = sum(prior.values())
    if abs(total - 1.0) > _MASS_TOLERANCE:
        raise ValueError(f"prior must sum to 1.0 within tolerance, got {total}")
