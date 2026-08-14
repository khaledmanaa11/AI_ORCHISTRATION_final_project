"""Per-turn helpers split out of turn_actions.py at the 150-code-line gate
(Segal Table 5): the D-11 illegal-transition log line, plus (Phase 4, D-47)
the hint buffer and the bounded wait that tells a MOVE envelope apart from
an optional HINT envelope on the same wire. The joint-turn ACTION buffer
(`record_action`/`maybe_resolve`) is a sibling split, `turn_resolve.py`
(same gate, deviation, 04-12).

Deviation (Rule 3 - blocking, 04-12): `record_hint` now also populates
`ctx.incoming_hints` (a cache that survives `pending_hints`' own
resolve-time clear, so `take_my_turn` can still decode a hint one call
later -- see `network/turn_language.py`). `send_hint` drops 04-04's
`PLACEHOLDER_HINT_TEXT` in favour of the real composed text/intent (D-33's
placeholder-must-be-gone requirement).

05-06 (G3): `record_hint` itself moved to the sibling
`turn_hint_buffer.py` -- this file had no room left (146/150) for the
inbound receipt-logging it gained. It is re-exported below, so
`turn_buffer.record_hint` still resolves for every caller and every
monkeypatch, exactly as `turn_resolve.py`'s own split left this file's
API unchanged.
"""

from __future__ import annotations

import asyncio

from pursuit.constants import Outcome
from pursuit.network import hint_payload, turn_events
from pursuit.network.deadline import call_with_retry, wait_for_opponent
from pursuit.network.envelope import Envelope, EnvelopeKey, MessageType
from pursuit.network.event_log import append_event
from pursuit.network.hint_payload import Intent
from pursuit.network.orchestrator import AgentContext
from pursuit.network.state_machine import State, TransitionResult
from pursuit.network.turn_hint_buffer import record_hint
from pursuit.network.verdict import TechnicalWin

# Re-exported (05-06): `record_hint` moved to turn_hint_buffer.py at the
# 150-line gate. Named here so `turn_buffer.record_hint` keeps resolving
# for turn_commit_wait's own `turn_buffer.record_hint(...)` reference and
# for every test that monkeypatches it at this module's namespace.
__all__ = [
    "HintProtocolError",
    "await_move",
    "drain_trailing_hint",
    "log_illegal",
    "record_hint",
    "reject_peer_payload",
    "send_hint",
]


class HintProtocolError(ValueError):
    """A hint violated the Task-3 buffering rules (duplicate/late/an
    unexpected non-hint trailer). The caller turns this into a technical
    loss for the sender, same as any rules-13/14 violation -- never a crash."""


def log_illegal(ctx: AgentContext, current: State, target: State, result: TransitionResult) -> None:
    """Persist the D-11 illegal-transition evidence. The reporter callback
    already fired synchronously inside ctx.machine.attempt() (NET-05)."""
    append_event(
        ctx.log_path,
        turn_events.illegal_transition_record(
            game_uid=ctx.game_uid,
            turn=ctx.state.turn,
            sender=ctx.role,
            current=current,
            target=target,
            severity=result.severity,
            reason=f"illegal transition {current.value} -> {target.value}",
        ),
    )


def reject_peer_payload(ctx: AgentContext, reason: str) -> Outcome:
    """Shared rules-13/14 rejection path for an illegal or unparseable
    payload from the peer: log evidence, end the game, return
    Outcome.TECHNICAL_LOSS -- never raise out of the caller's handler.
    retries_attempted/timeout_seconds are genuinely 0 here: this is an
    immediate protocol rejection, not a NET-06 retry-ladder exhaustion."""
    append_event(
        ctx.log_path,
        turn_events.technical_win_record(
            game_uid=ctx.game_uid, turn=ctx.state.turn, sender=ctx.role,
            retries_attempted=0, timeout_seconds=0.0, reason=reason,
        ),
    )
    ctx.machine.attempt(State.GAME_OVER)
    return Outcome.TECHNICAL_LOSS


async def await_move(ctx: AgentContext) -> tuple[Envelope | None, TechnicalWin | None]:
    """Bounded wait for the opponent's MOVE envelope, recording (never
    blocking on) any HINT seen first -- a peer that never sends hints must
    still be playable. Raises HintProtocolError on a buffering violation."""
    for _ in range(2):
        call_outcome = await call_with_retry(
            lambda: wait_for_opponent(ctx.runtime.queue, timeout=ctx.net.response_timeout),
            timeout=ctx.net.response_timeout, retries=ctx.net.retry_count,
            backoff=ctx.net.backoff_seconds,
        )
        ctx.watchdog.touch()
        if not call_outcome.succeeded:
            return None, call_outcome.verdict
        queued = call_outcome.value
        envelope = queued if isinstance(queued, Envelope) else Envelope.from_dict(queued)
        if envelope.type is MessageType.HINT:
            record_hint(ctx, envelope.sender, envelope.turn, envelope.payload)
            continue
        return envelope, None
    raise HintProtocolError("opponent sent two consecutive hints with no move")


def drain_trailing_hint(ctx: AgentContext) -> None:
    """Non-blocking: record a hint ALREADY sitting on the queue right
    behind the move just received; never waits for one that has not
    arrived (Task 3 rule). A non-hint item found here (e.g. a future
    turn's move arriving early) is put straight back untouched -- this
    function only ever consumes an actual HINT."""
    try:
        raw = ctx.runtime.queue.get_nowait()
    except asyncio.QueueEmpty:
        return
    envelope = raw if isinstance(raw, Envelope) else Envelope.from_dict(raw)
    if envelope.type is not MessageType.HINT:
        ctx.runtime.queue.put_nowait(raw)
        return
    record_hint(ctx, envelope.sender, envelope.turn, envelope.payload)


async def send_hint(ctx: AgentContext, turn: int, *, text: str, intent: Intent) -> None:
    """Best-effort hint push for *turn* (D-47). `text`/`intent` are the
    REAL composed deception channel (04-12, replacing 04-04's
    `PLACEHOLDER_HINT_TEXT` outright) -- this function only owns the
    push-and-log mechanics, never the content. A failed push never ends the
    game: the move is the authoritative, required channel (rules 13/14); a
    hint is optional even on our OWN send side, mirroring "a peer that
    sends no hints must still be playable"."""
    hint_envelope = hint_payload.build_hint(text, intent, turn, ctx.role)
    args = {k: v for k, v in hint_envelope.to_dict().items() if k != EnvelopeKey.TYPE}

    async def _push() -> object:
        async with ctx.runtime.client() as client:
            return await client.call_tool("receive_hint", args)

    call_outcome = await call_with_retry(
        _push, timeout=ctx.net.response_timeout, retries=ctx.net.retry_count,
        backoff=ctx.net.backoff_seconds,
    )
    ctx.watchdog.touch()
    if call_outcome.succeeded:
        append_event(
            ctx.log_path,
            turn_events.turn_record(
                game_uid=ctx.game_uid, turn=turn, event="message_sent", sender=ctx.role,
                state_from=State.MY_TURN, state_to=State.WAIT_OPPONENT,
                envelope=hint_envelope.to_dict(),
            ),
        )
