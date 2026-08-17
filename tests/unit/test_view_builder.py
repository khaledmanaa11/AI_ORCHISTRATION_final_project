"""`view_builder` behaviour: the ONE reader of `ctx.state` outside the turn
loop, the honest-`None` belief convention, and the caller-owned hint history
(NET-02 -- never a module-level global, never a class attribute).

Peer data is hostile by 05-12's boundary rule: `ctx.incoming_hints[sender]`
is whatever arrived over the wire, validated as nothing more than a dict.
The accumulator must be TOTAL over it -- a view that raises is a dashboard
that dies mid-game.
"""

from __future__ import annotations

import ast
import dataclasses
import pathlib

import pytest
from pursuit.sdk.view_builder import HintHistory, build_local_view

from tests.unit import local_view_fixtures as fx
from tests.unit._fakes_agent import make_ctx

_SDK_ROOT = pathlib.Path(__file__).parents[2] / "src" / "pursuit" / "sdk"
_TRUE_POSITION_FIELDS = ("cop", "thief", "barriers")

_HOSTILE_PAYLOADS = (
    {},
    {"text": None},
    {"text": 17, "intent": "lie", "turn": 1},
    {"text": "ok", "intent": "maybe", "turn": "3"},
    {"text": "ok", "intent": "truth", "turn": True},
    "not a dict at all",
)


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
    modules = sorted(_SDK_ROOT.rglob("*.py"))
    assert len(modules) >= 5, f"the sdk scan found only {len(modules)} modules"
    readers = {p.name for p in modules if _reads_true_position(p)}
    assert readers == {"view_builder.py"}, f"unexpected true-position readers: {readers}"


def test_the_scan_above_can_actually_fail(tmp_path):
    """Counter-control for the scan: a module that DOES read `ctx.state.thief`
    is reported, so an empty `readers` set means something."""
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
    view = fx.honest_view(tmp_path, default_params, network_params)
    assert view.belief.argmax == fx.BELIEF_ARGMAX
    assert len(view.belief.rows) == view.board_size
    assert all(len(row) == view.board_size for row in view.belief.rows)
    assert view.belief.entropy == pytest.approx(0.0)
    assert 0.0 <= view.belief.reliability <= 1.0


def test_belief_and_scent_grids_are_dense_and_positional(
    tmp_path, default_params, network_params
):
    """Coordinate-KEYED grids would put every cell on the board into the
    view as a value, including the opponent's -- so both are densified to
    row-major floats and nothing in them is a coordinate."""
    view = fx.honest_view(tmp_path, default_params, network_params)
    grids = (view.belief.rows, view.scent.own, view.scent.opponent)
    assert len(grids) == 3
    for grid in grids:
        assert len(grid) == view.board_size
        for row in grid:
            assert len(row) == view.board_size
            assert all(isinstance(value, float) for value in row)


def test_own_cell_follows_the_role_and_never_the_opponent(
    tmp_path, default_params, network_params
):
    ctx = make_ctx(tmp_path, default_params, network_params, role="thief")
    ctx.state = dataclasses.replace(ctx.state, cop=fx.OWN_CELL, thief=fx.OPPONENT_CELL)
    view = build_local_view(ctx, HintHistory())
    assert view.own_cell == fx.OPPONENT_CELL
    assert view.role == "thief"


def test_incoming_hints_are_recorded_with_the_senders_claimed_intent(
    tmp_path, default_params, network_params
):
    view = fx.honest_view(tmp_path, default_params, network_params)
    assert len(view.hints) == 1
    assert view.hints[0].sender == "thief"
    assert view.hints[0].claimed_intent == "lie"
    assert view.hints[0].text == fx.INCOMING_HINT["text"]


def test_hint_history_is_append_only_and_deduplicated(
    tmp_path, default_params, network_params
):
    """`ctx.incoming_hints` holds the LAST hint per sender and is never
    cleared, so a refresh loop re-reads the same one every tick."""
    ctx = fx.honest_context(tmp_path, default_params, network_params)
    history = HintHistory()
    for _ in range(3):
        build_local_view(ctx, history)
    assert len(history.entries) == 1
    ctx.incoming_hints = {"thief": {"text": "second", "intent": "truth", "turn": 3}}
    view = build_local_view(ctx, history)
    assert [h.text for h in view.hints] == [fx.INCOMING_HINT["text"], "second"]


def test_two_histories_in_one_interpreter_share_nothing(
    tmp_path, default_params, network_params
):
    """NET-02 / rule 2: the accumulator is an instance the caller owns."""
    ctx = fx.honest_context(tmp_path, default_params, network_params)
    first, second = HintHistory(), HintHistory()
    build_local_view(ctx, first)
    assert first.entries and second.entries == []


def test_recorded_outgoing_hints_join_the_same_log():
    history = HintHistory()
    history.record_outgoing(turn=5, text="I am heading south", intent="truth")
    assert [(h.sender, h.claimed_intent) for h in history.entries] == [("self", "truth")]


def test_hostile_hint_payloads_never_raise_and_never_fabricate(
    tmp_path, default_params, network_params
):
    """Total over peer data: nothing here may raise, and a field we cannot
    trust is dropped rather than coerced into something plausible."""
    assert len(_HOSTILE_PAYLOADS) == 6
    ctx = fx.honest_context(tmp_path, default_params, network_params)
    for payload in _HOSTILE_PAYLOADS:
        ctx.incoming_hints = {"thief": payload}
        view = build_local_view(ctx, HintHistory())
        assert all(isinstance(hint.text, str) for hint in view.hints)
        assert all(hint.turn is None or isinstance(hint.turn, int) for hint in view.hints)
        assert all(
            hint.claimed_intent in (None, "truth", "lie") for hint in view.hints
        )
