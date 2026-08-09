"""hint_likelihood: turning a decoded Inference into a Bayes likelihood
grid, weighted well below scent's own influence (D-40) and scaled by how
much THIS opponent has earned this game (D-51's adaptive `reliability.py`).

The translation from `Inference` to a per-cell distribution `q` lives HERE,
in `strategy/`, not in `services/llm/decode.py` -- 04-07 deliberately left it
out because it needs the board (a region needs `board_size` to become
cells; a heading needs the negotiated axis convention), and the decoder owns
no board.

`L(c) = w . [r . q(c) + (1 - r) . u(c)] + (1 - w) . u(c)`, then multiplied by
the decoder's OWN read-confidence -- a different question from reliability's
"do we trust this opponent's words" (see `shared/inference.py`). `w`
(`hint_likelihood.weight`, belief.json) is D-40's OTHER, still-fixed number
-- unlike `r` (`reliability.py`), unchanged by D-51 -- and the loader
(`shared/hint_likelihood_config.py`) refuses a config where it is not
strictly below `scent_likelihood.weight`, by name.

Mixing with `u`, the flat uniform baseline, means a hint can never zero a
cell: even a maximally confident, maximally trusted hint leaves
`(1 - w) . u(c) > 0` everywhere (guaranteed since `r_max < 1` is validated
strictly, so `w` and `r` can never together reach 1). At `confidence == 0`
(`NO_EVIDENCE`, or a heading with nothing to anchor it -- `Inference.is_evidence`)
the WHOLE grid comes back zero, which is deliberate: `BeliefMap.update()`'s
own zero-guard treats a degenerate all-zero product as "explains nothing"
and returns the PRIOR EXACTLY, unchanged bit for bit -- not merely
approximately, per D-33.
"""

from __future__ import annotations

from pursuit.shared.belief_config import BeliefParams
from pursuit.shared.directions import DEFAULT_ORIGIN, DirectionWord, axis_signs
from pursuit.shared.inference import Coord, Inference
from pursuit.strategy.belief_motion import Grid
from pursuit.strategy.regions import region_cells
from pursuit.strategy.reliability import Reliability


def hint_likelihood(
    inference: Inference,
    reliability: Reliability,
    board_size: int,
    config: BeliefParams,
) -> Grid:
    """Return the D-40 hint likelihood over a `board_size` x `board_size`
    grid.

    Every cell defaults to ALL-ZERO when `inference` carries no confidence
    -- see module docstring for why that, not a neutral-1.0 grid, is what
    buys the exact no-op D-33 requires.
    """
    size = board_size
    if inference.confidence <= 0.0:
        return [[0.0] * size for _ in range(size)]

    implied = _implied_distribution(inference, size)
    uniform_share = 1.0 / (size * size)
    w = config.hint_likelihood.weight
    r = reliability.value
    grid: Grid = [[0.0] * size for _ in range(size)]
    for row in range(size):
        for col in range(size):
            q_cell = implied.get((row, col), 0.0)
            mixed = r * q_cell + (1.0 - r) * uniform_share
            grid[row][col] = inference.confidence * (w * mixed + (1.0 - w) * uniform_share)
    return grid


def _implied_distribution(inference: Inference, board_size: int) -> dict[Coord, float]:
    """The decoder's claim, turned into a distribution over the cells it
    implicates.

    Explicit cells verbatim, a named region via `strategy/regions.py`, and
    -- when a heading rides ALONGSIDE either -- a directional tilt within
    that same cell set (never outside it, never zeroing a cell inside it).
    A heading with no region or cells to anchor it (a shape this codebase's
    own decoder never actually emits at positive confidence --
    `Inference.is_evidence`) has nothing to translate and returns empty,
    which the caller reads as "no shift, fall through to uniform only".
    """
    if inference.cells:
        base = tuple(sorted(set(inference.cells)))
    elif inference.region is not None:
        base = tuple(sorted(region_cells(inference.region, board_size)))
    else:
        return {}
    if inference.direction is None:
        share = 1.0 / len(base)
        return dict.fromkeys(base, share)
    return _tilted(base, inference.direction)


def _tilted(cells: tuple[Coord, ...], direction: DirectionWord) -> dict[Coord, float]:
    """Weight `cells` by how far each sits toward `direction`, shifted so the
    LEAST-favoured cell in the claim still carries positive mass -- a
    heading never zeroes a cell within the region/cells it rides alongside,
    matching the module-wide "no cell is ever zeroed" guarantee at every
    scale, not just the whole-board one."""
    ranks = {cell: _tilt(cell, direction) for cell in cells}
    floor = min(ranks.values())
    weights = {cell: (rank - floor) + 1.0 for cell, rank in ranks.items()}
    total = sum(weights.values())
    return {cell: weight / total for cell, weight in weights.items()}


def _tilt(cell: Coord, direction: DirectionWord, origin: str = DEFAULT_ORIGIN) -> float:
    """How far `cell` sits toward `direction`, resolved against the
    negotiated axis origin the wire codec and `strategy/regions.py` both use
    (`shared/directions.axis_signs`).

    A RANKING scale, not a step vector: it orders cells within an
    already-claimed set, and never moves a claim off it -- unlike
    `network/move_payload.py`'s own word-to-step resolution, which `strategy/`
    may not import (STRAT-03) and which answers a different question (where
    does one legal step land) from this one (which claimed cell is most
    "in that direction").
    """
    row_sign, col_sign = axis_signs(origin)
    row, col = cell
    if direction is DirectionWord.NORTH:
        return -row * row_sign
    if direction is DirectionWord.SOUTH:
        return row * row_sign
    if direction is DirectionWord.EAST:
        return col * col_sign
    if direction is DirectionWord.WEST:
        return -col * col_sign
    return 0.0
