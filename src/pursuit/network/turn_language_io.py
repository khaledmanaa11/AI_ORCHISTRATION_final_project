"""The two AWAITED language stages of a turn -- split out of
turn_actions.py at the 150-code-line gate (Segal Table 5, deviation, 04-12).

`decode_turn_hint` is Figure 7 stage 1 (in `_decode_turn_hint`'s own former
name); `send_turn_hint` is stages 3-5 (plan -> compose -> send -> log).
Both are guarded by `services/language_turn.py`'s timeout policy -- neither
can stall a turn past the configured budget (Task 1).
"""

from __future__ import annotations

import dataclasses
import time

from pursuit.network import turn_buffer, turn_events
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
    carry-over F) when a hint genuinely arrived."""
    payload = ctx.incoming_hints.pop(opponent_wire_role(ctx.role), None)
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


async def send_turn_hint(
    ctx: AgentContext, agent: str, pre_turn_state, dest, turn: int,
    started: float, budget: float, regime: str, incoming_log: dict,
) -> None:
    """Stages 3-5: plan -> compose -> send -> log. `dataclasses.replace`
    refreshes `BluffContext.degrade_level` from the gatekeeper's OWN budget
    (04-10 carry-over K) -- the only field that goes stale mid-game."""
    plan = build_deception_plan(ctx, agent, pre_turn_state, dest)
    remaining = max(0.0, budget - (time.monotonic() - started))
    bluff_context = dataclasses.replace(
        ctx.language.bluff_context, degrade_level=ctx.language.gatekeeper.budget.level
    )
    text = await compose_outgoing(plan, bluff_context, timeout=remaining)
    await turn_buffer.send_hint(ctx, turn, text=text, intent=plan.intent)

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
