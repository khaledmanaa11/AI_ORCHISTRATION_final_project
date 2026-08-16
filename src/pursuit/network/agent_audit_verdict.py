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

_OWN_SEND_FAILED = "own_final_reveal_send_failed"
"""The AUDIT_INCOMPLETE reason string (05-04). Deliberately NOT a
`TechnicalWinReason` member: this record is not a technical win, and the
subject of its sentence is OUR OWN send -- never the peer (rules 16/22)."""

OWN_RECEIVE_FAILED = "own_final_reveal_receive_failed"
"""The RECEIVE leg's own reason string (05-13, 05-UAT.md G6). Same rule,
same grammar: the subject is OUR OWN receive. Exported (no leading
underscore) because `agent_audit_wiring.run_final_audit` -- which owns the
policy deciding WHEN a failed receive is non-accusatory -- must name it at
the call site rather than have it defaulted in behind its back."""


def _verdict_record(
    ctx: AgentContext, verdict: TechnicalWin, *, event: EventType, reason: str,
) -> dict:
    """The field assembly both verdict-shaped records share -- one copy,
    two event types (no-duplication rule). Every field here is measured by
    the retry ladder that produced *verdict*, never assumed."""
    return {
        EventField.GAME_UID: ctx.game_uid,
        EventField.TURN: ctx.state.turn,
        EventField.EVENT: event.value,
        EventField.SENDER: ctx.role,
        EventField.TIMESTAMP: datetime.now(timezone.utc).isoformat(),
        "retries_attempted": verdict.attempts,
        "timeout_seconds": verdict.timeout_seconds,
        "reason": reason,
    }


def _technical_win_record(ctx: AgentContext, verdict: TechnicalWin) -> dict:
    return _verdict_record(
        ctx, verdict, event=EventType.TECHNICAL_WIN, reason=verdict.reason.value,
    )


def _record_to_dict(record: AuditRecord) -> dict:
    return {"turn": record.turn, "matched": record.matched, "detail": record.detail}


def record_audit_incomplete(
    ctx: AgentContext, verdict: TechnicalWin, *, reason: str = _OWN_SEND_FAILED,
) -> None:
    """05-UAT.md G1: THIS side's own FINAL_REVEAL push failed while the turn
    loop had ALREADY produced a board outcome. That is evidence about us --
    our send did not land -- and never grounds to declare the peer
    unresponsive. The 2026-08-13 remote round made the distinction concrete:
    machine B declared machine A `opponent_unresponsive` while A's own
    `peer_audit` already carried B's five ledger hashes byte-for-byte, so
    B's push HAD in fact been delivered and processed.

    Appends one AUDIT_INCOMPLETE record carrying the same measured evidence
    a technical win would carry, plus the ladder's elapsed time and last
    error, and returns None: the board outcome stands and `run_final_audit`
    continues into the receive + audit steps.

    05-13 (G6) generalises the record to the RECEIVE leg via *reason*,
    rather than adding a second near-identical writer (no-duplication
    rule). The default keeps every 05-04 call site byte-identical. Whatever
    a caller passes, the grammar is fixed by this function's contract: the
    subject of the sentence is OUR OWN half of the exchange, so no
    AUDIT_INCOMPLETE record can ever read as an accusation."""
    record = _verdict_record(
        ctx, verdict, event=EventType.AUDIT_INCOMPLETE, reason=reason,
    )
    record.update(elapsed_seconds=verdict.elapsed_seconds, last_error=verdict.last_error)
    append_event(ctx.log_path, record)


def record_technical_loss(ctx: AgentContext, verdict: TechnicalWin) -> Outcome:
    """Mirrors turn_commit_send.technical_loss()'s log+return shape, MINUS
    the machine.attempt(GAME_OVER) call -- ctx.machine is already terminal
    here (RESEARCH: GAME_OVER has no outgoing edges).

    ALSO appends a CORRECTED `game_over` record (05-04), for the same reason
    `record_audit_verdict`'s mismatch path already does: `game_over` is the
    only event in the log carrying an `outcome` field, `run_turn_loop` wrote
    its own with the BOARD outcome before any of this ran, and the log's
    LAST `game_over` is the authoritative one. Without this second record a
    technical loss is invisible to any reader of the log -- exactly what the
    2026-08-13 round produced, where machine B's log ends on
    `game_over=capture` while its process exited on a technical loss. The
    earlier record is left standing: the log is append-only evidence."""
    append_event(ctx.log_path, _technical_win_record(ctx, verdict))
    append_event(
        ctx.log_path,
        turn_events.game_over_record(
            game_uid=ctx.game_uid, turn=ctx.state.turn, sender=ctx.role,
            outcome=Outcome.TECHNICAL_LOSS,
        ),
    )
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
    Gap 2) -- delegated to `record_technical_loss`, which owns that
    two-record pattern for every technical loss recorded after the turn
    loop (05-04). It is never re-implemented here: a second copy would let
    the two paths drift on which record is the log's last word."""
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
    return record_technical_loss(ctx, verdict)
