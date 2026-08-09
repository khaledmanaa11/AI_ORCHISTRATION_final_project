"""D-67 verdict recording: how a Final-Reveal audit result becomes durable
evidence in this side's own JSONL.

Split out of `agent_audit_exchange.py` at the 150-code-line gate (Segal
Table 5) when 06-05's Gap-2 fix pushed that file to 159 -- along the seam
its own docstring already named: the sibling keeps the WIRE mechanics
(push/receive one FINAL_REVEAL, read this side's observed history), this
module keeps "how to record an audit verdict".

Both public names are re-exported from `agent_audit_exchange` so existing
importers (`agent_audit_wiring`) are unaffected.
"""

from __future__ import annotations

from datetime import datetime, timezone

from pursuit.constants import Outcome
from pursuit.network import turn_events
from pursuit.network.agent_context import AgentContext
from pursuit.network.event_log import EventField, EventType, append_event
from pursuit.network.verdict import TechnicalWin, TechnicalWinReason
from pursuit.security.audit import AuditRecord, all_matched


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


def record_technical_loss(ctx: AgentContext, verdict: TechnicalWin) -> Outcome:
    """Mirrors turn_commit_send.technical_loss()'s log+return shape, MINUS
    the machine.attempt(GAME_OVER) call -- ctx.machine is already terminal
    here (RESEARCH: GAME_OVER has no outgoing edges)."""
    append_event(ctx.log_path, _technical_win_record(ctx, verdict))
    return Outcome.TECHNICAL_LOSS


def record_audit_verdict(
    ctx: AgentContext, *, peer_audit: list[AuditRecord], self_audit: list[AuditRecord],
    elapsed_seconds: float,
) -> Outcome | None:
    """Append one AUDIT_VERDICT record (symmetric honesty, CONTEXT locked:
    a self-mismatch is reported with the exact same label as an opponent
    mismatch); on any mismatch, ALSO log a technical_win record via the
    EXISTING TechnicalWin(reason=AUDIT_HASH_MISMATCH) pathway and return
    Outcome.TECHNICAL_LOSS -- never a second, parallel verdict type.

    A mismatch additionally appends a CORRECTED `game_over` record (06-05,
    Gap 2). `run_turn_loop` writes its own `game_over` with the BOARD
    outcome before this audit ever runs (orchestrator.py), and `game_over`
    is the only event in the log carrying an `outcome` field -- so without
    this second record the log's outcome would still read as the cheating
    peer's win, no matter what the audit concluded. The earlier record is
    deliberately left in place rather than rewritten: the log is
    append-only evidence, and the pre-audit board result is a real fact
    about the game. The LAST game_over record is the audited one."""
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
    append_event(
        ctx.log_path,
        turn_events.game_over_record(
            game_uid=ctx.game_uid, turn=ctx.state.turn, sender=ctx.role,
            outcome=Outcome.TECHNICAL_LOSS,
        ),
    )
    return Outcome.TECHNICAL_LOSS
