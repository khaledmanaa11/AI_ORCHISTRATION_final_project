"""Shared doubles for the early-FINAL_REVEAL corridor (05-17).

Not a `test_*.py` file on purpose -- pytest never collects it as a test
module (the `_fakes_agent.py` / `_fakes_watchdog.py` / `_hint_decode_fixtures.py`
precedent).

WHAT IT BUILDS, and why it is not simpler. `honest_peer_turn` assembles ONE
turn the peer committed and revealed IN FRONT OF US -- two `message_received`
wire records in this side's own log -- plus the peer's own final-reveal entry
for that same turn, hashed through `security.commit_pack` itself rather than
hand-written. So a case claiming "the peer's ledger reached the audit" asserts
a MATCHED audit over real hashes, never merely the absence of an accusation.

The cheap alternative was measured and refused: with `records=[]` and nothing
observed, `audit_peer_records` returns `[]` and `all_matched([])` is True, so
every case here would pass over a ledger that never arrived. An empty
`{"records": []}` is also byte-indistinguishable from the rule-36 evasion
`security/audit.py` exists to punish -- the exact vacuity 05-15 caught in its
own control.
"""

from __future__ import annotations

import json

from pursuit.network.envelope import Envelope, MessageType
from pursuit.network.orchestrator import opponent_role
from pursuit.network.turn_commit_wait import H_COMMIT_KEY
from pursuit.security import commit_pack
from pursuit.shared.security_config import SecurityParams

ON = SecurityParams(version="1.00", commit_reveal=True, team_code="khm-mn17")
"""Commit-reveal ON: the FINAL_REVEAL exchange only exists on this path."""

RECORDS_KEY = "records"
_INTENT = "truth"
_ACTION = {"move": {"kind": "move", "direction": "north"}, "barrier": None}
_TURN = 0
_POSITION = {"row": 2, "col": 3}


def _peer_state(ctx) -> dict:
    """The peer's own D-60 committed state record for `_TURN`.

    `role` is the OPPONENT's role, never ours: `audit_state.state_binding_detail`
    rejects a record claiming to have been written by `forbidden_role`
    (= `ctx.role`) as a replay of our own commits, so a fixture that got this
    backwards would fail every case for a reason that has nothing to do with
    this plan."""
    return {
        "game_id": ctx.game_uid, "turn": _TURN, "role": opponent_role(ctx.role),
        "position": _POSITION, "barriers_remaining": 0,
    }


def _observe(ctx, envelope_type: str, payload: dict) -> None:
    """Append one `message_received` record in the shape
    `agent_audit_observed.observed` reads -- top-level turn stamped by THIS
    side (06-UAT.md Gap 1), the nested envelope carrying the peer's own."""
    record = {
        "game_uid": ctx.game_uid, "turn": _TURN, "event": "message_received",
        "sender": ctx.role, "timestamp": "t",
        "envelope": {
            "type": envelope_type, "turn": _TURN,
            "sender": opponent_role(ctx.role), "payload": payload,
        },
    }
    with ctx.log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")


def honest_peer_turn(ctx) -> dict:
    """One fully-exchanged honest turn: the observed COMMIT + REVEAL land in
    `ctx.log_path`, and the peer's matching final-reveal entry is returned."""
    state = _peer_state(ctx)
    h_commit, nonce = commit_pack.commit(state, _ACTION, _INTENT)
    _observe(ctx, MessageType.COMMIT.value, {H_COMMIT_KEY: h_commit})
    _observe(ctx, MessageType.REVEAL.value, _ACTION)
    payload = commit_pack.build_commit_payload(
        state=state, move=_ACTION, intent=_INTENT, nonce=nonce,
    )
    return {"turn": _TURN, H_COMMIT_KEY: h_commit, "payload": payload}


def final_reveal(ctx, records: list[dict]) -> Envelope:
    """The peer's FINAL_REVEAL envelope -- the one that must never be lost."""
    return Envelope(
        type=MessageType.FINAL_REVEAL, turn=_TURN, sender=opponent_role(ctx.role),
        payload={RECORDS_KEY: records},
    )


def in_game_reveal(ctx) -> Envelope:
    """The peer's in-game REVEAL -- what our turn-loop leg is waiting for."""
    return Envelope(
        type=MessageType.REVEAL, turn=_TURN, sender=opponent_role(ctx.role),
        payload=_ACTION,
    )


def peer_commit(ctx, h_commit: str) -> Envelope:
    """The peer's COMMIT -- what `wait_for_opponent_commit` is waiting for."""
    return Envelope(
        type=MessageType.COMMIT, turn=_TURN, sender=opponent_role(ctx.role),
        payload={H_COMMIT_KEY: h_commit},
    )


def events(ctx) -> list[dict]:
    if not ctx.log_path.exists():
        return []
    text = ctx.log_path.read_text(encoding="utf-8")
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def kinds(ctx) -> list[str]:
    return [event["event"] for event in events(ctx)]


def audit_verdicts(ctx) -> list[dict]:
    return [event for event in events(ctx) if event["event"] == "audit_verdict"]
