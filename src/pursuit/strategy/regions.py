"""Turning the nine named sectors into actual cells, on the strategy side.

`shared/inference.py` owns the `Region` VOCABULARY, because the decoder in
`services/llm/` has to constrain a model to it and that layer owns no board
(04-07 must_haves: *"the decoded region is translated to cells INSIDE the
strategy layer, not here"*). This module is that translation, and it is the
ONLY one -- 04-08's deception policies and 04-09's hint likelihood both call
it rather than each deriving a sector grid of their own.

The split is by thirds along each axis, which for the shipped 7x7 board gives
bands of 3 / 2 / 2 cells. Coarse on purpose: a hint is one short sentence,
and a sector vocabulary finer than the sentences can support would invite
precision the text never carried.

Orientation is DERIVED from the negotiated axis origin (PARAMETERS.md Table
13 row 3) via `shared/directions.axis_signs`, the same function the wire
codec resolves its direction tokens with -- so a game agreed on a
`bottom-left` origin has "north" mean the same thing to the mover, to the
hint we send, and to the hint we receive.
"""

from __future__ import annotations

from pursuit.shared.directions import DEFAULT_ORIGIN, axis_signs
from pursuit.shared.inference import Coord, Region

_BAND_COUNT = 3

#: (row_band, col_band) -> Region, in the natural top-left reading order.
#: Band 0 is the low end of the axis, band 2 the high end, AFTER the origin's
#: sign has been applied -- so this table itself never assumes a corner.
_SECTORS: dict[tuple[int, int], Region] = {
    (0, 0): Region.NORTHWEST,
    (0, 1): Region.NORTH,
    (0, 2): Region.NORTHEAST,
    (1, 0): Region.WEST,
    (1, 1): Region.CENTER,
    (1, 2): Region.EAST,
    (2, 0): Region.SOUTHWEST,
    (2, 1): Region.SOUTH,
    (2, 2): Region.SOUTHEAST,
}


def _band(index: int, board_size: int, sign: int) -> int:
    """Which third of the axis `index` falls in, under `sign`.

    A negative sign (a bottom-* or *-right origin) mirrors the axis, so the
    same cell lands in the opposite band and "north" keeps pointing at the
    corner the two peers agreed on.
    """
    position = index if sign > 0 else board_size - 1 - index
    return min(position * _BAND_COUNT // board_size, _BAND_COUNT - 1)


def region_of(cell: Coord, board_size: int, *, origin: str = DEFAULT_ORIGIN) -> Region:
    """The sector `cell` sits in."""
    row_sign, col_sign = axis_signs(origin)
    return _SECTORS[
        (_band(cell[0], board_size, row_sign), _band(cell[1], board_size, col_sign))
    ]


def region_cells(
    region: Region, board_size: int, *, origin: str = DEFAULT_ORIGIN
) -> frozenset[Coord]:
    """Every cell in `region`.

    Derived by asking `region_of` about each cell rather than by inverting
    the band arithmetic, so the two functions cannot disagree: whatever
    `region_of` says is what `region_cells` returns, by construction.
    """
    return frozenset(
        (row, col)
        for row in range(board_size)
        for col in range(board_size)
        if region_of((row, col), board_size, origin=origin) is region
    )


def region_center(
    region: Region, board_size: int, *, origin: str = DEFAULT_ORIGIN
) -> Coord:
    """The cell nearest the centroid of `region`, for distance scoring.

    Ties break toward the lowest row then the lowest column, so a replay
    reproduces the same choice -- the same deterministic-ordering convention
    `belief.argmax` and `sdk/actions.py` already follow.
    """
    cells = region_cells(region, board_size, origin=origin)
    mean_row = sum(row for row, _ in cells) / len(cells)
    mean_col = sum(col for _, col in cells) / len(cells)
    return min(cells, key=lambda c: (abs(c[0] - mean_row) + abs(c[1] - mean_col), c))


def region_distance(
    first: Region, second: Region, board_size: int, *, origin: str = DEFAULT_ORIGIN
) -> int:
    """Manhattan distance between two sectors' centres.

    Used to score how far a candidate claim sits from the sector our own
    freshest scent trail betrays -- book Sec4.4's contradiction test, run on
    ourselves before we commit to a lie.
    """
    a = region_center(first, board_size, origin=origin)
    b = region_center(second, board_size, origin=origin)
    return abs(a[0] - b[0]) + abs(a[1] - b[1])
