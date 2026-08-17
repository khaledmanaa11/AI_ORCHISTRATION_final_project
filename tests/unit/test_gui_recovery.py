"""Rules 8-9 asked of WHAT THE PANELS PAINT, at runtime, through the whole
production chain: real `decide()` -> `publish_view` -> the file on disk ->
`read_snapshot` -> the exact `view_render`/`view_text` calls `gui/` makes.

07-11 asked the recovery question of the published NUMBERS and closed it.
This file asks it of the DRAWN OUTPUT, which is a different question, because
rendering can lose information the floors were protecting:

**QUANTISATION IS A NEW WAY TO LEAK.** `display.min_support_cells` = 6 makes
the geometric inversion return `[]` by keeping the published support larger
than any one cell's step neighbourhood. That floor guards the PUBLISHED grid.
A heat ramp that rounded small probabilities down to the background would
draw a SMALLER support than the grid carries -- and a drawn support of five
cells shaped like a legal-move plus names its centre exactly as loudly as a
printed coordinate would, off numbers that were themselves compliant. So the
first assertion below is an EQUALITY between the drawn support and the
published one, and only then is the inversion attempted.

`scripts/check_local_truth.py` is NOT evidence here and is not cited: it is an
import/attribute gate, and 07-11 measured it returning `violations: []`,
exit 0 against a synthetic panel that markered `belief.argmax` and labelled
the `scent.opponent` peak (D7-9).
"""

from __future__ import annotations

import pytest

from pursuit.sdk import view_render as render
from pursuit.sdk import view_text as text
from pursuit.sdk.view_publish import publish_view, snapshot_path_for
from pursuit.sdk.view_snapshot import read_snapshot
from pursuit.strategy.display_belief import DisplayBelief
from tests.unit import local_view_fixtures as fx
from tests.unit import local_view_production as prod
from tests.unit import local_view_scanner as scan


def _published(tmp_path, default_params, network_params):
    """The view as the GUI PROCESS receives it: written to disk by the agent
    and read back through `read_snapshot`, never handed over in memory."""
    ctx = fx.honest_context(tmp_path, default_params, network_params)
    assert ctx.state.thief == fx.OPPONENT_CELL, "the agent must actually hold the truth"
    publish_view(ctx, ctx.view_history)
    view = read_snapshot(snapshot_path_for(ctx.log_path))
    assert view is not None
    return view


def _brightest(colours) -> list[tuple[int, int]]:
    """Every cell painted the top heat stop -- the one a viewer's eye goes to."""
    return [
        (row, col)
        for row, cells in enumerate(colours)
        for col, colour in enumerate(cells)
        if colour == render.HEAT_RAMP[-1]
    ]


@pytest.fixture
def drawn(tmp_path, default_params, network_params):
    return _published(tmp_path, default_params, network_params)


def test_the_drawn_belief_support_is_exactly_the_published_support(drawn):
    """THE QUANTISATION ASSERTION. Shrink this and the floor stops floring."""
    lit = render.lit_cells(render.belief_colours(drawn))
    assert lit == prod.support_cells(drawn.belief.rows)
    assert len(lit) >= prod.display_floors().min_support_cells


def test_the_drawn_belief_does_not_invert_to_the_true_cell(drawn):
    """THE LOAD-BEARING ASSERTION, over the painted cells rather than the
    numbers behind them."""
    lit = render.lit_cells(render.belief_colours(drawn))
    recovered = prod.geometric_inversion(lit, drawn.board_size)
    assert fx.OPPONENT_CELL not in recovered, f"the panel inverts to the truth: {recovered}"


def test_the_brightest_drawn_belief_cells_do_not_name_the_true_cell(drawn):
    """A viewer's eye goes to the top heat stop, so the top stop is attacked
    as a support in its own right.

    MEASURED, and the reason this is an inversion rather than a membership
    test: on the honest published map the top stop holds 20-odd cells of 49
    -- the posterior is nearly uniform (peak 0.0223), so `ceil(v/peak * 6)`
    puts most of the board in the last bucket, and the true cell is among
    them by arithmetic rather than by disclosure. What would be a leak is the
    top stop NAMING a cell, which is exactly what the inversion asks.
    """
    brightest = _brightest(render.belief_colours(drawn))
    assert brightest, "an empty brightest set would pass this vacuously"
    assert fx.OPPONENT_CELL not in prod.geometric_inversion(brightest, drawn.board_size)


def test_the_drawn_opponent_scent_does_not_recover_the_true_cell(drawn):
    """`scent.opponent` leaks INDEPENDENTLY of the belief, so it is attacked
    independently: peak, brightest stop and geometric inversion."""
    _own, opponent = render.scent_colours(drawn)
    lit = render.lit_cells(opponent)
    brightest = _brightest(opponent)
    assert lit and brightest, "an unlit scent panel would pass this vacuously"
    assert prod.grid_argmax(drawn.scent.opponent) != fx.OPPONENT_CELL
    assert fx.OPPONENT_CELL not in prod.geometric_inversion(brightest, drawn.board_size)
    assert fx.OPPONENT_CELL not in prod.geometric_inversion(lit, drawn.board_size)


def test_the_board_panel_paints_only_own_position_and_declared_barriers(drawn):
    """Rule 8 gives us our own cell; rule 22 makes declared barriers shared
    knowledge. Nothing else on the board may be distinguishable."""
    colours = render.board_colours(drawn)
    assert colours[fx.OWN_CELL[0]][fx.OWN_CELL[1]] == render.OWN_COLOUR
    for row, col in fx.BARRIERS:
        assert colours[row][col] == render.BARRIER_COLOUR
    assert colours[fx.OPPONENT_CELL[0]][fx.OPPONENT_CELL[1]] == render.EMPTY_COLOUR


def test_the_sidebar_text_carries_no_encoding_of_the_true_cell(drawn):
    blocks = {"sidebar": list(text.sidebar_blocks(drawn))}
    assert scan.coordinate_hits(blocks, fx.OPPONENT_CELL, drawn.board_size) == []


def test_the_sidebar_scan_is_not_a_no_op(drawn):
    """ANTI-VACUITY: the identical scan over the identical blocks, asked for
    a cell the sidebar legitimately DOES print, must find it."""
    blocks = {"sidebar": list(text.sidebar_blocks(drawn))}
    assert scan.coordinate_hits(blocks, fx.OWN_CELL, drawn.board_size)


def test_a_leaky_panel_fails_every_assertion_above(
    tmp_path, default_params, network_params, monkeypatch
):
    """THE COUNTER-CONTROL, and without it this whole file proves nothing.

    Put HEAD's leak back -- publish the strategy maps, which on the cop seat
    are `observe_exact`'d onto `ctx.state.thief` -- and render the result with
    the SAME functions. Every recovery above must succeed.
    """
    monkeypatch.setattr(DisplayBelief, "published_belief", lambda self, strategy: strategy)
    monkeypatch.setattr(DisplayBelief, "published_scent", lambda self, actual: actual)
    leaky = _published(tmp_path, default_params, network_params)

    lit = render.lit_cells(render.belief_colours(leaky))
    assert prod.geometric_inversion(lit, leaky.board_size) == [fx.OPPONENT_CELL]
    brightest = _brightest(render.belief_colours(leaky))
    assert fx.OPPONENT_CELL in prod.geometric_inversion(brightest, leaky.board_size)
    _own, opponent = render.scent_colours(leaky)
    assert _brightest(opponent) == [fx.OPPONENT_CELL]
    assert scan.coordinate_hits(
        {"sidebar": list(text.sidebar_blocks(leaky))}, fx.OPPONENT_CELL, leaky.board_size
    ), "the sidebar prints the peak cell, so a leaked argmax shows up in the text too"


def test_the_argmax_only_fix_still_leaks_through_the_panels(
    tmp_path, default_params, network_params, monkeypatch
):
    """THE TRAP, re-run at the RENDER layer. Deleting `BeliefView.argmax`
    buys a clean coordinate-scan verdict AND a clean sidebar, and the heatmap
    still inverts to the true cell. A panel validated by absence alone would
    have shipped the disqualification."""
    monkeypatch.setattr(DisplayBelief, "published_belief", lambda self, strategy: strategy)
    monkeypatch.setattr(DisplayBelief, "published_scent", lambda self, actual: actual)
    leaky = _published(tmp_path, default_params, network_params)

    lines = tuple(line for line in text.belief_lines(leaky) if "peak cell" not in line)
    assert scan.coordinate_hits(
        {"sidebar": [text.as_block(lines)]}, fx.OPPONENT_CELL, leaky.board_size
    ) == [], "dropping the peak-cell line does buy a clean scan -- that is the trap"
    lit = render.lit_cells(render.belief_colours(leaky))
    assert prod.geometric_inversion(lit, leaky.board_size) == [fx.OPPONENT_CELL]
