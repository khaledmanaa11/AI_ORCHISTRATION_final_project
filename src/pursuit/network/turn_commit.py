"""D-58: the both-locked Commit -> Acknowledge -> Reveal exchange (book
Sec5.3.2, SEC-01..04, SEC-07) -- the three PUBLIC entry points
`take_my_turn`/`await_opponent_turn` (turn_actions.py) drive. Wire
mechanics split into two siblings (150-line gate, pre-authorized):
`turn_commit_wait.py` (wait loops, the shared commit+ledger helper) and
`turn_commit_send.py` (push/log/technical-loss mechanics -- a third
split beyond the two pre-authorized files, forced by the line count).
This module keeps ONLY the three public entry points and policy.

Deadlock-freedom (traced): COMMIT_A -> responder decides+commits+sends
COMMIT_B+ACK_A, unconditional on anything the initiator has not already
sent -> initiator (inside `initiate`) receives COMMIT_B, ACKs it, reveals
REVEAL_A -- gated only on what the responder's step already satisfied ->
initiator's own `await_and_respond` call waits only for REVEAL_B (Rule 1
bug fix -- see that function's own docstring) -> responder's own
`reveal_pending` waits only for ACK_B, already sent above, then reveals
REVEAL_B. Every wait is satisfied by an earlier step in this chain.

`ctx.security.commit_reveal is False` bypasses the whole exchange, byte-
identically to pre-Phase-6, on all three entry points.
"""

from __future__ import annotations

import time

from pursuit.constants import Outcome
from pursuit.network import turn_buffer
from pursuit.network.agent_context import AgentContext, Coord
from pursuit.network.commit_state import PendingAction
from pursuit.network.envelope import Envelope, MessageType
from pursuit.network.orchestrator import engine_agent
from pursuit.network.state_machine import State
from pursuit.network.turn_commit_send import (
    send_and_log,
    send_move_only,
    technical_loss,
)
from pursuit.network.turn_commit_wait import (
    H_COMMIT_KEY,
    commit_own_action,
    wait_for_ack_and_commit,
    wait_for_matching_ack,
    wait_for_opponent_commit,
)
from pursuit.network.turn_commit_wait_reveal import wait_for_reveal_capturing_early_ack
from pursuit.network.turn_language import choose_destination, known_opponent_cell
from pursuit.network.turn_language_io import decode_turn_hint, plan_turn_deception
from pursuit.network.verdict import TechnicalWin
from pursuit.services.language_turn import turn_budget_seconds
from pursuit.shared.deception_types import Intent
from pursuit.shared.inference import NO_EVIDENCE


async def initiate(
    ctx: AgentContext, current: State, pre_cell: Coord, dest: Coord,
    barrier: Coord | None, plan: object | None, *, played_turn: int,
) -> Outcome | None:
    """D-58 initiator path (police, design note 7's "sends first"): commit
    -> send COMMIT -> wait for BOTH our own ACK and the opponent's COMMIT
    (ACKing theirs the instant it arrives) -> send REVEAL."""
    # *played_turn* (08-05, deferred item #13) is the turn the caller actually
    # played this action on, captured BEFORE its own `record_action`/
    # `maybe_resolve`. It is consumed by the TOGGLE-OFF branch below and by
    # nothing else. Required and keyword-only: a default would let the next
    # caller reintroduce #13 by omission, which is how this one survived 05-14,
    # the plan that fixed its twin on the hint channel one line away.
    #
    # THE COMMIT-REVEAL-ON PATH BELOW IS DELIBERATELY UNTOUCHED. `turn` is still
    # `ctx.state.turn`, read at the same point, and it is that value -- never
    # `played_turn` -- that feeds `commit_own_action`'s D-59 hash input and the
    # D-64 ledger join key. On this path the two are provably equal (with the
    # toggle ON the responder never calls `record_action`, so the initiator's own
    # `maybe_resolve` cannot fire and `ctx.state.turn` cannot have advanced), but
    # "provably equal" is an argument and byte-identity is a fact. A rules-19/22
    # technical loss is what a wrong number here costs, so the repair takes the
    # fact: MEASURED before and after on a nonce-pinned ON-path drive, the same
    # three pushes at turns [0,0,0], the same h_commit 6a34ee5c..., the same
    # single ledger record at turn 0, one identical fingerprint.
    # `tests/unit/test_shipped_path_turn_source.py` pins both halves structurally.
    if not ctx.security.commit_reveal:
        return await send_move_only(ctx, current, pre_cell, dest, played_turn)

    intent = plan.intent.value if plan is not None else Intent.TRUTH.value
    turn = ctx.state.turn
    h_commit, action_payload = commit_own_action(
        ctx, pre_cell=pre_cell, dest=dest, barrier=barrier, intent=intent, turn=turn,
    )

    verdict = await send_and_log(
        ctx, MessageType.COMMIT, turn, {H_COMMIT_KEY: h_commit},
        state_from=current, state_to=State.WAIT_OPPONENT,
    )
    if verdict is not None:
        return technical_loss(ctx, verdict)

    _opponent_h_commit, verdict = await wait_for_ack_and_commit(ctx, h_commit, turn, current)
    if verdict is not None:
        return technical_loss(ctx, verdict)

    verdict = await send_and_log(
        ctx, MessageType.REVEAL, turn, action_payload, state_from=current, state_to=State.WAIT_OPPONENT,
    )
    if verdict is not None:
        return technical_loss(ctx, verdict)
    return None


async def await_and_respond(ctx: AgentContext) -> tuple[Envelope | None, TechnicalWin | None]:
    """`await_opponent_turn`'s D-58 wait -- branches on role (Rule 1 bug
    fix, see module docstring): police already committed+revealed THIS
    turn inside `initiate`, so only the opponent's REVEAL is left to
    await. Thief has decided nothing yet: decide now, commit+send our
    own COMMIT, ACK theirs, wait for their REVEAL -- NEVER record_action/
    maybe_resolve here (`CommitTurnState`'s own docstring); only
    `pending_action` is set, consumed later by `reveal_pending`. Off:
    `turn_buffer.await_move(ctx)` verbatim, either way.

    BOTH branches now end in the SAME leg, `wait_for_reveal_capturing_early_ack`
    -- 05-18, deferred item #18. What differs is only whether this side has
    an outstanding commit for that leg to capture an ACK for."""
    if not ctx.security.commit_reveal:
        return await turn_buffer.await_move(ctx)
    if ctx.role == "police":
        # THE FIX (05-18, deferred item #18). This was
        # `return await next_protocol_message(ctx)` -- the pull primitive
        # called BARE, the only wait in the codebase with no type test, and
        # the only production caller of that primitive still taking
        # `on_attempt=None`. Whatever arrived was handed to
        # `turn_actions.await_opponent_turn` as the opponent's REVEAL, so a
        # peer's published FINAL_REVEAL was decoded as an illegal move.
        # MEASURED at `da45b55`, police, queue [FINAL_REVEAL, REVEAL]:
        #
        #     returned type = final_reveal   verdict = None
        #     await_opponent_turn outcome = Outcome.TECHNICAL_LOSS
        #     technical_win reasons = ['payload must be a dict, got NoneType']
        #
        # A false declaration against an honest peer (rules 16/22), and a
        # 0-point loss of a game we did not lose.
        #
        # `None` = we hold no outstanding commit: `initiate` already
        # collected this turn's ACK inside `wait_for_ack_and_commit`.
        #
        # THE DECISION, and the alternative was RUN, not argued. "Keep
        # waiting" versus "treat the peer's FINAL_REVEAL as the end of the
        # game", measured against this same turn loop and `run_final_audit`:
        #
        #   scenario                        keep waiting        end the game
        #   ledger, then the REVEAL         None, no accusation AttributeError
        #                                                       (returning no
        #                                                       envelope) or a
        #                                                       FABRICATED
        #                                                       technical_win
        #                                                       against a peer
        #                                                       that just spoke
        #   ledger, no REVEAL ever          technical_loss      technical_loss
        #                                   opponent_unresponsive  same, on
        #                                                       fabricated
        #                                                       evidence
        #   genuinely silent peer (rule 36) unchanged           unchanged
        #
        # Ending the game has no truthful expression here. This function
        # returns `(Envelope | None, TechnicalWin | None)`; `(None, None)`
        # makes `await_opponent_turn` raise `AttributeError: 'NoneType'
        # object has no attribute 'sender'`, and the only other door is to
        # build a `TechnicalWin` by hand -- whose own docstring says every
        # field is MEASURED by the retry ladder, "never assumed or
        # defaulted", precisely so the declaration is defensible at audit.
        #
        # Waiting costs nothing that is not already owed. The ledger is
        # already safe in `ctx.commit_state.early_final_reveal` (05-17), so
        # the audit matches either way; the REVEAL is normally the very next
        # item on the queue; and a peer that really has stopped exhausts the
        # ladder below and earns D-13's own measured `opponent_unresponsive`
        # -- NET-06's in-game sanction, untouched. No timeout, retry count or
        # backoff moves: 05-17 measured the timing fix directly and widening
        # the ladder to 21 attempts produced a BYTE-IDENTICAL accusation.
        return await wait_for_reveal_capturing_early_ack(ctx, None)

    current = ctx.machine.state
    # Captured BEFORE the wait and reused as this turn's single local
    # authority: it is the log join key for the opponent's COMMIT (Gap 1)
    # and the turn this side commits+reveals under. ctx.state cannot
    # advance in between -- nothing here calls record_action/maybe_resolve.
    turn = ctx.state.turn
    opponent_h_commit, verdict = await wait_for_opponent_commit(ctx, current, turn)
    if verdict is not None:
        return None, verdict

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

    intent = plan.intent.value if plan is not None else Intent.TRUTH.value
    h_commit, action_payload = commit_own_action(
        ctx, pre_cell=pre_cell, dest=dest, barrier=barrier, intent=intent, turn=turn,
    )
    ctx.commit_state.pending_action = PendingAction(
        move=dest, barrier=barrier, plan=plan, incoming_log=incoming_log, regime=regime,
        action_payload=action_payload, h_commit=h_commit, turn=turn,
    )

    verdict = await send_and_log(
        ctx, MessageType.COMMIT, turn, {H_COMMIT_KEY: h_commit}, state_from=current, state_to=current,
    )
    if verdict is not None:
        return None, verdict
    verdict = await send_and_log(
        ctx, MessageType.ACK, turn, {H_COMMIT_KEY: opponent_h_commit}, state_from=current, state_to=current,
    )
    if verdict is not None:
        return None, verdict

    return await wait_for_reveal_capturing_early_ack(ctx, h_commit)


async def reveal_pending(ctx: AgentContext) -> Outcome | None:
    """D-58 responder's own later take_my_turn: already decided -- wait
    for our own commit's ACK if it hasn't already arrived, reveal from
    the stash, never decide again. Does NOT clear `pending_action` itself
    -- `take_my_turn` clears it after using its other fields for the
    hint."""
    current = ctx.machine.state
    pending = ctx.commit_state.pending_action

    if not ctx.commit_state.own_ack_received:
        verdict = await wait_for_matching_ack(ctx, pending.h_commit)
        if verdict is not None:
            return technical_loss(ctx, verdict)
    ctx.commit_state.own_ack_received = False

    verdict = await send_and_log(
        ctx, MessageType.REVEAL, pending.turn, pending.action_payload,
        state_from=current, state_to=State.WAIT_OPPONENT,
    )
    if verdict is not None:
        return technical_loss(ctx, verdict)
    return None
