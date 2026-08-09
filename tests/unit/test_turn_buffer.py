"""Tests for the Phase-4 hint-buffering additions to turn_buffer.py
(record_hint, reject_peer_payload, await_move, drain_trailing_hint,
send_hint). The pre-existing action-buffer helpers (record_action,
maybe_resolve, log_illegal) are exercised through test_orchestrator.py /
test_orchestrator_loop.py, per that file's own house style (QUAL-02) --
not re-tested here."""

from pursuit.constants import Outcome
from pursuit.network import turn_buffer
from pursuit.network.envelope import Envelope, MessageType
from pursuit.network.hint_payload import HintKey, Intent
from pursuit.network.state_machine import State
from tests.unit._fakes_agent import FakeClient, make_ctx


def _hint_envelope(turn: int, sender: str = "thief") -> Envelope:
    return Envelope(
        type=MessageType.HINT, turn=turn, sender=sender,
        payload={HintKey.TEXT.value: "heading uptown", HintKey.INTENT.value: Intent.TRUTH.value,
                 HintKey.TURN.value: turn},
    )


def test_record_hint_buffers_by_sender(tmp_path, default_params, network_params):
    ctx = make_ctx(tmp_path, default_params, network_params, label="rh")
    turn_buffer.record_hint(ctx, "thief", ctx.state.turn, {"text": "hi"})
    assert ctx.pending_hints == {"thief": {"text": "hi"}}


def test_record_hint_overwrites_a_second_hint_from_the_same_sender(
    tmp_path, default_params, network_params
):
    """04-12 (Rule 1 - bug fix): a second not-yet-consumed hint from the
    same sender is ordinary timing (each hint is an independent
    round-trip), never a protocol violation -- the freshest one wins,
    matching `ctx.incoming_hints`' own overwrite semantics, and neither
    call may raise."""
    ctx = make_ctx(tmp_path, default_params, network_params, label="rh-dup")
    turn_buffer.record_hint(ctx, "thief", ctx.state.turn, {"text": "first"})
    turn_buffer.record_hint(ctx, "thief", ctx.state.turn, {"text": "second"})  # must not raise
    assert ctx.pending_hints == {"thief": {"text": "second"}}


def test_record_hint_silently_drops_a_hint_for_an_already_resolved_turn(
    tmp_path, default_params, network_params
):
    """04-12 (Rule 1 - bug fix): a late hint is ordinary network jitter
    (the move and the hint are independent round-trips), never a protocol
    violation -- it must never raise or end the game, and must never enter
    either buffer."""
    ctx = make_ctx(tmp_path, default_params, network_params, label="rh-late")
    turn_buffer.record_hint(ctx, "thief", ctx.state.turn - 1, {"text": "late"})  # must not raise
    assert ctx.pending_hints == {}
    assert ctx.incoming_hints == {}


def test_reject_peer_payload_logs_and_ends_the_game(tmp_path, default_params, network_params):
    # WAIT_OPPONENT: the real state await_opponent_turn is in when it calls
    # this helper (HANDSHAKE -> WAIT_OPPONENT already happened by then).
    ctx = make_ctx(
        tmp_path, default_params, network_params, label="reject", initial_state=State.WAIT_OPPONENT
    )
    outcome = turn_buffer.reject_peer_payload(ctx, reason="an illegal payload")
    assert outcome is Outcome.TECHNICAL_LOSS
    assert ctx.machine.state is State.GAME_OVER
    lines = ctx.log_path.read_text(encoding="utf-8").splitlines()
    assert any('"technical_win"' in line and "an illegal payload" in line for line in lines)


async def test_await_move_returns_the_move_directly_when_no_hint_precedes_it(
    tmp_path, default_params, network_params
):
    ctx = make_ctx(tmp_path, default_params, network_params, label="await-move")
    move = Envelope(type=MessageType.MOVE, turn=0, sender="thief", payload={"x": 3, "y": 3})
    ctx.runtime.queue.put_nowait(move)
    envelope, verdict = await turn_buffer.await_move(ctx)
    assert verdict is None
    assert envelope == move


async def test_await_move_buffers_a_leading_hint_then_returns_the_move(
    tmp_path, default_params, network_params
):
    ctx = make_ctx(tmp_path, default_params, network_params, label="await-move-hint")
    move = Envelope(type=MessageType.MOVE, turn=0, sender="thief", payload={"x": 3, "y": 3})
    ctx.runtime.queue.put_nowait(_hint_envelope(0))
    ctx.runtime.queue.put_nowait(move)
    envelope, verdict = await turn_buffer.await_move(ctx)
    assert verdict is None
    assert envelope == move
    assert "thief" in ctx.pending_hints


async def test_await_move_raises_on_two_consecutive_hints(tmp_path, default_params, network_params):
    ctx = make_ctx(tmp_path, default_params, network_params, label="await-move-2hints")
    ctx.runtime.queue.put_nowait(_hint_envelope(0, sender="thief"))
    ctx.runtime.queue.put_nowait(_hint_envelope(0, sender="police"))
    try:
        await turn_buffer.await_move(ctx)
    except turn_buffer.HintProtocolError:
        return
    raise AssertionError("expected two consecutive hints with no move to raise")


async def test_await_move_reports_a_silent_opponent(tmp_path, default_params, network_params):
    ctx = make_ctx(tmp_path, default_params, network_params, label="await-move-silent")
    envelope, verdict = await turn_buffer.await_move(ctx)
    assert envelope is None
    assert verdict is not None


def test_drain_trailing_hint_records_a_hint_present_on_the_queue(
    tmp_path, default_params, network_params
):
    ctx = make_ctx(tmp_path, default_params, network_params, label="drain-hint")
    ctx.runtime.queue.put_nowait(_hint_envelope(0))
    turn_buffer.drain_trailing_hint(ctx)
    assert "thief" in ctx.pending_hints
    assert ctx.runtime.queue.qsize() == 0


def test_drain_trailing_hint_is_a_no_op_on_an_empty_queue(tmp_path, default_params, network_params):
    ctx = make_ctx(tmp_path, default_params, network_params, label="drain-empty")
    turn_buffer.drain_trailing_hint(ctx)
    assert ctx.pending_hints == {}


def test_drain_trailing_hint_puts_back_a_non_hint_item(tmp_path, default_params, network_params):
    ctx = make_ctx(tmp_path, default_params, network_params, label="drain-putback")
    future_move = Envelope(type=MessageType.MOVE, turn=1, sender="thief", payload={"x": 3, "y": 3})
    ctx.runtime.queue.put_nowait(future_move)
    turn_buffer.drain_trailing_hint(ctx)
    assert ctx.pending_hints == {}
    assert ctx.runtime.queue.qsize() == 1
    assert ctx.runtime.queue.get_nowait() == future_move


async def test_send_hint_pushes_and_logs_on_success(tmp_path, default_params, network_params):
    ctx = make_ctx(tmp_path, default_params, network_params, label="send-hint-ok")
    await turn_buffer.send_hint(ctx, ctx.state.turn, text="heading uptown", intent=Intent.TRUTH)
    name, _args = ctx.runtime.client().calls[0]
    assert name == "receive_hint"
    lines = ctx.log_path.read_text(encoding="utf-8").splitlines()
    assert any('"message_sent"' in line and '"hint"' in line for line in lines)


async def test_send_hint_never_raises_when_the_push_fails(tmp_path, default_params, network_params):
    ctx = make_ctx(
        tmp_path, default_params, network_params, label="send-hint-fail",
        client=FakeClient(fail=True),
    )
    # 04-12: text/intent are the REAL composed channel now (send_hint owns
    # only push-and-log mechanics); must not raise.
    await turn_buffer.send_hint(ctx, ctx.state.turn, text="heading uptown", intent=Intent.TRUTH)
    assert ctx.machine.state is not State.ERROR
