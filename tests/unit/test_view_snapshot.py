"""The read half of D-76: the GUI process reconstructs the SAME frozen
dataclasses, and never dies on a file the writer is halfway through.

The round trip is asserted on EQUALITY of the whole `LocalView`, not field by
field: a field added to the closed set and forgotten in the decoder would
otherwise pass silently.
"""

from __future__ import annotations

import json

import pytest

from pursuit.sdk.local_view import LocalView
from pursuit.sdk.view_builder import build_local_view
from pursuit.sdk.view_publish import publish_view, snapshot_path_for, snapshot_payload
from pursuit.sdk.view_snapshot import decode_view, read_snapshot
from tests.unit import local_view_fixtures as fx

_TRUNCATED = '{"role": "police", "board_'


def test_a_published_view_round_trips_unchanged(tmp_path, default_params, network_params):
    ctx = fx.honest_context(tmp_path, default_params, network_params)
    publish_view(ctx, ctx.view_history)
    restored = read_snapshot(snapshot_path_for(ctx.log_path))
    assert isinstance(restored, LocalView)
    # `HintHistory.observe` is idempotent per (sender, hint), so rebuilding
    # over the same accumulator reproduces the published view exactly.
    assert restored == build_local_view(ctx, ctx.view_history, idle_seconds=None)


def test_a_belief_free_view_round_trips_as_none(tmp_path, default_params, network_params):
    """The honest empty panel, and a live case since 07-11: the publication
    floor can refuse a map mid-game, not only a disabled belief layer."""
    view = fx.honest_view(tmp_path, default_params, network_params, with_belief=False)
    assert view.belief is None
    restored = decode_view(snapshot_payload(view))
    assert restored == view and restored.belief is None


def test_a_missing_snapshot_reads_as_none(tmp_path):
    assert read_snapshot(tmp_path / "never-written.view.json") is None


def test_a_half_written_snapshot_reads_as_none(tmp_path):
    """The writer runs on the agent's loop, the reader on its own timer, so
    the reader WILL arrive mid-rotation."""
    path = tmp_path / "partial.view.json"
    path.write_text(_TRUNCATED, encoding="utf-8")
    assert read_snapshot(path) is None


def test_a_snapshot_falls_back_to_its_previous_generation(tmp_path, default_params, network_params):
    """`durable_write_json` rotates the old target to `.prev` before it
    replaces, so a crash in that window still leaves a readable frame."""
    ctx = fx.honest_context(tmp_path, default_params, network_params)
    publish_view(ctx, ctx.view_history)
    publish_view(ctx, ctx.view_history)
    path = snapshot_path_for(ctx.log_path)
    assert path.with_name(f"{path.stem}.prev{path.suffix}").exists()
    path.unlink()
    assert read_snapshot(path) is not None


@pytest.mark.parametrize(
    "payload",
    [
        None,
        [],
        {},
        {"role": "police"},
        {"board_size": "seven"},
    ],
)
def test_a_payload_that_is_not_a_view_decodes_to_none(payload):
    assert decode_view(payload) is None


def test_a_field_of_the_wrong_type_decodes_to_none(tmp_path, default_params, network_params):
    view = fx.honest_view(tmp_path, default_params, network_params)
    payload = snapshot_payload(view)
    assert decode_view(payload) == view, "the control must decode before it is broken"
    payload["belief"]["rows"] = "not a grid"
    assert decode_view(payload) is None


def test_the_decoder_reads_the_json_encoding_not_only_the_python_one(
    tmp_path, default_params, network_params
):
    """JSON turns every tuple into a LIST and every frozen grid into nested
    lists; the decoder must restore the tuple forms the view is typed on."""
    view = fx.honest_view(tmp_path, default_params, network_params)
    restored = decode_view(json.loads(json.dumps(snapshot_payload(view))))
    assert restored == view
    assert isinstance(restored.own_cell, tuple)
    assert isinstance(restored.belief.rows[0], tuple)
