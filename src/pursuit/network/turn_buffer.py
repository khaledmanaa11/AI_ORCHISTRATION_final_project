"""Per-turn helpers split out of turn_actions.py at the 150-code-line gate
(Segal Table 5): the D-11 illegal-transition log line, the joint-turn
action buffer (RULES-RESOLUTION.md) that lets take_my_turn/await_opponent_turn
each record one side's action and resolve exactly once when both are known,
and (Phase 4, D-47) the hint buffer plus the bounded wait that tells a MOVE
envelope apart from an optional HINT envelope on the same wire.
"""

from __future__ import annotations

import asyncio

from pursuit.constants import Outcome
from pursuit.network import hint_payload, turn_events
from pursuit.network.deadline import call_with_retry, wait_for_opponent
from pursuit.network.envelope import Envelope, EnvelopeKey, MessageType
from pursuit.network.event_log import append_event
from pursuit.network.hint_payload import Intent
from pursuit.network.orchestrator import AgentContext, Coord
from pursuit.network.state_machine import State, TransitionResult
from pursuit.network.verdict import TechnicalWin
from pursuit.sdk import engine
from pursuit.sdk.actions import CopAction

PLACEHOLDER_HINT_TEXT = "Placeholder hint text; the real bluff generator lands in a later plan."
"""04-04 transport scaffolding ONLY -- NOT the deception feature. 04-08
picks intent/payload, 04-10 phrases it through the LLM/template bank, and
04-12 wires that real pipeline in here, replacing this constant outright."""


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


def record_action(ctx: AgentContext, role: str, dest: Coord) -> None:
    """Store *dest* into this joint turn's buffer slot for *role*.

    The cop's wire action is always a move in this phase -- CopAction(move=
    dest) wraps it into the shape resolve_turn expects; barrier placement
    over the wire is Phase 6 work."""
    if role == "police":
        ctx.pending_cop_action = CopAction(move=dest)
    else:
        ctx.pending_thief_move = dest


def maybe_resolve(ctx: AgentContext) -> Outcome | None:
    """Resolve the joint turn once both actions are known; a no-op
    otherwise. Whichever half fills the second buffer slot calls
    engine.resolve_turn exactly once (RULES-RESOLUTION.md Sec1); the hint
    buffer is cleared too -- it belonged to the turn that just ended."""
    if ctx.pending_cop_action is None or ctx.pending_thief_move is None:
        return None
    ctx.state, outcome = engine.resolve_turn(
        ctx.state, ctx.pending_cop_action, ctx.pending_thief_move, ctx.params, ctx.rules
    )
    ctx.pending_cop_action = None
    ctx.pending_thief_move = None
    ctx.pending_hints = {}
    return outcome


def record_hint(ctx: AgentContext, sender: str, turn: int, payload: dict) -> None:
    """Buffer one hint for the turn currently being collected (Task 3
    rules): a duplicate from the same sender, or a hint whose turn has
    already resolved, raises HintProtocolError. A missing hint is simply
    never called here, and never blocks resolution."""
    if turn < ctx.state.turn:
        raise HintProtocolError(f"hint for turn {turn} arrived after turn {ctx.state.turn} started")
    if sender in ctx.pending_hints:
        raise HintProtocolError(f"duplicate hint from {sender} for turn {turn}")
    ctx.pending_hints[sender] = payload


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


async def send_hint(ctx: AgentContext, turn: int) -> None:
    """Best-effort placeholder-hint push for *turn* (D-47). A failed push
    never ends the game: the move is the authoritative, required channel
    (rules 13/14); a hint is optional even on our OWN send side, mirroring
    "a peer that sends no hints must still be playable"."""
    hint_envelope = hint_payload.build_hint(PLACEHOLDER_HINT_TEXT, Intent.TRUTH, turn, ctx.role)
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
