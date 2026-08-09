"""Tests for `turn_resolve.py`'s D-66/SEC-07 additions: `record_action`'s
optional barrier and the shape-aware `decode_revealed_action`.
`record_action`/`maybe_resolve`'s pre-existing move-only behavior is
already exercised via test_orchestrator.py/test_orchestrator_loop.py per
that file's own house style (QUAL-02) -- not re-tested here.
"""

import dataclasses

from pursuit.network import move_payload, turn_resolve
from pursuit.sdk import engine
from pursuit.sdk.actions import barrier_cells
from tests.unit._fakes_agent import make_ctx


def test_decode_revealed_action_flat_payload_toggle_off(default_params):
    state = engine.make_state(default_params)
    dest = engine.legal_moves(state, "cop", default_params)[0]
    payload = move_payload.encode(state.cop, dest, move_payload.ActionKind.MOVE)

    ok, reason, move_cell, barrier_cell = turn_resolve.decode_revealed_action(
        payload, state.cop, state, default_params, composite=False,
    )

    assert ok and reason is None
    assert move_cell == dest
    assert barrier_cell is None


def test_decode_revealed_action_composite_move_only(default_params):
    state = engine.make_state(default_params)
    dest = engine.legal_moves(state, "cop", default_params)[0]
    payload = {"move": move_payload.encode(state.cop, dest, move_payload.ActionKind.MOVE), "barrier": None}

    ok, reason, move_cell, barrier_cell = turn_resolve.decode_revealed_action(
        payload, state.cop, state, default_params, composite=True,
    )

    assert ok and reason is None
    assert move_cell == dest
    assert barrier_cell is None


def test_decode_revealed_action_composite_with_a_legal_barrier(default_params):
    state = engine.make_state(default_params)
    cell = barrier_cells(state, default_params)[0]
    payload = {
        "move": move_payload.encode(state.cop, state.cop, move_payload.ActionKind.MOVE),
        "barrier": move_payload.encode(state.cop, cell, move_payload.ActionKind.BARRIER),
    }

    ok, reason, move_cell, barrier_cell = turn_resolve.decode_revealed_action(
        payload, state.cop, state, default_params, composite=True,
    )

    assert ok and reason is None
    assert move_cell == state.cop
    assert barrier_cell == cell


def test_decode_revealed_action_rejects_an_illegal_forged_barrier(default_params):
    """SEC-07: a barrier that fails is_legal (here: quota already
    exhausted) rejects the WHOLE turn, exactly like an illegal flat move."""
    state = engine.make_state(default_params)
    exhausted = dataclasses.replace(state, barriers_placed=default_params.barrier_quota)
    payload = {
        "move": move_payload.encode(state.cop, state.cop, move_payload.ActionKind.MOVE),
        "barrier": move_payload.encode(state.cop, state.cop, move_payload.ActionKind.BARRIER),
    }

    ok, reason, move_cell, barrier_cell = turn_resolve.decode_revealed_action(
        payload, state.cop, exhausted, default_params, composite=True,
    )

    assert not ok
    assert reason is not None
    assert move_cell is None
    assert barrier_cell is None


def test_record_action_builds_a_barrier_cop_action_never_both_fields(
    tmp_path, default_params, network_params,
):
    ctx = make_ctx(tmp_path, default_params, network_params, label="record-barrier")
    cell = barrier_cells(ctx.state, default_params)[0]

    turn_resolve.record_action(ctx, "police", ctx.state.cop, cell)

    assert ctx.pending_cop_action.is_barrier
    assert ctx.pending_cop_action.barrier == cell
    assert ctx.pending_cop_action.move is None
