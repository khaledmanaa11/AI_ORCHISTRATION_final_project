"""Tests for the D-06 typed message envelope (NET-08)."""

import dataclasses
import json

import pytest

from pursuit.network.envelope import Envelope, MessageType


def _valid_dict():
    return {"type": "move", "turn": 1, "sender": "police", "payload": {"x": 0, "y": 0}}


def test_message_type_members():
    """MessageType pins exactly the four Phase-2 kinds (D-06)."""
    assert MessageType.HANDSHAKE.value == "handshake"
    assert MessageType.MOVE.value == "move"
    assert MessageType.BARRIER.value == "barrier"
    assert MessageType.GAME_OVER.value == "game_over"
    assert {m.value for m in MessageType} == {
        "handshake",
        "move",
        "barrier",
        "game_over",
    }


def test_to_dict_shape(default_params):
    """to_dict emits exactly four keys, type serialized to its string value."""
    env = Envelope(
        type=MessageType.MOVE,
        turn=1,
        sender="police",
        payload={"x": default_params.cop_start[0], "y": default_params.cop_start[1]},
    )
    d = env.to_dict()
    assert set(d) == {"type", "turn", "sender", "payload"}
    assert d["type"] == "move"
    assert d["payload"] == {
        "x": default_params.cop_start[0],
        "y": default_params.cop_start[1],
    }


def test_round_trip_move_envelope(default_params):
    """THE NET-08 gate test: to_dict -> json.dumps -> json.loads -> from_dict."""
    env = Envelope(
        type=MessageType.MOVE,
        turn=1,
        sender="thief",
        payload={
            "x": default_params.thief_start[0],
            "y": default_params.thief_start[1],
        },
    )
    wire = json.dumps(env.to_dict())
    restored = Envelope.from_dict(json.loads(wire))
    assert restored == env
    assert restored.type is MessageType.MOVE
    assert restored.payload["x"] == default_params.thief_start[0]
    assert restored.payload["y"] == default_params.thief_start[1]
    assert isinstance(restored.turn, int)


def test_round_trip_all_message_types():
    """Every MessageType member round-trips — the envelope is type-agnostic."""
    for member in MessageType:
        env = Envelope(type=member, turn=1, sender="police", payload={})
        wire = json.dumps(env.to_dict())
        restored = Envelope.from_dict(json.loads(wire))
        assert restored == env


def test_unknown_message_type_rejected():
    d = _valid_dict()
    d["type"] = "teleport"
    with pytest.raises(ValueError):
        Envelope.from_dict(d)


@pytest.mark.parametrize("key", ["type", "turn", "sender", "payload"])
def test_missing_key_rejected(key):
    d = _valid_dict()
    del d[key]
    with pytest.raises(KeyError):
        Envelope.from_dict(d)


def test_unexpected_key_rejected():
    # D-06 fixes the envelope at four keys; Phase-6 commit data travels INSIDE
    # payload as a new message type, never as a fifth top-level key.
    d = _valid_dict()
    d["nonce"] = "deadbeef"
    with pytest.raises(ValueError):
        Envelope.from_dict(d)


def test_non_dict_input_rejected():
    with pytest.raises(TypeError):
        Envelope.from_dict("not a dict")
    with pytest.raises(TypeError):
        Envelope.from_dict(None)


def test_non_int_turn_rejected():
    # bool is a subclass of int in Python — this forces explicit bool rejection.
    d = _valid_dict()
    d["turn"] = "1"
    with pytest.raises(TypeError):
        Envelope.from_dict(d)

    d2 = _valid_dict()
    d2["turn"] = True
    with pytest.raises(TypeError):
        Envelope.from_dict(d2)


def test_bad_sender_rejected():
    d = _valid_dict()
    d["sender"] = 7
    with pytest.raises(TypeError):
        Envelope.from_dict(d)

    d2 = _valid_dict()
    d2["sender"] = "   "
    with pytest.raises(ValueError):
        Envelope.from_dict(d2)


def test_non_dict_payload_rejected():
    d = _valid_dict()
    d["payload"] = ["x", "y"]
    with pytest.raises(TypeError):
        Envelope.from_dict(d)


def test_envelope_is_frozen():
    # NET-02 guard: a decoded envelope can be handed to the orchestrator
    # without any risk of a handler mutating shared state under it.
    env = Envelope(type=MessageType.MOVE, turn=1, sender="police", payload={})
    with pytest.raises(dataclasses.FrozenInstanceError):
        env.turn = 2
