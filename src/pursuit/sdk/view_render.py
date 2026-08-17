"""Every derivation the live dashboard draws: colour, shade and geometry.

THIS LIVES IN `sdk/` AND NOT IN `gui/` BECAUSE OF A MEASURED GAP.
`pyproject.toml:38` omits `*/gui/*` from coverage, so a probability-to-shade
mapping placed there would be invisible to the `fail_under = 85` gate and
would look like it had passed; `scripts/check_line_limit.sh:18` enumerates
`src/** tests/** training/**`, so `scripts/` escapes the size gate as well.
`gui/` therefore holds widget construction and attribute reads only, and
every function below is exercised by `tests/unit/test_view_render.py`.

THE SHADE RAMP RESERVES ITS BACKGROUND FOR EXACTLY ZERO, AND THAT IS A RULES
8-9 DECISION, NOT AN AESTHETIC ONE. Quantising a posterior into buckets is a
NEW way to leak that 07-11 could not have tested: a ramp that rounded small
probabilities down to the background would draw a SMALLER support than the
published grid carries, and `display.min_support_cells` -- the floor that
makes the geometric inversion return `[]` -- guards the published support,
not the drawn one. Shrink the drawn support below that floor and the true
cell inverts back out of a panel whose underlying numbers were compliant. So
`shade` maps every strictly positive value to at least the lowest lit stop,
`lit_cells(shaded_grid(g))` is exactly the positive support of `g`, and
`tests/unit/test_gui_recovery.py` asserts that equality on a production-wired
view before it attempts the inversion.
"""

from __future__ import annotations

import math

from pursuit.sdk.local_view import Grid, LocalView
from pursuit.shared.state import Coord

#: The unlit cell. Reserved for zero mass and for nothing else (see above).
BACKGROUND_COLOUR = "#12161c"

#: Board panel. `own` and the declared barriers are the only cells a board
#: may distinguish: rule 8 gives us our own position, rule 22 makes declared
#: barriers shared knowledge on both sides, and the closed field set carries
#: nothing else to draw.
OWN_COLOUR = "#4ec9b0"
BARRIER_COLOUR = "#c586c0"
EMPTY_COLOUR = "#1e242c"
OUTLINE_COLOUR = "#2b3440"

#: Heat stops, darkest lit to brightest. The number of buckets is
#: `len(HEAT_RAMP)` everywhere below -- never restated as a literal.
HEAT_RAMP = ("#1f3350", "#27507a", "#2f76a0", "#48a3b8", "#86ccc0", "#d7f0cf")

#: Widget geometry, in pixels. Presentation constants named here rather than
#: written inline at a `create_rectangle` call, so `gui/` performs no
#: arithmetic at all (CLAUDE.md: zero hardcoded values, and `gui/` is
#: coverage-omitted).
CELL_PIXELS = 26
CELL_GAP_PIXELS = 1

#: The grid panels, in the order `panel_grids` returns them. `gui/` builds one
#: widget per title and zips the two together with `strict=True`, so a title
#: added here without a grid (or the reverse) raises instead of drawing the
#: wrong data under the wrong heading.
PANEL_BOARD = "board (local truth)"
PANEL_BELIEF = "belief over the opponent"
PANEL_OWN_SCENT = "our own scent"
PANEL_OPPONENT_SCENT = "inferred opponent scent"
PANEL_TITLES = (PANEL_BOARD, PANEL_BELIEF, PANEL_OWN_SCENT, PANEL_OPPONENT_SCENT)

#: How the panels are laid out. Here rather than in `gui/` because it is
#: arithmetic, and `gui/` performs none.
PANELS_PER_ROW = 2


def grid_peak(grid: Grid) -> float:
    """The largest value in a dense grid, or 0.0 for an empty one."""
    return max((value for row in grid for value in row), default=0.0)


def shade(value: float, peak: float) -> str:
    """`value` as a heat stop, relative to `peak`.

    Strictly positive input NEVER returns `BACKGROUND_COLOUR`: the lowest
    bucket is `HEAT_RAMP[0]`, so the drawn support cannot be smaller than the
    published one. A non-positive peak means there is nothing lit at all.
    """
    if value <= 0.0 or peak <= 0.0:
        return BACKGROUND_COLOUR
    bucket = math.ceil(value / peak * len(HEAT_RAMP))
    return HEAT_RAMP[min(max(bucket, 1), len(HEAT_RAMP)) - 1]


def shaded_grid(grid: Grid) -> tuple[tuple[str, ...], ...]:
    """A dense probability/intensity grid as a dense grid of colours."""
    peak = grid_peak(grid)
    return tuple(tuple(shade(value, peak) for value in row) for row in grid)


def lit_cells(colours: tuple[tuple[str, ...], ...]) -> list[Coord]:
    """Every cell a panel actually paints -- the DRAWN support. The recovery
    test attacks this, not the numbers behind it."""
    return [
        (row, col)
        for row, cells in enumerate(colours)
        for col, colour in enumerate(cells)
        if colour != BACKGROUND_COLOUR
    ]


def board_colours(view: LocalView) -> tuple[tuple[str, ...], ...]:
    """The board panel: own cell, declared barriers, everything else empty."""
    barriers = set(view.declared_barriers)
    return tuple(
        tuple(_board_cell((row, col), view.own_cell, barriers) for col in range(view.board_size))
        for row in range(view.board_size)
    )


def _board_cell(cell: Coord, own: Coord, barriers: set) -> str:
    if cell == own:
        return OWN_COLOUR
    return BARRIER_COLOUR if cell in barriers else EMPTY_COLOUR


def belief_colours(view: LocalView) -> tuple[tuple[str, ...], ...] | None:
    """The belief heatmap, or None when nothing was published this turn.

    None is the honest empty panel: belief off this game, or 07-11's floor
    guard refusing to publish a map that names a cell. It is never replaced
    by a fabricated uniform grid.
    """
    return None if view.belief is None else shaded_grid(view.belief.rows)


def scent_colours(view: LocalView) -> tuple[tuple[tuple[str, ...], ...], ...] | None:
    """`(own, opponent)` shaded, or None when no scent was published. Each
    grid is shaded against ITS OWN peak: the two trails are different
    quantities and a shared scale would render one of them flat."""
    if view.scent is None:
        return None
    return (shaded_grid(view.scent.own), shaded_grid(view.scent.opponent))


def blank_grid(board_size: int) -> tuple[tuple[str, ...], ...]:
    """A panel with nothing painted on it -- every cell the background.

    This is what an absent belief or an absent scent renders as. It is NOT a
    fabricated stand-in: `BACKGROUND_COLOUR` is reserved for zero mass, so a
    blank panel asserts exactly "nothing to show" and `lit_cells` of it is
    empty.
    """
    return tuple(tuple(BACKGROUND_COLOUR for _ in range(board_size)) for _ in range(board_size))


def panel_grids(view: LocalView) -> tuple[tuple[tuple[str, ...], ...], ...]:
    """One colour grid per entry in `PANEL_TITLES`, in that order.

    The None-substitution happens HERE and not in `gui/`: a widget layer that
    decided for itself what to draw when a panel is absent would be making a
    rules 8-9 decision in the one place coverage cannot see it.
    """
    blank = blank_grid(view.board_size)
    belief = belief_colours(view)
    scent = scent_colours(view) or (blank, blank)
    return (board_colours(view), belief or blank, scent[0], scent[1])


def canvas_extent(board_size: int) -> int:
    """Pixel width/height of a `board_size` grid panel."""
    return board_size * (CELL_PIXELS + CELL_GAP_PIXELS) + CELL_GAP_PIXELS


def panel_positions() -> tuple[tuple[int, int], ...]:
    """`(grid row, grid column)` per entry in `PANEL_TITLES`."""
    return tuple(
        (index // PANELS_PER_ROW, index % PANELS_PER_ROW)
        for index in range(len(PANEL_TITLES))
    )


def grid_extent(colours: tuple[tuple[str, ...], ...]) -> int:
    """`canvas_extent` of a grid that is already in hand, so a canvas widget
    never has to size itself from a board_size it would have to be told."""
    return canvas_extent(len(colours))


def cell_rectangles(
    colours: tuple[tuple[str, ...], ...],
) -> list[tuple[int, int, int, int, str]]:
    """`(x0, y0, x1, y1, fill)` per cell, so a canvas widget only has to hand
    each tuple to `create_rectangle` -- no arithmetic in `gui/`."""
    return [
        (*_bounds(row, col), colour)
        for row, cells in enumerate(colours)
        for col, colour in enumerate(cells)
    ]


def _bounds(row: int, col: int) -> tuple[int, int, int, int]:
    x0 = CELL_GAP_PIXELS + col * (CELL_PIXELS + CELL_GAP_PIXELS)
    y0 = CELL_GAP_PIXELS + row * (CELL_PIXELS + CELL_GAP_PIXELS)
    return (x0, y0, x0 + CELL_PIXELS, y0 + CELL_PIXELS)
