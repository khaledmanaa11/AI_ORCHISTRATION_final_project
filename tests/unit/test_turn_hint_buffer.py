"""05-06 G3: an inbound HINT is durable, replayable wire evidence
(D-11/D-14, rule 20) -- and is invisible to the D-67 audit.

The 2026-08-13 remote round is the fixture these tests exist for: machine
A's log carried 5 `message_sent`+`hint` records and ZERO
`message_received`+`hint`, while its own `language_turn` records quoted
the thief's hint texts verbatim with `outcome: evidence`. The hints
arrived and moved the belief; nothing on disk said so.

Buffering semantics themselves (the lookback window, the freshness guard)
are exercised in `test_turn_buffer.py`, against the re-exported
`turn_buffer.record_hint` -- the name every production caller uses.
"""

from __future__ import annotations

import dataclasses
import json

from pursuit.network import turn_hint_buffer
from pursuit.network.agent_audit_exchange import observed
from pursuit.network.hint_payload import HintKey, Intent
from tests.unit._fakes_agent import make_ctx

_PEER_CLAIM = 99
"""The turn the peer stamps on its own envelope -- deliberately nothing
this side would ever produce, so a record keyed on it is unmistakable."""


def _hint_payload(turn: int) -> dict:
    return {
        HintKey.TEXT.value: "heading uptown",
        HintKey.INTENT.value: Intent.TRUTH.value,
        HintKey.TURN.value: turn,
    }


def _events(ctx) -> list[dict]:
    if not ctx.log_path.exists():
        return []
    return [json.loads(line) for line in ctx.log_path.read_text(encoding="utf-8").splitlines()]


def _hint_records(ctx) -> list[dict]:
    return [
        e for e in _events(ctx)
        if e["event"] == "message_received" and e["envelope"]["type"] == "hint"
    ]


def _at_turn(ctx, turn: int):
    ctx.state = dataclasses.replace(ctx.state, turn=turn)
    return ctx


def test_an_inbound_hint_lands_on_the_wire_log(tmp_path, default_params, network_params):
    """G3's primary: the receipt exists at all. Pre-fix this list was
    empty for every hint of every game."""
    ctx = _at_turn(make_ctx(tmp_path, default_params, network_params, label="hint-log"), 3)
    turn_hint_buffer.record_hint(ctx, "thief", 3, _hint_payload(3))

    records = _hint_records(ctx)
    assert len(records) == 1, "an inbound hint left no durable record"
    assert records[0]["envelope"]["payload"] == _hint_payload(3)


def test_the_record_turn_is_ours_and_the_envelope_keeps_the_peers_claim(
    tmp_path, default_params, network_params
):
    """The 06-05 Gap-1 split, applied to hints: the record's own top-level
    turn is LOCAL truth (`ctx.state.turn`), the nested envelope stores the
    peer's declared turn verbatim as evidence. Mirrors
    `test_audit_turn_binding.py`'s construction -- record turn and
    envelope turn set independently, then asserted apart."""
    ctx = _at_turn(make_ctx(tmp_path, default_params, network_params, label="hint-bind"), 3)
    turn_hint_buffer.record_hint(ctx, "thief", _PEER_CLAIM, _hint_payload(_PEER_CLAIM))

    record = _hint_records(ctx)[0]
    assert record["turn"] == 3, "the record must be keyed on OUR turn, never the peer's claim"
    assert record["envelope"]["turn"] == _PEER_CLAIM, "the peer's claim must survive as evidence"
    assert record["sender"] == ctx.role
    assert record["envelope"]["sender"] == "thief"


def test_receiving_a_hint_reports_no_state_change(tmp_path, default_params, network_params):
    """Receiving a hint moves the state machine nowhere, and the record
    says so explicitly rather than implying a transition that never
    happened."""
    ctx = _at_turn(make_ctx(tmp_path, default_params, network_params, label="hint-state"), 1)
    before = ctx.machine.state
    turn_hint_buffer.record_hint(ctx, "thief", 1, _hint_payload(1))

    record = _hint_records(ctx)[0]
    assert record["state_from"] == record["state_to"] == before.value
    assert ctx.machine.state is before


def test_a_genuinely_late_hint_is_still_logged_though_still_dropped(
    tmp_path, default_params, network_params
):
    """Logging happens BEFORE the drop guard on purpose: a hint we discard
    is still a thing that crossed the wire, and rule 20's replay evidence
    must show it. `turn - 2` is outside the lookback window, so this is
    the genuinely-too-late case, not the one-turn stagger."""
    ctx = _at_turn(make_ctx(tmp_path, default_params, network_params, label="hint-late-log"), 5)
    turn_hint_buffer.record_hint(ctx, "thief", 3, _hint_payload(3))

    assert len(_hint_records(ctx)) == 1, "a dropped hint must still be on the record"
    assert ctx.pending_hints == {}
    assert ctx.incoming_hints == {}


def test_hint_records_are_inert_to_the_audit(tmp_path, default_params, network_params):
    """`agent_audit_exchange.observed` keys only `commit`/`reveal`
    envelope types, so adding a whole new received type must leave both
    dicts byte-identical. Asserted as a paired before/after over the SAME
    log, not by reading the implementation."""
    ctx = _at_turn(make_ctx(tmp_path, default_params, network_params, label="hint-audit"), 1)
    ctx.log_path.parent.mkdir(parents=True, exist_ok=True)
    ctx.log_path.write_text(
        json.dumps({
            "event": "message_received", "turn": 1, "game_uid": "g", "sender": "police",
            "envelope": {"type": "commit", "turn": 1, "sender": "thief",
                         "payload": {"h_commit": "abc"}},
        }) + "\n"
        + json.dumps({
            "event": "message_received", "turn": 1, "game_uid": "g", "sender": "police",
            "envelope": {"type": "reveal", "turn": 1, "sender": "thief",
                         "payload": {"move": {"kind": "move", "direction": "north"},
                                     "barrier": None}},
        }) + "\n",
        encoding="utf-8",
    )
    before = observed(ctx, direction="message_received")

    turn_hint_buffer.record_hint(ctx, "thief", 1, _hint_payload(1))
    turn_hint_buffer.record_hint(ctx, "thief", 0, _hint_payload(0))

    assert _hint_records(ctx), "the probe is vacuous unless hint records actually landed"
    assert observed(ctx, direction="message_received") == before
