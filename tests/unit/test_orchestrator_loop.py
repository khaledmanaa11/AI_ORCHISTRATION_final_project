"""run_turn_loop-level tests -- split from test_orchestrator.py at the
150-code-line gate (Segal Table 5), not by test meaning. Shared fakes and the
`make_ctx` assembly helper live in tests/unit/_fakes_agent.py and are imported
here (QUAL-02): NET-05 illegal-transition severity handling, the NET-06
silent-opponent technical win, and a real-outcome clean exit.
"""

import asyncio
import json

from pursuit.constants import Outcome
from pursuit.network import orchestrator
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
    assert len(ctx.runtime.client().calls) == 1  # the move really was pushed


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
    assert len(ctx.runtime.client().calls) == 1  # the one push; never asked to keep playing


async def test_loop_ends_cleanly_on_a_real_outcome(tmp_path, default_params, network_params):
    """A real SDK outcome (capture) ends the loop and persists game_over."""
    ctx = make_ctx(tmp_path, default_params, network_params, role="police", label="capture")
    ctx.choose_move = lambda state, agent, params: state.thief  # cop lands on thief

    outcome = await asyncio.wait_for(orchestrator.run_turn_loop(ctx), timeout=5)

    assert outcome is Outcome.CAPTURE
    assert ctx.machine.state is State.GAME_OVER
    lines = ctx.log_path.read_text(encoding="utf-8").splitlines()
    records = [json.loads(line) for line in lines]
    assert any(r["event"] == "game_over" and r["outcome"] == Outcome.CAPTURE.value for r in records)
