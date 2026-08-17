"""Whole synthetic games on disk for the `log_` artifact tests.

Split from `artifact_log_fixtures.py` (which owns the per-RECORD builders) at
the 150-code-line gate; this half owns assembling them into a wire log plus its
`.ledger.jsonl` sibling. Not a `test_*.py` module -- pytest collects nothing.

THE ADVERSARIAL VARIANT IS THE POINT. `disjoint=True` makes the peer stamp its
COMMIT envelope with turn 99 and its REVEAL envelope with turn 7 while THIS
side logs both under local turn 3 -- the 06-05 attack, verbatim. A join keyed
on the peer's number scatters them; a join keyed on local turn truth pairs them.
"""

from __future__ import annotations

from pathlib import Path

from pursuit.network.envelope import MessageType
from tests.unit.artifact_log_fixtures import (
    GAME_UID,
    PEER,
    ROLE,
    audit_verdict_record,
    language_record,
    ledger_entry,
    over_record,
    wire,
    write_jsonl,
)

GAME_TURNS = (0, 1, 2, 3)
OVER_TURN = 4
DISJOINT_TURN = 3
PEER_COMMIT_CLAIM = 99
PEER_REVEAL_CLAIM = 7
PEER_REVEAL_PAYLOAD = {"move": {"direction": "west", "kind": "move"}, "barrier": None}


def _peer_h_commit(turn: int) -> str:
    """A stable stand-in for the peer's commitment -- this side never learns
    the peer's nonce during play (D-64), only the hash it published."""
    return f"peerhash{turn:02d}"


def _turn_wire(turn: int, entry: dict, *, disjoint: bool) -> list[dict]:
    """The seven envelopes one turn puts on the wire, from this side's view."""
    off = disjoint and turn == DISJOINT_TURN
    received = {"direction": "message_received", "sender": PEER}
    return [
        wire(local_turn=turn, sender=ROLE, kind=MessageType.COMMIT,
             payload={"h_commit": entry["h_commit"]}),
        wire(local_turn=turn, kind=MessageType.COMMIT, payload={"h_commit": _peer_h_commit(turn)},
             claimed_turn=PEER_COMMIT_CLAIM if off else None, **received),
        wire(local_turn=turn, sender=ROLE, kind=MessageType.ACK,
             payload={"h_commit": _peer_h_commit(turn)}),
        wire(local_turn=turn, sender=ROLE, kind=MessageType.REVEAL,
             payload=entry["payload"]["move"]),
        wire(local_turn=turn, kind=MessageType.REVEAL, payload=dict(PEER_REVEAL_PAYLOAD),
             claimed_turn=PEER_REVEAL_CLAIM if off else None, **received),
        wire(local_turn=turn, sender=ROLE, kind=MessageType.HINT,
             payload={"intent": "lie", "text": f"ours {turn}", "turn": turn}),
        wire(local_turn=turn, kind=MessageType.HINT,
             payload={"intent": "truth", "text": f"theirs {turn}", "turn": turn}, **received),
    ]


def write_game(
    directory: Path,
    *,
    disjoint: bool = False,
    log_tail: str | None = None,
    ledger_tail: str | None = None,
    log_corruption: str | None = None,
) -> Path:
    """Write `<uid>.jsonl` + `<uid>.ledger.jsonl` and return the log path.

    `log_corruption` injects a malformed line in the MIDDLE of the wire log --
    corruption, which must raise -- as against `log_tail`, an unterminated last
    line, which is an interrupted write and must not.
    """
    entries = [ledger_entry(turn) for turn in GAME_TURNS]
    records: list[dict] = []
    for turn, entry in zip(GAME_TURNS, entries, strict=True):
        records.extend(_turn_wire(turn, entry, disjoint=disjoint))
        records.append(language_record(turn, text=f"ours {turn}"))
    records.append(over_record(OVER_TURN))
    # The real log carries BOTH: the terminal `game_over` record and the
    # GAME_OVER envelope that went on the wire. The envelope gives the last
    # turn a wire bucket with no ledger entry behind it, which is the ordinary
    # unverifiable-turn case `verify_log_turns` has to count correctly.
    records.append(wire(local_turn=OVER_TURN, sender=ROLE, kind=MessageType.GAME_OVER,
                        payload={"outcome": "capture", "reason": "cop landed on the cell"}))
    records.append(audit_verdict_record(OVER_TURN, list(GAME_TURNS)))

    log_path = directory / f"{GAME_UID}.jsonl"
    write_jsonl(log_path, records, partial_tail=log_tail)
    if log_corruption is not None:
        lines = log_path.read_text(encoding="utf-8").splitlines()
        lines.insert(len(lines) // 2, log_corruption)
        log_path.write_text("".join(f"{line}\n" for line in lines), encoding="utf-8")
    write_jsonl(directory / f"{GAME_UID}.ledger.jsonl", entries, partial_tail=ledger_tail)
    return log_path
