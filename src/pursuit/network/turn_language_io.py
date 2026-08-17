"""The AWAITED language stages of a turn -- split out of turn_actions.py at
the 150-code-line gate (Segal Table 5, deviation, 04-12).

`decode_turn_hint` is Figure 7 stage 1. `plan_turn_deception` (06-02) is
stage 3 alone -- a thin wrapper calling the BARE `build_deception_plan`
name from THIS module's own namespace (never a direct
`turn_language.build_deception_plan(...)` reference), so a test that
monkeypatches `turn_language_io.build_deception_plan` (GATE-4's own spy
technique) keeps intercepting it regardless of which outer function
(`turn_actions.take_my_turn`, or `turn_commit`'s responder decide-now
step) calls this wrapper -- bare names resolve through the enclosing
MODULE's globals at call time, not at def time. `compose_and_send_hint`
(06-02, replacing `send_turn_hint`) is stages 4-5 (compose -> send -> log)
ALONE -- planning is split out because D-58 needs the responder to plan
BEFORE it commits, but only compose the actual TEXT after the reveal
round trip (a real network gap now sits between the two, where before
they were back-to-back sync calls). Both stages are guarded by
`services/language_turn.py`'s timeout policy -- neither can stall a turn
past the configured budget (Task 1).
"""

from __future__ import annotations

import dataclasses
import time

from pursuit.network import turn_buffer, turn_events, turn_hint_store
from pursuit.network.event_log import append_event
from pursuit.network.hint_payload import HintKey
from pursuit.network.orchestrator import AgentContext
from pursuit.network.turn_language import (
    belief_snapshot,
    build_deception_plan,
    observe_reliability,
    opponent_wire_role,
)
from pursuit.services.language_turn import (
    MIN_CALL_BUDGET_SECONDS,
    compose_outgoing,
    decode_incoming,
)
from pursuit.shared.deception_types import DeceptionPlan
from pursuit.shared.inference import NO_EVIDENCE, Inference


def _no_hint_log() -> dict:
    """A fresh "nothing arrived" log dict per call -- never a shared
    module-level literal (NET-02 discipline)."""
    return {"text": None, "outcome": "no_hint", "reason": "no hint received this turn"}


async def decode_turn_hint(
    ctx: AgentContext, started: float, budget: float
) -> tuple[Inference, dict]:
    """Stage 1: decode the opponent's hint, if any is cached (turn_buffer's
    `record_hint`), abandoning at whatever budget remains. Returns
    (inference, log_dict); also drives the reliability update (04-09
    carry-over F) when a hint genuinely arrived.

    05-14 (G8): the pop goes through `turn_hint_store.consume_hint`, which
    performs the SAME pop and additionally leaves what it took in
    `ctx.pending_hints` as the consumed marker -- so a re-sent hint cannot
    drive `observe_reliability` and the belief update a second time on
    evidence already spent. This is the one place in the codebase that
    spends an inbound hint, which is why it is the one place that may
    mark it spent; the buffers' own invariants stay in the module that
    owns them.

    `no_hint` continues to mean exactly one thing -- nothing was in the
    buffer -- and that branch still sits UPSTREAM of every provider and
    key concern, which is what makes it usable as evidence about the
    receive window rather than about the API key."""
    payload = turn_hint_store.consume_hint(ctx, opponent_wire_role(ctx.role))
    text = payload.get(HintKey.TEXT.value) if payload else None
    if text is None:
        return NO_EVIDENCE, _no_hint_log()
    remaining = max(0.0, budget - (time.monotonic() - started))
    inference = await decode_incoming(text, ctx.language.decode_context, timeout=remaining)
    observe_reliability(ctx, inference)
    outcome = "evidence" if inference.is_evidence else "no_evidence"
    reason = None if inference.is_evidence else "hint decoded to no evidence"
    if remaining < MIN_CALL_BUDGET_SECONDS:
        outcome, reason = "skipped", "insufficient turn budget"
    return inference, {"text": text, "outcome": outcome, "reason": reason}


def plan_turn_deception(ctx: AgentContext, agent: str, pre_turn_state, dest) -> DeceptionPlan:
    """Stage 3 alone (06-02 split -- see module docstring): calls the bare
    `build_deception_plan` name from this module's own globals."""
    return build_deception_plan(ctx, agent, pre_turn_state, dest)


async def compose_and_send_hint(
    ctx: AgentContext, plan: DeceptionPlan, turn: int,
    started: float, budget: float, regime: str, incoming_log: dict,
) -> None:
    """Stages 4-5: compose -> send -> log (`plan` already decided by the
    caller, per D-58). `dataclasses.replace` refreshes
    `BluffContext.degrade_level` from the gatekeeper's OWN budget (04-10
    carry-over K) -- the only field that goes stale mid-game."""
    remaining = max(0.0, budget - (time.monotonic() - started))
    bluff_context = dataclasses.replace(
        ctx.language.bluff_context, degrade_level=ctx.language.gatekeeper.budget.level
    )
    text = await compose_outgoing(plan, bluff_context, timeout=remaining)
    await turn_buffer.send_hint(ctx, turn, text=text, intent=plan.intent)
    # 07-06 (D-76, closing D7-7's zero-caller finding): the live sidebar's
    # hint log is one peer's WHOLE conversation, so our own outgoing hint is
    # recorded here -- after it actually went out, never before. Its intent
    # flag is the one entry in that log that is a fact rather than a claim.
    ctx.view_history.record_outgoing(turn=turn, text=text, intent=plan.intent.value)

    entropy, argmax, reliability = belief_snapshot(ctx)
    append_event(
        ctx.log_path,
        turn_events.language_turn_record(
            game_uid=ctx.game_uid, turn=turn, sender=ctx.role, regime=regime,
            belief_entropy=entropy, belief_argmax=argmax, reliability=reliability,
            token_spend=ctx.language.gatekeeper.budget.report(),
            incoming=incoming_log, outgoing={"text": text, "intent": plan.intent.value},
        ),
    )
