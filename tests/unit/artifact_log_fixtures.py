"""Synthetic wire-log + ledger pairs for the `log_` artifact tests.

Not a `test_*.py` module on purpose (the `local_view_fixtures.py` /
`late_peer_harness.py` precedent): pytest collects nothing from it.

Every record is built by the REAL production builder -- `turn_events`,
`state_record`, `commit_pack` -- so a shape change in any of them fails these
tests instead of quietly diverging from a hand-typed copy.
"""

from __future__ import annotations

import json
from pathlib import Path

from pursuit.constants import Outcome
from pursuit.network.envelope import Envelope, MessageType
from pursuit.network.state_machine import State
from pursuit.network.turn_events import game_over_record, language_turn_record, turn_record
from pursuit.security import commit_pack
from pursuit.security.state_record import build_state_record

GAME_UID = "fixtureuid0000001"
ROLE = "police"
PEER = "thief"
BARRIERS_REMAINING = 14
TRUE_CELL = (5, 3)


def ledger_entry(turn: int, *, intent: str = "truth") -> dict:
    """One real `{turn, h_commit, payload}` ledger record."""
    state = build_state_record(
        game_id=GAME_UID, turn=turn, role=ROLE, position=(turn, 0),
        barriers_remaining=BARRIERS_REMAINING,
    )
    move = {"move": {"direction": "east", "kind": "move"}, "barrier": None}
    h_commit, nonce = commit_pack.commit(state, move, intent)
    payload = commit_pack.build_commit_payload(
        state=state, move=move, intent=intent, nonce=nonce
    )
    return {"turn": turn, "h_commit": h_commit, "payload": payload}


def wire(
    *, local_turn: int, sender: str, kind: MessageType, payload: dict,
    claimed_turn: int | None = None, direction: str = "message_sent",
) -> dict:
    """One wire record. `claimed_turn` defaults to `local_turn`; passing a
    DIFFERENT value is how the adversarial fixtures stamp a disjoint envelope
    turn -- exactly the 06-05 attack, expressed in the fixture."""
    envelope = Envelope(
        type=kind,
        turn=local_turn if claimed_turn is None else claimed_turn,
        sender=sender,
        payload=payload,
    )
    return turn_record(
        game_uid=GAME_UID, turn=local_turn, event=direction, sender=ROLE,
        state_from=State.MY_TURN, state_to=State.WAIT_OPPONENT,
        envelope=envelope.to_dict(),
    )


def language_record(turn: int, *, text: str, intent: str = "lie") -> dict:
    """A real `language_turn` record, carrying D7-8's true argmax -- which is
    exactly what the artifact must NOT republish (rules 8-9)."""
    return language_turn_record(
        game_uid=GAME_UID, turn=turn, sender=ROLE, regime="B",
        belief_entropy=1.88, belief_argmax=TRUE_CELL, reliability=0.5,
        token_spend={"budget": 200000, "calls": 0},
        incoming={"outcome": "decoded", "reason": "ok", "text": "peer words"},
        outgoing={"intent": intent, "text": text},
    )


def audit_verdict_record(turn: int, turns: list[int], *, matched: bool = True) -> dict:
    """The terminal `audit_verdict` record, both ladders populated."""
    ladder = [{"turn": t, "matched": matched, "detail": f"turn {t}: matched"} for t in turns]
    return {
        "event": "audit_verdict", "game_uid": GAME_UID, "sender": ROLE, "turn": turn,
        "timestamp": "2026-08-17T00:00:00+00:00", "matched": matched,
        "self_audit": ladder, "peer_audit": list(ladder),
    }


def over_record(turn: int) -> dict:
    """The terminal `game_over` record."""
    return game_over_record(
        game_uid=GAME_UID, turn=turn, sender=ROLE, outcome=Outcome.CAPTURE
    )


def write_jsonl(path: Path, records: list[dict], *, partial_tail: str | None = None) -> Path:
    """Write records one per line, optionally appending an unterminated tail."""
    lines = [json.dumps(record, sort_keys=True, separators=(",", ":")) for record in records]
    text = "".join(f"{line}\n" for line in lines)
    if partial_tail is not None:
        text += partial_tail
    path.write_text(text, encoding="utf-8")
    return path
