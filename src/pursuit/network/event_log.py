"""Durable JSONL event log — the NET-05 sink and NET-07 crash-recovery record.

D-11 locks a structured JSONL event log per agent plus a human-readable
console echo. This one file is three things at once: the sink 02-03's
`transition(..., reporter)` writes every illegal transition into, the
NET-07 "rescues data" guarantee (a crash mid-game loses nothing because
every turn is already flushed and fsynced before this call returns), and
the seed of the Phase-7 `log_<game_id>` replay artifact.

Schema is eight stable top-level fields (see EventField). DETAILS is the
deliberate forward-compatibility hook: Phase-4 hint metadata, Phase-6
commit/nonce metadata, 02-03's transition severity and 02-07's
technical-win evidence all land there without reshaping the stable
fields — Phase 7 parses these files and must not special-case a schema
change.

Import rules: stdlib only. This module imports nothing from any sibling
network-layer or shared-config module built elsewhere in this wave —
wiring across those boundaries is 02-09's job, which keeps this module
safe to build in the same wave as its siblings (NET-02 parallel-safety).
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path


class EventType(Enum):
    """Every kind of record this log can hold."""

    MESSAGE_SENT = "message_sent"
    MESSAGE_RECEIVED = "message_received"
    STATE_TRANSITION = "state_transition"
    ILLEGAL_TRANSITION = "illegal_transition"
    TECHNICAL_WIN = "technical_win"
    WATCHDOG_INCIDENT = "watchdog_incident"
    AUDIT_VERDICT = "audit_verdict"
    # 05-04: our OWN final-reveal push failed while a board outcome already
    # stood. Evidence about us, never an accusation (rules 16/22) -- added
    # additively, exactly as AUDIT_VERDICT was, so the stable field set and
    # the Phase-7 replay parser are untouched.
    AUDIT_INCOMPLETE = "audit_incomplete"


class EventField:
    """Exact JSONL key names — mirrors constants.ConfigKey, avoids magic strings."""

    GAME_UID = "game_uid"
    TURN = "turn"
    EVENT = "event"
    SENDER = "sender"
    STATE_FROM = "state_from"
    STATE_TO = "state_to"
    ENVELOPE = "envelope"
    TIMESTAMP = "timestamp"
    DETAILS = "details"


_REQUIRED_FIELDS = (
    EventField.GAME_UID,
    EventField.TURN,
    EventField.EVENT,
    EventField.SENDER,
    EventField.TIMESTAMP,
)


def build_event(
    *,
    game_uid: str,
    turn: int,
    event: EventType,
    sender: str,
    state_from: str | None = None,
    state_to: str | None = None,
    envelope: dict | None = None,
    details: dict | None = None,
    timestamp: str | None = None,
) -> dict:
    """Assemble one log record. Optional fields are omitted, not nulled,
    when not supplied — a small, stable record keeps the Phase-7 replay
    parser simple."""
    record = {
        EventField.GAME_UID: game_uid,
        EventField.TURN: turn,
        EventField.EVENT: event.value,
        EventField.SENDER: sender,
        EventField.TIMESTAMP: timestamp or datetime.now(timezone.utc).isoformat(),
    }
    if state_from is not None:
        record[EventField.STATE_FROM] = state_from
    if state_to is not None:
        record[EventField.STATE_TO] = state_to
    if envelope is not None:
        record[EventField.ENVELOPE] = envelope
    if details is not None:
        record[EventField.DETAILS] = details
    return record


def _validate(record: dict) -> None:
    """Raise KeyError naming the first missing required field. Fail-loud,
    matching shared/config.py's house style — no silent default."""
    for field in _REQUIRED_FIELDS:
        if field not in record:
            raise KeyError(f"event record missing required field: {field!r}")


def append_event(
    path: Path | str,
    record: dict,
    *,
    echo: Callable[[str], None] | None = None,
) -> None:
    """Append one canonical-JSON line, flush + os.fsync, then optionally echo.

    Order matters: validate and serialize BEFORE the file is opened, so a
    rejected record never creates or grows the log; write, flush and
    fsync BEFORE the echo fires, so durability always outranks cosmetics.
    """
    _validate(record)
    line = json.dumps(record, sort_keys=True, separators=(",", ":"))

    with open(path, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")
        fh.flush()
        os.fsync(fh.fileno())

    if echo is not None:
        echo(console_line(record))


def console_line(record: dict) -> str:
    """One-line human-readable rendering of a valid record. Pure — no I/O."""
    parts = [
        f"[{record[EventField.TIMESTAMP]}]",
        f"turn={record[EventField.TURN]}",
        str(record[EventField.SENDER]),
        str(record[EventField.EVENT]),
    ]
    if EventField.STATE_FROM in record and EventField.STATE_TO in record:
        parts.append(f"{record[EventField.STATE_FROM]}->{record[EventField.STATE_TO]}")
    return " ".join(parts)
