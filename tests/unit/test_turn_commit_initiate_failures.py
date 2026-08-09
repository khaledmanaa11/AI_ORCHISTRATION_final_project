"""Technical-loss branch coverage for `turn_commit.initiate` (D-58's
initiator path) -- fake-driven, no real network. Split from
test_turn_commit.py at the 150-code-line gate: these share the "an
opponent that goes silent partway through" shape, distinct from that
file's own happy-path/toggle-off/jitter tests.
"""

from __future__ import annotations

import asyncio

from pursuit.constants import Outcome
from pursuit.network import turn_commit
from pursuit.network.envelope import Envelope, MessageType
from pursuit.network.state_machine import State
from pursuit.sdk import engine
from pursuit.shared.security_config import SecurityParams
from tests.unit._fakes_agent import FailAfterClient, FakeClient, make_ctx
from tests.unit.test_turn_commit import _pump

_ON = SecurityParams(version="1.00", commit_reveal=True, team_code="khm-mn17")


async def test_initiate_reports_technical_loss_when_the_commit_push_fails(
    tmp_path, default_params, network_params,
):
    ctx = make_ctx(
        tmp_path, default_params, network_params, role="police", label="init-commit-fail",
        security=_ON, client=FakeClient(fail=True), initial_state=State.MY_TURN,
    )
    current = ctx.machine.state
    dest = engine.legal_moves(ctx.state, "cop", default_params)[0]

    result = await turn_commit.initiate(ctx, current, ctx.state.cop, dest, None, None)

    assert result is Outcome.TECHNICAL_LOSS
    assert ctx.machine.state is State.GAME_OVER


async def test_initiate_reports_technical_loss_when_the_opponent_never_answers(
    tmp_path, default_params, network_params,
):
    """COMMIT push succeeds, but nothing ever arrives afterward --
    wait_for_ack_and_commit's own retry ladder exhausts."""
    ctx = make_ctx(
        tmp_path, default_params, network_params, role="police", label="init-wait-fail",
        security=_ON, initial_state=State.MY_TURN,
    )
    current = ctx.machine.state
    dest = engine.legal_moves(ctx.state, "cop", default_params)[0]

    result = await turn_commit.initiate(ctx, current, ctx.state.cop, dest, None, None)

    assert result is Outcome.TECHNICAL_LOSS
    assert ctx.machine.state is State.GAME_OVER


async def test_initiate_reports_technical_loss_when_acking_the_opponents_commit_fails(
    tmp_path, default_params, network_params,
):
    """COMMIT push succeeds; the opponent's COMMIT arrives; but the ACK we
    owe them (inside wait_for_ack_and_commit) fails to send."""
    client = FailAfterClient(succeed_calls=1)
    ctx = make_ctx(
        tmp_path, default_params, network_params, role="police", label="init-ack-fail",
        security=_ON, client=client, initial_state=State.MY_TURN,
    )
    current = ctx.machine.state
    dest = engine.legal_moves(ctx.state, "cop", default_params)[0]

    task = asyncio.create_task(turn_commit.initiate(ctx, current, ctx.state.cop, dest, None, None))
    await _pump()
    ctx.runtime.queue.put_nowait(
        Envelope(type=MessageType.COMMIT, turn=0, sender="thief", payload={"h_commit": "b" * 64}),
    )
    result = await task

    assert result is Outcome.TECHNICAL_LOSS
    assert ctx.machine.state is State.GAME_OVER


async def test_initiate_reports_technical_loss_when_the_reveal_push_fails(
    tmp_path, default_params, network_params,
):
    """COMMIT push, opponent's COMMIT arrival, and the ACK of it all
    succeed; only the final REVEAL push fails."""
    client = FailAfterClient(succeed_calls=2)
    ctx = make_ctx(
        tmp_path, default_params, network_params, role="police", label="init-reveal-fail",
        security=_ON, client=client, initial_state=State.MY_TURN,
    )
    current = ctx.machine.state
    dest = engine.legal_moves(ctx.state, "cop", default_params)[0]

    task = asyncio.create_task(turn_commit.initiate(ctx, current, ctx.state.cop, dest, None, None))
    await _pump()
    h_commit = client.calls[0][1]["payload"]["h_commit"]
    ctx.runtime.queue.put_nowait(
        Envelope(type=MessageType.ACK, turn=0, sender="thief", payload={"h_commit": h_commit}),
    )
    ctx.runtime.queue.put_nowait(
        Envelope(type=MessageType.COMMIT, turn=0, sender="thief", payload={"h_commit": "b" * 64}),
    )
    result = await task

    assert result is Outcome.TECHNICAL_LOSS
    assert ctx.machine.state is State.GAME_OVER
