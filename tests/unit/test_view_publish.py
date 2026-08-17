"""The snapshot publisher (07-06, D-76): it writes what a viewer may see, it
writes it once per resolved turn, and it cannot hurt the turn loop.

The containment test asserts on the CALLER'S OBSERVABLE BEHAVIOUR -- the
returned outcome and the resolved state -- against a control context that
differs only in whether the write raises. Asserting on a log message would
prove that the failure was reported, not that the game survived it.
"""

from __future__ import annotations

import dataclasses
import json

import pytest

from pursuit.network.turn_commit_ledger import ledger_path_for
from pursuit.network.turn_resolve import maybe_resolve
from pursuit.sdk import view_publish
from pursuit.sdk.actions import CopAction
from pursuit.sdk.view_builder import HintHistory
from pursuit.sdk.view_publish import publish_view, snapshot_path_for
from pursuit.sdk.view_snapshot import read_snapshot
from tests.unit import local_view_fixtures as fx
from tests.unit import local_view_scanner as scan

THIEF_STEP = (5, 4)


class _Ticking:
    """A watchdog exposing the reading `Watchdog.idle_seconds` exposes."""

    idle_seconds = 2.5


class _Boolish:
    """A watchdog whose reading is a `bool` -- `True` would render as 1.00 s."""

    idle_seconds = True


def _armed(tmp_path, default_params, network_params):
    ctx = fx.honest_context(tmp_path, default_params, network_params)
    ctx.pending_cop_action = CopAction(move=fx.OWN_CELL)
    ctx.pending_thief_move = THIEF_STEP
    return ctx


def test_a_snapshot_is_written_once_the_turn_resolves(tmp_path, default_params, network_params):
    ctx = _armed(tmp_path, default_params, network_params)
    path = snapshot_path_for(ctx.log_path)
    assert not path.exists(), "nothing is published before a turn resolves"
    maybe_resolve(ctx)
    assert read_snapshot(path) is not None


def test_an_unresolved_turn_publishes_nothing(tmp_path, default_params, network_params):
    ctx = fx.honest_context(tmp_path, default_params, network_params)
    ctx.pending_thief_move = THIEF_STEP
    assert maybe_resolve(ctx) is None
    assert not snapshot_path_for(ctx.log_path).exists()


def test_the_snapshot_path_follows_the_ledger_sibling_convention(tmp_path):
    log_path = tmp_path / "logs" / "police" / "abc123.jsonl"
    assert snapshot_path_for(log_path).parent == ledger_path_for(log_path).parent
    assert snapshot_path_for(log_path).stem.startswith(log_path.stem)
    assert snapshot_path_for(log_path).name == "abc123.view.json"


def test_a_failing_write_leaves_the_turn_loop_untouched(
    tmp_path, default_params, network_params, monkeypatch
):
    """RULE 22 / 06-05 tie-in: since 06-05 a non-zero exit code MEANS an audit
    mismatch, so an exception out of a cosmetic write forges a technical
    loss. The control differs ONLY in the injected writer."""
    control = _armed(tmp_path / "control", default_params, network_params)
    expected_outcome = maybe_resolve(control)

    calls = []

    def _explode(*args, **kwargs):
        calls.append(args)
        raise OSError("the disk is full")

    monkeypatch.setattr(view_publish, "durable_write_json", _explode)
    ctx = _armed(tmp_path / "broken", default_params, network_params)
    log_before = ctx.log_path.read_bytes() if ctx.log_path.exists() else b""

    assert maybe_resolve(ctx) == expected_outcome
    assert ctx.state == control.state
    assert calls, "the failing writer was never reached -- this proves nothing"
    assert not snapshot_path_for(ctx.log_path).exists()
    assert (ctx.log_path.read_bytes() if ctx.log_path.exists() else b"") == log_before


def test_a_failing_view_build_is_also_swallowed(tmp_path, default_params, network_params, monkeypatch):
    ctx = fx.honest_context(tmp_path, default_params, network_params)
    monkeypatch.setattr(
        view_publish, "build_local_view", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom"))
    )
    publish_view(ctx, HintHistory())
    assert not snapshot_path_for(ctx.log_path).exists()


def test_the_published_file_carries_no_coordinate_of_the_true_cell(
    tmp_path, default_params, network_params
):
    """Rules 8-9 over the BYTES that leave the agent process, with the
    opponent at a cell distinct from own position, from every declared
    barrier and from the published belief argmax."""
    ctx = fx.honest_context(tmp_path, default_params, network_params)
    publish_view(ctx, HintHistory())
    payload = json.loads(snapshot_path_for(ctx.log_path).read_text(encoding="utf-8"))

    assert ctx.state.thief == fx.OPPONENT_CELL, "the context must actually hold the truth"
    assert payload["own_cell"] != list(fx.OPPONENT_CELL)
    assert payload["belief"]["argmax"] != list(fx.OPPONENT_CELL)
    assert scan.coordinate_hits(payload, fx.OPPONENT_CELL, payload["board_size"]) == []


def test_the_same_scan_reports_a_leaky_published_file(tmp_path, default_params, network_params):
    """THE COUNTER-CONTROL. Without it the assertion above is satisfied by a
    scanner that cannot see anything."""
    ctx = fx.honest_context(tmp_path, default_params, network_params)
    publish_view(ctx, HintHistory())
    payload = json.loads(snapshot_path_for(ctx.log_path).read_text(encoding="utf-8"))
    variants = scan.leak_variants(payload, fx.OPPONENT_CELL, payload["board_size"])
    assert len(variants) == 5, "a thinned variant set would prove less"
    for name, leaky in variants.items():
        assert scan.coordinate_hits(leaky, fx.OPPONENT_CELL, payload["board_size"]), name


#: The three watchdog shapes the publisher must survive. NAMED and floored
#: below: a thinned table skips silently rather than failing.
_IDLE_CASES = [(_Ticking(), 2.5), (_Boolish(), None), (object(), None)]


def test_the_idle_case_table_is_not_thinned():
    assert len(_IDLE_CASES) == 3, "a live reading, a bool, and no reading at all"


@pytest.mark.parametrize(("watchdog", "expected"), _IDLE_CASES)
def test_the_idle_reading_is_carried_or_honestly_absent(watchdog, expected):
    assert view_publish.idle_reading(watchdog) == expected


def test_the_hint_log_survives_across_turns(tmp_path, default_params, network_params):
    """`ctx.incoming_hints` holds only the LAST hint per sender, so the log
    has to accumulate on the context that outlives the turn."""
    ctx = _armed(tmp_path, default_params, network_params)
    maybe_resolve(ctx)
    ctx.view_history.record_outgoing(turn=5, text="our own claim", intent="truth")
    ctx.incoming_hints = {"thief": {"text": "a second claim", "intent": "truth", "turn": 5}}
    publish_view(ctx, ctx.view_history)
    view = read_snapshot(snapshot_path_for(ctx.log_path))
    assert [hint.text for hint in view.hints] == [
        fx.INCOMING_HINT["text"], "our own claim", "a second claim",
    ]
    assert [hint.sender for hint in view.hints] == ["thief", "self", "thief"]


def test_two_contexts_do_not_share_a_hint_log(tmp_path, default_params, network_params):
    """NET-02 / CLAUDE.md rule 2: no shared runtime state between the two
    agents, and `default_factory` is what makes that true per instance."""
    first = fx.honest_context(tmp_path / "a", default_params, network_params)
    second = fx.honest_context(tmp_path / "b", default_params, network_params)
    first.view_history.record_outgoing(turn=1, text="mine", intent="truth")
    assert first.view_history.entries and second.view_history.entries == []
    assert first.view_history is not second.view_history


def test_the_payload_is_exactly_the_closed_field_set(tmp_path, default_params, network_params):
    view = fx.honest_view(tmp_path, default_params, network_params)
    assert set(view_publish.snapshot_payload(view)) == {
        f.name for f in dataclasses.fields(view)
    }
