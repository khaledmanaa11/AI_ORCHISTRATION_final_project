"""06-05 Gap 1: the audit's evidence dicts must be keyed on OUR OWN turn
stamp, never the peer's declared `envelope.turn`.

These are the adversarial siblings of `test_audit_coverage.py`. That file
builds both observed dicts from one honest fixture, so its keys always
agree and it cannot see this class of bug -- which is exactly why the bug
survived 1227 green tests and a PASS gate. Every test here deliberately
makes the RECORD's turn and the nested ENVELOPE's turn DISAGREE, then
asserts the audit follows the record (local truth), not the envelope
(the peer's claim).

Both exploits below were reproduced against the pre-fix code with paired
controls before the fix was written; see 06-UAT.md Gap 1.
"""

from __future__ import annotations

import json

from pursuit.network.agent_audit_exchange import observed
from pursuit.security import commit_pack
from pursuit.security.audit import all_matched, audit_peer_records

STATE = {"game_id": "g", "turn": 1, "role": "police",
         "position": {"row": 2, "col": 3}, "barriers_remaining": 0}
ACTION_A = {"move": {"kind": "move", "direction": "north"}, "barrier": None}
ACTION_B = {"move": {"kind": "move", "direction": "south"}, "barrier": None}


class _Ctx:
    """Minimal stand-in: `observed` touches only ctx.log_path."""

    def __init__(self, log_path):
        self.log_path = log_path


def _record(*, record_turn: int, envelope_turn: int, msg_type: str, payload: dict) -> dict:
    """One message_received JSONL record whose own turn and whose nested
    envelope turn are set INDEPENDENTLY -- the whole point of this file."""
    return {
        "event": "message_received", "turn": record_turn, "game_uid": "g", "sender": "thief",
        "envelope": {"type": msg_type, "turn": envelope_turn, "sender": "police", "payload": payload},
    }


def _write(tmp_path, records):
    log = tmp_path / "game.jsonl"
    log.write_text("".join(json.dumps(r) + "\n" for r in records), encoding="utf-8")
    return _Ctx(log)


def _honest_turn(turn: int, action: dict) -> tuple[str, dict]:
    h, nonce = commit_pack.commit(dict(STATE, turn=turn), action, "truth")
    payload = commit_pack.build_commit_payload(
        state=dict(STATE, turn=turn), move=action, intent="truth", nonce=nonce)
    return h, {"turn": turn, "h_commit": h, "payload": payload}


def test_observed_keys_on_our_own_turn_not_the_peers_claim(tmp_path):
    """The peer stamps its envelopes turn=0 and turn=99; we logged them
    under our own turn 1. Both dicts must land on 1."""
    ctx = _write(tmp_path, [
        _record(record_turn=1, envelope_turn=0, msg_type="commit", payload={"h_commit": "abc"}),
        _record(record_turn=1, envelope_turn=99, msg_type="reveal", payload=ACTION_A),
    ])
    commits, reveals = observed(ctx, direction="message_received")
    assert list(commits) == [1], "commit must be keyed on our turn, not the peer's 0"
    assert list(reveals) == [1], "reveal must be keyed on our turn, not the peer's 99"


def test_empty_final_reveal_still_mismatches_when_the_peer_skews_its_turn_stamps(tmp_path):
    """Exploit path A: skewing COMMIT/REVEAL turn stamps used to empty the
    rule-36 coverage intersection, so `{"records": []}` passed vacuously."""
    records = []
    for turn in (1, 2, 3):
        records.append(_record(
            record_turn=turn, envelope_turn=0, msg_type="commit", payload={"h_commit": f"h{turn}"}))
        records.append(_record(
            record_turn=turn, envelope_turn=99, msg_type="reveal", payload=ACTION_A))
    ctx = _write(tmp_path, records)

    commits, reveals = observed(ctx, direction="message_received")
    audit = audit_peer_records(commits, reveals, [])

    assert not all_matched(audit), "an empty final reveal must never pass"
    assert len(audit) == 3, "every fully-exchanged turn must be named"
    assert all("absent from final reveal" in r.detail for r in audit)


def test_d67_forgery_still_caught_when_the_peer_skews_its_reveal_turn(tmp_path):
    """Exploit path B: commit to A, play B, and stamp the REVEAL envelope
    with a bogus turn so the entry fell into the trailing-commit exemption
    instead of the D-67 revealed-vs-played check."""
    h1, record_for_a = _honest_turn(1, ACTION_A)
    ctx = _write(tmp_path, [
        _record(record_turn=1, envelope_turn=1, msg_type="commit", payload={"h_commit": h1}),
        _record(record_turn=1, envelope_turn=1001, msg_type="reveal", payload=ACTION_B),
    ])

    commits, reveals = observed(ctx, direction="message_received")
    audit = audit_peer_records(commits, reveals, [record_for_a])

    assert not all_matched(audit), "a played-vs-revealed divergence must be caught"
    assert any("does not match what was actually played" in r.detail for r in audit)


def test_one_turn_stamp_for_the_whole_game_cannot_collapse_the_audit(tmp_path):
    """The cheapest variant: stamp EVERY envelope turn=0 so both dicts
    collapse to one key and a single valid record covers an N-turn game."""
    records = []
    for turn in (1, 2, 3):
        h, _ = _honest_turn(turn, ACTION_A)
        records.append(_record(
            record_turn=turn, envelope_turn=0, msg_type="commit", payload={"h_commit": h}))
        records.append(_record(
            record_turn=turn, envelope_turn=0, msg_type="reveal", payload=ACTION_A))
    ctx = _write(tmp_path, records)
    _, record_for_turn_1 = _honest_turn(1, ACTION_A)

    commits, reveals = observed(ctx, direction="message_received")
    audit = audit_peer_records(commits, reveals, [record_for_turn_1])

    assert len(commits) == 3, "three distinct turns must survive as three keys"
    assert not all_matched(audit), "turns 2 and 3 are unaccounted for"


def test_an_honest_peer_is_still_matched(tmp_path):
    """The fairness control: agreeing stamps, a complete final reveal, and
    a genuinely trailing commit must all still pass. The fix must not have
    bought its security by accusing honest peers (rules 16/22)."""
    h1, record_1 = _honest_turn(1, ACTION_A)
    _, record_2 = _honest_turn(2, ACTION_A)
    h2 = record_2["h_commit"]
    ctx = _write(tmp_path, [
        _record(record_turn=1, envelope_turn=1, msg_type="commit", payload={"h_commit": h1}),
        _record(record_turn=1, envelope_turn=1, msg_type="reveal", payload=ACTION_A),
        # turn 2 committed but never revealed -- a legitimately trailing turn
        _record(record_turn=2, envelope_turn=2, msg_type="commit", payload={"h_commit": h2}),
    ])

    commits, reveals = observed(ctx, direction="message_received")
    audit = audit_peer_records(commits, reveals, [record_1, record_2])

    assert all_matched(audit), f"honest peer wrongly accused: {[r.detail for r in audit]}"
    assert any("trailing commit" in r.detail for r in audit)
