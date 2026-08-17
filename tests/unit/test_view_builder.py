"""`view_builder` as a projection: the ONE reader of `ctx.state` outside the
turn loop, the honest-`None` belief convention, and the densification that
keeps a coordinate from ever being a value in a grid.

The hint-history half lives in `test_view_hint_history.py` -- split at the
150-code-line gate (Segal Table 5).
"""

from __future__ import annotations

import ast
import dataclasses
import math
import pathlib

import pytest

from pursuit.network.turn_language import belief_snapshot
from pursuit.sdk.view_builder import HintHistory, build_local_view
from tests.unit import local_view_fixtures as fx
from tests.unit import local_view_production as prod
from tests.unit._fakes_agent import make_ctx

_SDK_ROOT = pathlib.Path(__file__).parents[2] / "src" / "pursuit" / "sdk"
_TRUE_POSITION_FIELDS = ("cop", "thief", "barriers")


def _reads_true_position(path: pathlib.Path) -> bool:
    """True when this module contains a `<anything>.state.<cop|thief|barriers>`
    attribute chain -- the field read D-74 says is the actual leak."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Attribute) or node.attr not in _TRUE_POSITION_FIELDS:
            continue
        if isinstance(node.value, ast.Attribute) and node.value.attr == "state":
            return True
    return False


def test_view_builder_is_the_only_sdk_module_that_reads_the_true_position():
    """D-74: `view_builder` is the ONE place the projection happens."""
    assert len(_TRUE_POSITION_FIELDS) == 3, "GameState's three position fields"
    modules = sorted(_SDK_ROOT.rglob("*.py"))
    assert len(modules) >= 5, f"the sdk scan found only {len(modules)} modules"
    readers = {p.name for p in modules if _reads_true_position(p)}
    assert readers == {"view_builder.py"}, f"unexpected true-position readers: {readers}"


def test_the_scan_above_can_actually_fail(tmp_path):
    """Counter-control for the scan: a module that DOES read `ctx.state.thief`
    is reported, so an empty `readers` set would mean something."""
    leaky = tmp_path / "leaky.py"
    leaky.write_text("def render(ctx):\n    return ctx.state.thief\n", encoding="utf-8")
    clean = tmp_path / "clean.py"
    clean.write_text("def render(view):\n    return view.own_cell\n", encoding="utf-8")
    assert _reads_true_position(leaky) is True
    assert _reads_true_position(clean) is False


def test_belief_disabled_builds_a_none_belief_and_fabricates_nothing(
    tmp_path, default_params, network_params
):
    """The honest-`None` convention `turn_language.belief_snapshot` already
    uses: belief off this game means None, never a uniform stand-in."""
    view = fx.honest_view(tmp_path, default_params, network_params, with_belief=False)
    assert view.belief is None
    assert view.scent is not None


def test_belief_view_carries_the_posterior_argmax_and_reliability(
    tmp_path, default_params, network_params
):
    """07-11: what a cop publishes is the map that clears `belief.json`'s
    `display` floors, not the strategy posterior `observe_exact` collapsed to
    a delta on the engine's truth. The two assertions this test used to make
    -- `argmax == BELIEF_ARGMAX` and `entropy == 0.0` -- described precisely
    that delta, and were only ever green because the fixture seeded it with a
    cell production never supplies."""
    view = fx.honest_view(tmp_path, default_params, network_params)
    floors = prod.display_floors()
    assert view.belief.argmax != fx.OPPONENT_CELL
    assert len(view.belief.rows) == view.board_size
    assert all(len(row) == view.board_size for row in view.belief.rows)
    assert view.belief.entropy >= floors.min_entropy_bits
    assert len(prod.support_cells(view.belief.rows)) >= floors.min_support_cells
    assert 0.0 <= view.belief.reliability <= 1.0


def test_entropy_is_shannon_bits_and_agrees_with_the_jsonl_snapshot(
    tmp_path, default_params, network_params
):
    """`BeliefMap.entropy()` was extracted out of `belief_snapshot` so the
    formula has one owner. Both halves of that are pinned here: the VALUE
    (a uniform 7x7 prior is log2(49) bits, so a base change to `ln` fails)
    and the AGREEMENT of the two consumers on the same map."""
    ctx = fx.honest_context(tmp_path, default_params, network_params)
    ctx.brain = fx.belief_adapter(default_params)
    cells = default_params.board_size**2
    assert ctx.brain.belief.entropy() == pytest.approx(math.log2(cells))
    entropy, argmax, _ = belief_snapshot(ctx)
    view = build_local_view(ctx, HintHistory())
    assert view.belief.entropy == entropy
    assert view.belief.argmax == argmax


def test_belief_and_scent_grids_are_dense_and_positional(
    tmp_path, default_params, network_params
):
    """A coordinate-KEYED grid would put every cell on the board into the
    view as a value, the opponent's true cell among them -- so both are
    densified to row-major floats and nothing in them is a coordinate."""
    view = fx.honest_view(tmp_path, default_params, network_params)
    grids = (view.belief.rows, view.scent.own, view.scent.opponent)
    assert len(grids) == 3
    for grid in grids:
        assert len(grid) == view.board_size
        for row in grid:
            assert len(row) == view.board_size
            assert all(type(value) is float for value in row)


def test_the_scent_grid_keeps_the_values_it_densified(
    tmp_path, default_params, network_params
):
    """Counter-control for the densification: a builder returning an
    all-zero board of the right SHAPE would satisfy the test above."""
    view = fx.honest_view(tmp_path, default_params, network_params)
    row, col = fx.OWN_CELL
    assert view.scent.own[row][col] > 0.0
    assert sum(sum(r) for r in view.scent.own) > 0.0
    assert sum(sum(r) for r in view.belief.rows) == pytest.approx(1.0)


def test_own_cell_follows_the_role_and_never_the_opponent(
    tmp_path, default_params, network_params
):
    ctx = make_ctx(tmp_path, default_params, network_params, role="thief")
    ctx.state = dataclasses.replace(ctx.state, cop=fx.OWN_CELL, thief=fx.OPPONENT_CELL)
    view = build_local_view(ctx, HintHistory())
    assert view.own_cell == fx.OPPONENT_CELL
    assert view.role == "thief"
    assert view.scent is None


def test_the_view_reports_the_machine_state_and_the_freeze_timer(
    tmp_path, default_params, network_params
):
    view = fx.honest_view(tmp_path, default_params, network_params)
    assert view.machine_state == "handshake"
    assert view.idle_seconds == fx.IDLE_SECONDS
    assert view.turn == fx.TURN
    assert view.declared_barriers == tuple(sorted(fx.BARRIERS))
    assert view.barriers_placed == fx.BARRIERS_PLACED
