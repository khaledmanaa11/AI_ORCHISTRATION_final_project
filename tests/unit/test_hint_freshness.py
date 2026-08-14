"""05-06 G4: the receive-side lookback window and the freshness guard.

Split from `test_turn_hint_buffer.py` at the 150-code-line gate (Segal
Table 5) -- that file owns "an inbound hint is durable wire evidence",
this one owns "which inbound hint wins, and which is too late". Shared
helpers live in `_hint_fixtures.py`, one copy (QUAL-02).

Both behaviours here exist because of the same 2026-08-13 finding: with
one turn of lookback admitted, two hints from the same sender can now
both pass the window, so "last write wins" is no longer safe -- and the
stamp the guard reads is peer-supplied data on a path that validates
nothing beyond `isinstance(payload, dict)`.
"""

from __future__ import annotations

from pursuit.network import turn_hint_buffer
from pursuit.network.hint_payload import HintKey
from tests.unit._fakes_agent import make_ctx
from tests.unit._hint_fixtures import at_turn, hint_payload, hint_records


def test_an_older_but_admissible_hint_never_clobbers_a_fresher_one(
    tmp_path, default_params, network_params
):
    """The freshness guard the lookback window makes necessary. With one
    turn of lookback, two hints from the SAME sender can both pass the
    drop guard, so an out-of-order older arrival could overwrite a
    fresher one and feed stale evidence to the belief update. Both
    buffers keep the fresher payload."""
    ctx = at_turn(make_ctx(tmp_path, default_params, network_params, label="hint-fresh"), 4)
    fresh, stale = hint_payload(4), hint_payload(3)

    turn_hint_buffer.record_hint(ctx, "thief", 4, fresh)
    turn_hint_buffer.record_hint(ctx, "thief", 3, stale)  # admissible, but older

    assert ctx.incoming_hints["thief"] == fresh, "a stale hint overwrote a fresher one"
    assert ctx.pending_hints["thief"] == fresh
    assert len(hint_records(ctx)) == 2, "both arrivals are still wire evidence"


def test_a_hostile_stamp_is_buffered_without_raising(tmp_path, default_params, network_params):
    """The case that would otherwise END THE GAME. The stored stamp is
    peer data: `validate_hint_payload` runs only inside `build_hint` on
    the SEND path, and `Envelope.from_dict` checks the payload as nothing
    but `isinstance(payload, dict)`. A bare `turn >= stored[...]` raises
    `TypeError` inside `record_hint`, which no call site catches
    (`await_opponent_turn` catches only `HintProtocolError`), so it
    escapes `run_turn_loop` -- the forfeit-caused-by-a-hint failure
    04-12's deviation exists to prevent.

    Every shape below is "no usable stamp -> replace", bool included
    (mirroring `envelope._require_non_bool_int`)."""
    hostile = (
        {"text": "a string stamp", HintKey.TURN.value: "3"},
        {"text": "a None stamp", HintKey.TURN.value: None},
        {"text": "a bool stamp", HintKey.TURN.value: True},
        {"text": "a float stamp", HintKey.TURN.value: 3.0},
        {"text": "a list stamp", HintKey.TURN.value: [3]},
        {"text": "a dict stamp", HintKey.TURN.value: {"turn": 3}},
        {"text": "no stamp at all"},
    )
    for index, payload in enumerate(hostile):
        ctx = at_turn(
            make_ctx(tmp_path, default_params, network_params, label=f"hostile-{index}"), 2
        )
        turn_hint_buffer.record_hint(ctx, "thief", 2, payload)  # must not raise
        turn_hint_buffer.record_hint(ctx, "thief", 2, dict(payload, text="replacement"))

        assert ctx.incoming_hints["thief"]["text"] == "replacement", (
            f"an unusable stamp must mean 'replace', not 'keep': {payload}"
        )
        assert ctx.pending_hints["thief"]["text"] == "replacement"
