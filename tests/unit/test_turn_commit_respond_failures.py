"""Technical-loss branch coverage for `turn_commit.await_and_respond`'s
responder path and `turn_commit.reveal_pending` -- fake-driven, no real
network, no `ctx.language` needed (the decide-now step's decode/plan
stages both no-op cleanly with `ctx.language is None`, matching
`make_ctx`'s own default). Split from test_turn_commit_responder.py at the
150-code-line gate.
"""

from __future__ import annotations

from pursuit.constants import Outcome
from pursuit.network import turn_actions, turn_commit
from pursuit.network.commit_state import PendingAction
from pursuit.network.envelope import Envelope, MessageType
from pursuit.network.state_machine import State
from pursuit.shared.security_config import SecurityParams
from tests.unit._fakes_agent import FailAfterClient, FakeClient, make_ctx

_ON = SecurityParams(version="1.00", commit_reveal=True, team_code="khm-mn17")


def _pending(ctx) -> PendingAction:
    return PendingAction(
        move=ctx.state.thief, barrier=None, plan=None, incoming_log=None, regime="B",
        action_payload={"move": {"kind": "move", "direction": "stay"}, "barrier": None},
        h_commit="a" * 64, turn=0,
    )


async def test_await_and_respond_reports_technical_loss_when_no_commit_ever_arrives(
    tmp_path, default_params, network_params,
):
    ctx = make_ctx(
        tmp_path, default_params, network_params, role="thief", label="respond-wait-fail",
        security=_ON, initial_state=State.WAIT_OPPONENT,
    )
    envelope, verdict = await turn_commit.await_and_respond(ctx)
    assert envelope is None
    assert verdict is not None


async def test_await_and_respond_reports_a_verdict_when_own_commit_push_fails(
    tmp_path, default_params, network_params,
):
    ctx = make_ctx(
        tmp_path, default_params, network_params, role="thief", label="respond-commit-fail",
        security=_ON, initial_state=State.WAIT_OPPONENT, client=FakeClient(fail=True),
    )
    ctx.runtime.queue.put_nowait(
        Envelope(type=MessageType.COMMIT, turn=0, sender="police", payload={"h_commit": "a" * 64}),
    )
    envelope, verdict = await turn_commit.await_and_respond(ctx)
    assert envelope is None
    assert verdict is not None


async def test_await_and_respond_reports_a_verdict_when_own_ack_push_fails(
    tmp_path, default_params, network_params,
):
    client = FailAfterClient(succeed_calls=1)
    ctx = make_ctx(
        tmp_path, default_params, network_params, role="thief", label="respond-ack-fail",
        security=_ON, initial_state=State.WAIT_OPPONENT, client=client,
    )
    ctx.runtime.queue.put_nowait(
        Envelope(type=MessageType.COMMIT, turn=0, sender="police", payload={"h_commit": "a" * 64}),
    )
    envelope, verdict = await turn_commit.await_and_respond(ctx)
    assert envelope is None
    assert verdict is not None


async def test_await_and_respond_reports_a_verdict_when_the_reveal_never_arrives(
    tmp_path, default_params, network_params,
):
    """COMMIT arrives, our own COMMIT+ACK both push fine, but the
    opponent's REVEAL never comes -- the tail wait's own ladder exhausts."""
    ctx = make_ctx(
        tmp_path, default_params, network_params, role="thief", label="respond-reveal-fail",
        security=_ON, initial_state=State.WAIT_OPPONENT,
    )
    ctx.runtime.queue.put_nowait(
        Envelope(type=MessageType.COMMIT, turn=0, sender="police", payload={"h_commit": "a" * 64}),
    )
    envelope, verdict = await turn_commit.await_and_respond(ctx)
    assert envelope is None
    assert verdict is not None


async def test_reveal_pending_reports_technical_loss_when_the_ack_never_arrives(
    tmp_path, default_params, network_params,
):
    ctx = make_ctx(
        tmp_path, default_params, network_params, role="thief", label="reveal-ack-fail",
        security=_ON, initial_state=State.MY_TURN,
    )
    ctx.commit_state.pending_action = _pending(ctx)

    result = await turn_commit.reveal_pending(ctx)

    assert result is Outcome.TECHNICAL_LOSS
    assert ctx.machine.state is State.GAME_OVER


async def test_reveal_pending_reports_technical_loss_when_the_reveal_push_fails(
    tmp_path, default_params, network_params,
):
    ctx = make_ctx(
        tmp_path, default_params, network_params, role="thief", label="reveal-push-fail",
        security=_ON, initial_state=State.MY_TURN, client=FakeClient(fail=True),
    )
    ctx.commit_state.pending_action = _pending(ctx)
    ctx.commit_state.own_ack_received = True  # skip the ack-wait, go straight to the push

    result = await turn_commit.reveal_pending(ctx)

    assert result is Outcome.TECHNICAL_LOSS
    assert ctx.machine.state is State.GAME_OVER


async def test_take_my_turn_propagates_reveal_pendings_technical_loss(
    tmp_path, default_params, network_params,
):
    """turn_actions.take_my_turn's responder branch returns reveal_pending's
    verdict immediately -- never masking it, never resolving the turn."""
    ctx = make_ctx(
        tmp_path, default_params, network_params, role="thief", label="take-my-turn-propagate",
        security=_ON, initial_state=State.MY_TURN, client=FakeClient(fail=True),
    )
    ctx.commit_state.pending_action = _pending(ctx)

    outcome = await turn_actions.take_my_turn(ctx)

    assert outcome is Outcome.TECHNICAL_LOSS
    assert ctx.machine.state is State.GAME_OVER
