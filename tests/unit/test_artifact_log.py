"""Task 1: the join is keyed on LOCAL turn truth and survives a crashed game."""

from __future__ import annotations

import json

import pytest

from pursuit.network.envelope import MessageType
from pursuit.network.event_log import EventType
from pursuit.services.reporting.log_join import (
    GAME_OVER_EVENT,
    LANGUAGE_TURN_EVENT,
    CorruptLogError,
    join_game,
    local_turn,
    peer_claimed_turn,
    read_tolerating_partial_tail,
)
from pursuit.services.reporting.log_turn_fields import TurnField, WireSide
from tests.unit.artifact_log_fixtures import PEER, ROLE
from tests.unit.artifact_log_games import (
    DISJOINT_TURN,
    GAME_TURNS,
    PEER_COMMIT_CLAIM,
    PEER_REVEAL_CLAIM,
    write_game,
)

PARAMETERS_FIELDS = (
    TurnField.COMMITMENT, TurnField.REVEALED_MOVE, TurnField.INTENT,
    TurnField.HINT, TurnField.VERDICT, TurnField.NONCE, TurnField.HASH,
)


def _received(path):
    """Every `message_received` record, straight off the log."""
    records, _ = read_tolerating_partial_tail(path)
    return [r for r in records if r.get("event") == EventType.MESSAGE_RECEIVED.value]


def _complete_peer_pairs(path, key) -> int:
    """Turns whose PEER commit AND peer reveal land in the same bucket under
    *key*. The control for the join: run it with `local_turn` and again with
    `peer_claimed_turn` and the difference is what the wrong key costs."""
    buckets: dict = {}
    for record in _received(path):
        kind = record["envelope"]["type"]
        buckets.setdefault(key(record), set()).add(kind)
    wanted = {MessageType.COMMIT.value, MessageType.REVEAL.value}
    return sum(1 for kinds in buckets.values() if wanted <= kinds)


def test_a_partial_last_line_is_dropped_and_reported(tmp_path):
    log_path = write_game(tmp_path, log_tail='{"event": "message_se')
    joined = join_game(log_path)
    assert joined.truncated_tail == {"log": True, "ledger": False}
    assert [t[TurnField.TURN] for t in joined.turns] == [*GAME_TURNS, 4]


def test_a_partial_ledger_tail_is_reported_on_its_own_side(tmp_path):
    log_path = write_game(tmp_path, ledger_tail='{"turn": 9, "h_com')
    joined = join_game(log_path)
    assert joined.truncated_tail == {"log": False, "ledger": True}


def test_mid_file_corruption_raises_rather_than_dropping(tmp_path):
    log_path = write_game(tmp_path, log_corruption='{"event": "message_se')
    with pytest.raises(CorruptLogError) as excinfo:
        join_game(log_path)
    # The exact class, not `ValueError`: `json.JSONDecodeError` is itself a
    # ValueError, so a looser assertion would pass on the tail case too.
    assert type(excinfo.value) is CorruptLogError
    assert not isinstance(excinfo.value, json.JSONDecodeError)


def test_a_missing_log_reads_empty_rather_than_raising(tmp_path):
    assert read_tolerating_partial_tail(tmp_path / "absent.jsonl") == ([], False)


def test_the_join_key_is_this_sides_number_and_the_peers_is_only_evidence(tmp_path):
    log_path = write_game(tmp_path, disjoint=True)
    disjoint = [r for r in _received(log_path) if local_turn(r) == DISJOINT_TURN]
    claims = sorted(peer_claimed_turn(r) for r in disjoint)
    assert claims == [DISJOINT_TURN, PEER_REVEAL_CLAIM, PEER_COMMIT_CLAIM]
    assert all(local_turn(r) == DISJOINT_TURN for r in disjoint)


def test_disjoint_peer_turns_still_pair_under_one_local_turn(tmp_path):
    log_path = write_game(tmp_path, disjoint=True)
    turn = next(t for t in join_game(log_path).turns if t[TurnField.TURN] == DISJOINT_TURN)
    assert turn[TurnField.COMMITMENT][WireSide.RECEIVED] is not None
    assert turn[TurnField.REVEALED_MOVE][WireSide.RECEIVED] is not None
    assert turn[TurnField.PEER_CLAIMED_TURNS] == {
        MessageType.COMMIT.value: PEER_COMMIT_CLAIM,
        MessageType.REVEAL.value: PEER_REVEAL_CLAIM,
        MessageType.HINT.value: DISJOINT_TURN,
    }


def test_rekeying_on_the_peers_claimed_turn_loses_a_counted_pair(tmp_path):
    log_path = write_game(tmp_path, disjoint=True)
    correct = _complete_peer_pairs(log_path, local_turn)
    wrong = _complete_peer_pairs(log_path, peer_claimed_turn)
    assert correct == len(GAME_TURNS)
    assert correct - wrong == 1, "the wrong key must lose the disjoint turn"


def test_the_control_loses_nothing_when_the_peer_stamps_honestly(tmp_path):
    log_path = write_game(tmp_path, disjoint=False)
    assert _complete_peer_pairs(log_path, local_turn) == len(GAME_TURNS)
    assert _complete_peer_pairs(log_path, peer_claimed_turn) == len(GAME_TURNS)


def test_the_two_bypass_event_names_are_still_absent_from_event_type(tmp_path):
    values = {member.value for member in EventType}
    assert LANGUAGE_TURN_EVENT not in values
    assert GAME_OVER_EVENT not in values


def test_the_game_over_and_language_records_reach_the_join(tmp_path):
    joined = join_game(write_game(tmp_path))
    assert joined.outcome == {"outcome": "capture", "turn": 4}
    assert joined.audit_verdict == {"matched": True, "turn": 4}
    assert joined.role == ROLE
    hints = [t[TurnField.HINT][WireSide.OUTGOING] for t in joined.turns]
    assert [h for h in hints if h] == [
        {"intent": "lie", "text": f"ours {turn}"} for turn in GAME_TURNS
    ]


@pytest.mark.parametrize("field", PARAMETERS_FIELDS)
def test_every_turn_carries_every_parameters_field(tmp_path, field):
    assert len(PARAMETERS_FIELDS) == 7, "docs/PARAMETERS.md:167 names seven"
    turns = join_game(write_game(tmp_path)).turns
    assert len(turns) > 0
    for turn in turns:
        assert field in turn


def test_a_boolean_turn_cannot_overwrite_turn_one(tmp_path):
    """`True == 1` and `hash(True) == hash(1)`, so a ledger line stamped
    `"turn": true` would land on turn 1's dict key and silently replace its
    nonce and hash. The `_is_turn` bool guard is what stops it."""
    log_path = write_game(tmp_path)
    ledger_path = log_path.parent / f"{log_path.stem}.ledger.jsonl"
    honest = join_game(log_path)
    with ledger_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"turn": True, "h_commit": "x" * 64, "payload": {}}) + "\n")
    poisoned = join_game(log_path)
    assert [t[TurnField.HASH] for t in poisoned.turns] == [
        t[TurnField.HASH] for t in honest.turns
    ]


def test_the_peers_hint_is_carried_verbatim_as_received(tmp_path):
    turns = join_game(write_game(tmp_path)).turns
    received = [t[TurnField.HINT][WireSide.RECEIVED] for t in turns[: len(GAME_TURNS)]]
    assert received == [
        {"intent": "truth", "text": f"theirs {turn}", "turn": turn} for turn in GAME_TURNS
    ]
    assert PEER != ROLE
