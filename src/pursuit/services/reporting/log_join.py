"""The `log_<game_id>_g<NN>` JOIN: this side's wire JSONL x its own nonce
ledger, keyed on LOCAL TURN TRUTH.

THE JOIN KEY IS THE RECORD'S OWN TOP-LEVEL `turn`, NEVER `envelope["turn"]`.
That is not a style preference; it is the exact bug 06-05 closed, and
`network/agent_audit_observed.observed` already writes it down: the top-level
turn is "a number THIS side stamped ... never on the nested `envelope`'s turn,
which on the received side is whatever the peer chose to claim". Keying on the
peer's number let an adversary stamp its COMMIT and REVEAL with disjoint turns,
which emptied `audit.audit_peer_records`'s coverage intersection (re-opening
the `{"records": []}` rule-36 evasion) and sent every entry down the
trailing-commit exemption, so the D-67 revealed-vs-played check never fired.
This builder reuses that discipline rather than re-deriving it. The peer's
claimed turn is carried verbatim into `peer_claimed_turns` as EVIDENCE and is
never a key.

A TRUNCATED TAIL IS TOLERATED; MID-FILE CORRUPTION IS NOT -- see
`log_read.py`, which owns that reader and the reasoning. A dropped partial
tail is reported in this module's `truncated_tail`, never swallowed.

TWO EVENT NAMES ARE NOT `EventType` MEMBERS. `turn_events.language_turn_record`
and `game_over_record` set `EventField.EVENT` to the bare strings
`"language_turn"` and `"game_over"`; `EventType(record[EVENT])` would raise on
them and a membership test would drop them silently, so every filter below is
on the STRING. Full reasoning: `docs/PRD_log_artifact.md` Sec4.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pursuit.network.envelope import EnvelopeKey
from pursuit.network.event_log import EventField, EventType
from pursuit.network.turn_commit_ledger import ledger_path_for
from pursuit.security.ledger import LedgerField
from pursuit.services.reporting.log_read import CorruptLogError, read_tolerating_partial_tail
from pursuit.services.reporting.log_turn_fields import TurnField, WireSide, build_turn_record

__all__ = (
    "GAME_OVER_EVENT",
    "LANGUAGE_TURN_EVENT",
    "CorruptLogError",
    "JoinedGame",
    "join_game",
    "local_turn",
    "peer_claimed_turn",
    "read_tolerating_partial_tail",
)

LANGUAGE_TURN_EVENT = "language_turn"
GAME_OVER_EVENT = "game_over"
OUTCOME_FIELD = "outcome"
MATCHED_FIELD = "matched"
SELF_AUDIT_FIELD = "self_audit"
PEER_AUDIT_FIELD = "peer_audit"
CLAIMED = "claimed"
LOG_SOURCE = "log"
LEDGER_SOURCE = "ledger"


def local_turn(record: dict) -> int | None:
    """THE JOIN KEY: the turn THIS side stamped on the record (06-05)."""
    return record.get(EventField.TURN)


def peer_claimed_turn(record: dict) -> int | None:
    """EVIDENCE, NEVER A KEY: the turn the peer stamped inside the envelope."""
    envelope = record.get(EventField.ENVELOPE)
    return envelope.get(EnvelopeKey.TURN) if isinstance(envelope, dict) else None


@dataclass(frozen=True)
class JoinedGame:
    """One finished game, joined. `turns` is sorted by local turn.

    `game_uids` is a TUPLE in first-appearance order, not one string, because
    D-61's `adopt_negotiated_game_id` renames this side's log mid-stream and a
    record written before the handshake keeps its pre-negotiation id. Measured
    on a real game and reasoned in `docs/PRD_log_artifact.md` Sec7.
    """

    game_uids: tuple[str, ...]
    role: str | None
    turns: list[dict]
    outcome: dict | None
    audit_verdict: dict | None
    truncated_tail: dict


def _is_turn(value: object) -> bool:
    """A usable turn key: a plain int (`bool` is an `int` subclass)."""
    return isinstance(value, int) and not isinstance(value, bool)


def _store_wire(wire: dict, turn: int, side: str, record: dict) -> None:
    """File one envelope under its LOCAL turn, per side and envelope type."""
    envelope = record.get(EventField.ENVELOPE)
    if not isinstance(envelope, dict):
        return
    bucket = wire.setdefault(turn, {WireSide.SENT: {}, WireSide.RECEIVED: {}, CLAIMED: {}})
    kind = envelope.get(EnvelopeKey.TYPE)
    bucket[side][kind] = envelope.get(EnvelopeKey.PAYLOAD)
    if side == WireSide.RECEIVED:
        bucket[CLAIMED][kind] = peer_claimed_turn(record)


def _verdicts_by_turn(record: dict | None) -> dict:
    """Split an `audit_verdict` record's two ladders into per-turn entries."""
    verdicts: dict = {}
    for name, side in ((SELF_AUDIT_FIELD, WireSide.SELF), (PEER_AUDIT_FIELD, WireSide.PEER)):
        for entry in (record or {}).get(name) or []:
            turn = entry.get(TurnField.TURN)
            if _is_turn(turn):
                verdicts.setdefault(turn, {})[side] = entry
    return verdicts


def join_game(log_path: Path | str) -> JoinedGame:
    """Join `log_path`'s wire JSONL to its `ledger_path_for` sibling."""
    file_path = Path(log_path)
    records, log_cut = read_tolerating_partial_tail(file_path)
    ledger_lines, ledger_cut = read_tolerating_partial_tail(ledger_path_for(file_path))

    ledger = {r.get(LedgerField.TURN): r for r in ledger_lines if _is_turn(r.get(LedgerField.TURN))}
    wire: dict = {}
    language: dict = {}
    uids: dict[str, None] = {}
    role = outcome = verdict_record = None

    for record in records:
        event, turn = record.get(EventField.EVENT), local_turn(record)
        uid = record.get(EventField.GAME_UID)
        if isinstance(uid, str):
            uids[uid] = None
        if not _is_turn(turn):
            continue
        if event == EventType.MESSAGE_SENT.value:
            role = role or record.get(EventField.SENDER)
            _store_wire(wire, turn, WireSide.SENT, record)
        elif event == EventType.MESSAGE_RECEIVED.value:
            _store_wire(wire, turn, WireSide.RECEIVED, record)
        elif event == LANGUAGE_TURN_EVENT:
            language[turn] = record
        elif event == GAME_OVER_EVENT:
            outcome = {OUTCOME_FIELD: record.get(OUTCOME_FIELD), TurnField.TURN: turn}
        elif event == EventType.AUDIT_VERDICT.value:
            verdict_record = record

    verdicts = _verdicts_by_turn(verdict_record)
    empty: dict = {WireSide.SENT: {}, WireSide.RECEIVED: {}, CLAIMED: {}}
    turns = [
        build_turn_record(
            turn=turn,
            ledger_record=ledger.get(turn),
            sent=wire.get(turn, empty)[WireSide.SENT],
            received=wire.get(turn, empty)[WireSide.RECEIVED],
            language=language.get(turn),
            verdict=verdicts.get(turn, {}),
            peer_claimed_turns=wire.get(turn, empty)[CLAIMED],
        )
        for turn in sorted(set(ledger) | set(wire))
    ]
    audit = None
    if verdict_record is not None:
        audit = {
            MATCHED_FIELD: verdict_record.get(MATCHED_FIELD),
            TurnField.TURN: local_turn(verdict_record),
        }
    return JoinedGame(
        game_uids=tuple(uids),
        role=role,
        turns=turns,
        outcome=outcome,
        audit_verdict=audit,
        truncated_tail={LOG_SOURCE: log_cut, LEDGER_SOURCE: ledger_cut},
    )
