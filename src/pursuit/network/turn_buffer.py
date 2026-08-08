"""Per-turn helpers split out of turn_actions.py at the 150-code-line gate
(Segal Table 5): the D-11 illegal-transition log line, and the joint-turn
action buffer (RULES-RESOLUTION.md) that lets take_my_turn/await_opponent_turn
each record one side's action and resolve exactly once when both are known.
"""

from __future__ import annotations

from pursuit.constants import Outcome
from pursuit.network import turn_events
from pursuit.network.event_log import append_event
from pursuit.network.orchestrator import AgentContext, Coord
from pursuit.network.state_machine import State, TransitionResult
from pursuit.sdk import engine
from pursuit.sdk.actions import CopAction


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
    engine.resolve_turn exactly once (RULES-RESOLUTION.md Sec1)."""
    if ctx.pending_cop_action is None or ctx.pending_thief_move is None:
        return None
    ctx.state, outcome = engine.resolve_turn(
        ctx.state, ctx.pending_cop_action, ctx.pending_thief_move, ctx.params, ctx.rules
    )
    ctx.pending_cop_action = None
    ctx.pending_thief_move = None
    return outcome
