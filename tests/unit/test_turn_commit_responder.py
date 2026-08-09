"""D-58 responder-path tests for `network/turn_commit.py`, split from
`test_turn_commit.py` at the 150-code-line gate: `await_and_respond` (the
thief's decide-now step) needs a real `ctx.language` to exercise the
decode/choose/plan spies the plan's own verify block asks for, which
`test_turn_commit.py`'s toggle-off/initiator tests never touch.
"""

from __future__ import annotations

import asyncio

from pursuit.network import turn_commit
from pursuit.network.agent_wiring import load_agent_config
from pursuit.network.envelope import Envelope, MessageType
from pursuit.network.language_wiring import build_language_runtime
from pursuit.network.move_payload import ActionKind, encode
from pursuit.shared.security_config import SecurityParams
from tests.unit._fakes_agent import make_ctx
from tests.unit.test_turn_commit import _pump

_ON = SecurityParams(version="1.00", commit_reveal=True, team_code="khm-mn17")


def _responder_ctx(tmp_path, default_params, network_params, label):
    ctx = make_ctx(
        tmp_path, default_params, network_params, role="thief", label=label, security=_ON,
    )
    cfg = load_agent_config("config/thief")
    ctx.language = build_language_runtime(
        language=cfg.language, deception=cfg.deception, board_size=default_params.board_size,
        seed=1,
    )
    return ctx


async def test_await_and_respond_decides_once_via_named_functions_never_resolving(
    tmp_path, default_params, network_params, monkeypatch,
):
    """The decide-now step calls decode_turn_hint/choose_destination/
    plan_turn_deception by their PUBLIC names -- asserted via spy (GATE-4's
    own technique) -- exactly once, builds a PendingAction, and never
    touches record_action/maybe_resolve (ctx.pending_thief_move/
    pending_cop_action stay untouched by this call alone)."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    ctx = _responder_ctx(tmp_path, default_params, network_params, "respond-on")
    opponent_h_commit = "a" * 64
    ctx.runtime.queue.put_nowait(
        Envelope(type=MessageType.COMMIT, turn=0, sender="police", payload={"h_commit": opponent_h_commit}),
    )

    calls = {"decode": 0, "choose": 0, "plan": 0}
    real_decode, real_choose, real_plan = (
        turn_commit.decode_turn_hint, turn_commit.choose_destination, turn_commit.plan_turn_deception,
    )

    async def spy_decode(*a, **kw):
        calls["decode"] += 1
        return await real_decode(*a, **kw)

    def spy_choose(*a, **kw):
        calls["choose"] += 1
        return real_choose(*a, **kw)

    def spy_plan(*a, **kw):
        calls["plan"] += 1
        return real_plan(*a, **kw)

    turn_commit.decode_turn_hint = spy_decode
    turn_commit.choose_destination = spy_choose
    turn_commit.plan_turn_deception = spy_plan
    try:
        task = asyncio.create_task(turn_commit.await_and_respond(ctx))
        await _pump()

        assert calls == {"decode": 1, "choose": 1, "plan": 1}
        assert ctx.commit_state.pending_action is not None
        assert ctx.pending_thief_move is None
        assert ctx.pending_cop_action is None
        names = [name for name, _args in ctx.runtime.client().calls]
        assert names == ["receive_commit", "receive_ack"]

        reveal = Envelope(
            type=MessageType.REVEAL, turn=0, sender="police",
            payload={"move": encode((0, 0), (0, 1), ActionKind.MOVE), "barrier": None},
        )
        ctx.runtime.queue.put_nowait(reveal)
        envelope, verdict = await task
    finally:
        turn_commit.decode_turn_hint = real_decode
        turn_commit.choose_destination = real_choose
        turn_commit.plan_turn_deception = real_plan

    assert verdict is None
    assert envelope == reveal
    assert calls == {"decode": 1, "choose": 1, "plan": 1}  # still exactly once


async def test_reveal_pending_sends_the_stash_without_deciding_again(
    tmp_path, default_params, network_params, monkeypatch,
):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    ctx = _responder_ctx(tmp_path, default_params, network_params, "reveal-pending")
    ctx.runtime.queue.put_nowait(
        Envelope(type=MessageType.COMMIT, turn=0, sender="police", payload={"h_commit": "a" * 64}),
    )
    task = asyncio.create_task(turn_commit.await_and_respond(ctx))
    await _pump()
    pending = ctx.commit_state.pending_action
    assert pending is not None
    ack_b = Envelope(type=MessageType.ACK, turn=0, sender="police", payload={"h_commit": pending.h_commit})
    reveal_a = Envelope(
        type=MessageType.REVEAL, turn=0, sender="police",
        payload={"move": encode((0, 0), (0, 1), ActionKind.MOVE), "barrier": None},
    )
    ctx.runtime.queue.put_nowait(reveal_a)
    await task

    def _fail(*_a, **_kw):
        raise AssertionError("reveal_pending must never decide again")

    real_decode, real_choose, real_plan = (
        turn_commit.decode_turn_hint, turn_commit.choose_destination, turn_commit.plan_turn_deception,
    )
    turn_commit.decode_turn_hint = _fail
    turn_commit.choose_destination = _fail
    turn_commit.plan_turn_deception = _fail
    try:
        reveal_task = asyncio.create_task(turn_commit.reveal_pending(ctx))
        await _pump()
        ctx.runtime.queue.put_nowait(ack_b)
        result = await reveal_task
    finally:
        turn_commit.decode_turn_hint = real_decode
        turn_commit.choose_destination = real_choose
        turn_commit.plan_turn_deception = real_plan

    assert result is None
    names = [name for name, _args in ctx.runtime.client().calls]
    assert names[-1] == "receive_reveal"
    sent_payload = ctx.runtime.client().calls[-1][1]["payload"]
    assert sent_payload == pending.action_payload
