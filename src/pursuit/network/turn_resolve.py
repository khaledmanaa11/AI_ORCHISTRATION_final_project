"""The joint-turn action buffer (RULES-RESOLUTION.md) -- split out of
turn_buffer.py at the 150-code-line gate (Segal Table 5, deviation, 04-12:
turn_buffer.py grew past the ceiling once `record_hint`/`maybe_resolve`
gained the 04-12 hint-cache/scent-advance responsibilities). Lets
take_my_turn/await_opponent_turn each record one side's action and resolve
exactly once when both are known.
"""

from __future__ import annotations

from pursuit.constants import Outcome
from pursuit.network.orchestrator import AgentContext, Coord
from pursuit.sdk import engine
from pursuit.sdk.actions import CopAction


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
    buffer is cleared too -- it belonged to the turn that just ended.

    04-12 (RESUME.md carry-over S): a joint turn just resolved is exactly
    the "once per joint turn, after resolve_turn" moment `ScentField.advance`
    requires -- called here, centrally, so neither take_my_turn nor
    await_opponent_turn has to duplicate the "did resolution just fire"
    check to find it."""
    if ctx.pending_cop_action is None or ctx.pending_thief_move is None:
        return None
    ctx.state, outcome = engine.resolve_turn(
        ctx.state, ctx.pending_cop_action, ctx.pending_thief_move, ctx.params, ctx.rules
    )
    if ctx.scent_field is not None:
        ctx.scent_field.advance()
    ctx.pending_cop_action = None
    ctx.pending_thief_move = None
    ctx.pending_hints = {}
    return outcome
