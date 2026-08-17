"""`sdk/view_render.py` -- every derivation the dashboard draws.

It lives in `sdk/` and is tested here because `pyproject.toml:38` omits
`*/gui/*` from coverage: the same code under `gui/` would be untested and
would look like the >=85% gate had passed.
"""

from __future__ import annotations

import dataclasses

import pytest

from pursuit.sdk.view_render import (
    BACKGROUND_COLOUR,
    BARRIER_COLOUR,
    CELL_PIXELS,
    EMPTY_COLOUR,
    HEAT_RAMP,
    OWN_COLOUR,
    PANEL_TITLES,
    belief_colours,
    blank_grid,
    board_colours,
    canvas_extent,
    cell_rectangles,
    grid_extent,
    grid_peak,
    lit_cells,
    panel_grids,
    panel_positions,
    scent_colours,
    shade,
    shaded_grid,
)
from tests.unit import local_view_fixtures as fx

#: Smaller than any probability a 49-cell posterior can carry, and still lit.
TINY = 1e-12

_SPARSE = ((1.0, TINY, 0.0), (0.0, 0.5, 0.0), (0.0, 0.0, 0.25))


@pytest.fixture
def view(tmp_path, default_params, network_params):
    return fx.honest_view(tmp_path, default_params, network_params)


def test_the_background_is_reserved_for_zero_mass():
    assert shade(0.0, 1.0) == BACKGROUND_COLOUR
    assert shade(-1.0, 1.0) == BACKGROUND_COLOUR
    assert shade(1.0, 0.0) == BACKGROUND_COLOUR


def test_a_vanishingly_small_probability_is_still_painted():
    """THE RULES 8-9 PROPERTY OF THE RAMP. A stop that rounded a small value
    down to the background would draw a SMALLER support than the published
    grid carries, and `display.min_support_cells` -- the floor that makes the
    geometric inversion return `[]` -- guards the published support, not the
    drawn one."""
    assert shade(TINY, 1.0) == HEAT_RAMP[0]
    assert shade(1.0, 1.0) == HEAT_RAMP[-1]


def test_the_drawn_support_is_exactly_the_positive_support():
    lit = lit_cells(shaded_grid(_SPARSE))
    assert lit == [(0, 0), (0, 1), (1, 1), (2, 2)]
    assert len(lit) == sum(1 for row in _SPARSE for value in row if value > 0.0)


def test_every_stop_in_the_ramp_is_reachable():
    """A thinned or duplicated ramp would quietly coarsen every heatmap."""
    peak = float(len(HEAT_RAMP))
    reached = {shade(step + 1.0, peak) for step in range(len(HEAT_RAMP))}
    assert reached == set(HEAT_RAMP)
    assert len(set(HEAT_RAMP)) == len(HEAT_RAMP)


def test_grid_peak_is_total_over_an_empty_grid():
    assert grid_peak(()) == 0.0
    assert grid_peak(((0.0, 0.0),)) == 0.0
    assert grid_peak(_SPARSE) == 1.0


def test_the_board_distinguishes_only_own_cell_and_declared_barriers(view):
    colours = board_colours(view)
    assert colours[fx.OWN_CELL[0]][fx.OWN_CELL[1]] == OWN_COLOUR
    assert {colours[r][c] for r, c in fx.BARRIERS} == {BARRIER_COLOUR}
    painted = {colour for row in colours for colour in row}
    assert painted == {OWN_COLOUR, BARRIER_COLOUR, EMPTY_COLOUR}


def test_a_blank_grid_paints_nothing_at_all():
    blank = blank_grid(len(_SPARSE))
    assert lit_cells(blank) == []
    assert {colour for row in blank for colour in row} == {BACKGROUND_COLOUR}


def test_an_absent_belief_renders_as_none_then_as_a_blank_panel(view):
    """07-11 made this a LIVE case: the publication floor can refuse a map
    mid-game, not only a disabled belief layer."""
    without = dataclasses.replace(view, belief=None)
    assert belief_colours(without) is None
    assert lit_cells(panel_grids(without)[PANEL_TITLES.index("belief over the opponent")]) == []


def test_an_absent_scent_renders_as_two_blank_panels(view):
    without = dataclasses.replace(view, scent=None)
    assert scent_colours(without) is None
    grids = panel_grids(without)
    assert lit_cells(grids[-1]) == [] and lit_cells(grids[-2]) == []


def test_every_panel_title_gets_exactly_one_grid(view):
    grids = panel_grids(view)
    assert len(grids) == len(PANEL_TITLES) == len(panel_positions())
    assert len(set(panel_positions())) == len(PANEL_TITLES), "two panels share a cell"
    for grid in grids:
        assert len(grid) == view.board_size
        assert {len(row) for row in grid} == {view.board_size}


def test_the_belief_and_scent_panels_carry_the_published_grids(view):
    grids = panel_grids(view)
    assert grids[PANEL_TITLES.index("belief over the opponent")] == belief_colours(view)
    assert (grids[-2], grids[-1]) == scent_colours(view)


def test_each_scent_grid_is_shaded_against_its_own_peak(view):
    """A shared scale would render the weaker trail flat -- the two grids are
    different quantities, not two halves of one."""
    own, opponent = scent_colours(view)
    assert HEAT_RAMP[-1] in {colour for row in own for colour in row}
    assert HEAT_RAMP[-1] in {colour for row in opponent for colour in row}


def test_the_geometry_covers_every_cell_without_overlap():
    colours = shaded_grid(_SPARSE)
    rectangles = cell_rectangles(colours)
    assert len(rectangles) == len(_SPARSE) ** 2
    assert {(x1 - x0, y1 - y0) for x0, y0, x1, y1, _ in rectangles} == {(CELL_PIXELS, CELL_PIXELS)}
    assert max(x1 for _, _, x1, _, _ in rectangles) < grid_extent(colours)
    assert grid_extent(colours) == canvas_extent(len(_SPARSE))


def test_every_rectangle_carries_its_own_cell_colour():
    colours = shaded_grid(_SPARSE)
    fills = [fill for *_bounds, fill in cell_rectangles(colours)]
    assert fills == [colour for row in colours for colour in row]
