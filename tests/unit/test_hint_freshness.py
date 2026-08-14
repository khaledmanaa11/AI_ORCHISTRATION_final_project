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

`record_hint`'s four window/overwrite cases moved here from
`test_turn_buffer.py` when 05-06's re-specification took that file past
the 150-code-line gate. They keep calling it as `turn_buffer.record_hint`
-- the re-exported name every production call site uses -- while the
tests below reach the implementation module directly.

WHY THOSE CASES GAINED AN `incoming_hints` ASSERTION (05-06, stated once
here rather than copied into each docstring, and applying equally to
`test_turn_buffer.py`'s remaining `await_move`/`drain_trailing_hint`
cases): they asserted ONLY on `ctx.pending_hints`, which has zero
production READERS -- `grep -rn pending_hints src/` returns the field
declaration (`agent_context.py:94`), the resolve-time clear
(`turn_resolve.py:96`, a write) and `turn_hint_buffer`'s own write.
`decode_turn_hint` pops `ctx.incoming_hints`. A regression populating
only the dead buffer therefore passed the whole suite -- which is how
the responder's 0-of-5 decode rate survived 1251 green tests. The
original assertions are not wrong, only insufficient, so they are KEPT
and joined, never replaced.
"""

from __future__ import annotations

from pursuit.network import turn_buffer, turn_hint_buffer
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


def test_record_hint_buffers_by_sender(tmp_path, default_params, network_params):
    """Re-specified 05-06: `incoming_hints` joins the assertion -- see this module's
    docstring for why `pending_hints` alone could not fail."""
    ctx = make_ctx(tmp_path, default_params, network_params, label="rh")
    turn_buffer.record_hint(ctx, "thief", ctx.state.turn, {"text": "hi"})
    assert ctx.pending_hints == {"thief": {"text": "hi"}}
    assert ctx.incoming_hints == {"thief": {"text": "hi"}}


def test_record_hint_overwrites_a_second_hint_from_the_same_sender(
    tmp_path, default_params, network_params
):
    """04-12 (Rule 1 - bug fix): a second not-yet-consumed hint from the
    same sender is ordinary timing (each hint is an independent
    round-trip), never a protocol violation -- the freshest one wins,
    matching `ctx.incoming_hints`' own overwrite semantics, and neither
    call may raise.

    Re-specified 05-06 on two counts: `incoming_hints` joins the
    assertion (module docstring), and this fixture pins the case
    05-06's freshness guard must NOT change -- a payload carrying no
    usable turn stamp is still replaced outright, same turn or not."""
    ctx = make_ctx(tmp_path, default_params, network_params, label="rh-dup")
    turn_buffer.record_hint(ctx, "thief", ctx.state.turn, {"text": "first"})
    turn_buffer.record_hint(ctx, "thief", ctx.state.turn, {"text": "second"})  # must not raise
    assert ctx.pending_hints == {"thief": {"text": "second"}}
    assert ctx.incoming_hints == {"thief": {"text": "second"}}


def test_record_hint_silently_drops_a_hint_for_an_already_resolved_turn(
    tmp_path, default_params, network_params
):
    """04-12 (Rule 1 - bug fix): a late hint is ordinary network jitter
    (the move and the hint are independent round-trips), never a protocol
    violation -- it must never raise or end the game, and must never enter
    either buffer.

    RE-SPECIFIED 05-06 (G4), not loosened. The old fixture used
    `ctx.state.turn - 1`, which is what the responder hits on EVERY
    correctly stamped hint -- a hint for turn N is emitted at the tail of
    turn N and pulled off the queue once the receiver has resolved to
    N + 1. This test therefore certified the bug that made the thief
    decode 0 of 5 in every game. The drop rule still keeps real content,
    so the case moves to a GENUINELY too-late hint (two turns back,
    outside the lookback window) and gains the Task-1 assertion that a
    dropped hint is still durable wire evidence (rule 20). The window's
    other side is pinned by the sibling below."""
    ctx = at_turn(make_ctx(tmp_path, default_params, network_params, label="rh-late"), 5)
    turn_buffer.record_hint(ctx, "thief", 3, {"text": "late"})  # must not raise
    assert ctx.pending_hints == {}
    assert ctx.incoming_hints == {}
    assert len(hint_records(ctx)) == 1, "a dropped hint is still wire evidence"


def test_record_hint_keeps_a_hint_one_turn_old(tmp_path, default_params, network_params):
    """The other side of the same boundary (05-06 G4). One turn of
    lookback is the MINIMUM that makes the channel deliverable at all, so
    the turn immediately behind ours must land in BOTH buffers. Pinned as
    a sibling of the drop test so neither edge of the window can move
    without a red test."""
    ctx = at_turn(make_ctx(tmp_path, default_params, network_params, label="rh-lookback"), 5)
    turn_buffer.record_hint(ctx, "thief", 4, {"text": "one turn behind"})
    assert ctx.pending_hints == {"thief": {"text": "one turn behind"}}
    assert ctx.incoming_hints == {"thief": {"text": "one turn behind"}}
