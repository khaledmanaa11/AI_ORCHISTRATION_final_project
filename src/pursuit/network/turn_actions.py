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
150-line gate).

06-02 (D-58): the actual wire exchange (single MOVE, or the full
Commit-Ack-Reveal protocol) now lives behind `turn_commit.py` --
`take_my_turn` branches on `ctx.commit_state.pending_action`: None means
this side is the initiator this turn (decide now, call
`turn_commit.initiate`); set means this side already decided during its
own prior `await_opponent_turn` (D-58's responder path) and only reveals
now, via `turn_commit.reveal_pending`. `await_opponent_turn` always calls
`turn_commit.await_and_respond` in place of the old bare
`turn_buffer.await_move`.

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
from pursuit.network import turn_buffer, turn_commit, turn_events
from pursuit.network.event_log import append_event
from pursuit.network.orchestrator import AgentContext, engine_agent
from pursuit.network.state_machine import State
from pursuit.network.turn_buffer import HintProtocolError, log_illegal
from pursuit.network.turn_commit_send import technical_loss
from pursuit.network.turn_language import choose_destination, known_opponent_cell
from pursuit.network.turn_language_io import (
    compose_and_send_hint,
    decode_turn_hint,
    plan_turn_deception,
)
from pursuit.network.turn_resolve import decode_revealed_action, maybe_resolve, record_action
from pursuit.services.language_turn import turn_budget_seconds
from pursuit.shared.inference import NO_EVIDENCE


async def take_my_turn(ctx: AgentContext) -> Outcome | None:
    """One MY_TURN cycle. Branches on `ctx.commit_state.pending_action`:
    None -> decide now (initiator path); set -> already decided, reveal
    only (D-58 responder path). ctx.state changes only if this call also
    completes the pair (maybe_resolve). Entry is guarded symmetrically
    with `await_opponent_turn`'s own guarded entry: `attempt(MY_TURN)`
    fires only when the machine is not already there (D-09's repeatable
    cycle)."""
    current = ctx.machine.state
    if current is not State.MY_TURN:
        result = ctx.machine.attempt(State.MY_TURN)
        if not result.accepted:
            log_illegal(ctx, current, State.MY_TURN, result)
            return None

    if ctx.commit_state.pending_action is not None:
        pending = ctx.commit_state.pending_action
        record_action(ctx, ctx.role, pending.move, pending.barrier)
        outcome = maybe_resolve(ctx)
        result = await turn_commit.reveal_pending(ctx)
        if result is not None:
            return result
        # 05-06 (G1/G4). `outcome is None`: a resolved turn is over -- the
        # opponent will never play another, and composing costs an LLM
        # round trip (17.4 s of the 18 s inter-side divergence in the
        # 2026-08-13 round, measured within machine B's own clock).
        # `pending.turn`: the turn this action was actually committed and
        # REVEALED under. ctx.state.turn is wrong here -- maybe_resolve
        # above already advanced it N->N+1, which stamped every responder
        # hint one turn into the future.
        if ctx.language is not None and outcome is None:
            fresh_started = time.monotonic()
            budget_fresh = turn_budget_seconds(ctx.net)
            await compose_and_send_hint(
                ctx, pending.plan, pending.turn, fresh_started, budget_fresh,
                pending.regime, pending.incoming_log,
            )
        ctx.commit_state.pending_action = None
        ctx.machine.attempt(State.WAIT_OPPONENT)
        return outcome

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
    barrier = ctx.commit_state.chosen_barrier if agent == "cop" else None
    plan = plan_turn_deception(ctx, agent, pre_turn_state, dest) if ctx.language is not None else None
    record_action(ctx, ctx.role, dest, barrier)
    outcome = maybe_resolve(ctx)

    # `played_turn=pre_turn_state.turn` (08-05, deferred item #13). The SAME
    # pre-resolve snapshot the hint stamp below already uses, by the SAME rule,
    # threaded through `initiate` to the toggle-off MOVE send. `ctx.state.turn`
    # is the wrong number HERE for the same reason it was the wrong number for
    # the hint: `maybe_resolve` two lines up may already have advanced it.
    # `GameState` is `@dataclass(frozen=True)` and `maybe_resolve` REBINDS
    # `ctx.state`, so the snapshot captured above still holds the played turn.
    result = await turn_commit.initiate(
        ctx, current, pre_cell, dest, barrier, plan, played_turn=pre_turn_state.turn,
    )
    if result is not None:
        return result

    # Same `outcome is None` guard as the responder branch above -- stated
    # so the two branches read as one rule, not as an asymmetry someone
    # later "tidies away".
    #
    # 05-14 (G8): the turn stamp here used to be `ctx.state.turn`, on the
    # ground that "the initiator's own maybe_resolve is a no-op, so
    # ctx.state.turn IS the turn being played". That ground is a
    # PRECONDITION -- commit-reveal ON -- which was assumed rather than
    # written down, and it does not hold on the other supported path.
    # With `ctx.security.commit_reveal` false (`turn_commit.py:63-64`,
    # `:100-101` -- documented, toggle-off, byte-identical to
    # pre-Phase-6) `pending_action` is NEVER set, so BOTH sides arrive
    # through THIS branch; the second mover finds the opponent's slot
    # already filled by its own `await_opponent_turn`, the maybe_resolve
    # above advances N -> N+1, and the hint went out stamped one turn in
    # the FUTURE. That is the original G4 defect still live on that path,
    # and there it corrupts wire evidence SILENTLY rather than losing it:
    # a receiver's drop guard never fires for a future stamp, so nothing
    # anywhere records that the number is wrong (rule 20). Latent, not
    # active -- shipped config is `commit_reveal: true` -- and fixed
    # anyway, because a latent evidence defect on a supported toggle is
    # still a defect.
    #
    # `pre_turn_state` is captured above BEFORE record_action/maybe_resolve
    # -- the same discipline `await_opponent_turn`'s `observed_turn` keeps
    # -- so its turn is the turn ACTUALLY PLAYED on either path. The
    # responder branch's `pending.turn` is that same fact by that same
    # rule, which is what makes the two branches one rule and not two.
    if ctx.language is not None and outcome is None:
        await compose_and_send_hint(
            ctx, plan, pre_turn_state.turn, started, budget, regime, incoming_log,
        )
    ctx.machine.attempt(State.WAIT_OPPONENT)
    return outcome


async def await_opponent_turn(ctx: AgentContext) -> Outcome | None:
    """One WAIT_OPPONENT cycle: bound the inbound wait (NET-06) via
    `turn_commit.await_and_respond` (D-58 -- delegates straight to
    `turn_buffer.await_move` when the toggle is off), decode and validate
    the opponent's revealed action -- shape-aware (D-66): the flat
    pre-Phase-6 payload off, the D-59 composite `{move, barrier}` dict on
    -- buffer it, hand off to MY_TURN. A hint encountered along the way is
    buffered but never required. ctx.state changes only if this call also
    completes the pair (maybe_resolve)."""
    if ctx.machine.state is State.HANDSHAKE:
        ctx.machine.attempt(State.WAIT_OPPONENT)  # design note 7: thief's first wait
    current = ctx.machine.state

    try:
        move_envelope, verdict = await turn_commit.await_and_respond(ctx)
        if verdict is None:
            turn_buffer.drain_trailing_hint(ctx)
    except HintProtocolError as exc:
        return turn_buffer.reject_peer_payload(ctx, reason=str(exc))

    if verdict is not None:
        # Was an inline copy of turn_commit_send.technical_loss, byte-for-byte
        # (same record, same GAME_OVER attempt, same return) -- extracted per
        # the no-duplication rule rather than kept as a second copy.
        return technical_loss(ctx, verdict)

    agent = engine_agent(move_envelope.sender)
    pre_cell = ctx.state.cop if agent == "cop" else ctx.state.thief
    # Captured BEFORE record_action/maybe_resolve: maybe_resolve advances
    # ctx.state.turn, and this is the join key the Final-Reveal audit
    # indexes the opponent's REVEAL on. It must be the turn the action was
    # actually played for, and it must be OUR number, not the peer's
    # declared move_envelope.turn (06-UAT.md Gap 1).
    observed_turn = ctx.state.turn
    ok, reason, move_cell, barrier_cell = decode_revealed_action(
        move_envelope.payload, pre_cell, ctx.state, ctx.params, composite=ctx.security.commit_reveal,
    )
    if not ok:
        return turn_buffer.reject_peer_payload(ctx, reason=reason)
    record_action(ctx, move_envelope.sender, move_cell, barrier_cell)
    outcome = maybe_resolve(ctx)

    append_event(
        ctx.log_path,
        turn_events.turn_record(
            game_uid=ctx.game_uid, turn=observed_turn, event="message_received", sender=ctx.role,
            state_from=current, state_to=State.MY_TURN, envelope=move_envelope.to_dict(),
        ),
    )
    result = ctx.machine.attempt(State.MY_TURN)
    if not result.accepted:
        log_illegal(ctx, current, State.MY_TURN, result)
    return outcome
