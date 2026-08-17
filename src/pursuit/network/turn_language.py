"""Figure 7 assembly (book Sec6.2, p.43/PDF 59) -- the SYNC decision-shaping
helpers `turn_actions.py` calls between the two AWAITED language calls
(`services/language_turn.py`). Deviation (Rule 3 - blocking, not in
04-12-PLAN.md's `files_modified`): keeps `turn_actions.py` under the
150-code-line gate once it also orchestrates decode/decide/plan/compose.

Nothing here touches the network or awaits anything -- it only shapes the
inputs `BeliefAdapter.decide()` / `strategy.deception.plan_deception()` need
from an `AgentContext`, and reads back what they produced for the JSONL
event (rules 8-9: only what THIS peer believed/observed).
"""

from __future__ import annotations

from dataclasses import replace

from pursuit.network.brain_wiring import inner_brain
from pursuit.network.orchestrator import AgentContext, Coord, first_legal_move
from pursuit.shared.deception_types import DeceptionPlan
from pursuit.shared.inference import Inference
from pursuit.strategy import scent_check
from pursuit.strategy.base import Observation
from pursuit.strategy.belief import BeliefMap
from pursuit.strategy.beliefadapter import BeliefAdapter
from pursuit.strategy.deception import plan_deception

_OPPONENT_ENGINE_ROLE = {"cop": "thief", "thief": "cop"}


def opponent_wire_role(role: str) -> str:
    """The opponent's role.json vocabulary name ("police"/"thief") -- the
    key `ctx.incoming_hints`/`pending_*` are buffered under, distinct from
    the engine's "cop"/"thief" (`orchestrator.engine_agent`)."""
    return "thief" if role == "police" else "police"


def known_opponent_cell(ctx: AgentContext, agent: str) -> Coord | None:
    """D-48's regime decision, in one place, logged per turn (Task 2).

    Cop moves first each cycle (design note 7): by the time `take_my_turn`
    runs again, `ctx.state.<opponent>` already reflects the opponent's
    LAST revealed move (folded in by `turn_resolve.maybe_resolve` in cop's
    own prior `await_opponent_turn`) -- Regime A, one turn behind (D-48) --
    except turn 0, where nothing has been revealed yet at all (Regime B,
    honestly, for exactly that one turn).

    Thief (06-02, D-58 revision): the responder now decides its own move
    the MOMENT the initiator's commit hash arrives -- before the
    initiator's current-turn action is ever revealed, only the hash has
    been seen. `ctx.pending_cop_action` is therefore still None at this
    decide-now point on EVERY turn, not just turn 0: Regime A no longer
    holds for the thief at all under commit-reveal. This closes a real
    blindness leak that pre-Phase-6 code had (the thief's decide step used
    to run only after a full prior `await_opponent_turn` had already
    filled `ctx.pending_cop_action`), rather than being a regression."""
    if agent == "cop":
        return ctx.state.thief if ctx.state.turn > 0 else None
    return ctx.pending_cop_action.move if ctx.pending_cop_action is not None else None


def choose_destination(
    ctx: AgentContext, agent: str, inference: Inference, known_cell: Coord | None
) -> Coord:
    """Move choice: `choose_move` (tests/training override) wins outright;
    otherwise the registry-built `brain` (BeliefAdapter-wrapped or raw);
    otherwise Phase 2's `first_legal_move` placeholder. `known_cell` is the
    SAME regime value the caller already computed via `known_opponent_cell`
    (Task 2: "the decision lives in one place") -- never recomputed here,
    since `record_action`/`maybe_resolve` may run between this call and a
    later one and change what `known_opponent_cell` would answer.

    D-66: every branch that CAN produce a barrier (BeliefAdapter, or a raw
    brain's own `_decide_move`) has its full `Decision` inspected before
    only `.move` is returned -- `ctx.commit_state.chosen_barrier` is set
    unconditionally on every call (None on the override/placeholder
    branches, which never carry a barrier by construction), so a later
    caller in the SAME turn can read it. Never left stale across turns."""
    pre_cell = ctx.state.cop if agent == "cop" else ctx.state.thief
    if ctx.choose_move is not None:
        ctx.commit_state.chosen_barrier = None
        return ctx.choose_move(ctx.state, agent, ctx.params)
    if ctx.brain is None:
        ctx.commit_state.chosen_barrier = None
        return first_legal_move(ctx.state, agent, ctx.params)
    if isinstance(ctx.brain, BeliefAdapter):
        decision = ctx.brain.decide(
            ctx.state, inference, ctx.scent_field, ctx.rules, known_cell=known_cell
        )
    else:
        opponent_cell = ctx.state.thief if agent == "cop" else ctx.state.cop
        obs = Observation(
            own_cell=pre_cell, target_cell=opponent_cell, blocked_mask=0,
            barriers_used=ctx.state.barriers_placed, turn_index=ctx.state.turn,
        )
        decision = ctx.brain._decide_move(obs, ctx.state)  # noqa: SLF001 (BrainBase's own seam)
    ctx.commit_state.chosen_barrier = decision.barrier
    return decision.move


def build_deception_plan(
    ctx: AgentContext, agent: str, pre_turn_state, dest: Coord
) -> DeceptionPlan:
    """The claim for this turn, decided AFTER the move (must_haves: "a lie
    that contradicts our own action is not deception, it is noise") --
    `claim_state` substitutes the JUST-CHOSEN destination for our own cell,
    regardless of whether `resolve_turn` has run yet, so the claim always
    reflects the move actually committed to."""
    claim_state = replace(pre_turn_state, **{agent: dest})
    if isinstance(ctx.brain, BeliefAdapter):
        belief = ctx.brain.belief
    else:
        belief = BeliefMap(ctx.params.board_size, _OPPONENT_ENGINE_ROLE[agent])
    weights = getattr(inner_brain(ctx.brain), "weights", None) if ctx.brain is not None else None
    return plan_deception(
        agent, claim_state, ctx.params, belief, ctx.language.deception_rng,
        ctx.language.deception_config, scent=ctx.scent_field, weights=weights,
    )


def observe_reliability(ctx: AgentContext, inference: Inference) -> None:
    """04-09 carry-over F/Q: `contradicts()` then `.observe()` on the
    adapter's OWN `Reliability`, once per turn a hint TEXT arrived (a
    schema-invalid/empty decode still counts -- `contradicts()` itself
    scores an untestable claim 0.0, never crashes on it)."""
    if not isinstance(ctx.brain, BeliefAdapter):
        return
    score = scent_check.contradicts(
        inference, ctx.scent_field, ctx.brain.scent_model, ctx.brain.belief_config
    )
    ctx.brain.reliability.observe(score)


def belief_snapshot(ctx: AgentContext) -> tuple[float | None, Coord | None, float | None]:
    """(entropy, argmax, reliability) for the JSONL log -- all None when
    belief is disabled this game (an honest "not run"), never fabricated."""
    if not isinstance(ctx.brain, BeliefAdapter):
        return None, None, None
    return (
        ctx.brain.belief.entropy(),
        ctx.brain.belief.argmax(),
        ctx.brain.reliability.value,
    )
