"""05-14 G8, the other half: what the single-decode rule must NOT refuse,
and what refuses a repeat once the marker is gone.

Split from `test_hint_replay.py` at the 150-code-line gate (Segal Table 5)
-- that file owns "a re-send is decoded once, on both roles' timings",
this one owns the rule's boundaries. The spy and the decode driver
both files use live in `_hint_decode_fixtures.py`, one copy (QUAL-02).

WHY THESE EXIST AT ALL. "Refuse everything after a decode" would pass
every case in the sibling file while silencing the channel, and
"re-narrow the window" -- the tempting wrong fix, since the pre-05-06
guard dropped the duplicate as a side effect -- would pass by dropping
the hint before it was ever decoded. Both are refuted here: a genuinely
newer hint still reaches the decoder, and the boundary hint one turn
behind is still admitted (`test_hint_freshness.py` pins that edge
unedited; this file pins its consequence at the decode).

THE MARKER AND THE WINDOW DOVETAIL rather than overlap, which is the
claim that lets the window keep 05-06's width: inside one joint turn the
marker refuses the repeat, and across the `maybe_resolve` that clears the
marker our own turn counter has advanced past the stamp, so the one-turn
window refuses it instead. The last case below is that hand-off, asserted
rather than argued.
"""

from __future__ import annotations

from pursuit.network import turn_hint_buffer
from tests.unit._hint_decode_fixtures import (
    SENDER,
    TEXT,
    decode_once,
    install_spy,
    language_ctx,
    resolve_turn,
)
from tests.unit._hint_fixtures import hint_payload, hint_records

_NEWER_TEXT = "a claim about a turn that had not happened yet"


async def test_a_genuinely_newer_hint_after_a_decode_is_still_decoded(
    monkeypatch, tmp_path, default_params, network_params
):
    """The discrimination the single-decode rule owes. A marker that
    refused everything after a pop would satisfy every replay case and
    still leave the channel dead from the second hint onward, which is
    the 0-of-5 shape 05-06 exists to have fixed. Only a STRICTLY OLDER-
    or-equal stamp is a repeat."""
    spy = install_spy(monkeypatch)
    ctx = language_ctx(tmp_path, default_params, network_params, "replay-newer", 4)
    turn_hint_buffer.record_hint(ctx, SENDER, 3, hint_payload(3))
    first = await decode_once(ctx)

    turn_hint_buffer.record_hint(ctx, SENDER, 4, dict(hint_payload(4), text=_NEWER_TEXT))
    second = await decode_once(ctx)

    assert first["outcome"] == second["outcome"] == "no_evidence"
    assert spy.decoded == [TEXT, _NEWER_TEXT], "a fresh hint was refused as a replay"
    assert len(spy.observed) == 2


async def test_a_re_send_carrying_no_usable_stamp_is_refused(
    monkeypatch, tmp_path, default_params, network_params
):
    """The peer-data half. The stamp is attacker-controlled and the
    inbound path validates a payload as nothing more than a dict, so a
    re-send can simply arrive without one. It cannot PROVE it is newer,
    so it does not re-enter -- and, like every other shape on this path,
    it must not raise (`await_opponent_turn` catches only
    `HintProtocolError`; anything else ends the game)."""
    spy = install_spy(monkeypatch)
    ctx = language_ctx(tmp_path, default_params, network_params, "replay-unstamped", 4)
    unstamped = {"text": TEXT}
    turn_hint_buffer.record_hint(ctx, SENDER, 3, unstamped)
    first = await decode_once(ctx)

    turn_hint_buffer.record_hint(ctx, SENDER, 3, dict(unstamped))  # must not raise
    second = await decode_once(ctx)

    assert first["outcome"] == "no_evidence"
    assert second["outcome"] == "no_hint"
    assert spy.decoded == [TEXT]


async def test_the_window_refuses_the_repeat_once_the_marker_is_cleared(
    monkeypatch, tmp_path, default_params, network_params
):
    """The dovetail. `maybe_resolve` clears `pending_hints`, so the marker
    does not outlive the turn -- and it does not need to: by then
    `ctx.state.turn` has advanced past the repeat's stamp and the
    unchanged one-turn window drops it. Both guards stay after the log, so
    the refused arrival is still on the wire record (rule 20)."""
    spy = install_spy(monkeypatch)
    ctx = language_ctx(tmp_path, default_params, network_params, "replay-dovetail", 4)
    turn_hint_buffer.record_hint(ctx, SENDER, 3, hint_payload(3))
    await decode_once(ctx)
    resolve_turn(ctx, 5)

    turn_hint_buffer.record_hint(ctx, SENDER, 3, hint_payload(3))
    assert ctx.incoming_hints == {}, "a repeat re-entered the buffer after the marker cleared"
    assert (await decode_once(ctx))["outcome"] == "no_hint"
    assert spy.decoded == [TEXT]
    assert len(hint_records(ctx)) == 2
