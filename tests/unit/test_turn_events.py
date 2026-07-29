"""Tests for the pure D-11 record builders in pursuit.network.turn_events.

No I/O anywhere in this file -- every assertion is against a plain dict
returned by a builder function. `default_params`/`network_params` are not
needed here: none of these builders accept a game or network number.
"""

import json

from pursuit.constants import Outcome
from pursuit.network import turn_events
from pursuit.network.envelope import Envelope, MessageType
from pursuit.network.state_machine import State, TransitionSeverity

_GAME_UID = "g1"


def test_turn_record_carries_the_full_schema():
    """D-11: every stable field present, states serialised as strings, JSON-safe."""
    env = Envelope(type=MessageType.MOVE, turn=1, sender="police", payload={"x": 0, "y": 1})
    rec = turn_events.turn_record(
        game_uid=_GAME_UID, turn=1, event="message_sent", sender="police",
        state_from=State.MY_TURN, state_to=State.WAIT_OPPONENT, envelope=env.to_dict(),
    )
    for key in ("game_uid", "turn", "event", "sender", "state_from", "state_to",
                "envelope", "timestamp"):
        assert key in rec
    assert rec["state_from"] == State.MY_TURN.value
    assert rec["state_to"] == State.WAIT_OPPONENT.value
    assert isinstance(rec["state_from"], str)
    assert isinstance(rec["state_to"], str)
    json.dumps(rec)


def test_illegal_transition_record_names_the_severity():
    """NET-05: the record names both the severity and the human reason."""
    rec = turn_events.illegal_transition_record(
        game_uid=_GAME_UID, turn=2, sender="police",
        current=State.INIT, target=State.GAME_OVER,
        severity=TransitionSeverity.PROTOCOL_VIOLATION, reason="not in table",
    )
    assert rec["event"] == "illegal_transition"
    blob = json.dumps(rec)
    assert TransitionSeverity.PROTOCOL_VIOLATION.value in blob
    assert "not in table" in blob


def test_technical_win_record_states_what_actually_happened():
    """D-13, rules 16/22: retries_attempted reports what actually ran, never a constant."""
    rec = turn_events.technical_win_record(
        game_uid=_GAME_UID, turn=3, sender="police",
        retries_attempted=0, timeout_seconds=0, reason="opponent silent",
    )
    assert rec["event"] == "technical_win"
    assert rec["retries_attempted"] == 0
    assert rec["timeout_seconds"] == 0
    assert isinstance(rec["reason"], str) and rec["reason"]
    json.dumps(rec)


def test_watchdog_incident_record_is_self_contained():
    """NET-07: the incident record stands alone -- no external lookup needed."""
    rec = turn_events.watchdog_incident_record(
        game_uid=_GAME_UID, turn=4, sender="police",
        idle_seconds=0, threshold_seconds=0,
    )
    assert rec["event"] == "watchdog_incident"
    json.dumps(rec)


def test_game_over_record_carries_the_outcome():
    """The game_over record names the final Outcome as its JSON-safe .value."""
    rec = turn_events.game_over_record(
        game_uid=_GAME_UID, turn=5, sender="police", outcome=Outcome.CAPTURE,
    )
    assert rec["event"] == "game_over"
    assert rec["outcome"] == Outcome.CAPTURE.value
    json.dumps(rec)
