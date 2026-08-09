"""The joint-turn action buffer (RULES-RESOLUTION.md) -- split out of
turn_buffer.py at the 150-code-line gate (Segal Table 5, deviation, 04-12:
turn_buffer.py grew past the ceiling once `record_hint`/`maybe_resolve`
gained the 04-12 hint-cache/scent-advance responsibilities). Lets
take_my_turn/await_opponent_turn each record one side's action and resolve
exactly once when both are known.

06-02 (D-66, SEC-07): `record_action` gains an optional `barrier`, open
for the first time to the cop's real barrier placement -- previously
always discarded before it ever reached the wire. `decode_revealed_action`
is the shape-aware receive-side helper `await_opponent_turn` calls: the
flat pre-Phase-6 payload (toggle off) or the D-59/D-66 composite
`{move, barrier}` dict (toggle on, decoding BOTH sub-keys through the
SAME move_payload.decode/is_legal branches an illegal flat move already
used -- the BARRIER branch is already shipped, quota enforced via
barrier_cells).
"""

from __future__ import annotations

from pursuit.constants import Outcome
from pursuit.network import move_payload
from pursuit.network.orchestrator import AgentContext, Coord
from pursuit.sdk import engine
from pursuit.sdk.actions import CopAction
from pursuit.shared.config import GameParams
from pursuit.shared.state import GameState


def record_action(ctx: AgentContext, role: str, dest: Coord, barrier: Coord | None = None) -> None:
    """Store this turn's action into the joint-turn buffer slot for *role*.

    For the cop, `barrier` (D-66) and `dest` are move-XOR-barrier, matching
    `CopAction.__post_init__`'s own invariant -- NEVER `CopAction(move=dest,
    barrier=barrier)` with both set. The thief never places a barrier
    (Decision's own contract); `barrier` is accepted for signature symmetry
    only and always ignored for that role."""
    if role == "police":
        ctx.pending_cop_action = CopAction(barrier=barrier) if barrier is not None else CopAction(move=dest)
    else:
        ctx.pending_thief_move = dest


def decode_revealed_action(
    payload: dict, pre_cell: Coord, state: GameState, params: GameParams, *, composite: bool,
) -> tuple[bool, str | None, Coord | None, Coord | None]:
    """Decode + validate one opponent's revealed action off the wire.

    `composite=False` (toggle off) decodes the flat pre-Phase-6 shape,
    unchanged. `composite=True` decodes the D-59 `{move, barrier}` action
    dict: the `move` sub-key ALWAYS through the same decode/is_legal branch
    as today (a "stay" token when a barrier was placed, mirroring
    `CopAction.destination()`'s own "unchanged when placing"); the
    `barrier` sub-key -- when present -- through the ALREADY-SHIPPED
    BARRIER decode/is_legal branch. Either part failing legality rejects
    the WHOLE turn for the sender, matching an illegal flat move today.

    Returns (ok, reason, move_cell, barrier_cell): move_cell/barrier_cell
    are None when ok is False; barrier_cell is None on a legal move-only
    turn even when ok is True."""
    move_part = payload.get("move") if composite else payload
    resolved_move = move_payload.decode(move_part, pre_cell, params)
    if not (resolved_move.ok and move_payload.is_legal(pre_cell, resolved_move, state, params)):
        reason = resolved_move.reason or f"{resolved_move.cell} is not a legal action"
        return False, reason, None, None
    if not composite or payload.get("barrier") is None:
        return True, None, resolved_move.cell, None

    resolved_barrier = move_payload.decode(payload["barrier"], pre_cell, params)
    if not (resolved_barrier.ok and move_payload.is_legal(pre_cell, resolved_barrier, state, params)):
        reason = resolved_barrier.reason or f"{resolved_barrier.cell} is not a legal barrier"
        return False, reason, None, None
    return True, None, resolved_move.cell, resolved_barrier.cell


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
