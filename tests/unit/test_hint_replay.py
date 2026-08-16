"""05-14 G8: one inbound hint is decoded AT MOST ONCE.

Asserted at the DECODE boundary, not at the buffer, because the defect is
not "a dict got overwritten" -- it is the same evidence driving
`observe_reliability` and the belief update twice. A double-counted hint
corrupts the posterior, which is the one thing the strategy layer is
entitled to trust (rule 20, LANG-01/03). So these cases count the two side
effects a repeat duplicates and read `decode_turn_hint`'s own outcome
word, whose two values say exactly the right things apart:

  * `no_evidence` -- a text ARRIVED and was decoded (whatever a keyless
    decode then concluded);
  * `no_hint` -- nothing was in the buffer at all.

BOTH ROLES' TIMINGS ARE COVERED SEPARATELY, and that is the point of this
file rather than an excess of care. They differ, and the 2026-08-16
attempt-4 evidence is what says so: the responder's six inbound records
sit at `record_turn == envelope_turn + 1` (the hint arrives AFTER its
receiver has resolved), while the initiator's five sit at delta 0 (it
arrives DURING the turn, and `maybe_resolve` clears `pending_hints` before
`take_my_turn` decodes it a turn later). A consumed marker written at
ARRIVAL survives to the responder's decode and is destroyed before the
initiator's -- measured, and it left the initiator decoding a re-send
twice. `turn_hint_store.consume_hint` writes it at CONSUMPTION instead.

The window WIDTH is untouched here and is pinned, unedited, by
`test_hint_freshness.py`'s two boundary siblings -- a re-narrowed window
would make every case below read `no_hint`, i.e. zero decodes rather than
one, so these tests reject that wrong fix too.
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


async def test_a_re_sent_hint_is_decoded_once_on_the_responder_timing(
    monkeypatch, tmp_path, default_params, network_params
):
    """The measured responder shape: the hint for turn 3 arrives once its
    receiver has already resolved to turn 4 (attempt-4, 6 of 6 records).
    The re-send after the decode must not reach the belief layer again."""
    spy = install_spy(monkeypatch)
    ctx = language_ctx(tmp_path, default_params, network_params, "replay-responder", 4)
    turn_hint_buffer.record_hint(ctx, SENDER, 3, hint_payload(3))

    first = await decode_once(ctx)
    turn_hint_buffer.record_hint(ctx, SENDER, 3, hint_payload(3))  # the peer re-sends
    second = await decode_once(ctx)

    assert first["outcome"] == "no_evidence", "the first arrival must genuinely decode"
    assert second["outcome"] == "no_hint", "a re-sent hint was handed to the decoder again"
    assert spy.decoded == [TEXT]
    assert len(spy.observed) == 1, "the same evidence drove the reliability update twice"
    assert len(hint_records(ctx)) == 2, "a refused re-send is still wire evidence (rule 20)"


async def test_a_re_sent_hint_is_decoded_once_on_the_initiator_timing(
    monkeypatch, tmp_path, default_params, network_params
):
    """The measured initiator shape, and the one an arrival-time marker
    CANNOT see: the hint for turn 3 arrives during turn 3 (attempt-4, 5 of
    5 records at delta 0), the joint turn then resolves -- clearing
    `pending_hints` -- and only then does `take_my_turn` decode it. Probed
    against an arrival-time marker this decoded TWICE."""
    spy = install_spy(monkeypatch)
    ctx = language_ctx(tmp_path, default_params, network_params, "replay-initiator", 3)
    turn_hint_buffer.record_hint(ctx, SENDER, 3, hint_payload(3))
    resolve_turn(ctx, 4)

    first = await decode_once(ctx)
    turn_hint_buffer.record_hint(ctx, SENDER, 3, hint_payload(3))  # the peer re-sends
    second = await decode_once(ctx)

    assert first["outcome"] == "no_evidence"
    assert second["outcome"] == "no_hint", "the initiator decoded the same hint twice"
    assert spy.decoded == [TEXT]
    assert len(spy.observed) == 1
