"""The two turn-cycle halves (D-01, D-07, D-09) -- split out of
orchestrator.py at the 150-code-line gate (Segal Table 5), not by
responsibility: `run_turn_loop` (the entry point named in this plan's
artifacts) stays in orchestrator.py and imports `take_my_turn` /
`await_opponent_turn` from here. This module imports the AgentContext shape
and the SDK-dispatch helpers FROM orchestrator.py (one-directional); it
never re-implements move choice, legality, capture or scoring (QUAL-01).
"""

from __future__ import annotations

from pursuit.constants import Outcome
from pursuit.network import turn_events
from pursuit.network.deadline import call_with_retry, wait_for_opponent
from pursuit.network.envelope import Envelope, EnvelopeKey, MessageType
from pursuit.network.event_log import append_event
from pursuit.network.orchestrator import (
    AgentContext,
    apply_role_move,
    engine_agent,
    first_legal_move,
)
from pursuit.network.state_machine import State, TransitionResult


def _log_illegal(ctx: AgentContext, current: State, target: State, result: TransitionResult) -> None:
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


async def take_my_turn(ctx: AgentContext) -> Outcome | None:
    """One MY_TURN cycle: choose and apply this agent's move via the SDK
    only, push it to the opponent, persist the turn, hand off to
    WAIT_OPPONENT.

    Entry is guarded symmetrically with `await_opponent_turn`'s own guarded
    entry (its `if state is HANDSHAKE: attempt(WAIT_OPPONENT)` clause):
    `attempt(MY_TURN)` fires only when the machine is not ALREADY at
    MY_TURN. Every completed `await_opponent_turn` call ends by legitimately
    transitioning WAIT_OPPONENT -> MY_TURN itself (D-09's repeatable
    MY_TURN <-> WAIT_OPPONENT cycle), so the very next `take_my_turn` call in
    `run_turn_loop` always finds the machine already there -- attempting
    MY_TURN unconditionally would re-collide with that same state as an
    illegal (MY_TURN, MY_TURN) self-transition every cycle after the first,
    silently turning every second-and-later turn into a no-op that starves
    `await_opponent_turn` into a false technical win (rules 16/22). Only a
    genuinely different starting state (HANDSHAKE for the first mover, or an
    out-of-order state) still goes through `attempt()` and is reported here.
    """
    current = ctx.machine.state
    if current is not State.MY_TURN:
        result = ctx.machine.attempt(State.MY_TURN)
        if not result.accepted:
            _log_illegal(ctx, current, State.MY_TURN, result)
            return None

    chooser = ctx.choose_move or first_legal_move
    agent = engine_agent(ctx.role)
    dest = chooser(ctx.state, agent, ctx.params)
    ctx.state, outcome = apply_role_move(ctx.state, ctx.role, dest, ctx.params)

    envelope = Envelope(
        type=MessageType.MOVE, turn=ctx.state.turn, sender=ctx.role,
        payload={"x": dest[0], "y": dest[1]},
    )
    args = {k: v for k, v in envelope.to_dict().items() if k != EnvelopeKey.TYPE}

    async def _push() -> object:
        async with ctx.runtime.client() as client:
            return await client.call_tool("receive_move", args)

    call_outcome = await call_with_retry(
        _push, timeout=ctx.net.response_timeout, retries=ctx.net.retry_count,
        backoff=ctx.net.backoff_seconds,
    )
    ctx.watchdog.touch()
    if not call_outcome.succeeded:
        verdict = call_outcome.verdict
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

    append_event(
        ctx.log_path,
        turn_events.turn_record(
            game_uid=ctx.game_uid, turn=ctx.state.turn, event="message_sent", sender=ctx.role,
            state_from=current, state_to=State.WAIT_OPPONENT, envelope=envelope.to_dict(),
        ),
    )
    ctx.machine.attempt(State.WAIT_OPPONENT)
    return outcome


async def await_opponent_turn(ctx: AgentContext) -> Outcome | None:
    """One WAIT_OPPONENT cycle: bound the inbound wait (NET-06), apply the
    opponent's move via the SDK only, hand off to MY_TURN."""
    if ctx.machine.state is State.HANDSHAKE:
        ctx.machine.attempt(State.WAIT_OPPONENT)  # design note 7: thief's first wait
    current = ctx.machine.state

    call_outcome = await call_with_retry(
        lambda: wait_for_opponent(ctx.runtime.queue, timeout=ctx.net.response_timeout),
        timeout=ctx.net.response_timeout, retries=ctx.net.retry_count,
        backoff=ctx.net.backoff_seconds,
    )
    ctx.watchdog.touch()
    if not call_outcome.succeeded:
        verdict = call_outcome.verdict
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

    queued = call_outcome.value
    envelope = queued if isinstance(queued, Envelope) else Envelope.from_dict(queued)
    dest = (envelope.payload["x"], envelope.payload["y"])
    ctx.state, outcome = apply_role_move(ctx.state, envelope.sender, dest, ctx.params)

    append_event(
        ctx.log_path,
        turn_events.turn_record(
            game_uid=ctx.game_uid, turn=ctx.state.turn, event="message_received", sender=ctx.role,
            state_from=current, state_to=State.MY_TURN, envelope=envelope.to_dict(),
        ),
    )
    result = ctx.machine.attempt(State.MY_TURN)
    if not result.accepted:
        _log_illegal(ctx, current, State.MY_TURN, result)
    return outcome
