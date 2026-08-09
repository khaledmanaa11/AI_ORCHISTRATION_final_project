"""D-67 wire mechanics for the Final-Reveal mutual audit -- split from
agent_audit_wiring.py at the 150-code-line gate (pre-authorized: this
plan's own must_haves anticipated agent_audit_wiring.py needing further
splitting, mirroring the handshake.py/turn_commit.py precedent). Holds
"how to push/receive one FINAL_REVEAL envelope", "how to read this side's
own observed commit/reveal history from its wire log", and "how to record
an audit verdict" -- agent_audit_wiring.py keeps only the two public entry
points and policy (declare_step0/write_declaration/run_final_audit).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from pursuit.constants import Outcome
from pursuit.network.agent_context import AgentContext
from pursuit.network.deadline import call_with_retry
from pursuit.network.envelope import Envelope, EnvelopeKey, MessageType
from pursuit.network.event_log import EventField, EventType, append_event
from pursuit.network.turn_commit_wait import H_COMMIT_KEY, next_protocol_message
from pursuit.network.verdict import TechnicalWin, TechnicalWinReason
from pursuit.security.audit import AuditRecord, all_matched

_FINAL_REVEAL_TOOL = "receive_final_reveal"
_RECORDS_KEY = "records"


async def push_final_reveal(ctx: AgentContext, records: list[dict]) -> TechnicalWin | None:
    """Send THIS side's own ledger as one FINAL_REVEAL envelope, via the
    SAME call_with_retry ladder every other push uses (D-17, no new number)."""
    envelope = Envelope(
        type=MessageType.FINAL_REVEAL, turn=ctx.state.turn, sender=ctx.role,
        payload={_RECORDS_KEY: records},
    )
    args = {k: v for k, v in envelope.to_dict().items() if k != EnvelopeKey.TYPE}

    async def _call() -> object:
        async with ctx.runtime.client() as client:
            return await client.call_tool(_FINAL_REVEAL_TOOL, args)

    call_outcome = await call_with_retry(
        _call, timeout=ctx.net.response_timeout, retries=ctx.net.retry_count,
        backoff=ctx.net.backoff_seconds,
    )
    return None if call_outcome.succeeded else call_outcome.verdict


async def receive_final_reveal(ctx: AgentContext) -> tuple[list[dict], TechnicalWin | None]:
    """Block for the opponent's own FINAL_REVEAL -- the SAME bounded-wait
    primitive turn_commit.py's own waits use (tolerant of a stray HINT)."""
    envelope, verdict = await next_protocol_message(ctx)
    if verdict is not None:
        return [], verdict
    return envelope.payload.get(_RECORDS_KEY, []), None


def _read_log(ctx: AgentContext) -> list[dict]:
    if not ctx.log_path.exists():
        return []
    with ctx.log_path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def observed(ctx: AgentContext, *, direction: str) -> tuple[dict[int, str], dict[int, dict]]:
    """Build (observed_commits, observed_reveals) from ctx.log_path's own
    JSONL, filtered to *direction* ("message_sent" or "message_received").
    Sent = this side's own self-check evidence; received = what this side
    actually saw the opponent do (D-67).

    Both dicts are keyed on the RECORD's own top-level turn -- a number
    THIS side stamped (`turn_commit_send.log_received`'s `local_turn`,
    `turn_actions.await_opponent_turn`'s pre-resolve `observed_turn`, and
    our own `send_and_log` turn on the sent side) -- never on the nested
    `envelope`'s turn, which on the received side is whatever the peer
    chose to claim.

    That distinction is load-bearing, not cosmetic. Keying on the peer's
    own number let an adversary stamp its COMMIT and REVEAL envelopes with
    disjoint turns, which (1) emptied `audit.audit_peer_records`'s
    `set(commits) & set(reveals)` coverage intersection, re-opening the
    `{"records": []}` rule-36 evasion, and (2) sent every entry down the
    trailing-commit exemption, so the D-67 revealed-vs-played check never
    fired. Found at /gsd:verify-work 6 and reproduced with paired
    controls; see 06-UAT.md Gap 1 and tests/unit/test_audit_turn_binding.py.

    The nested envelope is still read for its type and payload, and is
    still stored verbatim, so the peer's claimed turn remains on record as
    evidence."""
    commits: dict[int, str] = {}
    reveals: dict[int, dict] = {}
    for record in _read_log(ctx):
        if record.get(EventField.EVENT) != direction:
            continue
        envelope = record.get(EventField.ENVELOPE)
        if envelope is None:
            continue
        turn = record.get(EventField.TURN)
        payload = envelope.get(EnvelopeKey.PAYLOAD, {})
        if envelope.get(EnvelopeKey.TYPE) == MessageType.COMMIT.value:
            commits[turn] = payload.get(H_COMMIT_KEY)
        elif envelope.get(EnvelopeKey.TYPE) == MessageType.REVEAL.value:
            reveals[turn] = payload
    return commits, reveals


def record_technical_loss(ctx: AgentContext, verdict: TechnicalWin) -> Outcome:
    """Mirrors turn_commit_send.technical_loss()'s log+return shape, MINUS
    the machine.attempt(GAME_OVER) call -- ctx.machine is already terminal
    here (RESEARCH: GAME_OVER has no outgoing edges)."""
    append_event(
        ctx.log_path,
        _technical_win_record(ctx, verdict),
    )
    return Outcome.TECHNICAL_LOSS


def _technical_win_record(ctx: AgentContext, verdict: TechnicalWin) -> dict:
    return {
        EventField.GAME_UID: ctx.game_uid,
        EventField.TURN: ctx.state.turn,
        EventField.EVENT: EventType.TECHNICAL_WIN.value,
        EventField.SENDER: ctx.role,
        EventField.TIMESTAMP: datetime.now(timezone.utc).isoformat(),
        "retries_attempted": verdict.attempts,
        "timeout_seconds": verdict.timeout_seconds,
        "reason": verdict.reason.value,
    }


def _record_to_dict(record: AuditRecord) -> dict:
    return {"turn": record.turn, "matched": record.matched, "detail": record.detail}


def record_audit_verdict(
    ctx: AgentContext, *, peer_audit: list[AuditRecord], self_audit: list[AuditRecord],
    elapsed_seconds: float,
) -> Outcome | None:
    """Append one AUDIT_VERDICT record (symmetric honesty, CONTEXT locked:
    a self-mismatch is reported with the exact same label as an opponent
    mismatch); on any mismatch, ALSO log a technical_win record via the
    EXISTING TechnicalWin(reason=AUDIT_HASH_MISMATCH) pathway and return
    Outcome.TECHNICAL_LOSS -- never a second, parallel verdict type."""
    matched = all_matched(peer_audit) and all_matched(self_audit)
    append_event(
        ctx.log_path,
        {
            EventField.GAME_UID: ctx.game_uid,
            EventField.TURN: ctx.state.turn,
            EventField.EVENT: EventType.AUDIT_VERDICT.value,
            EventField.SENDER: ctx.role,
            EventField.TIMESTAMP: datetime.now(timezone.utc).isoformat(),
            "matched": matched,
            "peer_audit": [_record_to_dict(r) for r in peer_audit],
            "self_audit": [_record_to_dict(r) for r in self_audit],
        },
    )
    if matched:
        return None

    mismatches = [r.detail for r in (*peer_audit, *self_audit) if not r.matched]
    verdict = TechnicalWin(
        reason=TechnicalWinReason.AUDIT_HASH_MISMATCH, attempts=1,
        timeout_seconds=0.0, backoff_seconds=0.0, elapsed_seconds=elapsed_seconds,
        last_error="; ".join(mismatches),
    )
    append_event(ctx.log_path, _technical_win_record(ctx, verdict))
    return Outcome.TECHNICAL_LOSS
