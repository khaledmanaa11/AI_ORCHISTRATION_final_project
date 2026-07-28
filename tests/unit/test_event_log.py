"""Tests for the JSONL event log (D-11, D-14, NET-05 sink).

Durability is the point of this module, so it is asserted two independent
ways: observable (an independent file handle sees the line immediately) and
mechanical (os.fsync is actually called). Fail-loud rejection is asserted to
leave the log file untouched — a rejected record must not create or grow it.
"""

import json
import os
from datetime import datetime

import pytest

from pursuit.network.event_log import (
    EventField,
    EventType,
    append_event,
    build_event,
    console_line,
)


def test_append_event_writes_one_json_object_per_line(tmp_path):
    log_path = tmp_path / "log.jsonl"
    record_a = build_event(
        game_uid="g1",
        turn=1,
        event=EventType.STATE_TRANSITION,
        sender="police",
        state_from="my_turn",
        state_to="wait_opponent",
    )
    record_b = build_event(
        game_uid="g1",
        turn=1,
        event=EventType.MESSAGE_SENT,
        sender="police",
        envelope={"type": "move", "turn": 1, "sender": "police", "payload": {"x": 1, "y": 2}},
    )

    append_event(log_path, record_a)
    append_event(log_path, record_b)

    lines = log_path.read_text(encoding="utf-8").split("\n")
    assert lines[-1] == ""
    lines = lines[:-1]
    assert len(lines) == 2

    parsed = [json.loads(line) for line in lines]
    assert parsed[0] == record_a
    assert parsed[1] == record_b

    assert lines[0] == json.dumps(record_a, sort_keys=True, separators=(",", ":"))
    assert lines[1] == json.dumps(record_b, sort_keys=True, separators=(",", ":"))


def test_append_event_is_durable_after_write(tmp_path, monkeypatch):
    log_path = tmp_path / "log.jsonl"
    record = build_event(
        game_uid="g1", turn=1, event=EventType.MESSAGE_SENT, sender="police"
    )

    append_event(log_path, record)

    # (a) Observable: a fresh, independent handle already sees the line.
    with open(log_path, encoding="utf-8") as fh:
        content = fh.read()
    assert json.loads(content.strip()) == record

    # (b) Mechanical: os.fsync is actually invoked with an int fd.
    real_fsync = os.fsync
    calls = []

    def fsync_spy(fd):
        calls.append(fd)
        return real_fsync(fd)

    monkeypatch.setattr(os, "fsync", fsync_spy)

    record2 = build_event(
        game_uid="g1", turn=2, event=EventType.MESSAGE_SENT, sender="police"
    )
    append_event(log_path, record2)

    assert len(calls) == 1
    assert isinstance(calls[0], int)


def test_append_event_echoes_human_readable_line_after_the_write(tmp_path):
    log_path = tmp_path / "log.jsonl"
    record = build_event(
        game_uid="g1",
        turn=3,
        event=EventType.STATE_TRANSITION,
        sender="police",
        state_from="my_turn",
        state_to="wait_opponent",
    )
    captured = []

    def echo(line):
        captured.append((line, log_path.read_text(encoding="utf-8")))

    append_event(log_path, record, echo=echo)

    assert len(captured) == 1
    echoed_line, file_content_during_echo = captured[0]
    assert echoed_line == console_line(record)
    assert "police" in echoed_line
    assert EventType.STATE_TRANSITION.value in echoed_line
    assert "3" in echoed_line
    assert json.dumps(record, sort_keys=True, separators=(",", ":")) not in echoed_line
    # Durable write happened BEFORE the echo fired (D-11 ordering).
    assert json.loads(file_content_during_echo.strip()) == record


def test_append_event_rejects_record_missing_required_field(tmp_path):
    log_path = tmp_path / "log.jsonl"

    with pytest.raises(KeyError):
        append_event(log_path, {EventField.TURN: 1})

    assert not log_path.exists()


def test_append_event_rejects_unserializable_value(tmp_path):
    log_path = tmp_path / "log.jsonl"
    valid_record = build_event(
        game_uid="g1", turn=1, event=EventType.MESSAGE_SENT, sender="police"
    )
    append_event(log_path, valid_record)

    bad_record = build_event(
        game_uid="g1",
        turn=2,
        event=EventType.MESSAGE_SENT,
        sender="police",
        details={"probe": object()},
    )

    with pytest.raises(TypeError):
        append_event(log_path, bad_record)

    lines = [line for line in log_path.read_text(encoding="utf-8").split("\n") if line]
    assert len(lines) == 1


def test_build_event_defaults_timestamp_and_omits_empty_optionals():
    record = build_event(
        game_uid="g1", turn=1, event=EventType.MESSAGE_SENT, sender="police"
    )

    assert EventField.GAME_UID in record
    assert EventField.TURN in record
    assert EventField.EVENT in record
    assert EventField.SENDER in record
    assert EventField.TIMESTAMP in record

    assert isinstance(record[EventField.TIMESTAMP], str)
    datetime.fromisoformat(record[EventField.TIMESTAMP])

    assert EventField.STATE_FROM not in record
    assert EventField.STATE_TO not in record
    assert EventField.ENVELOPE not in record
    assert EventField.DETAILS not in record

    full_record = build_event(
        game_uid="g1",
        turn=1,
        event=EventType.STATE_TRANSITION,
        sender="police",
        state_from="my_turn",
        state_to="wait_opponent",
        details={"note": "ok"},
    )
    assert full_record[EventField.STATE_FROM] == "my_turn"
    assert full_record[EventField.STATE_TO] == "wait_opponent"
    assert full_record[EventField.DETAILS] == {"note": "ok"}
