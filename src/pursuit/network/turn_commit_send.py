"""D-58 send/log/technical-loss mechanics -- a THIRD sibling split beyond
06-PLAN-OUTLINE.md's two pre-authorized `turn_commit.py`/
`turn_commit_wait.py` files, required once `turn_commit.py` alone still
measured 251 code lines against the 150-line gate even after the wait
primitive and the commit+ledger helper had already moved to
`turn_commit_wait.py`. Mirrors the THREE-file `handshake.py`/
`handshake_wire.py`/`handshake_evaluate.py` precedent this plan's own
`turn_commit.py` docstring already cites as the split's model -- not an
improvised fallback, the natural extension of the same pattern.

Holds the "how to push one COMMIT/ACK/REVEAL envelope and log it, how to
declare a technical loss, how to send the toggle-off MOVE-only envelope"
mechanics -- `turn_commit.py` keeps ONLY the three public entry points and
the policy decisions (what to send when, what gates a reveal).
"""

from __future__ import annotations

from pursuit.constants import Outcome
from pursuit.network import move_payload, turn_events
from pursuit.network.agent_context import AgentContext, Coord
from pursuit.network.deadline import call_with_retry
from pursuit.network.envelope import Envelope, EnvelopeKey, MessageType
from pursuit.network.event_log import append_event
from pursuit.network.state_machine import State
from pursuit.network.verdict import TechnicalWin

_TOOL_FOR_TYPE = {
    MessageType.COMMIT: "receive_commit",
    MessageType.ACK: "receive_ack",
    MessageType.REVEAL: "receive_reveal",
}


async def push(ctx: AgentContext, message_type: MessageType, turn: int, payload: dict) -> TechnicalWin | None:
    """Send one COMMIT/ACK/REVEAL envelope via the existing call_with_retry
    ladder (D-58, D-17) -- byte-identical retry policy to the pre-Phase-6
    MOVE push. Returns the TechnicalWin verdict on exhaustion, None on
    success (never raises)."""
    envelope = Envelope(type=message_type, turn=turn, sender=ctx.role, payload=payload)
    args = {k: v for k, v in envelope.to_dict().items() if k != EnvelopeKey.TYPE}
    tool_name = _TOOL_FOR_TYPE[message_type]

    async def _call() -> object:
        async with ctx.runtime.client() as client:
            return await client.call_tool(tool_name, args)

    call_outcome = await call_with_retry(
        _call, timeout=ctx.net.response_timeout, retries=ctx.net.retry_count,
        backoff=ctx.net.backoff_seconds,
    )
    ctx.watchdog.touch()
    return None if call_outcome.succeeded else call_outcome.verdict


async def send_and_log(
    ctx: AgentContext, message_type: MessageType, turn: int, payload: dict,
    *, state_from: State, state_to: State,
) -> TechnicalWin | None:
    """Send, then log message_sent on success only -- h_commit is public,
    the nonce never appears in any Envelope this function builds."""
    verdict = await push(ctx, message_type, turn, payload)
    if verdict is not None:
        return verdict
    envelope = Envelope(type=message_type, turn=turn, sender=ctx.role, payload=payload)
    append_event(
        ctx.log_path,
        turn_events.turn_record(
            game_uid=ctx.game_uid, turn=turn, event="message_sent", sender=ctx.role,
            state_from=state_from, state_to=state_to, envelope=envelope.to_dict(),
        ),
    )
    return None


def log_received(
    ctx: AgentContext, envelope: Envelope, *, state_from: State, state_to: State, local_turn: int,
) -> None:
    """Log an inbound envelope under THIS side's own turn number, never the
    peer's declared `envelope.turn`.

    The record's top-level `turn` is the join key the Final-Reveal audit
    indexes on (`agent_audit_exchange.observed`), so it must be locally
    authoritative: an adversarial peer that stamps its COMMIT and REVEAL
    envelopes with disjoint turn numbers would otherwise empty the rule-36
    coverage intersection AND route every entry into `audit.py`'s
    trailing-commit exemption, defeating the D-67 check outright (found at
    /gsd:verify-work 6, reproduced with paired controls -- see 06-UAT.md
    Gap 1).

    `envelope.to_dict()` is stored UNCHANGED, so whatever turn the peer
    actually claimed stays on record as evidence -- the fix removes the
    peer from the join key without destroying what the peer said."""
    append_event(
        ctx.log_path,
        turn_events.turn_record(
            game_uid=ctx.game_uid, turn=local_turn, event="message_received", sender=ctx.role,
            state_from=state_from, state_to=state_to, envelope=envelope.to_dict(),
        ),
    )


def technical_loss(ctx: AgentContext, verdict: TechnicalWin) -> Outcome:
    append_event(
        ctx.log_path,
        turn_events.technical_win_record(
            game_uid=ctx.game_uid, turn=ctx.state.turn, sender=ctx.role,
            retries_attempted=verdict.attempts, timeout_seconds=verdict.timeout_seconds,
            reason=verdict.reason.value,
        ),
    )
    ctx.machine.attempt(State.GAME_OVER)
    return Outcome.TECHNICAL_LOSS


async def send_move_only(ctx: AgentContext, current: State, pre_cell: Coord, dest: Coord) -> Outcome | None:
    """Toggle-off byte-equivalence: the exact pre-Phase-6 single MOVE send."""
    envelope = Envelope(
        type=MessageType.MOVE, turn=ctx.state.turn, sender=ctx.role,
        payload=move_payload.encode(pre_cell, dest, move_payload.ActionKind.MOVE),
    )
    args = {k: v for k, v in envelope.to_dict().items() if k != EnvelopeKey.TYPE}

    async def _push_move() -> object:
        async with ctx.runtime.client() as client:
            return await client.call_tool("receive_move", args)

    call_outcome = await call_with_retry(
        _push_move, timeout=ctx.net.response_timeout, retries=ctx.net.retry_count,
        backoff=ctx.net.backoff_seconds,
    )
    ctx.watchdog.touch()
    if not call_outcome.succeeded:
        return technical_loss(ctx, call_outcome.verdict)

    append_event(
        ctx.log_path,
        turn_events.turn_record(
            game_uid=ctx.game_uid, turn=ctx.state.turn, event="message_sent", sender=ctx.role,
            state_from=current, state_to=State.WAIT_OPPONENT, envelope=envelope.to_dict(),
        ),
    )
    return None
