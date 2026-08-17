"""Rules 8-9, asked as a RECOVERY question (07-11): not "does the true cell
appear as a value in the serialised view" -- 07-03 answered that -- but "can
the true cell be RECOVERED from what a rules-compliant GUI would DRAW".

At HEAD it could, four different ways, all measured through the shipped path
with the real `config/police/*.json`: `belief.argmax == (5, 3)`, the true
cell; `argmax(scent.opponent) == (5, 3)` at value 0.9, which is exactly
`scent.json`'s `"source"`, i.e. the unmixed kernel centre and not a decayed
trace; the belief support `[(4,3),(5,2),(5,3),(5,4),(6,3)]`, 5 cells of 49,
inverting geometrically to `[(5, 3)]`; and a sealed thief published as
`argmax (0,0)`, `entropy -0.0`, `lit cells [(0,0,1.0)]` -- a one-pixel
heatmap painted on the truth, for the price of 2 barriers out of a quota of
14, in the endgame that IS the cop's win condition.

THE OBVIOUS FIX IS A TRAP AND THIS FILE IS THE REASON IT IS WRITTEN THIS WAY.
Deleting `BeliefView.argmax` makes 07-03's coordinate scanner return `[]` --
a clean verdict with the leak fully intact, because the support still
inverts. `test_the_inversion_attack_is_not_a_no_op` is the anti-vacuity
control: without it, a `geometric_inversion` that always returned `[]` would
make the load-bearing assertion here pass while the disqualification shipped.
"""

from __future__ import annotations

import dataclasses

import pytest

from pursuit.sdk.view_builder import HintHistory, build_local_view
from pursuit.strategy.display_belief import DisplayBelief
from tests.unit import local_view_fixtures as fx
from tests.unit import local_view_production as prod
from tests.unit import local_view_scanner as scan
from tests.unit._fakes_agent import make_ctx

#: The cop's win condition, not a corner case: the thief walled into a
#: corner so that STAY is its only legal action, at which point `spread` is
#: the identity and an `observe_exact` delta never disperses at all. Two
#: barriers against `game_params.json`'s `"barrier_quota": 14`.
SEALED_CELL = (0, 0)
SEALING_BARRIERS = frozenset({(0, 1), (1, 0)})
SEALED_COP_CELL = (3, 3)
SEALED_TURN = 6


@pytest.fixture
def view(tmp_path, default_params, network_params):
    """A cop view built through the production path -- `decide()` called with
    `known_cell=ctx.state.thief`, exactly as `choose_destination` calls it."""
    return fx.honest_view(tmp_path, default_params, network_params)


@pytest.fixture
def sealed_view(tmp_path, default_params, network_params):
    ctx = make_ctx(tmp_path, default_params, network_params, role="police")
    ctx.state = dataclasses.replace(
        ctx.state, cop=SEALED_COP_CELL, thief=SEALED_CELL, barriers=SEALING_BARRIERS,
        barriers_placed=len(SEALING_BARRIERS), turn=SEALED_TURN,
    )
    ctx.scent_field = fx.scent_field(default_params, cell=SEALED_COP_CELL)
    ctx.brain = fx.belief_adapter(default_params)
    prod.seed_belief_as_production_does(ctx)
    return build_local_view(ctx, HintHistory())


def test_the_published_belief_argmax_is_not_the_true_cell(view):
    """(1) The cheapest recovery of all: read the brightest pixel."""
    assert view.belief is not None
    assert view.belief.argmax != fx.OPPONENT_CELL


def test_the_published_opponent_scent_peak_is_not_the_true_cell(view):
    """(2) `scent.opponent` leaks INDEPENDENTLY of the belief, so fixing only
    the belief is a half fix. Decay is a uniform scalar, so two consecutive
    published snapshots subtract to recover the fresh deposit -- even an
    animate-only GUI leaks every turn."""
    assert view.scent is not None
    assert prod.grid_argmax(view.scent.opponent) != fx.OPPONENT_CELL


def test_the_belief_support_does_not_geometrically_invert_to_the_true_cell(view):
    """(3) THE LOAD-BEARING ASSERTION, and the one a coordinate scan cannot
    make. Paired with `test_the_inversion_attack_is_not_a_no_op` below."""
    support = prod.support_cells(view.belief.rows)
    recovered = prod.geometric_inversion(support, view.board_size)
    assert fx.OPPONENT_CELL not in recovered, (
        f"the true cell inverts out of the published support {support}: {recovered}"
    )


def test_the_published_belief_clears_the_configured_floors(view):
    """(4) The floors from `belief.json`'s `display` group -- never restated
    as literals here. `min_support_cells` exceeds the largest legal-move
    neighbourhood, which is what makes assertion (3) structural rather than
    lucky."""
    floors = prod.display_floors()
    support = prod.support_cells(view.belief.rows)
    assert len(support) >= floors.min_support_cells
    assert view.belief.entropy >= floors.min_entropy_bits


def test_the_sealed_thief_endgame_does_not_publish_a_one_pixel_heatmap(sealed_view):
    """The whole recovery set again, in the endgame where `spread` is the
    identity and the delta cannot disperse even in principle."""
    floors = prod.display_floors()
    assert sealed_view.belief is not None
    support = prod.support_cells(sealed_view.belief.rows)
    assert sealed_view.belief.argmax != SEALED_CELL
    assert prod.grid_argmax(sealed_view.scent.opponent) != SEALED_CELL
    assert SEALED_CELL not in prod.geometric_inversion(support, sealed_view.board_size)
    assert len(support) >= floors.min_support_cells
    assert sealed_view.belief.entropy >= floors.min_entropy_bits


def test_the_inversion_attack_is_not_a_no_op(default_params):
    """ANTI-VACUITY, and the reason this file is not another absence test:
    the identical inversion, given the support `observe_exact` + `spread`
    actually produced at HEAD, returns the true cell and only the true cell.
    A `geometric_inversion` that always returned `[]` would make the
    load-bearing assertions above pass while the leak shipped."""
    size = default_params.board_size
    row, col = fx.OPPONENT_CELL
    leaked_support = [(row - 1, col), (row, col - 1), (row, col), (row, col + 1), (row + 1, col)]
    assert len(leaked_support) == 5, "the legal-move plus is STAY plus four moves"
    assert prod.geometric_inversion(leaked_support, size) == [fx.OPPONENT_CELL]
    assert prod.geometric_inversion([], size) == []


def test_the_argmax_only_fix_would_still_leak(
    tmp_path, default_params, network_params, monkeypatch
):
    """THE TRAP, pinned permanently. Put the strategy maps back on the wire
    (what HEAD published) and redact `argmax` from the payload -- which is
    exactly what deleting `BeliefView.argmax` would achieve. 07-03's
    coordinate scanner then returns a CLEAN verdict on a payload from which
    the true cell is still recoverable twice over. Any fix validated by a
    coordinate-absence test would have shipped the disqualification."""
    monkeypatch.setattr(DisplayBelief, "published_belief", lambda self, strategy: strategy)
    monkeypatch.setattr(DisplayBelief, "published_scent", lambda self, actual: actual)
    view = fx.honest_view(tmp_path, default_params, network_params)
    payload = scan.payloads(view)["asdict"]
    assert payload["belief"].pop("argmax") == fx.OPPONENT_CELL, "the map is the truth"
    assert scan.coordinate_hits(payload, fx.OPPONENT_CELL, view.board_size) == [], (
        "the argmax-only fix does buy a clean scanner verdict -- that is the trap"
    )
    support = prod.support_cells(view.belief.rows)
    assert prod.geometric_inversion(support, view.board_size) == [fx.OPPONENT_CELL]
    assert prod.grid_argmax(view.scent.opponent) == fx.OPPONENT_CELL


def test_the_scent_peak_reader_is_not_a_no_op(view):
    """ANTI-VACUITY for assertion (2): `grid_argmax` must actually find the
    strongest cell, or its verdict about the opponent grid means nothing."""
    peak = prod.grid_argmax(view.scent.own)
    assert peak == fx.OWN_CELL
    assert view.scent.own[peak[0]][peak[1]] == max(
        value for row in view.scent.own for value in row
    )
