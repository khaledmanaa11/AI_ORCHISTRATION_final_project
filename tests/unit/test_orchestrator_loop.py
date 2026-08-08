"""run_turn_loop-level tests -- split from test_orchestrator.py at the
150-code-line gate (Segal Table 5), not by test meaning. Shared fakes and the
`make_ctx` assembly helper live in tests/unit/_fakes_agent.py and are imported
here (QUAL-02): NET-05 illegal-transition severity handling, the NET-06
silent-opponent technical win, and a real-outcome clean exit.
"""

import asyncio
import dataclasses
import json

from pursuit.constants import Outcome
from pursuit.network import orchestrator
from pursuit.network.envelope import Envelope, MessageType
from pursuit.network.state_machine import State, TransitionSeverity
from tests.unit._fakes_agent import make_ctx


async def test_illegal_transition_is_reported_and_escalates_to_error(
    tmp_path, default_params, network_params
):
    """THE NET-05 GATE (PROTOCOL_VIOLATION half): reported exactly once, escalates.

    RECOVERABLE severity for a genuine duplicate/out-of-order attempt is
    already covered directly at the state-machine level by
    test_state_machine.py::test_recoverable_attempt_keeps_machine_usable
    (QUAL-02) -- not restated here. Calling take_my_turn while the machine is
    ALREADY at MY_TURN is no longer a rejectable duplicate at this level; see
    test_take_my_turn_proceeds_when_the_machine_is_already_at_my_turn below
    for why (the D-09 repeatable-cycle fix)."""
    violation_ctx = make_ctx(
        tmp_path, default_params, network_params,
        label="violation", initial_state=State.GAME_OVER,
    )
    outcome = await orchestrator.take_my_turn(violation_ctx)
    assert outcome is None
    assert len(violation_ctx.reporter.calls) == 1
    assert violation_ctx.reporter.calls[0]["severity"] is TransitionSeverity.PROTOCOL_VIOLATION
    assert violation_ctx.machine.state is State.ERROR
    lines = violation_ctx.log_path.read_text(encoding="utf-8").splitlines()
    assert any(json.loads(line)["event"] == "illegal_transition" for line in lines)


async def test_take_my_turn_proceeds_when_the_machine_is_already_at_my_turn(
    tmp_path, default_params, network_params
):
    """Regression test for a real multi-cycle bug found while building 02-10's
    GATE-3 integration test: `await_opponent_turn` legitimately ends every
    cycle by transitioning WAIT_OPPONENT -> MY_TURN itself (D-09), so the
    very next `take_my_turn` call in `run_turn_loop` always finds the machine
    already at MY_TURN. Unconditionally re-attempting MY_TURN there used to
    collide with that same state as an illegal (MY_TURN, MY_TURN)
    self-transition every cycle after the first, silently turning every
    second-and-later turn into a no-op (proven live via `run_turn_loop` in
    tests/integration/test_turn_lifecycle.py::test_full_lifecycle_init_to_game_over).
    `take_my_turn` must instead treat "already at MY_TURN" as its normal,
    unguarded precondition and actually take the turn -- never report it as
    illegal and never skip the move."""
    ctx = make_ctx(
        tmp_path, default_params, network_params,
        label="already-my-turn", initial_state=State.MY_TURN,
    )
    outcome = await orchestrator.take_my_turn(ctx)
    assert outcome is None  # no capture on the first legal move
    assert ctx.reporter.calls == []  # no illegal-transition report of any kind
    assert ctx.machine.state is State.WAIT_OPPONENT  # the move really happened
    # Phase 4 (D-47): the move push plus the placeholder-hint push -- both
    # calls really happened, the move first.
    assert len(ctx.runtime.client().calls) == 2
    assert ctx.runtime.client().calls[0][0] == "receive_move"
    assert ctx.runtime.client().calls[1][0] == "receive_hint"


async def test_silent_opponent_produces_a_technical_win(tmp_path, default_params, network_params):
    """THE NET-06 GATE: a silent opponent ends the game cleanly, never a hang."""
    ctx = make_ctx(tmp_path, default_params, network_params, role="police", label="silent")
    outcome = await asyncio.wait_for(orchestrator.run_turn_loop(ctx), timeout=5)

    assert ctx.machine.state is State.GAME_OVER
    assert outcome is Outcome.TECHNICAL_LOSS
    lines = ctx.log_path.read_text(encoding="utf-8").splitlines()
    records = [json.loads(line) for line in lines]
    wins = [r for r in records if r["event"] == "technical_win"]
    assert len(wins) == 1
    assert wins[0]["retries_attempted"] == ctx.net.retry_count + 1
    assert wins[0]["timeout_seconds"] == ctx.net.response_timeout
    # Phase 4 (D-47): take_my_turn's move push AND its placeholder-hint push
    # both succeed against the (non-failing) FakeClient; only the SUBSEQUENT
    # await_opponent_turn wait on an empty queue times out -- never asked to
    # keep playing beyond that.
    assert len(ctx.runtime.client().calls) == 2


async def test_await_opponent_turn_rejects_an_illegal_move_as_a_technical_loss(
    tmp_path, default_params, network_params
):
    """Rules 13/14: an off-board (unparseable-to-legal) move from the peer
    never crashes the handler -- it becomes Outcome.TECHNICAL_LOSS with a
    technical_win JSONL record naming the reason (D-53)."""
    ctx = make_ctx(
        tmp_path, default_params, network_params, label="illegal-move",
        initial_state=State.WAIT_OPPONENT,
    )
    bad_move = Envelope(type=MessageType.MOVE, turn=0, sender="thief", payload={"x": 99, "y": 99})
    ctx.runtime.queue.put_nowait(bad_move)

    outcome = await orchestrator.await_opponent_turn(ctx)

    assert outcome is Outcome.TECHNICAL_LOSS
    assert ctx.machine.state is State.GAME_OVER
    lines = ctx.log_path.read_text(encoding="utf-8").splitlines()
    assert any('"technical_win"' in line for line in lines)


async def test_await_opponent_turn_rejects_two_consecutive_hints_with_no_move(
    tmp_path, default_params, network_params
):
    """The HintProtocolError raised by turn_buffer.await_move (two hints,
    no move) is caught at the orchestrator entry point, never crashes the
    caller, and ends the game as Outcome.TECHNICAL_LOSS."""
    ctx = make_ctx(
        tmp_path, default_params, network_params, label="two-hints",
        initial_state=State.WAIT_OPPONENT,
    )
    hint_payload = {"text": "heading uptown", "intent": "truth", "turn": 0}
    ctx.runtime.queue.put_nowait(
        Envelope(type=MessageType.HINT, turn=0, sender="thief", payload=hint_payload)
    )
    ctx.runtime.queue.put_nowait(
        Envelope(type=MessageType.HINT, turn=0, sender="police", payload=hint_payload)
    )

    outcome = await orchestrator.await_opponent_turn(ctx)

    assert outcome is Outcome.TECHNICAL_LOSS
    assert ctx.machine.state is State.GAME_OVER


async def test_await_opponent_turn_from_handshake_self_transitions_first(
    tmp_path, default_params, network_params
):
    """D-09 design note 7: the thief's FIRST call is await_opponent_turn
    while still in HANDSHAKE; it self-transitions to WAIT_OPPONENT before
    waiting, exactly like take_my_turn's own guarded entry."""
    ctx = make_ctx(
        tmp_path, default_params, network_params, role="thief", label="handshake-first",
        initial_state=State.HANDSHAKE,
    )
    stay_in_place = {"x": ctx.state.cop[0], "y": ctx.state.cop[1]}
    incoming = Envelope(type=MessageType.MOVE, turn=0, sender="police", payload=stay_in_place)
    ctx.runtime.queue.put_nowait(incoming)

    await orchestrator.await_opponent_turn(ctx)

    assert ctx.machine.state is State.MY_TURN


async def test_loop_ends_cleanly_on_a_real_outcome(tmp_path, default_params, network_params):
    """A real SDK outcome (capture) ends the loop and persists game_over.

    Positions are overridden to adjacent cells reachable in one legal step:
    resolve_turn now validates legality (RULES-RESOLUTION.md), so the old
    scenario -- a cop "teleporting" six cells straight onto the thief's
    start position, with no thief move involved at all -- is no longer
    reachable (it only "worked" because the superseded apply_move validated
    nothing). The thief's matching move is injected on the queue exactly as
    test_full_turn_cycle does, because a capture now requires both sides'
    actions to be known before resolve_turn can fire -- the single-sided-
    capture bug this migration fixes."""
    ctx = make_ctx(tmp_path, default_params, network_params, role="police", label="capture")
    ctx.state = dataclasses.replace(ctx.state, cop=(2, 2), thief=(2, 3))
    ctx.choose_move = lambda state, agent, params: state.thief  # cop steps onto the thief

    incoming = Envelope(type=MessageType.MOVE, turn=1, sender="thief", payload={"x": 2, "y": 3})
    ctx.runtime.queue.put_nowait(incoming.to_dict())

    outcome = await asyncio.wait_for(orchestrator.run_turn_loop(ctx), timeout=5)

    assert outcome is Outcome.CAPTURE
    assert ctx.machine.state is State.GAME_OVER
    lines = ctx.log_path.read_text(encoding="utf-8").splitlines()
    records = [json.loads(line) for line in lines]
    assert any(r["event"] == "game_over" and r["outcome"] == Outcome.CAPTURE.value for r in records)
