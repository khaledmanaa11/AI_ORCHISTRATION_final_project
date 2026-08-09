"""Tests for `network/turn_commit.py`'s D-58 exchange, fake-driven, no real
network (`FakeClient`/`FakeRuntime`, `tests/unit/_fakes_agent.py`).

`initiate` (the initiator path, police) is covered here in full: toggle-off
byte-equivalence, the on-toggle Commit-then-Reveal order with the ledger
appended before either send, and jitter tolerance (a duplicate ACK/COMMIT
dropped, never raised). The responder path (`await_and_respond`/
`reveal_pending`) needs a real `ctx.language` to exercise the decide-now
spies the plan's own verify block asks for, and lives in the sibling
`test_turn_commit_responder.py` -- split at the 150-code-line gate.
"""

from __future__ import annotations

import asyncio

from pursuit.network import turn_commit
from pursuit.network.envelope import Envelope, MessageType
from pursuit.sdk import engine
from pursuit.shared.security_config import SecurityParams
from tests.unit._fakes_agent import make_ctx

_ON = SecurityParams(version="1.00", commit_reveal=True, team_code="khm-mn17")


async def _pump(rounds: int = 50) -> None:
    """Yield control back to the event loop `rounds` times -- enough for a
    fake-driven `initiate()`/`await_and_respond()` task to unwind its own
    nested `call_with_retry`/`asyncio.wait_for` layers up to its next real
    block on an empty `asyncio.Queue`, with no real network or real sleep
    involved."""
    for _ in range(rounds):
        await asyncio.sleep(0)


async def test_initiate_toggle_off_is_byte_equivalent_to_pre_phase_6(
    tmp_path, default_params, network_params,
):
    ctx = make_ctx(tmp_path, default_params, network_params, role="police", label="init-off")
    current = ctx.machine.state
    dest = engine.legal_moves(ctx.state, "cop", default_params)[0]

    result = await turn_commit.initiate(ctx, current, ctx.state.cop, dest, None, None)

    assert result is None
    assert [name for name, _args in ctx.runtime.client().calls] == ["receive_move"]
    assert not (tmp_path / "init-off.ledger.jsonl").exists()


async def test_await_and_respond_toggle_off_delegates_to_await_move_verbatim(
    tmp_path, default_params, network_params,
):
    ctx = make_ctx(tmp_path, default_params, network_params, role="thief", label="await-off")
    move = Envelope(type=MessageType.MOVE, turn=0, sender="police", payload={"x": 0, "y": 0})
    ctx.runtime.queue.put_nowait(move)

    envelope, verdict = await turn_commit.await_and_respond(ctx)

    assert verdict is None
    assert envelope == move


async def test_initiate_on_toggle_commits_then_reveals_with_ledger_before_any_send(
    tmp_path, default_params, network_params,
):
    ctx = make_ctx(
        tmp_path, default_params, network_params, role="police", label="init-on", security=_ON,
    )
    current = ctx.machine.state
    dest = engine.legal_moves(ctx.state, "cop", default_params)[0]

    task = asyncio.create_task(
        turn_commit.initiate(ctx, current, ctx.state.cop, dest, None, None)
    )
    await _pump()

    calls = ctx.runtime.client().calls
    assert len(calls) == 1
    name, args = calls[0]
    assert name == "receive_commit"
    h_commit = args["payload"]["h_commit"]

    # The ledger already carries this exact h_commit BEFORE either send --
    # commit_own_action's own ordering (D-64), observable the moment the
    # COMMIT push has happened.
    ledger_lines = (tmp_path / "init-on.ledger.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(ledger_lines) == 1
    assert h_commit in ledger_lines[0]
    assert '"nonce"' in ledger_lines[0]

    ctx.runtime.queue.put_nowait(
        Envelope(type=MessageType.ACK, turn=0, sender="thief", payload={"h_commit": h_commit})
    )
    ctx.runtime.queue.put_nowait(
        Envelope(type=MessageType.COMMIT, turn=0, sender="thief", payload={"h_commit": "b" * 64})
    )
    result = await task

    assert result is None
    names = [name for name, _args in ctx.runtime.client().calls]
    assert names == ["receive_commit", "receive_ack", "receive_reveal"]
    reveal_args = ctx.runtime.client().calls[2][1]
    assert "nonce" not in reveal_args["payload"]  # SEC-04: nonce never rides REVEAL
    assert reveal_args["payload"]["barrier"] is None


async def test_initiate_drops_a_duplicate_ack_and_commit_without_raising(
    tmp_path, default_params, network_params,
):
    ctx = make_ctx(
        tmp_path, default_params, network_params, role="police", label="init-dup", security=_ON,
    )
    current = ctx.machine.state
    dest = engine.legal_moves(ctx.state, "cop", default_params)[0]

    task = asyncio.create_task(
        turn_commit.initiate(ctx, current, ctx.state.cop, dest, None, None)
    )
    await _pump()
    h_commit = ctx.runtime.client().calls[0][1]["payload"]["h_commit"]

    ack = Envelope(type=MessageType.ACK, turn=0, sender="thief", payload={"h_commit": h_commit})
    commit_b = Envelope(
        type=MessageType.COMMIT, turn=0, sender="thief", payload={"h_commit": "c" * 64},
    )
    # A late duplicate of EACH arrives first -- both must be tolerated
    # jitter, dropped, never raised (D-58, 04-12's jitter lesson).
    ctx.runtime.queue.put_nowait(ack)
    ctx.runtime.queue.put_nowait(commit_b)
    ctx.runtime.queue.put_nowait(ack)
    ctx.runtime.queue.put_nowait(commit_b)

    result = await task

    assert result is None
    names = [name for name, _args in ctx.runtime.client().calls]
    assert names.count("receive_ack") == 1  # only ONE ack sent back for COMMIT_B
    assert names[-1] == "receive_reveal"
