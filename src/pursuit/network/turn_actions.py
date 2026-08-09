"""The two turn-cycle halves (D-01, D-07, D-09) -- split out of
orchestrator.py at the 150-code-line gate (Segal Table 5), not by
responsibility: `run_turn_loop` (the entry point named in this plan's
artifacts) stays in orchestrator.py and imports `take_my_turn` /
`await_opponent_turn` from here. This module imports the AgentContext shape
and the SDK-dispatch helpers FROM orchestrator.py (one-directional); it
never re-implements move choice, legality, capture or scoring (QUAL-01).

Joint turn (RULES-RESOLUTION.md): each half below records its own or the
opponent's action into ctx's buffer via `turn_resolve.record_action`, then
calls `turn_resolve.maybe_resolve` -- a no-op until BOTH slots are filled,
at which point whichever half completes the pair calls `engine.resolve_turn`
exactly once (split into `turn_resolve.py`/`turn_buffer.py` at the same
150-line gate). The cop's wire action is always a move in this phase
(barrier placement over the wire is Phase 6 work).

Phase 4 (D-47, D-53, D-33, D-48): the move payload is a direction token
(`move_payload.encode`/`decode`), never a coordinate. 04-12 replaces
04-04's placeholder hint with the real pipeline -- decode the opponent's
last-revealed hint -> choose our move (belief-aware when `ctx.brain` is
wired) -> plan a claim about the move just chosen -> compose it -> send
both. The language half is entirely OPTIONAL per `AgentContext.language`
(None -> move-only turns, matching pre-04-04 mechanics); every real game
(`agent_lifecycle.default_context`) always wires it.
"""

from __future__ import annotations

import time

from pursuit.constants import Outcome
from pursuit.network import move_payload, turn_buffer, turn_events
from pursuit.network.deadline import call_with_retry
from pursuit.network.envelope import Envelope, EnvelopeKey, MessageType
from pursuit.network.event_log import append_event
from pursuit.network.orchestrator import AgentContext, engine_agent
from pursuit.network.state_machine import State
from pursuit.network.turn_buffer import HintProtocolError, log_illegal
from pursuit.network.turn_language import choose_destination, known_opponent_cell
from pursuit.network.turn_language_io import decode_turn_hint, send_turn_hint
from pursuit.network.turn_resolve import maybe_resolve, record_action
from pursuit.services.language_turn import turn_budget_seconds
from pursuit.shared.inference import NO_EVIDENCE


async def take_my_turn(ctx: AgentContext) -> Outcome | None:
    """One MY_TURN cycle: decode -> choose -> buffer -> push move -> plan
    deception -> compose -> push hint -> hand off to WAIT_OPPONENT.
    ctx.state changes only if this call also completes the pair
    (maybe_resolve). Entry is guarded symmetrically with
    `await_opponent_turn`'s own guarded entry: `attempt(MY_TURN)` fires only
    when the machine is not already there (D-09's repeatable cycle)."""
    current = ctx.machine.state
    if current is not State.MY_TURN:
        result = ctx.machine.attempt(State.MY_TURN)
        if not result.accepted:
            log_illegal(ctx, current, State.MY_TURN, result)
            return None

    agent = engine_agent(ctx.role)
    pre_turn_state = ctx.state
    pre_cell = pre_turn_state.cop if agent == "cop" else pre_turn_state.thief
    known = known_opponent_cell(ctx, agent)
    regime = "A" if known is not None else "B"

    budget = turn_budget_seconds(ctx.net) if ctx.language is not None else 0.0
    started = time.monotonic()
    inference, incoming_log = NO_EVIDENCE, None
    if ctx.language is not None:
        inference, incoming_log = await decode_turn_hint(ctx, started, budget)

    dest = choose_destination(ctx, agent, inference, known)
    record_action(ctx, ctx.role, dest)
    outcome = maybe_resolve(ctx)

    envelope = Envelope(
        type=MessageType.MOVE, turn=ctx.state.turn, sender=ctx.role,
        payload=move_payload.encode(pre_cell, dest, move_payload.ActionKind.MOVE),
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
    if ctx.language is not None:
        await send_turn_hint(
            ctx, agent, pre_turn_state, dest, envelope.turn, started, budget, regime, incoming_log,
        )
    ctx.machine.attempt(State.WAIT_OPPONENT)
    return outcome


async def await_opponent_turn(ctx: AgentContext) -> Outcome | None:
    """One WAIT_OPPONENT cycle: bound the inbound wait (NET-06), decode and
    validate the opponent's direction-token or legacy move (D-53), buffer
    it, hand off to MY_TURN. A hint encountered along the way is buffered
    but never required (Task 3: "a peer that sends no hints must still be
    playable"). ctx.state changes only if this call also completes the
    pair (maybe_resolve)."""
    if ctx.machine.state is State.HANDSHAKE:
        ctx.machine.attempt(State.WAIT_OPPONENT)  # design note 7: thief's first wait
    current = ctx.machine.state

    try:
        move_envelope, verdict = await turn_buffer.await_move(ctx)
        if verdict is None:
            turn_buffer.drain_trailing_hint(ctx)
    except HintProtocolError as exc:
        return turn_buffer.reject_peer_payload(ctx, reason=str(exc))

    if verdict is not None:
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

    agent = engine_agent(move_envelope.sender)
    pre_cell = ctx.state.cop if agent == "cop" else ctx.state.thief
    resolved = move_payload.decode(move_envelope.payload, pre_cell, ctx.params)
    if not (resolved.ok and move_payload.is_legal(pre_cell, resolved, ctx.state, ctx.params)):
        reason = resolved.reason or f"{resolved.cell} is not a legal {agent} action"
        return turn_buffer.reject_peer_payload(ctx, reason=reason)
    record_action(ctx, move_envelope.sender, resolved.cell)
    outcome = maybe_resolve(ctx)

    append_event(
        ctx.log_path,
        turn_events.turn_record(
            game_uid=ctx.game_uid, turn=ctx.state.turn, event="message_received", sender=ctx.role,
            state_from=current, state_to=State.MY_TURN, envelope=move_envelope.to_dict(),
        ),
    )
    result = ctx.machine.attempt(State.MY_TURN)
    if not result.accepted:
        log_illegal(ctx, current, State.MY_TURN, result)
    return outcome
