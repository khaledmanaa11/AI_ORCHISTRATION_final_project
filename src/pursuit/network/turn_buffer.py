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
from pursuit.network.verdict import TechnicalWin


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


def record_hint(ctx: AgentContext, sender: str, turn: int, payload: dict) -> None:
    """Buffer one hint for the turn currently being collected. A missing
    hint is simply never called here, and never blocks resolution.

    Deviation (Rule 1 - bug, 04-12): TWO of 04-04's original rules --
    "late" and "duplicate" both raising `HintProtocolError` -- are replaced
    with silent drop / overwrite. The move and the hint are two INDEPENDENT
    network round-trips, each with its own (now real, variable-latency)
    decode/compose work between them; a genuine two-peer game measurably
    hits both timing patterns (a hint arriving after the receiver already
    resolved that turn, and a second not-yet-consumed hint arriving before
    a slower side finishes processing the first). Raising in either case
    turned ordinary jitter into a spurious `Outcome.TECHNICAL_LOSS` --
    exactly the "forfeit caused by a hint" this plan's own must_haves rules
    out. The channel is best-effort by design (04-04's own decision); only
    `await_move`'s SEPARATE "two consecutive hints, no move" cap still
    raises -- that one guards liveness (an opponent that never sends a
    move), not hint timing.

    Also caches `payload` into `ctx.incoming_hints[sender]` (04-12) --
    UNLIKE `pending_hints`, this survives `maybe_resolve`'s clear, so
    whichever side's `take_my_turn` runs after the buffer already cleared
    (design note 7's "police sends first") can still decode the hint that
    arrived alongside the opponent's last revealed move."""
    if turn < ctx.state.turn:
        return
    ctx.pending_hints[sender] = payload
    ctx.incoming_hints[sender] = payload


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
